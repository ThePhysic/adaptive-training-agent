"""Synthetic native-stream/HTTP/privacy evidence, never a provider capture."""

import asyncio
import copy
import gzip
import json
from fractions import Fraction
from random import Random

import httpx
import pytest
from agent_doubles import make_agent
from responses_doubles import Chunks, fixture, frames, response
from test_observability import CANARIES, assert_private
from test_observability import console as console

from future_training.agent.budget import AgentFault
from future_training.agent.protocol import canonical
from future_training.identity import Principal
from future_training.observability import LocalTracer, span
from future_training.providers.accounting import ActualUsage, cost_micro, proposed_probe_micro
from future_training.providers.gates import ENDPOINT, LiveGate
from future_training.providers.http import OfflineHTTP, destination
from future_training.providers.responses import ResponsesReplay, read_stream
from future_training.schemas import GenerateRequest


def event_bytes(events):
    return b"".join(
        b"data: " + canonical({**e, "sequence_number": i}) + b"\n\n" for i, e in enumerate(events)
    )


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "different",
        "duplicate",
        "index",
        "id",
        "summary",
        "incomplete_call",
        "phase",
        "oversize",
        "unknown",
        "delta_after",
    ],
)
async def test_completed_native_items_must_match_terminal(fault):
    final = fixture("tool")
    items = copy.deepcopy(final["output"])
    events = [
        {"type": "response.output_item.done", "output_index": i, "item": v}
        for i, v in enumerate(items)
    ]
    if fault == "missing":
        events.pop()
    elif fault == "different":
        items[0]["encrypted_content"] = "changed"
    elif fault == "duplicate":
        events.append(copy.deepcopy(events[0]))
    elif fault == "index":
        events[0]["output_index"] = True
    elif fault == "id":
        items[-1]["id"] = items[0]["id"]
    elif fault == "summary":
        items[0]["summary"] = [{"type": "summary_text", "text": "private"}]
    elif fault == "incomplete_call":
        items[-1]["status"] = "in_progress"
    elif fault == "phase":
        items[-1]["phase"] = "unapproved"
    elif fault == "oversize":
        items[0]["encrypted_content"] = "x" * 65537
    elif fault == "unknown":
        items[0]["type"] = "hosted_unknown"
    else:
        events.append(
            {
                "type": "response.function_call_arguments.delta",
                "output_index": 1,
                "item_id": items[-1]["id"],
                "delta": "{}",
            }
        )
    events.append({"type": "response.completed", "response": final})
    with pytest.raises((ValueError, AgentFault)):
        await read_stream(response(event_bytes(events)))


async def test_completed_reasoning_replaces_partial_only_in_memory(profile):
    value = fixture("tool")
    partial = copy.deepcopy(value["output"][0])
    partial["encrypted_content"] = "partial"
    backend_calls = []

    async def handler(request):
        backend_calls.append(json.loads(request.content))
        if len(backend_calls) == 1:
            return response(
                frames(
                    value,
                    prefix=[
                        {"type": "response.output_item.added", "output_index": 0, "item": partial}
                    ],
                )
            )
        return response(frames(fixture()))

    agent = await make_agent(profile, provider=ResponsesReplay(httpx.MockTransport(handler)))
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "plan"
    assert backend_calls[1]["input"][1]["encrypted_content"] == "opaque-synthetic-only"
    assert agent.candidates.stats()["lineages"] == 0


@pytest.mark.parametrize("name", ["plan", "tool", "refusal", "incomplete"])
async def test_native_fixture_roundtrip_with_phase_and_split_bytes(name):
    value = fixture(name)
    for v in value["output"]:
        if v["type"] == "message":
            v["phase"] = "final_answer"
    parsed = await read_stream(response(frames(value), size=1))
    assert parsed == value


@pytest.mark.parametrize(
    "method,url",
    [
        ("GET", ENDPOINT),
        ("post", ENDPOINT),
        ("POST", ENDPOINT + "?x=1"),
        ("POST", ENDPOINT + "#x"),
        ("POST", ENDPOINT + "/"),
        ("POST", ENDPOINT + "/cancel"),
        ("POST", "http://api.openai.com/v1/responses"),
        ("POST", "https://api.openai.com:444/v1/responses"),
        ("POST", "https://api.openai.com.evil.invalid/v1/responses"),
        ("POST", "https://secret@api.openai.com/v1/responses"),
        ("POST", "https://api.openai.com/v1/%72esponses"),
        ("POST", "https://127.0.0.1/v1/responses"),
    ],
)
def test_destination_denies_noncanonical_addresses(method, url):
    with pytest.raises(AgentFault):
        destination(method, url)


async def test_single_client_no_proxy_retry_or_credential_inheritance(monkeypatch):
    for name in ("HTTPS_PROXY", "ALL_PROXY", "SSL_CERT_FILE", "OPENAI_API_KEY"):
        monkeypatch.setenv(name, "synthetic-private-invalid")
    calls = []

    async def handler(request):
        calls.append(request)
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"ok": True})

    wire = OfflineHTTP(httpx.MockTransport(handler))
    first = await wire.client()
    for url in (ENDPOINT, ENDPOINT + "/input_tokens"):
        async with wire.stream(url, b"{}", accept="application/json", maximum=100) as r:
            assert await r.aread() == b'{"ok":true}'
        assert await wire.client() is first
    await wire.aclose()
    assert first.is_closed and len(calls) == 2
    with pytest.raises(AgentFault):
        await wire.client()
    with pytest.raises(ValueError):
        OfflineHTTP(httpx.AsyncHTTPTransport(trust_env=False))


@pytest.mark.parametrize("fault", ["redirect", "gzip", "length", "chunked", "mime", "transport"])
async def test_bounded_http_errors_never_retry(fault):
    calls = []

    async def handler(request):
        calls.append(1)
        if fault == "transport":
            raise httpx.ReadError("secret raw detail")
        if fault == "redirect":
            return httpx.Response(307, headers={"location": "https://evil.invalid"})
        headers = {"content-type": "application/json"}
        body = b"{}"
        if fault == "gzip":
            headers["content-encoding"] = "gzip"
            body = gzip.compress(b"x" * 100000)
        if fault == "length":
            headers["content-length"] = "101"
        if fault == "chunked":
            body = b"x" * 101
        if fault == "mime":
            headers["content-type"] = "text/html"
        return httpx.Response(200, headers=headers, stream=Chunks(body, size=7))

    wire = OfflineHTTP(httpx.MockTransport(handler))
    try:
        with pytest.raises(AgentFault):
            async with wire.stream(ENDPOINT, b"{}", accept="application/json", maximum=100) as r:
                await r.aread()
        assert calls == [1]
    finally:
        await wire.aclose()


async def test_gate_shutdown_awaits_owned_tasks_and_cannot_enable_live():
    gate = LiveGate(enabled=True)
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def job():
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    task = asyncio.create_task(job())
    gate.track(task)
    await entered.wait()
    await gate.stop()
    await gate.stop()
    assert cleaned.is_set() and task.cancelled() and not gate._tasks
    with pytest.raises(AgentFault):
        gate.check()


def test_financial_rounding_and_no_unknown_count_tariff():
    parts = [(5333, 1333), (5333, 1333), (5334, 1334)]
    assert (
        sum(
            cost_micro(ActualUsage(input_tokens=i, output_tokens=o, write_30m_tokens=i))
            for i, o in parts
        )
        == 80001
    )
    assert proposed_probe_micro(0) == 80002
    assert proposed_probe_micro(1000) == 83002  # Synthetic arithmetic, not a permit.
    for invalid in (None, True, -1, 0.01):
        with pytest.raises(ValueError):
            proposed_probe_micro(invalid)


def test_rounding_bound_for_reproducible_mixed_cache_workloads():
    random = Random(30304)
    for _ in range(500):
        input_left, output_left, total = 16000, 4000, 0
        for _attempt in range(3):
            inp = random.randint(0, input_left)
            out = random.randint(0, min(2000, output_left))
            cached = random.randint(0, inp)
            written = random.randint(0, inp - cached)
            usage = ActualUsage(
                input_tokens=inp,
                output_tokens=out,
                cached_tokens=cached,
                write_30m_tokens=written,
                reasoning_tokens=out,
            )
            amount = cost_micro(usage)
            exact = (
                2 * (inp - cached - written)
                + Fraction(cached, 10)
                + Fraction(5 * written, 2)
                + 10 * out
            )
            assert 0 <= amount - exact < 1
            input_left -= inp
            output_left -= out
            total += amount
        assert total <= 80002


async def test_shutdown_from_owned_task_cannot_deadlock():
    gate = LiveGate()

    async def owned():
        gate.track(asyncio.current_task())
        await gate.stop()

    task = asyncio.create_task(owned())
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled() and not gate._tasks


async def test_shutdown_denies_future_runs_without_cancelling_the_caller(profile):
    provider = ResponsesReplay(httpx.MockTransport(lambda request: None))
    await provider.stop()
    agent = await make_agent(profile, provider=provider)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error" and result.metrics.provider_requests == 0
    assert not asyncio.current_task().cancelling()


async def test_private_stream_and_errors_remain_absent_from_every_sink(profile, console):
    value = fixture("tool")
    value["output"][0]["encrypted_content"] = " ".join(CANARIES)

    async def handler(request):
        return response(frames(value))

    agent = await make_agent(profile, provider=ResponsesReplay(httpx.MockTransport(handler)))
    tracer = LocalTracer()
    with span("http", tracer=tracer):
        result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert_private(console.getvalue() + json.dumps(tracer.snapshot()) + repr(result))
