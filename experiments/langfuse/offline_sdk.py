"""Isolated SDK exercise. Permanently seals this disposable process's network.

Never import into the application: its only inputs are bounded, sanitized local
snapshots. No exporter, credential, URL or HTTP client is caller-configurable.
"""

import json
import logging
import os
import socket
from collections import deque
from uuid import uuid4

from future_training.observability import configure_logging, safe_record

_ASYNC_ORIGINAL = None


def seal():
    for key in tuple(os.environ):
        if key.startswith(("LANGFUSE_", "OTEL_", "OPENAI_", "ANTHROPIC_")) or key.upper() in {
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        }:
            os.environ.pop(key)
    os.environ.update(
        LANGFUSE_MEDIA_UPLOAD_ENABLED="false",
        OTEL_BSP_MAX_QUEUE_SIZE="512",
        OTEL_BSP_MAX_EXPORT_BATCH_SIZE="64",
    )

    def denied(*args, **kwargs):
        raise OSError("Offline SDK network disabled")

    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
        "create_connection",
    ):
        setattr(socket, name, denied)
    for name in ("connect", "connect_ex", "sendto", "sendmsg"):
        if hasattr(socket.socket, name):
            setattr(socket.socket, name, denied)
    configure_logging()


class Capture:
    def __init__(self, *, fail=False):
        global _ASYNC_ORIGINAL
        seal()
        import httpx
        from langfuse import Langfuse
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
        from opentelemetry.sdk.trace.id_generator import IdGenerator

        for name in tuple(logging.Logger.manager.loggerDict):
            if name.startswith(("langfuse", "opentelemetry")):
                logger = logging.getLogger(name)
                logger.handlers.clear()
                logger.propagate = True
                logger.setLevel(logging.WARNING)
        self.fail, self.closed, self.failed, self.dropped = fail, False, 0, 0
        self.spans, self.requests = deque(maxlen=2048), deque(maxlen=512)
        self.seen, self.collisions, self.scored = {}, {}, {}
        self.experiment_links = {}
        self.async_clients = []
        if _ASYNC_ORIGINAL is None:
            _ASYNC_ORIGINAL = httpx.AsyncClient
        owner = self

        class OfflineAsync(_ASYNC_ORIGINAL):
            def __init__(self, *args, **kwargs):
                super().__init__(
                    transport=httpx.MockTransport(
                        lambda r: (_ for _ in ()).throw(ValueError("Async SDK API disabled"))
                    ),
                    trust_env=False,
                    follow_redirects=False,
                    timeout=1,
                )
                owner.async_clients.append(self)

        # SDK 5.0.4 creates a secondary async API client even for sync tracing.
        # Its public constructor has no async-client option. Seal this separately
        # isolated process's factory as well as all socket operations.
        httpx.AsyncClient = OfflineAsync

        owner = self

        class Exporter(SpanExporter):
            def export(self, spans):
                if owner.fail:
                    owner.failed += len(spans)
                    return SpanExportResult.FAILURE
                for s in spans:
                    if len(owner.spans) == owner.spans.maxlen:
                        owner.dropped += 1
                    # No ReadableSpan/resource/event objects escape to artifacts.
                    owner.spans.append(
                        {
                            "trace_id": f"{s.context.trace_id:032x}",
                            "span_id": f"{s.context.span_id:016x}",
                            "parent_id": f"{s.parent.span_id:016x}" if s.parent else None,
                            "name": s.name,
                            "status": s.status.status_code.name,
                            "duration_ns": s.end_time - s.start_time,
                            "attributes": dict(s.attributes),
                        }
                    )
                return SpanExportResult.SUCCESS

            def shutdown(self):
                return None

        class IDs(IdGenerator):
            value = 1
            trace_value = 1

            def generate_span_id(self):
                return self.value

            def generate_trace_id(self):
                return self.trace_value

        def mock(request):
            if (
                request.method != "POST"
                or str(request.url) != "https://offline.invalid/api/public/scores"
            ):
                raise ValueError("Offline SDK endpoint denied")
            value = json.loads(request.content)
            if len(request.content) > 65536:
                raise ValueError("Offline SDK body too large")
            # Auth is synthetic and never retained; keep typed numerical score
            # evidence only, not headers, raw requests or exceptions.
            self.requests.append(value)
            return httpx.Response(202, json={"message": "Accepted"})

        self.ids = IDs()
        self.provider = TracerProvider(
            resource=Resource({"service.name": "future-training-offline"}),
            id_generator=self.ids,
            shutdown_on_exit=False,
        )
        self.http = httpx.Client(
            transport=httpx.MockTransport(mock), trust_env=False, follow_redirects=False, timeout=1
        )
        self.public_key = "offline-" + uuid4().hex
        self.client = Langfuse(
            public_key=self.public_key,
            secret_key="synthetic-no-authority",
            base_url="https://offline.invalid",
            httpx_client=self.http,
            tracer_provider=self.provider,
            span_exporter=Exporter(),
            tracing_enabled=True,
            environment="offline-synthetic",
            release="f3-05a",
            sample_rate=1,
            timeout=1,
            flush_at=64,
            flush_interval=1,
            media_upload_thread_count=1,
            debug=False,
            mask=lambda **kw: None if kw.get("field") in ("input", "output") else kw.get("data"),
        )

    def observations(self, records):
        if self.closed or len(records) > 2048:
            raise ValueError("Closed or oversized capture")
        from langfuse import LangfuseAgent, LangfuseGeneration, LangfuseSpan, LangfuseTool
        from opentelemetry.context import Context
        from opentelemetry.trace import (
            NonRecordingSpan,
            SpanContext,
            TraceFlags,
            set_span_in_context,
        )

        for original in records:
            r = safe_record(original)
            ended = original.get("ended_ns")
            if (
                r is None
                or type(ended) is not int
                or not 0 < ended < 2**63
                or int(r["trace_id"], 16) == 0
            ):
                raise ValueError("Invalid sanitized observation")
            key = (r["trace_id"], r["span_id"])
            fingerprint = json.dumps(r, sort_keys=True)
            if key in self.seen:
                if self.seen[key] != fingerprint:
                    raise ValueError("Conflicting observation")
                continue
            if len(self.seen) >= 2048:
                raise ValueError("Capture identity capacity exhausted")
            mapped = int(r["span_id"][-16:], 16)
            mapping = (r["trace_id"], mapped)
            if mapped == 0 or (mapping in self.collisions and self.collisions[mapping] != key):
                raise ValueError("OTel identity collision")
            self.collisions[mapping] = key
            self.seen[key] = fingerprint
            self.ids.value = mapped
            self.ids.trace_value = int(r["trace_id"], 16)
            parent = int(r["parent_id"][-16:], 16) if r["parent_id"] else 0
            context = set_span_in_context(
                NonRecordingSpan(SpanContext(int(r["trace_id"], 16), parent, True, TraceFlags(1))),
                Context(),
            )
            if parent == 0:
                if r["parent_id"] is not None:
                    raise ValueError("Invalid parent mapping")
                context = Context()
            duration = round(r["duration_ms"] * 1_000_000)
            if duration > ended:
                raise ValueError("Invalid timing interval")
            span = self.provider.get_tracer(
                "langfuse-sdk", attributes={"public_key": self.public_key}
            ).start_span(r["stage"], context=context, start_time=ended - duration)
            if r["stage"] == "evaluation.case" and r["trace_id"] in self.experiment_links:
                item = self.experiment_links[r["trace_id"]]
                span.set_attributes(
                    {
                        "langfuse.experiment.id": item["experiment_id"],
                        "langfuse.experiment.name": "offline-"
                        + item["source"]
                        + "-model-evaluation-v1",
                        "langfuse.experiment.item.id": item["case_id"],
                        "langfuse.experiment.item.root_observation_id": f"{mapped:016x}",
                        "langfuse.experiment.item.metadata": json.dumps(item["metadata"]),
                    }
                )
            a = r["attributes"]
            metadata = {
                **a,
                "local_span_id": r["span_id"],
                "local_parent_id": r["parent_id"],
                "duration_ms": r["duration_ms"],
                "root": r["parent_id"] is None,
                "usage_scope": "request_aggregate"
                if r["stage"] == "agent.execute"
                else "stage_metadata_only",
            }
            kwargs = dict(
                otel_span=span,
                langfuse_client=self.client,
                metadata=metadata,
                level="ERROR"
                if a.get("outcome") == "error"
                else "WARNING"
                if a.get("outcome") == "cancelled"
                else "DEFAULT",
                status_message=a.get("reason"),
            )
            wrapper = (
                LangfuseGeneration
                if r["stage"] == "provider"
                else LangfuseTool
                if r["stage"] == "tool"
                else LangfuseAgent
                if r["stage"].startswith("agent.")
                else LangfuseSpan
            )
            observation = wrapper(**kwargs)
            observation.end(end_time=ended)

    def scores(self, projection):
        if self.closed or len(projection["items"]) != 150:
            raise ValueError("Exact bounded experiment required")
        from langfuse import Evaluation

        from future_training.experiments.model_evaluation import load_suite

        known = {c.case_id: c for c in load_suite()[1]}
        expected = {(s, c) for s in ("template", "fake", "replay") for c in known}
        if {(i["source"], i["case_id"]) for i in projection["items"]} != expected:
            raise ValueError("Exact scenario/source mapping required")

        for item in projection["items"]:
            if item.get("quality_scores") is not None:
                raise ValueError("No fabricated quality score")
            trace_id = item["trace_id"]
            if (
                type(trace_id) is not str
                or len(trace_id) != 32
                or any(c not in "0123456789abcdef" for c in trace_id)
            ):
                raise ValueError("Invalid score correlation")
            if len(item["scores"]) != 2 or {s["name"] for s in item["scores"]} != {
                "hard_passed",
                "handling_passed",
            }:
                raise ValueError("Only existing hard/handling scores")
            for score in item["scores"]:
                if (
                    type(score["value"]) is not int
                    or score["value"] not in (0, 1)
                    or score["data_type"] != "BOOLEAN"
                ):
                    raise ValueError("Strict BOOLEAN score required")
                key = (item["source"], item["case_id"], score["name"])
                if key in self.scored:
                    if self.scored[key] != score["value"]:
                        raise ValueError("Conflicting score")
                    continue
                self.scored[key] = score["value"]
                evaluation = Evaluation(**score)
                case = known[item["case_id"]]
                self.client.create_score(
                    name=evaluation.name,
                    value=evaluation.value,
                    data_type=evaluation.data_type,
                    trace_id=item["trace_id"],
                    metadata={
                        "case_id": case.case_id,
                        "source": item["source"],
                        "split": case.split,
                        "exposure": case.exposure,
                    },
                )

    def experiments(self, projection):
        """Use documented experiment OTEL attributes, never another task runner."""
        from future_training.experiments.model_evaluation import load_suite

        known = {c.case_id: c for c in load_suite()[1]}
        items = projection["items"]
        expected = {(s, c) for s in ("template", "fake", "replay") for c in known}
        if (
            self.closed
            or len(items) != 150
            or {(i["source"], i["case_id"]) for i in items} != expected
        ):
            raise ValueError("Exact bounded experiment required")
        if self.experiment_links:
            raise ValueError("Experiment already bound")
        ids = {s: uuid4().hex for s in ("template", "fake", "replay")}
        for item in items:
            trace_id = item["trace_id"]
            if (
                type(trace_id) is not str
                or len(trace_id) != 32
                or any(c not in "0123456789abcdef" for c in trace_id)
            ):
                raise ValueError("Invalid experiment trace")
            case = known[item["case_id"]]
            self.experiment_links[trace_id] = {
                "experiment_id": ids[item["source"]],
                "source": item["source"],
                "case_id": case.case_id,
                "metadata": {
                    "split": case.split,
                    "exposure": case.exposure,
                    "eligibility": case.eligibility,
                    "dataset_version": "model-evaluation-v1",
                    "evidence": "offline_fixture",
                },
            }
        if len(self.experiment_links) != 150:
            raise ValueError("Distinct experiment traces required")

    def flush(self):
        self.client.flush()
        return list(self.spans)

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.client.shutdown()
        finally:
            # Pinned SDK 5.0.4 leaves the prompt-cache refresh consumer running
            # after client.shutdown(). No prompt cache API is exposed here.
            self.client._resources.prompt_cache._task_manager.shutdown()
            self.provider.shutdown()
            self.http.close()
            for client in self.async_clients:
                # No async API operation is permitted. MockTransport.aclose()
                # completes synchronously without a loop/socket/background task.
                coroutine = client.aclose()
                try:
                    coroutine.send(None)
                except StopIteration:
                    pass
                else:
                    coroutine.close()
                    raise RuntimeError("Offline async cleanup unexpectedly suspended")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
