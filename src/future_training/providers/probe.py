"""Single unpublished probe assembly; only local authority fixtures can execute.

The same counted sessions, Agent, tools, validator, limits and HTTP cleanup are
used. Real transport retains both unconditional barriers; no CLI or app route.
"""

from contextlib import contextmanager
from contextvars import ContextVar

import httpx

from future_training.agent.budget import AgentFault
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.authority import AuthorityLedger, AuthorityPair
from future_training.providers.authority import approved_preferences
from future_training.providers.counted import CountedResponseSession
from future_training.providers.counting import COUNT_ENDPOINT
from future_training.providers.gates import ENDPOINT, LiveGate
from future_training.providers.http import LocalTLS
from future_training.providers.responses import ResponsesReplay
from future_training.providers.sender import (
    ClaimedHTTP,
    OpenAIHTTPS,
    require_live_financial_authority,
)
from future_training.schemas import GenerateRequest, SavedProfile

_send_context = ContextVar("probe_send_context", default=None)


def consume_network_send(binding, request):
    context = _send_context.get()
    if context is None:
        raise AgentFault("live_provider_disabled")
    ledger, proof = context
    if ledger.execution != "live" or binding != ledger.spec:
        raise AgentFault("live_provider_disabled")
    ledger.consume_send(proof, request.method, str(request.url), request.content)


class ProbeHTTP(ClaimedHTTP):
    def __init__(self, parent):
        if type(parent.ledger) is not AuthorityLedger:
            raise ValueError("Separate authority ledger required")
        self.parent = parent
        if type(parent.transport) is OpenAIHTTPS:
            parent.check_network()
            # Reuse OfflineHTTP's exact owned client, body/framing and close
            # implementation once source review permits this branch, never now.
            self._transport, self._client, self.closed = parent.transport, None, False
            self.ledger, self.scope = parent.ledger, parent.scope
            self.count_request_bytes = self.generation_request_bytes = 0
        else:
            super().__init__(parent.transport, ledger=parent.ledger, scope=parent.scope)

    def pair_type(self):
        return AuthorityPair

    @contextmanager
    def send_scope(self, pair, kind, body):
        proof = self.ledger.authorize_send(pair, kind, body)
        context = _send_context.set((self.ledger, proof))
        try:
            if type(self._transport) is not OpenAIHTTPS:
                self.ledger.consume_send(
                    proof, "POST", COUNT_ENDPOINT if kind == "count" else ENDPOINT, body
                )
            yield
        finally:
            self.ledger.discard_send(proof)
            _send_context.reset(context)

    async def client(self):
        if type(self._transport) is OpenAIHTTPS:
            self.parent.check_network()
        return await super().client()


class ProbeSession(CountedResponseSession):
    def _check(self):
        self._before_send()
        self.parent.spec.checked(positive=True, network=self.kind == "live")
        if self.kind == "live":
            self.parent.check_network()
        elif type(self.parent.transport) not in (httpx.MockTransport, LocalTLS):
            raise AgentFault("live_provider_disabled")
        if self.closed or self._failed or self.deadline is None:
            raise AgentFault("count_protocol_failure")
        self.deadline.check()

    def _payload(self, request):
        context = request.context()
        if (
            context.profile.preferences != approved_preferences()
            or context.profile.revision != 1
            or context.request_text
            or context.previous_plan is not None
        ):
            raise AgentFault("invalid_request", "invalid_request")
        return super()._payload(request)


class ResponsesProbe(ResponsesReplay):
    def __init__(self, ledger, transport, *, gate=None):
        if type(ledger) is not AuthorityLedger:
            raise ValueError("Separate authority ledger required")
        self.spec = ledger.spec.checked(positive=True, network=type(transport) is OpenAIHTTPS)
        if type(transport) not in (httpx.MockTransport, LocalTLS, OpenAIHTTPS):
            raise ValueError("Fixed probe connector required")
        network = type(transport) is OpenAIHTTPS
        if (ledger.execution == "live") != network:
            raise ValueError("Transport and authority execution kind mismatch")
        if gate is not None and type(gate) is not LiveGate:
            raise ValueError("Exact live gate required")
        super().__init__(
            httpx.MockTransport(lambda r: None) if network else transport,
            ledger=ledger,
            scope=(self.spec.project, self.spec.grant, self.spec.session),
            counted=True,
            count_ceiling_micro=self.spec.count_bound.ceiling_micro,
        )
        self.transport = transport
        self.kind = "live" if network else "replay"
        self.evidence_source = "live" if network else "authority_fixture"
        self.supervisor = gate if gate is not None else LiveGate()
        if network and (transport._gate is not self.supervisor or transport._binding != self.spec):
            raise ValueError("Connector and authority binding mismatch")

    def __repr__(self):
        return "<ResponsesProbe bound-redacted>"

    def check_network(self):
        LiveGate.check(self.supervisor)
        require_live_financial_authority()

    def create_http(self):
        return ProbeHTTP(self)

    def make_pair(self, *args):
        return AuthorityPair(*args)

    def for_request(self):
        if self.supervisor.stopped:
            raise AgentFault("live_provider_disabled")
        if self.kind == "live":
            self.check_network()
        return ProbeSession(self)


class FixedProfile:
    async def get(self, principal):
        if principal is not Principal.A:
            raise ServiceError(404, "not_found")
        return SavedProfile(revision=1, preferences=approved_preferences())


class SingleProbe:
    """One explicit run with fixed synthetic input and no candidate authority."""

    def __init__(self, provider: ResponsesProbe, *, clock=None):
        if type(provider) is not ResponsesProbe:
            raise ValueError("Exact probe provider required")
        self.provider, self.clock, self.used = provider, clock, False

    async def run(self):
        from future_training.agent.orchestration import Agent

        if self.used:
            raise AgentFault("invalid_request", "invalid_request")
        self.used = True
        try:
            if self.provider.kind == "live":
                self.provider.check_network()
            agent = Agent(FixedProfile(), load_catalog(), provider=self.provider, clock=self.clock)
            return await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
        finally:
            if self.provider.kind == "live" and not self.provider.transport._closed:
                await self.provider.transport.aclose()
