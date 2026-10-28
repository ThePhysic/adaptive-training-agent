"""Provider-reported usage and exact money; independent of simulated fake tokens."""

from fractions import Fraction
from typing import Annotated

from pydantic import Field, StrictInt, model_validator

from future_training.schemas import Contract

Count = Annotated[StrictInt, Field(ge=0, le=10**9)]
MODEL = "gpt-6.1-sol"
RATE_VERSION = "sol-standard-2026-10-24-v1"
GENERATION_RUN_MICRO = 80002


def proposed_probe_micro(count_ceiling_micro):
    """Arithmetic only; no price verification, grant, permit or authorization."""
    if type(count_ceiling_micro) is not int or not 0 <= count_ceiling_micro <= 10**9:
        raise ValueError("An explicit count bound is required")
    return GENERATION_RUN_MICRO + 3 * count_ceiling_micro


class ActualUsage(Contract):
    input_tokens: Count
    output_tokens: Count
    cached_tokens: Count = 0
    write_30m_tokens: Count = 0
    write_12h_tokens: Count = 0
    reasoning_tokens: Count = 0

    @model_validator(mode="after")
    def partitions(self):
        if self.cached_tokens + self.write_30m_tokens + self.write_12h_tokens > self.input_tokens:
            raise ValueError("Invalid input partition")
        if self.reasoning_tokens > self.output_tokens:
            raise ValueError("Invalid output partition")
        return self

    @classmethod
    def from_response(cls, raw):
        if not isinstance(raw, dict):
            raise ValueError("Missing usage")
        details = raw.get("input_tokens_details")
        outputs = raw.get("output_tokens_details")
        if not isinstance(details, dict) or not isinstance(outputs, dict):
            raise ValueError("Missing usage details")
        writes = details.get("cache_write_tokens_details")
        if writes is None and type(details.get("cache_write_tokens")) is int:
            if details["cache_write_tokens"] == 0:
                # Official Responses examples omit the TTL breakdown for an
                # explicit zero total. Nonnegative partitions then must be zero;
                # this does not infer missing/nonzero writes or a free request.
                writes = {"ttl_30m_tokens": 0, "ttl_12h_tokens": 0}
        if not isinstance(writes, dict):
            raise ValueError("Missing cache accounting")
        value = cls(
            input_tokens=raw["input_tokens"],
            output_tokens=raw["output_tokens"],
            cached_tokens=details["cached_tokens"],
            write_30m_tokens=writes["ttl_30m_tokens"],
            write_12h_tokens=writes["ttl_12h_tokens"],
            reasoning_tokens=outputs["reasoning_tokens"],
        )
        if (
            type(raw.get("total_tokens")) is not int
            or raw["total_tokens"] != value.input_tokens + value.output_tokens
            or type(details.get("cache_write_tokens")) is not int
            or details["cache_write_tokens"] != value.write_30m_tokens + value.write_12h_tokens
        ):
            raise ValueError("Inconsistent usage")
        return value


def ceiling(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def reserve_micro(input_bound: int, output_cap: int) -> int:
    if type(input_bound) is not int or type(output_cap) is not int:
        raise ValueError("Integer bounds required")
    if not 0 <= input_bound <= 16000 or not 1 <= output_cap <= 2000:
        raise ValueError("Unsupported allowance")
    return ceiling(Fraction(5, 2) * input_bound + 10 * output_cap)


def cost_micro(usage: ActualUsage) -> int:
    usage = ActualUsage.model_validate(usage.model_dump())
    ordinary = (
        usage.input_tokens - usage.cached_tokens - usage.write_30m_tokens - usage.write_12h_tokens
    )
    return ceiling(
        2 * ordinary
        + Fraction(1, 10) * usage.cached_tokens
        + Fraction(5, 2) * usage.write_30m_tokens
        + 5 * usage.write_12h_tokens
        + 10 * usage.output_tokens
    )
