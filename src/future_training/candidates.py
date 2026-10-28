"""Single-process transient lifecycle and guarded durable-approval finalization seams."""

import asyncio
import hashlib
import json
import math
import time
from collections import OrderedDict
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from future_training.domain.catalog import Catalog
from future_training.domain.validator import VALIDATOR_VERSION
from future_training.errors import ServiceError
from future_training.identity import Principal, owner_id
from future_training.observability import traced, validate_plan
from future_training.persistence.profiles import ProfileAccess
from future_training.schemas import (
    ApprovalRequest,
    ApprovalResult,
    CandidateIdentity,
    CandidateLimits,
    ContextVersions,
    Identifier,
    PlanProposal,
)

_IDENTIFIER = TypeAdapter(Identifier)


def encode_snapshot(plan: PlanProposal) -> bytes:
    return json.dumps(
        plan.model_dump(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


@dataclass(frozen=True)
class Snapshot:
    candidate_id: str
    revision: int
    content_hash: str
    canonical_bytes: bytes = field(repr=False)
    profile_revision: int
    catalog_revision: str
    validator_revision: str
    expires_at_monotonic: float

    def identity(self) -> CandidateIdentity:
        return CandidateIdentity(
            candidate_id=self.candidate_id, revision=self.revision, content_hash=self.content_hash
        )

    def versions(self) -> ContextVersions:
        return ContextVersions(
            profile_revision=self.profile_revision,
            catalog_revision=self.catalog_revision,
            validator_revision=self.validator_revision,
        )

    def proposal(self) -> PlanProposal:
        return PlanProposal.model_validate_json(self.canonical_bytes)


@dataclass
class _Lineage:
    lineage_id: str
    owner: Principal
    current: Snapshot | None
    aliases: dict[str, float]
    guard: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending: str | None = None
    revisions: int = 0
    expired: bool = False
    unresolved: bool = False
    approved: bool = False
    reconciliation_request: bytes | None = None


@dataclass(frozen=True)
class Reservation:
    lineage_id: str
    candidate_id: str
    token: str = field(repr=False)


class GuardedLineage:
    """Coordinator seam. Acquire → recheck durable key → check readiness.

    Memory transitions remain task-affine and guarded. Only the approval
    coordinator resolves commit uncertainty against authoritative PostgreSQL.
    """

    def __init__(self, store, lineage, candidate_id):
        self._store = store
        self._lineage = lineage
        self._candidate_id = candidate_id
        self.acquired_at = store._now()
        self._task = asyncio.current_task()
        self._active = True

    def _owned(self):
        if not self._active or asyncio.current_task() is not self._task:
            raise RuntimeError("Lineage guard used outside its owning context")

    @property
    def owner(self) -> Principal:
        self._owned()
        return self._lineage.owner

    def check_ready(
        self, identity: CandidateIdentity | None = None, *, use_acquisition_time: bool = False
    ) -> Snapshot:
        self._owned()
        line = self._lineage
        if line.unresolved:
            raise ServiceError(503, "reconciliation_pending", retryable=True)
        if line.expired or line.current is None:
            raise ServiceError(410, "candidate_expired")
        now = self.acquired_at if use_acquisition_time else self._store._now()
        if now >= line.aliases[self._candidate_id]:
            if self._candidate_id == line.current.candidate_id:
                self._store._expire_locked(line)
            raise ServiceError(410, "candidate_expired")
        if self._candidate_id != line.current.candidate_id:
            raise ServiceError(409, "candidate_superseded")
        if identity is not None:
            try:
                identity = CandidateIdentity.model_validate(identity.model_dump(warnings=False))
            except (
                ValidationError,
                AttributeError,
            ):
                raise ServiceError(422, "invalid_request") from None
            if identity.candidate_id != line.current.candidate_id:
                raise ServiceError(409, "candidate_superseded")
            if identity != line.current.identity():
                raise ServiceError(409, "candidate_mismatch")
        if line.approved:
            raise ServiceError(409, "candidate_already_approved")
        return line.current

    def block_for_reconciliation(self, request: ApprovalRequest | None = None):
        self._owned()
        self._lineage.unresolved = True
        if request is not None:
            self._lineage.reconciliation_request = request.model_dump_json().encode()

    def pending_approval(self) -> ApprovalRequest | None:
        self._owned()
        data = self._lineage.reconciliation_request
        return ApprovalRequest.model_validate_json(data) if data else None

    def mark_approved(self):
        self._owned()
        self._lineage.approved = True
        self._lineage.unresolved = False
        self._lineage.reconciliation_request = None
        self._lineage.pending = None

    def mark_rolled_back(self):
        self._owned()
        self._lineage.unresolved = False
        self._lineage.reconciliation_request = None

    async def reconcile_if_needed(self):
        self._owned()
        if self._lineage.unresolved:
            if self._store._reconciler is None or self.pending_approval() is None:
                raise ServiceError(503, "reconciliation_pending", retryable=True)
            await self._store._reconciler(self)


class CandidateStore:
    def __init__(
        self,
        profiles: ProfileAccess,
        catalog: Catalog,
        *,
        clock: Callable[[], float] = time.monotonic,
        new_id: Callable[[], str] = lambda: uuid4().hex,
    ):
        self._profiles = profiles
        self._catalog = catalog
        self._clock = clock
        self._new_id = new_id
        self._limits = CandidateLimits()
        self._lineages: dict[str, _Lineage] = {}
        self._aliases: dict[str, _Lineage] = {}
        self._expired: OrderedDict[str, Principal] = OrderedDict()
        self._bytes = 0
        self._last_time = 0.0
        self._reconciler = None

    def set_reconciler(self, reconciler):
        self._reconciler = reconciler

    async def note_committed(self, principal: Principal, result: ApprovalResult):
        """Optional memory repair on a durable retry; never require a transient ID.

        Skip a busy/missing lineage: its current holder already owns finalization
        or will reconcile before allowing another operation. No unlocked mutation.
        """
        try:
            line = self._find(principal, result.candidate.candidate_id)
        except ServiceError:
            return
        if line.guard.locked():
            return
        async with self.lineage_guard(principal, result.candidate.candidate_id) as guard:
            if line.current and line.current.identity() == result.candidate:
                guard.mark_approved()

    def _now(self):
        value = self._clock()
        if not math.isfinite(value) or value < self._last_time:
            raise RuntimeError("Candidate clock must be finite and monotonic")
        self._last_time = value
        return value

    def _id(self):
        for _ in range(8):
            value = self._new_id()
            try:
                value = _IDENTIFIER.validate_python(value)
            except ValidationError:
                raise ServiceError(503, "internal_error") from None
            if (
                value not in self._aliases
                and value not in self._lineages
                and value not in self._expired
            ):
                return value
        raise ServiceError(503, "internal_error")

    def _find(self, principal: Principal, candidate_id: str) -> _Lineage:
        owner_id(principal)
        line = self._aliases.get(candidate_id)
        if line is None or line.owner != principal:
            if self._expired.get(candidate_id) == principal:
                raise ServiceError(410, "candidate_expired")
            raise ServiceError(404, "not_found")
        return line

    @asynccontextmanager
    async def lineage_guard(self, principal: Principal, candidate_id: str):
        line = self._find(principal, candidate_id)
        async with line.guard:
            guard = GuardedLineage(self, line, candidate_id)
            try:
                # Deliberately no status/expiry rejection before yielding: the
                # approval coordinator MUST re-read committed idempotency here first.
                yield guard
            finally:
                guard._active = False

    def _expire_locked(self, line: _Lineage):
        if line.expired:
            return
        if line.current:
            self._bytes -= len(line.current.canonical_bytes)
        line.current = None
        line.expired = True
        line.pending = None
        self._lineages.pop(line.lineage_id, None)
        for alias in sorted(line.aliases):
            self._aliases.pop(alias, None)
            self._expired[alias] = line.owner
        # Bounded identity-only tombstones; no draft bytes retained after expiry.
        while len(self._expired) > 2 * self._limits.lineages:
            self._expired.popitem(last=False)

    async def expire(self):
        for line in list(self._lineages.values()):
            if line.guard.locked() or line.unresolved:
                continue
            async with line.guard:
                if line.current and self._now() >= line.current.expires_at_monotonic:
                    self._expire_locked(line)

    def stats(self):
        return {
            "lineages": len(self._lineages),
            "payload_bytes": self._bytes,
            "aliases": len(self._aliases),
            "expired_ids": len(self._expired),
        }

    def _freeze(self, raw: object, profile):
        if not validate_plan(raw, profile.preferences, self._catalog).valid:
            raise ServiceError(422, "invalid_request")
        if isinstance(raw, PlanProposal):
            raw = raw.model_dump(warnings=False)
        plan = PlanProposal.model_validate(raw)
        encoded = encode_snapshot(plan)
        if len(encoded) > self._limits.candidate_bytes:
            raise ServiceError(413, "invalid_request")
        return encoded

    async def _fresh_profile(self, principal, snapshot):
        profile = await self._profiles.get(principal)
        if profile.revision != snapshot.profile_revision:
            raise ServiceError(409, "stale_profile")
        if (
            snapshot.catalog_revision != self._catalog.revision
            or snapshot.validator_revision != VALIDATOR_VERSION
        ):
            raise ServiceError(409, "candidate_mismatch")
        return profile

    @traced("candidate.initial")
    async def publish_initial(
        self,
        principal: Principal,
        raw: object,
        *,
        expected_profile_revision: int,
        before_publish: Callable[[], None] | None = None,
    ):
        owner_id(principal)
        if type(expected_profile_revision) is not int or expected_profile_revision < 1:
            raise ServiceError(422, "invalid_request")
        # Sweep before the final profile read: no await may separate that read,
        # validation and insertion (a concurrent Save could otherwise interleave).
        await self.expire()
        profile = await self._profiles.get(principal)
        if profile.revision != expected_profile_revision:
            raise ServiceError(409, "stale_profile")
        encoded = self._freeze(raw, profile)
        if (
            len(self._lineages) >= self._limits.lineages
            or self._bytes + len(encoded) > self._limits.store_bytes
        ):
            raise ServiceError(429, "capacity_exceeded", retryable=True)
        snapshot = Snapshot(
            self._id(),
            1,
            hashlib.sha256(encoded).hexdigest(),
            encoded,
            profile.revision,
            self._catalog.revision,
            VALIDATOR_VERSION,
            self._now() + self._limits.ttl_seconds,
        )
        lineage_id = self._id()
        line = _Lineage(
            lineage_id, principal, snapshot, {snapshot.candidate_id: snapshot.expires_at_monotonic}
        )
        if before_publish is not None:
            before_publish()
        # No await in the capacity check/insertion critical section.
        self._lineages[lineage_id] = line
        self._aliases[snapshot.candidate_id] = line
        self._bytes += len(encoded)
        return snapshot

    async def get(self, principal: Principal, candidate_id: str) -> Snapshot:
        async with self.lineage_guard(principal, candidate_id) as guard:
            await guard.reconcile_if_needed()
            snapshot = guard.check_ready()
            if candidate_id != snapshot.candidate_id:
                raise ServiceError(409, "candidate_superseded")
            return snapshot

    @asynccontextmanager
    async def revision(self, principal: Principal, identity: CandidateIdentity):
        async with self.lineage_guard(principal, identity.candidate_id) as guard:
            await guard.reconcile_if_needed()
            snapshot = guard.check_ready(identity)
            line = guard._lineage
            if line.pending:
                raise ServiceError(409, "revision_in_progress")
            if line.revisions >= 1:
                raise ServiceError(409, "candidate_mismatch")
            await self._fresh_profile(principal, snapshot)
            guard.check_ready(identity)
            token = self._id()
            line.pending = token
            reservation = Reservation(line.lineage_id, snapshot.candidate_id, token)
        try:
            yield reservation
        finally:
            task = asyncio.create_task(self._release(principal, reservation))
            cancelled = False
            while True:
                try:
                    await asyncio.shield(task)
                    break
                except asyncio.CancelledError:
                    cancelled = True
                    if task.done():
                        task.result()
            if cancelled:
                raise asyncio.CancelledError

    async def _release(self, principal, reservation):
        line = self._lineages.get(reservation.lineage_id)
        if line is None or line.owner != principal:
            return
        async with line.guard:
            if line.pending == reservation.token:
                line.pending = None

    @traced("candidate.revision")
    async def publish_revision(
        self,
        principal: Principal,
        reservation: Reservation,
        raw: object,
        *,
        before_publish: Callable[[], None] | None = None,
    ):
        async with self.lineage_guard(principal, reservation.candidate_id) as guard:
            await guard.reconcile_if_needed()
            snapshot = guard.check_ready()
            line = guard._lineage
            if (
                line.pending is None
                or line.revisions >= 1
                or line.lineage_id != reservation.lineage_id
                or line.pending != reservation.token
                or snapshot.candidate_id != reservation.candidate_id
            ):
                raise ServiceError(409, "candidate_mismatch")
            profile = await self._fresh_profile(principal, snapshot)
            guard.check_ready()
            encoded = self._freeze(raw, profile)
            total = self._bytes - len(snapshot.canonical_bytes) + len(encoded)
            if total > self._limits.store_bytes:
                raise ServiceError(429, "capacity_exceeded", retryable=True)
            updated = Snapshot(
                self._id(),
                snapshot.revision + 1,
                hashlib.sha256(encoded).hexdigest(),
                encoded,
                profile.revision,
                self._catalog.revision,
                VALIDATOR_VERSION,
                self._now() + self._limits.ttl_seconds,
            )
            if before_publish is not None:
                before_publish()
            line.current = updated
            line.aliases[updated.candidate_id] = updated.expires_at_monotonic
            self._aliases[updated.candidate_id] = line
            line.pending = None
            line.revisions += 1
            self._bytes = total
            return updated
