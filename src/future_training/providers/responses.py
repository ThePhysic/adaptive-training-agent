"""Responses replay with exact mocks or explicitly counted fixed-loopback TLS.

Recorded synthetic replay is explicit, never real model evidence. State belongs
to one Agent session. No credential reading, default network transport or retry.
"""

from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import ValidationError

from future_training.agent.budget import AgentFault
from future_training.agent.protocol import (
    MAX_REQUEST_BYTES,
    MAX_RESPONSE_BYTES,
    FailureKind,
    FinalResponse,
    ProviderFailure,
    RefusalResponse,
    ToolCall,
    ToolCallsResponse,
    TruncatedResponse,
    Usage,
    canonical,
    parse_json,
)
from future_training.agent.tools import ToolResult
from future_training.domain.duration import (
    PRESETS,
    SECONDS_PER_REPETITION,
    TOLERANCE_SECONDS,
    TRANSITION_SECONDS,
)
from future_training.persistence.spending import Reservation
from future_training.providers.accounting import MODEL, ActualUsage
from future_training.providers.gates import ENDPOINT, LiveGate
from future_training.providers.http import LocalTLS, OfflineHTTP
from future_training.providers.native import item as native_item
from future_training.providers.schemas import output_schema, provider_tools

ASSETS = Path(__file__).resolve().parents[3] / "data/experiments/f3-02/v1"
MAX_STREAM = 65536


class ResponsesReplay:
    kind = "replay"

    def __init__(
        self,
        transport,
        *,
        input_allowances=(6000, 6000, 4000),
        ledger=None,
        scope=None,
        counted=False,
        count_ceiling_micro=None,
    ):
        if type(transport) is not httpx.MockTransport and not (
            type(transport) is LocalTLS and counted is True
        ):
            raise ValueError("Only MockTransport or explicitly counted loopback TLS is supported")
        if (
            not isinstance(input_allowances, tuple)
            or not 1 <= len(input_allowances) <= 3
            or any(type(n) is not int or not 0 <= n <= 16000 for n in input_allowances)
        ):
            raise ValueError("Explicit replay allowances required")
        if (ledger is None) != (scope is None):
            raise ValueError("Ledger and replay project/grant/session scope are paired")
        self.transport, self.allowances = transport, input_allowances
        self.ledger, self.scope = ledger, scope
        if type(counted) is not bool:
            raise ValueError("Explicit counted mode required")
        if counted and (
            ledger is None
            or type(count_ceiling_micro) is not int
            or not 1 <= count_ceiling_micro <= 10**9
        ):
            raise ValueError("Counted replay requires a ledger and positive synthetic quote")
        self.counted, self.count_ceiling_micro = counted, count_ceiling_micro
        self.supervisor = LiveGate()

    async def stop(self):
        await self.supervisor.stop(
            ledger=self.ledger, project=self.scope[0] if self.scope else None
        )

    def for_request(self):
        if self.supervisor.stopped:
            raise AgentFault("live_provider_disabled")
        if self.counted:
            from future_training.providers.counted import CountedResponseSession

            return CountedResponseSession(self)
        return ResponseSession(self)

    def create_http(self):
        if self.counted:
            from future_training.providers.sender import ClaimedHTTP

            return ClaimedHTTP(self.transport, ledger=self.ledger, scope=self.scope)
        return OfflineHTTP(self.transport)

    def make_pair(self, *args):
        from future_training.persistence.counted_spending import PairReservation

        return PairReservation(*args)


class ResponseSession:
    kind = "replay"
    counted = False

    def __init__(self, parent):
        self.parent = parent
        self.run_id = uuid4().hex
        self.history = []
        self.pending = {}
        self.seen_native = set()
        self.consumed = 0
        self.usages = []
        self.closed = False
        self.deadline = None
        self.kind = parent.kind
        self.http = parent.create_http()

    def __repr__(self):
        return "<ResponseSession synthetic-replay>"

    def clear(self):
        self.history.clear()
        self.pending.clear()
        self.seen_native.clear()
        self.closed = True

    async def aclose(self):
        try:
            await self.http.aclose()
        finally:
            self.clear()

    def input_allowance(self, attempt):
        # Fixture upper allowances ONLY. This is explicitly not a live counter.
        if attempt > len(self.parent.allowances):
            raise AgentFault("provider_budget_exhausted", "budget_exceeded")
        return self.parent.allowances[attempt - 1]

    def _payload(self, request):
        context = request.context()
        if len(context.messages) < self.consumed:
            raise AgentFault("malformed_provider_response")
        for message in context.messages[self.consumed :]:
            data = parse_json(message.data_json)
            if message.role == "assistant":
                expected = set(self.pending)
                if set(c["call_id"] for c in data["calls"]) != expected:
                    raise AgentFault("malformed_provider_response")
            elif message.role == "tool":
                result = ToolResult.model_validate(data)
                if result.call_id not in self.pending:
                    raise AgentFault("malformed_provider_response")
                native_id, name = self.pending.pop(result.call_id)
                if result.name != name:
                    raise AgentFault("malformed_provider_response")
                self.history.append(
                    {
                        "type": "function_call_output",
                        "call_id": native_id,
                        "output": canonical(result.model_dump()).decode(),
                    }
                )
            else:
                self.history.append({"role": "developer", "content": canonical(data).decode()})
        self.consumed = len(context.messages)
        if self.pending:
            raise AgentFault("malformed_provider_response")
        settings = parse_json((ASSETS / "config.json").read_bytes())
        settings.pop("endpoint")
        settings.pop("version")
        settings["instructions"] = (ASSETS / "prompt.txt").read_text(encoding="utf-8")
        settings["input"] = [
            {
                "role": "user",
                "content": canonical(
                    {
                        "profile": context.profile.model_dump(),
                        "catalog_revision": context.catalog_revision,
                        "request_text": context.request_text,
                        "previous_plan": context.previous_plan.model_dump()
                        if context.previous_plan
                        else None,
                        "domain_timing": {
                            "presets": {str(k): list(v) for k, v in PRESETS.items()},
                            "seconds_per_repetition": SECONDS_PER_REPETITION,
                            "transition_seconds": TRANSITION_SECONDS,
                            "tolerance_seconds": TOLERANCE_SECONDS,
                            "block_formula": "sets*work+(sets-1)*rest",
                            "session_formula": (
                                "warmup+cooldown+sum(blocks)+(block_count-1)*transition"
                            ),
                        },
                    }
                ).decode(),
            },
            *self.history,
        ]
        settings["tools"] = provider_tools()
        settings["text"] = {
            "format": {
                "type": "json_schema",
                "name": "plan_envelope_v1",
                "strict": True,
                "schema": output_schema(),
            }
        }
        settings["max_output_tokens"] = request.max_output_tokens
        payload = canonical(settings)
        if len(payload) > MAX_REQUEST_BYTES:
            raise AgentFault("provider_budget_exhausted", "budget_exceeded")
        return payload

    async def _send(self, payload):
        if type(self.parent.transport) is not httpx.MockTransport:
            raise AgentFault("live_provider_disabled")
        if self.deadline is not None:
            self.deadline.check()
        if self.parent.supervisor.stopped:
            raise AgentFault("live_provider_disabled")
        # MockTransport has no retry, DNS, proxy, key or socket path. Never
        # accept a caller's AsyncClient with hidden hooks/default transports.
        async with self.http.stream(
            ENDPOINT,
            payload,
            accept="text/event-stream",
            maximum=MAX_STREAM,
            check=self._before_send,
        ) as response:
            final = await read_stream(response)
        return final

    def _before_send(self):
        if self.parent.supervisor.stopped:
            raise AgentFault("live_provider_disabled")
        if self.deadline is not None:
            self.deadline.check()

    async def complete(self, request):
        if self.closed or type(self.parent.transport) is not httpx.MockTransport:
            raise AgentFault("malformed_provider_response")
        payload = self._payload(request)
        usage = None
        reservation = None
        if self.parent.ledger:
            project, grant, session = self.parent.scope
            reservation = Reservation(
                project,
                grant,
                session,
                self.run_id,
                f"{self.run_id}-{request.attempt}",
                request.attempt,
                request.max_input_tokens,
                request.max_output_tokens,
            )
            await self.parent.ledger.reserve(reservation)
            await self.parent.ledger.mark_sent(reservation)
        if self.deadline is not None:
            self.deadline.check()
        try:
            final = await self._send(payload)
            try:
                usage = ActualUsage.from_response(final.get("usage"))
            except (
                ValueError,
                KeyError,
                TypeError,
            ):
                if reservation:
                    await self.parent.ledger.observe_generation(reservation, final)
                raise AgentFault("malformed_provider_response") from None
            # Store only numeric usage, not raw output, identifiers or reasoning.
            self.usages.append(usage)
            if reservation:
                await self.parent.ledger.settle(
                    reservation,
                    usage,
                    model=final.get("model"),
                    tier=final.get("service_tier"),
                )
            if final.get("model") != MODEL or final.get("service_tier") != "default":
                raise AgentFault("provider_fatal")
            if usage.write_12h_tokens:
                raise AgentFault("provider_fatal")
            output = self._normalize(final, usage)
            encoded = canonical(output.model_dump())
            if len(encoded) > MAX_RESPONSE_BYTES:
                raise AgentFault("provider_response_too_large_or_invalid")
            return encoded
        except httpx.TransportError:
            raise ProviderFailure(FailureKind.TRANSPORT) from None
        except (
            KeyError,
            ValueError,
            TypeError,
            ValidationError,
            UnicodeError,
        ):
            if usage is not None:
                raise ProviderFailure(
                    FailureKind.FATAL,
                    usage=Usage(
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                    ),
                ) from None
            raise AgentFault("malformed_provider_response") from None

    def _normalize(self, response, usage):
        common = {
            "response_id": f"response-{len(self.usages)}",
            "usage": Usage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            ),
        }
        status = response.get("status")
        if status == "incomplete":
            return TruncatedResponse(kind="truncated", finish_reason="length", **common)
        if status != "completed":
            raise ProviderFailure(FailureKind.FATAL, usage=common["usage"])
        items = response["output"]
        if not isinstance(items, list) or len(items) > 12:
            raise ValueError("Invalid output")
        calls, text, refused = [], [], False
        pending, seen = {}, set(self.seen_native)
        for item in items:
            native_item(item)
            if item["type"] == "reasoning":
                if set(item) - {"id", "type", "summary", "encrypted_content", "status"}:
                    raise ValueError("Unsupported reasoning item")
                if item.get("summary"):
                    raise ValueError("Reasoning summaries are not accepted")
            elif item["type"] == "function_call":
                native = item["call_id"]
                if (
                    not isinstance(native, str)
                    or not 1 <= len(native.encode()) <= 512
                    or native in seen
                ):
                    raise ValueError("Duplicate or malformed call ID")
                seen.add(native)
                local = f"call-{len(seen)}"
                call = ToolCall(call_id=local, name=item["name"], arguments_json=item["arguments"])
                if len(call.arguments_json.encode()) > 4096:
                    raise ValueError("Oversized arguments")
                calls.append(call)
                pending[local] = (native, call.name)
            elif item["type"] == "message":
                if item.get("role") != "assistant" or item.get("status") != "completed":
                    raise ValueError("Invalid message")
                for part in item["content"]:
                    if part["type"] == "refusal":
                        refused = True
                    elif part["type"] == "output_text":
                        text.append(part["text"])
                    else:
                        raise ValueError("Unsupported content")
            else:
                raise ValueError("Unsupported provider item")
        if calls and (text or refused) or len(calls) > 4:
            raise ValueError("Ambiguous output")
        # Ordered replayable items remain request-local and are cleared at exit.
        if len(canonical([*self.history, *items])) > MAX_REQUEST_BYTES:
            raise ValueError("Continuation too large")
        self.history.extend(items)
        self.pending, self.seen_native = pending, seen
        if calls:
            return ToolCallsResponse(
                kind="tool_calls", finish_reason="tool_calls", calls=calls, **common
            )
        if refused:
            return RefusalResponse(
                kind="refusal", finish_reason="refusal", reason="policy", **common
            )
        if not text:
            raise ValueError("Missing structured output")
        raw = "".join(text)
        try:
            envelope = parse_json(raw)
            result = envelope["result"] if set(envelope) == {"result"} else {}
        except (
            ValueError,
            TypeError,
            KeyError,
        ):
            result = {}  # Existing orchestration owns bounded semantic repair.
        return FinalResponse(
            kind="final",
            finish_reason="stop",
            output_json=canonical(result).decode(),
            **common,
        )


async def read_stream(response):
    """Bound total bytes before decoding; strict UTF-8 and complete SSE frames.

    Deltas are progress only. Terminal response is the sole authoritative usage
    snapshot. A duplicate terminal is rejected, never added a second time.
    """
    buffer = b""
    total = 0
    terminal = None
    completed_items, added_items = {}, {}
    last_sequence = -1
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > MAX_STREAM:
            raise AgentFault("provider_response_too_large_or_invalid")
        buffer += chunk
        # CRLF normalization is done only for complete lines, so split CR/LF
        # and split UTF-8 sequences remain intact in this bytes buffer.
        while b"\n\n" in buffer or b"\r\n\r\n" in buffer:
            lf = buffer.find(b"\n\n")
            crlf = buffer.find(b"\r\n\r\n")
            offset, width = (crlf, 4) if crlf >= 0 and (lf < 0 or crlf < lf) else (lf, 2)
            frame, buffer = buffer[:offset], buffer[offset + width :]
            lines = frame.decode("utf-8", errors="strict").splitlines()
            data, event_name = [], None
            for line in lines:
                if line.startswith(":"):
                    continue
                field, _, value = line.partition(":")
                value = value.removeprefix(" ")
                if field == "data":
                    data.append(value)
                elif field == "event" and event_name is None:
                    event_name = value
                else:
                    raise ValueError("Invalid SSE field")
            if not data:
                continue
            event = parse_json("\n".join(data))
            sequence = event["sequence_number"]
            if (
                type(sequence) is not int
                or sequence <= last_sequence
                or terminal is not None
                or event_name is not None
                and event_name != event["type"]
            ):
                raise ValueError("Invalid stream order")
            last_sequence = sequence
            kind = event["type"]
            if kind.endswith(".delta"):
                if (
                    not isinstance(event.get("delta"), str)
                    or not isinstance(event.get("item_id"), str)
                    or type(event.get("output_index")) is not int
                    or not 0 <= event["output_index"] < 12
                ):
                    raise ValueError("Malformed delta")
                if event["output_index"] in completed_items:
                    raise ValueError("Delta after completed item")
            if kind in ("response.output_item.added", "response.output_item.done"):
                if not isinstance(event.get("item"), dict):
                    raise ValueError("Malformed item event")
                index = event.get("output_index")
                if type(index) is not int or not 0 <= index < 12:
                    raise ValueError("Invalid native index")
                native = event["item"]
                if kind.endswith(".done"):
                    if index in completed_items:
                        raise ValueError("Duplicate completed item")
                    native_item(native, completed=False)
                    if index in added_items and added_items[index] != (
                        native["id"],
                        native["type"],
                    ):
                        raise ValueError("Mismatched native identity")
                    completed_items[index] = native
                else:
                    if index in added_items or index in completed_items:
                        raise ValueError("Repeated item start")
                    if native.get("type") not in ("reasoning", "function_call", "message"):
                        raise ValueError("Unsupported native item")
                    added_items[index] = (native.get("id"), native["type"])
            if kind in ("response.completed", "response.incomplete", "response.failed"):
                terminal = event["response"]
                expected = kind.removeprefix("response.")
                if terminal.get("status") != expected:
                    raise ValueError("Mismatched terminal status")
            elif kind == "error":
                raise ProviderFailure(FailureKind.FATAL)
            elif kind not in {
                "response.created",
                "response.in_progress",
                "response.output_item.added",
                "response.output_item.done",
                "response.content_part.added",
                "response.content_part.done",
                "response.output_text.delta",
                "response.output_text.done",
                "response.function_call_arguments.delta",
                "response.function_call_arguments.done",
                "response.refusal.delta",
                "response.refusal.done",
            }:
                raise ValueError("Unsupported event")
    if buffer.strip() or terminal is None:
        raise ValueError("Incomplete stream")
    output = terminal.get("output")
    if (
        not isinstance(output, list)
        or len(output) > 12
        or set(completed_items) != set(range(len(output)))
        or set(added_items) - set(completed_items)
    ):
        raise ValueError("Missing completed output items")
    identities = set()
    for index, value in enumerate(output):
        native_item(value, completed=terminal["status"] == "completed")
        if value["id"] in identities or canonical(value) != canonical(completed_items[index]):
            raise ValueError("Inconsistent terminal output")
        identities.add(value["id"])
    terminal["output"] = [completed_items[i] for i in range(len(output))]
    return terminal
