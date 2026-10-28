"""F3-03A mock protocol and explicitly labeled proposed-policy reference checks."""

import asyncio
import copy
import json

import httpx
import pytest
from agent_doubles import ManualClock, make_agent
from responses_doubles import Chunks, fixture, frames, response
from test_observability import CANARIES, assert_private
from test_observability import console as console

from future_training.agent.budget import AgentFault, Budget, Deadline
from future_training.agent.protocol import (
    OUTCOME_ADAPTER,
    SYSTEM_PROMPT,
    ModelInput,
    ProviderRequest,
    canonical,
)
from future_training.agent.tools import tool_definitions
from future_training.experiments.token_admission import (
    COMMON,
    COUNT_ENDPOINT,
    GENERATION_ONLY,
    CountedMockWire,
    FrozenPayload,
    pair_reservation_micro,
    proposed_schedule_reference,
)
from future_training.identity import Principal
from future_training.observability import LocalTracer, span
from future_training.providers.accounting import ActualUsage
from future_training.providers.gates import ENDPOINT, LiveGate
from future_training.providers.responses import ResponsesReplay
from future_training.schemas import BudgetLimits, GenerateRequest, SavedProfile

REQUEST = GenerateRequest(profile_revision=1)


def prepared(profile):
    state = ResponsesReplay(httpx.MockTransport(lambda request: None)).for_request()
    context = ModelInput(
        system=SYSTEM_PROMPT,
        profile=SavedProfile(revision=1, preferences=profile),
        catalog_revision="catalog-v1",
        messages=[],
        tool_schemas=tool_definitions(),
        output_schema=OUTCOME_ADAPTER.json_schema(),
    )
    raw = state._payload(ProviderRequest(context.model_dump_json().encode(), 1, 6000, 2000))
    state.clear()
    return FrozenPayload.prepare(raw)


class Backend:
    def __init__(self, values, count=1000):
        self.values = values
        self.count = count
        self.paths = []
        self.payloads = []  # Test assertion capture, never written or logged.
        self.generations = 0
        self.streams = []

    async def __call__(self, request):
        self.paths.append(request.url.path)
        self.payloads.append(json.loads(request.content))
        assert "authorization" not in request.headers
        assert request.headers["content-type"] == "application/json"
        if str(request.url) == COUNT_ENDPOINT:
            assert request.headers["accept"] == "application/json"
            value = self.count
            if callable(value):
                return await value(request)
            return httpx.Response(
                200, json={"object": "response.input_tokens", "input_tokens": value}
            )
        assert str(request.url) == ENDPOINT
        assert request.headers["accept"] == "text/event-stream"
        value = self.values[self.generations]
        self.generations += 1
        if callable(value):
            return await value(request)
        result = response(frames(value))
        self.streams.append(result.stream)
        return result


async def experiment(profile, backend, *, input_allowances=(6000, 6000, 4000)):
    clock = ManualClock()
    wire = CountedMockWire(
        httpx.MockTransport(backend), deadline=Deadline(clock), synthetic_count_ceiling_micro=1000
    )
    provider = ResponsesReplay(httpx.MockTransport(wire), input_allowances=input_allowances)
    agent = await make_agent(profile, provider=provider, clock=clock)
    async with agent.session(Principal.A, REQUEST) as run:
        wire.deadline = run.deadline
        result = await run.execute()
        state = run.provider
    assert state.closed and not state.history and not state.pending
    assert all(s.closed for s in backend.streams)
    assert agent.candidates.stats()["lineages"] == 0
    return result, wire


async def test_initial_count_generation_and_exact_projection(profile):
    backend = Backend([fixture()])
    result, wire = await experiment(profile, backend)
    assert result.output().outcome == "plan"
    assert backend.paths == ["/v1/responses/input_tokens", "/v1/responses"]
    count, generation = backend.payloads
    assert set(count) == COMMON
    assert set(generation) == COMMON | GENERATION_ONLY
    assert all(count[k] == generation[k] for k in COMMON)
    assert count["truncation"] == "disabled"
    assert wire.report()["wire_requests"] == 2
    assert wire.report()["input_tokens"] == 1000
    assert wire.report()["synthetic_count_liability_micro"] == 1000  # Never assume zero charge.


async def test_ratified_three_wire_calls_block_tool_continuation(profile):
    backend = Backend([fixture("tool"), fixture()])
    result, wire = await experiment(profile, backend)
    assert result.output().outcome == "error"
    assert result.diagnostic == "ratified_combined_call_limit"
    assert result.metrics.tool_dispatches == 1
    assert backend.paths == ["/v1/responses/input_tokens", "/v1/responses"]
    assert wire.report()["generation_requests"] == 1
    assert wire.report()["count_requests"] == 1
    assert wire.report()["synthetic_count_liability_micro"] == 1000


async def test_semantic_repair_keeps_original_attempt_limit(profile):
    bad = fixture()
    text = bad["output"][0]["content"][0]
    value = json.loads(text["text"])
    value["result"]["plan"]["days"][0]["planned_seconds"] += 1
    text["text"] = json.dumps(value)
    result, wire = await experiment(profile, Backend([bad, fixture()]))
    assert result.output().outcome == "error" and result.metrics.semantic_repairs == 1
    assert result.diagnostic == "ratified_combined_call_limit" and wire.wire_requests == 2


@pytest.mark.parametrize("value", [-1, 0, True, 1.0, "1000", None, 16001, 10**12])
async def test_count_types_and_bounds_fail_closed_before_generation(profile, value):
    backend = Backend([], count=value)
    result, wire = await experiment(profile, backend)
    assert result.output().outcome == "error"
    assert backend.generations == 0 and wire.count_requests == 1
    assert wire.count_liability_micro == 1000


@pytest.mark.parametrize(
    "failure",
    [
        "http",
        "redirect",
        "wrong_mime",
        "missing",
        "extra",
        "duplicate",
        "malformed",
        "oversized",
        "connection",
    ],
)
async def test_count_failures_no_retry_no_generation(profile, failure):
    async def bad_count(request):
        if failure == "connection":
            raise httpx.ReadError("synthetic private error")
        if failure == "http":
            return httpx.Response(429, json={"error": "synthetic"})
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "https://example.invalid"})
        if failure == "wrong_mime":
            return httpx.Response(200, text="{}")
        body = {
            "missing": b'{"object":"response.input_tokens"}',
            "extra": b'{"object":"response.input_tokens","input_tokens":1000,"extra":true}',
            "duplicate": b'{"object":"response.input_tokens","input_tokens":1000,"input_tokens":2}',
            "malformed": b"{bad",
            "oversized": b"x" * 1025,
        }[failure]
        return httpx.Response(
            200, headers={"content-type": "application/json"}, stream=Chunks(body, 1)
        )

    backend = Backend([], count=bad_count)
    result, wire = await experiment(profile, backend)
    assert result.output().outcome == "error" and len(backend.paths) == 1
    assert wire.count_liability_micro == 1000 and backend.generations == 0


@pytest.mark.parametrize("field", sorted(COMMON | GENERATION_ONLY))
def test_every_payload_field_is_bound_including_uncounted_options(profile, field):
    frozen = prepared(profile)
    value = json.loads(frozen.generation)
    value[field] = {"changed": "synthetic"}
    with pytest.raises(AgentFault, match="count_payload_mismatch"):
        frozen.assert_unchanged(canonical(value))
    with pytest.raises(AgentFault, match="count_payload_mismatch"):
        frozen.assert_unchanged(json.dumps(json.loads(frozen.generation), indent=3).encode())
    frozen.assert_unchanged(frozen.generation)


@pytest.mark.parametrize(
    "field",
    [
        "conversation",
        "previous_response_id",
        "metadata",
        "include",
        "personality",
        "temperature",
        "user",
    ],
)
def test_unsupported_or_ambiguous_generation_options_reject(profile, field):
    value = json.loads(prepared(profile).generation)
    value[field] = "synthetic"
    with pytest.raises(AgentFault, match="count_payload_invalid"):
        FrozenPayload.prepare(canonical(value))


def test_opaque_state_order_and_phase_are_bound_without_interpretation(profile):
    value = json.loads(prepared(profile).generation)
    value["input"].extend(copy.deepcopy(fixture("tool")["output"]))
    value["input"].append(
        {"type": "function_call_output", "call_id": "call.synthetic/one", "output": "{}"}
    )
    frozen = FrozenPayload.prepare(canonical(value))
    assert json.loads(frozen.counting)["input"] == value["input"]
    value["input"][1]["encrypted_content"] += "changed"
    with pytest.raises(AgentFault, match="count_payload_mismatch"):
        frozen.assert_unchanged(canonical(value))
    value = json.loads(frozen.generation)
    value["input"] = value["input"][:1] + list(reversed(value["input"][1:]))
    with pytest.raises(AgentFault):
        frozen.assert_unchanged(canonical(value))


@pytest.mark.parametrize("delta", [-1, 1])
async def test_actual_count_mismatch_stops_and_preserves_reported_tokens(profile, delta):
    value = fixture()
    value["usage"]["input_tokens"] += delta
    value["usage"]["total_tokens"] += delta
    backend = Backend([value])
    result, wire = await experiment(profile, backend)
    assert result.output().outcome == "error" and len(backend.paths) == 2
    assert wire.budget.input == 1000 + delta
    assert wire.count_liability_micro == 1000


@pytest.mark.parametrize("cancel", [False, True])
async def test_hanging_count_deadline_or_cancellation_drains(profile, cancel):
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    backend = Backend([], count=hang)
    clock = ManualClock()
    wire = CountedMockWire(
        httpx.MockTransport(backend), deadline=Deadline(clock), synthetic_count_ceiling_micro=1000
    )
    agent = await make_agent(
        profile, provider=ResponsesReplay(httpx.MockTransport(wire)), clock=clock
    )
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    if cancel:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        clock.advance(30)
        result = await task
        assert result.diagnostic == "deadline_exceeded"
    assert cleaned.is_set() and backend.generations == 0 and wire.count_liability_micro == 1000
    async with agent.session(Principal.A, REQUEST):
        pass


@pytest.mark.contract_spec
def test_proposed_six_call_reference_not_runtime_activation():
    actions = [
        "count",
        "generation",
        "tool",
        "count",
        "generation",
        "repair",
        "count",
        "generation",
    ]
    assert proposed_schedule_reference(actions) == "allowed_by_proposal_only"
    assert proposed_schedule_reference(actions + ["count"]) == "proposed_limit_exceeded"
    assert proposed_schedule_reference(["generation"]) == "missing_fresh_count"
    assert proposed_schedule_reference(["retry", "retry"]) == "proposed_limit_exceeded"
    assert proposed_schedule_reference(["repair", "repair"]) == "proposed_limit_exceeded"
    assert proposed_schedule_reference(["tool"] * 5) == "proposed_limit_exceeded"
    assert BudgetLimits().provider_attempts == 3
    with pytest.raises(AgentFault, match="live_provider_disabled"):
        LiveGate().check()


@pytest.mark.parametrize("price", [None, 0, -1, True, 1.5])
def test_unverified_count_price_is_not_zero_allowance(price):
    with pytest.raises(AgentFault, match="count_pricing_unverified"):
        pair_reservation_micro(16000, 2000, price)


def test_synthetic_pair_ceiling_and_existing_generation_caps():
    assert pair_reservation_micro(16000, 2000, 1000) == 61000
    budget = Budget()
    budget.reserve(16000)
    budget.unknown("synthetic_uncertain")
    with pytest.raises(AgentFault):
        budget.reserve(1)
    assert budget.input == 16000 and budget.output == 2000
    budget = Budget()
    for _ in range(2):
        budget.reserve(1)
        budget.unknown("synthetic_uncertain")
    with pytest.raises(AgentFault):
        budget.reserve(1)
    assert budget.output == 4000


async def test_count_canaries_absent_from_both_local_sinks(profile, console):
    value = fixture("tool")
    value["output"][0]["encrypted_content"] = " ".join(CANARIES)
    tracer = LocalTracer()
    with span("http", tracer=tracer):
        result, wire = await experiment(profile, Backend([value]))
    encoded = (
        console.getvalue()
        + json.dumps(tracer.snapshot())
        + json.dumps(wire.report())
        + repr(result)
    )
    assert_private(encoded)
    assert "opaque-synthetic" not in encoded


def test_documented_explicit_zero_writes_without_ttl_details_is_known_zero():
    raw = fixture()["usage"]
    raw["input_tokens_details"]["cache_write_tokens"] = 0
    raw["input_tokens_details"].pop("cache_write_tokens_details")
    usage = ActualUsage.from_response(raw)
    assert usage.write_30m_tokens == usage.write_12h_tokens == 0
    assert usage.input_tokens == 1000 and usage.output_tokens == 100


@pytest.mark.parametrize("value", [None, True, False, -1, 1, 300])
def test_missing_ttl_breakdown_never_invents_zero_or_price_for_unknown_writes(value):
    raw = fixture()["usage"]
    raw["input_tokens_details"].pop("cache_write_tokens_details")
    raw["input_tokens_details"]["cache_write_tokens"] = value
    with pytest.raises(ValueError):
        ActualUsage.from_response(raw)


async def test_current_agent_continuation_binds_native_state_before_budget_stop(
    profile, monkeypatch
):
    captured = []
    original = FrozenPayload.prepare

    def capture(cls, raw):
        value = original(raw)
        captured.append(value)
        return value

    monkeypatch.setattr(FrozenPayload, "prepare", classmethod(capture))
    result, _ = await experiment(profile, Backend([fixture("tool")]))
    assert result.output().outcome == "error" and len(captured) == 2
    count = json.loads(captured[-1].counting)
    generation = json.loads(captured[-1].generation)
    assert count["input"] == generation["input"]
    native = count["input"][1:]
    assert native[0] == fixture("tool")["output"][0]
    assert native[1]["call_id"] == native[2]["call_id"] == "call.synthetic/one"
    assert native[2]["type"] == "function_call_output"


async def test_exact_input_boundary_and_unexpected_overrun_are_distinct(profile):
    valid = fixture()
    valid["usage"]["input_tokens"] = 16000
    valid["usage"]["total_tokens"] = 16100
    result, wire = await experiment(
        profile, Backend([valid], count=16000), input_allowances=(16000,)
    )
    assert result.output().outcome == "plan" and wire.budget.input == 16000
    invalid = copy.deepcopy(valid)
    invalid["usage"]["input_tokens"] = 16001
    invalid["usage"]["total_tokens"] = 16101
    result, wire = await experiment(
        profile, Backend([invalid], count=16000), input_allowances=(16000,)
    )
    assert result.output().outcome == "error" and wire.budget.input == 16001
    assert wire.wire_requests == 2


async def test_missing_generation_usage_retains_generation_and_count_allowances(profile):
    invalid = fixture()
    invalid.pop("usage")
    result, wire = await experiment(profile, Backend([invalid]))
    assert result.output().outcome == "error"
    assert wire.report()["generation_unknown_attempts"] == 1
    assert wire.budget.input == 1000 and wire.budget.output == 2000
    assert wire.count_liability_micro == 1000


async def test_count_wait_holds_existing_admission_and_two_run_cap(profile):
    entered, second_entered, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def hold_count(request):
        entered.set()
        await release.wait()
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 1000})

    async def hold_second(request):
        second_entered.set()
        return await hold_count(request)

    def wire_for(handler):
        clock = ManualClock()
        backend = Backend([fixture()], count=handler)
        wire = CountedMockWire(
            httpx.MockTransport(backend),
            deadline=Deadline(clock),
            synthetic_count_ceiling_micro=1000,
        )
        return clock, wire

    first_clock, first_wire = wire_for(hold_count)
    agent = await make_agent(
        profile, provider=ResponsesReplay(httpx.MockTransport(first_wire)), clock=first_clock
    )
    first = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    conflict = await agent.generate(Principal.A, REQUEST)
    assert conflict.diagnostic == "concurrency_limit" and first_wire.count_requests == 1
    second_clock, second_wire = wire_for(hold_second)
    second_agent = await make_agent(
        profile, provider=ResponsesReplay(httpx.MockTransport(second_wire)), clock=second_clock
    )
    second = asyncio.create_task(second_agent.generate(Principal.B, REQUEST))
    await second_entered.wait()
    release.set()
    assert all(r.output().outcome == "plan" for r in await asyncio.gather(first, second))
    assert first_wire.wire_requests == second_wire.wire_requests == 2


def test_unknown_count_cost_cannot_be_enabled_by_provider_settings(monkeypatch):
    from future_training.config import Settings

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-non-key")
    monkeypatch.setenv("FATA_PROVIDER", "count_aware")
    with pytest.raises(RuntimeError):
        Settings.from_env()
    with pytest.raises(ValueError):
        CountedMockWire(
            httpx.AsyncHTTPTransport(),
            deadline=Deadline(ManualClock()),
            synthetic_count_ceiling_micro=1000,
        )


def test_count_evidence_separates_actual_mock_routes_and_proposal_only():
    from pathlib import Path

    evidence = json.loads(
        Path("docs/implementation/evidence/f3-03a-token-admission.json").read_text()
    )
    assert evidence["amendment_ratified"] is False and evidence["live_provider_requests"] == 0
    assert evidence["ratified_total_wire_limit"] == 3
    assert evidence["proposed_reference"]["source"] == "pure_reference_no_transport"
    assert evidence["proposed_reference"]["combined_limit"] == 6
    assert all(case["applied_combined_limit"] == 3 for case in evidence["cases"])


async def test_request_local_wire_rejects_concurrent_reuse_before_second_count(profile):
    entered, release = asyncio.Event(), asyncio.Event()

    async def hold(request):
        entered.set()
        await release.wait()
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 1000})

    wire = CountedMockWire(
        httpx.MockTransport(Backend([fixture()], count=hold)),
        deadline=Deadline(ManualClock()),
        synthetic_count_ceiling_micro=1000,
    )
    payload = prepared(profile)
    request = httpx.Request("POST", ENDPOINT, content=payload.generation)
    first = asyncio.create_task(wire(request))
    await entered.wait()
    with pytest.raises(AgentFault, match="count_scope_in_use"):
        await wire(request)
    release.set()
    assert (await first).status_code == 200 and wire.count_requests == 1
