import asyncio

import psycopg
import pytest
from profile_doubles import MemoryProfiles

from future_training.candidates import CandidateStore
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.profiles import PostgresProfiles
from future_training.schemas import ProfileSaveRequest


async def test_connection_failure_has_sanitized_profile_errors(profile):
    async def failing_connect():
        raise psycopg.OperationalError("synthetic-private-canary")

    repository = PostgresProfiles(load_catalog(), connect=failing_connect)
    for operation in (
        repository.get(Principal.A),
        repository.save(Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile)),
    ):
        with pytest.raises(ServiceError) as error:
            await operation
        assert (error.value.status, error.value.code) == (503, "internal_error")
        assert "synthetic-private-canary" not in str(error.value)


async def test_profile_read_fault_during_revision_keeps_old_candidate(profile, monkeypatch):
    profiles = MemoryProfiles()
    await profiles.save(Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile))
    catalog = load_catalog()
    store = CandidateStore(profiles, catalog)
    proposal = plan_week(profile, catalog).plan
    snapshot = await store.publish_initial(Principal.A, proposal, expected_profile_revision=1)
    async with store.revision(Principal.A, snapshot.identity()) as reservation:
        with monkeypatch.context() as patch:

            async def unavailable(principal):
                raise ServiceError(503, "internal_error")

            patch.setattr(profiles, "get", unavailable)
            with pytest.raises(ServiceError, match="internal_error"):
                await store.publish_revision(Principal.A, reservation, proposal)
    assert await store.get(Principal.A, snapshot.candidate_id) == snapshot
    async with store.revision(Principal.A, snapshot.identity()):
        pass


async def test_cancel_while_reserving_releases_guard_without_leaving_token(profile, monkeypatch):
    profiles = MemoryProfiles()
    await profiles.save(Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile))
    catalog = load_catalog()
    store = CandidateStore(profiles, catalog)
    snapshot = await store.publish_initial(
        Principal.A, plan_week(profile, catalog).plan, expected_profile_revision=1
    )
    entered = asyncio.Event()
    original = profiles.get

    async def hanging(principal):
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(profiles, "get", hanging)

    async def reserve():
        async with store.revision(Principal.A, snapshot.identity()):
            pytest.fail("cancelled reservation entered generation")

    task = asyncio.create_task(reserve())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    monkeypatch.setattr(profiles, "get", original)
    async with store.revision(Principal.A, snapshot.identity()):
        pass
