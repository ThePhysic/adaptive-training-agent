import asyncio
import hashlib
from dataclasses import FrozenInstanceError, replace
from itertools import count

import pytest
from profile_doubles import MemoryProfiles

from future_training.candidates import CandidateStore
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.schemas import CandidateLimits, ProfileSaveRequest


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
async def setup_store(profile):
    profiles = MemoryProfiles()
    for principal in Principal:
        await profiles.save(principal, ProfileSaveRequest(expected_revision=0, preferences=profile))
    clock = Clock()
    ids = count(1)
    catalog = load_catalog()
    store = CandidateStore(profiles, catalog, clock=clock, new_id=lambda: f"opaque-{next(ids)}")
    proposal = plan_week(profile, catalog).plan
    snapshot = await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
    return store, profiles, clock, proposal, snapshot


async def test_immutable_bytes_hash_copies_and_ownership(setup_store):
    store, _, _, proposal, snapshot = setup_store
    assert hashlib.sha256(snapshot.canonical_bytes).hexdigest() == snapshot.content_hash
    with pytest.raises(FrozenInstanceError):
        snapshot.content_hash = "b" * 64
    proposal.days.clear()
    copy = snapshot.proposal()
    copy.days.clear()
    assert len((await store.get(Principal.A, snapshot.candidate_id)).proposal().days) == 2
    for principal, candidate in [(Principal.B, snapshot.candidate_id), (Principal.B, "unknown")]:
        with pytest.raises(ServiceError) as error:
            await store.get(principal, candidate)
        assert (error.value.status, error.value.code) == (404, "not_found")


async def test_publication_supersedes_old_and_one_success_per_lineage(setup_store):
    store, _, _, proposal, old = setup_store
    async with store.revision(Principal.A, old.identity()) as reservation:
        assert await store.get(Principal.A, old.candidate_id) == old
        revised = proposal.model_copy(deep=True)
        revised.days[0].blocks.reverse()
        new = await store.publish_revision(Principal.A, reservation, revised)
    assert new.revision == 2 and new.candidate_id != old.candidate_id
    assert new.content_hash != old.content_hash
    assert store.stats()["payload_bytes"] == len(new.canonical_bytes)
    with pytest.raises(ServiceError, match="candidate_superseded"):
        await store.get(Principal.A, old.candidate_id)
    with pytest.raises(ServiceError, match="candidate_mismatch"):
        async with store.revision(Principal.A, new.identity()):
            pytest.fail("second successful revision admitted")
    forged = replace(reservation, candidate_id=new.candidate_id, token=None)
    with pytest.raises(ServiceError, match="candidate_mismatch"):
        await store.publish_revision(Principal.A, forged, revised)


async def test_failure_releases_token_without_revoking_old(setup_store):
    store, _, _, proposal, old = setup_store
    with pytest.raises(RuntimeError, match="synthetic failure"):
        async with store.revision(Principal.A, old.identity()):
            raise RuntimeError("synthetic failure")
    assert await store.get(Principal.A, old.candidate_id) == old
    async with store.revision(Principal.A, old.identity()) as reservation:
        updated = await store.publish_revision(Principal.A, reservation, proposal)
    assert updated.revision == 2


async def test_invalid_revision_preserves_current_and_reservation_can_retry(setup_store):
    store, _, _, proposal, old = setup_store
    bad = proposal.model_copy(deep=True)
    bad.days[0].planned_seconds += 1
    with pytest.raises(ServiceError, match="invalid_request"):
        async with store.revision(Principal.A, old.identity()) as reservation:
            await store.publish_revision(Principal.A, reservation, bad)
    async with store.revision(Principal.A, old.identity()):
        assert await store.get(Principal.A, old.candidate_id) == old


async def test_second_concurrent_revision_is_rejected(setup_store):
    store, _, _, _, old = setup_store
    entered, release = asyncio.Event(), asyncio.Event()

    async def first():
        async with store.revision(Principal.A, old.identity()):
            entered.set()
            await release.wait()

    task = asyncio.create_task(first())
    await entered.wait()
    with pytest.raises(ServiceError, match="revision_in_progress"):
        async with store.revision(Principal.A, old.identity()):
            pytest.fail("concurrent revision admitted")
    release.set()
    await task


async def test_repeated_cancellation_awaits_cleanup_even_while_guard_is_busy(
    setup_store, monkeypatch
):
    store, _, _, _, old = setup_store
    reserved, cleanup = asyncio.Event(), asyncio.Event()
    release_original = store._release

    async def observed_release(principal, reservation):
        cleanup.set()
        await release_original(principal, reservation)

    monkeypatch.setattr(store, "_release", observed_release)

    async def job():
        async with store.revision(Principal.A, old.identity()):
            reserved.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(job())
    await reserved.wait()
    async with store.lineage_guard(Principal.A, old.candidate_id):
        task.cancel()
        await cleanup.wait()
        task.cancel()
        scheduled = asyncio.Event()
        asyncio.get_running_loop().call_soon(scheduled.set)
        await scheduled.wait()
        assert not task.done()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with store.revision(Principal.A, old.identity()):
        pass


@pytest.mark.parametrize("at", [1799.999, 1800.0, 1800.001])
async def test_exact_ttl_boundary_and_no_raw_bytes_after_expiry(setup_store, at):
    store, _, clock, _, old = setup_store
    clock.now = at
    if at < 1800:
        assert await store.get(Principal.A, old.candidate_id) == old
    else:
        with pytest.raises(ServiceError, match="candidate_expired") as error:
            await store.get(Principal.A, old.candidate_id)
        assert error.value.status == 410
        assert store.stats()["payload_bytes"] == 0
        assert store.stats()["lineages"] == 0
        with pytest.raises(ServiceError, match="not_found"):
            await store.get(Principal.B, old.candidate_id)


async def test_pending_publication_cannot_revive_an_expired_candidate(setup_store):
    store, _, clock, proposal, old = setup_store
    async with store.revision(Principal.A, old.identity()) as reservation:
        clock.now = 1800.0
        with pytest.raises(ServiceError, match="candidate_expired"):
            await store.publish_revision(Principal.A, reservation, proposal)
    assert store.stats()["lineages"] == 0


async def test_guard_pins_expiry_and_acceptance_time_is_guard_acquisition(setup_store):
    store, _, clock, _, old = setup_store
    clock.now = 1799.999
    async with store.lineage_guard(Principal.A, old.candidate_id) as guard:
        assert guard.check_ready(old.identity(), use_acquisition_time=True) == old
        clock.now = 1801
        await store.expire()
        assert store.stats()["lineages"] == 1
        assert guard.check_ready(old.identity(), use_acquisition_time=True) == old
    with pytest.raises(RuntimeError):
        guard.check_ready()
    await store.expire()
    assert store.stats()["lineages"] == 0


async def test_waiting_request_does_not_get_an_old_acceptance_timestamp(setup_store):
    store, _, clock, _, old = setup_store
    waiting = asyncio.Event()

    async def wait_then_check():
        waiting.set()
        async with store.lineage_guard(Principal.A, old.candidate_id) as guard:
            guard.check_ready(old.identity(), use_acquisition_time=True)

    async with store.lineage_guard(Principal.A, old.candidate_id):
        clock.now = 1799
        task = asyncio.create_task(wait_then_check())
        await waiting.wait()
        clock.now = 1800
    with pytest.raises(ServiceError, match="candidate_expired"):
        await task


async def test_unresolved_gate_blocks_publication_reads_and_eviction(setup_store):
    store, _, clock, proposal, old = setup_store
    async with store.revision(Principal.A, old.identity()) as reservation:
        async with store.lineage_guard(Principal.A, old.candidate_id) as guard:
            guard.block_for_reconciliation()
        with pytest.raises(ServiceError, match="reconciliation_pending"):
            await store.publish_revision(Principal.A, reservation, proposal)
    clock.now = 2000
    await store.expire()
    assert store.stats()["lineages"] == 1
    with pytest.raises(ServiceError, match="reconciliation_pending"):
        await store.get(Principal.A, old.candidate_id)


async def test_profile_save_between_reservation_and_publication_rejects_stale(setup_store):
    store, profiles, _, proposal, old = setup_store
    async with store.revision(Principal.A, old.identity()) as reservation:
        previous = await profiles.get(Principal.A)
        await profiles.save(
            Principal.A, ProfileSaveRequest(expected_revision=1, preferences=previous.preferences)
        )
        with pytest.raises(ServiceError, match="stale_profile"):
            await store.publish_revision(Principal.A, reservation, proposal)
    with pytest.raises(ServiceError, match="stale_profile"):
        await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)


async def test_capacity_rejects_instead_of_evicting_and_expiry_frees_it(setup_store):
    store, _, clock, proposal, old = setup_store
    for _ in range(199):
        await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
    assert store.stats()["lineages"] == 200
    with pytest.raises(ServiceError, match="capacity_exceeded"):
        await store.publish_initial(Principal.B, proposal, expected_profile_revision=1)
    assert await store.get(Principal.A, old.candidate_id) == old
    assert store.stats()["payload_bytes"] <= CandidateLimits().store_bytes
    clock.now = 1800
    await store.expire()
    assert store.stats()["lineages"] == 0
    await store.publish_initial(Principal.B, proposal, expected_profile_revision=1)


async def test_byte_limits_fail_closed_under_encoder_and_accounting_faults(
    setup_store, monkeypatch
):
    import future_training.candidates as module

    store, _, _, proposal, old = setup_store
    with monkeypatch.context() as patch:
        patch.setattr(module, "encode_snapshot", lambda _: b"x" * 65537)
        with pytest.raises(ServiceError, match="invalid_request") as error:
            await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
        assert error.value.status == 413
    original_bytes = store.stats()["payload_bytes"]
    store._bytes = CandidateLimits().store_bytes
    with pytest.raises(ServiceError, match="capacity_exceeded"):
        await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
    store._bytes = original_bytes
    assert await store.get(Principal.A, old.candidate_id) == old


async def test_restart_new_store_has_no_transient_candidates(setup_store):
    _, profiles, clock, proposal, old = setup_store
    new_store = CandidateStore(profiles, load_catalog(), clock=clock)
    with pytest.raises(ServiceError, match="not_found"):
        await new_store.get(Principal.A, old.candidate_id)
    assert (await profiles.get(Principal.A)).revision == 1
    assert (
        await new_store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
    ).revision == 1


async def test_wrong_owner_or_hash_cannot_reserve_or_publish(setup_store):
    store, _, _, proposal, old = setup_store
    with pytest.raises(ServiceError, match="not_found"):
        async with store.revision(Principal.B, old.identity()):
            pytest.fail("wrong owner admitted")
    wrong = old.identity()
    wrong.content_hash = "b" * 64
    with pytest.raises(ServiceError, match="candidate_mismatch"):
        async with store.revision(Principal.A, wrong):
            pytest.fail("wrong hash admitted")
    async with store.revision(Principal.A, old.identity()) as reservation:
        with pytest.raises(ServiceError, match="not_found"):
            await store.publish_revision(Principal.B, reservation, proposal)


async def test_superseded_identity_keeps_its_original_expiry(setup_store):
    store, _, clock, proposal, old = setup_store
    clock.now = 900
    async with store.revision(Principal.A, old.identity()) as reservation:
        new = await store.publish_revision(Principal.A, reservation, proposal)
    assert new.expires_at_monotonic == 2700
    clock.now = 1800
    with pytest.raises(ServiceError, match="candidate_expired"):
        await store.get(Principal.A, old.candidate_id)
    assert await store.get(Principal.A, new.candidate_id) == new
    assert store.stats()["lineages"] == 1


async def test_concurrent_publications_use_one_pending_token_once(setup_store):
    store, _, _, proposal, old = setup_store
    gate = asyncio.Barrier(2)
    async with store.revision(Principal.A, old.identity()) as reservation:

        async def publish():
            await gate.wait()
            return await store.publish_revision(Principal.A, reservation, proposal)

        results = await asyncio.gather(publish(), publish(), return_exceptions=True)
    assert sum(isinstance(r, ServiceError) for r in results) == 1
    new = next(r for r in results if not isinstance(r, ServiceError))
    assert new.revision == 2 and store.stats()["aliases"] == 2


async def test_guard_wait_yields_before_expiry_check_for_future_key_recheck(setup_store):
    store, _, clock, _, old = setup_store
    waiting = asyncio.Event()
    fake_committed_result = {}

    async def future_coordinator_seam():
        waiting.set()
        async with store.lineage_guard(Principal.A, old.candidate_id):
            # An actual owner-scoped DB key lookup belongs here in F1-06.
            return fake_committed_result.get("same-key")

    async with store.lineage_guard(Principal.A, old.candidate_id):
        task = asyncio.create_task(future_coordinator_seam())
        await waiting.wait()
        fake_committed_result["same-key"] = "reference-result-only"
        clock.now = 1800
    assert await task == "reference-result-only"


async def test_expired_identity_metadata_is_bounded(setup_store):
    store, _, clock, proposal, old = setup_store
    for _ in range(401):
        clock.now += 1800
        await store.expire()
        newest = await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
    assert store.stats()["expired_ids"] == 400
    assert store.stats()["lineages"] == 1
    with pytest.raises(ServiceError, match="not_found"):
        await store.get(Principal.A, old.candidate_id)
    assert await store.get(Principal.A, newest.candidate_id) == newest


async def test_other_lineage_progresses_while_a_guard_is_held(setup_store):
    store, _, _, proposal, old = setup_store
    async with store.lineage_guard(Principal.A, old.candidate_id):
        new = await store.publish_initial(Principal.B, proposal, expected_profile_revision=1)
        assert await store.get(Principal.B, new.candidate_id) == new
