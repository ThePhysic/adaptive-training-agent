"""Single-process approval coordinator. SQL is authoritative; drafts remain transient."""

import asyncio

import psycopg
from pydantic import ValidationError

from future_training.candidates import CandidateStore, GuardedLineage
from future_training.domain.validator import VALIDATOR_VERSION
from future_training.errors import ServiceError
from future_training.identity import Principal, owner_id
from future_training.observability import traced, validate_plan
from future_training.persistence.approvals import CommitUncertain, PostgresApprovals
from future_training.schemas import ApprovalRequest, ApprovalResult, CandidateIdentity


async def finish_owned(coroutine):
    """Shield AND await an owned critical task, including repeated client cancellation."""
    task = asyncio.create_task(coroutine)
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
        except Exception:
            break
    if cancelled:
        # Consume any failure but preserve caller cancellation, never detach work.
        if not task.cancelled():
            task.exception()
        raise asyncio.CancelledError
    return task.result()


class Approvals:
    def __init__(self, candidates: CandidateStore, database: PostgresApprovals):
        self.candidates = candidates
        self.database = database
        candidates.set_reconciler(self._reconcile)

    async def _reconcile(self, guard: GuardedLineage) -> ApprovalResult | None:
        request = guard.pending_approval()
        if request is None:
            raise ServiceError(503, "reconciliation_pending", retryable=True)
        # Ownership is from the guarded lineage, never from a request/tool field.
        principal = guard.owner
        try:
            result = await self.database.reconcile(principal, request.candidate_id)
            if result is None:
                guard.mark_rolled_back()
            else:
                if result.candidate.model_dump() != request.model_dump(exclude={"idempotency_key"}):
                    raise ServiceError(503, "reconciliation_pending", retryable=True)
                guard.mark_approved()
            return result
        except Exception:
            guard.block_for_reconciliation(request)
            raise ServiceError(503, "reconciliation_pending", retryable=True) from None

    @traced("approval")
    async def approve(self, principal: Principal, request: ApprovalRequest) -> ApprovalResult:
        owner_id(principal)
        try:
            request = ApprovalRequest.model_validate(request.model_dump(warnings=False))
        except (
            AttributeError,
            ValidationError,
        ):
            raise ServiceError(422, "invalid_request") from None
        committed = await self.database.committed(principal, request)
        if committed is not None:
            await self.candidates.note_committed(principal, committed)
            return committed
        return await finish_owned(self._critical(principal, request))

    async def _critical(self, principal: Principal, request: ApprovalRequest) -> ApprovalResult:
        try:
            # Bound waiting for a busy lineage without applying TTL until the
            # guard is ACTUALLY acquired. The transaction runs under its own bound.
            async with asyncio.timeout(5):
                context = self.candidates.lineage_guard(principal, request.candidate_id)
                try:
                    guard = await context.__aenter__()
                except ServiceError as error:
                    if error.status in (404, 410):
                        # A winner can commit and be swept between the initial
                        # lookup and guard resolution. Durable retries still win.
                        committed = await self.database.committed(principal, request)
                        if committed is not None:
                            return committed
                    raise
            try:
                # MUST precede every transient-state rejection after waiting.
                committed = await self.database.committed(principal, request)
                if committed is not None:
                    guard.mark_approved()
                    return committed
                needed_reconciliation = guard.pending_approval() is not None
                await guard.reconcile_if_needed()
                # Reconciliation may have recovered a key binding. Re-read it
                # before approved/expired-state rejection as well.
                if needed_reconciliation:
                    committed = await self.database.committed(principal, request)
                    if committed is not None:
                        return committed
                snapshot = guard.check_ready(
                    CandidateIdentity.model_validate(
                        request.model_dump(exclude={"idempotency_key"})
                    ),
                    use_acquisition_time=True,
                )
                if (
                    snapshot.catalog_revision != self.database.catalog.revision
                    or snapshot.validator_revision != VALIDATOR_VERSION
                ):
                    raise ServiceError(409, "candidate_mismatch")
                if not validate_plan(
                    snapshot.proposal(), snapshot.proposal().profile, self.database.catalog
                ).valid:
                    raise ServiceError(422, "invalid_request")
                guard.block_for_reconciliation(request)
                try:
                    result = await self.database.write(principal, request, snapshot)
                except CommitUncertain:
                    result = await self._reconcile(guard)
                    if result is None:
                        raise ServiceError(503, "internal_error", retryable=True) from None
                    return result
                except psycopg.errors.UniqueViolation:
                    # The failed transaction was closed without COMMIT. Classify
                    # using fresh durable owner-scoped state, never partial rows.
                    await self._reconcile(guard)
                    committed = await self.database.committed(principal, request)
                    if committed is not None:
                        return committed
                    raise ServiceError(409, "candidate_already_approved") from None
                except (
                    psycopg.Error,
                    TimeoutError,
                    ServiceError,
                    ValidationError,
                ):
                    # This attempt never invoked COMMIT. Still reconcile the
                    # identity before reopening: SQL may already contain a winner,
                    # and a failed close can leave transaction locks outstanding.
                    recovered = await self._reconcile(guard)
                    if recovered is not None:
                        committed = await self.database.committed(principal, request)
                        if committed is not None:
                            return committed
                        raise ServiceError(409, "candidate_already_approved") from None
                    raise
                except Exception:
                    # A trusted adapter/finalization fault cannot silently reopen
                    # the lineage. Try authoritative reconciliation, else quarantine.
                    recovered = await self._reconcile(guard)
                    if recovered is None:
                        raise ServiceError(503, "internal_error", retryable=True) from None
                    return recovered
                try:
                    guard.mark_approved()
                except Exception:
                    # Durable commit already succeeded. Recovery is still guarded.
                    guard.block_for_reconciliation(request)
                    recovered = await self._reconcile(guard)
                    if recovered is None:
                        raise ServiceError(503, "reconciliation_pending", retryable=True) from None
                    return recovered
                return result
            finally:
                await context.__aexit__(None, None, None)
        except ServiceError:
            raise
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
        ):
            raise ServiceError(503, "internal_error", retryable=True) from None
