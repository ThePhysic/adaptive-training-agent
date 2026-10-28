"""Ratified count-aware Responses pathway, exclusively local synthetic replay."""

import asyncio
from dataclasses import dataclass, field
from uuid import uuid4

import httpx

from future_training.agent.budget import AgentFault
from future_training.agent.protocol import (
    MAX_RESPONSE_BYTES,
    FailureKind,
    ProviderFailure,
    ProviderRequest,
    Usage,
    canonical,
    parse_json,
)
from future_training.persistence.counted_spending import PairReservation
from future_training.persistence.spending import LedgerFault
from future_training.providers.accounting import MODEL, ActualUsage
from future_training.providers.counting import FrozenPayload
from future_training.providers.http import LocalTLS
from future_training.providers.responses import ResponseSession, read_stream


@dataclass(frozen=True, repr=False)
class CountTicket:
    context: bytes = field(repr=False)
    native: bytes = field(repr=False)
    frozen: FrozenPayload = field(repr=False)
    pair: PairReservation
    counted_input: int


class CountedResponseSession(ResponseSession):
    counted = True

    def __init__(self, parent):
        super().__init__(parent)
        self.count_requests = self.generation_requests = self.wire_requests = 0
        self._ticket = None
        self._pairs = []
        self._base = None
        self._failed = False
        self._busy = False

    @property
    def count_request_bytes(self):
        return self.http.count_request_bytes

    @property
    def generation_request_bytes(self):
        return self.http.generation_request_bytes

    def clear(self):
        self._ticket = None
        for pair in self._pairs:
            self.parent.ledger.invalidate(pair)
        self._pairs.clear()
        self._base = None
        super().clear()

    async def aclose(self):
        try:
            for pair in tuple(self._pairs):
                await self._abandon(pair)
        finally:
            await super().aclose()

    def _check(self):
        self._before_send()
        if (
            self.closed
            or self._failed
            or type(self.parent.transport) not in (httpx.MockTransport, LocalTLS)
        ):
            raise AgentFault("count_protocol_failure")
        if self.deadline is None:
            raise AgentFault("count_protocol_failure")
        self.deadline.check()

    def _claim(self, kind):
        self._check()
        if self.wire_requests >= 6:
            raise AgentFault("wire_exhausted", "budget_exceeded")
        if kind == "count":
            if self.count_requests >= 3:
                raise AgentFault("count_call_limit", "budget_exceeded")
            self.count_requests += 1
        else:
            if self.generation_requests >= 3:
                raise AgentFault("provider_budget_exhausted", "budget_exceeded")
            self.generation_requests += 1
        self.wire_requests += 1

    async def _abandon(self, pair):
        self.parent.ledger.invalidate(pair)
        try:
            await self.parent.ledger.abandon_pair(pair)
        except LedgerFault:
            # Reconciliation fence and worst-case dollars survive an outage.
            pass
        else:
            if pair in self._pairs:
                self._pairs.remove(pair)

    async def admit(self, payload, attempt, input_remaining, output_cap):
        self._check()
        if self._busy or self._ticket is not None:
            raise AgentFault("count_ticket_reused")
        if self.count_requests >= 3 or self.generation_requests >= 3 or self.wire_requests + 2 > 6:
            raise AgentFault("wire_exhausted", "budget_exceeded")
        if not 1 <= input_remaining <= 16000 or not 1 <= output_cap <= 2000:
            raise AgentFault("provider_budget_exhausted", "budget_exceeded")
        self._busy = True
        pair = None
        try:
            request = ProviderRequest(payload, attempt, input_remaining, output_cap)
            context = request.context().model_dump()
            context.pop("messages")
            context.pop("repair")
            base = canonical(context)
            if self._base is not None and base != self._base:
                raise AgentFault("stale_native_state")
            self._base = base
            # 1 user + two preceding outputs (<=12 each) + four tool results
            # + one repair message = at most 30 under the unchanged request caps.
            frozen = FrozenPayload.prepare(self._payload(request), max_items=30)
            native = canonical(self.history)
            project, grant, session = self.parent.scope
            pair = self.parent.make_pair(
                project,
                grant,
                session,
                self.run_id,
                uuid4().hex,
                attempt,
                input_remaining,
                output_cap,
                self.parent.count_ceiling_micro,
            )
            self._pairs.append(pair)
            await self.parent.ledger.reserve_pair(pair)
            self._claim("count")
            async with self.http.counted_stream(
                pair,
                "count",
                frozen,
                check=self._check,
            ) as response:
                body = b""
                async for chunk in response.aiter_bytes():
                    if len(body) + len(chunk) > 1024:
                        raise AgentFault("count_invalid_response")
                    body += chunk
                result = parse_json(body)
            if (
                not isinstance(result, dict)
                or set(result) != {"object", "input_tokens"}
                or result["object"] != "response.input_tokens"
                or type(result["input_tokens"]) is not int
                or not 1 <= result["input_tokens"] <= input_remaining
            ):
                raise AgentFault("count_invalid_or_exceeded")
            self._check()
            await self.parent.ledger.accept_count(pair, result["input_tokens"])
            self._ticket = CountTicket(payload, native, frozen, pair, result["input_tokens"])
            return result["input_tokens"]
        except BaseException as exc:
            self._failed = True
            if pair is not None:
                await self._abandon(pair)
            if isinstance(exc, Exception) and not isinstance(exc, AgentFault):
                raise AgentFault("count_protocol_failure") from None
            raise
        finally:
            self._busy = False

    async def complete(self, request):
        self._check()
        ticket = self._ticket
        self._ticket = None  # Single-use even if the following claim/COMMIT is uncertain.
        if ticket is None:
            raise AgentFault("count_ticket_missing")
        usage = None
        try:
            if (
                request.payload != ticket.context
                or canonical(self.history) != ticket.native
                or request.attempt != ticket.pair.ordinal
                or request.max_input_tokens != ticket.counted_input
                or request.max_output_tokens != ticket.pair.output_cap
            ):
                raise AgentFault("count_payload_mismatch")
            ticket.frozen.assert_unchanged(ticket.frozen.generation)
            self._claim("generation")
            async with self.http.counted_stream(
                ticket.pair, "generation", ticket.frozen, check=self._check
            ) as response:
                final = await read_stream(response)
            try:
                usage = ActualUsage.from_response(final.get("usage"))
            except (
                ValueError,
                KeyError,
                TypeError,
            ):
                await self.parent.ledger.observe_generation(ticket.pair, final)
                raise AgentFault("malformed_provider_response") from None
            self.usages.append(usage)
            await self.parent.ledger.settle_generation(
                ticket.pair,
                usage,
                model=final.get("model"),
                tier=final.get("service_tier"),
            )
            self._check()
            if (
                usage.input_tokens != ticket.counted_input
                or final.get("model") != MODEL
                or final.get("service_tier") != "default"
                or usage.write_12h_tokens
            ):
                raise AgentFault("count_usage_mismatch")
            if final.get("status") == "failed" and final.get("error", {}).get("code") in (
                "server_error",
                "rate_limit_exceeded",
            ):
                # Only the existing Agent owns retry. Known terminal usage is
                # settled; a retry needs a new independent count and pair.
                raise ProviderFailure(
                    FailureKind.UNAVAILABLE,
                    usage=Usage(
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                    ),
                )
            output = self._normalize(final, usage)
            encoded = canonical(output.model_dump())
            if len(encoded) > MAX_RESPONSE_BYTES:
                raise AgentFault("provider_response_too_large_or_invalid")
            return encoded
        except httpx.TransportError:
            self._failed = True
            raise ProviderFailure(FailureKind.TRANSPORT) from None
        except ProviderFailure as exc:
            if exc.usage is None or exc.kind == FailureKind.FATAL:
                self._failed = True
            raise
        except BaseException as exc:
            self._failed = True
            if usage is not None:
                # Authoritative actuals are retained for the owning Agent even
                # on pricing/mismatch errors; never clamp to the counted value.
                if not isinstance(exc, asyncio.CancelledError):
                    raise ProviderFailure(
                        FailureKind.FATAL,
                        usage=Usage(
                            input_tokens=usage.input_tokens,
                            output_tokens=usage.output_tokens,
                        ),
                    ) from None
            if isinstance(exc, Exception) and not isinstance(exc, AgentFault):
                raise ProviderFailure(FailureKind.FATAL) from None
            raise
        finally:
            await self._abandon(ticket.pair)
