import asyncio
import json
import os
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from agent_doubles import ManualClock, make_agent
from responses_doubles import Chunks, Script, fixture, frames, response
from test_observability import CANARIES, assert_private
from test_observability import console as console

from future_training.agent.budget import AgentFault
from future_training.agent.protocol import (
    OUTCOME_ADAPTER,
    SYSTEM_PROMPT,
    Message,
    ModelInput,
    ProviderRequest,
    canonical,
)
from future_training.agent.tools import tool_definitions
from future_training.config import Settings
from future_training.identity import Principal
from future_training.observability import LocalTracer, span
from future_training.providers.accounting import ActualUsage, cost_micro, reserve_micro
from future_training.providers.artifacts import assets
from future_training.providers.gates import ENDPOINT, LiveGate, LivePermit
from future_training.providers.responses import ASSETS, ResponsesReplay, read_stream
from future_training.providers.schemas import output_schema, provider_tools, strict_schema
from future_training.schemas import GenerateRequest, SavedProfile

REQUEST = GenerateRequest(profile_revision=1)


def tool(name="search_exercises", call_id="call.synthetic/one", arguments=None):
    value = fixture("tool")
    call = value["output"][-1]
    call["name"], call["call_id"] = name, call_id
    if arguments is not None:
        call["arguments"] = arguments
    return value


async def run(profile, values, **kwargs):
    script = Script(values)
    provider = ResponsesReplay(httpx.MockTransport(script), **kwargs)
    agent = await make_agent(profile, provider=provider)
    result = await agent.generate(Principal.A, REQUEST)
    return result, script, agent


async def test_native_tool_continuation_validation_and_cleanup(profile):
    result, script, agent = await run(profile, [tool(), fixture()])
    assert result.output().outcome == "plan", result.diagnostic
    assert result.metrics.provider_requests == 2 and result.metrics.tool_dispatches == 1
    assert result.metrics.input_tokens == 2000 and result.metrics.output_tokens == 200
    assert result.metrics.token_kind == "provider_reported_replay"
    assert result.model_id == "gpt-6.1-sol-replay"
    assert len(result.provider_usage) == 2
    second = script.requests[1]
    native = second["input"][1:]
    assert native[0]["type"] == "reasoning"
    assert native[0]["encrypted_content"] == "opaque-synthetic-only"
    assert native[-1]["type"] == "function_call_output"
    assert native[-1]["call_id"] == "call.synthetic/one"
    assert json.loads(native[-1]["output"])["data"]["records"]
    assert second["store"] is False and second["parallel_tool_calls"] is False
    assert all(stream.closed for stream in script.streams)
    assert agent.candidates.stats()["lineages"] == 0
    async with agent.session(Principal.A, REQUEST) as session:
        state = session.provider
    assert state.closed and state.history == [] and state.pending == {}


@pytest.mark.parametrize(
    "name,outcome", [("plan", "plan"), ("refusal", "abstain"), ("incomplete", "error")]
)
async def test_terminal_outcomes(profile, name, outcome):
    result, script, _ = await run(profile, [fixture(name)])
    assert result.output().outcome == outcome
    assert len(script.requests) == 1


@pytest.mark.parametrize(
    "change", ["unknown_exercise", "wrong_duration", "outer_extra", "broken_json"]
)
async def test_semantic_repair_uses_existing_validator(profile, change):
    bad = fixture()
    content = bad["output"][0]["content"][0]
    value = json.loads(content["text"])
    if change == "unknown_exercise":
        value["result"]["plan"]["days"][0]["blocks"][0]["exercise_id"] = "unknown"
    elif change == "wrong_duration":
        value["result"]["plan"]["days"][0]["planned_seconds"] += 1
    elif change == "outer_extra":
        value["write_plan"] = True
    content["text"] = "{" if change == "broken_json" else json.dumps(value)
    result, script, _ = await run(profile, [bad, fixture()])
    assert result.output().outcome == "plan"
    assert result.metrics.semantic_repairs == 1
    assert "issue_codes" in script.requests[-1]["input"][-1]["content"]


@pytest.mark.parametrize(
    "values,dispatches",
    [
        ([tool(), tool()], 1),
        ([{**tool(), "output": [tool()["output"][-1], tool()["output"][-1]]}], 0),
    ],
)
async def test_duplicate_native_calls_cannot_dispatch_twice(profile, values, dispatches):
    result, _, _ = await run(profile, values)
    assert result.output().outcome == "error"
    assert result.metrics.tool_dispatches == dispatches


@pytest.mark.parametrize(
    "name,args",
    [
        ("approve_plan", "{}"),
        ("get_user_preferences", '{"owner":"other"}'),
        ("search_exercises", '{"limit":true}'),
        ("search_exercises", "{bad"),
    ],
)
async def test_tool_validation_and_no_write_capability(profile, name, args):
    result, script, _ = await run(profile, [tool(name=name, arguments=args), fixture()])
    assert result.metrics.tool_dispatches == 1
    output = json.loads(script.requests[1]["input"][-1]["output"])
    assert output["status"] == "error" and output["data"] is None


@pytest.mark.parametrize("status", [301, 400, 401, 429, 500, 503])
async def test_http_errors_never_hidden_retry_or_free_usage(profile, status):
    result, script, _ = await run(profile, [httpx.Response(status, text="private-error")])
    assert result.output().outcome == "error"
    assert len(script.requests) == 1 and result.metrics.uncertain_attempts == 1
    assert result.metrics.input_tokens == 6000 and result.metrics.output_tokens == 2000


async def test_connection_interruption_is_uncertain_and_no_nested_retry(profile):
    async def interrupted(request):
        raise httpx.ReadError("private synthetic detail")

    result, script, _ = await run(profile, [interrupted])
    assert result.output().outcome == "error" and len(script.requests) == 1
    assert result.metrics.uncertain_attempts == 1


@pytest.mark.parametrize(
    "fault",
    [
        "missing_usage",
        "negative_usage",
        "wrong_model",
        "wrong_tier",
        "bad_partition",
        "reasoning_overflow",
        "extra_output_item",
    ],
)
async def test_usage_and_provider_integrity_fail_closed(profile, fault):
    value = fixture()
    if fault == "missing_usage":
        value.pop("usage")
    elif fault == "negative_usage":
        value["usage"]["input_tokens"] = -1
    elif fault == "wrong_model":
        value["model"] = "unapproved-model"
    elif fault == "wrong_tier":
        value["service_tier"] = "ultrafast"
    elif fault == "bad_partition":
        value["usage"]["input_tokens_details"]["cached_tokens"] = 99999
    elif fault == "reasoning_overflow":
        value["usage"]["output_tokens_details"]["reasoning_tokens"] = 101
    else:
        value["output"].append({"type": "unapproved_hosted_tool"})
    result, _, _ = await run(profile, [value])
    assert result.output().outcome == "error"


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate_terminal",
        "backward_sequence",
        "eof",
        "invalid_utf8",
        "oversized",
        "unknown_event",
        "mismatched_event",
    ],
)
async def test_bounded_malformed_streams(profile, fault):
    body = frames(fixture())
    if fault == "duplicate_terminal":
        body += body
    elif fault == "backward_sequence":
        body = frames(fixture(), prefix=[{"type": "response.in_progress"}]).replace(
            b'"sequence_number":1', b'"sequence_number":0'
        )
    elif fault == "eof":
        body = body[:-2]
    elif fault == "invalid_utf8":
        body = b"data: \xff\n\n"
    elif fault == "oversized":
        body = b"x" * 65537
    elif fault == "unknown_event":
        body = b'data: {"type":"unapproved","sequence_number":0}\n\n'
    else:
        body = body.replace(b"event: response.completed", b"event: response.failed")
    result, script, _ = await run(profile, [body])
    assert result.output().outcome == "error"
    assert all(s.closed for s in script.streams)


@pytest.mark.parametrize("size", [1, 2, 7, 4096])
async def test_unicode_multiline_crlf_and_cumulative_snapshots(size):
    value = fixture("refusal")
    value["output"][0]["content"][0]["refusal"] = "Synthetic café 🏋"
    body = frames(
        value,
        prefix=[
            {
                "type": "response.in_progress",
                "response": {"usage": value["usage"]},
            }
        ],
    ).replace(b"\n", b"\r\n")
    # JSON whitespace between properties becomes valid multiline data fields.
    body = body.replace(b',"sequence_number"', b',\r\ndata: "sequence_number"')
    stream = Chunks(body, size)
    result = await read_stream(response(body, size=size))
    assert ActualUsage.from_response(result["usage"]).input_tokens == 1000
    assert stream.closed is False  # read_stream caller owns response context; separate check above.


async def test_cancellation_deadline_and_session_cleanup(profile):
    entered, cleaned = asyncio.Event(), asyncio.Event()

    class Hanging(httpx.AsyncByteStream):
        async def __aiter__(self):
            entered.set()
            try:
                await asyncio.Event().wait()
                yield b""
            finally:
                cleaned.set()

        async def aclose(self):
            cleaned.set()

    async def handler(request):
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Hanging())

    provider = ResponsesReplay(httpx.MockTransport(handler))
    agent = await make_agent(profile, provider=provider)

    async def generate():
        async with agent.session(Principal.A, REQUEST) as session:
            state = session.provider
            try:
                return await session.execute()
            finally:
                assert state.pending == {}

    task = asyncio.create_task(generate())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cleaned.is_set()
    # Admission is available again; no child transport task remains.
    async with agent.session(Principal.A, REQUEST):
        pass


async def test_request_deadline_controls_hanging_mock_transport(profile):
    entered = asyncio.Event()

    async def handler(request):
        entered.set()
        await asyncio.Event().wait()

    clock = ManualClock()
    agent = await make_agent(
        profile, provider=ResponsesReplay(httpx.MockTransport(handler)), clock=clock
    )
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    clock.advance(30)
    result = await task
    assert result.output().outcome == "error" and result.diagnostic == "deadline_exceeded"


async def test_privacy_all_local_sinks_and_opaque_state(profile, console):
    hostile = tool()
    hostile["output"][0]["encrypted_content"] = " ".join(CANARIES)
    hostile["id"] = "private-billing-id-should-not-export"
    script = Script([hostile, fixture()])
    agent = await make_agent(profile, provider=ResponsesReplay(httpx.MockTransport(script)))
    tracer = LocalTracer()
    with span("http", tracer=tracer):
        result = await agent.generate(Principal.A, REQUEST)
    encoded = console.getvalue() + json.dumps(tracer.snapshot()) + repr(result)
    assert_private(encoded)
    assert "private-billing-id" not in encoded and "opaque-synthetic" not in encoded


def test_strict_projection_and_versioned_assets_have_no_drift():
    def inspect(node):
        if not isinstance(node, dict):
            return
        assert not ({"oneOf", "discriminator", "default", "const"} & set(node))
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
        for value in node.values():
            if isinstance(value, dict):
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

    inspect(output_schema())
    for definition in provider_tools():
        inspect(definition["parameters"])
    for name, text in assets().items():
        assert (ASSETS / name).read_text(encoding="utf-8") == text
    manifest = json.loads((ASSETS / "manifest.json").read_text())
    assert Counter(c["eligibility"] for c in manifest["cases"])["agent_reachable"] == 28


@pytest.mark.parametrize(
    "source", [{"type": "object", "properties": {}}, {"not": {}}, {"oneOf": [{"type": "string"}]}]
)
def test_projection_rejects_unproven_or_unsupported_schemas(source):
    with pytest.raises(ValueError):
        strict_schema(source)


def test_exact_usage_rate_accounting_not_reasoning_double_counted():
    usage = ActualUsage.from_response(fixture()["usage"])
    assert usage.reasoning_tokens == 20
    assert cost_micro(usage) == 2770  # 500*2 + 200*.1 + 300*2.5 + 100*10
    assert reserve_micro(16000, 2000) == 60000
    assert cost_micro(ActualUsage(input_tokens=1, output_tokens=0, cached_tokens=1)) == 1


async def test_credentials_and_opt_in_never_enable_live_and_stop_drains(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-not-a-key")
    assert Settings.from_env().provider == "fake"
    with pytest.raises(ValueError):
        ResponsesReplay(httpx.AsyncHTTPTransport())
    gate = LiveGate()
    with pytest.raises(AgentFault, match="live_provider_disabled"):
        gate.check()


@pytest.mark.parametrize("duplicate", [False, True])
async def test_unmatched_or_repeated_tool_results_never_reach_second_http(profile, duplicate):
    script = Script([tool()])
    state = ResponsesReplay(httpx.MockTransport(script)).for_request()
    context = ModelInput(
        system=SYSTEM_PROMPT,
        profile=SavedProfile(revision=1, preferences=profile),
        catalog_revision="catalog-v1",
        messages=[],
        tool_schemas=tool_definitions(),
        output_schema=OUTCOME_ADAPTER.json_schema(),
    )
    raw = await state.complete(ProviderRequest(context.model_dump_json().encode(), 1, 6000, 2000))
    call = json.loads(raw)["calls"][0]
    result = {
        "call_id": call["call_id"] if duplicate else "unmatched",
        "name": call["name"],
        "status": "error",
        "error": "invalid_arguments",
    }
    context.messages.append(Message(role="tool", data_json=canonical(result).decode()))
    if duplicate:
        context.messages.append(context.messages[0])
    with pytest.raises(AgentFault, match="malformed_provider_response"):
        await state.complete(ProviderRequest(context.model_dump_json().encode(), 2, 6000, 2000))
    assert len(script.requests) == 1
    state.clear()
    assert not state.history and not state.pending


async def test_replay_principal_admission_and_isolated_native_state(profile):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def handler(request):
        body = json.loads(request.content)
        if len(body["input"]) == 1:
            entered.set()
            await release.wait()
            return response(frames(tool()))
        assert body["input"][-1]["call_id"] == "call.synthetic/one"
        return response(frames(fixture()))

    agent = await make_agent(profile, provider=ResponsesReplay(httpx.MockTransport(handler)))
    first = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    conflict = await agent.generate(Principal.A, REQUEST)
    assert conflict.diagnostic == "concurrency_limit"
    second = asyncio.create_task(agent.generate(Principal.B, REQUEST))
    release.set()
    results = await asyncio.gather(first, second)
    assert all(r.output().outcome == "plan" and r.metrics.tool_dispatches == 1 for r in results)


@pytest.mark.parametrize("limit", ["tools", "attempts", "input", "output"])
async def test_replay_preserves_request_wide_limits(profile, limit):
    first, second = tool(), tool(call_id="different/native-call")
    if limit == "tools":
        first["output"] = [{**first["output"][-1], "call_id": f"call/{i}"} for i in range(4)]
        values = [first, second]
    elif limit == "attempts":
        values = [first, second, tool(call_id="third/native-call")]
    elif limit == "input":
        first["usage"]["input_tokens"] = 6001
        first["usage"]["total_tokens"] = 6101
        values = [first]
    else:
        first["usage"]["output_tokens"] = 2001
        first["usage"]["total_tokens"] = 3001
        values = [first]
    result, script, _ = await run(profile, values)
    assert result.output().outcome == "error"
    assert result.metrics.provider_requests <= 3 and result.metrics.tool_dispatches <= 4
    assert len(script.requests) <= 3


async def test_even_hypothetical_permit_is_blocked_and_repeated_stop_drains():
    gate = LiveGate()
    gate.enabled = True
    gate.permit = LivePermit(
        ENDPOINT, "gpt-6.1-sol", datetime.now(UTC) + timedelta(hours=1), "none", True
    )
    with pytest.raises(AgentFault, match="real_input_admission_unproven"):
        gate.check()
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def work():
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    task = asyncio.create_task(work())
    gate.track(task)
    await entered.wait()
    await gate.stop()
    await gate.stop()
    assert task.cancelled() and cleaned.is_set()
    with pytest.raises(AgentFault, match="live_provider_disabled"):
        gate.check()


async def test_replay_failure_trace_and_private_protocol_error(profile, console):
    bad = fixture()
    content = bad["output"][0]["content"][0]
    value = json.loads(content["text"])
    value["result"]["plan"]["days"][0]["blocks"][0]["exercise_id"] = "unknown"
    content["text"] = json.dumps(value)
    script = Script([bad, bad])
    agent = await make_agent(profile, provider=ResponsesReplay(httpx.MockTransport(script)))
    tracer = LocalTracer()
    with span("http", tracer=tracer):
        result = await agent.generate(Principal.A, REQUEST)
    assert result.output().outcome == "error"
    assert result.diagnostic == "semantic_repair_exhausted"
    assert result.metrics.provider_requests == 2 and result.metrics.semantic_repairs == 1
    assert result.metrics.input_tokens == 2000 and result.metrics.output_tokens == 200
    records = tracer.snapshot()
    assert len({r["trace_id"] for r in records}) == 1
    assert_private(json.dumps(records) + console.getvalue() + repr(result))
    if os.environ.get("FATA_F302_EVIDENCE") == "1":
        target = Path("docs/implementation/evidence/f3-02-replay-failure-trace.json")
        target.write_text(
            json.dumps(
                {
                    "version": "f3-02-replay-failure-v1",
                    "source": "replay",
                    "fixture": "synthetic_invalid_exercise_then_failed_repair",
                    "outcome": "error",
                    "diagnostic": result.diagnostic,
                    "spans": records,
                    "no_candidate_published": agent.candidates.stats()["lineages"] == 0,
                    "live_provider_requests": 0,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
