"""Reduced in-memory model of two approval obligations ONLY.

No PostgreSQL, identity service, candidate lifecycle or real commit is implemented.
F1-06 must run equivalent scenarios against its actual service and PostgreSQL.
"""

import asyncio
from dataclasses import dataclass, field


class ReconciliationPending(Exception):
    pass


class UncertainCommit(Exception):
    pass


class CommitRolledBack(Exception):
    pass


@dataclass
class Reference:
    guard: asyncio.Lock = field(default_factory=asyncio.Lock)
    entered_commit: asyncio.Event = field(default_factory=asyncio.Event)
    release_commit: asyncio.Event = field(default_factory=asyncio.Event)
    cancellation_observed: asyncio.Event = field(default_factory=asyncio.Event)
    guard_wait_observed: asyncio.Event = field(default_factory=asyncio.Event)
    records: dict = field(default_factory=dict)
    state: str = "ready"
    commit_calls: int = 0
    report_uncertain: bool = False
    reconciliation_available: bool = True
    actually_commits: bool = True

    def lookup(self, owner, key, fingerprint):
        record = self.records.get((owner, key))
        if record is not None and record[0] != fingerprint:
            raise ValueError("idempotency_mismatch")
        return record

    async def reference_commit_and_finalize(self, owner, key, fingerprint):
        self.commit_calls += 1
        self.entered_commit.set()
        await self.release_commit.wait()
        if self.actually_commits:
            self.records[owner, key] = (fingerprint, "synthetic-plan")
        if self.report_uncertain:
            self.state = "unresolved"
            if not self.reconciliation_available:
                raise ReconciliationPending
            # Reference authoritative reconciliation; no actual database query.
            committed = self.lookup(owner, key, fingerprint)
            if committed is None:
                self.state = "ready"
                raise CommitRolledBack
        self.state = "approved"
        return self.lookup(owner, key, fingerprint)

    async def approve_reference(
        self, owner="owner-a", key="key-a", fingerprint="hash-a", after_initial_read=None
    ):
        result = self.lookup(owner, key, fingerprint)
        if result is not None:
            return result
        if after_initial_read:
            await after_initial_read()
        if self.guard.locked():
            self.guard_wait_observed.set()
        async with self.guard:
            # Essential: another request may have committed during guard wait.
            result = self.lookup(owner, key, fingerprint)
            if result is not None:
                return result
            if self.state == "unresolved":
                raise ReconciliationPending
            if self.state != "ready":
                raise ValueError("candidate_already_approved")
            finalizer = asyncio.create_task(
                self.reference_commit_and_finalize(owner, key, fingerprint)
            )
            cancelled = False
            while True:
                try:
                    result = await asyncio.shield(finalizer)
                    break
                except asyncio.CancelledError:
                    cancelled = True
                    self.cancellation_observed.set()
                    # Keep ownership and await finalization; shield alone is insufficient.
            if cancelled:
                raise asyncio.CancelledError
            return result

    async def can_publish_revision(self, waiting=None):
        if waiting:
            waiting.set()
        async with self.guard:
            return self.state == "ready"
