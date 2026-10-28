"""Public-data dummy review only. No human judgments, curator or live model."""

import asyncio
import copy
import json
import os
import subprocess
import sys

import httpx
import pytest
import test_synthetic_collection as execution
from test_token_admission import Backend

from experiments import blinded_review as e
from future_training.agent.protocol import canonical

pg_schema, paths, stable, rig = (
    execution.pg_schema,
    execution.paths,
    execution.stable,
    execution.rig,
)


@pytest.fixture
async def review(rig):
    c, ctl, _ = rig
    for i in (1, 2):
        await c.run(
            i, c.receipt(i), httpx.MockTransport(Backend(execution.values(c, i, repair=i == 2)))
        )
    r = e.Review(c)
    await r.initialize()
    await r.issue()
    return r, ctl


def rated(form, value=3):
    v = copy.deepcopy(form)
    v.update(judgment_status="rated_dummy", ratings=dict.fromkeys(e.DIMENSIONS, value))
    return v


@pytest.mark.integration
async def test_full_synthetic_packet_import_report_demo(rig):
    c, ctl, _ = rig
    backends = []
    for i in range(1, 11):
        backend = Backend(execution.values(c, i, repair=i == 3))
        backends.append(backend)
        await c.run(i, c.receipt(i), httpx.MockTransport(backend))
    r = e.Review(c)
    await r.initialize()
    a = await r.issue()
    b = await r.build()
    assert a == b["packet"] == await r.issue() == await r.export()
    assert len(a["content"]["pairs"]) == 9
    text = canonical(a["content"]).decode()
    for secret in (
        "hard_passed",
        "scored",
        "quality_eligible",
        "template",
        "replay",
        "ME-D",
        "fixture-",
        "configuration",
        "reasoning",
        "accounting",
        "expected",
    ):
        assert secret not in text
    assert set(a) == {"version", "practice", "packet_id", "content"}
    assert all(set(p) == {"pair_id", "preferences", "variants"} for p in a["content"]["pairs"])
    forms = await r.blanks()
    assert len(forms) == 36
    first, second, third = rated(forms[0]), copy.deepcopy(forms[1]), rated(forms[2], 5)
    second.update(judgment_status="abstained_dummy", abstention_reason="unjudgeable")
    for v in (first, second, third):
        assert (await r.submit(canonical(v)))["result"] == "accepted_dummy"
    assert (await r.submit(canonical(first)))["result"] == "duplicate_dummy"
    with pytest.raises(ValueError, match="conflict"):
        await r.submit(canonical(rated(forms[0], 1)))
    with pytest.raises(ValueError):
        await r.submit(b'{"missing":true}')
    v = copy.deepcopy(first)
    v["evidence"] = "genuine_human"
    with pytest.raises(ValueError):
        await r.submit(canonical(v))
    report = await r.report()
    assert report["automated"]["hard_passed"] == 19 and report["automated"]["hard_failed"] == 1
    assert report["automated"]["completed_evaluations"] == 20
    d = report["dummy_review"]
    assert d["statuses"] == dict(
        rated_dummy=2, abstained_dummy=1, indeterminate=0, missing=33, ineligible_pair=4
    )
    assert d["events"] == dict(duplicate=1, conflict=1, invalid=2)
    assert d["planned_slots"] == 40 and d["issued_slots"] == 36
    assert d["planned_dimension_slots"] == 120 and d["dimension_denominators"]["rated_dummy"] == 6
    assert d["rated_per_dimension"] == dict.fromkeys(e.DIMENSIONS, 2)
    assert d["dummy_only_means"] == dict.fromkeys(e.DIMENSIONS, 4)
    assert (
        report["genuine_human"]["judgments"] == 0
        and report["genuine_human"]["quality_scores"] is None
    )
    assert sum(len(b.paths) for b in backends) == 42
    directory = e.ROOT / ".cache/f3-e10/evidence"
    directory.mkdir(parents=True, exist_ok=True)
    e.replay.cases.sealed.write_exclusive(directory / (c.schema + ".json"), report)


@pytest.mark.integration
async def test_invalid_judgments_do_not_consume_a_valid_first_result(review, capsys, caplog):
    r, _ = review
    form = (await r.blanks())[0]
    variants = []
    for number in (0, 6, True, 2.5, "3", None):
        variants.append(rated(form, number))
    v = rated(form)
    v["ratings"].pop("plan_variety")
    variants.append(v)
    v = rated(form)
    v["explanation_clarity"] = 5
    variants.append(v)
    v = rated(form)
    v["pair_id"] = "sealed-PRIVATE_CANARY"
    variants.append(v)
    v = rated(form)
    v["packet_id"] = "0" * 64
    variants.append(v)
    v = rated(form)
    v["source"] = "genuine_human"
    variants.append(v)
    v = rated(form)
    v["rubric"] = "other"
    variants.append(v)
    for v in variants:
        with pytest.raises(ValueError, match="^dummy_submission_invalid$"):
            await r.submit(canonical(v))
    assert not capsys.readouterr().out and "PRIVATE_CANARY" not in caplog.text
    before = await r.report()
    assert before["dummy_review"]["valid_submissions"] == 0
    await r.submit(canonical(rated(form)))
    assert (await r.report())["dummy_review"]["valid_submissions"] == 1


@pytest.mark.integration
@pytest.mark.parametrize("stage", ["claim", "result"])
@pytest.mark.parametrize("mode", ["lost_after", "rollback_uncertain", "open_uncertain"])
async def test_uncertain_import_commit_never_replaces_or_invents_review(review, stage, mode):
    r, ctl = review
    v = rated((await r.blanks())[0])

    async def fault(query, db):
        if (stage == "claim" and "INSERT INTO experiment_e10_reviews" in query) or (
            stage == "result" and "UPDATE experiment_e10_reviews" in query
        ):
            ctl.mode = mode

    ctl.after_execute = fault
    with pytest.raises(ValueError, match="uncertain"):
        await r.submit(canonical(v))
    ctl.mode = "normal"
    ctl.after_execute = None
    fresh = e.Review(r.auto)
    s = await fresh.report()
    if stage == "result" and mode == "lost_after":
        assert s["dummy_review"]["statuses"]["rated_dummy"] == 1
        assert (await fresh.submit(canonical(v)))["result"] == "duplicate_dummy"
    else:
        assert s["dummy_review"]["statuses"]["indeterminate"] == 1
        with pytest.raises(ValueError):
            await fresh.submit(canonical(v))
    assert s["genuine_human"]["quality_scores"] is None


@pytest.mark.integration
async def test_concurrent_submission_exclusive_claim_and_conflict(review):
    r, ctl = review
    v = rated((await r.blanks())[0])
    entered, release = asyncio.Event(), asyncio.Event()

    async def wait(query, db):
        if "INSERT INTO experiment_e10_reviews" in query:
            entered.set()
            await release.wait()

    ctl.before_execute = wait
    first = asyncio.create_task(r.submit(canonical(v)))
    await asyncio.wait_for(entered.wait(), 10)
    with pytest.raises(ValueError):
        await e.Review(r.auto).submit(canonical(v))
    release.set()
    await first
    ctl.before_execute = None
    changed = copy.deepcopy(v)
    changed["ratings"] = dict.fromkeys(e.DIMENSIONS, 1)
    with pytest.raises(ValueError, match="conflict"):
        await r.submit(canonical(changed))
    assert (await r.report())["dummy_review"]["statuses"]["rated_dummy"] == 1


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["packet", "source", "selection", "automated"])
async def test_changed_binding_never_accepts_reviews(review, fault, monkeypatch):
    from psycopg.types.json import Jsonb

    r, ctl = review
    v = rated((await r.blanks())[0])
    if fault == "source":
        r.configuration["fingerprint"] = "0" * 64
    elif fault == "automated":
        async with await ctl.connect() as db:
            await db.execute("UPDATE experiment_e9_results SET result=NULL WHERE ordinal=1")
    else:
        bundle = await r.load()
        if fault == "packet":
            bundle["packet"]["content"]["pairs"][0]["preferences"]["days_per_week"] = 4
        else:
            bundle["selection"] = "0" * 64
        async with await ctl.connect() as db:
            await db.execute(
                "UPDATE experiment_e10_packet SET bundle=%s WHERE slot=1", (Jsonb(bundle),)
            )
    with pytest.raises(ValueError):
        await r.submit(canonical(v))
    async with await ctl.connect() as db:
        assert (await (await db.execute("SELECT count(*) FROM experiment_e10_reviews")).fetchone())[
            0
        ] == 0


@pytest.mark.integration
async def test_corrupt_judgment_is_indeterminate_and_not_replaced(review):
    from psycopg.types.json import Jsonb

    r, ctl = review
    v = rated((await r.blanks())[0])
    await r.submit(canonical(v))
    async with await ctl.connect() as db:
        await db.execute("UPDATE experiment_e10_reviews SET result=%s", (Jsonb({"partial": True}),))
    s = await r.report()
    assert s["dummy_review"]["statuses"]["indeterminate"] == 1
    assert s["dummy_review"]["dummy_only_means"] == dict.fromkeys(e.DIMENSIONS, None)
    with pytest.raises(ValueError):
        await r.submit(canonical(v))


@pytest.mark.integration
async def test_partial_file_cancellation_and_restart_are_read_only(review):
    r, ctl = review
    v = rated((await r.blanks())[0])
    ctl.point = "after"
    task = asyncio.create_task(r.submit(canonical(v)))
    await asyncio.wait_for(ctl.entered.wait(), 10)
    task.cancel()
    ctl.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    ctl.point = None
    code = """import asyncio,json,sys
from datetime import UTC,datetime
sys.path[:0]=['src']
import psycopg
from experiments.synthetic_collection import Collection,Issuer
from experiments.blinded_review import Review
from experiments import sealed_evaluation as metadata
from future_training.persistence.counted_spending import CountedSpendingLedger
# Independently enumerate PUBLIC paths once in this fresh child, as the parent
# fixture does. Every freeze still rehashes the actual file bytes on each call.
public_paths=metadata.public_sources()
metadata.public_sources=lambda:public_paths
async def connect():return await psycopg.AsyncConnection.connect(sys.argv[1])
async def main():
 r=Review(Collection(CountedSpendingLedger(connect=connect),Issuer(now=lambda:datetime.now(UTC))))
 v=await r.report()
 print(json.dumps({'statuses':v['dummy_review']['statuses'],'genuine':v['genuine_human']}))
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(main())
"""
    p = await asyncio.to_thread(
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
    s = json.loads(p.stdout)
    assert s["statuses"]["indeterminate"] == 1 and s["genuine"]["quality_scores"] is None
    with pytest.raises(ValueError):
        await e.Review(r.auto).submit(canonical(v))


@pytest.mark.integration
async def test_partial_fence_and_failed_audit_never_infer_acceptance(review, monkeypatch):
    r, ctl = review
    v = rated((await r.blanks())[0])
    b = await r.load()
    ordinal = b["mapping"][v["pair_id"]]
    path = r.path(f"review-{ordinal:02}-{v['label']}-{v['reviewer']}.claim")
    path.write_bytes(b'{"partial":')
    with pytest.raises(ValueError):
        await r.submit(canonical(v))
    assert (await r.report())["dummy_review"]["statuses"]["indeterminate"] == 1

    async def fail(query, db):
        if "INSERT INTO experiment_e10_events" in query:
            raise OSError("PRIVATE_CANARY")

    ctl.before_execute = fail
    with pytest.raises(ValueError, match="review_audit_unavailable"):
        await r.submit(b"{}")
    ctl.before_execute = None
    assert (await r.report())["dummy_review"]["valid_submissions"] == 0


@pytest.mark.integration
async def test_late_source_change_after_claim_wait_stays_pending(review, monkeypatch):
    r, ctl = review
    v = rated((await r.blanks())[0])
    ctl.point = "after"
    task = asyncio.create_task(r.submit(canonical(v)))
    await asyncio.wait_for(ctl.entered.wait(), 10)
    original = copy.deepcopy(r.configuration)
    r.configuration["fingerprint"] = "0" * 64
    ctl.release.set()
    with pytest.raises(ValueError):
        await task
    ctl.point = None
    r.configuration = original
    assert (await r.report())["dummy_review"]["statuses"]["indeterminate"] == 1


@pytest.mark.integration
async def test_output_directory_change_cannot_replace_first_review(review, tmp_path, monkeypatch):
    r, _ = review
    v = rated((await r.blanks())[0])
    await r.submit(canonical(v))
    monkeypatch.chdir(tmp_path)
    assert (await e.Review(r.auto).submit(canonical(v)))["result"] == "duplicate_dummy"


@pytest.mark.parametrize(
    "raw", [b"{}", b"null", b'{"version":1,"version":2}', b"\xff", b" " * 16385]
)
def test_malformed_review_is_finite_without_echo(raw, capsys):
    with pytest.raises(ValueError, match="^dummy_submission_invalid$"):
        e.parse(raw)
    assert not capsys.readouterr().out


def test_genuine_import_and_foreign_collection_denied():
    with pytest.raises(ValueError):
        e.import_genuine(approved=True)
    with pytest.raises(ValueError):
        e.Review(object())


@pytest.mark.integration
async def test_missing_automated_evidence_stays_missing_not_reviewable(rig):
    c, _, _ = rig
    r = e.Review(c)
    await r.initialize()
    packet = await r.issue()
    assert packet["content"]["pairs"] == [] and await r.blanks() == []
    s = await r.report()
    assert s["automated"]["completed_evaluations"] == 10  # Actual deterministic templates only.
    assert s["automated"]["missing_or_indeterminate"] == 10
    assert s["dummy_review"]["statuses"]["ineligible_pair"] == 40
    assert s["dummy_review"]["valid_submissions"] == 0
    assert s["genuine_human"]["quality_scores"] is None


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["lost_after", "rollback_uncertain", "open_uncertain"])
async def test_uncertain_packet_issue_is_not_a_new_packet_namespace(rig, mode):
    c, ctl, _ = rig
    r = e.Review(c)
    await r.initialize()
    ctl.mode = mode
    with pytest.raises(ValueError, match="uncertain"):
        await r.issue()
    ctl.mode = "normal"
    if mode == "lost_after":
        assert await r.issue() == await r.export()
    else:
        with pytest.raises(ValueError):
            await e.Review(c).issue()
        with pytest.raises(ValueError):
            await r.export()


@pytest.mark.integration
async def test_fsync_failure_keeps_import_fence_and_unknown_status(review, monkeypatch):
    r, _ = review
    v = rated((await r.blanks())[0])
    original = e.replay.cases.sealed.os.fsync

    def fail(*a):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(e.replay.cases.sealed.os, "fsync", fail)
    with pytest.raises(ValueError):
        await r.submit(canonical(v))
    monkeypatch.setattr(e.replay.cases.sealed.os, "fsync", original)
    assert (await r.report())["dummy_review"]["statuses"]["indeterminate"] == 1
    with pytest.raises(ValueError):
        await e.Review(r.auto).submit(canonical(v))
