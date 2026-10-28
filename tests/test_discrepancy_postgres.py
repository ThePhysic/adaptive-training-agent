"""Native SQL: bounded observations and the original maximum holds commit together."""

import asyncio
import json
import os
import subprocess
import sys

import httpx
import psycopg
import pytest
from agent_doubles import make_agent
from approval_db_doubles import Controls
from responses_doubles import fixture
from test_approvals_postgres import wait_for_block
from test_counted_spending_postgres import NOW, USAGE, pair, ready, rows
from test_counted_spending_postgres import rig as rig
from test_observability import CANARIES
from test_profile_postgres import pg_schema as pg_schema
from test_token_admission import Backend

from future_training.identity import Principal
from future_training.persistence.counted_spending import CountedSpendingLedger
from future_training.persistence.spending import LedgerFault, SpendingLedger
from future_training.providers.responses import ResponsesReplay
from future_training.schemas import GenerateRequest

pytestmark = pytest.mark.integration


async def observations(controls):
    async with await controls.connect() as c:
        return await (
            await c.execute(
                "SELECT reason,model_class,tier_class,numbers FROM spend_observations "
                "ORDER BY operation_id"
            )
        ).fetchall()


async def sent(ledger):
    body = pair()
    await ready(ledger, body)
    await ledger.claim(body, "generation")
    return body


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("model", "model"),
        ("tier", "tier"),
        ("input", "usage_input"),
        ("output", "usage_output"),
        ("cache", "cache_ttl"),
    ],
)
async def test_atomic_freeze_observation_and_hold(rig, fault, reason):
    ledger, controls, clock = rig
    body = await sent(ledger)
    usage = USAGE
    kwargs = {}
    if fault in ("model", "tier"):
        kwargs[fault] = " ".join(CANARIES)
    if fault == "input":
        usage = usage.model_copy(update={"input_tokens": 1001})
    if fault == "output":
        usage = usage.model_copy(update={"output_tokens": 2001})
    if fault == "cache":
        usage = usage.model_copy(update={"write_12h_tokens": 1})
    for _ in range(2):
        with pytest.raises(LedgerFault, match="pricing_or_usage_discrepancy"):
            await ledger.settle_generation(body, usage, **kwargs)
    found = await observations(controls)
    assert len(found) == 1 and found[0][0] == reason
    assert found[0][3] == usage.model_dump()
    assert all(s not in json.dumps(found) for s in CANARIES)
    assert (await rows(ledger))[1][2:5] == ("sent", 22500, None)
    restarted = CountedSpendingLedger(connect=controls.connect, now=lambda: clock[0])
    with pytest.raises(LedgerFault, match="pricing_or_usage_discrepancy"):
        await restarted.settle_generation(
            body, USAGE
        )  # No corrected report refunds an observed fault.
    with pytest.raises(LedgerFault, match="spending_disabled"):
        await restarted.reserve_pair(pair())


@pytest.mark.parametrize("mode,committed", [("lost_after", True), ("rollback_uncertain", False)])
async def test_discrepancy_uncertain_commit_requires_authoritative_ordering(rig, mode, committed):
    ledger, controls, _ = rig
    body = await sent(ledger)
    controls.mode = mode
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.settle_generation(body, USAGE, model="unexpected")
    controls.mode = "normal"
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.reserve_pair(pair())
    await rows(ledger)
    assert len(await observations(controls)) == int(committed)
    assert (await rows(ledger))[1][2:5] == ("sent", 22500, None)
    with pytest.raises(LedgerFault, match="pricing_or_usage_discrepancy"):
        await ledger.settle_generation(body, USAGE, model="unexpected")
    assert len(await observations(controls)) == 1


async def test_write_failure_cannot_partially_commit_observation_or_refund(rig):
    ledger, controls, _ = rig
    body = await sent(ledger)

    async def fail(query, c):
        if "INSERT INTO spend_observations" in query:
            raise psycopg.OperationalError("synthetic secret failure")

    controls.before_execute = fail
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.settle_generation(body, USAGE, tier="unknown")
    controls.before_execute = None
    await rows(ledger)
    assert await observations(controls) == []
    assert (await rows(ledger))[1][2:5] == ("sent", 22500, None)
    with pytest.raises(LedgerFault):
        await ledger.settle_generation(body, USAGE, tier="unknown")
    assert len(await observations(controls)) == 1


async def test_changed_duplicate_does_not_overwrite_first_observation(rig):
    ledger, controls, _ = rig
    body = await sent(ledger)
    with pytest.raises(LedgerFault):
        await ledger.settle_generation(body, USAGE, model="unknown")
    before = await observations(controls)
    with pytest.raises(LedgerFault, match="observation_conflict"):
        await ledger.settle_generation(
            body, USAGE.model_copy(update={"output_tokens": 101}), model="unknown"
        )
    assert await observations(controls) == before


async def test_freeze_serializes_with_concurrent_new_reservation(rig):
    ledger, controls, _ = rig
    body = await sent(ledger)
    controls.point = "before"
    first = asyncio.create_task(ledger.settle_generation(body, USAGE, model="unknown"))
    await controls.entered.wait()
    other = Controls(controls.dsn)
    entered = asyncio.Event()

    async def before(query, c):
        if "FOR UPDATE" in query:
            entered.set()

    other.before_execute = before
    another = CountedSpendingLedger(connect=other.connect, now=lambda: NOW)
    second = asyncio.create_task(another.reserve_pair(pair()))
    await entered.wait()
    await wait_for_block(controls.dsn, other.pids[-1])
    assert not second.done()
    controls.release.set()
    with pytest.raises(LedgerFault):
        await first
    with pytest.raises(LedgerFault, match="spending_disabled"):
        await second
    assert len(await observations(controls)) == 1


@pytest.mark.parametrize("commit", [True, False])
async def test_inflight_discrepancy_commit_blocks_reconciliation(rig, commit):
    ledger, controls, _ = rig
    body = await sent(ledger)
    controls.mode = "open_uncertain"
    with pytest.raises(LedgerFault):
        await ledger.settle_generation(body, USAGE, model="unknown")
    controls.mode = "normal"
    other = Controls(controls.dsn)
    entered = asyncio.Event()

    async def before(query, c):
        if "FOR UPDATE" in query:
            entered.set()

    other.before_execute = before
    restarted = CountedSpendingLedger(connect=other.connect, now=lambda: NOW)
    task = asyncio.create_task(rows(restarted))
    await entered.wait()
    await wait_for_block(controls.dsn, other.pids[-1])
    await controls.settle_retained(commit=commit)
    assert (await task)[1][2:5] == ("sent", 22500, None)
    assert len(await observations(controls)) == int(commit)


async def test_cancel_during_discrepancy_commit_drains_and_persists(rig):
    ledger, controls, _ = rig
    body = await sent(ledger)
    controls.point = "before"
    task = asyncio.create_task(ledger.settle_generation(body, USAGE, tier="unknown"))
    await controls.entered.wait()
    task.cancel()
    task.cancel()
    controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(await observations(controls)) == 1
    assert (await rows(ledger))[1][2:5] == ("sent", 22500, None)


@pytest.mark.parametrize(
    "fault,reason",
    [("missing", "usage_missing"), ("cache", "cache_details"), ("invalid", "usage_invalid")],
)
async def test_adapter_persists_unpriced_numerical_usage_without_guessing(
    rig, profile, fault, reason
):
    ledger, controls, _ = rig
    value = fixture()
    if fault == "missing":
        value.pop("usage")
    elif fault == "cache":
        value["usage"]["input_tokens_details"].pop("cache_write_tokens_details")
    else:
        value["usage"]["output_tokens_details"]["reasoning_tokens"] = 101
    backend = Backend([value])
    provider = ResponsesReplay(
        httpx.MockTransport(backend),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    agent = await make_agent(profile, provider=provider)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error" and len(backend.paths) == 2
    found = await observations(controls)
    assert len(found) == 1 and found[0][0] == reason
    if fault != "missing":
        assert found[0][3]["input_tokens"] == 1000
    assert (await rows(ledger))[1][2:5] == ("sent", 22500, None)


async def test_restart_process_restores_discrepancy_evidence_and_freeze(rig):
    ledger, controls, _ = rig
    body = await sent(ledger)
    writer_code = """
import sys,asyncio,os
from datetime import datetime
import psycopg
from future_training.persistence.counted_spending import CountedSpendingLedger,PairReservation
from future_training.persistence.spending import LedgerFault
from future_training.providers.accounting import ActualUsage
async def run():
 async def connect():return await psycopg.AsyncConnection.connect(sys.argv[1])
 ledger=CountedSpendingLedger(connect=connect,now=lambda:datetime.fromisoformat(sys.argv[4]))
 pair=PairReservation("project","grant","session",sys.argv[2],sys.argv[3],1,16000,2000,1000)
 usage=ActualUsage(input_tokens=1000,output_tokens=100,cached_tokens=200,
                   write_30m_tokens=300,reasoning_tokens=20)
 try:await ledger.settle_generation(pair,usage,model="private model")
 except LedgerFault as exc:assert exc.reason=="pricing_or_usage_discrepancy"
 else:raise AssertionError("Missing discrepancy")
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(run())
os._exit(0)
"""
    writer = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", writer_code, controls.dsn, body.run, body.pair, NOW.isoformat()],
        capture_output=True,
        timeout=15,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert writer.returncode == 0, writer.stderr.decode()
    code = """
import sys,asyncio,json
import psycopg
async def run():
 c=await psycopg.AsyncConnection.connect(sys.argv[1])
 frozen=await (await c.execute("SELECT frozen FROM spend_projects")).fetchone()
 observed=await (await c.execute("SELECT reason,numbers FROM spend_observations")).fetchone()
 assert frozen==(True,) and observed[0]=="model" and observed[1]["input_tokens"]==1000
 await c.close()
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(run())
"""
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, controls.dsn],
        capture_output=True,
        timeout=15,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert result.returncode == 0, result.stderr.decode()


async def test_count_quote_discrepancy_retains_held_count(rig):
    ledger, controls, _ = rig
    body = pair()
    await ready(ledger, body)
    with pytest.raises(ValueError):
        await ledger.settle_count(body, 1001)
    assert (await observations(controls))[0][0] == "count_price"
    assert (await rows(ledger))[0][2:5] == ("responded_held", 1000, None)
    with pytest.raises(LedgerFault):
        await ledger.claim(body, "generation")


async def test_legacy_discrepancy_uses_same_observation_authority(rig):
    from test_spending_postgres import request

    _, controls, _ = rig
    ledger = SpendingLedger(connect=controls.connect, now=lambda: NOW)
    body = request()
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    with pytest.raises(LedgerFault):
        await ledger.settle(body, USAGE, model="private")
    assert (await observations(controls))[0][0] == "model"
    assert (await ledger.reconcile("project"))[0][1:3] == ("sent", 22500)


@pytest.mark.parametrize("stage", ["reserve", "claim", "generation_claim", "transport"])
async def test_emergency_stop_orders_disable_cancel_cleanup(rig, profile, stage):
    ledger, controls, _ = rig
    entered = asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    backend = Backend([hang] if stage == "transport" else [fixture()])
    provider = ResponsesReplay(
        httpx.MockTransport(backend),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    if stage != "transport":
        action = ledger.reserve_pair if stage == "reserve" else ledger.claim

        async def pause(*args):
            result = await action(*args)
            if stage == "generation_claim" and args[1] == "count":
                return result
            entered.set()
            await asyncio.Event().wait()
            return result

        if stage == "reserve":
            ledger.reserve_pair = pause
        else:
            ledger.claim = pause
    agent = await make_agent(profile, provider=provider)
    task = asyncio.create_task(agent.generate(Principal.A, GenerateRequest(profile_revision=1)))
    await entered.wait()
    await provider.stop()
    await provider.stop()
    assert task.cancelled() and not provider.supervisor._tasks and not ledger._tickets
    state = await rows(ledger)
    if stage == "reserve":
        assert all(r[2] == "not_sent" for r in state) and backend.paths == []
    if stage == "claim":
        assert state[0][2] == "sent" and backend.paths == []
    if stage == "generation_claim":
        assert state[0][2] == "responded_held" and state[1][2] == "sent" and len(backend.paths) == 1
    if stage == "transport":
        assert state[0][2] == "responded_held" and state[1][2] == "sent"


@pytest.mark.parametrize("different", [False, True])
async def test_concurrent_observations_are_single_and_immutable(rig, different):
    ledger, controls, _ = rig
    body = await sent(ledger)
    controls.point = "before"
    first = asyncio.create_task(ledger.settle_generation(body, USAGE, model="unknown"))
    await controls.entered.wait()
    other = Controls(controls.dsn)
    entered = asyncio.Event()

    async def before(query, c):
        if "FOR UPDATE" in query:
            entered.set()

    other.before_execute = before
    repository = CountedSpendingLedger(connect=other.connect, now=lambda: NOW)
    second = asyncio.create_task(
        repository.settle_generation(
            body,
            USAGE.model_copy(update={"output_tokens": 101 if different else 100}),
            model="unknown",
        )
    )
    await entered.wait()
    await wait_for_block(controls.dsn, other.pids[-1])
    controls.release.set()
    with pytest.raises(LedgerFault, match="pricing_or_usage_discrepancy"):
        await first
    with pytest.raises(
        LedgerFault, match="observation_conflict" if different else "pricing_or_usage_discrepancy"
    ):
        await second
    assert len(await observations(controls)) == 1


@pytest.mark.parametrize(
    "invalid",
    [
        {"input_tokens": -1},
        {"input_tokens": 0.5},
        {"input_tokens": 1000000001},
        {"input_tokens": "private"},
        {"prompt": 123},
    ],
)
async def test_observation_database_constraints_reject_unbounded_values(rig, invalid):
    from psycopg.types.json import Jsonb

    _, controls, _ = rig
    async with await controls.connect() as c:
        with pytest.raises(psycopg.errors.CheckViolation):
            await c.execute(
                "INSERT INTO spend_observations(project_id,source,operation_id,reason,"
                "model_class,tier_class,numbers,fingerprint) "
                "VALUES ('project','mixed','invalid','usage_invalid','expected','expected',%s,%s)",
                (Jsonb(invalid), "0" * 64),
            )


async def test_shutdown_cancellation_and_uncertain_disable_preserve_liability(rig, profile):
    ledger, controls, _ = rig
    entered = asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    provider = ResponsesReplay(
        httpx.MockTransport(Backend([], count=hang)),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    agent = await make_agent(profile, provider=provider)
    running = asyncio.create_task(agent.generate(Principal.A, GenerateRequest(profile_revision=1)))
    await entered.wait()
    controls.point = "before"
    controls.mode = "lost_after"
    stopping = asyncio.create_task(provider.stop())
    await controls.entered.wait()
    stopping.cancel()
    stopping.cancel()
    controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await stopping
    assert running.cancelled() and provider.supervisor.stopped and not provider.supervisor._tasks
    controls.mode = "normal"
    state = await rows(ledger)
    assert [(r[2], r[3]) for r in state] == [("sent", 1000), ("reserved", 60000)]
    async with await controls.connect() as c:
        assert await (await c.execute("SELECT disabled FROM spend_projects")).fetchone() == (True,)


async def test_real_tls_count_generation_respects_native_sql_claims(rig, profile, tmp_path):
    from local_tls_doubles import certificates, server, trusted
    from responses_doubles import frames
    from test_token_admission import prepared

    from future_training.providers.accounting import ActualUsage
    from future_training.providers.gates import ENDPOINT
    from future_training.providers.http import LocalTLS, OfflineHTTP
    from future_training.providers.responses import read_stream

    ledger, _, _ = rig
    body = pair()
    await ledger.reserve_pair(body)
    frozen = prepared(profile)

    def reply(line):
        if b"input_tokens" in line:
            return b'{"object":"response.input_tokens","input_tokens":1000}', "application/json"
        return frames(fixture()), "text/event-stream"

    materials = await asyncio.to_thread(certificates, tmp_path)
    async with server(materials["valid"], body=reply) as (port, entered, closed, requests):
        wire = OfflineHTTP(LocalTLS(port, trusted(materials["valid"][0])))
        try:
            await ledger.claim(body, "count")
            assert (await rows(ledger))[0][2] == "sent"
            async with wire.stream(
                ENDPOINT + "/input_tokens", frozen.counting, accept="application/json", maximum=1024
            ) as response:
                count = json.loads(await response.aread())["input_tokens"]
            await ledger.accept_count(body, count)
            await ledger.claim(body, "generation")
            assert (await rows(ledger))[1][2] == "sent"
            async with wire.stream(
                ENDPOINT, frozen.generation, accept="text/event-stream", maximum=65536
            ) as response:
                final = await read_stream(response)
            assert (
                await ledger.settle_generation(body, ActualUsage.from_response(final["usage"]))
                == 2770
            )
            assert len(requests) == 2 and (await rows(ledger))[0][2] == "responded_held"
        finally:
            await wire.aclose()
