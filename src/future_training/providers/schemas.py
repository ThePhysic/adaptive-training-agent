"""Narrow strict-schema projection; original Pydantic/domain parsers remain final."""

from copy import deepcopy

from future_training.agent.protocol import OUTCOME_ADAPTER
from future_training.agent.tools import tool_definitions

_KEYS = {
    "$ref",
    "$defs",
    "type",
    "properties",
    "additionalProperties",
    "required",
    "items",
    "anyOf",
    "enum",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
}


def strict_schema(source: dict) -> dict:
    root = deepcopy(source)
    definitions = root.get("$defs", {})

    def visit(node):
        node = dict(node)
        for annotation in ("title", "description", "default"):
            node.pop(annotation, None)
        discriminator = node.pop("discriminator", None)
        if "oneOf" in node:
            if not discriminator or set(discriminator) - {"propertyName", "mapping"}:
                raise ValueError("Only provably disjoint discriminated unions are supported")
            values = []
            for branch in node["oneOf"]:
                target = definitions[branch["$ref"].removeprefix("#/$defs/")]
                values.append(target["properties"][discriminator["propertyName"]]["const"])
            if len(set(values)) != len(values):
                raise ValueError("Overlapping union")
            node["anyOf"] = node.pop("oneOf")
        elif discriminator:
            raise ValueError("Unexpected discriminator")
        if "const" in node:
            node["enum"] = [node.pop("const")]
        if set(node) - _KEYS:
            raise ValueError("Unsupported provider schema keyword")
        for key in ("$defs", "properties"):
            if key in node:
                node[key] = {name: visit(child) for name, child in node[key].items()}
        if "items" in node:
            node["items"] = visit(node["items"])
        if "anyOf" in node:
            node["anyOf"] = [visit(child) for child in node["anyOf"]]
        if node.get("type") == "object":
            if node.get("additionalProperties") is not False:
                raise ValueError("Open objects are not supported")
            node["required"] = list(node.get("properties", {}))
        return node

    return visit(root)


def output_schema() -> dict:
    schema = strict_schema(OUTCOME_ADAPTER.json_schema())
    definitions = schema.pop("$defs", {})
    return {
        "type": "object",
        "properties": {"result": schema},
        "required": ["result"],
        "additionalProperties": False,
        "$defs": definitions,
    }


def provider_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "name": tool["name"],
            "description": tool["description"],
            "strict": True,
            "parameters": strict_schema(tool["arguments"]),
        }
        for tool in tool_definitions()
    ]
