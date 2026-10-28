"""Actual local counted public replay. No genuine cases, accounts or money."""

import asyncio
import copy
import json
import os
import subprocess
import sys
from datetime import timedelta

import httpx
import pytest
from approval_db_doubles import Controls
from authority_doubles import NOW
from responses_doubles import fixture
from test_profile_postgres import pg_schema as pg_schema
from test_token_admission import Backend

from experiments import synthetic_collection as e
from future_training.agent.protocol import canonical
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.persistence.counted_spending import CountedSpendingLedger


@pytest.fixture(scope="module")
def paths():
    return e.cases.sealed.public_sources()


@pytest.fixture
def stable(monkeypatch, paths):
    monkeypatch.setattr(e.cases.sealed, "public_sources", lambda: paths)


@pytest.fixture
async def rig(pg_schema, stable):
    ctl = Controls(pg_schema[1])
    wall = [NOW]
    ledger = CountedSpendingLedger(connect=ctl.connect, now=lambda: wall[0])
    p, g, s = e.SCOPE
    await ledger.create_replay_project(p, 1_000_000, 1_000_000)
    await ledger.grant(p, g, 1_000_000, NOW + timedelta(days=2))
    await ledger.session(p, g, s, 1_000_000, NOW + timedelta(hours=2))
    c = e.Collection(ledger, e.Issuer(now=lambda: wall[0]))
    await c.initialize()
    try:
        yield c, ctl, wall
    finally:
        await ctl.settle_retained(commit=False)


def values(c, ordinal, *, repair=False):
    profile = e.cases.CaseContent.model_validate_json(c.originals[ordinal - 1]).profile
    output = dict(outcome="plan", plan=plan_week(profile, load_catalog()).plan.model_dump())
    final = fixture()
    final["output"][0]["content"][0]["text"] = canonical({"result": output}).decode()
    if repair:
        broken = copy.deepcopy(final)
        bad = copy.deepcopy(output)
        bad["plan"]["days"][0]["planned_seconds"] += 1
        broken["output"][0]["content"][0]["text"] = canonical({"result": bad}).decode()
        return [fixture("tool"), broken, final]
    return [fixture("tool"), final]


@pytest.mark.integration
async def test_all_ten_actual_counted_cases_summary_and_duplicate(rig):
    c, ctl, _ = rig
    result = []
    for i in range(1, 11):
        backend = Backend(values(c, i, repair=i == 3))
        receipt = c.receipt(i)
        row = await c.run(i, receipt, httpx.MockTransport(backend))
        result.append(row)
        assert len(backend.paths) == (6 if i == 3 else 4)
        assert row["scored"]["hard_passed"] is (i != 3)
        assert row["scored"]["quality_scores"] is None
        assert row["accounting"]["held_micro"] == (3000 if i == 3 else 2000)
        assert row["accounting"]["actual_total_micro"] is None
        fresh = e.Collection(c.ledger, c.issuer)
        assert await fresh.run(i, receipt, httpx.MockTransport(Backend([]))) == row
    summary = await c.summary()
    assert summary["scheduled"] == 10
    assert summary["dispositions"] == dict(
        not_started=0, interrupted=0, indeterminate=0, failed=1, completed=9
    )
    assert summary["observed_counts_subtotal"] == dict(
        count_requests=21, provider_requests=21, wire_requests=42
    )
    assert summary["known_held_subtotal_micro"] == 21000 and summary["actual_total_micro"] is None
    assert result[2]["proposals"][0]["agent_rejected"]
    directory = e.ROOT / ".cache/f3-e9-implementation/evidence"
    directory.mkdir(parents=True, exist_ok=True)
    e.cases.sealed.write_exclusive(directory / (c.schema + ".json"), summary)
    async with await ctl.connect() as db:
        assert (await (await db.execute("SELECT count(*) FROM experiment_e9_results")).fetchone())[
            0
        ] == 10
        assert (await (await db.execute("SELECT count(*) FROM approved_plans")).fetchone())[0] == 0
        assert (
            await (
                await db.execute("SELECT count(*) FROM probe_authorities WHERE state='active'")
            ).fetchone()
        )[0] == 0


@pytest.mark.integration
async def test_concurrent_claim_and_changed_receipt_do_not_replace(rig):
    c, ctl, wall = rig
    entered, release = asyncio.Event(), asyncio.Event()

    async def wait(query, db):
        if "INSERT INTO experiment_e9_results" in query:
            entered.set()
            await release.wait()

    ctl.before_execute = wait
    receipt = c.receipt(2)
    backend = Backend(values(c, 2))
    first = asyncio.create_task(c.run(2, receipt, httpx.MockTransport(backend)))
    await asyncio.wait_for(entered.wait(), 10)
    fresh = e.Collection(c.ledger, c.issuer)
    with pytest.raises(ValueError):
        await fresh.run(2, receipt, httpx.MockTransport(Backend([])))
    release.set()
    await first
    ctl.before_execute = None
    wall[0] += timedelta(minutes=1)
    with pytest.raises(ValueError, match="conflict"):
        await fresh.run(2, fresh.receipt(2), httpx.MockTransport(Backend([])))
    assert len(backend.paths) == 4


@pytest.mark.integration
@pytest.mark.parametrize("stage", ["claim", "result"])
@pytest.mark.parametrize("mode", ["lost_after", "rollback_uncertain", "open_uncertain"])
async def test_ambiguous_commits_retain_slot_and_never_replay(rig, stage, mode):
    c, ctl, _ = rig

    async def fault(query, db):
        if (stage == "claim" and "INSERT INTO experiment_e9_results" in query) or (
            stage == "result" and "UPDATE experiment_e9_results" in query
        ):
            ctl.mode = mode

    ctl.after_execute = fault
    backend = Backend(values(c, 1))
    receipt = c.receipt(1)
    with pytest.raises(ValueError):
        await c.run(1, receipt, httpx.MockTransport(backend))
    ctl.after_execute = None
    ctl.mode = "normal"
    assert len(backend.paths) == (0 if stage == "claim" else 4)
    fresh = e.Collection(c.ledger, c.issuer)
    s = await fresh.summary()
    assert s["dispositions"]["not_started"] == 9
    if stage == "result" and mode == "lost_after":
        assert s["dispositions"]["completed"] == 1
        assert s["known_held_subtotal_micro"] == 2000
    else:
        assert s["dispositions"]["indeterminate"] == 1
        with pytest.raises(ValueError):
            await fresh.run(1, receipt, httpx.MockTransport(Backend([])))


@pytest.mark.integration
async def test_cancellation_retains_count_hold_and_interrupted_result(rig):
    c, _, _ = rig
    entered, drained = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    backend = Backend([], count=hang)
    task = asyncio.create_task(c.run(4, c.receipt(4), httpx.MockTransport(backend)))
    await asyncio.wait_for(entered.wait(), 10)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    s = await c.summary()
    assert drained.is_set() and len(backend.paths) == 1
    assert s["dispositions"]["interrupted"] == 1 and s["known_held_subtotal_micro"] == 1000
    assert s["actual_total_micro"] is None


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["partial_fence", "observations", "accounting", "result"])
async def test_partial_or_missing_evidence_is_not_success(rig, monkeypatch, fault):
    c, ctl, _ = rig
    if fault == "partial_fence":
        path = c.fence_path(1)
        path.write_bytes(b'{"partial":')
    elif fault == "observations":
        monkeypatch.setattr(e.shared.Observations, "_response", lambda *a: None)
    elif fault == "accounting":

        async def fail(*a):
            raise OSError("PRIVATE_CANARY")

        monkeypatch.setattr(c, "accounting", fail)
    else:

        async def fail(*a):
            raise OSError("PRIVATE_CANARY")

        monkeypatch.setattr(c, "_finish", fail)
    backend = Backend(values(c, 1))
    receipt = c.receipt(1)
    if fault in ("partial_fence", "result"):
        with pytest.raises(ValueError):
            await c.run(1, receipt, httpx.MockTransport(backend))
    else:
        result = await c.run(1, receipt, httpx.MockTransport(backend))
        assert not result["evidence_complete"]
    fresh = e.Collection(c.ledger, c.issuer)
    s = await fresh.summary()
    assert s["dispositions"]["indeterminate"] == 1 and s["slots"][0]["hard_passed"] is not True
    if fault == "partial_fence":
        assert not backend.paths


@pytest.mark.integration
async def test_alternate_working_directory_and_wrong_configuration(rig, monkeypatch, tmp_path):
    c, _, _ = rig
    r = c.receipt(1)
    await c.run(1, r, httpx.MockTransport(Backend(values(c, 1))))
    monkeypatch.chdir(tmp_path)
    fresh = e.Collection(c.ledger, c.issuer)
    before = await fresh.summary()
    assert (await fresh.run(1, r, httpx.MockTransport(Backend([]))))["disposition"] == "completed"
    fresh.configuration["fingerprint"] = "0" * 64
    with pytest.raises(ValueError):
        await fresh.summary()
    assert before["dispositions"]["completed"] == 1


@pytest.mark.parametrize("ordinal", [True, 0, 11, "1"])
def test_no_arbitrary_case_identity(ordinal):
    with pytest.raises(ValueError):
        e.ordinal_checked(ordinal)


def test_no_genuine_opening():
    with pytest.raises(ValueError):
        e.open_genuine(approved=True)


def test_authority_ledger_and_credential_objects_are_not_replay_inputs():
    with pytest.raises(ValueError, match="exact_synthetic"):
        e.Collection(object(), e.Issuer(now=lambda: NOW))


@pytest.mark.integration
async def test_unowned_private_execution_or_result_write_is_denied(rig):
    from future_training.agent.budget import Deadline, SystemClock

    c, _, _ = rig
    b = c.binding(1)
    receipt = c.receipt(1)
    backend = Backend(values(c, 1))
    with pytest.raises(ValueError, match="owned_execution_required"):
        await c._execute(
            b, receipt, httpx.MockTransport(backend), Deadline(SystemClock()), object()
        )
    with pytest.raises(ValueError, match="owned_execution_required"):
        await c._finish(b, receipt, {}, object())
    assert not backend.paths
    assert (await c.summary())["dispositions"]["not_started"] == 10


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["case", "tag", "source", "expired", "transport"])
async def test_receipt_or_transport_mismatch_stops_before_send(rig, fault):
    c, _, wall = rig
    raw = c.receipt(1)
    if fault in ("case", "tag"):
        v = json.loads(raw)
        if fault == "case":
            v["body"]["binding"]["ordinal"] = 2
        else:
            v["tag"] = "0" * 64
        raw = canonical(v)
    if fault == "source":
        c.configuration["fingerprint"] = "0" * 64
    if fault == "expired":
        wall[0] += timedelta(minutes=31)
    backend = Backend(values(c, 1))
    with pytest.raises(ValueError):
        await c.run(1, raw, object() if fault == "transport" else httpx.MockTransport(backend))
    assert not backend.paths


@pytest.mark.integration
async def test_process_restart_after_claim_reads_uncertainty_without_execution(rig):
    c, ctl, _ = rig
    ctl.point = "after"
    backend = Backend(values(c, 1))
    receipt = c.receipt(1)
    task = asyncio.create_task(c.run(1, receipt, httpx.MockTransport(backend)))
    await asyncio.wait_for(ctl.entered.wait(), 10)
    task.cancel()
    ctl.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    ctl.point = None
    assert not backend.paths
    code = """import asyncio,json,sys
from datetime import datetime,UTC
sys.path[:0]=['src']
import psycopg
from experiments.synthetic_collection import Collection,Issuer
from future_training.persistence.counted_spending import CountedSpendingLedger
async def connect():return await psycopg.AsyncConnection.connect(sys.argv[1])
async def main():
 c=Collection(CountedSpendingLedger(connect=connect),Issuer(now=lambda:datetime.now(UTC)))
 s=await c.summary()
 print(json.dumps({'dispositions':s['dispositions'],'actual_total_micro':s['actual_total_micro']}))
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(main())
"""
    process = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, ctl.dsn],
        cwd=e.ROOT,
        env={
            k: os.environ[k]
            for k in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP")
            if k in os.environ
        },
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    value = json.loads(process.stdout)
    assert value["dispositions"]["indeterminate"] == 1 and value["actual_total_micro"] is None
    with pytest.raises(ValueError):
        await e.Collection(c.ledger, c.issuer).run(1, receipt, httpx.MockTransport(Backend([])))


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["write", "owner", "arguments", "refusal", "model", "usage"])
async def test_native_bad_tool_or_usage_cannot_become_passing_result(rig, kind):
    c, _, _ = rig
    native = values(c, 2)
    if kind == "refusal":
        native = [fixture("refusal")]
    elif kind in ("model", "usage"):
        if kind == "model":
            native[0]["model"] = "unexpected-model"
        else:
            native[0].pop("usage")
    else:
        tool = native[0]["output"][-1]
        if kind == "write":
            tool["name"] = "approve_plan"
        else:
            tool["arguments"] = (
                '{"owner_id":"PRIVATE_CANARY"}' if kind == "owner" else '{"limit":true}'
            )
    backend = Backend(native)
    value = await c.run(2, c.receipt(2), httpx.MockTransport(backend))
    assert value["disposition"] != "completed"
    assert value["scored"] is None or not value["scored"]["hard_passed"]
    assert value["accounting"]["actual_total_micro"] is None


@pytest.mark.integration
@pytest.mark.parametrize(
    "kind", ["score", "boolean", "missing", "accounting", "partial", "provenance"]
)
async def test_stored_conflict_or_partial_result_is_indeterminate_not_pass(rig, kind):
    from psycopg.types.json import Jsonb

    c, ctl, _ = rig
    value = await c.run(1, c.receipt(1), httpx.MockTransport(Backend(values(c, 1))))
    altered = copy.deepcopy(value)
    if kind == "score":
        altered["scored"]["hard_passed"] = False
    elif kind == "boolean":
        altered["scored"]["hard_passed"] = 1
    elif kind == "missing":
        altered["observation"].pop("no_publication")
    elif kind == "accounting":
        altered["accounting"]["held_micro"] = 0
    elif kind == "partial":
        altered = {"version": "synthetic-ten-result-v1"}
    else:
        altered["provenance"] = "live"
    async with await ctl.connect() as db:
        await db.execute(
            "UPDATE experiment_e9_results SET result=%s WHERE ordinal=1", (Jsonb(altered),)
        )
    s = await c.summary()
    assert s["dispositions"]["indeterminate"] == 1 and s["hard_passed"] == 0
    assert s["unknown_liability_slots"] == 1


@pytest.mark.integration
async def test_deadline_shutdown_and_cleanup_faults_are_retained(rig, monkeypatch):
    c, _, _ = rig
    backend = Backend(values(c, 1))
    transport = httpx.MockTransport(backend)

    async def failed_close():
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(transport, "aclose", failed_close)
    result = await c.run(1, c.receipt(1), transport)
    assert result["disposition"] == "indeterminate" and "cleanup_uncertain" in result["reasons"]
    assert result["accounting"]["held_micro"] == 2000


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["timeout", "shutdown"])
async def test_count_timeout_or_shutdown_drains_without_retry(rig, fault):
    from agent_doubles import ManualClock

    c, _, _ = rig
    c.clock = ManualClock()
    entered, drained = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    backend = Backend([], count=hang)
    task = asyncio.create_task(c.run(1, c.receipt(1), httpx.MockTransport(backend)))
    await asyncio.wait_for(entered.wait(), 10)
    if fault == "timeout":
        c.clock.advance(30)
    else:
        await c.ledger.stop(e.SCOPE[0])
        task.cancel()
    if fault == "shutdown":
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        with pytest.raises(ValueError):
            await task
    assert drained.is_set() and len(backend.paths) == 1
    s = await c.summary()
    assert s["dispositions"]["interrupted"] == 1 and s["known_held_subtotal_micro"] == 1000


@pytest.mark.integration
async def test_fsync_failure_blocks_new_handle_after_partial_claim(rig, monkeypatch):
    c, _, _ = rig
    original = e.cases.sealed.os.fsync

    def fail(*a):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(e.cases.sealed.os, "fsync", fail)
    receipt = c.receipt(1)
    backend = Backend(values(c, 1))
    with pytest.raises(ValueError):
        await c.run(1, receipt, httpx.MockTransport(backend))
    monkeypatch.setattr(e.cases.sealed.os, "fsync", original)
    assert not backend.paths
    with pytest.raises(ValueError):
        await e.Collection(c.ledger, c.issuer).run(1, receipt, httpx.MockTransport(Backend([])))
    assert (await c.summary())["dispositions"]["indeterminate"] == 1
