"""Explicit opt-in/shutdown and unresolved admission. No live-capable factory."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from future_training.agent.budget import AgentFault

ENDPOINT = "https://api.openai.com/v1/responses"
INPUT_BOUND_PROVEN = False


@dataclass(frozen=True)
class LivePermit:
    """A proposed capability, never loaded from credentials or created by startup."""

    endpoint: str
    model: str
    expires_at: datetime
    grant_id: str
    owner_approved: bool = False


@dataclass
class LiveGate:
    enabled: bool = False
    permit: LivePermit | None = field(default=None, repr=False)
    _stopped: bool = field(default=False, init=False, repr=False)
    _tasks: set = field(default_factory=set, init=False, repr=False)

    def check(self):
        if self._stopped or not self.enabled or self.permit is None:
            raise AgentFault("live_provider_disabled")
        permit = self.permit
        if (
            not permit.owner_approved
            or permit.endpoint != ENDPOINT
            or permit.model != "gpt-6.1-sol"
            or not permit.grant_id
            or permit.expires_at.tzinfo is None
            or permit.expires_at <= datetime.now(UTC)
        ):
            raise AgentFault("live_provider_disabled")
        # Deliberately unconditional in this unit: there is no approved proof of
        # live authorization or verified provider pricing/privacy. A-C are offline-only.
        raise AgentFault("real_input_admission_unproven")

    def track(self, task: asyncio.Task):
        """Shutdown supervision can be exercised offline without enabling admission."""
        if self._stopped:
            task.cancel()
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    @property
    def stopped(self):
        return self._stopped

    def untrack(self, task):
        self._tasks.discard(task)

    async def stop(self, *, ledger=None, project=None):
        self._stopped = True
        owner = asyncio.current_task()
        owned = owner in self._tasks

        async def shutdown():
            try:
                if ledger is not None:
                    await ledger.stop(project)
            finally:
                tasks = tuple(t for t in self._tasks if t is not owner)
                for task in tasks:
                    task.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

        task = asyncio.create_task(shutdown())
        cancelled = False
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                cancelled = True
            except Exception:
                if not cancelled and not owned:
                    raise
        if owned:
            self._tasks.discard(owner)
        if cancelled or owned:
            if not task.cancelled():
                task.exception()  # Observe failure; its ledger fence remains authoritative.
            raise asyncio.CancelledError
        task.result()
