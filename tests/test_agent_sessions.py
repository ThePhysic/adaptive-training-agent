import asyncio

import pytest
from agent_doubles import Hanging, make_agent, valid_final

from future_training.agent.budget import AgentFault
from future_training.agent.fake import ScriptedFake
from future_training.agent.orchestration import State
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.schemas import GenerateRequest

REQUEST = GenerateRequest(profile_revision=1)


async def initial(agent):
    output = (await agent.generate(Principal.A, REQUEST)).output()
    return await agent.candidates.publish_initial(
        Principal.A, output.plan, expected_profile_revision=1
    )


async def test_session_keeps_admission_and_revision_reservation_but_never_publishes(profile):
    agent = await make_agent(profile)
    snapshot = await initial(agent)
    before = agent.candidates.stats()
    async with agent.session(Principal.A, REQUEST, revise=snapshot.identity()) as run:
        result = await run.execute()
        assert result.output().outcome == "plan"
        assert run.reservation is not None
        assert result.states[-1] == State.READY
        assert agent.candidates.stats() == before
        assert (await agent.candidates.get(Principal.A, snapshot.candidate_id)) == snapshot
        same = await agent.generate(Principal.A, REQUEST)
        assert same.output().error.code == "capacity_exceeded"
        with pytest.raises(ServiceError, match="revision_in_progress"):
            async with agent.candidates.revision(Principal.A, snapshot.identity()):
                pytest.fail("Released before terminalization")
        with pytest.raises(RuntimeError, match="only once"):
            await run.execute()
    with pytest.raises(RuntimeError):
        await run.execute()
    with pytest.raises(ServiceError, match="candidate_mismatch"):
        await agent.candidates.publish_revision(Principal.A, run.reservation, result.output().plan)
    # Preview completion did not consume the successful revision allowance.
    async with agent.candidates.revision(Principal.A, snapshot.identity()):
        pass
    assert agent.candidates.stats() == before


async def test_run_execution_must_use_session_task_so_deadline_covers_actual_work(profile):
    agent = await make_agent(profile)
    async with agent.session(Principal.A, REQUEST) as run:
        with pytest.raises(RuntimeError, match="only once"):
            await asyncio.create_task(run.execute())
        assert (await run.execute()).output().outcome == "plan"


async def test_deadline_covers_future_transport_session_after_validated_preview(profile):
    agent = await make_agent(profile)
    snapshot = await initial(agent)
    ready = asyncio.Event()

    async def stalled_transport():
        async with agent.session(Principal.A, REQUEST, revise=snapshot.identity()) as run:
            result = await run.execute()
            assert result.output().outcome == "plan"
            ready.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(stalled_transport())
    await ready.wait()
    agent.clock.advance(30)
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(task, 2)
    assert not agent.clock.waiters
    assert (await agent.candidates.get(Principal.A, snapshot.candidate_id)) == snapshot
    async with agent.candidates.revision(Principal.A, snapshot.identity()):
        pass


@pytest.mark.parametrize("cancel", [False, True])
async def test_revision_failure_or_cancel_releases_reservation_for_new_request(profile, cancel):
    agent = await make_agent(profile)
    snapshot = await initial(agent)
    hanging = Hanging()
    agent.provider = ScriptedFake([hanging])
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST, revise=snapshot.identity()))
    await hanging.started.wait()
    if cancel:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        agent.clock.advance(30)
        result = await asyncio.wait_for(task, 2)
        assert result.output().error.code == "budget_exceeded"
    assert hanging.cleaned.is_set()
    assert not agent.clock.waiters
    async with agent.candidates.revision(Principal.A, snapshot.identity()):
        pass
    agent.provider = ScriptedFake([valid_final])
    result = await agent.generate(Principal.A, REQUEST, revise=snapshot.identity())
    assert result.output().outcome == "plan"
    assert result.metrics.provider_requests == 1  # Fresh per-request budget.
    assert (await agent.candidates.get(Principal.A, snapshot.candidate_id)) == snapshot


async def test_repeated_cancel_waits_for_candidate_guard_cleanup(profile):
    agent = await make_agent(profile)
    snapshot = await initial(agent)
    hanging = Hanging()
    agent.provider = ScriptedFake([hanging])
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST, revise=snapshot.identity()))
    await hanging.started.wait()
    async with agent.candidates.lineage_guard(Principal.A, snapshot.candidate_id):
        task.cancel()
        await hanging.cleaned.wait()
        # The inherited F1-03 release is now waiting on this guard. A second
        # cancel cannot release admission or skip reservation cleanup early.
        task.cancel()
        assert not task.done()
        assert (
            await agent.generate(Principal.A, REQUEST)
        ).output().error.code == "capacity_exceeded"
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 2)
    async with agent.candidates.revision(Principal.A, snapshot.identity()):
        pass


async def test_revision_expiry_during_model_work_cannot_return_plan(profile):
    agent = await make_agent(profile)
    snapshot = await initial(agent)
    agent.clock.advance(snapshot.expires_at_monotonic - agent.clock.now() - 10)
    hanging = Hanging()
    agent.provider = ScriptedFake([hanging])
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST, revise=snapshot.identity()))
    await hanging.started.wait()
    agent.clock.advance(10)
    hanging.release.set()
    result = await task
    assert result.output().error.code == "candidate_expired"
    assert agent.candidates.stats()["lineages"] == 0


async def test_revision_wrong_owner_hash_or_pending_rejected_before_model(profile):
    agent = await make_agent(profile)
    snapshot = await initial(agent)
    wrong_owner = await agent.generate(Principal.B, REQUEST, revise=snapshot.identity())
    assert wrong_owner.output().error.code == "not_found"
    assert wrong_owner.metrics.provider_requests == 0
    forged = snapshot.identity().model_copy(update={"content_hash": "0" * 64})
    wrong_hash = await agent.generate(Principal.A, REQUEST, revise=forged)
    assert wrong_hash.output().error.code == "candidate_mismatch"
    assert wrong_hash.metrics.provider_requests == 0
    async with agent.candidates.revision(Principal.A, snapshot.identity()):
        pending = await agent.generate(Principal.A, REQUEST, revise=snapshot.identity())
        assert pending.output().error.code == "revision_in_progress"
        assert pending.metrics.provider_requests == 0


async def test_explicit_deadline_check_before_future_terminalization(profile):
    agent = await make_agent(profile)
    async with agent.session(Principal.A, REQUEST) as run:
        await run.execute()
        agent.clock.advance(30)
        with pytest.raises(AgentFault, match="deadline_exceeded"):
            run.deadline.check()
    assert agent.candidates.stats()["lineages"] == 0
