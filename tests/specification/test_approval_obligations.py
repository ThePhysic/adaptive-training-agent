"""Reference-model proofs; NOT tests of an implemented approval transaction."""

import asyncio

import pytest

from .approval_reference import CommitRolledBack, ReconciliationPending, Reference

pytestmark = pytest.mark.contract_spec


@pytest.mark.parametrize("second_fingerprint", ["hash-a", "hash-b"])
async def test_concurrent_initial_misses_recheck_key_after_guard_wait(second_fingerprint):
    model = Reference()
    first_read, second_read = asyncio.Event(), asyncio.Event()
    release_first, release_second = asyncio.Event(), asyncio.Event()

    async def first_barrier():
        first_read.set()
        await release_first.wait()

    async def second_barrier():
        second_read.set()
        await release_second.wait()

    first = asyncio.create_task(model.approve_reference(after_initial_read=first_barrier))
    second = asyncio.create_task(
        model.approve_reference(fingerprint=second_fingerprint, after_initial_read=second_barrier)
    )
    await first_read.wait()
    await second_read.wait()  # Both observed no committed result.
    release_first.set()
    await model.entered_commit.wait()  # First owns the lineage through finalization.
    release_second.set()
    await model.guard_wait_observed.wait()
    model.release_commit.set()
    result = await first
    if second_fingerprint == "hash-a":
        assert await second == result
    else:
        with pytest.raises(ValueError, match="idempotency_mismatch"):
            await second
    assert model.commit_calls == 1


async def test_repeated_cancellation_holds_guard_until_memory_finalization():
    model = Reference()
    approval = asyncio.create_task(model.approve_reference())
    await model.entered_commit.wait()
    for _ in range(2):
        model.cancellation_observed.clear()
        approval.cancel()
        await model.cancellation_observed.wait()
        assert model.guard.locked()
        assert not approval.done()
    waiting = asyncio.Event()
    revision = asyncio.create_task(model.can_publish_revision(waiting))
    await waiting.wait()
    assert not revision.done()
    model.release_commit.set()
    with pytest.raises(asyncio.CancelledError):
        await approval
    assert not await revision
    assert model.state == "approved"
    assert model.records["owner-a", "key-a"][1] == "synthetic-plan"


async def test_uncertain_commit_reconciles_to_approved():
    model = Reference(report_uncertain=True)
    model.release_commit.set()
    assert await model.approve_reference() == ("hash-a", "synthetic-plan")
    assert model.state == "approved"


async def test_unavailable_reconciliation_blocks_new_approval_and_revision():
    model = Reference(report_uncertain=True, reconciliation_available=False)
    model.release_commit.set()
    with pytest.raises(ReconciliationPending):
        await model.approve_reference()
    assert model.state == "unresolved"
    assert not await model.can_publish_revision()
    with pytest.raises(ReconciliationPending):
        await model.approve_reference(key="new-key")
    assert model.commit_calls == 1


async def test_reconciled_rollback_can_be_retried_without_claiming_success():
    model = Reference(report_uncertain=True, actually_commits=False)
    model.release_commit.set()
    with pytest.raises(CommitRolledBack):
        await model.approve_reference()
    assert model.state == "ready"
    assert model.records == {}
