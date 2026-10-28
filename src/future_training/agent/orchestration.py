"""Request-local typed flow. A validated result is a preview, never a candidate.

One Agent composition per process (all instances share admission). The future SSE
adapter must keep session() open through terminalization, recheck its deadline,
and use the existing candidate store only immediately before done(plan).
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import ValidationError

from future_training.candidates import CandidateStore, Reservation
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import Catalog
from future_training.domain.validator import VALIDATOR_VERSION
from future_training.errors import ServiceError
from future_training.identity import Principal, owner_id
from future_training.observability import annotate, span, traced, validate_plan
from future_training.persistence.profiles import ProfileAccess
from future_training.providers.accounting import ActualUsage
from future_training.schemas import (
    AbstainOutcome,
    ApiError,
    CandidateIdentity,
    ClarifyOutcome,
    ErrorOutcome,
    GenerateRequest,
    SavedProfile,
)

from .budget import (
    Admission,
    AgentFault,
    Budget,
    Clock,
    Deadline,
    Metrics,
    SystemClock,
    valid_delay,
)
from .fake import FakeModel
from .protocol import (
    ATTEMPT_OUTPUT_TOKENS,
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
    ModelOutcome,
    ModelPlan,
    ModelProvider,
    ModelResponse,
    ProviderFailure,
    ProviderRequest,
    RefusalResponse,
    ToolCallsResponse,
    Usage,
    canonical,
    fake_tokens,
    parse_json,
)
from .tools import ReadTools, tool_definitions


class State(StrEnum):
    CREATED = "created"
    CONTEXT = "context"
    MODEL = "model"
    TOOLS = "tools"
    VALIDATING = "validating"
    REPAIRING = "repairing"
    READY = "ready_unpublished"
    FAILED = "failed"
    CANCELLED = "cancelled"


_NEXT = {
    State.CREATED: {State.CONTEXT},
    State.CONTEXT: {State.MODEL},
    State.MODEL: {State.TOOLS, State.VALIDATING},
    State.TOOLS: {State.MODEL},
    State.VALIDATING: {State.REPAIRING, State.READY},
    State.REPAIRING: {State.MODEL},
}
_ADMISSION = Admission()
Progress = Callable[[State], Awaitable[None]]


@dataclass(frozen=True)
class RunResult:
    """Immutable unpublished output; output() returns a fresh transport model."""

    canonical_bytes: bytes = field(repr=False)
    metrics: Metrics
    states: tuple[State, ...]
    diagnostic: str
    profile_revision: int | None = None
    catalog_revision: str | None = None
    validator_revision: str = VALIDATOR_VERSION
    prompt_version: str = PROMPT_VERSION
    tool_version: str = TOOL_VERSION
    output_version: str = OUTPUT_VERSION
    model_id: str = MODEL_ID
    provider_usage: tuple[ActualUsage, ...] = ()
    count_requests: int = 0
    wire_requests: int = 0
    count_request_bytes: int = 0
    generation_request_bytes: int = 0
    evidence_source: str = "fake"

    def output(self) -> ModelOutcome | ErrorOutcome:
        return RESULT_ADAPTER.validate_json(self.canonical_bytes)


class Agent:
    def __init__(
        self,
        profiles: ProfileAccess,
        catalog: Catalog,
        *,
        candidates: CandidateStore | None = None,
        provider: ModelProvider | None = None,
        clock: Clock | None = None,
    ):
        self.profiles = profiles
        self.catalog = catalog
        self.candidates = candidates
        self.provider = provider if provider is not None else FakeModel(catalog)
        if self.provider.kind != "fake":
            from future_training.providers.probe import ResponsesProbe
            from future_training.providers.responses import ResponsesReplay

            if type(self.provider) not in (ResponsesReplay, ResponsesProbe):
                raise ValueError(
                    "Live configuration is fake-only; explicit offline replay is supported"
                )
            if type(self.provider) is ResponsesProbe:
                if candidates is not None:
                    raise ValueError("Probe results must remain unpublished")
                if self.provider.kind == "live":
                    self.provider.check_network()
        self.clock = clock if clock is not None else SystemClock()
        self.tools = ReadTools(profiles, catalog)

    @asynccontextmanager
    async def session(
        self,
        principal: Principal,
        request: GenerateRequest,
        *,
        revise: CandidateIdentity | None = None,
        progress: Progress | None = None,
        started_at: float | None = None,
    ) -> AsyncIterator[Run]:
        """Admission + deadline + revision reservation survive execute() until context exit.

        Entry/transport failures are exceptions for the future adapter to translate.
        execute() translates generation failures; external cancellation always propagates.
        Neither entry nor exit publishes a candidate. A reservation is only live here.
        """
        owner_id(principal)
        request = GenerateRequest.model_validate(request.model_dump(warnings=False))
        if revise is not None:
            revise = CandidateIdentity.model_validate(revise.model_dump(warnings=False))
        deadline = Deadline(self.clock, started_at=started_at)
        with span("agent.session"), _ADMISSION.take(principal):
            async with deadline.scope(), AsyncExitStack() as stack:
                run = Run(self, principal, request, revise, progress, deadline, stack)
                try:
                    yield run
                finally:
                    run.closed = True

    async def generate(
        self,
        principal: Principal,
        request: GenerateRequest,
        *,
        revise: CandidateIdentity | None = None,
        progress: Progress | None = None,
    ) -> RunResult:
        """Convenience for offline callers; no terminal publication, including revisions."""
        run = None
        try:
            async with self.session(principal, request, revise=revise, progress=progress) as run:
                result = await run.execute()
            return result
        except AgentFault as exc:
            return _entry_failure(exc.code, exc.retryable, exc.reason)
        except ServiceError as exc:
            return _entry_failure(exc.code, exc.retryable, exc.code)
        except (
            ValidationError,
            AttributeError,
        ):
            return _entry_failure("invalid_request", False, "invalid_request")
        except TimeoutError:
            # Deadline may fire during session cleanup, after execute returned.
            if run is not None:
                if run.states[-1] != State.FAILED:
                    run.states.append(State.FAILED)
                return run._result(
                    ErrorOutcome(outcome="error", error=ApiError(code="budget_exceeded")),
                    "deadline_exceeded",
                )
            return _entry_failure("budget_exceeded", False, "deadline_exceeded")


def _entry_failure(code, retryable, diagnostic):
    output = ErrorOutcome(outcome="error", error=ApiError(code=code, retryable=retryable))
    return RunResult(
        canonical(output.model_dump()),
        Budget().metrics(),
        (State.CREATED, State.FAILED),
        diagnostic,
    )


class Run:
    def __init__(
        self,
        agent: Agent,
        principal: Principal,
        request: GenerateRequest,
        revise: CandidateIdentity | None,
        progress: Progress | None,
        deadline: Deadline,
        stack: AsyncExitStack,
    ):
        self.agent = agent
        self.principal = principal
        self.request = request
        self.revise = revise
        self.progress = progress
        self.deadline = deadline
        self.stack = stack
        self.provider = agent.provider
        self.native_provider = False
        if self.provider.kind != "fake":
            from future_training.providers.probe import ResponsesProbe
            from future_training.providers.responses import ResponsesReplay

            self.native_provider = type(self.provider) in (ResponsesReplay, ResponsesProbe)
        if self.native_provider:
            self.provider = self.provider.for_request()
            self.provider.deadline = deadline
            task = asyncio.current_task()
            self.provider.parent.supervisor.track(task)
            stack.callback(self.provider.parent.supervisor.untrack, task)
            stack.push_async_callback(self.provider.aclose)
        evidence_source = (
            getattr(self.provider.parent, "evidence_source", "replay")
            if self.native_provider
            else "fake"
        )
        self.budget = Budget(
            token_kind=(
                "provider_reported_authority_fixture"
                if evidence_source == "authority_fixture"
                else "provider_reported_counted_live"
                if evidence_source == "live"
                else "provider_reported_counted_replay"
                if getattr(self.provider, "counted", False)
                else "provider_reported_replay"
                if self.provider.kind == "replay"
                else "simulated_utf8_quarters"
            )
        )
        self.states = [State.CREATED]
        self.profile: SavedProfile | None = None
        self.reservation: Reservation | None = None
        self.closed = False
        self.executed = False
        self._task = asyncio.current_task()

    async def _move(self, state: State) -> None:
        self.deadline.check()
        if state not in _NEXT.get(self.states[-1], set()):
            raise RuntimeError("Invalid orchestration transition")
        self.states.append(state)
        annotate(state=state.value)
        if self.progress is not None:
            await self.progress(state)
        self.deadline.check()

    def _result(self, output: ModelOutcome | ErrorOutcome, diagnostic: str) -> RunResult:
        metrics = self.budget.metrics()
        replay = self.native_provider
        evidence_source = (
            getattr(self.provider.parent, "evidence_source", "replay") if replay else "fake"
        )
        model_id = (
            "gpt-6.1-sol"
            if evidence_source == "live"
            else "gpt-6.1-sol-authority-fixture"
            if evidence_source == "authority_fixture"
            else "gpt-6.1-sol-replay"
            if replay
            else MODEL_ID
        )
        prompt_version = "real-planner-prompt-v1" if replay else PROMPT_VERSION
        tool_version = "real-read-tools-v1" if replay else TOOL_VERSION
        output_version = "real-plan-envelope-v1" if replay else OUTPUT_VERSION
        usages = tuple(self.provider.usages) if replay else ()
        annotate(
            state=self.states[-1].value,
            outcome=output.outcome,
            reason=diagnostic,
            provider_requests=metrics.provider_requests,
            tool_dispatches=metrics.tool_dispatches,
            transport_retries=metrics.transport_retries,
            semantic_repairs=metrics.semantic_repairs,
            input_tokens=metrics.input_tokens,
            output_tokens=metrics.output_tokens,
            uncertain_attempts=metrics.uncertain_attempts,
            finish_reason=metrics.finish_reasons[-1] if metrics.finish_reasons else "unknown",
            profile_revision=self.profile.revision if self.profile else 0,
            catalog_revision=self.agent.catalog.revision,
            validator_revision=VALIDATOR_VERSION,
            prompt_version=prompt_version,
            tool_version=tool_version,
            output_version=output_version,
            model_id=model_id,
            token_kind=metrics.token_kind,
            cached_tokens=sum(u.cached_tokens for u in usages),
            cache_write_tokens=sum(u.write_30m_tokens + u.write_12h_tokens for u in usages),
            reasoning_tokens=sum(u.reasoning_tokens for u in usages),
            count_requests=getattr(self.provider, "count_requests", 0),
            wire_requests=getattr(self.provider, "wire_requests", metrics.provider_requests),
            count_request_bytes=getattr(self.provider, "count_request_bytes", 0),
            generation_request_bytes=getattr(self.provider, "generation_request_bytes", 0),
            evidence_source=evidence_source,
        )
        return RunResult(
            canonical(output.model_dump()),
            self.budget.metrics(),
            tuple(self.states),
            diagnostic,
            self.profile.revision if self.profile else None,
            self.agent.catalog.revision,
            model_id=model_id,
            provider_usage=usages,
            prompt_version=prompt_version,
            tool_version=tool_version,
            output_version=output_version,
            count_requests=getattr(self.provider, "count_requests", 0),
            wire_requests=getattr(self.provider, "wire_requests", metrics.provider_requests),
            count_request_bytes=getattr(self.provider, "count_request_bytes", 0),
            generation_request_bytes=getattr(self.provider, "generation_request_bytes", 0),
            evidence_source=evidence_source,
        )

    @traced("agent.execute")
    async def execute(self) -> RunResult:
        if self.closed or self.executed or asyncio.current_task() is not self._task:
            raise RuntimeError("Run can execute only once inside its session")
        self.executed = True
        try:
            output = await self._flow()
            return self._result(output, "validated_unpublished")
        except asyncio.CancelledError:
            self.budget.unknown("cancelled")
            expired = self.agent.clock.now() >= self.deadline.expires
            self.states.append(State.FAILED if expired else State.CANCELLED)
            self._result(
                ErrorOutcome(outcome="error", error=ApiError(code="budget_exceeded")),
                "deadline_exceeded" if expired else "cancelled",
            )
            # Let the existing deadline scope translate its own cancellation.
            raise
        except AgentFault as exc:
            code, retryable, diagnostic = exc.code, exc.retryable, exc.reason
        except ServiceError as exc:
            code, retryable, diagnostic = exc.code, exc.retryable, exc.code
        except Exception:
            # Never log/return provider exceptions, raw text or tool payloads.
            code, retryable, diagnostic = "internal_error", False, "internal_error"
        self.budget.unknown("unclassified_failure")
        self.states.append(State.FAILED)
        return self._result(
            ErrorOutcome(outcome="error", error=ApiError(code=code, retryable=retryable)),
            diagnostic,
        )

    async def _flow(self) -> ModelOutcome:
        await self._move(State.CONTEXT)
        self.profile = SavedProfile.model_validate(
            (await self.agent.profiles.get(self.principal)).model_dump(warnings=False)
        )
        if self.profile.revision != self.request.profile_revision:
            raise AgentFault("profile_changed", "stale_profile")
        previous = None
        if self.revise is not None:
            if self.agent.candidates is None:
                raise AgentFault("revision_store_required", "invalid_request")
            self.reservation = await self.stack.enter_async_context(
                self.agent.candidates.revision(self.principal, self.revise)
            )
            snapshot = await self.agent.candidates.get(self.principal, self.revise.candidate_id)
            previous = snapshot.proposal()
        context = ModelInput(
            system=SYSTEM_PROMPT,
            profile=self.profile.model_copy(deep=True),
            catalog_revision=self.agent.catalog.revision,
            request_text=self.request.preferences_text,
            previous_plan=previous,
            messages=[],
            tool_schemas=tool_definitions(),
            output_schema=OUTCOME_ADAPTER.json_schema(),
        )
        seen_calls = set()
        while True:
            await self._move(State.MODEL)
            response = await self._call(context)
            if isinstance(response, ToolCallsResponse):
                await self._move(State.TOOLS)
                ids = [call.call_id for call in response.calls]
                if len(set(ids)) != len(ids) or seen_calls.intersection(ids):
                    raise AgentFault("duplicate_tool_call")
                seen_calls.update(ids)
                context.messages.append(
                    Message(
                        role="assistant",
                        data_json=canonical(
                            {"calls": [call.model_dump() for call in response.calls]}
                        ).decode(),
                    )
                )
                for call in response.calls:
                    self.deadline.check()
                    self.budget.dispatch()  # Invalid and unknown calls are dispatches too.
                    result = await self.agent.tools.dispatch(self.principal, self.profile, call)
                    encoded = self.agent.tools.checked_bytes(self.profile, call, result)
                    context.messages.append(Message(role="tool", data_json=encoded.decode()))
                    self.deadline.check()
                continue
            await self._move(State.VALIDATING)
            if isinstance(response, RefusalResponse):
                output = AbstainOutcome(
                    outcome="abstain",
                    reason="unsupported_scope",
                    next_step="change_supported_preferences",
                )
            elif isinstance(response, FinalResponse):
                output, issues = self._validate(response.output_json)
                if output is None:
                    with span("agent.repair", state="repairing"):
                        self.budget.repair()
                        await self._move(State.REPAIRING)
                    # No raw invalid output/errors enter the repair prompt. The same
                    # immutable profile and prior context remain authoritative.
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
                    continue
            else:
                raise AgentFault("provider_output_truncated")
            current = await self.agent.profiles.get(self.principal)
            if current != self.profile:
                raise AgentFault("profile_changed", "stale_profile")
            if self.revise is not None:
                # Expiry/supersession during model work must not yield a usable preview.
                await self.agent.candidates.get(self.principal, self.revise.candidate_id)
            await self._move(State.READY)
            return output

    def _validate(self, raw: str) -> tuple[ModelOutcome | None, list[str]]:
        try:
            output = OUTCOME_ADAPTER.validate_python(parse_json(raw))
        except (
            ValidationError,
            ValueError,
            RecursionError,
        ):
            return None, ["structured_output"]
        if isinstance(output, ModelPlan):
            report = validate_plan(output.plan, self.profile.preferences, self.agent.catalog)
            if not report.valid:
                return None, sorted({issue.code for issue in report.issues})[:12]
            if self.request.preferences_text:
                # F1's offline baseline cannot interpret arbitrary constraints in text.
                # Do not quietly ignore them even if a scripted provider returns a plan.
                return self._clarification(["preferences_text"]), []
        elif isinstance(output, ClarifyOutcome):
            fields = set(output.fields)
            supported = set(type(self.profile.preferences).model_fields) | {"preferences_text"}
            if not fields <= supported:
                return None, ["unsupported_clarification_field"]
            output = self._clarification(sorted(fields))
        elif isinstance(output, AbstainOutcome):
            expected = (
                "seek_qualified_professional"
                if output.reason == "medical_context"
                else "change_supported_preferences"
            )
            if output.next_step != expected:
                return None, ["invalid_abstention_step"]
        return output, []

    def _clarification(self, fields: list[str]) -> ClarifyOutcome:
        baseline = plan_week(
            self.profile.preferences, self.agent.catalog, request_text=self.request.preferences_text
        )
        choices = list(baseline.choices) or [
            "Explicitly select supported structured preferences and exclusions before generating."
        ]
        # Never forward unconstrained provider prose as user-facing instructions.
        return ClarifyOutcome(outcome="clarify", fields=fields, choices=choices)

    async def _call(self, context: ModelInput) -> ModelResponse:
        while True:
            self.deadline.check()
            if self.provider.kind not in ("fake", "replay", "live"):
                raise AgentFault("live_provider_disabled", "invalid_request")
            if self.provider.kind in ("replay", "live") and not self.native_provider:
                raise AgentFault("live_provider_disabled", "invalid_request")
            # Revalidate mutable models and bound the entire accumulated context.
            payload = ModelInput.model_validate(context.model_dump()).model_dump_json().encode()
            if len(payload) > MAX_REQUEST_BYTES:
                raise AgentFault("provider_input_too_large", "budget_exceeded")
            if getattr(self.provider, "counted", False):
                if self.budget.attempts >= self.budget.limits.provider_attempts:
                    raise AgentFault("provider_budget_exhausted", "budget_exceeded")
                with span("provider.count", attempt=self.budget.attempts + 1):
                    allowance = await self.provider.admit(
                        payload,
                        self.budget.attempts + 1,
                        self.budget.limits.input_tokens - self.budget.input,
                        min(
                            ATTEMPT_OUTPUT_TOKENS,
                            self.budget.limits.output_tokens - self.budget.output,
                        ),
                    )
            else:
                allowance = (
                    self.provider.input_allowance(self.budget.attempts + 1)
                    if self.provider.kind == "replay"
                    else fake_tokens(payload)
                )
            input_tokens, output_tokens = self.budget.reserve(allowance)
            request = ProviderRequest(payload, self.budget.attempts, input_tokens, output_tokens)
            try:
                with span("provider", attempt=request.attempt):
                    raw = await self.provider.complete(request)
            except ProviderFailure as exc:
                if exc.usage is None:
                    self.budget.unknown(exc.kind.value)
                    if self.provider.kind in ("replay", "live"):
                        raise AgentFault("provider_fatal") from None
                else:
                    usage = Usage.model_validate(exc.usage.model_dump(warnings=False))
                    self.budget.settle(usage, exc.kind.value)
                if exc.kind not in (
                    FailureKind.TRANSPORT,
                    FailureKind.RATE_LIMIT,
                    FailureKind.UNAVAILABLE,
                ):
                    raise AgentFault("provider_fatal") from None
                if not valid_delay(exc.retry_after_seconds):
                    raise AgentFault("invalid_retry_delay") from None
                self.budget.retry()
                self.deadline.check()
                if exc.retry_after_seconds:
                    await self.agent.clock.wait_until(
                        self.agent.clock.now() + exc.retry_after_seconds
                    )
                continue
            try:
                if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE_BYTES:
                    raise AgentFault("provider_response_too_large_or_invalid")
                parsed = parse_json(raw)
                response = RESPONSE_ADAPTER.validate_python(parsed)
                body = {key: value for key, value in parsed.items() if key != "usage"}
                if self.provider.kind == "fake" and (
                    response.usage.input_tokens < input_tokens
                    or response.usage.output_tokens < fake_tokens(canonical(body))
                ):
                    self.budget.settle(response.usage, response.finish_reason, uncertain=True)
                    raise AgentFault("provider_usage_underreported")
            except (
                ValidationError,
                ValueError,
                RecursionError,
            ):
                raise AgentFault("malformed_provider_response") from None
            self.budget.settle(response.usage, response.finish_reason)
            self.deadline.check()
            return response
