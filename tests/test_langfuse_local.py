import asyncio
import copy
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from agent_doubles import invalid_final, tool_response
from profile_doubles import MemoryProfiles
from test_identity_profiles import client_for
from test_observability import CANARIES, A, assert_private
from test_observability import console as console

from future_training.agent.fake import ScriptedFake
from future_training.api import create_app
from future_training.config import Settings
from future_training.experiments.model_eval_assets import SCORE_REFERENCE
from future_training.experiments.model_evaluation import evaluate
from future_training.langfuse_local import LangfuseTracer, Observations, experiment_projection
from future_training.observability import Span, span


def record(**changes):
    return {
        "stage": "tool",
        "trace_id": uuid4().hex,
        "span_id": uuid4().hex,
        "parent_id": None,
        "duration_ms": 12.5,
        "attributes": {"outcome": "ok", "tool": "search_exercises"},
        **changes,
    }


def test_duplicates_conflicts_eviction_byte_bound_and_copy():
    buffer = Observations(capacity=2, byte_limit=1024)
    r = record()
    buffer.append(r)
    buffer.append(r)
    buffer.append({**r, "duration_ms": 11})
    assert (buffer.duplicates, buffer.conflicts) == (1, 1)
    buffer.snapshot()[0]["attributes"]["secret"] = "canary"
    assert "secret" not in buffer.snapshot()[0]["attributes"]
    for _ in range(10):
        buffer.append(record())
    assert len(buffer.snapshot()) <= 2 and buffer._bytes <= 1024 and buffer.dropped >= 9
    buffer.close()
    buffer.close()
    buffer.append(record())
    assert not buffer.snapshot() and buffer._bytes == 0


@pytest.mark.parametrize(
    "change",
    [
        dict(trace_id="0" * 32),
        dict(stage="secret"),
        dict(span_id="bad"),
        dict(duration_ms=float("nan")),
    ],
)
def test_invalid_observations_rejected(change):
    b = Observations()
    b.append(record(**change))
    assert b.invalid == 1 and not b.snapshot()


def test_concurrent_duplicate_publication_is_bounded():
    b = Observations()
    r = record()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(b.append, [r] * 100))
    assert len(b.snapshot()) == 1 and b.duplicates == 99


@pytest.mark.parametrize("canary", CANARIES)
def test_projection_privacy_and_no_environment_activation(canary, monkeypatch, console):
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", canary)
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://outside.invalid")
    tracer = LangfuseTracer()
    with Span("http", tracer=tracer, owner=canary, input=canary):
        with span("provider", raw_response=canary, credential=canary):
            pass
    projected = tracer.observations.snapshot()
    assert len(projected) == 2 and projected[0]["parent_id"] == projected[1]["span_id"]
    rendered = json.dumps(projected) + console.getvalue()
    assert canary not in rendered
    assert_private(rendered)


async def test_induced_failure_trace_and_repair_evidence(profile, console):
    tracer = LangfuseTracer()
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=MemoryProfiles(),
        provider=ScriptedFake([tool_response, invalid_final, invalid_final]),
        tracer=tracer,
    )
    async with client_for(app) as client:
        await client.put(
            "/api/v1/profile", headers=A, json={"expected_revision": 0, "preferences": profile}
        )
        response = await client.post(
            "/api/v1/drafts/stream", headers=A, json={"profile_revision": 1}
        )
    rows = [
        r
        for r in tracer.observations.snapshot()
        if r["trace_id"] == response.headers["x-request-id"]
    ]
    assert '"outcome":"error"' in response.text
    assert len([r for r in rows if r["stage"] == "provider"]) == 3
    assert len([r for r in rows if r["stage"] == "tool"]) == 1
    assert len([r for r in rows if r["stage"] == "agent.repair"]) == 2
    final = next(r for r in rows if r["stage"] == "agent.execute")["attributes"]
    assert final["reason"] == "semantic_repair_exhausted"
    assert (final["provider_requests"], final["semantic_repairs"], final["tool_dispatches"]) == (
        3,
        1,
        1,
    )
    ids = {r["span_id"] for r in rows}
    assert all(r["parent_id"] in ids for r in rows if r["parent_id"])
    assert_private(json.dumps(rows) + console.getvalue())
    if os.environ.get("FATA_WRITE_F305A_EVIDENCE") == "1":
        p = Path(".cache/f3-05a/failure.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


async def test_cancellation_observed_and_context_cleared():
    tracer = LangfuseTracer()
    entered = asyncio.Event()

    async def run():
        with Span("http", tracer=tracer):
            with span("provider"):
                entered.set()
                await asyncio.Future()

    task = asyncio.create_task(run())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert all(r["attributes"]["outcome"] == "cancelled" for r in tracer.observations.snapshot())
    with Span("http", tracer=tracer):
        pass
    assert tracer.observations.snapshot()[-1]["parent_id"] is None


async def test_full_existing_evaluation_projection_without_rescoring():
    tracer = LangfuseTracer()
    report = await evaluate(tracer=tracer)
    projected = experiment_projection(report)
    assert len(projected["items"]) == 150 and len(report["trace_links"]) == 150
    assert projected["human_scores"] == projected["judge_scores"] == 0
    assert not tracer.observations.dropped
    expected = json.loads(SCORE_REFERENCE.read_text(encoding="utf-8"))
    for actual, old in zip(report["cases"], expected["cases"], strict=True):
        actual.pop("elapsed_ms")
        assert actual == old
    assert all(i["quality_scores"] is None for i in projected["items"])
    assert all(i["trace_id"] for i in projected["items"])


@pytest.mark.parametrize("mutation", ["quality", "hard", "split", "duplicate"])
def test_experiment_integrity_cannot_invent_quality_or_hide_hard_failures(mutation):
    report = json.loads(SCORE_REFERENCE.read_text(encoding="utf-8"))
    report = copy.deepcopy(report)
    if mutation == "quality":
        report["cases"][0]["quality_scores"] = {"human": 5}
    elif mutation == "hard":
        bad = next(r for r in report["cases"] if not r["hard_passed"])
        bad["hard_passed"] = True
    elif mutation == "split":
        report["cases"][0]["split"] = "sealed_holdout"
    else:
        report["cases"][1] = report["cases"][0]
    with pytest.raises(ValueError):
        experiment_projection(report)
