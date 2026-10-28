"""Native isolated SQL and local protocol/TLS authority integration evidence."""

import asyncio
import copy
import json
import os
import subprocess
import sys
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from agent_doubles import ManualClock
from approval_db_doubles import Controls
from authority_doubles import NOW, spec
from local_tls_doubles import server, trusted
from responses_doubles import fixture, frames
from test_observability import console as console
from test_profile_postgres import pg_schema as pg_schema
from test_provider_tls import certs as certs
from test_token_admission import Backend

from future_training.agent.budget import AgentFault
from future_training.persistence.authority import AuthorityLedger, AuthorityPair
from future_training.persistence.spending import LedgerFault
from future_training.providers.accounting import ActualUsage
from future_training.providers.counting import COMMON
from future_training.providers.probe import ResponsesProbe, SingleProbe

pytestmark = pytest.mark.integration


@pytest.fixture
async def rig(pg_schema):
    ctl = Controls(pg_schema[1])
    clock = [NOW]
    ledger = AuthorityLedger(spec(), connect=ctl.connect, now=lambda: clock[0])
    try:
        yield ledger, ctl, clock
    finally:
        await ctl.settle_retained(commit=False)


def pair(s, **changes):
    data = dict(
        project=s.project,
        grant=s.grant,
        session=s.session,
        run="one-synthetic-request",
        pair=uuid4().hex,
        ordinal=1,
        input_ceiling=16000,
        output_cap=2000,
        count_ceiling_micro=s.count_bound.ceiling_micro,
    )
    data.update(changes)
    return AuthorityPair(**data)


async def rows(ledger):
    return await ledger.reconcile_mixed(ledger.spec.project)


async def test_prepared_and_simulation_are_separate_from_live_and_replay(rig):
    ledger, ctl, _ = rig
    assert await ledger.prepare() == "prepared"
    async with await ctl.connect() as c:
        assert (
            await (await c.execute("SELECT limit_micro FROM probe_spend_projects")).fetchone()
        ) == (0,)
        assert (await (await c.execute("SELECT count(*) FROM probe_spend_grants")).fetchone()) == (
            0,
        )
    with pytest.raises(LedgerFault, match="inactive"):
        await ledger.reserve_pair(pair(ledger.spec))
    assert await ledger.simulate() == "simulation"
    await ledger.reserve_pair(pair(ledger.spec))
    async with await ctl.connect() as c:
        assert await (await c.execute("SELECT state FROM probe_authorities")).fetchone() == (
            "simulation",
        )
        assert await (await c.execute("SELECT count(*) FROM spend_projects")).fetchone() == (0,)
        assert await (
            await c.execute("SELECT count(*) FROM probe_authorities WHERE state='active'")
        ).fetchone() == (0,)


@pytest.mark.parametrize("different", [False, True])
async def test_concurrent_issuance_is_idempotent_or_conflicts(rig, different):
    ledger, ctl, clock = rig
    other = AuthorityLedger(
        spec(operator="other-operator") if different else spec(),
        connect=ctl.connect,
        now=lambda: clock[0],
    )
    barrier = asyncio.Barrier(2)

    async def issue(repo):
        await barrier.wait()
        try:
            return await repo.prepare()
        except LedgerFault as exc:
            return exc.reason

    assert sorted(await asyncio.gather(issue(ledger), issue(other))) == (
        ["authority_conflict", "prepared"] if different else ["prepared", "prepared"]
    )
    async with await ctl.connect() as c:
        assert await (await c.execute("SELECT count(*) FROM probe_authorities")).fetchone() == (1,)


@pytest.mark.parametrize("mode,exists", [("lost_after", True), ("rollback_uncertain", False)])
async def test_unknown_issuance_commit_reconciles_before_reuse(rig, mode, exists):
    ledger, ctl, clock = rig
    ctl.mode = mode
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.prepare()
    assert ledger.spec.project in ledger._uncertain
    ctl.mode = "normal"
    assert await rows(ledger) == []
    async with await ctl.connect() as c:
        assert await (await c.execute("SELECT count(*) FROM probe_authorities")).fetchone() == (
            int(exists),
        )
    assert await ledger.prepare() == "prepared"


@pytest.mark.parametrize("dimension", ["project", "grant", "day", "session"])
async def test_each_exact_ceiling_is_enforced(rig, dimension):
    _, ctl, clock = rig
    s = spec(**{dimension + "_limit_micro": 61000})
    ledger = AuthorityLedger(s, connect=ctl.connect, now=lambda: clock[0])
    await ledger.simulate()
    body = pair(s)
    await ledger.reserve_pair(body)
    await ledger.claim(body, "count")
    await ledger.accept_count(body, 1000)
    await ledger.claim(body, "generation")
    # A valid settlement leaves enough for another reservation; both operation
    # types are accounted, not silently excluded from one financial dimension.
    from future_training.providers.accounting import ActualUsage

    await ledger.settle_generation(body, ActualUsage.from_response(fixture()["usage"]))
    with pytest.raises(LedgerFault, match="exhausted"):
        await ledger.reserve_pair(pair(s, ordinal=2, input_ceiling=15000))


@pytest.mark.parametrize("change", ["expired", "not_started", "revoked", "account", "assets"])
async def test_bad_authority_denies_reservation_and_preserves_cleanup(rig, change, monkeypatch):
    ledger, ctl, clock = rig
    original = ledger
    await ledger.simulate()
    body = pair(ledger.spec)
    await ledger.reserve_pair(body)
    if change == "expired":
        clock[0] += timedelta(hours=1)
    elif change == "not_started":
        clock[0] -= timedelta(seconds=1)
    elif change == "revoked":
        await ledger.revoke()
    elif change == "account":
        ledger = AuthorityLedger(
            spec(account="wrong-account"), connect=ctl.connect, now=lambda: clock[0]
        )
    else:
        from future_training.providers import authority

        monkeypatch.setattr(authority, "frozen_assets", lambda: "0" * 64)
    with pytest.raises(LedgerFault):
        await ledger.claim(body, "count")
    await original.abandon_pair(body)
    assert (await rows(original))[0][2] == "not_sent"


async def test_single_request_cannot_be_reset_by_new_run_ids_or_restart(rig, pg_schema):
    ledger, ctl, clock = rig
    await ledger.simulate()
    body = pair(ledger.spec)
    await ledger.reserve_pair(body)
    await ledger.claim(body, "count")
    await ledger.abandon_pair(body)
    fresh = AuthorityLedger(ledger.spec, connect=ctl.connect, now=lambda: clock[0])
    with pytest.raises(LedgerFault):
        await fresh.reserve_pair(pair(ledger.spec, run="other-run"))
    assert (await rows(fresh))[0][2:4] == ("sent", 1000)
    # Actual new interpreter, not another instance: retained claim and bound run.
    env = dict(os.environ, PYTHONPATH="src;tests" if os.name == "nt" else "src:tests")
    env["FATA_TEST_DSN"] = pg_schema[1]
    script = """import asyncio,os,psycopg
from authority_doubles import spec,NOW
from future_training.persistence.authority import AuthorityLedger
async def main():
 async def connect(): return await psycopg.AsyncConnection.connect(os.environ['FATA_TEST_DSN'])
 ledger=AuthorityLedger(spec(),connect=connect,now=lambda:NOW)
 rows=await ledger.reconcile_mixed(ledger.spec.project)
 assert rows[0][2]=='sent' and rows[0][3]==1000
 print('fresh-process retained claim')
asyncio.run(main(),loop_factory=asyncio.SelectorEventLoop)
"""
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("repair", [False, True])
async def test_actual_probe_assembly_mock_or_tls(rig, certs, repair):
    ledger, _, _ = rig
    await ledger.simulate()
    values = [fixture("tool"), fixture()]
    if repair:
        invalid = copy.deepcopy(fixture())
        envelope = json.loads(invalid["output"][0]["content"][0]["text"])
        envelope["result"]["plan"]["days"][0]["blocks"][0]["exercise_id"] = "unknown-exercise"
        invalid["output"][0]["content"][0]["text"] = json.dumps(envelope)
        values = [fixture("tool"), invalid, fixture()]
    payloads = []

    async def capture(head, body):
        payloads.append(json.loads(body))

    gen = 0

    def reply(line):
        nonlocal gen
        if b"input_tokens" in line:
            return b'{"object":"response.input_tokens","input_tokens":1000}', "application/json"
        value = values[gen]
        gen += 1
        return frames(value), "text/event-stream"

    async with server(certs["valid"], body=reply, on_request=capture) as (port, *_):
        connector = __import__("future_training.providers.http", fromlist=["LocalTLS"]).LocalTLS(
            port, trusted(certs["valid"][0])
        )
        provider = ResponsesProbe(ledger, connector)
        probe = SingleProbe(provider)
        result = await probe.run()
        assert result.output().outcome == "plan"
        assert result.evidence_source == "authority_fixture"
        n = 3 if repair else 2
        assert (result.count_requests, result.metrics.provider_requests, result.wire_requests) == (
            n,
            n,
            2 * n,
        )
        assert result.metrics.semantic_repairs == int(repair)
        with pytest.raises(AgentFault):
            await probe.run()
    for i in range(0, len(payloads), 2):
        assert payloads[i] == {k: payloads[i + 1][k] for k in sorted(COMMON)}
    saved = await rows(ledger)
    assert all(r[2] == "responded_held" for r in saved if r[1] == "count")
    assert all(r[2] == "settled" and r[4] == 2770 for r in saved if r[1] == "generation")


async def test_deadline_and_emergency_cleanup_on_new_assembly(rig):
    ledger, _, _ = rig
    await ledger.simulate()
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def hang(request):
        entered.set()
        try:
            await asyncio.Future()
        finally:
            cleaned.set()

    backend = Backend([], count=hang)
    provider = ResponsesProbe(ledger, httpx.MockTransport(backend))
    clock = ManualClock()
    task = asyncio.create_task(SingleProbe(provider, clock=clock).run())
    await entered.wait()
    clock.advance(30)
    result = await task
    assert result.output().error.code == "budget_exceeded" and cleaned.is_set()
    assert not provider.supervisor._tasks
    await provider.stop()
    await provider.stop()
    saved = await rows(ledger)
    assert saved[0][2] == "sent" and saved[1][2] == "not_sent"


async def test_repeated_cancel_during_issuance_drains_transaction(rig):
    ledger, ctl, clock = rig
    ctl.point = "after"
    task = asyncio.create_task(ledger.simulate())
    await ctl.entered.wait()
    task.cancel()
    task.cancel()
    assert not task.done()
    ctl.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    ctl.point = None
    fresh = await AuthorityLedger.load(
        ledger.spec.project, ledger.spec.account, connect=ctl.connect, now=lambda: clock[0]
    )
    assert fresh.spec == ledger.spec
    async with await ctl.connect() as c:
        assert await (await c.execute("SELECT count(*) FROM probe_spend_grants")).fetchone() == (1,)
        assert await (await c.execute("SELECT count(*) FROM probe_spend_sessions")).fetchone() == (
            1,
        )
        assert await (
            await c.execute("SELECT count(*) FROM probe_authorities WHERE state='active'")
        ).fetchone() == (0,)


async def test_failed_issuance_is_atomic_and_retry_requires_reconciliation(rig):
    import psycopg

    ledger, ctl, _ = rig

    async def fail(query, connection):
        if "INSERT INTO probe_authorities" in query:
            raise psycopg.OperationalError("synthetic failure")

    ctl.before_execute = fail
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.simulate()
    ctl.before_execute = None
    assert await rows(ledger) == []
    async with await ctl.connect() as c:
        assert await (await c.execute("SELECT count(*) FROM probe_authorities")).fetchone() == (0,)
        assert await (await c.execute("SELECT count(*) FROM probe_spend_grants")).fetchone() == (0,)
    assert await ledger.simulate() == "simulation"


async def test_ambiguous_claim_retains_liability_and_new_runtime_cannot_replay(rig):
    ledger, ctl, clock = rig
    await ledger.simulate()
    body = pair(ledger.spec)
    await ledger.reserve_pair(body)
    ctl.mode = "lost_after"
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.claim(body, "count")
    ctl.mode = "normal"
    fresh = await AuthorityLedger.load(
        ledger.spec.project, ledger.spec.account, connect=ctl.connect, now=lambda: clock[0]
    )
    assert (await rows(fresh))[0][2:4] == ("sent", 1000)
    with pytest.raises(LedgerFault):
        await fresh.claim(body, "count")
    await fresh.abandon_pair(body)
    assert (await rows(fresh))[0][2:4] == ("sent", 1000)


@pytest.mark.parametrize("field", ["limit_micro", "day_limit_micro"])
async def test_sql_limit_drift_cannot_enlarge_authority(rig, field):
    ledger, ctl, _ = rig
    await ledger.simulate()
    async with await ctl.connect() as c:
        await c.execute("UPDATE probe_spend_projects SET " + field + "=999999999")
    with pytest.raises(LedgerFault, match="authority_mismatch"):
        await ledger.reserve_pair(pair(ledger.spec))


async def test_private_load_and_discrepancy_reconciliation_survive_asset_change(rig, monkeypatch):
    ledger, ctl, clock = rig
    await ledger.simulate()
    body = pair(ledger.spec)
    await ledger.reserve_pair(body)
    await ledger.claim(body, "count")
    await ledger.accept_count(body, 1000)
    await ledger.claim(body, "generation")
    usage = ActualUsage.from_response(fixture()["usage"]).model_copy(update={"input_tokens": 1001})
    with pytest.raises(LedgerFault, match="discrepancy"):
        await ledger.settle_generation(body, usage)
    from future_training.providers import authority

    monkeypatch.setattr(authority, "frozen_assets", lambda: "0" * 64)
    fresh = await AuthorityLedger.load(
        ledger.spec.project, ledger.spec.account, connect=ctl.connect, now=lambda: clock[0]
    )
    assert (await rows(fresh))[1][2:4] == ("sent", 22500)
    async with await ctl.connect() as c:
        assert await (await c.execute("SELECT frozen FROM probe_spend_projects")).fetchone() == (
            True,
        )
        assert await (
            await c.execute("SELECT count(*) FROM probe_spend_observations")
        ).fetchone() == (1,)
    with pytest.raises(LedgerFault):
        await AuthorityLedger.load(ledger.spec.project, "wrong-account", connect=ctl.connect)


@pytest.mark.parametrize("mutation", ["body", "endpoint", "reuse", "restart", "expired"])
async def test_one_shot_acknowledged_send_proof_is_exact_and_transient(rig, mutation):
    from future_training.providers.counting import COUNT_ENDPOINT
    from future_training.providers.gates import ENDPOINT

    ledger, ctl, clock = rig
    await ledger.simulate()
    body = pair(ledger.spec)
    await ledger.reserve_pair(body)
    await ledger.claim(body, "count")
    if mutation == "expired":
        clock[0] += timedelta(hours=1)
        with pytest.raises(LedgerFault):
            ledger.authorize_send(body, "count", b"{}")
        return
    proof = ledger.authorize_send(body, "count", b"{}")
    if mutation == "restart":
        fresh = await AuthorityLedger.load(
            ledger.spec.project, ledger.spec.account, connect=ctl.connect, now=lambda: clock[0]
        )
        with pytest.raises(LedgerFault):
            fresh.consume_send(proof, "POST", COUNT_ENDPOINT, b"{}")
    elif mutation == "reuse":
        ledger.consume_send(proof, "POST", COUNT_ENDPOINT, b"{}")
        with pytest.raises(LedgerFault):
            ledger.consume_send(proof, "POST", COUNT_ENDPOINT, b"{}")
    else:
        with pytest.raises(LedgerFault):
            ledger.consume_send(
                proof,
                "POST",
                ENDPOINT if mutation == "endpoint" else COUNT_ENDPOINT,
                b"changed" if mutation == "body" else b"{}",
            )
    assert (await rows(ledger))[0][2:4] == ("sent", 1000)


@pytest.mark.parametrize("limit", ["attempts", "input", "output"])
async def test_original_whole_request_limits_in_new_assembly(rig, limit):
    ledger, _, _ = rig
    await ledger.simulate()
    values = []
    for i in range(3):
        value = copy.deepcopy(fixture("tool"))
        value["output"][-1]["call_id"] = "synthetic-call-" + str(i)
        value["output"][-1]["id"] = "synthetic-item-" + str(i)
        value["output"][0]["id"] = "synthetic-reasoning-" + str(i)
        if limit == "input":
            value["usage"]["input_tokens"] = 16000
        if limit == "output":
            value["usage"]["output_tokens"] = 2000
        value["usage"]["total_tokens"] = (
            value["usage"]["input_tokens"] + value["usage"]["output_tokens"]
        )
        values.append(value)
    backend = Backend(values, count=16000 if limit == "input" else 1000)
    result = await SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(backend))).run()
    assert result.output().outcome == "error" and result.output().error.code == "budget_exceeded"
    n = {"attempts": 3, "input": 1, "output": 2}[limit]
    assert (result.count_requests, result.metrics.provider_requests, result.wire_requests) == (
        n,
        n,
        2 * n,
    )
    assert result.metrics.input_tokens <= 16000 and result.metrics.output_tokens <= 4000


async def test_private_binding_and_credentials_absent_from_both_sinks(rig, request, monkeypatch):
    from future_training.observability import LocalTracer, Span

    _, ctl, clock = rig
    sink = request.getfixturevalue("console")
    marker = "private-account-canary"
    secret = "sk-synthetic-authority-secret"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("FATA_PROVIDER", "live")
    s = spec(account=marker, project="private-project-canary", operator="private-operator-canary")
    ledger = AuthorityLedger(s, connect=ctl.connect, now=lambda: clock[0])
    await ledger.simulate()
    backend = Backend([fixture("tool"), fixture()])
    tracer = LocalTracer()
    with Span("agent.session", tracer=tracer, account=marker, credential=secret):
        result = await SingleProbe(ResponsesProbe(ledger, httpx.MockTransport(backend))).run()
    assert result.output().outcome == "plan" and result.evidence_source == "authority_fixture"
    rendered = str(tracer.snapshot()) + sink.getvalue() + repr(ledger) + repr(s)
    assert tracer.snapshot() and sink.getvalue()
    for value in (marker, secret, s.project, s.operator, "encrypted_content", "exercise_id"):
        assert value not in rendered
    assert any(
        r["attributes"].get("evidence_source") == "authority_fixture" for r in tracer.snapshot()
    )
