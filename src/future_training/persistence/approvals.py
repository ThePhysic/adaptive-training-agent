"""Native PostgreSQL approved snapshots, durable keys and authoritative reconciliation."""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from uuid import uuid4

import psycopg
from pydantic import TypeAdapter, ValidationError

from future_training.candidates import Snapshot, encode_snapshot
from future_training.domain.catalog import Catalog
from future_training.domain.validator import VALIDATOR_VERSION
from future_training.errors import ServiceError
from future_training.identity import Principal, owner_id
from future_training.observability import annotate, traced, validate_plan
from future_training.persistence.plans import PlanRow
from future_training.persistence.profiles import connect_local
from future_training.schemas import (
    ApprovalRequest,
    ApprovalResult,
    CandidateIdentity,
    ContextVersions,
    Identifier,
    PlanProposal,
    SavedPlan,
    SavedProfile,
)


def fingerprint(owner: str, request: ApprovalRequest) -> str:
    value = {
        "owner": owner,
        "operation": "approve_plan",
        **request.model_dump(exclude={"idempotency_key"}),
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def identity_lock(owner: str, candidate_id: str) -> int:
    # A collision only serializes unrelated identities; SQL predicates/uniques
    # still decide ownership and equality. Never use Python's randomized hash().
    return int.from_bytes(
        hashlib.sha256((owner + ":" + candidate_id).encode()).digest()[:8], signed=True
    )


class CommitUncertain(Exception):
    """COMMIT was invoked; its failure/cancellation does not establish rollback."""


class PostgresApprovals:
    def __init__(self, catalog: Catalog, *, connect: Callable[[], Awaitable] = connect_local):
        self.catalog = catalog
        self._connect = connect
        self._slots = asyncio.Semaphore(4)

    @staticmethod
    def _result(row) -> ApprovalResult:
        return ApprovalResult(
            plan_id=row[0],
            candidate=CandidateIdentity(candidate_id=row[1], revision=row[2], content_hash=row[3]),
        )

    @traced("approval.lookup")
    async def committed(
        self, principal: Principal, request: ApprovalRequest
    ) -> ApprovalResult | None:
        owner = owner_id(principal)
        try:
            async with asyncio.timeout(10), self._slots, await self._connect() as connection:
                cursor = await connection.execute(
                    "SELECT p.plan_id,p.candidate_id,p.candidate_revision,"
                    "p.content_hash,k.fingerprint "
                    "FROM approval_idempotency k JOIN approved_plans p "
                    "ON p.owner_id=k.owner_id AND p.plan_id=k.plan_id "
                    "WHERE k.owner_id=%s AND k.operation='approve_plan' AND k.idempotency_key=%s",
                    (owner, request.idempotency_key),
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                if row[4] != fingerprint(owner, request):
                    raise ServiceError(409, "idempotency_mismatch")
                result = self._result(row)
                if result.candidate != CandidateIdentity.model_validate(
                    request.model_dump(exclude={"idempotency_key"})
                ):
                    raise ServiceError(503, "internal_error")
                return result
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
        ):
            raise ServiceError(503, "internal_error", retryable=True) from None

    @traced("approval.reconcile")
    async def reconcile(self, principal: Principal, candidate_id: str) -> ApprovalResult | None:
        """Absence is conclusive ONLY after the original transaction releases its lock."""
        owner = owner_id(principal)
        try:
            async with asyncio.timeout(5), self._slots, await self._connect() as connection:
                if connection.autocommit:
                    raise ServiceError(503, "reconciliation_pending", retryable=True)
                await connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                cursor = await connection.execute(
                    "SELECT pg_try_advisory_xact_lock(%s)", (identity_lock(owner, candidate_id),)
                )
                if not (await cursor.fetchone())[0]:
                    raise ServiceError(503, "reconciliation_pending", retryable=True)
                # READ COMMITTED takes a fresh snapshot for this statement after
                # lock acquisition. Validate the binding AND audit, not a lone row.
                cursor = await connection.execute(
                    "SELECT p.plan_id,p.candidate_id,p.candidate_revision,p.content_hash, "
                    "k.fingerprint,k.idempotency_key,a.operation "
                    "FROM approved_plans p LEFT JOIN approval_idempotency k "
                    "ON k.owner_id=p.owner_id AND k.plan_id=p.plan_id "
                    "LEFT JOIN approval_audit a ON a.owner_id=p.owner_id AND a.plan_id=p.plan_id "
                    "WHERE p.owner_id=%s AND p.candidate_id=%s",
                    (owner, candidate_id),
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                result = self._result(row)
                if row[5] is None or row[6] != "approve_plan":
                    raise ServiceError(503, "reconciliation_pending", retryable=True)
                bound = ApprovalRequest(**result.candidate.model_dump(), idempotency_key=row[5])
                if row[4] != fingerprint(owner, bound):
                    raise ServiceError(503, "reconciliation_pending", retryable=True)
                return result
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
        ):
            raise ServiceError(503, "reconciliation_pending", retryable=True) from None

    @traced("approval.transaction")
    async def write(
        self, principal: Principal, request: ApprovalRequest, snapshot: Snapshot
    ) -> ApprovalResult:
        owner = owner_id(principal)
        annotate(
            profile_revision=snapshot.profile_revision,
            catalog_revision=snapshot.catalog_revision,
            validator_revision=snapshot.validator_revision,
        )
        connection = None
        commit_started = False
        try:
            async with asyncio.timeout(10), self._slots:
                connection = await self._connect()
                if connection.autocommit:
                    raise ServiceError(503, "internal_error")
                await connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                # Keep the advisory lock through COMMIT/ROLLBACK. Reconciliation
                # cannot mistake a still-running transaction for an absent result.
                await connection.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (identity_lock(owner, snapshot.candidate_id),),
                )
                cursor = await connection.execute(
                    "SELECT revision,preferences FROM profiles WHERE owner_id=%s FOR UPDATE",
                    (owner,),
                )
                row = await cursor.fetchone()
                if row is None:
                    raise ServiceError(409, "stale_profile")
                current = SavedProfile(revision=row[0], preferences=row[1])
                if current.revision != snapshot.profile_revision:
                    raise ServiceError(409, "stale_profile")
                plan = snapshot.proposal()
                if (
                    snapshot.catalog_revision != self.catalog.revision
                    or snapshot.validator_revision != VALIDATOR_VERSION
                    or request.model_dump(exclude={"idempotency_key"})
                    != snapshot.identity().model_dump()
                    or hashlib.sha256(snapshot.canonical_bytes).hexdigest() != snapshot.content_hash
                    or encode_snapshot(plan) != snapshot.canonical_bytes
                ):
                    raise ServiceError(409, "candidate_mismatch")
                if not validate_plan(plan, current.preferences, self.catalog).valid:
                    raise ServiceError(422, "invalid_request")
                result = ApprovalResult(plan_id=uuid4().hex, candidate=snapshot.identity())
                await connection.execute(
                    "INSERT INTO approved_plans (plan_id,owner_id,candidate_id,candidate_revision,"
                    "content_hash,profile_revision,catalog_revision,validator_revision,plan_bytes) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        result.plan_id,
                        owner,
                        snapshot.candidate_id,
                        snapshot.revision,
                        snapshot.content_hash,
                        snapshot.profile_revision,
                        snapshot.catalog_revision,
                        snapshot.validator_revision,
                        snapshot.canonical_bytes,
                    ),
                )
                await connection.execute(
                    "INSERT INTO approval_idempotency VALUES (%s,'approve_plan',%s,%s,%s)",
                    (owner, request.idempotency_key, fingerprint(owner, request), result.plan_id),
                )
                await connection.execute(
                    "INSERT INTO approval_audit (owner_id,plan_id,operation) "
                    "VALUES (%s,%s,'approve_plan')",
                    (owner, result.plan_id),
                )
                commit_started = True
                await connection.commit()
                return result
        except (
            Exception,
            asyncio.CancelledError,
        ):
            if commit_started:
                raise CommitUncertain() from None
            raise
        finally:
            if connection is not None:
                # close() never commits. If COMMIT was in flight, reconciliation
                # still acquires its lock; socket closure alone proves nothing.
                try:
                    async with asyncio.timeout(3):
                        await connection.close()
                except (
                    Exception,
                    asyncio.CancelledError,
                ):
                    if commit_started:
                        raise CommitUncertain() from None
                    raise

    @staticmethod
    def _plan_row(row) -> PlanRow:
        plan = PlanProposal.model_validate_json(bytes(row[8]))
        if hashlib.sha256(bytes(row[8])).hexdigest() != row[4] or encode_snapshot(plan) != bytes(
            row[8]
        ):
            raise ServiceError(503, "internal_error")
        saved = SavedPlan(
            approval=ApprovalResult(
                plan_id=row[0],
                candidate=CandidateIdentity(
                    candidate_id=row[2], revision=row[3], content_hash=row[4]
                ),
            ),
            plan=plan,
            versions=ContextVersions(
                profile_revision=row[5], catalog_revision=row[6], validator_revision=row[7]
            ),
        )
        return PlanRow(row[1], row[0], saved.model_dump_json().encode())

    @traced("plan.read")
    async def _read(self, owner, limit, plan_id=None, cursor=None):
        if owner not in (Principal.A.value, Principal.B.value):
            raise ServiceError(401, "unauthorized")
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ServiceError(422, "invalid_request")
        try:
            for value in (plan_id, cursor):
                if value is not None:
                    TypeAdapter(Identifier).validate_python(value)
        except ValidationError:
            raise ServiceError(422, "invalid_request") from None
        try:
            async with asyncio.timeout(10), self._slots, await self._connect() as connection:
                query = (
                    "SELECT plan_id,owner_id,candidate_id,candidate_revision,content_hash,"
                    "profile_revision,catalog_revision,validator_revision,plan_bytes "
                    "FROM approved_plans WHERE owner_id=%s"
                )
                args = [owner]
                if plan_id is not None:
                    query += " AND plan_id=%s"
                    args.append(plan_id)
                if cursor is not None:
                    query += " AND plan_id>%s"
                    args.append(cursor)
                query += " ORDER BY plan_id ASC LIMIT %s"
                args.append(limit)
                result = await connection.execute(query, args)
                return [self._plan_row(row) for row in await result.fetchall()]
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
            ValueError,
        ):
            raise ServiceError(503, "internal_error", retryable=True) from None

    async def get_owned(self, owner: str, plan_id: str) -> PlanRow | None:
        rows = await self._read(owner, 1, plan_id=plan_id)
        return rows[0] if rows else None

    async def list_owned(self, owner: str, limit: int, cursor: str | None):
        return await self._read(owner, limit, cursor=cursor)
