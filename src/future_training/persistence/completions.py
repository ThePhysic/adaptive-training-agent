"""Owner-scoped immutable session Submit; PostgreSQL alone owns records and keys."""

import asyncio
import hashlib
import json
from uuid import uuid4

import psycopg
from pydantic import TypeAdapter, ValidationError

from future_training.approval import finish_owned
from future_training.candidates import encode_snapshot
from future_training.completion_contracts import SessionIndex, SessionRecord, SessionSubmission
from future_training.errors import ServiceError
from future_training.identity import owner_id
from future_training.observability import traced
from future_training.persistence.profiles import connect_local
from future_training.schemas import Identifier, PlanProposal

COLUMNS = (
    "r.record_id,r.plan_id,r.day_index,r.revision,r.plan_revision,"
    "r.plan_content_hash,r.status,r.effort,r.rating"
)


def fingerprint(owner, plan_id, day_index, request):
    encoded = json.dumps(
        {
            "owner": owner,
            "operation": "submit_session",
            "plan_id": plan_id,
            "day_index": day_index,
            **request.model_dump(exclude={"idempotency_key"}),
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def lock_id(owner, kind, *identity):
    encoded = json.dumps(["submit_session", owner, kind, *identity], separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(encoded).digest()[:8], signed=True)


def record(row):
    return SessionRecord(
        **dict(
            zip(
                (
                    "record_id",
                    "plan_id",
                    "day_index",
                    "revision",
                    "plan_revision",
                    "plan_content_hash",
                    "status",
                    "effort",
                    "rating",
                ),
                row,
                strict=True,
            )
        )
    )


class PostgresCompletions:
    def __init__(self, *, connect=connect_local):
        self._connect = connect
        self._slots = asyncio.Semaphore(4)

    @staticmethod
    def identity(principal, plan_id, day_index=None):
        owner = owner_id(principal)
        try:
            TypeAdapter(Identifier).validate_python(plan_id)
            if day_index is not None:
                TypeAdapter(SessionIndex).validate_python(day_index)
        except ValidationError:
            raise ServiceError(422, "invalid_request") from None
        return owner

    @staticmethod
    async def plan(connection, owner, plan_id, day_index=None, *, lock=False):
        cursor = await connection.execute(
            "SELECT candidate_revision,content_hash,plan_bytes FROM approved_plans "
            "WHERE owner_id=%s AND plan_id=%s" + (" FOR KEY SHARE" if lock else ""),
            (owner, plan_id),
        )
        row = await cursor.fetchone()
        if row is None:
            raise ServiceError(404, "not_found")
        raw = bytes(row[2])
        plan = PlanProposal.model_validate_json(raw)
        if encode_snapshot(plan) != raw or hashlib.sha256(raw).hexdigest() != row[1]:
            raise ServiceError(503, "internal_error")
        if day_index is not None and day_index not in {day.day_index for day in plan.days}:
            raise ServiceError(422, "invalid_request")
        return row[0], row[1]

    @traced("completion.submit")
    async def submit(self, principal, plan_id, day_index, request):
        owner = self.identity(principal, plan_id, day_index)
        try:
            request = SessionSubmission.model_validate(request.model_dump(warnings=False))
        except (
            ValidationError,
            AttributeError,
        ):
            raise ServiceError(422, "invalid_request") from None
        # Explicit writes may finish after disconnect; caller cancellation is still
        # propagated after all owned work settles. No memory or candidate finalization.
        return await finish_owned(self._write(owner, plan_id, day_index, request))

    @traced("completion.transaction")
    async def _write(self, owner, plan_id, day_index, request):
        connection, commit_started = None, False
        try:
            async with asyncio.timeout(10), self._slots:
                connection = await self._connect()
                if connection.autocommit:
                    raise ServiceError(503, "internal_error")
                await connection.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                await connection.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (lock_id(owner, "key", request.idempotency_key),),
                )
                cursor = await connection.execute(
                    "SELECT k.fingerprint," + COLUMNS + " FROM session_idempotency k "
                    "JOIN session_records r ON r.owner_id=k.owner_id AND r.record_id=k.record_id "
                    "WHERE k.owner_id=%s AND k.operation='submit_session' AND k.idempotency_key=%s",
                    (owner, request.idempotency_key),
                )
                found = await cursor.fetchone()
                expected = fingerprint(owner, plan_id, day_index, request)
                if found is not None:
                    if found[0] != expected:
                        raise ServiceError(409, "idempotency_mismatch")
                    return record(found[1:])
                version, digest = await self.plan(connection, owner, plan_id, day_index, lock=True)
                if version != request.plan_revision or digest != request.plan_content_hash:
                    raise ServiceError(409, "plan_mismatch")
                await connection.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (lock_id(owner, "session", plan_id, day_index),),
                )
                cursor = await connection.execute(
                    "SELECT 1 FROM session_records "
                    "WHERE owner_id=%s AND plan_id=%s AND day_index=%s",
                    (owner, plan_id, day_index),
                )
                if await cursor.fetchone() is not None:
                    raise ServiceError(409, "session_already_recorded")
                result = SessionRecord(
                    record_id=uuid4().hex,
                    plan_id=plan_id,
                    day_index=day_index,
                    **request.model_dump(exclude={"expected_revision", "idempotency_key"}),
                )
                await connection.execute(
                    "INSERT INTO session_records (record_id,owner_id,plan_id,day_index,"
                    "plan_revision,plan_content_hash,status,effort,rating) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        result.record_id,
                        owner,
                        plan_id,
                        day_index,
                        result.plan_revision,
                        result.plan_content_hash,
                        result.status,
                        result.effort,
                        result.rating,
                    ),
                )
                await connection.execute(
                    "INSERT INTO session_idempotency VALUES (%s,'submit_session',%s,%s,%s)",
                    (owner, request.idempotency_key, expected, result.record_id),
                )
                commit_started = True
                await connection.commit()
                return result
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
            ValueError,
        ):
            raise ServiceError(
                503,
                "reconciliation_pending" if commit_started else "internal_error",
                retryable=True,
            ) from None
        finally:
            if connection is not None:
                try:
                    async with asyncio.timeout(3):
                        await connection.close()
                except (
                    psycopg.Error,
                    TimeoutError,
                ):
                    raise ServiceError(
                        503,
                        "reconciliation_pending" if commit_started else "internal_error",
                        retryable=True,
                    ) from None

    @traced("completion.read")
    async def read(self, principal, plan_id, day_index=None):
        owner = self.identity(principal, plan_id, day_index)
        try:
            async with asyncio.timeout(10), self._slots, await self._connect() as connection:
                await connection.execute("SET TRANSACTION READ ONLY")
                version, digest = await self.plan(connection, owner, plan_id, day_index)
                query = (
                    "SELECT "
                    + COLUMNS
                    + " FROM session_records r WHERE r.owner_id=%s AND r.plan_id=%s"
                )
                args = [owner, plan_id]
                if day_index is not None:
                    query += " AND r.day_index=%s"
                    args.append(day_index)
                cursor = await connection.execute(query + " ORDER BY r.day_index LIMIT 4", args)
                records = [record(row) for row in await cursor.fetchall()]
                if any(
                    row.plan_revision != version or row.plan_content_hash != digest
                    for row in records
                ):
                    raise ServiceError(503, "internal_error")
                if day_index is not None:
                    if not records:
                        raise ServiceError(404, "not_found")
                    return records[0]
                return records
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
            ValueError,
        ):
            raise ServiceError(503, "internal_error", retryable=True) from None
