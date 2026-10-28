"""Native PostgreSQL evidence, not an in-memory accounting reference model."""

import asyncio
import os
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import psycopg
import pytest
from agent_doubles import make_agent
from approval_db_doubles import Controls
from responses_doubles import Script, fixture, frames
from test_approvals_postgres import wait_for_block
from test_profile_postgres import pg_schema as pg_schema

from future_training.identity import Principal
from future_training.persistence.spending import LedgerFault, Reservation, SpendingLedger
from future_training.providers.accounting import ActualUsage, cost_micro
from future_training.providers.responses import ResponsesReplay
from future_training.schemas import GenerateRequest

pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 24, 23, 59, 50, tzinfo=UTC)


@pytest.fixture
async def ledger_rig(pg_schema):
    controls = Controls(pg_schema[1])
    clock = [NOW]
    ledger = SpendingLedger(connect=controls.connect, now=lambda: clock[0])
    await ledger.create_replay_project("project", 1_000_000, 300_000)
    await ledger.grant("project", "grant", 800_000, NOW + timedelta(days=2))
    await ledger.session("project", "grant", "session", 200_000, NOW + timedelta(hours=2))
    try:
        yield ledger, controls, clock
    finally:
        await controls.settle_retained(commit=False)


def request(*, run=None, number=1, **changes):
    run = run or uuid4().hex
    return replace(
        Reservation(
            "project",
            "grant",
            "session",
            run,
            f"{run}-{number}",
            number,
            1000,
            2000,
        ),
        **changes,
    )


async def attempt_rows(ledger):
    return await ledger.reconcile("project")


async def test_empty_migration_replay_only_and_no_live_permit(ledger_rig):
    ledger, controls, _ = ledger_rig
    async with await controls.connect() as connection:
        assert await (
            await connection.execute("SELECT count(*) FROM spend_attempts")
        ).fetchone() == (0,)
        assert await (await connection.execute("SELECT mode FROM spend_projects")).fetchone() == (
            "replay",
        )
        with pytest.raises(psycopg.errors.CheckViolation):
            await connection.execute("UPDATE spend_projects SET mode='live'")


async def test_reserve_claim_settle_once_and_restart(ledger_rig):
    ledger, controls, clock = ledger_rig
    body = request()
    assert await ledger.reserve(body) == "reserved"
    await ledger.mark_sent(body)
    usage = ActualUsage.from_response(fixture()["usage"])
    assert await ledger.settle(body, usage) == cost_micro(usage) == 2770
    assert await ledger.settle(body, usage) == 2770
    restarted = SpendingLedger(connect=controls.connect, now=lambda: clock[0])
    assert await restarted.reserve(body) == "settled"
    assert await restarted.settle(body, usage) == 2770
    with pytest.raises(LedgerFault, match="settlement_conflict"):
        await restarted.settle(body, usage.model_copy(update={"output_tokens": 99}))
    with pytest.raises(LedgerFault, match="attempt_already_claimed"):
        await restarted.mark_sent(body)
    assert len(await attempt_rows(ledger)) == 1


@pytest.mark.parametrize("dimension", ["project", "day", "grant", "session"])
async def test_atomic_limits_under_concurrent_reservations(ledger_rig, dimension):
    ledger, controls, _ = ledger_rig
    update = {
        "project": "UPDATE spend_projects SET limit_micro=22500",
        "day": "UPDATE spend_projects SET day_limit_micro=22500",
        "grant": "UPDATE spend_grants SET limit_micro=22500",
        "session": "UPDATE spend_sessions SET limit_micro=22500",
    }[dimension]
    async with await controls.connect() as connection:
        await connection.execute(update)
    barrier = asyncio.Barrier(3)

    async def reserve():
        await barrier.wait()
        try:
            return await ledger.reserve(request())
        except LedgerFault as exc:
            return exc.reason

    tasks = [asyncio.create_task(reserve()) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    assert sorted(results) == ["reserved", "spend_exhausted", "spend_exhausted"]
    assert len(await attempt_rows(ledger)) == 1


async def test_real_row_lock_wait_and_same_attempt_unique_binding(ledger_rig):
    ledger, controls, _ = ledger_rig
    body = request()
    controls.point = "before"
    first = asyncio.create_task(ledger.reserve(body))
    await controls.entered.wait()
    other_controls = Controls(controls.dsn)
    second_started = asyncio.Event()

    async def before(query, connection):
        if "FOR UPDATE" in query:
            second_started.set()

    other_controls.before_execute = before
    second_ledger = SpendingLedger(connect=other_controls.connect, now=lambda: NOW)
    second = asyncio.create_task(second_ledger.reserve(body))
    await second_started.wait()
    await wait_for_block(controls.dsn, other_controls.pids[-1])
    assert not second.done()
    controls.release.set()
    assert await first == await second == "reserved"
    with pytest.raises(LedgerFault, match="attempt_conflict"):
        await ledger.reserve(replace(body, output_cap=1))
    assert len(await attempt_rows(ledger)) == 1


@pytest.mark.parametrize("mode,committed", [("lost_after", True), ("rollback_uncertain", False)])
async def test_reservation_ambiguous_commit_and_authoritative_reconciliation(
    ledger_rig, mode, committed
):
    ledger, controls, _ = ledger_rig
    body = request()
    controls.mode = mode
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.reserve(body)
    controls.mode = "normal"
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.mark_sent(body)
    rows = await ledger.reconcile("project")
    assert bool(rows) == committed
    assert await ledger.reserve(body) == "reserved"
    await ledger.mark_sent(body)
    with pytest.raises(LedgerFault, match="attempt_already_claimed"):
        await ledger.mark_sent(body)


@pytest.mark.parametrize("commit", [True, False])
async def test_inflight_commit_reconcile_waits_for_actual_transaction(ledger_rig, commit):
    ledger, controls, _ = ledger_rig
    body = request()
    controls.mode = "open_uncertain"
    with pytest.raises(LedgerFault):
        await ledger.reserve(body)
    controls.mode = "normal"
    new_controls = Controls(controls.dsn)
    entered = asyncio.Event()

    async def before(query, connection):
        if "FOR UPDATE" in query:
            entered.set()

    new_controls.before_execute = before
    restarted = SpendingLedger(connect=new_controls.connect, now=lambda: NOW)
    reconciliation = asyncio.create_task(restarted.reconcile("project"))
    await entered.wait()
    await wait_for_block(controls.dsn, new_controls.pids[-1])
    assert not reconciliation.done()
    await controls.settle_retained(commit=commit)
    assert bool(await reconciliation) == commit


async def test_repeated_cancellation_drains_owned_reservation_commit(ledger_rig):
    ledger, controls, _ = ledger_rig
    body = request()
    controls.point = "before"
    task = asyncio.create_task(ledger.reserve(body))
    await controls.entered.wait()
    task.cancel()
    task.cancel()
    controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    rows = await attempt_rows(ledger)
    assert len(rows) == 1 and rows[0][1] == "reserved"
    await ledger.release_unsent(body)
    assert (await attempt_rows(ledger))[0][1] == "not_sent"


async def test_lost_sent_claim_acknowledgement_never_resends(ledger_rig):
    ledger, controls, _ = ledger_rig
    body = request()
    await ledger.reserve(body)
    controls.mode = "lost_after"
    with pytest.raises(LedgerFault):
        await ledger.mark_sent(body)
    controls.mode = "normal"
    rows = await ledger.reconcile("project")
    assert rows[0][1:3] == ("sent", 22500)
    with pytest.raises(LedgerFault, match="attempt_already_claimed"):
        await ledger.mark_sent(body)
    with pytest.raises(LedgerFault, match="cannot_release_sent"):
        await ledger.release_unsent(body)
    with pytest.raises(LedgerFault, match="run_reconciliation_pending"):
        await ledger.reserve(request(run=body.run, number=2))


async def test_lost_settlement_ack_retries_exactly_once(ledger_rig):
    ledger, controls, _ = ledger_rig
    body = request()
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    usage = ActualUsage.from_response(fixture()["usage"])
    controls.mode = "lost_after"
    with pytest.raises(LedgerFault):
        await ledger.settle(body, usage)
    controls.mode = "normal"
    await ledger.reconcile("project")
    assert await ledger.settle(body, usage) == 2770
    assert len(await attempt_rows(ledger)) == 1


async def test_midnight_rechecks_daily_allowance_before_claim(ledger_rig):
    ledger, controls, clock = ledger_rig
    first, other = request(), request()
    async with await controls.connect() as connection:
        await connection.execute("UPDATE spend_projects SET day_limit_micro=22500")
    await ledger.reserve(first)
    clock[0] += timedelta(seconds=20)
    await ledger.reserve(other)  # New day has capacity; first remains charged to old day.
    with pytest.raises(LedgerFault, match="spend_exhausted"):
        await ledger.mark_sent(first)  # Rebase cannot evade the new day's reservation.
    await ledger.release_unsent(other)
    await ledger.mark_sent(first)
    assert sum(row[2] for row in await attempt_rows(ledger) if row[1] == "sent") == 22500


async def test_expired_session_new_session_and_unknown_not_freed(ledger_rig):
    ledger, controls, clock = ledger_rig
    body = request()
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    clock[0] += timedelta(hours=3)
    with pytest.raises(LedgerFault, match="permit_expired_or_missing"):
        await ledger.reserve(request())
    await ledger.session("project", "grant", "newsession", 200_000, clock[0] + timedelta(hours=1))
    await ledger.reserve(request(session="newsession"))
    restarted = SpendingLedger(connect=controls.connect, now=lambda: clock[0])
    rows = await restarted.reconcile("project")
    assert any(row[1:3] == ("sent", 22500) for row in rows)
    with pytest.raises(LedgerFault, match="cannot_release_sent"):
        await restarted.release_unsent(body)


@pytest.mark.parametrize(
    "change",
    [{"model": "unapproved"}, {"tier": "ultrafast"}, {"tokens": True}, {"long_cache": True}],
)
async def test_unexpected_pricing_or_usage_freezes_persistently(ledger_rig, change):
    ledger, controls, clock = ledger_rig
    body = request()
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    usage = ActualUsage(
        input_tokens=1001 if change.get("tokens") else 1000,
        output_tokens=100,
        write_12h_tokens=1 if change.get("long_cache") else 0,
    )
    kwargs = {k: v for k, v in change.items() if k in ("model", "tier")}
    with pytest.raises(LedgerFault, match="pricing_or_usage_discrepancy"):
        await ledger.settle(body, usage, **kwargs)
    assert (await attempt_rows(ledger))[0][1:3] == ("sent", 22500)
    restarted = SpendingLedger(connect=controls.connect, now=lambda: clock[0])
    with pytest.raises(LedgerFault, match="spending_disabled"):
        await restarted.reserve(request())


async def test_attempt_and_token_allowances_remain_cumulative(ledger_rig):
    ledger, _, _ = ledger_rig
    body = request(input_bound=16000)
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    await ledger.settle(body, ActualUsage(input_tokens=16000, output_tokens=2000))
    with pytest.raises(LedgerFault, match="token_exhausted"):
        await ledger.reserve(request(run=body.run, number=2))
    with pytest.raises(ValueError):
        await ledger.reserve(request(number=4))


async def test_emergency_shutdown_blocks_reserved_attempt_send(ledger_rig):
    ledger, _, _ = ledger_rig
    body = request()
    await ledger.reserve(body)
    await ledger.stop("project")
    await ledger.stop("project")
    with pytest.raises(LedgerFault, match="spending_disabled"):
        await ledger.mark_sent(body)
    await ledger.release_unsent(body)


async def test_adapter_ledger_integration_and_missing_usage_retention(ledger_rig, profile):
    ledger, _, _ = ledger_rig
    value = fixture()
    value.pop("usage")
    script = Script([frames(value)])
    provider = ResponsesReplay(
        httpx.MockTransport(script), ledger=ledger, scope=("project", "grant", "session")
    )
    agent = await make_agent(profile, provider=provider)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error" and len(script.requests) == 1
    rows = await attempt_rows(ledger)
    assert len(rows) == 1 and rows[0][1:3] == ("sent", 35000)


async def test_adapter_success_reserves_before_http_and_settles(ledger_rig, profile):
    ledger, controls, _ = ledger_rig

    async def handler(request):
        rows = await ledger.reconcile("project")
        assert len(rows) == 1 and rows[0][1] == "sent"
        return fixture()

    script = Script([handler])
    provider = ResponsesReplay(
        httpx.MockTransport(script), ledger=ledger, scope=("project", "grant", "session")
    )
    agent = await make_agent(profile, provider=provider)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "plan", result.diagnostic
    assert (await attempt_rows(ledger))[0][1:] == ("settled", 35000, 2770)


async def test_reservation_failure_never_calls_transport(ledger_rig, profile):
    ledger, controls, _ = ledger_rig
    controls.mode = "rollback_uncertain"
    script = Script([fixture()])
    agent = await make_agent(
        profile,
        provider=ResponsesReplay(
            httpx.MockTransport(script),
            ledger=ledger,
            scope=("project", "grant", "session"),
        ),
    )
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error" and script.requests == []
    controls.mode = "normal"
    assert await attempt_rows(ledger) == []


async def test_actual_process_exit_retains_durable_unknown_claim(ledger_rig):
    ledger, controls, _ = ledger_rig
    code = """
import asyncio,os,sys
from datetime import UTC,datetime
import psycopg
from future_training.persistence.spending import SpendingLedger,Reservation
async def main():
    async def connect(): return await psycopg.AsyncConnection.connect(sys.argv[1])
    ledger=SpendingLedger(connect=connect,now=lambda:datetime(2026,10,24,23,59,50,tzinfo=UTC))
    request=Reservation('project','grant','session','crashed-run','crashed-attempt',1,1000,2000)
    await ledger.reserve(request)
    await ledger.mark_sent(request)
    os._exit(0)
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
    runner.run(main())
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src"
    process = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, controls.dsn],
        env=environment,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert process.returncode == 0, process.stderr.decode()
    restarted = SpendingLedger(connect=controls.connect, now=lambda: NOW)
    assert await restarted.reconcile("project") == [("crashed-attempt", "sent", 22500, None)]
    body = request(run="crashed-run", attempt="crashed-attempt")
    with pytest.raises(LedgerFault, match="cannot_release_sent"):
        await restarted.release_unsent(body)
    with pytest.raises(LedgerFault, match="run_reconciliation_pending"):
        await restarted.reserve(request(run="crashed-run", number=2))


@pytest.mark.parametrize("cancel", [False, True])
async def test_settlement_rollback_or_cancel_keeps_authoritative_state(ledger_rig, cancel):
    ledger, controls, _ = ledger_rig
    body = request()
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    usage = ActualUsage.from_response(fixture()["usage"])
    if cancel:
        controls.point = "before"
        task = asyncio.create_task(ledger.settle(body, usage))
        await controls.entered.wait()
        task.cancel()
        controls.release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert (await attempt_rows(ledger))[0][1:] == ("settled", 22500, 2770)
    else:
        controls.mode = "rollback_uncertain"
        with pytest.raises(LedgerFault):
            await ledger.settle(body, usage)
        controls.mode = "normal"
        assert (await attempt_rows(ledger))[0][1:] == ("sent", 22500, None)
        assert await ledger.settle(body, usage) == 2770


async def test_adapter_cancelled_after_send_claim_retains_reservation(ledger_rig, profile):
    ledger, _, _ = ledger_rig
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def hanging(request):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned.set()

    script = Script([hanging])
    agent = await make_agent(
        profile,
        provider=ResponsesReplay(
            httpx.MockTransport(script),
            ledger=ledger,
            scope=("project", "grant", "session"),
        ),
    )
    task = asyncio.create_task(agent.generate(Principal.A, GenerateRequest(profile_revision=1)))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cleaned.is_set() and len(script.requests) == 1
    assert (await attempt_rows(ledger))[0][1:] == ("sent", 35000, None)


async def test_database_unavailable_does_not_send_or_leak_driver_error(ledger_rig, profile):
    ledger, _, _ = ledger_rig

    async def unavailable():
        raise psycopg.OperationalError("synthetic-private-database-error")

    ledger.connect = unavailable
    script = Script([fixture()])
    agent = await make_agent(
        profile,
        provider=ResponsesReplay(
            httpx.MockTransport(script),
            ledger=ledger,
            scope=("project", "grant", "session"),
        ),
    )
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error" and not script.requests
    assert "synthetic-private" not in repr(result)


async def test_cancellation_wins_when_owned_commit_also_fails(ledger_rig):
    ledger, controls, _ = ledger_rig
    controls.point = "before"
    controls.mode = "rollback_uncertain"
    task = asyncio.create_task(ledger.reserve(request()))
    await controls.entered.wait()
    task.cancel()
    controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    controls.mode = "normal"
    assert await ledger.reconcile("project") == []


async def test_explicit_zero_unitemized_writes_settle_nonzero_actual_cost(ledger_rig):
    ledger, _, _ = ledger_rig
    body = request()
    await ledger.reserve(body)
    await ledger.mark_sent(body)
    raw = fixture()["usage"]
    raw["input_tokens_details"]["cache_write_tokens"] = 0
    raw["input_tokens_details"].pop("cache_write_tokens_details")
    usage = ActualUsage.from_response(raw)
    assert await ledger.settle(body, usage) == 2620
    assert (await ledger.reconcile("project"))[0][1:] == ("settled", 22500, 2620)
