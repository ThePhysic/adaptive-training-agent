"""Narrow completed native-item checks; contents remain request-local only."""

from future_training.agent.protocol import MAX_RESPONSE_BYTES


def text(value, maximum=MAX_RESPONSE_BYTES):
    if not isinstance(value, str) or len(value.encode()) > maximum:
        raise ValueError("Invalid native text")


def item(value, *, completed=True):
    if not isinstance(value, dict):
        raise ValueError("Invalid native item")
    text(value.get("id"), 512)
    if not value["id"]:
        raise ValueError("Missing native identity")
    kind = value.get("type")
    if value.get("status") not in (None, "in_progress", "completed", "incomplete"):
        raise ValueError("Invalid native status")
    if kind == "reasoning":
        if (
            set(value) - {"id", "type", "summary", "encrypted_content", "status"}
            or value.get("summary") != []
        ):
            raise ValueError("Unsupported reasoning")
        if value.get("status") not in (None, "completed") and completed:
            raise ValueError("Incomplete reasoning")
        if completed:
            text(value.get("encrypted_content"), 65536)
            if not value["encrypted_content"]:
                raise ValueError("Missing native state")
    elif kind == "function_call":
        if set(value) - {"id", "type", "status", "call_id", "name", "arguments"}:
            raise ValueError("Unsupported call")
        for key, maximum in (("call_id", 512), ("name", 64), ("arguments", 4096)):
            text(value.get(key), maximum)
            if not value[key]:
                raise ValueError("Missing call field")
        if completed and value.get("status") != "completed":
            raise ValueError("Incomplete call")
    elif kind == "message":
        if (
            set(value) - {"id", "type", "status", "role", "content", "phase"}
            or value.get("role") != "assistant"
            or value.get("phase") not in (None, "commentary", "final_answer")
            or not isinstance(value.get("content"), list)
        ):
            raise ValueError("Unsupported message")
        if completed and value.get("status") != "completed":
            raise ValueError("Incomplete message")
        for part in value["content"]:
            if not isinstance(part, dict):
                raise ValueError("Invalid content")
            if part.get("type") == "output_text":
                if (
                    set(part) - {"type", "text", "annotations", "logprobs"}
                    or part.get("annotations", [])
                    or part.get("logprobs", [])
                ):
                    raise ValueError("Unsupported text metadata")
                text(part.get("text"))
            elif part.get("type") == "refusal" and set(part) == {"type", "refusal"}:
                text(part["refusal"])
            else:
                raise ValueError("Unsupported content")
    else:
        raise ValueError("Unsupported native item")
