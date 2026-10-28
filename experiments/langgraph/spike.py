"""Synthetic-only LangGraph comparison. Never imported by application composition."""

import asyncio
import hashlib
import time
from contextlib import AsyncExitStack, ExitStack, contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Literal, TypedDict
from unittest.mock import patch

import aiosqlite
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langsmith import tracing_context
from pydantic import Field

from future_training.agent.budget import AgentFault, Budget, valid_delay
from future_training.agent.fake import FakeModel, ScriptedFake, response_bytes
from future_training.agent.orchestration import Agent, Run
from future_training.agent.protocol import (
    MAX_REQUEST_BYTES,
    MAX_RESPONSE_BYTES,
    MODEL_ID,
    OUTCOME_ADAPTER,
    OUTPUT_VERSION,
    PROMPT_VERSION,
    RESPONSE_ADAPTER,
    RESULT_ADAPTER,
    SYSTEM_PROMPT,
    TOOL_VERSION,
    FailureKind,
    FinalResponse,
    Message,
    ModelInput,
    ModelPlan,
    ProviderFailure,
    ProviderRequest,
    RefusalResponse,
    ToolCall,
    ToolCallsResponse,
    Usage,
    Wire,
    canonical,
    fake_tokens,
    parse_json,
)
from future_training.agent.tools import ToolResult, tool_definitions
from future_training.domain.catalog import load_catalog
from future_training.domain.validator import VALIDATOR_VERSION, validate_plan
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.schemas import (
    ApiError,
    BudgetLimits,
    ErrorOutcome,
    GenerateRequest,
    SavedProfile,
)

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / ".cache/f203"
CONFIG = {"configurable": {"thread_id": "synthetic-comparison"}, "recursion_limit": 64}
SCENARIOS = (
    "plan",
    "clarify",
    "refusal",
    "repair",
    "invalid_twice",
    "transient",
    "retry_exhausted",
    "malformed",
    "unknown_tool",
    "tool_budget",
    "provider_budget",
    "token_overrun",
    "bad_tool",
    "malformed_tool",
)
VERSIONS = [PROMPT_VERSION, TOOL_VERSION, OUTPUT_VERSION, MODEL_ID, VALIDATOR_VERSION]


class SyntheticProfiles:
    """Read-only fixture, not application persistence or an identity source."""

    def __init__(self):
        self.profile = SavedProfile(
            revision=1,
            preferences={
                "adult": True,
                "goal": "general_strength",
                "equipment": "bodyweight",
                "experience": "beginner",
                "days_per_week": 2,
                "session_minutes": 20,
            },
        )

    async def get(self, principal):
        if principal is not Principal.A:
            raise ServiceError(404, "not_found")
        return self.profile.model_copy(deep=True)


def fixture(scenario):
    if scenario not in SCENARIOS:
        raise ValueError("Unknown synthetic scenario")
    catalog = load_catalog()
    fake = FakeModel(catalog)

    async def invalid(request):
        raw = parse_json(await fake.complete(request))
        raw["output_json"] = '{"outcome":"plan","plan":{}}'
        return response_bytes(request, kind="final", output_json=raw["output_json"])

    def tools(request, name="search_exercises", count=1):
        return response_bytes(
            request,
            kind="tool_calls",
            calls=[
                ToolCall(
                    call_id=f"read-{request.attempt}-{i}",
                    name=name,
                    arguments_json='{"limit":20}' if name == "search_exercises" else "{}",
                ).model_dump()
                for i in range(count)
            ],
        )

    actions = {
        "refusal": [lambda r: response_bytes(r, kind="refusal", reason="policy")],
        "repair": [fake.complete, invalid, fake.complete],
        "invalid_twice": [fake.complete, invalid, invalid],
        "transient": [ProviderFailure(FailureKind.TRANSPORT), fake.complete, fake.complete],
        "retry_exhausted": [ProviderFailure(FailureKind.TRANSPORT)] * 2,
        "malformed": [b"not-json"],
        "unknown_tool": [lambda r: tools(r, "approve_plan"), fake.complete],
        "tool_budget": [lambda r: tools(r, count=4), lambda r: tools(r)],
        "provider_budget": [lambda r: tools(r)] * 3,
        "token_overrun": [
            lambda r: canonical(
                {
                    "kind": "refusal",
                    "finish_reason": "refusal",
                    "response_id": "overrun",
                    "reason": "policy",
                    "usage": {"input_tokens": 16001, "output_tokens": 4001},
                }
            )
        ],
    }
    provider = ScriptedFake(actions[scenario]) if scenario in actions else fake
    agent = Agent(SyntheticProfiles(), catalog, provider=provider)
    if scenario in ("bad_tool", "malformed_tool"):
        dispatch = agent.tools.dispatch

        async def malformed(*args):
            value = await dispatch(*args)
            return value.model_copy(
                update=(
                    {"call_id": "mismatched"} if scenario == "bad_tool" else {"status": "corrupt"}
                )
            )

        agent.tools.dispatch = malformed
    request = GenerateRequest(
        profile_revision=1, preferences_text="choose for me" if scenario == "clarify" else ""
    )
    return agent, request


@contextmanager
def offline():
    """No sockets or hosted callbacks, even if inherited environment enables tracing."""

    def denied(*_args, **_kwargs):
        raise OSError("Experiment network disabled")

    with ExitStack() as stack:
        stack.enter_context(tracing_context(enabled=False))
        for name in (
            "socket.connect",
            "socket.connect_ex",
            "socket.sendto",
            "getaddrinfo",
            "gethostbyname",
            "gethostbyname_ex",
            "gethostbyaddr",
            "getnameinfo",
        ):
            stack.enter_context(patch("socket." + name, denied))
        yield


class Ledger(Wire):
    attempts: int = Field(default=0, ge=0, le=3)
    tools: int = Field(default=0, ge=0, le=4)
    retries: int = Field(default=0, ge=0, le=1)
    repairs: int = Field(default=0, ge=0, le=1)
    input: int = Field(default=0, ge=0)  # Retain reported overages, never clamp.
    output: int = Field(default=0, ge=0)
    uncertain: int = Field(default=0, ge=0, le=3)
    finishes: list[str] = Field(default_factory=list, max_length=3)
    pending: list[int] | None = Field(default=None, min_length=2, max_length=2)

    @classmethod
    def capture(cls, budget):
        return cls(
            **{key: getattr(budget, key) for key in cls.model_fields if key != "pending"},
            pending=list(budget._pending) if budget._pending else None,
        )

    def restore(self):
        budget = Budget()
        for key in type(self).model_fields:
            if key != "pending":
                setattr(budget, key, getattr(self, key))
        budget._pending = tuple(self.pending) if self.pending else None
        return budget


class Payload(Wire):
    schema_version: Literal["synthetic-graph-v1"] = "synthetic-graph-v1"
    scenario: str
    principal_slot: Literal["a"] = "a"
    catalog_revision: str
    catalog_fingerprint: str
    versions: list[str]
    started_epoch: float
    started_monotonic: float
    ledger: Ledger = Field(default_factory=Ledger)
    context: dict | None = None
    response: dict | None = None
    seen: list[str] = Field(default_factory=list, max_length=12)
    calls: list[dict] = Field(default_factory=list, max_length=4)
    call_index: int = 0
    pending: Literal["provider", "tool"] | None = None
    stage: str = "context"
    output_json: str | None = None
    reason: str = "running"
    gated: bool = False
    pause: bool = False


class GraphState(TypedDict):
    payload: dict


class GateFault(Exception):
    """Controlled safe-node failure; retry needs a fresh explicit invocation."""


class GraphRuntime:
    def __init__(
        self,
        path,
        scenario="plan",
        *,
        pause=False,
        fault_gate=False,
        principal=Principal.A,
        wall=time.time,
        monotonic=time.monotonic,
    ):
        self.path = Path(path).resolve()
        if not self.path.is_relative_to(AREA.resolve()) or self.path.suffix != ".sqlite":
            raise ValueError("Checkpoint must stay in ignored experiment area")
        self.scenario, self.pause, self.fault_gate = scenario, pause, fault_gate
        self.principal, self.wall, self.monotonic = principal, wall, monotonic
        self.agent, self.request = fixture(scenario)
        self.run = None
        self.uncertain_resume = False

    async def __aenter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Checkpoint exceeds experiment size guard")
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        try:
            self.conn = await self.stack.enter_async_context(aiosqlite.connect(self.path))
            await self.conn.execute("PRAGMA max_page_count=4096")
            await self.conn.commit()
            saver = AsyncSqliteSaver(
                self.conn,
                serde=JsonPlusSerializer(pickle_fallback=False, allowed_msgpack_modules=None),
            )
            builder = StateGraph(GraphState)
            for name in ("context", "reserve_model", "model", "reserve_tool", "tool", "validate"):
                builder.add_node(name, self.node(name))
            builder.add_node("gate", self.gate)
            builder.add_edge(START, "context")
            for name in (
                "context",
                "reserve_model",
                "model",
                "reserve_tool",
                "tool",
                "validate",
                "gate",
            ):
                builder.add_conditional_edges(
                    name,
                    lambda state: state["payload"]["stage"],
                    {
                        key: key
                        for key in (
                            "context",
                            "reserve_model",
                            "model",
                            "reserve_tool",
                            "tool",
                            "validate",
                            "gate",
                        )
                    }
                    | {"end": END},
                )
            self.graph = builder.compile(checkpointer=saver)
            return self
        except BaseException:
            await self.stack.aclose()
            raise

    async def __aexit__(self, *exc):
        await self.stack.__aexit__(*exc)

    def checked(self, state):
        data = Payload.model_validate(state["payload"])
        if (
            data.scenario != self.scenario
            or self.principal is not Principal.A
            or data.catalog_revision != self.agent.catalog.revision
            or data.catalog_fingerprint != self.agent.catalog.fingerprint()
            or data.versions != VERSIONS
        ):
            raise AgentFault("checkpoint_context_changed", "invalid_request")
        if len(canonical(data.model_dump())) > 131072:
            raise AgentFault("checkpoint_state_too_large", "budget_exceeded")
        if data.context is not None:
            context = ModelInput.model_validate(data.context)
            if (
                context.profile != self.agent.profiles.profile
                or context.request_text != self.request.preferences_text
                or context.system != SYSTEM_PROMPT
                or context.previous_plan is not None
                or context.tool_schemas != tool_definitions()
                or context.output_schema != OUTCOME_ADAPTER.json_schema()
            ):
                raise AgentFault("checkpoint_context_changed", "invalid_request")
            # Persisted tool messages are untrusted data on restoration too.
            calls = {}
            for message in context.messages:
                if message.role == "assistant":
                    for raw in parse_json(message.data_json)["calls"]:
                        call = ToolCall.model_validate(raw)
                        calls[call.call_id] = call
                elif message.role == "tool":
                    result = ToolResult.model_validate_json(message.data_json)
                    if result.call_id not in calls:
                        raise AgentFault("tool_result_mismatch")
                    self.agent.tools.checked_bytes(context.profile, calls[result.call_id], result)
        self.run.deadline.check()
        return data

    def error(self, data, exc):
        self.run.budget.unknown("unclassified_failure")
        return data.model_copy(
            update={
                "ledger": Ledger.capture(self.run.budget),
                "pending": None,
                "stage": "end",
                "reason": exc.reason,
                "output_json": ErrorOutcome(
                    outcome="error", error=ApiError(code=exc.code, retryable=exc.retryable)
                ).model_dump_json(),
            }
        )

    def node(self, name):
        async def execute(state):
            data = Payload.model_validate(state["payload"])
            self.run.budget = data.ledger.restore()
            try:
                data = self.checked(state)
                if self.uncertain_resume and data.pending:
                    raise AgentFault("uncertain_operation_not_replayed")
                data = await getattr(self, "_" + name)(data)
            except AgentFault as exc:
                data = self.error(data, exc)
            except ServiceError as exc:
                data = self.error(data, AgentFault(exc.code, exc.code))
            except (
                ValueError,
                TypeError,
                AttributeError,
            ):
                data = self.error(data, AgentFault("malformed_provider_response"))
            return {
                "payload": data.model_copy(
                    update={"ledger": Ledger.capture(self.run.budget)}
                ).model_dump()
            }

        return execute

    async def _context(self, data):
        profile = await self.agent.profiles.get(self.principal)
        self.run.profile = profile
        context = ModelInput(
            system=SYSTEM_PROMPT,
            profile=profile,
            catalog_revision=self.agent.catalog.revision,
            request_text=self.request.preferences_text,
            messages=[],
            tool_schemas=tool_definitions(),
            output_schema=OUTCOME_ADAPTER.json_schema(),
        )
        return data.model_copy(update={"context": context.model_dump(), "stage": "reserve_model"})

    async def _reserve_model(self, data):
        context = ModelInput.model_validate(data.context)
        encoded = context.model_dump_json().encode()
        if len(encoded) > MAX_REQUEST_BYTES:
            raise AgentFault("provider_input_too_large", "budget_exceeded")
        self.run.budget.reserve(fake_tokens(encoded))
        return data.model_copy(update={"pending": "provider", "stage": "model"})

    async def _model(self, data):
        budget = self.run.budget
        if self.agent.provider.kind != "fake":
            raise AgentFault("live_provider_disabled", "invalid_request")
        context = ModelInput.model_validate(data.context)
        request = ProviderRequest(
            context.model_dump_json().encode(),
            budget.attempts,
            budget._pending[0],
            budget._pending[1],
        )
        try:
            raw = await self.agent.provider.complete(request)
        except ProviderFailure as exc:
            if exc.usage is None:
                budget.unknown(exc.kind.value)
            else:
                budget.settle(Usage.model_validate(exc.usage.model_dump()), exc.kind.value)
            if exc.kind not in (
                FailureKind.TRANSPORT,
                FailureKind.UNAVAILABLE,
                FailureKind.RATE_LIMIT,
            ):
                raise AgentFault("provider_fatal") from None
            if not valid_delay(exc.retry_after_seconds):
                raise AgentFault("invalid_retry_delay") from None
            budget.retry()
            if exc.retry_after_seconds:
                await self.agent.clock.wait_until(self.agent.clock.now() + exc.retry_after_seconds)
            return data.model_copy(update={"pending": None, "stage": "reserve_model"})
        if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE_BYTES:
            raise AgentFault("provider_response_too_large_or_invalid")
        parsed = parse_json(raw)
        response = RESPONSE_ADAPTER.validate_python(parsed)
        body = {key: value for key, value in parsed.items() if key != "usage"}
        if (
            response.usage.input_tokens < request.max_input_tokens
            or response.usage.output_tokens < fake_tokens(canonical(body))
        ):
            budget.settle(response.usage, response.finish_reason, uncertain=True)
            raise AgentFault("provider_usage_underreported")
        budget.settle(response.usage, response.finish_reason)
        update = {"pending": None, "response": response.model_dump(), "stage": "validate"}
        if isinstance(response, ToolCallsResponse):
            ids = [call.call_id for call in response.calls]
            if len(set(ids)) != len(ids) or set(data.seen).intersection(ids):
                raise AgentFault("duplicate_tool_call")
            context.messages.append(
                Message(
                    role="assistant",
                    data_json=canonical(
                        {"calls": [call.model_dump() for call in response.calls]}
                    ).decode(),
                )
            )
            update.update(
                calls=[call.model_dump() for call in response.calls],
                call_index=0,
                seen=data.seen + ids,
                context=context.model_dump(),
                stage="reserve_tool",
            )
        return data.model_copy(update=update)

    async def _reserve_tool(self, data):
        self.run.budget.dispatch()
        return data.model_copy(update={"pending": "tool", "stage": "tool"})

    async def _tool(self, data):
        context = ModelInput.model_validate(data.context)
        call = ToolCall.model_validate(data.calls[data.call_index])
        result = await self.agent.tools.dispatch(self.principal, context.profile, call)
        encoded = self.agent.tools.checked_bytes(context.profile, call, result)
        context.messages.append(Message(role="tool", data_json=encoded.decode()))
        index = data.call_index + 1
        return data.model_copy(
            update={
                "pending": None,
                "context": context.model_dump(),
                "call_index": index,
                "stage": "reserve_tool" if index < len(data.calls) else "gate",
            }
        )

    async def gate(self, state):
        # No effects before interrupt: this node starts over when resumed.
        data = self.checked(state)
        if self.fault_gate:
            raise GateFault("controlled gate failure")
        if data.pause and not data.gated:
            value = interrupt({"code": "synthetic_review", "approval_authority": False})
            if value != {"continue_preview": True}:
                self.run.budget = data.ledger.restore()
                data = self.error(data, AgentFault("invalid_resume", "invalid_request"))
                return {"payload": data.model_dump()}
        return {
            "payload": data.model_copy(
                update={"gated": True, "stage": "reserve_model"}
            ).model_dump()
        }

    async def _validate(self, data):
        context = ModelInput.model_validate(data.context)
        self.run.profile = context.profile
        response = RESPONSE_ADAPTER.validate_python(data.response)
        if isinstance(response, RefusalResponse):
            output = {
                "outcome": "abstain",
                "reason": "unsupported_scope",
                "next_step": "change_supported_preferences",
            }
        elif isinstance(response, FinalResponse):
            # Reuse the accepted independent domain/clarification/abstention policy.
            value, issues = Run._validate(self.run, response.output_json)
            if value is None:
                self.run.budget.repair()
                context.messages.append(
                    Message(
                        role="repair",
                        data_json=canonical(
                            {
                                "issue_codes": issues,
                                "instruction": "Correct output within unchanged constraints.",
                            }
                        ).decode(),
                    )
                )
                context = context.model_copy(update={"repair": True})
                return data.model_copy(
                    update={"context": context.model_dump(), "stage": "reserve_model"}
                )
            output = value.model_dump()
        else:
            raise AgentFault("provider_output_truncated")
        if await self.agent.profiles.get(self.principal) != context.profile:
            raise AgentFault("profile_changed", "stale_profile")
        return data.model_copy(
            update={
                "output_json": canonical(output).decode(),
                "reason": "validated_unpublished",
                "stage": "end",
            }
        )

    async def invoke(self, *, start=False, resume=False):
        try:
            return await self._invoke(start=start, resume=resume)
        except TimeoutError:
            raise AgentFault("deadline_exceeded", "budget_exceeded") from None

    async def _invoke(self, *, start=False, resume=False):
        # Callers cannot supply arbitrary graph state, checkpoint IDs or model/provider kinds.
        if start and resume:
            raise ValueError("Choose start or resume")
        invoked_epoch, invoked_monotonic = self.wall(), self.monotonic()
        with offline():
            # Bound initial local checkpoint loading too; no adapter retries.
            async with asyncio.timeout(2):
                snapshot = await self.graph.aget_state(CONFIG)
            existing = snapshot.values.get("payload")
            if start and existing:
                raise ValueError("Thread already started")
            if not start and not existing:
                raise ValueError("Checkpoint not found")
            data = (
                Payload.model_validate(existing)
                if existing
                else Payload(
                    scenario=self.scenario,
                    catalog_revision=self.agent.catalog.revision,
                    catalog_fingerprint=self.agent.catalog.fingerprint(),
                    versions=VERSIONS,
                    started_epoch=invoked_epoch,
                    started_monotonic=invoked_monotonic,
                    pause=self.pause,
                )
            )
            wall_elapsed = self.wall() - data.started_epoch
            monotonic_elapsed = self.monotonic() - data.started_monotonic
            if min(wall_elapsed, monotonic_elapsed) < 0:
                raise AgentFault("checkpoint_clock_regressed", "budget_exceeded")
            # Same-machine, same-boot process restart only. A wall-clock setback
            # cannot extend the original allowance; a monotonic setback fails closed.
            elapsed = max(wall_elapsed, monotonic_elapsed)
            if elapsed >= BudgetLimits().deadline_seconds:
                raise AgentFault("deadline_exceeded", "budget_exceeded")
            self.uncertain_resume = bool(existing and data.pending)
            async with self.agent.session(
                self.principal, self.request, started_at=self.agent.clock.now() - elapsed
            ) as run:
                self.run = run
                run.profile = (
                    ModelInput.model_validate(data.context).profile if data.context else None
                )
                if data.stage == "end":
                    self.checked({"payload": data.model_dump()})
                    self.verify_output(data)
                    run.deadline.check()
                    return data
                value = (
                    {"payload": data.model_dump()}
                    if start
                    else (Command(resume={"continue_preview": True}) if resume else None)
                )
                result = await self.graph.ainvoke(value, CONFIG, durability="sync")
                data = Payload.model_validate(result["payload"])
                if data.stage == "end":
                    self.verify_output(data)
                run.deadline.check()
                return data

    def verify_output(self, data):
        output = RESULT_ADAPTER.validate_json(data.output_json)
        if isinstance(output, ModelPlan):
            profile = ModelInput.model_validate(data.context).profile
            if not validate_plan(output.plan, profile.preferences, self.agent.catalog).valid:
                raise AgentFault("restored_output_invalid")

    async def inspect(self):
        with offline():
            snapshot = await self.graph.aget_state(CONFIG)
            stages = [
                row.values["payload"]["stage"]
                async for row in self.graph.aget_state_history(CONFIG, limit=64)
                if "payload" in row.values
            ]
        data = Payload.model_validate(snapshot.values["payload"])
        counts = {}
        for name in ("checkpoints", "writes"):
            async with self.conn.execute(f"SELECT count(*) FROM {name}") as cursor:
                counts[name] = (await cursor.fetchone())[0]
        storage = {
            name: target.stat().st_size if target.exists() else 0
            for name, target in (
                ("main", self.path),
                ("wal", Path(str(self.path) + "-wal")),
                ("shm", Path(str(self.path) + "-shm")),
            )
        }
        return {
            "next": list(snapshot.next),
            "stage": data.stage,
            "reason": data.reason,
            "metrics": asdict(data.ledger.restore().metrics()),
            "tables": counts,
            "context_restored": data.context is not None,
            "pending": data.pending,
            "file_bytes": self.path.stat().st_size,
            "storage_bytes": storage | {"total": sum(storage.values())},
            "context_sha256": hashlib.sha256(canonical(data.context)).hexdigest(),
            "history_stages": list(reversed(stages)),
        }
