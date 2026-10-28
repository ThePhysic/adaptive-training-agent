"""Immutable provider payload binding shared with the historical offline experiment."""

import hashlib
from dataclasses import dataclass, field

from future_training.agent.budget import AgentFault
from future_training.agent.protocol import MAX_REQUEST_BYTES, canonical, parse_json
from future_training.providers.accounting import MODEL
from future_training.providers.gates import ENDPOINT
from future_training.providers.schemas import output_schema, provider_tools

COUNT_ENDPOINT = ENDPOINT + "/input_tokens"
COMMON = frozenset(
    {
        "model",
        "input",
        "instructions",
        "tools",
        "tool_choice",
        "parallel_tool_calls",
        "reasoning",
        "text",
        "truncation",
    }
)
GENERATION_ONLY = frozenset(
    {
        "store",
        "background",
        "stream",
        "service_tier",
        "max_output_tokens",
        "prompt_cache_options",
    }
)


@dataclass(frozen=True, repr=False)
class FrozenPayload:
    generation: bytes = field(repr=False)
    counting: bytes = field(repr=False)
    _binding: bytes = field(repr=False)

    @classmethod
    def prepare(cls, raw: bytes, *, max_items=24):
        if not isinstance(raw, bytes) or len(raw) > MAX_REQUEST_BYTES:
            raise AgentFault("count_payload_invalid")
        data = parse_json(raw)
        if not isinstance(data, dict) or set(data) - COMMON - GENERATION_ONLY:
            raise AgentFault("count_payload_invalid")
        # Set an explicit documented default ONCE, before freezing both bodies.
        data.setdefault("truncation", "disabled")
        if (
            set(data) != COMMON | GENERATION_ONLY
            or data["model"] != MODEL
            or data["tools"] != provider_tools()
            or data["text"]
            != {
                "format": {
                    "type": "json_schema",
                    "name": "plan_envelope_v1",
                    "strict": True,
                    "schema": output_schema(),
                }
            }
            or data["reasoning"] != {"effort": "low"}
            or data["tool_choice"] != "auto"
            or data["parallel_tool_calls"] is not False
            or data["truncation"] != "disabled"
            or data["store"] is not False
            or data["background"] is not False
            or data["stream"] is not True
            or data["service_tier"] != "default"
            or data["prompt_cache_options"] != {"mode": "implicit", "ttl": "30m"}
            or type(data["max_output_tokens"]) is not int
            or not 1 <= data["max_output_tokens"] <= 2000
            or not isinstance(data["instructions"], str)
            or not isinstance(data["input"], list)
            or not 1 <= len(data["input"]) <= max_items
        ):
            raise AgentFault("count_payload_invalid")
        # This deliberately accepts only the already supported text/native-item
        # subset. No hosted tools, conversation references, files or remote URLs.
        for item in data["input"]:
            if not isinstance(item, dict):
                raise AgentFault("count_payload_invalid")
            kind = item.get("type")
            if kind is None:
                if set(item) != {"role", "content"} or item["role"] not in ("user", "developer"):
                    raise AgentFault("count_payload_invalid")
                if not isinstance(item["content"], str):
                    raise AgentFault("count_payload_invalid")
            elif kind == "reasoning":
                if (
                    set(item) - {"type", "id", "summary", "encrypted_content", "status"}
                    or item.get("summary") != []
                    or not isinstance(item.get("encrypted_content"), str)
                    or not item["encrypted_content"]
                ):
                    raise AgentFault("count_payload_invalid")
            elif kind not in ("function_call", "function_call_output", "message"):
                raise AgentFault("count_payload_invalid")
        generation = canonical(data)
        counting = canonical({key: data[key] for key in sorted(COMMON)})
        if max(len(generation), len(counting)) > MAX_REQUEST_BYTES:
            raise AgentFault("count_payload_invalid")
        return cls(generation, counting, hashlib.sha256(generation).digest())

    def assert_unchanged(self, raw: bytes):
        # Serialize once BEFORE counting; after that, even a harmless reserialize
        # is rejected. Nested schema property ordering can affect provider output.
        if (
            not isinstance(raw, bytes)
            or len(raw) > MAX_REQUEST_BYTES
            or hashlib.sha256(raw).digest() != self._binding
        ):
            raise AgentFault("count_payload_mismatch")
