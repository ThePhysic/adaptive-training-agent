"""F3-03A mock-only count/generate experiment, NOT an enabled provider policy.

The actual mock wire stops at the RATIFIED three combined requests. Six-call
results are pure reference-policy calculations with no transport. No live gate,
Agent budget, PostgreSQL schema or spending authority is changed.
"""

import asyncio

import httpx

from future_training.agent.budget import AgentFault, Budget, Deadline
from future_training.agent.protocol import Usage, canonical, parse_json
from future_training.providers.accounting import MODEL, ActualUsage, reserve_micro
from future_training.providers.counting import COMMON as COMMON
from future_training.providers.counting import COUNT_ENDPOINT as COUNT_ENDPOINT
from future_training.providers.counting import GENERATION_ONLY as GENERATION_ONLY
from future_training.providers.counting import FrozenPayload as FrozenPayload
from future_training.providers.gates import ENDPOINT
from future_training.providers.responses import read_stream


def pair_reservation_micro(input_allowance: int, output_cap: int, count_ceiling_micro: int | None):
    """Reference arithmetic only; None means price unknown, NOT free."""
    if type(count_ceiling_micro) is not int or count_ceiling_micro <= 0:
        raise AgentFault("count_pricing_unverified")
    return reserve_micro(input_allowance, output_cap) + count_ceiling_micro


class CountedMockWire:
    """Interpose before ResponsesReplay using another explicitly local mock.

    Counting prices are invented positive test ceilings. Held amounts below are
    in-memory reference liabilities, never a PostgreSQL/live budget claim.
    """

    def __init__(self, backend, *, deadline: Deadline, synthetic_count_ceiling_micro: int):
        if type(backend) is not httpx.MockTransport:
            raise ValueError("MockTransport required")
        pair_reservation_micro(0, 1, synthetic_count_ceiling_micro)
        self.backend, self.deadline = backend, deadline
        self.count_ceiling = synthetic_count_ceiling_micro
        self.budget = Budget(token_kind="count_aware_synthetic_reference")
        self.count_requests = self.generation_requests = self.wire_requests = 0
        self.count_liability_micro = 0
        self._used_bindings = set()
        self._failed = False
        self._active = False

    def _claim(self, kind):
        self.deadline.check()
        if self._failed or self.wire_requests >= 3:
            raise AgentFault("ratified_combined_call_limit")
        if kind == "count":
            if self.count_requests >= 3:
                raise AgentFault("count_call_limit")
            self.count_requests += 1
            self.count_liability_micro += self.count_ceiling
        else:
            if self.generation_requests >= 3:
                raise AgentFault("provider_budget_exhausted")
            self.generation_requests += 1
        self.wire_requests += 1

    async def __call__(self, request):
        if self._active:
            raise AgentFault("count_scope_in_use")
        if (
            str(request.url) != ENDPOINT
            or request.method != "POST"
            or type(self.backend) is not httpx.MockTransport
        ):
            raise AgentFault("count_payload_invalid")
        self._active = True
        try:
            return await self._exchange(FrozenPayload.prepare(request.content))
        except (
            asyncio.CancelledError,
            AgentFault,
        ):
            # No automatic retry or reuse after cancellation, unknown response,
            # mismatch or error. There is no background child request.
            self._failed = True
            self.budget.unknown("count_protocol_failure")
            raise
        except Exception:
            self._failed = True
            self.budget.unknown("count_protocol_failure")
            raise AgentFault("count_protocol_failure") from None
        finally:
            self._active = False

    async def _exchange(self, frozen):
        # Do not spend/disclose another count when its required generation cannot
        # fit. Failed counts still consume the already-claimed wire allowance.
        if self._failed or self.wire_requests + 2 > 3:
            raise AgentFault("ratified_combined_call_limit")
        if frozen._binding in self._used_bindings:
            raise AgentFault("count_ticket_reused")
        async with httpx.AsyncClient(
            transport=self.backend,
            trust_env=False,
            follow_redirects=False,
            timeout=30,
            headers={"Content-Type": "application/json"},
        ) as client:
            self._claim("count")
            async with client.stream(
                "POST",
                COUNT_ENDPOINT,
                content=frozen.counting,
                headers={"Accept": "application/json"},
            ) as response:
                if response.status_code != 200:
                    raise AgentFault("count_unavailable")
                if response.headers.get("content-type", "").split(";")[0] != "application/json":
                    raise AgentFault("count_invalid_response")
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
                or not 1 <= result["input_tokens"] <= 16000 - self.budget.input
            ):
                raise AgentFault("count_invalid_or_exceeded")
            frozen.assert_unchanged(frozen.generation)
            # Snapshot/cap is bound to this specific next attempt; never reused
            # after a generation retry, repair or changed tool continuation.
            self._used_bindings.add(frozen._binding)
            before_input, output_cap = self.budget.reserve(result["input_tokens"])
            if parse_json(frozen.generation)["max_output_tokens"] > output_cap:
                raise AgentFault("provider_budget_exhausted")
            self._claim("generation")
            async with client.stream(
                "POST",
                ENDPOINT,
                content=frozen.generation,
                headers={"Accept": "text/event-stream"},
            ) as response:
                if response.status_code != 200:
                    raise AgentFault("generation_unavailable")
                if response.headers.get("content-type", "").split(";")[0] != "text/event-stream":
                    raise AgentFault("malformed_provider_response")
                final = await read_stream(response)
            usage = ActualUsage.from_response(final.get("usage"))
            self.budget.settle(
                Usage(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens),
                final.get("status", "unknown"),
            )
            if (
                usage.input_tokens != before_input
                or final.get("model") != MODEL
                or final.get("service_tier") != "default"
                or usage.write_12h_tokens
            ):
                raise AgentFault("count_usage_mismatch")
            # Return one authoritative terminal frame to the existing adapter;
            # no delta or raw reasoning is exposed to the user or persisted.
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=completed_frames(final),
            )

    def report(self):
        return {
            "source": "mock_protocol_experiment",
            "applied_combined_limit": 3,
            "count_requests": self.count_requests,
            "generation_requests": self.generation_requests,
            "wire_requests": self.wire_requests,
            "input_tokens": self.budget.input,
            "output_tokens": self.budget.output,
            "generation_unknown_attempts": self.budget.uncertain,
            "synthetic_count_liability_micro": self.count_liability_micro,
            "count_pricing_verified": False,
            "durable_count_ledger_implemented": False,
            "live_provider_requests": 0,
        }


def completed_frames(final):
    """Synthetic complete native-item stream for the historical replay harness."""
    events = [
        {"type": "response.output_item.done", "output_index": i, "item": value}
        for i, value in enumerate(final["output"])
    ]
    events.append({"type": "response." + final["status"], "response": final})
    return b"".join(
        b"data: " + canonical({**event, "sequence_number": i}) + b"\n\n"
        for i, event in enumerate(events)
    )


def proposed_schedule_reference(actions):
    """Pure proposed-policy model: no client, network, permits, ledger or Agent change."""
    counts = generations = retries = repairs = reads = 0
    budget = Budget()
    counted = False
    for action in actions:
        if action == "count":
            counts += 1
            counted = True
        elif action == "generation":
            if not counted:
                return "missing_fresh_count"
            generations += 1
            counted = False
        elif action == "retry":
            retries += 1
            counted = False
        elif action == "repair":
            repairs += 1
            counted = False
        elif action == "tool":
            reads += 1
            counted = False
        else:
            return "invalid_action"
        if (
            counts > 3
            or generations > 3
            or counts + generations > 6
            or retries > budget.limits.transport_retries
            or repairs > budget.limits.semantic_repairs
            or reads > budget.limits.read_tools
        ):
            return "proposed_limit_exceeded"
    return "allowed_by_proposal_only"
