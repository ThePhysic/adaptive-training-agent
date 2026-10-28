"""Offline, request-indexed provider actions and event-driven clock for F1-04."""

import asyncio

from profile_doubles import MemoryProfiles

from future_training.agent.fake import response_bytes
from future_training.agent.orchestration import Agent
from future_training.agent.protocol import ToolCall, canonical
from future_training.candidates import CandidateStore
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.identity import Principal
from future_training.schemas import ProfileSaveRequest


class ManualClock:
    def __init__(self):
        self.value = 100.0
        self.waiters = set()
        self.waiting = asyncio.Event()

    def now(self):
        return self.value

    async def wait_until(self, target):
        if target <= self.value:
            return
        future = asyncio.get_running_loop().create_future()
        item = (target, future)
        self.waiters.add(item)
        self.waiting.set()
        try:
            await future
        finally:
            self.waiters.remove(item)

    def advance(self, seconds):
        assert seconds >= 0
        self.value += seconds
        for target, future in self.waiters:
            if target <= self.value and not future.done():
                future.set_result(None)


class Hanging:
    def __init__(self, result=None):
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.cleaned = asyncio.Event()
        self.result = result

    async def __call__(self, request):
        self.started.set()
        try:
            await self.release.wait()
            return self.result(request) if self.result else valid_final(request)
        finally:
            self.cleaned.set()


async def make_agent(profile, *, provider=None, clock=None):
    profiles = MemoryProfiles()
    for principal in Principal:
        await profiles.save(principal, ProfileSaveRequest(expected_revision=0, preferences=profile))
    catalog = load_catalog()
    clock = clock or ManualClock()
    candidates = CandidateStore(profiles, catalog, clock=clock.now)
    return Agent(profiles, catalog, provider=provider, clock=clock, candidates=candidates)


def valid_output(request):
    plan = plan_week(request.context().profile.preferences, load_catalog()).plan
    assert plan is not None
    return {"outcome": "plan", "plan": plan.model_dump()}


def valid_final(request):
    return response_bytes(
        request, kind="final", output_json=canonical(valid_output(request)).decode()
    )


def invalid_final(request):
    output = valid_output(request)
    output["plan"]["days"][0]["blocks"][0]["exercise_id"] = "invented-exercise"
    return response_bytes(request, kind="final", output_json=canonical(output).decode())


def tool_response(request, *, count=1, name="search_exercises", arguments="{}", same_ids=False):
    calls = [
        ToolCall(
            call_id=f"read-{request.attempt}-{0 if same_ids else i}",
            name=name,
            arguments_json=arguments,
        ).model_dump()
        for i in range(count)
    ]
    return response_bytes(request, kind="tool_calls", calls=calls)
