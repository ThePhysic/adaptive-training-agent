"""F3-E6 public controls only: no genuine secrets, cases or human authorization."""

import asyncio
import copy
import hashlib
import hmac
import json
import os
import subprocess
import sys
from datetime import timedelta

import httpx
import pytest
import test_authority_postgres as authority_tests
from agent_doubles import ManualClock
from authority_doubles import NOW, spec
from local_tls_doubles import server, trusted
from responses_doubles import fixture, frames
from test_counted_probe_evidence import broken
from test_independent_cases import package as previous_package
from test_provider_tls import certs as certs
from test_token_admission import Backend

from experiments import opening_collection as e
from future_training.agent.protocol import canonical
from future_training.persistence.authority import AuthorityLedger
from future_training.providers.http import LocalTLS
from future_training.providers.probe import ResponsesProbe, SingleProbe

pg_schema, rig = authority_tests.pg_schema, authority_tests.rig


@pytest.fixture(scope="module")
def public_paths():
    return e.cases.sealed.public_sources()


@pytest.fixture
def preparation(monkeypatch, public_paths):
    # Transform only known public test controls, not any sealed population.
    old = previous_package.__wrapped__(monkeypatch, public_paths)
    f = e.freeze()
    fp = f["fingerprint"]
    originals, entries = [], []
    for ordinal, raw in enumerate(old[0], 1):
        value = json.loads(raw)
        value["freeze_sha256"] = fp
        body = e.cases.canonical_fixture(canonical(value))
        originals.append(body)
        entries.append(
            dict(
                ordinal=ordinal,
                content_commitment=e.cases.sealed.curator_token(
                    e.cases.TEST_KEY, fp, body, purpose="content"
                ),
                input_token=e.cases.sealed.curator_token(
                    e.cases.TEST_KEY,
                    fp,
                    e.cases.sealed.input_fingerprint(value["profile"], "").encode(),
                    purpose="input",
                ),
            )
        )
    m = json.loads(old[1])
    context = e.cases.sealed.curator_token(
        e.cases.TEST_KEY, fp, b"SYNTHETIC", purpose="key_context"
    )
    m.update(
        freeze_sha256=fp,
        key_context=context,
        entries=entries,
        content_root=e.cases.sealed.digest(entries),
    )
    exposure = json.loads(old[2])
    exposure.update(
        freeze_sha256=fp,
        key_context=context,
        tokens=[
            e.cases.sealed.curator_token(e.cases.TEST_KEY, fp, d.encode(), purpose="input")
            for d in e.cases.sealed.exposed_input_index()
        ],
    )
    pins = old[4].model_copy(
        update=dict(
            freeze_sha256=fp,
            key_context=context,
            content_root=m["content_root"],
            manifest_sha256=e.cases.sealed.digest(m),
            exposure_sha256=e.cases.sealed.digest(exposure),
        )
    )
    return e.Preparation(
        tuple(originals), canonical(m), canonical(pins.model_dump(mode="json")), canonical(f)
    )


@pytest.fixture
def simple():
    async def no_database():
        raise AssertionError("Pure opening tests must not access PostgreSQL")

    ledger = AuthorityLedger(spec(), connect=no_database, now=lambda: NOW)
    backend = Backend([])
    probe = SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(backend)))
    clock = [NOW]
    authority = e.SyntheticAuthority(now=lambda: clock[0])
    return probe, authority, clock, backend


def opened(preparation, probe, authority):
    receipt = authority.issue(preparation, probe)
    return e.open_simulation(preparation, receipt, authority, probe)


def test_original_bytes_remain_committed_and_separate_opening(preparation, simple):
    probe, authority, _, backend = simple
    before = preparation.original
    capability = opened(preparation, probe, authority)
    assert capability.original == before[0] and preparation.original == before
    assert json.loads(capability.original)["origin"]["state"] == "synthetic_fixture"
    body = json.loads(capability.receipt)["body"]
    assert body["mode"] == "synthetic_not_human_authorization" and body["ordinal"] == 1
    assert body["configuration"] == json.loads(preparation.configuration)["fingerprint"]
    assert not backend.paths
    for denied in (e.open_genuine, e.cases.open_independent, e.cases.sealed.open_population):
        with pytest.raises(ValueError):
            denied(approved=True)


@pytest.mark.parametrize(
    "fault",
    [
        "study",
        "configuration",
        "selection",
        "root",
        "case_id",
        "ordinal",
        "variant",
        "operation",
        "logical_execution",
        "financial_binding",
        "tag",
        "unsigned",
        "coherent_unissued",
    ],
)
def test_forged_receipts_are_not_authority(preparation, simple, fault, capsys, caplog):
    probe, authority, _, _ = simple
    raw = authority.issue(preparation, probe)
    value = json.loads(raw)
    if fault == "tag":
        value["tag"] = "0" * 64
    elif fault == "unsigned":
        value.pop("tag")
    elif fault == "ordinal":
        value["body"]["ordinal"] = True
    elif fault == "coherent_unissued":
        value["body"]["expires_at"] = (NOW + timedelta(minutes=20)).isoformat()
        value["tag"] = hmac.new(e.AUTH_KEY, canonical(value["body"]), hashlib.sha256).hexdigest()
    else:
        value["body"][fault] = "PRIVATE_CANARY"
    with pytest.raises(ValueError, match="^synthetic_opening_not_authorized$"):
        e.open_simulation(preparation, canonical(value), authority, probe)
    assert not capsys.readouterr().out and not caplog.text


def test_expired_receipt_or_wrong_issuer_cannot_open(preparation, simple):
    probe, authority, clock, _ = simple
    raw = authority.issue(preparation, probe)
    other = e.SyntheticAuthority(now=lambda: NOW)
    with pytest.raises(ValueError):
        e.open_simulation(preparation, raw, other, probe)
    clock[0] += timedelta(minutes=30)
    with pytest.raises(ValueError):
        e.open_simulation(preparation, raw, authority, probe)


@pytest.mark.parametrize(
    "fault",
    [
        "bytes",
        "input",
        "ordinal",
        "duplicate",
        "commitment",
        "root",
        "pins",
        "count",
        "source",
        "genuine",
    ],
)
def test_preparation_tampering_stops_before_execution(preparation, simple, fault):
    originals = list(preparation.original)
    m = json.loads(preparation.manifest)
    p = json.loads(preparation.pins)
    f = json.loads(preparation.configuration)
    if fault in ("bytes", "input", "ordinal", "genuine"):
        value = json.loads(originals[0])
        if fault == "bytes":
            originals[0] = json.dumps(value, indent=2).encode()
        elif fault == "input":
            value["profile"]["session_minutes"] = 30
            originals[0] = canonical(value)
        elif fault == "ordinal":
            value["ordinal"] = 2
            originals[0] = canonical(value)
        else:
            value["origin"]["kind"] = "independent_curator"
            originals[0] = canonical(value)
    elif fault == "duplicate":
        originals[1] = originals[0]
    elif fault == "commitment":
        m["entries"][0]["content_commitment"] = "0" * 64
    elif fault == "root":
        m["content_root"] = "0" * 64
    elif fault == "pins":
        p["exposure_sha256"] = "0" * 64
    elif fault == "count":
        originals.pop()
    else:
        f["files"][next(iter(f["files"]))] = "0" * 64
    bad = e.Preparation(tuple(originals), canonical(m), canonical(p), canonical(f))
    with pytest.raises(ValueError, match="synthetic_preparation_rejected"):
        e.verified(bad)
    assert not simple[3].paths


def test_new_freeze_captures_source_and_prior_candidates(preparation):
    f = json.loads(preparation.configuration)
    assert f == e.freeze() and f["version"] == "evaluation-configuration-freeze-v3"
    assert e.SPEC in f["files"] and "tests/test_opening_collection.py" in f["files"]
    assert not f["live_enabled"] and not f["monetary_authority"]
    path = e.ROOT / "docs/implementation/evidence/f3-e4-freeze-candidate.json"
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "b26c26e49a66055edf81ca5f33756669353d09c9189cd15991ad5e35b4d35502"
    )


async def setup(rig, preparation, values, *, count=1000, transport=None, clock=None):
    ledger, ctl, wall = rig
    await ledger.simulate()
    backend = Backend(values, count=count)
    probe = SingleProbe(
        ResponsesProbe(
            ledger, transport if transport is not None else httpx.MockTransport(backend)
        ),
        clock=clock,
    )
    authority = e.SyntheticAuthority(now=lambda: wall[0])
    capability = opened(preparation, probe, authority)
    collection = e.Collection(probe, authority)
    await collection.initialize()
    return collection, capability, backend


@pytest.mark.integration
@pytest.mark.parametrize("repair", [False, True])
@pytest.mark.parametrize("tls", [False, True])
async def test_complete_open_claim_count_execute_observe_score(
    rig, preparation, certs, repair, tls
):
    values = [fixture("tool"), *([broken()] if repair else []), fixture()]
    index = 0

    def reply(line):
        nonlocal index
        if b"input_tokens" in line:
            return b'{"object":"response.input_tokens","input_tokens":1000}', "application/json"
        value = values[index]
        index += 1
        return frames(value), "text/event-stream"

    async with server(certs["valid"], body=reply) as (port, *_):
        transport = LocalTLS(port, trusted(certs["valid"][0])) if tls else None
        c, cap, backend = await setup(rig, preparation, values, transport=transport)
        result = await c.run(cap)
        n = 3 if repair else 2
        assert result["evidence_complete"] and result["original_bytes_unchanged"]
        assert result["common_score"]["handling_passed"]
        assert result["common_score"]["hard_passed"] is not repair
        assert result["common_score"]["quality_scores"] is None
        counts = result["common_score"]["counts"]
        assert (counts["count_requests"], counts["provider_requests"], counts["wire_requests"]) == (
            n,
            n,
            2 * n,
        )
        assert result["packet"]["accounting"]["held_micro"] == n * 1000
        assert result["packet"]["accounting"]["known_charged_micro"] == n * 2770
        assert result["packet"]["accounting"]["actual_total_micro"] is None
        assert result["packet"]["tool_attempts"][0]["result_observed"]
        assert json.loads(cap.original)["origin"]["state"] == "synthetic_fixture"
        saved = await c.readback()
        assert saved["disposition"] == "recorded" and saved["result"] == result
        with pytest.raises(ValueError, match="already_attempted"):
            await c.run(cap)
        async with await rig[1].connect() as db:
            assert (
                await (
                    await db.execute("SELECT count(*) FROM probe_authorities WHERE state='active'")
                ).fetchone()
            )[0] == 0
            assert (await (await db.execute("SELECT count(*) FROM approved_plans")).fetchone())[
                0
            ] == 0
    # These are isolated native fixture observations, not live/human results.


@pytest.mark.integration
async def test_concurrent_and_changed_identity_attempts_cannot_replace_first(rig, preparation):
    c, cap, backend = await setup(rig, preparation, [fixture("tool"), fixture()])
    ctl = rig[1]
    entered, release = asyncio.Event(), asyncio.Event()

    async def before(query, db):
        if "INSERT INTO experiment_e6_first" in query:
            entered.set()
            await release.wait()

    ctl.before_execute = before
    first = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(entered.wait(), 5)
    second_probe = SingleProbe(ResponsesProbe(rig[0], httpx.MockTransport(Backend([]))))
    second = e.Collection(second_probe, c.authority)
    with pytest.raises(ValueError, match="outcome_uncertain"):
        await second.run(cap)
    release.set()
    await first
    ctl.before_execute = None
    assert len(backend.paths) == 4
    # Fresh receipt window and handle do not change the fixed durable slot.
    rig[2][0] += timedelta(minutes=1)
    cap2 = opened(preparation, second_probe, c.authority)
    with pytest.raises(ValueError):
        await e.Collection(second_probe, c.authority).run(cap2)
    assert (await c.readback())["result"]["common_score"]["hard_passed"]


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["lost_after", "rollback_uncertain", "open_uncertain"])
async def test_uncertain_initial_claim_never_releases_probe_or_allows_restart(
    rig, preparation, mode
):
    c, cap, backend = await setup(rig, preparation, [fixture()])
    ctl = rig[1]
    ctl.mode = mode
    with pytest.raises(ValueError, match="outcome_uncertain"):
        await c.run(cap)
    assert not backend.paths
    ctl.mode = "normal"
    before = await c.readback()
    assert before["outcome_uncertain"]
    probe = SingleProbe(ResponsesProbe(rig[0], httpx.MockTransport(Backend([]))))
    with pytest.raises(ValueError):
        await e.Collection(probe, c.authority).run(cap)
    assert (e.ROOT / ".cache/f3-e6/attempt-fences" / (c.schema + ".json")).is_file()


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["lost_after", "rollback_uncertain", "open_uncertain"])
async def test_uncertain_result_commit_retains_first_and_liability(rig, preparation, mode):
    c, cap, backend = await setup(rig, preparation, [fixture("tool"), fixture()])
    ctl = rig[1]

    async def after(query, db):
        if "UPDATE experiment_e6_first" in query:
            ctl.mode = mode

    ctl.after_execute = after
    with pytest.raises(ValueError, match="outcome_uncertain"):
        await c.run(cap)
    ctl.mode = "normal"
    ctl.after_execute = None
    state = await c.readback()
    assert len(backend.paths) == 4
    if mode == "lost_after":
        assert state["result"]["packet"]["accounting"]["held_micro"] == 2000
        assert state["result"]["packet"]["accounting"]["actual_total_micro"] is None
    else:
        assert state["disposition"] == "claimed_unknown"
    fresh = SingleProbe(ResponsesProbe(rig[0], httpx.MockTransport(Backend([]))))
    with pytest.raises(ValueError):
        await e.Collection(fresh, c.authority).run(cap)


@pytest.mark.integration
async def test_cancellation_preserves_actual_sent_count_and_drain(rig, preparation):
    entered, drained = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    c, cap, backend = await setup(rig, preparation, [], count=hang)
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(entered.wait(), 5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert drained.is_set() and len(backend.paths) == 1
    result = (await c.readback())["result"]
    assert result["outcome_uncertain"] and result["common_score"] is None
    assert result["packet"]["accounting"]["held_micro"] == 1000
    assert result["packet"]["accounting"]["actual_total_micro"] is None


@pytest.mark.integration
async def test_receipt_expiry_after_claim_wait_keeps_unknown_without_send(rig, preparation):
    c, cap, backend = await setup(rig, preparation, [fixture()])
    ctl = rig[1]
    ctl.point = "after"
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(ctl.entered.wait(), 5)
    rig[2][0] += timedelta(minutes=31)
    ctl.release.set()
    with pytest.raises(ValueError):
        await task
    ctl.point = None
    assert not backend.paths and (await c.readback())["disposition"] == "claimed_unknown"


@pytest.mark.integration
async def test_whole_deadline_includes_claim_work(rig, preparation):
    clock = ManualClock()
    c, cap, backend = await setup(rig, preparation, [fixture()], clock=clock)
    ctl = rig[1]
    ctl.point = "after"
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(ctl.entered.wait(), 5)
    clock.advance(30)
    ctl.release.set()
    with pytest.raises(ValueError):
        await task
    ctl.point = None
    assert not backend.paths and (await c.readback())["outcome_uncertain"]


@pytest.mark.integration
@pytest.mark.parametrize("kind", ["refusal", "write", "owner", "invalid"])
async def test_real_observed_safe_rejection_is_not_quality_success(rig, preparation, kind):
    value = copy.deepcopy(fixture("refusal" if kind == "refusal" else "tool"))
    if kind != "refusal":
        call = value["output"][-1]
        if kind == "write":
            call["name"] = "approve_plan"
        elif kind == "owner":
            call["arguments"] = '{"owner_id":"PRIVATE_CANARY"}'
        else:
            call["arguments"] = '{"limit":true}'
    c, cap, _ = await setup(rig, preparation, [value, fixture()])
    result = await c.run(cap)
    assert result["common_score"] is None or not result["common_score"]["quality_eligible"]
    if kind != "refusal":
        assert not result["packet"]["tool_attempts"][0]["arguments_valid"]


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["observations", "accounting", "drift"])
async def test_missing_actual_evidence_or_drift_cannot_default_pass(
    rig, preparation, monkeypatch, fault
):
    c, cap, _ = await setup(rig, preparation, [fixture("tool"), fixture()])
    if fault == "observations":
        monkeypatch.setattr(e._Recorder, "_response", lambda *a: None)
    elif fault == "accounting":

        async def unknown(_):
            raise OSError("PRIVATE_CANARY")

        monkeypatch.setattr(e.recorder, "accounting", unknown)
    else:
        original = e.collected

        def drift(*args):
            monkeypatch.setattr(e, "freeze", lambda: {"drift": True})
            return original(*args)

        monkeypatch.setattr(e, "collected", drift)
    result = await c.run(cap)
    assert not result["evidence_complete"] and result["common_score"] is None
    if fault == "accounting":
        assert result["packet"]["accounting"]["held_micro"] is None


@pytest.mark.integration
async def test_restart_after_claim_is_pending_and_never_reexecuted(rig, preparation):
    c, cap, backend = await setup(rig, preparation, [fixture()])
    ctl = rig[1]
    ctl.point = "after"
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(ctl.entered.wait(), 5)
    task.cancel()
    ctl.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    ctl.point = None
    assert not backend.paths
    # New OS process observes actual durable SQL state; it cannot clear/replay it.
    script = """import json,sys,psycopg
with psycopg.connect(sys.argv[1]) as c:
 row=c.execute('SELECT disposition FROM experiment_e6_first WHERE slot=1').fetchone()
 print(json.dumps({'disposition':row[0]}))
"""
    proc = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", script, ctl.dsn],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
        env={
            k: os.environ[k]
            for k in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP")
            if k in os.environ
        },
    )
    assert json.loads(proc.stdout) == {"disposition": "claimed_unknown"}
    fresh = SingleProbe(ResponsesProbe(rig[0], httpx.MockTransport(Backend([]))))
    with pytest.raises(ValueError):
        await e.Collection(fresh, c.authority).run(cap)


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["partial", "fsync"])
async def test_interrupted_fence_write_blocks_new_handle(rig, preparation, monkeypatch, fault):
    c, cap, backend = await setup(rig, preparation, [fixture()])
    original = e.cases.sealed.os.fsync
    if fault == "fsync":
        monkeypatch.setattr(
            e.cases.sealed.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY"))
        )
    else:
        original_open = e.cases.sealed.os.fdopen

        class Partial:
            def __init__(self, fd, mode):
                self.stream = original_open(fd, mode)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.stream.close()

            def write(self, body):
                self.stream.write(body[:7])
                self.stream.flush()
                raise OSError("PRIVATE_CANARY")

        monkeypatch.setattr(e.cases.sealed.os, "fdopen", Partial)
    with pytest.raises(ValueError):
        await c.run(cap)
    monkeypatch.setattr(e.cases.sealed.os, "fsync", original)
    if fault == "partial":
        monkeypatch.setattr(e.cases.sealed.os, "fdopen", original_open)
    assert not backend.paths
    with pytest.raises(ValueError):
        await e.Collection(c.probe, c.authority).run(cap)


@pytest.mark.integration
@pytest.mark.parametrize("fault", ["score", "boolean_type", "provenance", "observation"])
async def test_stored_contradictory_evidence_rejected(rig, preparation, fault):
    c, cap, _ = await setup(rig, preparation, [fixture("tool"), fixture()])
    value = await c.run(cap)
    if fault == "score":
        value["common_score"]["hard_passed"] = False
    elif fault == "boolean_type":
        value["common_score"]["hard_passed"] = 1
    elif fault == "provenance":
        value["provenance"] = "real_model"
    else:
        value["packet"]["observation"]["no_publication"] = False
    with pytest.raises(ValueError):
        e.validate_result(value)


@pytest.mark.integration
async def test_timeout_cancels_count_and_preserves_unknown_hold(rig, preparation):
    clock = ManualClock()
    entered, drained = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    c, cap, backend = await setup(rig, preparation, [], count=hang, clock=clock)
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(entered.wait(), 5)
    clock.advance(30)
    with pytest.raises(ValueError, match="outcome_uncertain"):
        await task
    assert drained.is_set() and len(backend.paths) == 1
    value = (await c.readback())["result"]
    assert value["common_score"] is None and value["packet"]["accounting"]["held_micro"] == 1000


@pytest.mark.integration
async def test_repeated_cancellation_awaits_owned_finalization(rig, preparation):
    entered, retaining, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    c, cap, _ = await setup(rig, preparation, [], count=hang)

    async def before(query, db):
        if "UPDATE experiment_e6_first" in query:
            retaining.set()
            await release.wait()

    rig[1].before_execute = before
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(entered.wait(), 5)
    task.cancel()
    await asyncio.wait_for(retaining.wait(), 5)
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert (await c.readback())["result"]["packet"]["accounting"]["held_micro"] == 1000


@pytest.mark.integration
async def test_shutdown_preserves_owned_result_and_no_replay(rig, preparation):
    entered = asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    c, cap, backend = await setup(rig, preparation, [], count=hang)
    task = asyncio.create_task(c.run(cap))
    await asyncio.wait_for(entered.wait(), 5)
    await c.probe.provider.supervisor.stop(ledger=rig[0], project=rig[0].spec.project)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(backend.paths) == 1
    result = (await c.readback())["result"]
    assert not result["evidence_complete"] and result["packet"]["accounting"]["disabled"]


@pytest.mark.integration
async def test_readback_rejects_different_financial_identity(rig, preparation):
    c, cap, _ = await setup(rig, preparation, [fixture("tool"), fixture()])
    await c.run(cap)
    other = AuthorityLedger(
        spec(project="different-synthetic-project"), connect=rig[1].connect, now=lambda: NOW
    )
    probe = SingleProbe(ResponsesProbe(other, httpx.MockTransport(Backend([]))))
    with pytest.raises(ValueError, match="binding_mismatch"):
        await e.Collection(probe, c.authority).readback()


@pytest.mark.integration
async def test_public_schema_rejected_before_any_experimental_ddl(rig, preparation):
    from approval_db_doubles import Controls

    from future_training.persistence.profiles import LOCAL_DSN

    ctl = Controls(LOCAL_DSN)
    queries = []

    async def before(query, db):
        queries.append(query)

    ctl.before_execute = before
    ledger = AuthorityLedger(spec(), connect=ctl.connect, now=lambda: NOW)
    probe = SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(Backend([]))))
    authority = e.SyntheticAuthority(now=lambda: NOW)
    with pytest.raises(ValueError, match="disposable_test_schema_required"):
        await e.Collection(probe, authority).initialize()
    assert not any("CREATE" in q for q in queries)


@pytest.mark.integration
async def test_alternate_working_directory_cannot_reset_claim(
    rig, preparation, monkeypatch, tmp_path
):
    c, cap, backend = await setup(rig, preparation, [fixture("tool"), fixture()])
    await c.run(cap)
    monkeypatch.chdir(tmp_path)
    fresh = SingleProbe(ResponsesProbe(rig[0], httpx.MockTransport(Backend([]))))
    with pytest.raises(ValueError):
        await e.Collection(fresh, c.authority).run(cap)
    assert len(backend.paths) == 4
