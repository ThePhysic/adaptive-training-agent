"""Native SQL + exact counted SingleProbe, with synthetic HTTP/TLS only."""

import asyncio
import copy
import importlib.util
import json
from pathlib import Path

import httpx
import pytest
import test_authority_postgres as authority_tests
from local_tls_doubles import server, trusted
from responses_doubles import fixture, frames
from test_observability import console as console
from test_provider_tls import certs as certs
from test_token_admission import Backend

from future_training.observability import LocalTracer, Span
from future_training.providers.http import LocalTLS
from future_training.providers.probe import ResponsesProbe, SingleProbe

pg_schema, rig = authority_tests.pg_schema, authority_tests.rig
pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def artifact_directory():
    from uuid import uuid4

    directory = ROOT / ".cache/f3-e1" / ("synthetic-test-" + uuid4().hex)
    directory.mkdir(mode=0o700, parents=True)
    return directory


def test_artifact_scratch_setup_is_cold_and_exclusive(tmp_path, monkeypatch):
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    assert not (tmp_path / ".cache").exists()
    first = artifact_directory.__wrapped__()
    marker = first / "attempt.claim"
    marker.write_bytes(b"retained-first-attempt")
    second = artifact_directory.__wrapped__()
    assert first != second and second.is_dir()
    assert marker.read_bytes() == b"retained-first-attempt"
    with pytest.raises(FileExistsError):
        marker.open("xb")
    assert not list(second.iterdir())


@pytest.fixture
def evidence():
    spec = importlib.util.spec_from_file_location(
        "counted_probe_evidence", ROOT / "experiments/counted_probe.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def broken(kind="domain"):
    value = copy.deepcopy(fixture())
    part = value["output"][0]["content"][0]
    if kind == "json":
        part["text"] = "{PRIVATE_CANARY"
    elif kind == "duplicate":
        part["text"] = '{"result":{},"result":{}}'
    else:
        output = json.loads(part["text"])
        output["result"]["plan"]["days"][0]["blocks"][0]["exercise_id"] = "unknown-exercise"
        part["text"] = json.dumps(output)
    return value


async def execute(evidence, rig, values, *, count=1000):
    ledger, _, _ = rig
    await ledger.simulate()
    backend = Backend(values, count=count)
    probe = SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(backend)))
    adapter = evidence.Rehearsal(probe)
    packet = await adapter.run()
    evidence.validate_packet(packet)
    return adapter, packet, backend


@pytest.mark.parametrize("repair", [False, True])
@pytest.mark.parametrize("tls", [False, True])
async def test_real_counted_probe_common_score_and_read_only_liabilities(
    evidence, rig, certs, repair, tls, artifact_directory
):
    ledger, ctl, _ = rig
    await ledger.simulate()
    values = [fixture("tool"), *([broken()] if repair else []), fixture()]
    backend = Backend(values)
    generations = 0

    def reply(line):
        nonlocal generations
        if b"input_tokens" in line:
            return b'{"object":"response.input_tokens","input_tokens":1000}', "application/json"
        value = values[generations]
        generations += 1
        return frames(value), "text/event-stream"

    async with server(certs["valid"], body=reply) as (port, *_):
        transport = (
            LocalTLS(port, trusted(certs["valid"][0])) if tls else httpx.MockTransport(backend)
        )
        probe = SingleProbe(ResponsesProbe(ledger, transport))
        adapter = evidence.Rehearsal(probe)
        packet = await adapter.run()
        n = 3 if repair else 2
        assert packet["evidence_complete"]
        assert packet["observation"]["counts"]["count_requests"] == n
        assert packet["observation"]["counts"]["provider_requests"] == n
        assert packet["observation"]["counts"]["wire_requests"] == 2 * n
        assert packet["scored"]["handling_passed"]
        assert packet["scored"]["hard_passed"] is not repair
        assert packet["scored"]["quality_eligible"] is not repair
        assert packet["scored"]["quality_scores"] is None
        assert packet["accounting"]["known_charged_micro"] == n * 2770
        assert packet["accounting"]["held_micro"] == n * 1000
        assert packet["accounting"]["actual_total_micro"] is None
        assert packet["accounting"]["liability_micro"] == n * 3770
        assert len(packet["reported_usage"]) == n
        assert len(packet["manifest"]["case_ids"]) == 1
        assert (
            packet["manifest"]["selection"]
            == "one_fixed_compatibility_profile_not_50_case_execution"
        )
        assert packet["proposals"] == (
            [{"schema_valid": True, "domain_valid": False, "agent_rejected": True}]
            if repair
            else []
        ) + [{"schema_valid": True, "domain_valid": True, "agent_rejected": False}]
        assert "for_request" not in probe.provider.__dict__
        assert not adapter.calls and not adapter.results and not adapter.sessions
        with pytest.raises(ValueError, match="already_used"):
            await adapter.run()
        evidence.validate_packet(packet)
    async with await ctl.connect() as c:
        assert await (
            await c.execute("SELECT count(*) FROM probe_authorities WHERE state='active'")
        ).fetchone() == (0,)
        assert await (await c.execute("SELECT count(*) FROM approved_plans")).fetchone() == (0,)
    # Retain only the two mocked illustrative artifacts, not an inflated sample population.
    if not tls:
        from uuid import uuid4

        path = artifact_directory / (("repair-" if repair else "success-") + uuid4().hex + ".json")
        adapter.persist(path)


@pytest.mark.parametrize("kind", ["json", "duplicate"])
async def test_repaired_final_never_erases_malformed_intermediate(evidence, rig, kind):
    _, packet, _ = await execute(evidence, rig, [fixture("tool"), broken(kind), fixture()])
    assert packet["evidence_complete"]
    assert packet["scored"]["actual"] == "plan"
    assert not packet["scored"]["hard_passed"] and not packet["scored"]["quality_eligible"]
    assert not packet["proposals"][0]["schema_valid"]


@pytest.mark.parametrize("kind", ["unknown", "write", "owner", "invalid"])
async def test_actual_tool_rejection_not_hidden_by_final_plan(evidence, rig, kind):
    tool = copy.deepcopy(fixture("tool"))
    call = tool["output"][-1]
    if kind in ("unknown", "write"):
        call["name"] = "unknown_read" if kind == "unknown" else "approve_plan"
    elif kind == "owner":
        call["name"], call["arguments"] = "get_user_preferences", '{"owner_id":"PRIVATE_CANARY"}'
    else:
        call["arguments"] = '{"limit":21}'
    _, packet, _ = await execute(evidence, rig, [tool, fixture()])
    assert packet["scored"]["actual"] == "plan"
    assert not packet["scored"]["hard_passed"]
    assert packet["observation"]["tools"][0]["status"] == "error"
    assert "PRIVATE_CANARY" not in json.dumps(packet)


@pytest.mark.parametrize("which", ["proposal", "tool"])
async def test_missing_observations_are_incomplete_not_default_success(
    evidence, rig, which, monkeypatch
):
    if which == "proposal":
        original = evidence.Rehearsal._response

        def omit(self, raw):
            original(self, raw)
            if self.responses[-1] == "final":
                self.responses.pop()
                self.proposals.clear()

        monkeypatch.setattr(evidence.Rehearsal, "_response", omit)
    else:
        monkeypatch.setattr(evidence.Rehearsal, "_context", lambda *_: None)
    _, packet, _ = await execute(evidence, rig, [fixture("tool"), fixture()])
    assert not packet["evidence_complete"] and not packet["scored"]["hard_passed"]
    assert not packet["scored"]["quality_eligible"]


@pytest.mark.parametrize("fault", ["usage", "missing_usage", "transport", "terminal", "count"])
async def test_incomplete_native_or_accounting_results_preserve_holds(evidence, rig, fault):
    value = copy.deepcopy(fixture())

    async def interrupted(request):
        raise httpx.ReadError("PRIVATE_CANARY")

    count = 1000
    if fault == "usage":
        value["usage"]["input_tokens"] = 1001
        value["usage"]["total_tokens"] = 1101
    elif fault == "missing_usage":
        value.pop("usage")
    elif fault == "terminal":
        value["status"] = "unexpected"
    elif fault == "count":
        count = interrupted
    _, packet, backend = await execute(
        evidence, rig, [interrupted if fault == "transport" else value], count=count
    )
    assert not packet["evidence_complete"] and not packet["scored"]["hard_passed"]
    assert packet["accounting"]["held_micro"] > 0
    assert packet["accounting"]["actual_total_micro"] is None
    assert packet["observation"]["counts"]["transport_retries"] == 0
    assert len(backend.paths) <= 2
    if fault in ("usage", "missing_usage"):
        assert packet["accounting"]["frozen"]
    if fault == "usage":
        assert packet["reported_usage"][0]["input_tokens"] == 1001


async def test_failed_accounting_read_is_unknown_not_zero(evidence, rig, monkeypatch):
    async def fail(*_):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(evidence, "accounting", fail)
    _, packet, _ = await execute(evidence, rig, [fixture("tool"), fixture()])
    assert packet["accounting"]["liability_micro"] is None
    assert not packet["evidence_complete"] and not packet["scored"]["hard_passed"]
    assert "PRIVATE_CANARY" not in json.dumps(packet)


async def test_cancelled_probe_drains_and_keeps_uncertain_sent_count(
    evidence, rig, artifact_directory
):
    ledger, _, _ = rig
    await ledger.simulate()
    entered, drained = asyncio.Event(), asyncio.Event()

    async def hanging(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    backend = Backend([], count=hanging)
    probe = SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(backend)))
    adapter = evidence.Rehearsal(probe)
    task = asyncio.create_task(adapter.run())
    await asyncio.wait_for(entered.wait(), 5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert drained.is_set() and len(backend.paths) == 1
    packet = adapter.packet()
    assert packet["observation"] is None and packet["scored"] is None
    assert packet["accounting"]["held_micro"] == 1000
    assert not packet["evidence_complete"] and "cancelled" in packet["reasons"]
    with pytest.raises(ValueError):
        await adapter.run()
    evidence.validate_packet(packet)

    from uuid import uuid4

    adapter.persist(artifact_directory / ("cancelled-" + uuid4().hex + ".json"))


async def test_shared_sinks_never_acquire_private_fixture_bindings_or_native_state(
    evidence, rig, request
):
    sink = request.getfixturevalue("console")
    tracer = LocalTracer()
    with Span("agent.session", tracer=tracer):
        _, packet, _ = await execute(evidence, rig, [fixture("tool"), fixture()])
    rendered = str(tracer.snapshot()) + sink.getvalue() + json.dumps(packet)
    for canary in (
        "synthetic-account",
        "synthetic-project",
        "synthetic-grant",
        "synthetic-session",
        "synthetic-operator",
        "encrypted_content",
    ):
        assert canary not in rendered
    assert tracer.snapshot() and sink.getvalue()


@pytest.mark.parametrize(
    "mutation",
    ["source", "provenance", "observation", "proposals", "responses", "flags", "manifest"],
)
async def test_packet_consistency_and_provenance_cannot_be_upgraded(evidence, rig, mutation):
    _, packet, _ = await execute(evidence, rig, [fixture("tool"), fixture()])
    packet = copy.deepcopy(packet)
    if mutation in ("source", "provenance"):
        packet[mutation] = "live"
    elif mutation == "observation":
        packet["observation"]["source"] = "live"
    elif mutation == "flags":
        packet["evidence_complete"] = False
    elif mutation == "manifest":
        packet["manifest"]["live_enabled"] = True
    else:
        packet[mutation] = []
    with pytest.raises(ValueError):
        evidence.validate_packet(packet)


@pytest.mark.parametrize("fault", ["partial", "fsync"])
async def test_partial_artifact_never_replays_or_overwrites(
    evidence, rig, monkeypatch, fault, artifact_directory
):
    adapter, _, backend = await execute(evidence, rig, [fixture("tool"), fixture()])
    path = artifact_directory / "partial-artifact.json"
    # Unique test artifact; never touch any historical attempt or evidence path.
    from uuid import uuid4

    path = path.with_name("partial-" + uuid4().hex + ".json")
    original = evidence.os.fsync

    def fail(fd):
        raise OSError("SYNTHETIC persistence failure")

    original_open = evidence.os.fdopen

    class Partial:
        def __init__(self, fd, mode):
            self.stream = original_open(fd, mode)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def write(self, body):
            self.stream.write(body[:9])
            self.stream.flush()
            raise OSError("SYNTHETIC partial write")

    if fault == "partial":
        monkeypatch.setattr(evidence.os, "fdopen", Partial)
    else:
        monkeypatch.setattr(evidence.os, "fsync", fail)
    with pytest.raises(OSError):
        adapter.persist(path)
    monkeypatch.setattr(evidence.os, "fsync", original)
    monkeypatch.setattr(evidence.os, "fdopen", original_open)
    assert path.exists()
    before = path.read_bytes()
    if fault == "partial":
        with pytest.raises(ValueError):
            json.loads(before)
    with pytest.raises(ValueError):
        adapter.persist(path)
    with pytest.raises(ValueError):
        await adapter.run()
    assert path.read_bytes() == before and len(backend.paths) == 4


@pytest.mark.parametrize("limit", ["attempts", "input", "output"])
async def test_budget_exhaustion_is_not_common_scored_success(evidence, rig, limit):
    values = []
    for i in range(3):
        value = copy.deepcopy(fixture("tool"))
        value["output"][-1]["call_id"] = "synthetic-call-" + str(i)
        value["output"][-1]["id"] = "synthetic-item-" + str(i)
        if limit == "input":
            value["usage"]["input_tokens"] = 16000
        elif limit == "output":
            value["usage"]["output_tokens"] = 2000
        value["usage"]["total_tokens"] = (
            value["usage"]["input_tokens"] + value["usage"]["output_tokens"]
        )
        values.append(value)
    _, packet, _ = await execute(evidence, rig, values, count=16000 if limit == "input" else 1000)
    assert packet["scored"]["actual"] == "error"
    assert not packet["scored"]["hard_passed"] and not packet["scored"]["quality_eligible"]
    assert packet["observation"]["counts"]["wire_requests"] <= 6


@pytest.mark.parametrize("terminal", ["refusal", "incomplete"])
async def test_explicit_nonplan_terminals_are_not_fabricated_quality(evidence, rig, terminal):
    _, packet, _ = await execute(evidence, rig, [fixture(terminal)])
    assert packet["scored"]["actual"] in ("abstain", "error")
    assert packet["scored"]["quality_scores"] is None
    assert not packet["scored"]["quality_eligible"]


async def test_authoritative_repair_rejection_survives_broad_schema_acceptance(evidence, rig):
    value = copy.deepcopy(fixture())
    value["output"][0]["content"][0]["text"] = json.dumps(
        {
            "result": {
                "outcome": "clarify",
                "fields": ["unsupported_field"],
                "choices": ["PRIVATE_CANARY"],
            }
        }
    )
    _, packet, _ = await execute(evidence, rig, [fixture("tool"), value, fixture()])
    assert packet["scored"]["actual"] == "plan"
    assert packet["proposals"][0]["agent_rejected"]
    assert not packet["scored"]["hard_passed"]
    assert "PRIVATE_CANARY" not in json.dumps(packet)


async def test_duplicate_native_calls_cannot_look_like_missing_clean_proposals(evidence, rig):
    value = copy.deepcopy(fixture("tool"))
    value["output"].append(copy.deepcopy(value["output"][-1]))
    _, packet, backend = await execute(evidence, rig, [value])
    assert not packet["evidence_complete"] and not packet["scored"]["quality_eligible"]
    assert packet["observation"]["tools"] == [] and len(backend.paths) == 2


@pytest.mark.parametrize("mode", ["deadline", "shutdown"])
async def test_controlled_deadline_shutdown_and_second_owner(evidence, rig, mode):
    from agent_doubles import ManualClock

    ledger, _, _ = rig
    await ledger.simulate()
    entered, drained = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    backend = Backend([hang])
    clock = ManualClock()
    provider = ResponsesProbe(ledger, httpx.MockTransport(backend))
    probe = SingleProbe(provider, clock=clock)
    first, second = evidence.Rehearsal(probe), evidence.Rehearsal(probe)
    task = asyncio.create_task(first.run())
    await asyncio.wait_for(entered.wait(), 5)
    with pytest.raises(ValueError, match="fresh_owned"):
        await second.run()
    if mode == "deadline":
        clock.advance(31)
        packet = await asyncio.wait_for(task, 5)
    else:
        await provider.stop()
        with pytest.raises(asyncio.CancelledError):
            await task
        packet = first.packet()
    assert drained.is_set() and len(backend.paths) == 2
    assert not packet["evidence_complete"]
    assert packet["accounting"]["actual_total_micro"] is None
    assert packet["accounting"]["held_micro"] == 23500


async def test_cleanup_failure_is_incomplete_and_owned_methods_restored(evidence, rig, monkeypatch):
    ledger, _, _ = rig
    await ledger.simulate()
    backend = Backend([fixture("tool"), fixture()])
    transport = httpx.MockTransport(backend)

    async def fail():
        raise OSError("PRIVATE_CANARY cleanup")

    monkeypatch.setattr(transport, "aclose", fail)
    probe = SingleProbe(ResponsesProbe(ledger, transport))
    adapter = evidence.Rehearsal(probe)
    packet = await adapter.run()
    assert not packet["evidence_complete"] and packet["scored"] is None
    assert "for_request" not in probe.provider.__dict__
    assert not adapter.calls and not adapter.results and not adapter.sessions
    assert "PRIVATE_CANARY" not in json.dumps(packet)


async def test_sql_snapshot_is_read_only_and_does_not_clear_reconciliation(evidence, rig):
    adapter, packet, _ = await execute(evidence, rig, [fixture("tool"), fixture()])
    ledger, ctl, _ = rig
    ledger._uncertain.add(ledger.spec.project)
    queries = []

    async def read_only(query, connection):
        queries.append(query)
        assert query.startswith(("SET ", "SELECT "))

    ctl.before_execute = read_only
    observed = await evidence.accounting(adapter.probe)
    ctl.before_execute = None
    assert observed["reconciliation_pending"]
    assert observed["held_micro"] is None and observed["liability_micro"] is None
    assert ledger.spec.project in ledger._uncertain
    assert observed["operations"] == packet["accounting"]["operations"]
    assert queries and queries[0].endswith("READ ONLY")


@pytest.mark.parametrize("mode", ["lost_after", "open_uncertain"])
async def test_ambiguous_reservation_is_not_zero_or_implicitly_reconciled(evidence, rig, mode):
    ledger, ctl, _ = rig
    await ledger.simulate()
    ctl.mode = mode
    backend = Backend([fixture()])
    probe = SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(backend)))
    adapter = evidence.Rehearsal(probe)
    packet = await adapter.run()
    assert not backend.paths and not packet["evidence_complete"]
    assert packet["accounting"]["liability_micro"] is None
    assert packet["accounting"]["actual_total_micro"] is None
    assert ledger.spec.project in ledger._uncertain
    # Explicit test cleanup only; the evidence reader never resolves the transaction.
    ctl.mode = "normal"
    await ctl.settle_retained(commit=False)
    with pytest.raises(ValueError):
        await adapter.run()


@pytest.mark.parametrize("mutation", ["kind", "transport", "execution", "source", "method"])
async def test_observer_cannot_accept_live_or_overridden_execution(evidence, rig, mutation):
    ledger, _, _ = rig
    provider = ResponsesProbe(ledger, httpx.MockTransport(lambda _: pytest.fail("No send")))
    probe = SingleProbe(provider)
    if mutation == "kind":
        provider.kind = "live"
    elif mutation == "transport":
        provider.transport = object()
    elif mutation == "execution":
        ledger.execution = "live"
    elif mutation == "source":
        provider.evidence_source = "live"
    else:
        probe.run = lambda: None
    with pytest.raises(ValueError):
        evidence.Rehearsal(probe)


@pytest.mark.parametrize(
    "mutation", ["zero_hold", "zero_unknown", "tool_attempts", "extra_content"]
)
async def test_accounting_and_missing_intents_cannot_be_relabelled_as_complete(
    evidence, rig, mutation
):
    _, packet, _ = await execute(evidence, rig, [fixture("tool"), fixture()])
    if mutation == "zero_hold":
        packet["accounting"]["held_micro"] = 0
    elif mutation == "zero_unknown":
        packet["accounting"]["actual_total_micro"] = 0
    elif mutation == "tool_attempts":
        packet["tool_attempts"] = []
    else:
        packet["PRIVATE_CANARY"] = "PRIVATE_CANARY"
    with pytest.raises(ValueError):
        evidence.validate_packet(packet)
