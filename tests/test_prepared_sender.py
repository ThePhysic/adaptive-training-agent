"""Offline prepared HTTPS gates and claim/transport policy, never live sockets."""

import asyncio
import ssl
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from counted_doubles import RecorderLedger
from test_counted_spending_postgres import pair
from test_observability import console as console
from test_provider_tls import certs as certs
from test_token_admission import prepared

from future_training.agent.budget import AgentFault
from future_training.persistence.spending import LedgerFault
from future_training.providers.counting import COUNT_ENDPOINT
from future_training.providers.gates import ENDPOINT, LiveGate, LivePermit
from future_training.providers.http import LocalTLS, OfflineHTTP, verified_transport
from future_training.providers.responses import ResponsesReplay
from future_training.providers.sender import (
    BearerCredential,
    ClaimedHTTP,
    OpenAIHTTPS,
    provider_request,
)


@pytest.mark.parametrize("supplied", [False, True])
async def test_credentials_environment_and_positive_proposed_permit_cannot_open_network(
    monkeypatch, supplied
):
    for key in ("OPENAI_API_KEY", "FATA_PROVIDER", "FATA_LIVE_ENABLED", "HTTPS_PROXY"):
        monkeypatch.setenv(key, "synthetic-secret-canary")
    gate = (
        LiveGate(
            enabled=True,
            permit=LivePermit(
                endpoint=ENDPOINT,
                model="gpt-6.1-sol",
                grant_id="synthetic-proposed-not-authority",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                owner_approved=True,
            ),
        )
        if supplied
        else LiveGate()
    )
    constructed = []
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **kw: constructed.append(kw))
    wire = OpenAIHTTPS(gate=gate, credential=BearerCredential("synthetic-explicit-secret"))
    try:
        with pytest.raises(AgentFault):
            await wire.handle_async_request(httpx.Request("POST", ENDPOINT, content=b"{}"))
        assert constructed == [] and wire._transport is None
        assert "secret" not in repr(wire)
    finally:
        await wire.aclose()
    assert wire._credential is None


async def test_financial_barrier_independent_of_accidentally_permissive_opt_in(monkeypatch):
    # A deliberate unit fault in the first gate must not activate replay money.
    monkeypatch.setattr(LiveGate, "check", lambda self: None)
    wire = OpenAIHTTPS(credential=BearerCredential("synthetic-only"))
    try:
        with pytest.raises(AgentFault, match="live_provider_disabled"):
            await wire.handle_async_request(httpx.Request("POST", COUNT_ENDPOINT, content=b"{}"))
        assert wire._transport is None
    finally:
        await wire.aclose()


def test_real_connector_rejected_by_replay_and_local_http():
    wire = OpenAIHTTPS()
    with pytest.raises(ValueError):
        OfflineHTTP(wire)
    with pytest.raises(ValueError):
        ResponsesReplay(
            wire, counted=True, ledger=object(), scope=("p", "g", "s"), count_ceiling_micro=1000
        )


@pytest.mark.parametrize(
    "method,url",
    [
        ("GET", ENDPOINT),
        ("POST", "http://api.openai.com/v1/responses"),
        ("POST", ENDPOINT + "/"),
        ("POST", ENDPOINT + "?x=secret"),
        ("POST", "https://api.openai.com:444/v1/responses"),
        ("POST", "https://api.openai.com.evil.invalid/v1/responses"),
        ("POST", "https://user:secret@api.openai.com/v1/responses"),
        ("POST", "https://127.0.0.1/v1/responses"),
        ("POST", ENDPOINT + "#secret"),
        ("POST", "https://api.openai.com/v1/models"),
    ],
)
def test_exact_destination_precedes_credential_use(method, url):
    with pytest.raises(AgentFault, match="provider_destination_denied"):
        provider_request(httpx.Request(method, url, content=b"{}"), None)


@pytest.mark.parametrize(
    "extensions",
    [
        {"sni_hostname": "evil.invalid"},
        {"trace": object()},
        {"target": ("evil.invalid", 443)},
    ],
)
def test_no_routing_or_trace_extension_can_substitute_destination(extensions):
    with pytest.raises(AgentFault, match="provider_destination_denied"):
        provider_request(
            httpx.Request("POST", ENDPOINT, content=b"{}", extensions=extensions),
            BearerCredential("synthetic-secret"),
        )


@pytest.mark.parametrize(
    "url,accept", [(ENDPOINT, "text/event-stream"), (COUNT_ENDPOINT, "application/json")]
)
def test_only_explicit_credential_fixed_headers_and_exact_bytes(url, accept):
    credential = BearerCredential("synthetic-explicit-secret")
    source = httpx.Request(
        "POST",
        url,
        content=b'{"synthetic":true}',
        headers={
            "Host": "evil.invalid",
            "Authorization": "Bearer injected-secret",
            "Cookie": "private-cookie",
            "X-Owner": "private-owner",
            "Accept-Encoding": "gzip",
        },
        extensions={"timeout": {"read": 999999}},
    )
    result = provider_request(source, credential)
    assert result.url == httpx.URL(url) and result.content == source.content
    assert result.headers["host"] == "api.openai.com"
    assert result.headers["authorization"] == "Bearer synthetic-explicit-secret"
    assert result.headers["accept"] == accept and result.headers["accept-encoding"] == "identity"
    assert "cookie" not in result.headers and "x-owner" not in result.headers
    assert result.extensions == {
        "timeout": dict.fromkeys(("connect", "read", "write", "pool"), 30.0)
    }
    assert "secret" not in repr(credential)


@pytest.mark.parametrize("value", ["", "bad\r\nAuthorization:x", "bad token", "界", "x" * 513])
def test_credentials_are_bounded_and_header_injection_rejected(value):
    with pytest.raises(ValueError, match="Invalid explicit credential"):
        BearerCredential(value)


def test_native_tls_factory_ignores_proxy_ca_environment_and_has_no_retry(monkeypatch):
    for name in ("HTTPS_PROXY", "ALL_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR"):
        monkeypatch.setenv(name, "synthetic-invalid-value")
    seen = []
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **kw: seen.append(kw))
    verified_transport()
    assert seen == [{"verify": True, "retries": 0, "trust_env": False}]
    with pytest.raises(AgentFault):
        verified_transport(ssl._create_unverified_context())


@pytest.mark.parametrize("mutation", ["scope", "count_body", "generation_body", "kind"])
async def test_bound_payload_or_scope_rejected_before_claim(profile, mutation):
    frozen = prepared(profile)
    ledger = RecorderLedger()
    body = pair()
    kind = "count"
    if mutation == "scope":
        body = replace(body, project="other-project")
    elif mutation == "count_body":
        frozen = replace(frozen, counting=b"{}")
    elif mutation == "generation_body":
        frozen = replace(frozen, generation=frozen.generation + b" ")
    else:
        kind = "delete"
    wire = ClaimedHTTP(
        httpx.MockTransport(lambda r: pytest.fail("no send permitted")),
        ledger=ledger,
        scope=("project", "grant", "session"),
    )
    try:
        with pytest.raises(AgentFault, match="count_payload_mismatch"):
            async with wire.counted_stream(body, kind, frozen, check=lambda: None):
                pass
        assert ledger.operations == [] and wire._client is None
    finally:
        await wire.aclose()


async def test_claim_acknowledgment_is_awaited_before_transport(profile):
    entered, release = asyncio.Event(), asyncio.Event()

    class Ledger(RecorderLedger):
        async def claim(self, pair, kind):
            entered.set()
            await release.wait()
            await super().claim(pair, kind)

    ledger = Ledger()
    calls = []

    def send(request):
        calls.append(request.content)
        assert ledger.operations == [("count", 1)]
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 1000})

    wire = ClaimedHTTP(
        httpx.MockTransport(send), ledger=ledger, scope=("project", "grant", "session")
    )
    frozen = prepared(profile)

    async def run():
        async with wire.counted_stream(pair(), "count", frozen, check=lambda: None) as response:
            await response.aread()

    task = asyncio.create_task(run())
    try:
        await entered.wait()
        assert calls == [] and wire._client is None
        release.set()
        await task
        assert calls == [frozen.counting] and wire.count_request_bytes == len(frozen.counting)
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)
        await wire.aclose()


@pytest.mark.parametrize(
    "reason", ["reconciliation_pending", "spend_exhausted", "spending_disabled"]
)
async def test_ledger_denial_has_zero_transport_calls(profile, reason):
    class Ledger(RecorderLedger):
        async def claim(self, pair, kind):
            raise LedgerFault(reason)

    wire = ClaimedHTTP(
        httpx.MockTransport(lambda r: pytest.fail("no send")),
        ledger=Ledger(),
        scope=("project", "grant", "session"),
    )
    try:
        with pytest.raises(LedgerFault, match=reason):
            async with wire.counted_stream(pair(), "count", prepared(profile), check=lambda: None):
                pass
        assert wire._client is None and wire.count_request_bytes == 0
    finally:
        await wire.aclose()


async def test_stop_between_acknowledged_claim_and_transport_retains_claim(profile):
    stopped = False

    class Ledger(RecorderLedger):
        async def claim(self, pair, kind):
            nonlocal stopped
            await super().claim(pair, kind)
            stopped = True

    ledger = Ledger()
    wire = ClaimedHTTP(
        httpx.MockTransport(lambda r: pytest.fail("no send")),
        ledger=ledger,
        scope=("project", "grant", "session"),
    )

    def check():
        if stopped:
            raise AgentFault("live_provider_disabled")

    try:
        with pytest.raises(AgentFault):
            async with wire.counted_stream(pair(), "count", prepared(profile), check=check):
                pass
        assert ledger.operations == [("count", 1)] and wire.count_request_bytes == 0
    finally:
        await wire.aclose()


async def test_synthetic_credential_cannot_leak_to_loopback_or_sinks(certs, request, monkeypatch):
    from local_tls_doubles import server, trusted

    from future_training.observability import LocalTracer, Span

    sink = request.getfixturevalue("console")
    secret = "synthetic-explicit-token-canary"
    for name in ("OPENAI_API_KEY", "OPENAI_PROJECT_ID", "HTTPS_PROXY"):
        monkeypatch.setenv(name, secret)
    captures = []

    async def capture(head, body):
        captures.append((head, body))

    tracer = LocalTracer()
    async with server(certs["valid"], on_request=capture) as (port, *_):
        wire = OfflineHTTP(LocalTLS(port, trusted(certs["valid"][0])))
        try:
            outbound = provider_request(
                httpx.Request("POST", ENDPOINT, content=b"{}"), BearerCredential(secret)
            )
            with Span("provider", tracer=tracer, credential=secret):
                client = await wire.client()
                async with client.stream(
                    outbound.method,
                    outbound.url,
                    content=outbound.content,
                    headers=outbound.headers,
                ) as response:
                    assert await response.aread() == b"{}"
        finally:
            await wire.aclose()
    assert len(captures) == 1 and b"authorization" not in captures[0][0].lower()
    assert secret not in str(captures) + str(tracer.snapshot()) + sink.getvalue()
