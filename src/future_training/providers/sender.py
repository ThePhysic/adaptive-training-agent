"""Dormant HTTPS preparation and acknowledged-claim local sending.

The real connector has TWO unconditional admission barriers. No live authority
exists in this repository; replay rows cannot fund it. Tests use only the exact
MockTransport or fixed-loopback LocalTLS accepted by OfflineHTTP.
"""

from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field

import httpx

from future_training.agent.budget import AgentFault
from future_training.persistence.counted_spending import PairReservation
from future_training.providers.counting import COUNT_ENDPOINT, FrozenPayload
from future_training.providers.gates import ENDPOINT, LiveGate
from future_training.providers.http import OfflineHTTP, destination, verified_transport


@dataclass(frozen=True, repr=False)
class BearerCredential:
    value: str = field(repr=False)

    def __post_init__(self):
        if (
            type(self.value) is not str
            or not 1 <= len(self.value) <= 512
            or any(ord(c) < 33 or ord(c) > 126 for c in self.value)
        ):
            raise ValueError("Invalid explicit credential")

    def __repr__(self):
        return "<BearerCredential redacted>"


def provider_request(request, credential, *, binding=None):
    """Pure request construction, testable without enabling either live gate.

    No supplied auth/cookie/Host/trace callback/SNI override/proxy extension is
    forwarded. Only this explicit secret can populate Authorization, AFTER URL
    and body validation. No environment lookup or default credential exists.
    """
    url = destination(request.method, request.url)
    if type(credential) is not BearerCredential:
        raise AgentFault("live_provider_disabled")
    try:
        payload = request.content
    except httpx.RequestNotRead:
        raise AgentFault("provider_input_too_large") from None
    if type(payload) is not bytes or len(payload) > 65536:
        raise AgentFault("provider_input_too_large")
    accept = "application/json" if url.raw_path.endswith(b"/input_tokens") else "text/event-stream"
    # Deny caller-supplied routing/SNI, trace hooks and connection extensions.
    if set(request.extensions) - {"timeout"}:
        raise AgentFault("provider_destination_denied")
    headers = {}
    if binding is not None:
        from future_training.providers.authority import AuthoritySpec

        if type(binding) is not AuthoritySpec:
            raise AgentFault("live_provider_disabled")
        binding.checked(positive=True)
        headers = {"OpenAI-Organization": binding.account, "OpenAI-Project": binding.project}
    return httpx.Request(
        "POST",
        url,
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": accept,
            "Accept-Encoding": "identity",
            "Authorization": "Bearer " + credential.value,
            **headers,
        },
        extensions={"timeout": dict.fromkeys(("connect", "read", "write", "pool"), 30.0)},
    )


def require_live_financial_authority():
    """Independent hard barrier: there is no ratified live ledger capability.

    Current SQL enforces mode=replay and a synthetic count quote. Even a future
    permissive opt-in gate must not turn those records into live send authority.
    Replace only in separately authorized, reviewed live-authority work.
    """
    raise AgentFault("live_provider_disabled")


class OpenAIHTTPS(httpx.AsyncBaseTransport):
    """Prepared real destination connector; unconditionally non-activatable now.

    No client, pool, DNS, TLS handshake or credential use precedes BOTH gates.
    The bounded/owned session HTTP wrapper is still required for future assembly;
    current OfflineHTTP/ResponsesReplay reject this connector outright.
    """

    def __init__(self, *, gate=None, credential=None, binding=None):
        if gate is not None and type(gate) is not LiveGate:
            raise ValueError("Exact live gate required")
        if credential is not None and type(credential) is not BearerCredential:
            raise ValueError("Explicit credential object required")
        self._gate = gate if gate is not None else LiveGate()
        self._credential = credential
        self._binding = binding
        self._transport = None
        self._closed = False

    def __repr__(self):
        return "<OpenAIHTTPS disabled>"

    async def handle_async_request(self, request):
        if self._closed:
            raise AgentFault("provider_transport_closed")
        destination(request.method, request.url)
        LiveGate.check(self._gate)  # Unconditional denial, not an overridable callback.
        require_live_financial_authority()  # Independent unconditional denial.
        from future_training.providers.probe import consume_network_send

        consume_network_send(self._binding, request)
        if self._binding is None:
            raise AgentFault("live_provider_disabled")
        outbound = provider_request(request, self._credential, binding=self._binding)
        if self._transport is None:
            self._transport = verified_transport()
        return await self._transport.handle_async_request(outbound)

    async def aclose(self):
        self._closed = True
        self._credential = None
        self._binding = None
        if self._transport is not None:
            await self._transport.aclose()


class ClaimedHTTP(OfflineHTTP):
    """Same owned bounded HTTP session; sends require acknowledged SQL claims.

    This local implementation cannot accept OpenAIHTTPS or a caller's client.
    Financial reserve remains the counted session's paired atomic operation;
    claim ownership is centralized here immediately before the transport await.
    """

    def __init__(self, transport, *, ledger, scope):
        super().__init__(transport)
        self.ledger, self.scope = ledger, tuple(scope)
        self.count_request_bytes = self.generation_request_bytes = 0

    def pair_type(self):
        return PairReservation

    @contextmanager
    def send_scope(self, pair, kind, body):
        yield

    @asynccontextmanager
    async def counted_stream(self, pair, kind, frozen, *, check):
        if type(pair) is not self.pair_type() or type(frozen) is not FrozenPayload:
            raise AgentFault("count_payload_mismatch")
        if (
            kind not in ("count", "generation")
            or (pair.project, pair.grant, pair.session) != self.scope
        ):
            raise AgentFault("count_payload_mismatch")
        check()
        frozen.assert_unchanged(frozen.generation)
        # Re-project to reject a forged count body or input-affecting changes,
        # not just a changed generation hash. Never persist/log this binding.
        verified = FrozenPayload.prepare(frozen.generation, max_items=30)
        if verified.counting != frozen.counting:
            raise AgentFault("count_payload_mismatch")
        url, body, accept, maximum = (
            (COUNT_ENDPOINT, frozen.counting, "application/json", 1024)
            if kind == "count"
            else (ENDPOINT, frozen.generation, "text/event-stream", 65536)
        )
        # Never send after uncertain/cancelled COMMIT, a reused claim, exhausted
        # grant or shutdown. Existing ledger owns cancellation-safe finalization.
        await self.ledger.claim(pair, kind)
        check()
        if kind == "count":
            self.count_request_bytes += len(body)
        else:
            self.generation_request_bytes += len(body)
        with self.send_scope(pair, kind, body):
            async with self.stream(
                url, body, accept=accept, maximum=maximum, check=check
            ) as response:
                yield response
