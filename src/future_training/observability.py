"""Bounded metadata-only local spans. No exporter, content or identity capture."""

import asyncio
import inspect
import json
import logging
import math
import re
import time
from collections import deque
from contextvars import ContextVar
from functools import wraps
from uuid import uuid4

from starlette.responses import JSONResponse

_current = ContextVar("local_span", default=None)
_logger = logging.getLogger("future_training.trace")
_logger.addHandler(logging.NullHandler())
STAGES = frozenset(
    {
        "http",
        "evaluation.case",
        "agent.session",
        "agent.execute",
        "agent.repair",
        "provider",
        "provider.count",
        "tool",
        "validation",
        "candidate.initial",
        "candidate.revision",
        "profile.read",
        "profile.save",
        "approval",
        "approval.lookup",
        "approval.transaction",
        "approval.reconcile",
        "plan.read",
        "completion.submit",
        "completion.transaction",
        "completion.read",
        "readiness",
        "stream.terminal",
        "async.read",
        "async.http",
        "async.batch",
    }
)
VALUES = {
    "read": {"profile", "catalog", "history"},
    "execution": {"sequential", "concurrent"},
    "outcome": {"ok", "error", "cancelled", "plan", "clarify", "abstain", "pending"},
    "route": {
        "profile",
        "generate",
        "revise",
        "approve",
        "plans",
        "completions",
        "catalog",
        "health",
        "ready",
        "web",
        "other",
    },
    "tool": {"search_exercises", "get_user_preferences", "unknown"},
    "state": {
        "created",
        "context",
        "model",
        "tools",
        "validating",
        "repairing",
        "ready_unpublished",
        "failed",
        "cancelled",
    },
    "catalog_revision": {"catalog-v1"},
    "validator_revision": {"validator-v1"},
    "model_id": {
        "deterministic-fake-v1",
        "gpt-6.1-sol-replay",
        "gpt-6.1-sol-authority-fixture",
        "gpt-6.1-sol",
    },
    "evidence_source": {"template", "fake", "replay", "authority_fixture", "live"},
    "token_kind": {
        "simulated_utf8_quarters",
        "provider_reported_replay",
        "provider_reported_counted_replay",
        "provider_reported_authority_fixture",
        "provider_reported_counted_live",
    },
    "prompt_version": {"planner-prompt-v1", "real-planner-prompt-v1"},
    "tool_version": {"read-tools-v1", "real-read-tools-v1"},
    "output_version": {"plan-output-v1", "real-plan-envelope-v1"},
    "finish_reason": {
        "stop",
        "tool_calls",
        "length",
        "refusal",
        "transport",
        "unavailable",
        "rate_limit",
        "authentication",
        "malformed",
        "unknown",
    },
    "reason": {
        "internal_error",
        "invalid_request",
        "unauthorized",
        "not_found",
        "stale_profile",
        "session_already_recorded",
        "plan_mismatch",
        "candidate_mismatch",
        "candidate_expired",
        "candidate_superseded",
        "candidate_already_approved",
        "idempotency_mismatch",
        "reconciliation_pending",
        "capacity_exceeded",
        "revision_in_progress",
        "budget_exceeded",
        "provider_failure",
        "semantic_repair_exhausted",
        "malformed_provider_response",
        "provider_response_too_large_or_invalid",
        "deadline_exceeded",
        "concurrency_limit",
        "provider_budget_exhausted",
        "transport_retry_exhausted",
        "tool_budget_exhausted",
        "profile_changed",
        "provider_fatal",
        "provider_http_failure",
        "provider_transport_failure",
        "provider_encoding_denied",
        "provider_destination_denied",
        "provider_tls_verification_required",
        "provider_transport_closed",
        "count_protocol_failure",
        "count_invalid_or_exceeded",
        "count_invalid_response",
        "count_unavailable",
        "count_payload_mismatch",
        "count_ticket_missing",
        "wire_exhausted",
        "invalid_tool_result",
        "cancelled",
        "dependency_unavailable",
        "disconnect",
        "validated_unpublished",
        "invalid_plan",
        "structured_output",
        "read_unauthorized",
        "read_invalid_result",
        "read_response_too_large",
        "read_timeout",
        "read_transport",
        "read_http",
        "read_unavailable",
        "read_internal",
    },
}
COUNTS = frozenset(
    {
        "http_status",
        "provider_requests",
        "count_requests",
        "wire_requests",
        "count_request_bytes",
        "generation_request_bytes",
        "tool_dispatches",
        "transport_retries",
        "semantic_repairs",
        "input_tokens",
        "output_tokens",
        "cached_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "uncertain_attempts",
        "attempt",
        "profile_revision",
        "read_requests",
        "response_bytes",
    }
)


def attributes(values):
    safe = {}
    if not isinstance(values, dict):
        return safe
    for key, value in values.items():
        if key in {"terminal_complete", "cancelled_cleanup"} and type(value) is bool:
            safe[key] = value
        elif key in COUNTS and type(value) is int and 0 <= value <= 10**9:
            safe[key] = value
        elif key in VALUES and type(value) is str and value in VALUES[key]:
            safe[key] = value
    return safe


class LocalTracer:
    def __init__(self, capacity=2048, *, clock=time.perf_counter):
        if type(capacity) is not int or not 1 <= capacity <= 4096:
            raise ValueError("Invalid local trace capacity")
        self._records = deque(maxlen=capacity)
        self._clock = clock
        self.dropped = 0

    def snapshot(self):
        return json.loads(json.dumps(list(self._records)))

    def append(self, record):
        record = safe_record(record)
        if record is None:
            return
        if len(self._records) == self._records.maxlen:
            self.dropped += 1
        self._records.append(record)
        # SafeFormatter accepts only this reconstructed, validated record.
        _logger.info("local_span", extra={"local_span": record})


class Span:
    def __init__(self, stage, *, tracer=None, **values):
        if stage not in STAGES:
            raise ValueError("Unknown tracing stage")
        parent = _current.get()
        self.parent = parent if tracer is None else None
        self.tracer = tracer or (parent.tracer if parent else None)
        self.stage, self.values = stage, attributes(values)
        self.trace_id = parent.trace_id if parent and tracer is None else uuid4().hex
        self.span_id = uuid4().hex
        self.parent_id = parent.span_id if parent and tracer is None else None

    def set(self, **values):
        self.values.update(attributes(values))

    def __enter__(self):
        try:
            self.started = self.tracer._clock() if self.tracer else 0
        except Exception:
            self.started = 0
        self.token = _current.set(self)
        return self

    def __exit__(self, kind, error, tb):
        _current.reset(self.token)
        if self.tracer is None:
            return
        if error is not None:
            if isinstance(error, asyncio.CancelledError) and self.values.get("terminal_complete"):
                self.set(cancelled_cleanup=True)
            elif (
                isinstance(error, asyncio.CancelledError)
                and self.values.get("reason") == "deadline_exceeded"
            ):
                self.set(outcome="error")
            elif isinstance(error, TimeoutError) and self.stage == "agent.session":
                self.set(outcome="error", reason="deadline_exceeded")
            else:
                self.set(
                    outcome="cancelled" if isinstance(error, asyncio.CancelledError) else "error"
                )
                reason = (
                    "cancelled"
                    if isinstance(error, asyncio.CancelledError)
                    else getattr(error, "reason", getattr(error, "code", "internal_error"))
                )
                self.set(
                    reason=reason
                    if type(reason) is str and reason in VALUES["reason"]
                    else "internal_error"
                )
        try:
            duration = (self.tracer._clock() - self.started) * 1000
        except Exception:
            duration = 0
        if not math.isfinite(duration):
            duration = 0
        record = {
            "stage": self.stage,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "duration_ms": round(max(0, min(duration, 3600000)), 3),
            "attributes": {"outcome": "ok", **self.values},
        }
        try:
            self.tracer.append(record)
        except Exception:
            # A diagnostic sink cannot change publication/transaction correctness.
            pass


def span(stage, **values):
    return Span(stage, **values)


def annotate(**values):
    current = _current.get()
    if current:
        current.set(**values)


def correlation_id():
    current = _current.get()
    return current.trace_id if current else uuid4().hex


def terminal_outcome(outcome):
    current = _current.get()
    while current:
        if current.stage in {"http", "agent.session"}:
            current.set(outcome=outcome, terminal_complete=True)
        current = current.parent


def traced(stage):
    def decorate(function):
        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def asynchronous(*args, **kwargs):
                with span(stage):
                    return await function(*args, **kwargs)

            return asynchronous

        @wraps(function)
        def synchronous(*args, **kwargs):
            with span(stage):
                return function(*args, **kwargs)

        return synchronous

    return decorate


def validate_plan(*args, **kwargs):
    """Observe the existing authoritative validator without changing its rules."""
    from future_training.domain.validator import validate_plan as authoritative

    with span("validation") as observation:
        result = authoritative(*args, **kwargs)
        if not result.valid:
            observation.set(outcome="error", reason="invalid_plan")
        return result


def route_name(path):
    fixed = {
        "/api/v1/profile": "profile",
        "/api/v1/drafts/stream": "generate",
        "/api/v1/plans": "plans",
        "/api/v1/exercises": "catalog",
        "/health": "health",
        "/ready": "ready",
        "/": "web",
    }
    if path in fixed:
        return fixed[path]
    for pattern, name in [
        (r"/api/v1/plans/[^/]+/sessions/[^/]+/completion", "completions"),
        (r"/api/v1/plans/[^/]+/completions", "completions"),
        (r"/api/v1/drafts/[^/]+/revise/stream", "revise"),
        (r"/api/v1/drafts/[^/]+/approve", "approve"),
        (r"/api/v1/plans/[^/]+", "plans"),
    ]:
        if re.fullmatch(pattern, path):
            return name
    return "web" if path.startswith("/assets/") else "other"


class TraceBoundary:
    def __init__(self, app, tracer):
        self.app, self.tracer = app, tracer

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        with Span("http", tracer=self.tracer, route=route_name(scope["path"])) as root:
            started = False

            async def correlated_send(message):
                nonlocal started
                if message["type"] == "http.response.start":
                    started = True
                    root.set(http_status=message["status"])
                    if message["status"] >= 400:
                        root.set(outcome="error")
                    message = {
                        **message,
                        "headers": [
                            *message.get("headers", []),
                            (b"x-request-id", root.trace_id.encode()),
                        ],
                    }
                await send(message)

            try:
                await self.app(scope, receive, correlated_send)
            except Exception:
                root.set(outcome="error", reason="internal_error")
                if started:
                    raise
                await JSONResponse({"code": "internal_error", "retryable": True}, 503)(
                    scope, receive, correlated_send
                )


def safe_record(value):
    if (
        not isinstance(value, dict)
        or type(value.get("stage")) is not str
        or value["stage"] not in STAGES
    ):
        return None
    ids = (value.get("trace_id"), value.get("span_id"))
    if not all(type(v) is str and re.fullmatch(r"[0-9a-f]{32}", v) for v in ids):
        return None
    parent = value.get("parent_id")
    if parent is not None and (
        type(parent) is not str or not re.fullmatch(r"[0-9a-f]{32}", parent)
    ):
        return None
    duration = value.get("duration_ms")
    if (
        type(duration) not in (int, float)
        or not math.isfinite(duration)
        or not 0 <= duration <= 3600000
    ):
        return None
    return {
        "stage": value["stage"],
        "trace_id": ids[0],
        "span_id": ids[1],
        "parent_id": parent,
        "duration_ms": duration,
        "attributes": attributes(value.get("attributes", {})),
    }


class SafeFormatter(logging.Formatter):
    def format(self, record):
        value = (
            safe_record(getattr(record, "local_span", None))
            if record.name == _logger.name
            else None
        )
        return json.dumps(
            value
            or {
                "event": "runtime_log",
                "level": record.levelname
                if record.levelname in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
                else "UNKNOWN",
            },
            separators=(",", ":"),
        )


def configure_logging(stream=None):
    """The supported launcher has one safe console sink; access/exception text is omitted."""
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SafeFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "future_training.trace"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
