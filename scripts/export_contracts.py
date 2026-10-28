"""Export implemented local profile routes plus explicitly labeled future operations."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pydantic import TypeAdapter  # noqa: E402

from future_training.api import create_app  # noqa: E402
from future_training.completion_contracts import (  # noqa: E402
    SessionRecord,
    SessionSubmission,
    SubmissionError,
)
from future_training.schemas import (  # noqa: E402
    ApiError,
    ApprovalRequest,
    ApprovalResult,
    BudgetLimits,
    CandidateLimits,
    CatalogRecord,
    GenerateRequest,
    ProfileSaveRequest,
    ReviseRequest,
    SavedPlan,
    SavedProfile,
    StreamEvent,
)
from future_training.streaming import MAX_EVENTS, MAX_FRAME_BYTES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REF = "#/components/schemas/"


def document() -> dict:
    spec = create_app().openapi()
    spec["info"]["description"] = (
        "Local profiles, catalog and direct POST generation/revision streams are implemented. "
        "Business operations marked x-implementation=specification-only are NOT implemented. "
        "Stream ordering, durable approval/idempotency and owned history are implemented locally."
        " Explicit owner-scoped session completion and structured feedback "
        "Submit/readback are implemented."
    )
    schemas = spec.setdefault("components", {}).setdefault("schemas", {})
    models = [
        ApprovalRequest,
        ApprovalResult,
        BudgetLimits,
        CandidateLimits,
        CatalogRecord,
        GenerateRequest,
        ReviseRequest,
        SavedPlan,
        SavedProfile,
        ProfileSaveRequest,
        ApiError,
        SessionRecord,
        SessionSubmission,
        SubmissionError,
    ]
    for model in models:
        schema = model.model_json_schema(ref_template=REF + "{model}")
        schemas.update(schema.pop("$defs", {}))
        schemas[model.__name__] = schema
    stream = TypeAdapter(StreamEvent).json_schema(ref_template=REF + "{model}")
    schemas.update(stream.pop("$defs", {}))
    schemas["StreamEvent"] = stream
    spec["components"]["securitySchemes"] = {
        "SyntheticPrincipal": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Synthetic-Principal",
            "description": (
                "Local opt-in and actual loopback peer only; synthetic-a or synthetic-b. "
                "Not production authentication."
            ),
        }
    }
    routes = [
        ("/api/v1/profile", "get", None, "SavedProfile", False),
        ("/api/v1/profile", "put", "ProfileSaveRequest", "SavedProfile", False),
        ("/api/v1/exercises", "get", None, "CatalogRecord", False),
        ("/api/v1/drafts/stream", "post", "GenerateRequest", None, True),
        ("/api/v1/drafts/{candidate_id}/revise/stream", "post", "ReviseRequest", None, True),
        (
            "/api/v1/drafts/{candidate_id}/approve",
            "post",
            "ApprovalRequest",
            "ApprovalResult",
            False,
        ),
        ("/api/v1/plans", "get", None, "ApprovalResult", False),
        ("/api/v1/plans/{plan_id}", "get", None, "ApprovalResult", False),
        (
            "/api/v1/plans/{plan_id}/sessions/{day_index}/completion",
            "post",
            "SessionSubmission",
            "SessionRecord",
            False,
        ),
        (
            "/api/v1/plans/{plan_id}/sessions/{day_index}/completion",
            "get",
            None,
            "SessionRecord",
            False,
        ),
        ("/api/v1/plans/{plan_id}/completions", "get", None, "SessionRecord", False),
    ]
    for path, method, request, response, streaming in routes:
        if path in ("/api/v1/plans", "/api/v1/plans/{plan_id}"):
            response = "SavedPlan"
        schema = {"$ref": REF + response} if response else {"type": "string"}
        if path in ("/api/v1/plans", "/api/v1/exercises"):
            schema = {"type": "array", "items": schema, "maxItems": 20}
        if path.endswith("/completions"):
            schema = {"type": "array", "items": schema, "maxItems": 4}
        operation = {
            "operationId": method + path.replace("/", "_").replace("{", "").replace("}", ""),
            "x-implementation": "specification-only",
            "security": [{"SyntheticPrincipal": []}],
            "responses": {
                "200": {
                    "description": "Implemented local success",
                    "content": {
                        "text/event-stream" if streaming else "application/json": {"schema": schema}
                    },
                }
            },
        }
        if streaming:
            operation["x-sse-envelope"] = {"$ref": REF + "StreamEvent"}
            operation["description"] = (
                "No replay; only done(plan) exposes approval identity. "
                "EOF without terminal done is incomplete. Post-header errors use error+done(error)."
            )
            operation["x-sse-limits"] = {"maxFrameBytes": MAX_FRAME_BYTES, "maxEvents": MAX_EVENTS}
        if request:
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": REF + request}}},
            }
        operation["parameters"] = []
        for parameter in ("candidate_id", "plan_id"):
            if "{" + parameter + "}" in path:
                operation["parameters"].append(
                    {
                        "name": parameter,
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "pattern": "^[A-Za-z0-9_-]+$",
                            "maxLength": 64,
                        },
                    }
                )
        if "{day_index}" in path:
            operation["parameters"].append(
                {
                    "name": "day_index",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer", "minimum": 1, "maximum": 4},
                }
            )
        if path in ("/api/v1/plans", "/api/v1/exercises"):
            operation["parameters"] += [
                {
                    "name": "limit",
                    "in": "query",
                    "schema": {"type": "integer", "minimum": 1, "maximum": 20, "default": 20},
                },
                {"name": "cursor", "in": "query", "schema": {"type": "string", "maxLength": 64}},
            ]
        if path == "/api/v1/exercises":
            for name, values in {
                "goal": ["general_strength", "general_conditioning"],
                "equipment": ["bodyweight", "dumbbells_and_bodyweight"],
                "experience": ["beginner", "intermediate"],
            }.items():
                operation["parameters"].append(
                    {"name": name, "in": "query", "schema": {"type": "string", "enum": values}}
                )
        for status in ("401", "403", "404", "409", "410", "413", "422", "429", "503"):
            operation["responses"][status] = {
                "description": "Sanitized pre-header error",
                "content": {"application/json": {"schema": {"$ref": REF + "ApiError"}}},
            }
        if path.endswith("/approve"):
            operation["description"] = (
                "Path candidate_id must equal body candidate_id. Owner comes from server identity. "
                "Committed idempotency lookup BEFORE candidate access AND AGAIN after guard wait. "
                "Unknown commit blocks approval/revision until reconciled; see approval-safety.md."
            )
        operation["x-implementation"] = "implemented-local"
        if path.endswith(("/completion", "/completions")):
            operation["description"] = (
                "Explicit immutable session Submit/readback against an owned approved snapshot. "
                "First create expects revision 0; record revision 1 is immutable. "
                "Same-key matching retry returns original; different key conflicts. "
                "No free-text notes; see contracts/completion-feedback.md."
            )
            if method == "post":
                operation["x-request-max-bytes"] = 4096
            for value in operation["responses"].values():
                if value["description"] == "Sanitized pre-header error":
                    value["content"]["application/json"]["schema"] = {
                        "$ref": REF + "SubmissionError"
                    }
        if path == "/api/v1/profile":
            operation["description"] = (
                "Requires FATA_LOCAL_DEV=1, loopback peer/listener and synthetic principal header. "
                "PUT is explicit Save with optimistic expected_revision; no owner field accepted."
            )
        spec["paths"].setdefault(path, {})[method] = operation
    for path in ("/health", "/ready"):
        spec["paths"][path]["get"]["x-implementation"] = "implemented-foundation"
    return spec


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = json.dumps(document(), indent=2, sort_keys=True) + "\n"
    destination = ROOT / "contracts/openapi.json"
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != content:
            raise SystemExit("OpenAPI is stale; run scripts/export_contracts.py")
    else:
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
