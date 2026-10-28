"""Stateless fake: typed read roundtrip then the accepted deterministic baseline."""

from collections.abc import Callable, Sequence

from future_training.domain.baseline import plan_week
from future_training.domain.catalog import Catalog
from future_training.schemas import AbstainOutcome, ClarifyOutcome

from .protocol import (
    FailureKind,
    ModelPlan,
    ProviderFailure,
    ProviderRequest,
    ToolCall,
    Usage,
    canonical,
    fake_tokens,
)
from .tools import ToolResult


def response_bytes(request: ProviderRequest, *, kind: str, **fields) -> bytes:
    content = {
        "kind": kind,
        "finish_reason": {
            "tool_calls": "tool_calls",
            "final": "stop",
            "refusal": "refusal",
            "truncated": "length",
        }[kind],
        "response_id": f"fake-{request.attempt}",
        **fields,
    }
    usage = Usage(
        input_tokens=request.max_input_tokens, output_tokens=fake_tokens(canonical(content))
    )
    return canonical({**content, "usage": usage.model_dump()})


class FakeModel:
    kind = "fake"

    def __init__(self, catalog: Catalog):
        self._catalog = catalog

    async def complete(self, request: ProviderRequest) -> bytes:
        context = request.context()
        if not any(message.role == "tool" for message in context.messages):
            call = ToolCall(
                call_id="catalog-1", name="search_exercises", arguments_json='{"limit":20}'
            )
            return response_bytes(request, kind="tool_calls", calls=[call.model_dump()])
        reads = [
            ToolResult.model_validate_json(message.data_json)
            for message in context.messages
            if message.role == "tool"
        ]
        if any(read.status != "ok" for read in reads):
            return response_bytes(request, kind="refusal", reason="unspecified")
        result = plan_week(
            context.profile.preferences, self._catalog, request_text=context.request_text
        )
        if result.outcome == "plan":
            output = ModelPlan(outcome="plan", plan=result.plan).model_dump()
        elif result.outcome == "clarify":
            fields = (
                ["preferences_text"]
                if result.code == "uninterpreted_request"
                else ["excluded_ids", "excluded_tags", "session_minutes", "equipment"]
            )
            output = ClarifyOutcome(
                outcome="clarify", fields=fields, choices=list(result.choices)
            ).model_dump()
        elif result.outcome == "error":
            raise ProviderFailure(FailureKind.FATAL)
        else:
            output = AbstainOutcome(
                outcome="abstain", reason="infeasible", next_step="change_supported_preferences"
            ).model_dump()
        return response_bytes(request, kind="final", output_json=canonical(output).decode())


class ScriptedFake:
    """Explicit fixture adapter; script position is per-request attempt, never global."""

    kind = "fake"

    def __init__(self, actions: Sequence[bytes | ProviderFailure | Callable]):
        self._actions = tuple(actions)

    async def complete(self, request: ProviderRequest) -> bytes:
        if request.attempt > len(self._actions):
            raise RuntimeError("Scripted fake exhausted")
        action = self._actions[request.attempt - 1]
        if isinstance(action, ProviderFailure):
            raise action
        if callable(action):
            result = action(request)
            # Async fixture actions can implement barrier-controlled faults/hangs.
            import inspect

            return await result if inspect.isawaitable(result) else result
        return action
