"""Salvage only independently bounded numbers; never retain raw provider metadata."""

from future_training.providers.accounting import MODEL

FIELDS = frozenset(
    {
        "input_tokens",
        "output_tokens",
        "cached_tokens",
        "write_30m_tokens",
        "write_12h_tokens",
        "reasoning_tokens",
        "total_tokens",
        "cache_write_tokens",
        "charge_micro",
    }
)


def classification(value, expected):
    return "missing" if value is None else "expected" if value == expected else "unexpected"


def numbers(values):
    return {k: v for k, v in values.items() if k in FIELDS and type(v) is int and 0 <= v <= 10**9}


def response_observation(response):
    raw = response.get("usage")
    if not isinstance(raw, dict):
        return "usage_missing", {}
    observed = numbers({k: raw.get(k) for k in ("input_tokens", "output_tokens", "total_tokens")})
    detail = raw.get("input_tokens_details")
    if isinstance(detail, dict):
        observed.update(
            numbers({k: detail.get(k) for k in ("cached_tokens", "cache_write_tokens")})
        )
        writes = detail.get("cache_write_tokens_details")
        if isinstance(writes, dict):
            observed.update(
                numbers(
                    {
                        "write_30m_tokens": writes.get("ttl_30m_tokens"),
                        "write_12h_tokens": writes.get("ttl_12h_tokens"),
                    }
                )
            )
        if (
            type(detail.get("cache_write_tokens")) is int
            and detail["cache_write_tokens"] > 0
            and not isinstance(writes, dict)
        ):
            reason = "cache_details"
        else:
            reason = "usage_invalid"
    else:
        reason = "usage_invalid"
    output = raw.get("output_tokens_details")
    if isinstance(output, dict):
        observed.update(numbers({"reasoning_tokens": output.get("reasoning_tokens")}))
    return reason, observed


def discrepancy(usage, model, tier, input_bound, output_cap, *, exact=False):
    if model != MODEL:
        return "model"
    if tier != "default":
        return "tier"
    if usage.write_12h_tokens:
        return "cache_ttl"
    if usage.input_tokens > input_bound or exact and usage.input_tokens != input_bound:
        return "usage_input"
    if usage.output_tokens > output_cap:
        return "usage_output"
    return None
