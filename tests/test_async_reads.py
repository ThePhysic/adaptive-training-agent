import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest
from agent_doubles import ManualClock, make_agent, tool_response, valid_final
from async_read_doubles import ControlledReads

from future_training.agent.budget import AgentFault, Budget, Deadline
from future_training.agent.fake import ScriptedFake
from future_training.agent.protocol import FailureKind, ProviderFailure
from future_training.api import create_app
from future_training.candidates import encode_snapshot
from future_training.config import Settings
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.experiments.async_reads import LocalReads, ReadFailure, ReadFault, read_context
from future_training.identity import Principal
from future_training.observability import LocalTracer, Span
from future_training.schemas import GenerateRequest, ProfilePreferences, SavedPlan


async def execute(fake, *, concurrent=True, clock=None, budget=None, tracer=None):
    clock = clock or ManualClock()
    budget = budget or Budget()
    deadline = Deadline(clock)
    with Span("http", tracer=tracer):
        async with LocalReads(fake.transport(), Principal.A, load_catalog()) as reads:
            async with deadline.scope():
                return await read_context(reads, deadline, budget, concurrent=concurrent)


async def test_independent_reads_overlap_and_dependent_filter_waits(profile):
    fake = ControlledReads(profile)
    fake.header_gates = {name: asyncio.Event() for name in fake.payloads}
    task = asyncio.create_task(execute(fake))
    await fake.all_started.wait()
    assert fake.active == fake.maximum == 3 and not task.done()
    for gate in fake.header_gates.values():
        gate.set()
    result = await task
    assert result.profile.revision == 1 and len(result.catalog) == 20
    assert result.eligible_ids == tuple(
        r.exercise_id for r in load_catalog().eligible(result.profile.preferences)
    )
    assert result.history.plans == () and result.history.unavailable is None
    assert fake.active == 0 and all(t.done() for t in fake.tasks)


async def test_sequential_same_workload_has_no_overlap_and_same_result(profile):
    sequential = ControlledReads(profile)
    first = await execute(sequential, concurrent=False)
    concurrent = ControlledReads(profile)
    second = await execute(concurrent)
    assert first == second and sequential.requests == ["profile", "catalog", "history"]
    assert sequential.maximum == 1


@pytest.mark.parametrize("fault", ["invalid", "interrupt", "oversize", "authorization", "redirect"])
async def test_required_failure_cancels_and_awaits_siblings(profile, fault):
    fake = ControlledReads(profile)
    fake.header_gates = {name: asyncio.Event() for name in fake.payloads}
    fake.body_gates = {name: asyncio.Event() for name in ("profile", "history")}
    if fault == "invalid":
        fake.payloads["catalog"][0]["catalog_revision"] = "wrong"
    elif fault == "interrupt":
        fake.body_faults["catalog"] = httpx.ReadError("synthetic-private-canary")
    elif fault == "oversize":
        fake.raw["catalog"] = b"x" * 32769
    elif fault == "authorization":
        fake.statuses["catalog"] = 403
    else:
        fake.statuses["catalog"] = 302
        fake.headers["catalog"] = {"location": "https://external.invalid/private"}
    tracer = LocalTracer()
    task = asyncio.create_task(execute(fake, tracer=tracer))
    await fake.all_started.wait()
    for gate in fake.header_gates.values():
        gate.set()
    with pytest.raises(ReadFault) as error:
        await task
    expected = {
        "invalid": ReadFailure.INVALID,
        "interrupt": ReadFailure.TRANSPORT,
        "oversize": ReadFailure.OVERSIZE,
        "authorization": ReadFailure.AUTHORIZATION,
        "redirect": ReadFailure.HTTP,
    }
    assert error.value.kind == expected[fault]
    assert fake.active == 0 and all(t.done() for t in fake.tasks)
    assert len(fake.requests) == 3
    text = json.dumps(tracer.snapshot())
    assert "synthetic-private-canary" not in text and "external.invalid" not in text
    if fault == "invalid" and os.environ.get("FATA_F2_EVIDENCE") == "1":
        Path("docs/implementation/evidence/f2-01-read-fault-trace.json").write_text(
            json.dumps(tracer.snapshot(), indent=2) + "\n", encoding="utf-8"
        )


@pytest.mark.parametrize("fault", ["http", "transport", "timeout", "unauthorized", "malformed"])
async def test_optional_history_degrades_only_on_availability(profile, fault):
    fake = ControlledReads(profile)
    if fault == "http":
        fake.statuses["history"] = 503
    elif fault == "transport":
        fake.faults["history"] = httpx.ConnectError("synthetic-secret")
    elif fault == "timeout":
        fake.faults["history"] = httpx.ReadTimeout("synthetic-secret")
    elif fault == "unauthorized":
        fake.statuses["history"] = 401
    else:
        fake.raw["history"] = b"[broken"
    if fault in ("unauthorized", "malformed"):
        with pytest.raises(ReadFault):
            await execute(fake)
    else:
        result = await execute(fake)
        assert result.history.plans == () and result.history.unavailable is not None
    assert fake.active == 0 and all(t.done() for t in fake.tasks)
    assert len(fake.requests) == 3  # Never retry a failed read.


@pytest.mark.parametrize("phase", ["headers", "body"])
@pytest.mark.parametrize("stop", ["cancel", "deadline", "repeated_cancel"])
async def test_cancellation_and_deadline_drain_all_children(profile, stop, phase):
    fake, clock = ControlledReads(profile), ManualClock()
    gates = {name: asyncio.Event() for name in fake.payloads}
    if phase == "headers":
        fake.header_gates = gates
    else:
        fake.body_gates = gates
    if stop == "repeated_cancel" and phase == "body":
        fake.close_gates = {name: asyncio.Event() for name in fake.payloads}
    task = asyncio.create_task(execute(fake, clock=clock))
    await fake.all_started.wait()
    if stop == "deadline":
        clock.advance(30)
        with pytest.raises(TimeoutError):
            await task
    else:
        task.cancel()
        if stop == "repeated_cancel" and phase == "body":
            await fake.closing.wait()
            task.cancel()
            assert not task.done()
            for gate in fake.close_gates.values():
                gate.set()
        elif stop == "repeated_cancel":
            task.cancel()  # Two queued cancels before any response headers exist.
        with pytest.raises(asyncio.CancelledError):
            await task
    assert fake.active == 0 and all(t.done() for t in fake.tasks) and not clock.waiters
    recovered = await execute(ControlledReads(profile), clock=clock)
    assert recovered.profile.revision == 1


async def test_budget_reservation_fails_before_http_and_never_resets_counters(profile):
    fake, budget = ControlledReads(profile), Budget()
    budget.dispatch()
    budget.dispatch()
    with pytest.raises(AgentFault, match="tool_budget_exhausted"):
        await execute(fake, budget=budget)
    assert fake.requests == [] and budget.metrics().tool_dispatches == 4
    assert budget.metrics().provider_requests == budget.metrics().input_tokens == 0


@pytest.mark.parametrize("raw", [b'{"revision":1,"revision":2}', b'"\xff"', b'{"revision":NaN}'])
async def test_invalid_wire_json_fails_closed(profile, raw):
    fake = ControlledReads(profile)
    fake.raw["profile"] = raw
    with pytest.raises(ReadFault, match="read_invalid_result"):
        await execute(fake)
    assert fake.active == 0


async def test_no_socket_transport_or_caller_owner_string_is_accepted():
    with pytest.raises(ValueError, match="offline"):
        LocalReads(None, Principal.A, load_catalog())
    with pytest.raises(ServiceError, match="unauthorized"):
        LocalReads(
            httpx.MockTransport(lambda request: httpx.Response(200)), "synthetic-a", load_catalog()
        )


@pytest.mark.parametrize("status", [302, 404, 422])
async def test_optional_history_nonavailability_errors_are_fatal(profile, status):
    fake = ControlledReads(profile)
    fake.statuses["history"] = status
    with pytest.raises(ReadFault, match="read_http"):
        await execute(fake)
    assert fake.active == 0


@pytest.mark.parametrize("headers", [{"content-type": "text/plain"}, {"content-encoding": "gzip"}])
async def test_unexpected_content_envelope_is_rejected(profile, headers):
    fake = ControlledReads(profile)
    fake.headers["catalog"] = headers
    with pytest.raises(ReadFault, match="read_invalid_result"):
        await execute(fake)
    assert fake.active == 0


async def test_phase_timeout_of_stalled_optional_read_is_typed_and_drained(profile):
    fake = ControlledReads(profile)
    fake.body_gates["history"] = asyncio.Event()
    result = await execute(fake)
    assert result.history.unavailable == ReadFailure.TIMEOUT
    assert fake.active == 0 and all(task.done() for task in fake.tasks)


async def test_unexpected_adapter_exception_is_sanitized_and_fatal(profile):
    fake = ControlledReads(profile)
    fake.faults["history"] = RuntimeError("synthetic-secret-exception")
    with pytest.raises(ReadFault, match="read_internal"):
        await execute(fake)
    assert fake.active == 0 and all(task.done() for task in fake.tasks)


async def test_controlled_clock_comparison_proves_overlap_without_wall_clock_assertion(profile):
    async def trial(concurrent):
        fake, clock = ControlledReads(profile), ManualClock()
        fake.header_gates = {name: asyncio.Event() for name in fake.payloads}
        started = clock.now()
        task = asyncio.create_task(execute(fake, concurrent=concurrent, clock=clock))
        if concurrent:
            await fake.all_started.wait()
            assert fake.active == 3
            clock.advance(0.04)
            for gate in fake.header_gates.values():
                gate.set()
        else:
            for name in ("profile", "catalog", "history"):
                await fake.started[name].wait()
                assert fake.active == 1
                clock.advance(0.04)
                fake.header_gates[name].set()
        value = await task
        return value, clock.now() - started, fake

    sequential, seq_seconds, seq = await trial(False)
    concurrent, conc_seconds, conc = await trial(True)
    assert sequential == concurrent
    assert seq_seconds == pytest.approx(0.12) and conc_seconds == pytest.approx(0.04)
    assert len(seq.requests) == len(conc.requests) == 3
    assert seq.maximum == 1 and conc.maximum == 3 and seq.active == conc.active == 0


@pytest.mark.parametrize("corrupt", [False, True])
async def test_history_snapshot_hash_and_historical_versions_are_preserved(profile, corrupt):
    import hashlib

    fake = ControlledReads(profile)
    plan = plan_week(profile, load_catalog()).plan
    digest = hashlib.sha256(encode_snapshot(plan)).hexdigest()
    saved = SavedPlan.model_validate(
        {
            "approval": {
                "plan_id": "stored",
                "candidate": {"candidate_id": "old", "revision": 1, "content_hash": digest},
            },
            "plan": plan.model_dump(),
            "versions": {
                "profile_revision": 1,
                "catalog_revision": "historical",
                "validator_revision": "historical",
            },
        }
    )
    fake.payloads["history"] = [saved.model_dump()]
    if corrupt:
        fake.payloads["history"][0]["plan"]["days"][0]["planned_seconds"] += 1
        with pytest.raises(ReadFault, match="read_invalid_result"):
            await execute(fake)
    else:
        value = await execute(fake)
        assert value.history.plans == (saved,)


async def test_exclusions_use_authoritative_catalog_after_profile_read(profile):
    catalog = load_catalog()
    excluded = catalog.eligible(ProfilePreferences.model_validate(profile))[0].exercise_id
    fake = ControlledReads({**profile, "excluded_ids": [excluded]})
    value = await execute(fake)
    assert excluded not in value.eligible_ids


@pytest.mark.parametrize("mode", ["success", "tool_limit", "transport_retry", "provider_fatal"])
async def test_parent_session_keeps_admission_and_one_shared_budget(profile, mode):
    provider = None
    if mode == "tool_limit":
        provider = ScriptedFake([lambda request: tool_response(request, count=2), valid_final])
    elif mode == "transport_retry":
        provider = ScriptedFake([ProviderFailure(FailureKind.TRANSPORT), valid_final])
    elif mode == "provider_fatal":
        provider = ScriptedFake([ProviderFailure(FailureKind.FATAL)])
    agent = await make_agent(profile, provider=provider)
    fake = ControlledReads(profile)
    async with agent.session(Principal.A, GenerateRequest(profile_revision=1)) as run:
        async with LocalReads(fake.transport(), Principal.A, agent.catalog) as reads:
            await read_context(reads, run.deadline, run.budget)
        rejected = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
        assert rejected.output().error.code == "capacity_exceeded"
        result = await run.execute()
    assert len(fake.requests) == 3 and fake.active == 0
    assert result.metrics.tool_dispatches <= 4 and result.metrics.provider_requests <= 3
    assert result.metrics.input_tokens <= 16000 and result.metrics.output_tokens <= 4000
    if mode == "tool_limit":
        assert result.output().error.code == "budget_exceeded"
        assert result.metrics.tool_dispatches == 4 and result.metrics.provider_requests == 1
    elif mode == "provider_fatal":
        assert result.output().error.code == "provider_failure"
        assert result.metrics.transport_retries == 0
    else:
        assert result.output().outcome == "plan"
        assert result.metrics.transport_retries == (1 if mode == "transport_retry" else 0)


async def test_adapter_cannot_bypass_real_nonlocal_identity_boundary():
    app = create_app(settings=Settings(local_development="1"))
    transport = httpx.ASGITransport(app=app, client=("198.51.100.7", 1234))
    deadline = Deadline(ManualClock())
    async with LocalReads(transport, Principal.A, load_catalog()) as reads:
        async with deadline.scope():
            with pytest.raises(ReadFault, match="read_unauthorized"):
                await read_context(reads, deadline, Budget())
