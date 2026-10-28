import asyncio
import json

import pytest
from agent_doubles import (
    Hanging,
    ManualClock,
    invalid_final,
    make_agent,
    tool_response,
    valid_final,
)

from future_training.agent.budget import Admission, AgentFault, Budget
from future_training.agent.fake import ScriptedFake
from future_training.agent.orchestration import Agent, State
from future_training.agent.protocol import (
    FailureKind,
    ProviderFailure,
    Usage,
    canonical,
    fake_tokens,
    parse_json,
)
from future_training.identity import Principal
from future_training.schemas import GenerateRequest, ProfileSaveRequest

REQUEST = GenerateRequest(profile_revision=1)


@pytest.mark.parametrize(
    "raw,diagnostic",
    [
        (b"not-json", "malformed_provider_response"),
        (b'{"kind":"invented"}', "malformed_provider_response"),
        (b"{}" * 9000, "provider_response_too_large_or_invalid"),
        ("not-bytes", "provider_response_too_large_or_invalid"),
        (b'{"kind":"final","kind":"refusal"}', "malformed_provider_response"),
        (b"\xff", "malformed_provider_response"),
    ],
)
async def test_malformed_envelopes_retain_unknown_usage_without_retry(profile, raw, diagnostic):
    result = await (await make_agent(profile, provider=ScriptedFake([raw]))).generate(
        Principal.A, REQUEST
    )
    assert result.output().outcome == "error"
    assert result.diagnostic == diagnostic
    assert result.metrics.provider_requests == 1
    assert result.metrics.uncertain_attempts == 1
    assert result.metrics.output_tokens == 2000
    assert result.metrics.input_tokens > 0
    assert result.metrics.transport_retries == result.metrics.semantic_repairs == 0


@pytest.mark.parametrize("kind", list(FailureKind))
@pytest.mark.parametrize("known_usage", [False, True])
async def test_classified_failures_count_attempts_and_only_transient_retry(
    profile, kind, known_usage
):
    failure = ProviderFailure(
        kind, usage=Usage(input_tokens=1, output_tokens=0) if known_usage else None
    )
    result = await (
        await make_agent(profile, provider=ScriptedFake([failure, valid_final]))
    ).generate(Principal.A, REQUEST)
    transient = kind != FailureKind.FATAL
    assert result.output().outcome == ("plan" if transient else "error")
    assert result.metrics.provider_requests == (2 if transient else 1)
    assert result.metrics.transport_retries == int(transient)
    assert result.metrics.uncertain_attempts == int(not known_usage)
    assert result.metrics.finish_reasons[0] == kind.value


async def test_transport_failure_retry_continuation_and_no_fourth_repair(profile):
    failure = ProviderFailure(FailureKind.TRANSPORT)
    result = await (
        await make_agent(
            profile,
            provider=ScriptedFake(
                [
                    failure,
                    tool_response,
                    invalid_final,
                    valid_final,
                ]
            ),
        )
    ).generate(Principal.A, REQUEST)
    assert result.output().error.code == "budget_exceeded"
    assert result.metrics.provider_requests == 3
    assert result.metrics.transport_retries == 1
    assert result.metrics.semantic_repairs == 1
    assert result.metrics.tool_dispatches == 1
    assert result.metrics.uncertain_attempts == 1
    assert result.metrics.output_tokens <= 4000


async def test_continuation_repair_and_no_fourth_transport_attempt(profile):
    failure = ProviderFailure(FailureKind.UNAVAILABLE, usage=Usage(input_tokens=1, output_tokens=0))
    result = await (
        await make_agent(
            profile,
            provider=ScriptedFake(
                [
                    tool_response,
                    invalid_final,
                    failure,
                    valid_final,
                ]
            ),
        )
    ).generate(Principal.A, REQUEST)
    assert result.output().error.code == "budget_exceeded"
    assert result.metrics.provider_requests == 3
    assert result.metrics.semantic_repairs == 1
    assert result.metrics.transport_retries == 1


async def test_continuation_plus_repair_succeeds_with_three_total_requests(profile):
    result = await (
        await make_agent(
            profile,
            provider=ScriptedFake(
                [
                    tool_response,
                    invalid_final,
                    valid_final,
                ]
            ),
        )
    ).generate(Principal.A, REQUEST)
    assert result.output().outcome == "plan"
    assert result.metrics.provider_requests == 3
    assert result.metrics.semantic_repairs == 1
    assert result.metrics.transport_retries == 0


async def test_second_transport_failure_cannot_retry_and_retains_both_uncertain_reservations(
    profile,
):
    failure = ProviderFailure(FailureKind.TRANSPORT)
    result = await (await make_agent(profile, provider=ScriptedFake([failure, failure]))).generate(
        Principal.A, REQUEST
    )
    assert result.output().outcome == "error"
    assert result.metrics.provider_requests == 2
    assert result.metrics.transport_retries == 1
    assert result.metrics.uncertain_attempts == 2
    assert result.metrics.output_tokens == 4000


@pytest.mark.parametrize(
    "counts,expected,success", [([4], 4, True), ([3, 2], 4, False), ([2, 2], 4, True)]
)
async def test_read_tool_cap_is_independent_of_provider_cap(profile, counts, expected, success):
    actions = [lambda r, n=count: tool_response(r, count=n) for count in counts] + [valid_final]
    result = await (await make_agent(profile, provider=ScriptedFake(actions))).generate(
        Principal.A, REQUEST
    )
    assert result.output().outcome == ("plan" if success else "error")
    assert result.metrics.tool_dispatches == expected
    assert result.metrics.provider_requests == (len(counts) + 1 if success else len(counts))
    if not success:
        assert result.diagnostic == "tool_budget_exhausted"


@pytest.mark.parametrize(
    "usage,code",
    [
        ({"input_tokens": 17000, "output_tokens": 10}, "budget_exceeded"),
        ({"input_tokens": 0, "output_tokens": 0}, "provider_failure"),
        ({"input_tokens": 1, "output_tokens": -1}, "provider_failure"),
        ({"input_tokens": True, "output_tokens": 1}, "provider_failure"),
        ({"input_tokens": 17000, "output_tokens": 5000}, "budget_exceeded"),
    ],
)
async def test_underreported_invalid_and_overrun_usage_fail_closed(profile, usage, code):
    def action(request):
        body = parse_json(valid_final(request))
        body["usage"] = usage
        return canonical(body)

    result = await (await make_agent(profile, provider=ScriptedFake([action]))).generate(
        Principal.A, REQUEST
    )
    assert result.output().outcome == "error"
    assert result.output().error.code == code
    assert result.metrics.provider_requests == 1
    if code == "budget_exceeded":
        assert result.metrics.input_tokens == 17000


def test_exact_cumulative_token_boundaries_and_reservations():
    budget = Budget()
    assert budget.reserve(8000) == (8000, 2000)
    budget.settle(Usage(input_tokens=8000, output_tokens=2000), "stop")
    assert budget.reserve(8000) == (8000, 2000)
    budget.settle(Usage(input_tokens=8000, output_tokens=2000), "stop")
    assert (budget.metrics().input_tokens, budget.metrics().output_tokens) == (16000, 4000)
    with pytest.raises(AgentFault, match="provider_budget_exhausted"):
        budget.reserve(0)
    budget = Budget()
    with pytest.raises(AgentFault):
        budget.reserve(16001)
    assert budget.metrics().provider_requests == 0
    for _ in range(3):
        budget.reserve(1)
        budget.settle(Usage(input_tokens=1, output_tokens=0), "stop")
    with pytest.raises(AgentFault):
        budget.reserve(1)
    assert budget.metrics().provider_requests == 3


async def test_hanging_provider_hits_whole_deadline_and_drains_cleanup(profile):
    hanging = Hanging()
    clock = ManualClock()
    agent = await make_agent(profile, provider=ScriptedFake([hanging]), clock=clock)
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await hanging.started.wait()
    await clock.waiting.wait()
    clock.advance(30)
    result = await asyncio.wait_for(task, 2)
    assert result.output().error.code == "budget_exceeded"
    assert result.diagnostic == "deadline_exceeded"
    assert result.metrics.provider_requests == result.metrics.uncertain_attempts == 1
    assert result.metrics.output_tokens == 2000
    assert hanging.cleaned.is_set()
    assert not clock.waiters
    # Admission is released, not leaked by cancellation from the watchdog.
    agent.provider = ScriptedFake([valid_final])
    assert (await agent.generate(Principal.A, REQUEST)).output().outcome == "plan"


async def test_shared_deadline_includes_tool_hangs(profile, monkeypatch):
    agent = await make_agent(profile)
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def hang(*_):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    monkeypatch.setattr(agent.tools, "dispatch", hang)
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    agent.clock.advance(30)
    result = await asyncio.wait_for(task, 2)
    assert result.output().error.code == "budget_exceeded"
    assert result.metrics.provider_requests == result.metrics.tool_dispatches == 1
    assert cleaned.is_set()
    assert not agent.clock.waiters


async def test_deadline_includes_profile_context_reads(profile, monkeypatch):
    agent = await make_agent(profile)
    entered = asyncio.Event()

    async def hang(_):
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(agent.profiles, "get", hang)
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    agent.clock.advance(30)
    result = await asyncio.wait_for(task, 2)
    assert result.output().error.code == "budget_exceeded"
    assert result.metrics.provider_requests == 0


async def test_retry_after_cannot_reset_absolute_deadline(profile):
    clock = ManualClock()
    entered = asyncio.Event()

    def slow_failure(_):
        clock.advance(29)
        entered.set()
        raise ProviderFailure(FailureKind.RATE_LIMIT, retry_after_seconds=2)

    agent = await make_agent(
        profile, provider=ScriptedFake([slow_failure, valid_final]), clock=clock
    )
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await entered.wait()
    clock.advance(1)
    result = await asyncio.wait_for(task, 2)
    assert result.output().error.code == "budget_exceeded"
    assert result.metrics.provider_requests == 1
    assert result.metrics.transport_retries == 1


@pytest.mark.parametrize("delay", [-1, float("nan"), float("inf"), True])
async def test_invalid_provider_retry_delay_is_not_slept(profile, delay):
    failure = ProviderFailure(FailureKind.RATE_LIMIT, retry_after_seconds=delay)
    result = await (await make_agent(profile, provider=ScriptedFake([failure]))).generate(
        Principal.A, REQUEST
    )
    assert result.diagnostic == "invalid_retry_delay"
    assert result.metrics.provider_requests == 1


async def test_external_cancellation_propagates_counts_uncertain_and_releases_admission(profile):
    hanging = Hanging()
    agent = await make_agent(profile, provider=ScriptedFake([hanging]))
    async with agent.session(Principal.A, REQUEST) as run:
        # execute must be cancelled on the session's owning task, as in ASGI.
        async def cancel_owner(owner):
            await hanging.started.wait()
            owner.cancel()

        cancel = asyncio.create_task(cancel_owner(asyncio.current_task()))
        with pytest.raises(asyncio.CancelledError):
            await run.execute()
        await cancel
        assert run.states[-1] == State.CANCELLED
        assert run.budget.metrics().uncertain_attempts == 1
    assert hanging.cleaned.is_set()
    assert not agent.clock.waiters
    agent.provider = ScriptedFake([valid_final])
    assert (await agent.generate(Principal.A, REQUEST)).output().outcome == "plan"


async def test_concurrent_same_principal_rejected_other_principal_allowed_across_agent_instances(
    profile,
):
    hanging = Hanging()
    agent = await make_agent(profile, provider=ScriptedFake([hanging]))
    other = Agent(
        agent.profiles, agent.catalog, provider=ScriptedFake([hanging]), clock=agent.clock
    )
    tasks = [asyncio.create_task(agent.generate(Principal.A, REQUEST))]
    await hanging.started.wait()
    same = await other.generate(Principal.A, REQUEST)
    assert same.output().error.code == "capacity_exceeded"
    entered = asyncio.Event()

    async def second(request):
        entered.set()
        return await hanging(request)

    other.provider = ScriptedFake([second])
    tasks.append(asyncio.create_task(other.generate(Principal.B, REQUEST)))
    await entered.wait()
    rejected = await agent.generate(Principal.B, REQUEST)
    assert rejected.output().error.code == "capacity_exceeded"
    hanging.release.set()
    results = await asyncio.gather(*tasks)
    assert all(result.output().outcome == "plan" for result in results)
    assert (await other.generate(Principal.A, REQUEST)).output().outcome == "plan"


def test_global_limit_and_raw_identity_rejected():
    admission = Admission()
    # There are exactly two authorized identities; exercising two slots proves
    # the global bound without inventing a third production principal.
    with admission.take(Principal.A), admission.take(Principal.B):
        assert admission.active() == 2
        with pytest.raises(AgentFault):
            with admission.take(Principal.A):
                pytest.fail("Admitted third run")
    assert admission.active() == 0


async def test_live_environment_and_credentials_do_not_change_fake_mode(profile, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "FAKE_TEST_ONLY_NOT_A_CREDENTIAL")
    monkeypatch.setenv("MODEL_PROVIDER", "live")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://example.invalid")
    agent = await make_agent(profile)
    assert (await agent.generate(Principal.A, REQUEST)).output().outcome == "plan"

    class Live:
        kind = "live"

        async def complete(self, _):
            pytest.fail("Live adapter invoked")

    with pytest.raises(ValueError, match="fake-only"):
        Agent(agent.profiles, agent.catalog, provider=Live())
    result = await agent.generate("synthetic-a", REQUEST)
    assert result.output().error.code == "unauthorized"


async def test_provider_exception_is_sanitized(profile, caplog):
    def fail(_):
        raise RuntimeError("FAKE_SECRET_RAW_PROMPT")

    agent = await make_agent(profile, provider=ScriptedFake([fail]))
    result = await agent.generate(Principal.A, REQUEST)
    assert result.output().error.code == "internal_error"
    assert result.metrics.uncertain_attempts == 1
    assert "FAKE_SECRET_RAW_PROMPT" not in repr(result) + caplog.text


async def test_injected_fake_cannot_use_external_dns(profile):
    import socket

    def egress(_):
        socket.getaddrinfo("provider.invalid", 443)
        pytest.fail("External DNS escaped the offline guard")

    result = await (await make_agent(profile, provider=ScriptedFake([egress]))).generate(
        Principal.A, REQUEST
    )
    assert result.output().error.code == "internal_error"
    assert result.metrics.provider_requests == result.metrics.uncertain_attempts == 1


async def test_progress_callback_is_deadline_bounded_and_has_only_states(profile):
    agent = await make_agent(profile)
    entered = asyncio.Event()

    async def progress(state):
        assert isinstance(state, State)
        entered.set()
        await asyncio.Event().wait()

    task = asyncio.create_task(agent.generate(Principal.A, REQUEST, progress=progress))
    await entered.wait()
    agent.clock.advance(30)
    result = await asyncio.wait_for(task, 2)
    assert result.output().error.code == "budget_exceeded"
    assert result.metrics.provider_requests == 0


async def test_profile_change_during_model_work_rejects_final_output(profile):
    hanging = Hanging()
    agent = await make_agent(profile, provider=ScriptedFake([hanging]))
    task = asyncio.create_task(agent.generate(Principal.A, REQUEST))
    await hanging.started.wait()
    await agent.profiles.save(
        Principal.A,
        ProfileSaveRequest(
            expected_revision=1,
            preferences={
                **profile,
                "session_minutes": 30,
            },
        ),
    )
    hanging.release.set()
    result = await task
    assert result.output().error.code == "stale_profile"
    assert agent.candidates.stats()["lineages"] == 0


async def test_profile_revision_precondition_and_invalid_request_prevent_provider_calls(profile):
    agent = await make_agent(profile)
    stale = await agent.generate(Principal.A, GenerateRequest(profile_revision=2))
    assert stale.output().error.code == "stale_profile"
    assert stale.metrics.provider_requests == 0
    malformed = GenerateRequest.model_construct(profile_revision=True)
    result = await agent.generate(Principal.A, malformed)
    assert result.output().error.code == "invalid_request"
    assert result.metrics.provider_requests == 0


def test_fake_tokenizer_is_explicit_and_byte_based():
    assert fake_tokens("é".encode()) == 1
    assert fake_tokens(b"12345") == 2
    assert json.loads(canonical({"x": 1})) == {"x": 1}
