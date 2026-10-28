import asyncio
import hashlib
import json
import socket
import sqlite3
import uuid
from contextlib import closing
from dataclasses import asdict

import pytest
from langgraph.types import Command
from run import clean, demo, typed_interruption
from spike import AREA, CONFIG, SCENARIOS, GateFault, GraphRuntime, Payload, fixture, offline

from future_training.agent.budget import AgentFault
from future_training.agent.fake import FakeModel
from future_training.agent.orchestration import _ADMISSION
from future_training.agent.protocol import canonical
from future_training.identity import Principal


@pytest.fixture
def database():
    path = AREA / f"test-{uuid.uuid4().hex}.sqlite"
    yield path
    clean(path)


@pytest.mark.parametrize("scenario", SCENARIOS)
async def test_equivalent_scenarios_and_exact_accounting(database, scenario):
    agent, request = fixture(scenario)
    typed = await agent.generate(Principal.A, request)
    async with GraphRuntime(database, scenario) as runtime:
        graph = await runtime.invoke(start=True)
        assert canonical(json.loads(graph.output_json)) == canonical(typed.output().model_dump())
        assert graph.reason == typed.diagnostic
        assert asdict(graph.ledger.restore().metrics()) == asdict(typed.metrics)
        assert runtime.agent.candidates is None
        assert not hasattr(runtime.agent.profiles, "save")
        assert graph.pending is None
        assert graph.stage == "end"


async def test_interrupt_closes_runtime_and_restores_in_new_object(database):
    async with GraphRuntime(database, pause=True) as original:
        paused = await original.invoke(start=True)
        before = await original.inspect()
        digest = hashlib.sha256(canonical(paused.context)).hexdigest()
        assert before["next"] == ["gate"] and paused.output_json is None
        assert paused.ledger.attempts == paused.ledger.tools == 1
        assert _ADMISSION.active() == 0
    with closing(sqlite3.connect(database)) as conn:
        assert conn.execute("SELECT count(*) FROM checkpoints").fetchone()[0] > 0
        assert conn.execute("SELECT count(*) FROM writes").fetchone()[0] > 0
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    async with GraphRuntime(database) as fresh:
        restored = await fresh.graph.aget_state(CONFIG)
        assert (
            hashlib.sha256(canonical(restored.values["payload"]["context"])).hexdigest() == digest
        )
        result = await fresh.invoke(resume=True)
        assert json.loads(result.output_json)["outcome"] == "plan"
        assert result.ledger.attempts == 2 and result.ledger.tools == 1
        again = await fresh.invoke()
        assert again == result


def test_three_real_interpreter_processes_and_cleanup():
    before = set(AREA.glob("restart-*"))
    report = demo()
    assert report["original_process_exited"]
    assert report["independent_processes"] == 3
    assert report["sqlite_integrity"] == "ok"
    assert report["tables"] == ["checkpoints", "writes"]
    assert set(AREA.glob("restart-*")) == before


async def test_failed_safe_node_recovers_without_redispatch(database):
    async with GraphRuntime(database, fault_gate=True) as runtime:
        with pytest.raises(GateFault):
            await runtime.invoke(start=True)
        state = await runtime.inspect()
        assert state["metrics"]["tool_dispatches"] == state["metrics"]["provider_requests"] == 1
        assert state["next"] == ["gate"]
    async with GraphRuntime(database) as recovered:
        result = await recovered.invoke()
        assert json.loads(result.output_json)["outcome"] == "plan"
        assert result.ledger.tools == 1 and result.ledger.attempts == 2


@pytest.mark.parametrize("operation", ["provider", "tool"])
async def test_cancelled_pending_operation_is_not_replayed_after_restart(database, operation):
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def hanging(*args):
        calls.append(operation)
        entered.set()
        await release.wait()

    async with GraphRuntime(database) as runtime:
        if operation == "provider":
            runtime.agent.provider.complete = hanging
        else:
            runtime.agent.tools.dispatch = hanging
        task = asyncio.create_task(runtime.invoke(start=True))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        snapshot = await runtime.inspect()
        assert snapshot["pending"] == operation
        assert _ADMISSION.active() == 0
    async with GraphRuntime(database) as restarted:
        # Any actual redispatch in the new process/object would hit this assertion.
        async def forbidden(*_args):
            raise AssertionError("Uncertain operation replayed")

        restarted.agent.provider.complete = forbidden
        restarted.agent.tools.dispatch = forbidden
        result = await restarted.invoke()
        assert result.reason == "uncertain_operation_not_replayed"
        assert json.loads(result.output_json)["outcome"] == "error"
        assert result.ledger.attempts == 1
        assert result.ledger.uncertain == (1 if operation == "provider" else 0)
        assert result.pending is None and result.ledger.pending is None
    assert calls == [operation]


async def test_same_principal_admission_and_cancellation_cleanup(database):
    entered, release = asyncio.Event(), asyncio.Event()
    async with GraphRuntime(database) as runtime:

        async def hang(_request):
            entered.set()
            await release.wait()

        runtime.agent.provider.complete = hang
        task = asyncio.create_task(runtime.invoke(start=True))
        await entered.wait()
        other = AREA / f"test-{uuid.uuid4().hex}.sqlite"
        try:
            async with GraphRuntime(other) as second:
                with pytest.raises(AgentFault, match="concurrency_limit"):
                    await second.invoke(start=True)
        finally:
            clean(other)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert _ADMISSION.active() == 0


@pytest.mark.parametrize("delta", [31, -1])
async def test_original_deadline_survives_pause_and_clock_regression_fails(database, delta):
    async with GraphRuntime(database, pause=True, wall=lambda: 1000.0) as first:
        await first.invoke(start=True)
    async with GraphRuntime(database, wall=lambda: 1000.0 + delta) as second:
        with pytest.raises(AgentFault, match="deadline_exceeded|checkpoint_clock_regressed"):
            await second.invoke(resume=True)
    assert _ADMISSION.active() == 0


async def test_invalid_resume_value_does_not_authorize_anything(database):
    async with GraphRuntime(database, pause=True) as runtime:
        await runtime.invoke(start=True)
        # Test the graph gate directly inside the same bounded existing session.
        async with runtime.agent.session(Principal.A, runtime.request) as run:
            runtime.run = run
            result = await runtime.graph.ainvoke(
                Command(resume={"approve": True}), CONFIG, durability="sync"
            )
        assert result["payload"]["reason"] == "invalid_resume"
        assert json.loads(result["payload"]["output_json"])["outcome"] == "error"


async def test_second_start_rejected_and_terminal_output_revalidated(database):
    async with GraphRuntime(database) as runtime:
        await runtime.invoke(start=True)
        with pytest.raises(ValueError, match="already started"):
            await runtime.invoke(start=True)
        snapshot = await runtime.graph.aget_state(CONFIG)
        data = Payload.model_validate(snapshot.values["payload"])
        bad = json.loads(data.output_json)
        bad["plan"]["days"][0]["planned_seconds"] += 1
        await runtime.graph.aupdate_state(
            CONFIG,
            {"payload": data.model_copy(update={"output_json": json.dumps(bad)}).model_dump()},
        )
        with pytest.raises(AgentFault, match="restored_output_invalid"):
            await runtime.invoke()


@pytest.mark.parametrize("field", ["scenario", "catalog_fingerprint", "versions"])
async def test_stale_checkpoint_context_never_calls_provider(database, field):
    async with GraphRuntime(database, pause=True) as runtime:
        await runtime.invoke(start=True)
    async with GraphRuntime(database) as fresh:
        state = await fresh.graph.aget_state(CONFIG)
        payload = dict(state.values["payload"])
        payload[field] = [] if field == "versions" else "stale"
        await fresh.graph.aupdate_state(CONFIG, {"payload": payload}, as_node="tool")
        with pytest.raises(AgentFault, match="checkpoint_context_changed"):
            await fresh.invoke(resume=True)


async def test_wrong_principal_cannot_resume(database):
    async with GraphRuntime(database, pause=True) as runtime:
        await runtime.invoke(start=True)
    async with GraphRuntime(database, principal=Principal.B) as fresh:
        with pytest.raises(AgentFault, match="checkpoint_context_changed"):
            await fresh.invoke(resume=True)


def test_path_boundary():
    with pytest.raises(ValueError, match="ignored experiment"):
        GraphRuntime(AREA.parent / "not-experiment.sqlite")


async def test_credentials_and_tracing_environment_do_not_enable_network(database, monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "synthetic-secret-canary")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-provider-canary")
    with offline():
        with pytest.raises(OSError, match="network disabled"):
            socket.getaddrinfo("example.com", 443)
    async with GraphRuntime(database) as runtime:
        result = await runtime.invoke(start=True)
        report = json.dumps(await runtime.inspect())
        assert json.loads(result.output_json)["outcome"] == "plan"
        assert "synthetic-secret-canary" not in report
        assert "synthetic-provider-canary" not in report
    assert b"synthetic-secret-canary" not in database.read_bytes()
    assert b"synthetic-provider-canary" not in database.read_bytes()


async def test_live_kind_is_rejected_even_if_provider_mutated(database):
    async with GraphRuntime(database) as runtime:
        runtime.agent.provider.kind = "live"
        data = await runtime.invoke(start=True)
        assert data.reason == "live_provider_disabled"
        assert data.ledger.attempts == data.ledger.uncertain == 1
        # Restore the class's unchanged fake fixture label for other tests.
        assert FakeModel.kind == "fake"


@pytest.mark.parametrize("scenario", ["repair", "transient", "tool_budget"])
async def test_resume_preserves_all_cumulative_budgets(database, scenario):
    agent, request = fixture(scenario)
    expected = await agent.generate(Principal.A, request)
    async with GraphRuntime(database, scenario, pause=True) as first:
        paused = await first.invoke(start=True)
        assert paused.stage == "gate"
    async with GraphRuntime(database, scenario) as second:
        resumed = await second.invoke(resume=True)
        assert canonical(json.loads(resumed.output_json)) == canonical(
            expected.output().model_dump()
        )
        assert asdict(resumed.ledger.restore().metrics()) == asdict(expected.metrics)


async def test_stalled_provider_deadline_uses_controlled_clock_and_releases_admission(database):
    entered, tick = asyncio.Event(), asyncio.Event()

    class Clock:
        value = 0

        def now(self):
            return self.value

        async def wait_until(self, target):
            await tick.wait()

    async with GraphRuntime(database) as runtime:
        clock = Clock()
        runtime.agent.clock = clock

        async def stalled(_request):
            entered.set()
            await asyncio.Event().wait()

        runtime.agent.provider.complete = stalled
        task = asyncio.create_task(runtime.invoke(start=True))
        await entered.wait()
        clock.value = 31
        tick.set()
        with pytest.raises(AgentFault, match="deadline_exceeded"):
            await task
        assert _ADMISSION.active() == 0
        snapshot = await runtime.inspect()
        assert snapshot["pending"] == "provider"
        assert snapshot["metrics"]["provider_requests"] == 1


@pytest.mark.parametrize("changed", ["profile", "request_text", "system", "tool_result"])
async def test_restored_context_and_tool_messages_are_revalidated(database, changed):
    async with GraphRuntime(database, pause=True) as first:
        await first.invoke(start=True)
    async with GraphRuntime(database) as fresh:
        saved = await fresh.graph.aget_state(CONFIG)
        payload = saved.values["payload"]
        context = payload["context"]
        if changed == "profile":
            context["profile"]["preferences"]["days_per_week"] = 3
        elif changed == "tool_result":
            message = next(message for message in context["messages"] if message["role"] == "tool")
            value = json.loads(message["data_json"])
            value["data"]["records"][0]["title"] = "synthetic corruption"
            message["data_json"] = json.dumps(value)
        else:
            context[changed] = "synthetic changed context"
        await fresh.graph.aupdate_state(CONFIG, {"payload": payload}, as_node="tool")
        with pytest.raises(AgentFault, match="checkpoint_context_changed|tool_result_mismatch"):
            await fresh.invoke(resume=True)


@pytest.mark.parametrize(
    "lookup", ["gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo"]
)
def test_alternate_dns_paths_denied(lookup):
    with offline(), pytest.raises(OSError, match="network disabled"):
        getattr(socket, lookup)("external.invalid")


async def test_typed_cancellation_requires_new_request_instead_of_resume():
    result = await typed_interruption()
    assert result["closed_run_rejected"]
    assert result["cancelled_metrics"]["provider_requests"] == 1
    assert result["cancelled_metrics"]["tool_dispatches"] == 1
    assert result["new_request_metrics"]["provider_requests"] == 2
    assert result["new_request_metrics"]["tool_dispatches"] == 1
    assert result["new_request_outcome"] == "plan"


@pytest.mark.parametrize(
    "monotonic_after,reason", [(1031.0, "deadline_exceeded"), (900.0, "checkpoint_clock_regressed")]
)
async def test_wall_clock_cannot_extend_same_boot_deadline(database, monotonic_after, reason):
    async with GraphRuntime(
        database, pause=True, wall=lambda: 1000.0, monotonic=lambda: 1000.0
    ) as first:
        await first.invoke(start=True)
    async with GraphRuntime(
        database, wall=lambda: 1005.0, monotonic=lambda: monotonic_after
    ) as fresh:
        with pytest.raises(AgentFault, match=reason):
            await fresh.invoke(resume=True)


async def test_final_validation_cannot_return_past_original_deadline(database):
    class Clock:
        value = 0.0

        def now(self):
            return self.value

        async def wait_until(self, _target):
            await asyncio.Event().wait()

    clock = Clock()
    async with GraphRuntime(
        database, wall=lambda: 1000.0 + clock.now(), monotonic=clock.now
    ) as runtime:
        runtime.agent.clock = clock
        original = runtime.verify_output

        def validation_crosses_deadline(data):
            original(data)
            clock.value = 31.0

        runtime.verify_output = validation_crosses_deadline
        with pytest.raises(AgentFault, match="deadline_exceeded"):
            await runtime.invoke(start=True)
        with pytest.raises(AgentFault, match="deadline_exceeded"):
            await runtime.invoke()
    assert _ADMISSION.active() == 0
