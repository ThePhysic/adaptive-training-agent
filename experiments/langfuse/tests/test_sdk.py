import asyncio
import copy
import json
import logging
import socket
import sys
import threading
from uuid import uuid4

import pytest
from offline_sdk import Capture

from future_training.experiments.model_eval_assets import SCORE_REFERENCE
from future_training.langfuse_local import LangfuseTracer, experiment_projection
from future_training.observability import Span, span


def records():
    tracer = LangfuseTracer()
    with Span("http", tracer=tracer):
        with span("agent.execute", input_tokens=1000, output_tokens=100, evidence_source="replay"):
            with span("provider", attempt=1):
                pass
            with span("tool", tool="search_exercises"):
                pass
            with span("validation", outcome="error", reason="invalid_plan"):
                pass
    return tracer.observations.snapshot()


def test_actual_sdk_correlation_order_status_duration_and_dedup():
    rows = records()
    with Capture() as c:
        c.observations(rows)
        c.observations(rows)
        spans = c.flush()
        assert len(spans) == len(rows)
        for old, new in zip(rows, spans, strict=True):
            assert old["trace_id"] == new["trace_id"]
            assert new["span_id"] == old["span_id"][-16:]
            assert new["parent_id"] == (old["parent_id"][-16:] if old["parent_id"] else None)
            assert new["duration_ns"] == round(old["duration_ms"] * 1000000)
        assert next(s for s in spans if s["name"] == "validation")["status"] == "ERROR"
    assert c.closed and c.http.is_closed and all(x.is_closed for x in c.async_clients)


def test_existing_150_items_actual_sdk_evaluations_and_mock_score_api():
    report = json.loads(SCORE_REFERENCE.read_text(encoding="utf-8"))
    report["trace_links"] = [
        {"source": r["source"], "case_id": r["case_id"], "trace_id": uuid4().hex}
        for r in report["cases"]
    ]
    p = experiment_projection(report)
    with Capture() as c:
        c.experiments(p)
        assert len({i["experiment_id"] for i in c.experiment_links.values()}) == 3
        c.scores(p)
        c.scores(p)
        c.flush()
        scores = [v for batch in c.requests for v in batch]
        assert len(scores) == 300
        hard = [s for s in scores if s["name"] == "hard_passed"]
        assert sum(s["value"] for s in hard) == 138
        assert all(s["dataType"] == "BOOLEAN" and s["value"] in (0, 1) for s in scores)
        assert {s["metadata"]["source"] for s in scores} == {"template", "fake", "replay"}


def test_secondary_otel_exporter_is_blocked_and_capture_capacity_is_fixed():
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    with Capture() as c:
        with pytest.raises(ValueError):
            c.observations(records() * 410)
        span = c.provider.get_tracer("foreign-scope").start_span("provider")
        span.end()
        exporter = OTLPSpanExporter(endpoint="https://outside.invalid/v1/traces", timeout=0.001)
        try:
            # Both the permanent process seal and pytest's independent socket
            # guard reject this unapproved secondary exporter before I/O.
            try:
                result = exporter.export((span,))
            except Exception:
                pass
            else:
                from opentelemetry.sdk.trace.export import SpanExportResult

                assert result is SpanExportResult.FAILURE
        finally:
            exporter.shutdown()
        assert not c.flush()


@pytest.mark.parametrize("mutation", ["source", "quality", "value", "data_type"])
def test_malformed_scores_cannot_become_quality_judgments(mutation):
    report = json.loads(SCORE_REFERENCE.read_text(encoding="utf-8"))
    report["trace_links"] = [
        {"source": r["source"], "case_id": r["case_id"], "trace_id": uuid4().hex}
        for r in report["cases"]
    ]
    projection = experiment_projection(report)
    item = projection["items"][0]
    if mutation == "source":
        item["source"] = "live"
    elif mutation == "quality":
        item["quality_scores"] = {"human": 5}
    elif mutation == "value":
        item["scores"][0]["value"] = 2
    else:
        item["scores"][0]["data_type"] = "NUMERIC"
    with Capture() as c, pytest.raises(ValueError):
        c.scores(projection)


@pytest.mark.parametrize(
    "canary", ["sk-secret-canary", "person@example.invalid", "private-account-canary"]
)
def test_hostile_environment_secondary_export_and_privacy(canary, monkeypatch, capsys):
    for key in (
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_DEBUG",
        "LANGFUSE_RELEASE",
        "LANGFUSE_BASE_URL",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_RESOURCE_ATTRIBUTES",
        "HTTP_PROXY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.setenv(key, canary)
    for key, value in {
        "LANGFUSE_DEBUG": "true",
        "LANGFUSE_TRACING_ENABLED": "true",
        "LANGFUSE_MEDIA_UPLOAD_ENABLED": "true",
        "OTEL_TRACES_EXPORTER": "otlp",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": "otlp",
    }.items():
        monkeypatch.setenv(key, value)
    rows = records()
    rows[0]["attributes"].update(
        input=canary, output=canary, owner_id=canary, encrypted_content=canary
    )
    from opentelemetry import trace

    before = trace.get_tracer_provider()
    with Capture() as c:
        c.observations(rows)
        with pytest.raises(OSError, match="Offline SDK network disabled"):
            socket.getaddrinfo("cloud.langfuse.com", 443)
        with pytest.raises(OSError):
            socket.create_connection(("1.1.1.1", 443))
        with pytest.raises(ValueError):
            c.http.get("https://cloud.langfuse.com")
        logging.getLogger("langfuse").error(canary, exc_info=(ValueError, ValueError(canary), None))
        out = json.dumps(c.flush()) + capsys.readouterr().err
        assert canary not in out and "encrypted_content" not in out
        assert trace.get_tracer_provider() is before
        assert "langfuse.openai" not in sys.modules and "langfuse.langchain" not in sys.modules


def test_failure_no_retry_shutdown_and_cancellation():
    before = {t.ident for t in threading.enumerate()}
    c = Capture(fail=True)
    with pytest.raises(asyncio.CancelledError), c:
        c.observations(records())
        assert not c.flush()
        failed = c.failed
        c.flush()
        assert c.failed == failed
        raise asyncio.CancelledError
    c.close()
    assert c.closed and {t.ident for t in threading.enumerate()} <= before
    with pytest.raises(ValueError):
        c.observations(records())


def test_collision_and_changed_duplicate_rejected():
    rows = records()
    with Capture() as c:
        c.observations(rows)
        bad = copy.deepcopy(rows[:1])
        bad[0]["duration_ms"] += 1
        with pytest.raises(ValueError, match="Conflicting"):
            c.observations(bad)
        bad = copy.deepcopy(rows[:1])
        bad[0]["span_id"] = "0" * 16 + rows[0]["span_id"][-16:]
        with pytest.raises(ValueError, match="collision"):
            c.observations(bad)


@pytest.mark.parametrize("mutation", ["stage", "duration_ms", "trace_id", "ended_ns"])
def test_malformed_capture_rejected(mutation):
    rows = records()[:1]
    rows[0][mutation] = "private-canary"
    with Capture() as c, pytest.raises(ValueError):
        c.observations(rows)
