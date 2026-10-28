"""Whole-request accounting, admission and cancellation-safe deadline supervision."""

import asyncio
import math
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Protocol

from future_training.identity import Principal, owner_id
from future_training.schemas import BudgetLimits

from .protocol import ATTEMPT_OUTPUT_TOKENS, Usage


class AgentFault(Exception):
    def __init__(self, reason: str, code: str = "provider_failure", *, retryable: bool = False):
        self.reason = reason
        self.code = code
        self.retryable = retryable
        super().__init__(reason)


class Clock(Protocol):
    def now(self) -> float: ...
    async def wait_until(self, target: float) -> None: ...


class SystemClock:
    def now(self) -> float:
        return time.monotonic()

    async def wait_until(self, target: float) -> None:
        await asyncio.sleep(max(0, target - self.now()))


class Deadline:
    def __init__(self, clock: Clock, *, started_at: float | None = None):
        self.clock = clock
        self.started = clock.now() if started_at is None else min(started_at, clock.now())
        self.expires = self.started + BudgetLimits().deadline_seconds

    def check(self):
        if self.clock.now() >= self.expires:
            raise AgentFault("deadline_exceeded", "budget_exceeded")

    @asynccontextmanager
    async def scope(self):
        # asyncio.Timeout handles external cancellation separately from its own
        # cancellation. A fake clock can wake this watchdog without sleeping.
        async with asyncio.timeout(None) as timer:

            async def watch():
                await self.clock.wait_until(self.expires)
                timer.reschedule(asyncio.get_running_loop().time())

            watcher = asyncio.create_task(watch())
            try:
                yield
            finally:
                watcher.cancel()
                # Always own and drain the watchdog, including repeated cancellation.
                cancelled = False
                owner = asyncio.current_task()
                cancellations = owner.cancelling()
                while not watcher.done():
                    try:
                        await asyncio.shield(watcher)
                    except asyncio.CancelledError:
                        if owner.cancelling() > cancellations:
                            cancelled = True
                if not watcher.cancelled():
                    watcher.result()
                if cancelled:
                    raise asyncio.CancelledError


@dataclass(frozen=True)
class Metrics:
    provider_requests: int
    tool_dispatches: int
    transport_retries: int
    semantic_repairs: int
    input_tokens: int
    output_tokens: int
    uncertain_attempts: int
    finish_reasons: tuple[str, ...]
    token_kind: str = "simulated_utf8_quarters"


class Budget:
    def __init__(self, *, token_kind="simulated_utf8_quarters"):
        self.token_kind = token_kind
        self.limits = BudgetLimits()
        self.attempts = self.tools = self.retries = self.repairs = 0
        self.input = self.output = self.uncertain = 0
        self.finishes = []
        self._pending: tuple[int, int] | None = None

    def reserve(self, input_tokens: int) -> tuple[int, int]:
        if (
            type(input_tokens) is not int
            or input_tokens < 0
            or self._pending is not None
            or self.attempts >= self.limits.provider_attempts
            or input_tokens > self.limits.input_tokens - self.input
            or self.output >= self.limits.output_tokens
        ):
            raise AgentFault("provider_budget_exhausted", "budget_exceeded")
        output = min(ATTEMPT_OUTPUT_TOKENS, self.limits.output_tokens - self.output)
        self.attempts += 1
        self.input += input_tokens
        self.output += output
        self._pending = (input_tokens, output)
        return input_tokens, output

    def settle(self, usage: Usage, finish: str, *, uncertain: bool = False):
        if self._pending is None:
            raise RuntimeError("No reserved provider attempt")
        before_input, before_output = self._pending
        if uncertain:
            self.uncertain += 1
            usage = Usage(
                input_tokens=max(before_input, usage.input_tokens),
                output_tokens=max(before_output, usage.output_tokens),
            )
        self.input += usage.input_tokens - before_input
        self.output += usage.output_tokens - before_output
        self._pending = None
        self.finishes.append(finish)
        # Retain actual reported overages; never clamp or make a further call.
        if self.input > self.limits.input_tokens or self.output > self.limits.output_tokens:
            raise AgentFault("reported_token_overrun", "budget_exceeded")
        if usage.input_tokens > before_input or usage.output_tokens > before_output:
            raise AgentFault("provider_exceeded_attempt_allowance")

    def unknown(self, finish: str):
        if self._pending is not None:
            self._pending = None
            self.uncertain += 1
            self.finishes.append(finish)

    def dispatch(self):
        if self.tools >= self.limits.read_tools:
            raise AgentFault("tool_budget_exhausted", "budget_exceeded")
        self.tools += 1

    def repair(self):
        if self.repairs >= self.limits.semantic_repairs:
            raise AgentFault("semantic_repair_exhausted")
        self.repairs += 1

    def retry(self):
        if self.retries >= self.limits.transport_retries:
            raise AgentFault("transport_retry_exhausted", retryable=True)
        self.retries += 1

    def metrics(self):
        return Metrics(
            self.attempts,
            self.tools,
            self.retries,
            self.repairs,
            self.input,
            self.output,
            self.uncertain,
            tuple(self.finishes),
            self.token_kind,
        )


class Admission:
    def __init__(self):
        self._active: set[Principal] = set()

    @contextmanager
    def take(self, principal: Principal):
        owner_id(principal)
        if principal in self._active or len(self._active) >= BudgetLimits().global_runs:
            raise AgentFault("concurrency_limit", "capacity_exceeded", retryable=True)
        self._active.add(principal)
        try:
            yield
        finally:
            self._active.remove(principal)

    def active(self):
        return len(self._active)


def valid_delay(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0
