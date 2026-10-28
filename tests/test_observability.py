import asyncio
import io
import json
import logging
import os
import socket
from pathlib import Path

import pytest
from agent_doubles import Hanging, invalid_final, tool_response
from profile_doubles import MemoryProfiles
from stream_doubles import Exchange, stream_app
from test_identity_profiles import client_for

from future_training.agent.fake import ScriptedFake
from future_training.api import create_app
from future_training.config import Settings
from future_training.identity import LocalBoundary
from future_training.observability import LocalTracer, Span, configure_logging, span

CANARIES = ("sk-synthetic-secret-canary-9481", "synthetic.person@example.invalid", "555-010-9876")
A = {"X-Synthetic-Principal": "synthetic-a"}
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def console():
    names = ("", "uvicorn", "uvicorn.error", "uvicorn.access", "future_training.trace")
    previous = [
        (
            logging.getLogger(n),
            list(logging.getLogger(n).handlers),
            logging.getLogger(n).level,
            logging.getLogger(n).propagate,
        )
        for n in names
    ]
    output = io.StringIO()
    configure_logging(output)
    try:
        yield output
    finally:
        for logger, handlers, level, propagate in previous:
            logger.handlers[:] = handlers
            logger.setLevel(level)
            logger.propagate = propagate


def assert_private(output):
    for value in (
        *CANARIES,
        "synthetic-a",
        "synthetic-b",
        "exercise_id",
        "idempotency_key",
        "authorization",
        "preferences_text",
        "repetitions_per_set",
    ):
        assert value not in output


async def test_induced_failure_is_correlated_without_content(profile, console):
    tracer = LocalTracer()
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=MemoryProfiles(),
        provider=ScriptedFake([tool_response, invalid_final, invalid_final]),
        tracer=tracer,
    )
    async with client_for(app) as client:
        await client.put(
            "/api/v1/profile", headers=A, json={"expected_revision": 0, "preferences": profile}
        )
        response = await client.post(
            "/api/v1/drafts/stream", headers=A, json={"profile_revision": 1}
        )
    assert '"outcome":"error"' in response.text
    trace = [r for r in tracer.snapshot() if r["trace_id"] == response.headers["x-request-id"]]
    assert {r["stage"] for r in trace} >= {
        "http",
        "agent.session",
        "agent.execute",
        "provider",
        "tool",
        "validation",
        "stream.terminal",
    }
    run = next(r for r in trace if r["stage"] == "agent.execute")
    assert run["attributes"]["reason"] == "semantic_repair_exhausted"
    assert {
        key: run["attributes"][key]
        for key in ("provider_requests", "tool_dispatches", "semantic_repairs")
    } == {"provider_requests": 3, "tool_dispatches": 1, "semantic_repairs": 1}
    assert run["attributes"]["input_tokens"] > 0
    assert run["attributes"]["output_tokens"] > 0
    assert run["attributes"]["catalog_revision"] == "catalog-v1"
    ids = {r["span_id"] for r in trace}
    assert all(r["parent_id"] in ids for r in trace if r["parent_id"])
    assert all(r["duration_ms"] >= 0 for r in trace)
    assert all(
        json.loads(f.split("\ndata: ")[1])["request_id"] == response.headers["x-request-id"]
        for f in response.text.strip().split("\n\n")
    )
    assert_private(json.dumps(trace) + console.getvalue())
    if os.environ.get("FATA_WRITE_EVIDENCE") == "1":
        (ROOT / "docs/implementation/evidence/f1-07-failure-trace.json").write_text(
            json.dumps(trace, indent=2) + "\n", encoding="utf-8"
        )


@pytest.mark.parametrize("canary", CANARIES)
async def test_canaries_never_reach_configured_sinks(profile, console, canary, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", canary)
    monkeypatch.setenv("ANTHROPIC_API_KEY", canary)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", canary)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", canary)
    tracer = LocalTracer()

    def fail(request):
        raise RuntimeError(canary)

    app = create_app(
        settings=Settings(local_development="1"),
        profiles=MemoryProfiles(),
        tracer=tracer,
        provider=ScriptedFake([fail]),
    )
    # Headers, URL/query, rejected body, arbitrary prompt and forged trace headers.
    async with client_for(app) as client:
        await client.put(
            "/api/v1/profile", headers=A, json={"expected_revision": 0, "preferences": profile}
        )
        headers = {**A, "Authorization": canary, "X-Request-ID": canary, "traceparent": canary}
        await client.post(
            "/api/v1/drafts/stream",
            headers=headers,
            json={"profile_revision": 1, "preferences_text": canary},
        )
        await client.get("/api/v1/plans/" + canary + "?owner=" + canary, headers=headers)
        await client.put("/api/v1/profile", headers=headers, json={"secret": canary})
    for name in ("uvicorn.error", "uvicorn.access", "httpx", "psycopg", "future_training.trace"):
        logging.getLogger(name).error(canary, exc_info=(RuntimeError, RuntimeError(canary), None))
    with Span("provider", tracer=tracer, reason=canary, model_id=canary, owner=canary):
        pass
    assert_private(console.getvalue() + json.dumps(tracer.snapshot()))
    assert app.state.agent.provider.kind == "fake"
    assert all(r["trace_id"] != canary for r in tracer.snapshot())


def test_bounded_allowlist_copy_and_controlled_duration(console):
    clock = iter((1, 1.25, 2, 2.5, 3, 3.75))
    tracer = LocalTracer(2, clock=lambda: next(clock))
    for _ in range(3):
        with Span(
            "validation",
            tracer=tracer,
            outcome="ok",
            profile_revision=True,
            prompt="never stored",
            input_tokens=10**15,
        ):
            pass
    records = tracer.snapshot()
    assert len(records) == 2 and tracer.dropped == 1
    assert [r["duration_ms"] for r in records] == [500, 750]
    assert all(r["attributes"] == {"outcome": "ok"} for r in records)
    records[0]["attributes"]["secret"] = "changed copy"
    assert "secret" not in tracer.snapshot()[0]["attributes"]
    tracer.append({"stage": "not-an-allowed-stage", "secret": "discarded"})
    assert len(tracer.snapshot()) == 2


async def test_concurrent_trace_context_and_cancellation_do_not_cross_requests():
    tracer = LocalTracer()
    barrier = asyncio.Barrier(2)

    async def operation():
        with Span("http", tracer=tracer):
            with span("provider"):
                await barrier.wait()

    await asyncio.gather(operation(), operation())
    traces = tracer.snapshot()
    assert len({r["trace_id"] for r in traces}) == 2
    for root in (r for r in traces if r["stage"] == "http"):
        child = next(r for r in traces if r["parent_id"] == root["span_id"])
        assert child["trace_id"] == root["trace_id"]


async def test_stalled_stream_cancellation_releases_admission(profile):
    hanging = Hanging()
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=MemoryProfiles(),
        provider=ScriptedFake([hanging]),
    )
    async with client_for(app) as client:
        await client.put(
            "/api/v1/profile", headers=A, json={"expected_revision": 0, "preferences": profile}
        )
        request = asyncio.create_task(
            client.post("/api/v1/drafts/stream", headers=A, json={"profile_revision": 1})
        )
        await hanging.started.wait()
        request.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request
        assert hanging.cleaned.is_set()
        hanging.release.set()
        response = await client.post(
            "/api/v1/drafts/stream", headers=A, json={"profile_revision": 1}
        )
        assert '"outcome":"plan"' in response.text
    assert any(r["attributes"]["outcome"] == "cancelled" for r in app.state.tracer.snapshot())


@pytest.mark.parametrize("method", ["gethostbyname", "gethostbyname_ex", "gethostbyaddr"])
def test_additional_dns_paths_are_blocked(method):
    with pytest.raises(OSError, match="External DNS disabled"):
        getattr(socket, method)("external.invalid")


@pytest.mark.parametrize("method", ["connect_ex", "sendto"])
def test_external_tcp_ex_and_udp_are_blocked(method):
    with pytest.raises(OSError, match="External socket I/O disabled"):
        socket.getnameinfo(("198.51.100.1", 443), socket.NI_NAMEREQD)
    with socket.socket(
        type=socket.SOCK_DGRAM if method == "sendto" else socket.SOCK_STREAM
    ) as sock:
        with pytest.raises(OSError, match="External socket I/O disabled"):
            if method == "sendto":
                sock.sendto(b"synthetic", ("198.51.100.1", 443))
            else:
                sock.connect_ex(("198.51.100.1", 443))


async def test_stalled_request_body_is_bounded_before_business_work():
    cleaned = asyncio.Event()

    async def receive():
        try:
            await asyncio.Future()
        finally:
            cleaned.set()

    async def forbidden(scope, receive, send):
        raise AssertionError("Incomplete body cannot reach application")

    messages = []

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "path": "/api/v1/profile",
        "method": "PUT",
        "client": ("127.0.0.1", 1),
        "server": ("127.0.0.1", 8000),
        "headers": [(b"host", b"127.0.0.1:8000"), (b"x-synthetic-principal", b"synthetic-a")],
    }
    await LocalBoundary(forbidden, Settings(local_development="1"), body_timeout=0)(
        scope, receive, send
    )
    assert cleaned.is_set()
    assert messages[0]["status"] == 503
    assert json.loads(messages[1]["body"])["code"] == "budget_exceeded"


async def test_unexpected_preheader_exception_is_sanitized_and_correlated():
    class BrokenProfiles:
        async def get(self, principal):
            raise RuntimeError(CANARIES[0])

    app = create_app(settings=Settings(local_development="1"), profiles=BrokenProfiles())
    async with client_for(app) as client:
        response = await client.get("/api/v1/profile", headers=A)
    assert response.status_code == 503
    assert response.json() == {"code": "internal_error", "retryable": True}
    assert response.headers["x-request-id"] == app.state.tracer.snapshot()[-1]["trace_id"]
    assert_private(json.dumps(app.state.tracer.snapshot()) + response.text)


def test_diagnostic_sink_and_clock_failure_do_not_change_business_result(monkeypatch):
    def broken(*args):
        raise RuntimeError("Synthetic diagnostic failure")

    tracer = LocalTracer(clock=broken)
    monkeypatch.setattr(tracer, "append", broken)
    with Span("approval.transaction", tracer=tracer):
        result = "business-result"
    assert result == "business-result"


async def test_generation_deadline_includes_body_read_time(profile):
    hanging = Hanging()
    app = await stream_app(profile, provider=ScriptedFake([hanging]))
    exchange = Exchange(app)
    original = exchange.incoming.get
    received = False

    async def receive():
        nonlocal received
        message = await original()
        if not received:
            received = True
            app.state.agent.clock.advance(4)
        return message

    task = asyncio.create_task(app(exchange.scope, receive, exchange.send))
    await hanging.started.wait()
    assert any(target == 130 for target, _ in app.state.agent.clock.waiters)
    app.state.agent.clock.advance(26)
    await task
    assert hanging.cleaned.is_set()
    assert app.state.candidates.stats()["lineages"] == 0
