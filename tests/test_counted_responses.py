"""Actual Agent/Responses pathway against synthetic HTTP; no SQL claims here."""

import asyncio
import json

import httpx
import pytest
from agent_doubles import ManualClock, make_agent
from counted_doubles import RecorderLedger
from responses_doubles import fixture
from test_observability import CANARIES, assert_private
from test_observability import console as console
from test_token_admission import Backend

from future_training.agent.orchestration import _ADMISSION
from future_training.agent.protocol import ProviderRequest
from future_training.identity import Principal
from future_training.observability import LocalTracer, span
from future_training.providers.counting import COMMON
from future_training.providers.responses import ResponsesReplay
from future_training.schemas import GenerateRequest

REQUEST = GenerateRequest(profile_revision=1)


def provider(backend, ledger=None):
    return ResponsesReplay(
        httpx.MockTransport(backend),
        counted=True,
        ledger=ledger or RecorderLedger(),
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )


async def run(profile, values, *, count=1000):
    backend = Backend(values, count=count)
    replay = provider(backend)
    agent = await make_agent(profile, provider=replay)
    return await agent.generate(Principal.A, REQUEST), backend, replay, agent


def broken():
    value = fixture()
    value["output"][0]["content"][0]["text"] = "{"
    return value


@pytest.mark.parametrize("repair", [False, True])
async def test_actual_two_and_three_generation_sequences(profile, repair):
    values = [fixture("tool"), *([broken()] if repair else []), fixture()]
    result, backend, replay, agent = await run(profile, values)
    n = 3 if repair else 2
    assert result.output().outcome == "plan", result.diagnostic
    assert result.metrics.provider_requests == n
    assert result.count_requests == n and result.wire_requests == n * 2
    assert result.metrics.input_tokens == 1000 * n
    assert result.metrics.output_tokens == 100 * n
    assert result.metrics.semantic_repairs == int(repair)
    assert result.metrics.tool_dispatches == 1
    assert result.metrics.token_kind == "provider_reported_counted_replay"
    assert 0 < result.count_request_bytes <= n * 65536
    assert result.generation_request_bytes > result.count_request_bytes
    assert backend.paths == ["/v1/responses/input_tokens", "/v1/responses"] * n
    for i in range(n):
        count, generation = backend.payloads[2 * i : 2 * i + 2]
        assert count == {key: generation[key] for key in COMMON}
        assert generation["max_output_tokens"] == 2000
    assert backend.payloads[2]["input"][-1]["type"] == "function_call_output"
    assert len(replay.ledger.pairs) == n
    assert not replay.ledger.tickets and agent.candidates.stats()["lineages"] == 0
    assert all(stream.closed for stream in backend.streams)


@pytest.mark.parametrize("value", [None, True, -1, 0, 16001, "1000", 1.0])
async def test_bad_counts_never_generate(profile, value):
    result, backend, _, _ = await run(profile, [], count=value)
    assert result.output().outcome == "error" and len(backend.paths) == 1
    assert result.metrics.provider_requests == 0 and result.count_requests == 1


@pytest.mark.parametrize("fault", ["http", "mime", "duplicate", "oversize", "connection"])
async def test_failed_count_stops_without_retry(profile, fault):
    async def count(request):
        if fault == "connection":
            raise httpx.ReadError("private-count-detail")
        if fault == "http":
            return httpx.Response(503, text="private")
        if fault == "mime":
            return httpx.Response(200, text="{}")
        content = (
            b"x" * 1025
            if fault == "oversize"
            else (b'{"object":"response.input_tokens","input_tokens":1000,"input_tokens":1}')
        )
        return httpx.Response(200, content=content, headers={"content-type": "application/json"})

    result, backend, replay, _ = await run(profile, [], count=count)
    assert result.output().outcome == "error" and len(backend.paths) == 1
    assert result.metrics.transport_retries == 0 and not replay.ledger.tickets


@pytest.mark.parametrize("delta", [-1, 1])
async def test_input_usage_mismatch_preserves_actuals_and_stops(profile, delta):
    value = fixture()
    value["usage"]["input_tokens"] += delta
    value["usage"]["total_tokens"] += delta
    result, backend, _, _ = await run(profile, [value])
    assert result.output().outcome == "error" and len(backend.paths) == 2
    assert result.metrics.input_tokens == 1000 + delta


async def test_one_retry_owner_recounts_known_failure(profile):
    failure = fixture()
    failure.update(status="failed", error={"code": "server_error"}, output=[])
    result, backend, _, _ = await run(profile, [fixture("tool"), failure, fixture()])
    assert result.output().outcome == "plan", result.diagnostic
    assert result.metrics.transport_retries == 1
    assert result.metrics.provider_requests == result.count_requests == 3
    assert len(backend.paths) == 6


async def test_no_fourth_pair_for_repair_after_three_attempts(profile):
    failure = fixture()
    failure.update(status="failed", error={"code": "server_error"}, output=[])
    result, backend, _, _ = await run(profile, [fixture("tool"), failure, broken()])
    assert result.output().outcome == "error" and len(backend.paths) == 6
    assert result.metrics.provider_requests == result.count_requests == 3


async def test_ambiguous_generation_error_never_replays(profile):
    async def interrupted(request):
        raise httpx.ReadError("private-interruption")

    result, backend, _, _ = await run(profile, [fixture("tool"), interrupted])
    assert result.output().outcome == "error" and len(backend.paths) == 4
    assert result.metrics.uncertain_attempts == 1
    assert result.metrics.transport_retries == 0


@pytest.mark.parametrize(
    "fault", ["duplicate", "unknown_tool", "bad_arguments", "refusal", "incomplete"]
)
async def test_continuation_keeps_existing_tool_and_outcome_rules(profile, fault):
    value = fixture("tool")
    expected, dispatches = "plan", 1
    values = [value, fixture()]
    if fault == "duplicate":
        value["output"].append(value["output"][-1].copy())
        expected, dispatches = "error", 0
    elif fault == "unknown_tool":
        value["output"][-1]["name"] = "approve_plan"
    elif fault == "bad_arguments":
        value["output"][-1]["arguments"] = '{"owner":"other"}'
    else:
        values = [fixture(fault)]
        expected, dispatches = ("abstain" if fault == "refusal" else "error"), 0
    result, backend, _, _ = await run(profile, values)
    assert result.output().outcome == expected
    assert result.metrics.tool_dispatches == dispatches
    if fault in ("unknown_tool", "bad_arguments"):
        tool_result = json.loads(backend.payloads[2]["input"][-1]["output"])
        assert tool_result["status"] == "error" and tool_result["data"] is None


async def test_cumulative_inference_tokens_block_continuation_before_count(profile):
    value = fixture("tool")
    value["usage"]["input_tokens"] = 16000
    value["usage"]["total_tokens"] = 16100
    result, backend, _, _ = await run(profile, [value], count=16000)
    assert result.output().outcome == "error" and len(backend.paths) == 2
    assert result.metrics.input_tokens == 16000 and result.count_requests == 1


async def test_unexpected_over_limit_usage_retained_without_clamping(profile):
    value = fixture()
    value["usage"]["input_tokens"] = 16001
    value["usage"]["total_tokens"] = 16101
    result, backend, _, _ = await run(profile, [value], count=16000)
    assert result.output().outcome == "error" and len(backend.paths) == 2
    assert result.metrics.input_tokens == 16001


@pytest.mark.parametrize("phase", ["count", "generation"])
@pytest.mark.parametrize("cancel", [True, False])
async def test_cancellation_deadline_cleanup_and_admission(profile, phase, cancel):
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    backend = Backend(
        [hang] if phase == "generation" else [], count=hang if phase == "count" else 1000
    )
    replay = provider(backend)
    clock = ManualClock()
    agent = await make_agent(profile, provider=replay, clock=clock)
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    busy = await agent.generate(Principal.A, REQUEST)
    assert busy.output().outcome == "error"
    if cancel:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        clock.advance(30)
        result = await task
        assert result.output().outcome == "error"
    assert cleaned.is_set() and not replay.ledger.tickets
    assert _ADMISSION.active() == 0
    assert len(backend.paths) == (1 if phase == "count" else 2)


@pytest.mark.parametrize("mutation", ["context", "native", "allowance", "attempt"])
async def test_bound_ticket_rejects_mutation_before_generation(profile, mutation):
    backend = Backend([fixture()])
    replay = provider(backend)
    agent = await make_agent(profile, provider=replay)
    # Observe the real context at the admission boundary; the session remains owned.
    original = replay.for_request

    def for_request():
        session = original()
        complete = session.complete

        async def change(request):
            if mutation == "native":
                session.history.append({"role": "user", "content": "changed"})
            if mutation == "context":
                request = ProviderRequest(
                    request.payload + b" ",
                    request.attempt,
                    request.max_input_tokens,
                    request.max_output_tokens,
                )
            if mutation == "allowance":
                request = ProviderRequest(
                    request.payload,
                    request.attempt,
                    request.max_input_tokens + 1,
                    request.max_output_tokens,
                )
            if mutation == "attempt":
                request = ProviderRequest(
                    request.payload, 2, request.max_input_tokens, request.max_output_tokens
                )
            return await complete(request)

        session.complete = change
        return session

    replay.for_request = for_request
    result = await agent.generate(Principal.A, REQUEST)
    assert result.output().outcome == "error" and len(backend.paths) == 1
    assert not replay.ledger.tickets


async def test_count_requires_explicit_ledger_and_positive_synthetic_quote():
    for kwargs in ({}, {"count_ceiling_micro": 0}, {"count_ceiling_micro": 1000}):
        with pytest.raises(ValueError):
            ResponsesReplay(httpx.MockTransport(lambda r: None), counted=True, **kwargs)


async def test_private_content_never_enters_configured_sinks(profile, console):
    from future_training.agent.protocol import canonical

    canary = " ".join(CANARIES)
    value = fixture("tool")
    value["output"][0]["encrypted_content"] = canary
    backend = Backend([value, fixture()])
    agent = await make_agent(profile, provider=provider(backend))
    trace = LocalTracer()
    with span("http", tracer=trace, route="generate"):
        result = await agent.generate(Principal.A, REQUEST)
    assert result.output().outcome == "plan"
    assert_private(canonical(trace.snapshot()).decode() + console.getvalue())
    assert canary not in repr(result)
