"""Real PostgreSQL mixed-operation accounting and transport integration evidence."""

import asyncio
import os
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from agent_doubles import make_agent
from approval_db_doubles import Controls
from responses_doubles import fixture
from test_approvals_postgres import wait_for_block
from test_profile_postgres import pg_schema as pg_schema
from test_token_admission import Backend

from future_training.identity import Principal
from future_training.persistence.counted_spending import CountedSpendingLedger, PairReservation
from future_training.persistence.spending import LedgerFault, Reservation, SpendingLedger
from future_training.providers.accounting import ActualUsage
from future_training.providers.responses import ResponsesReplay
from future_training.schemas import GenerateRequest

pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 24, 23, 59, 50, tzinfo=UTC)
USAGE = ActualUsage.from_response(fixture()["usage"])


@pytest.fixture
async def rig(pg_schema):
    controls = Controls(pg_schema[1])
    clock = [NOW]
    ledger = CountedSpendingLedger(connect=controls.connect, now=lambda: clock[0])
    await ledger.create_replay_project("project", 1_000_000, 300_000)
    await ledger.grant("project", "grant", 800_000, NOW + timedelta(days=2))
    await ledger.session("project", "grant", "session", 200_000, NOW + timedelta(hours=2))
    try:
        yield ledger, controls, clock
    finally:
        await controls.settle_retained(commit=False)


def pair(**changes):
    return replace(
        PairReservation(
            "project", "grant", "session", uuid4().hex, uuid4().hex, 1, 16000, 2000, 1000
        ),
        **changes,
    )


async def ready(ledger, body):
    await ledger.reserve_pair(body)
    await ledger.claim(body, "count")
    await ledger.accept_count(body, 1000)


async def rows(ledger):
    return await ledger.reconcile_mixed("project")


async def test_pair_atomic_count_retains_cost_and_generation_settles_once(rig):
    ledger, controls, _ = rig
    body = pair()
    await ledger.reserve_pair(body)
    await ledger.reserve_pair(body)
    assert [(r[1], r[2], r[3]) for r in await rows(ledger)] == [
        ("count", "reserved", 1000),
        ("generation", "reserved", 60000),
    ]
    assert await ledger.claim(body, "count") == 1
    await ledger.accept_count(body, 1000)
    assert [(r[1], r[2], r[3]) for r in await rows(ledger)] == [
        ("count", "responded_held", 1000),
        ("generation", "reserved", 22500),
    ]
    assert await ledger.claim(body, "generation") == 2
    assert await ledger.settle_generation(body, USAGE) == 2770
    assert await ledger.settle_generation(body, USAGE) == 2770
    await ledger.abandon_pair(body)
    assert (await rows(ledger))[0][2:5] == ("responded_held", 1000, None)
    assert await ledger.settle_count(body, 250) == 250
    assert await ledger.settle_count(body, 250) == 250
    with pytest.raises(LedgerFault, match="settlement_conflict"):
        await ledger.settle_count(body, 251)
    with pytest.raises(ValueError):
        await ledger.settle_count(body, 1001)
    with pytest.raises(LedgerFault, match="settlement_conflict"):
        await ledger.settle_generation(body, USAGE.model_copy(update={"output_tokens": 99}))
    async with await controls.connect() as c:
        assert await (await c.execute("SELECT count(*) FROM spend_pairs")).fetchone() == (1,)
        assert await (await c.execute("SELECT mode FROM spend_projects")).fetchone() == ("replay",)


@pytest.mark.parametrize("dimension", ["project", "day", "grant", "session"])
async def test_concurrent_paired_reservations_respect_every_ceiling(rig, dimension):
    ledger, controls, _ = rig
    query = {
        "project": "UPDATE spend_projects SET limit_micro=61000",
        "day": "UPDATE spend_projects SET day_limit_micro=61000",
        "grant": "UPDATE spend_grants SET limit_micro=61000",
        "session": "UPDATE spend_sessions SET limit_micro=61000",
    }[dimension]
    async with await controls.connect() as c:
        await c.execute(query)
    barrier = asyncio.Barrier(3)

    async def reserve():
        await barrier.wait()
        try:
            await ledger.reserve_pair(pair())
            return "reserved"
        except LedgerFault as exc:
            return exc.reason

    assert sorted(await asyncio.gather(*(reserve() for _ in range(3)))) == [
        "reserved",
        "spend_exhausted",
        "spend_exhausted",
    ]
    assert len(await rows(ledger)) == 2


@pytest.mark.parametrize("legacy_first", [True, False])
async def test_legacy_and_mixed_liabilities_share_ceilings_and_run_ids(rig, legacy_first):
    ledger, controls, clock = rig
    old = SpendingLedger(connect=controls.connect, now=lambda: clock[0])
    new = pair()
    legacy = Reservation("project", "grant", "session", uuid4().hex, uuid4().hex, 1, 1000, 2000)
    async with await controls.connect() as c:
        await c.execute("UPDATE spend_projects SET limit_micro=61000")
    if legacy_first:
        await old.reserve(legacy)
        with pytest.raises(LedgerFault, match="run_protocol_conflict"):
            await ledger.reserve_pair(replace(new, run=legacy.run))
        with pytest.raises(LedgerFault, match="spend_exhausted"):
            await ledger.reserve_pair(new)
    else:
        await ledger.reserve_pair(new)
        with pytest.raises(LedgerFault, match="run_protocol_conflict"):
            await old.reserve(replace(legacy, run=new.run))
        with pytest.raises(LedgerFault, match="spend_exhausted"):
            await old.reserve(legacy)


async def test_matching_reservation_waits_for_real_project_lock(rig):
    ledger, controls, _ = rig
    body = pair()
    controls.point = "before"
    first = asyncio.create_task(ledger.reserve_pair(body))
    await controls.entered.wait()
    other = Controls(controls.dsn)
    entered = asyncio.Event()

    async def before(query, c):
        if "FOR UPDATE" in query:
            entered.set()

    other.before_execute = before
    second = asyncio.create_task(
        CountedSpendingLedger(connect=other.connect, now=lambda: NOW).reserve_pair(body)
    )
    await entered.wait()
    await wait_for_block(controls.dsn, other.pids[-1])
    assert not second.done()
    controls.release.set()
    await asyncio.gather(first, second)
    assert len(await rows(ledger)) == 2
    with pytest.raises(LedgerFault, match="pair_conflict"):
        await ledger.reserve_pair(replace(body, count_ceiling_micro=1001))


@pytest.mark.parametrize("mode,committed", [("lost_after", True), ("rollback_uncertain", False)])
async def test_paired_commit_is_atomic_and_requires_reconciliation(rig, mode, committed):
    ledger, controls, _ = rig
    body = pair()
    controls.mode = mode
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.reserve_pair(body)
    controls.mode = "normal"
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await ledger.claim(body, "count")
    assert len(await rows(ledger)) == (2 if committed else 0)
    await ledger.reserve_pair(body)
    assert len(await rows(ledger)) == 2


@pytest.mark.parametrize("commit", [True, False])
async def test_uncertain_inflight_transaction_orders_authoritative_read(rig, commit):
    ledger, controls, _ = rig
    controls.mode = "open_uncertain"
    with pytest.raises(LedgerFault):
        await ledger.reserve_pair(pair())
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
    assert not task.done()
    await controls.settle_retained(commit=commit)
    assert len(await task) == (2 if commit else 0)


@pytest.mark.parametrize("stage", ["count_claim", "accept", "generation_claim", "settlement"])
async def test_lost_acknowledgements_retain_claims_and_never_replay(rig, stage):
    ledger, controls, clock = rig
    body = pair()
    await ledger.reserve_pair(body)
    if stage != "count_claim":
        await ledger.claim(body, "count")
    if stage in ("generation_claim", "settlement"):
        await ledger.accept_count(body, 1000)
    if stage == "settlement":
        await ledger.claim(body, "generation")
    controls.mode = "lost_after"
    action = {
        "count_claim": lambda: ledger.claim(body, "count"),
        "accept": lambda: ledger.accept_count(body, 1000),
        "generation_claim": lambda: ledger.claim(body, "generation"),
        "settlement": lambda: ledger.settle_generation(body, USAGE),
    }[stage]
    with pytest.raises(LedgerFault, match="reconciliation_pending"):
        await action()
    controls.mode = "normal"
    state = await rows(ledger)
    assert state[0][2] == ("sent" if stage == "count_claim" else "responded_held")
    restarted = CountedSpendingLedger(connect=controls.connect, now=lambda: clock[0])
    with pytest.raises(LedgerFault, match="count_ticket_missing"):
        await restarted.claim(body, "generation")
    if stage == "settlement":
        assert await restarted.settle_generation(body, USAGE) == 2770
    elif stage == "accept":
        await restarted.accept_count(body, 1000)  # Durable result cannot remint a ticket.
        with pytest.raises(LedgerFault, match="count_ticket_missing"):
            await restarted.claim(body, "generation")
    await ledger.abandon_pair(body)
    assert (await rows(ledger))[0][3:5] == (1000, None)


@pytest.mark.parametrize("stage", ["reserve", "accept", "generation_claim"])
async def test_repeated_cancellation_drains_commit_without_reusable_ticket(rig, stage):
    ledger, controls, _ = rig
    body = pair()
    if stage != "reserve":
        await ledger.reserve_pair(body)
        await ledger.claim(body, "count")
    if stage == "generation_claim":
        await ledger.accept_count(body, 1000)
    controls.point = "before"
    action = {
        "reserve": lambda: ledger.reserve_pair(body),
        "accept": lambda: ledger.accept_count(body, 1000),
        "generation_claim": lambda: ledger.claim(body, "generation"),
    }[stage]
    task = asyncio.create_task(action())
    await controls.entered.wait()
    task.cancel()
    task.cancel()
    controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    await ledger.abandon_pair(body)
    state = await rows(ledger)
    assert len(state) == 2
    assert state[0][2] == ("not_sent" if stage == "reserve" else "responded_held")
    assert state[1][2] == ("sent" if stage == "generation_claim" else "not_sent")
    with pytest.raises(LedgerFault, match="count_ticket_missing"):
        await ledger.claim(body, "generation")


@pytest.mark.parametrize("change", ["shutdown", "session_expiry", "grant_expiry"])
async def test_shutdown_and_expiry_between_count_and_generation(rig, change):
    ledger, controls, clock = rig
    body = pair()
    await ready(ledger, body)
    if change == "shutdown":
        await ledger.stop("project")
    else:
        clock[0] += timedelta(hours=3) if change == "session_expiry" else timedelta(days=3)
    with pytest.raises(LedgerFault, match="spending_disabled|permit_expired_or_missing"):
        await ledger.claim(body, "generation")
    await ledger.abandon_pair(body)
    assert [(r[2], r[3]) for r in await rows(ledger)] == [
        ("responded_held", 1000),
        ("not_sent", 22500),
    ]


async def test_midnight_rebases_only_unsent_generation_and_checks_new_day(rig):
    ledger, controls, clock = rig
    body = pair()
    await ready(ledger, body)
    async with await controls.connect() as c:
        await c.execute("UPDATE spend_projects SET day_limit_micro=61000")
    clock[0] += timedelta(seconds=20)
    other = pair()
    await ledger.reserve_pair(other)  # Uses full new-day capacity.
    with pytest.raises(LedgerFault, match="spend_exhausted"):
        await ledger.claim(body, "generation")
    await ledger.abandon_pair(other)
    # Failed claim consumes the ephemeral ticket: no automatic retry.
    with pytest.raises(LedgerFault, match="count_ticket_missing"):
        await ledger.claim(body, "generation")
    another = pair()
    await ready(ledger, another)
    clock[0] += timedelta(days=1)
    # session expired, so extend a synthetic session explicitly for this boundary probe.
    async with await controls.connect() as c:
        await c.execute("UPDATE spend_sessions SET expires_at=%s", (NOW + timedelta(days=2),))
    await ledger.claim(another, "generation")
    async with await controls.connect() as c:
        dates = await (
            await c.execute(
                "SELECT kind,day FROM spend_operations WHERE pair_id=%s ORDER BY kind",
                (another.pair,),
            )
        ).fetchall()
    assert dates[0][1] != dates[1][1]


@pytest.mark.parametrize("fault", ["over", "under", "model", "tier", "output"])
async def test_usage_discrepancies_freeze_project_without_refund(rig, fault):
    ledger, controls, _ = rig
    body = pair()
    await ready(ledger, body)
    await ledger.claim(body, "generation")
    usage = USAGE
    kwargs = {}
    if fault in ("over", "under"):
        usage = usage.model_copy(update={"input_tokens": 1001 if fault == "over" else 999})
    elif fault == "output":
        usage = usage.model_copy(update={"output_tokens": 2001})
    else:
        kwargs[fault] = "unexpected"
    with pytest.raises(LedgerFault, match="pricing_or_usage_discrepancy"):
        await ledger.settle_generation(body, usage, **kwargs)
    assert (await rows(ledger))[1][2:5] == ("sent", 22500, None)
    async with await controls.connect() as c:
        assert await (await c.execute("SELECT frozen FROM spend_projects")).fetchone() == (True,)
    with pytest.raises(LedgerFault, match="spending_disabled"):
        await ledger.reserve_pair(pair())


async def test_process_exit_discards_ticket_but_preserves_held_liability(rig):
    ledger, controls, _ = rig
    body = pair()
    code = """
import asyncio,sys,os
from datetime import datetime
import psycopg
from future_training.persistence.counted_spending import CountedSpendingLedger,PairReservation
async def run():
 async def connect(): return await psycopg.AsyncConnection.connect(sys.argv[1])
 ledger=CountedSpendingLedger(connect=connect,now=lambda:datetime.fromisoformat(sys.argv[2]))
 p=PairReservation("project","grant","session",sys.argv[3],sys.argv[4],1,16000,2000,1000)
 await ledger.reserve_pair(p)
 await ledger.claim(p,"count")
 await ledger.accept_count(p,1000)
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
 runner.run(run())
os._exit(0)
"""
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, controls.dsn, NOW.isoformat(), body.run, body.pair],
        capture_output=True,
        timeout=15,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert result.returncode == 0, result.stderr.decode()
    assert [(r[2], r[3]) for r in await rows(ledger)] == [
        ("responded_held", 1000),
        ("reserved", 22500),
    ]
    await ledger.accept_count(body, 1000)
    with pytest.raises(LedgerFault, match="count_ticket_missing"):
        await ledger.claim(body, "generation")
    await ledger.abandon_pair(body)
    assert (await rows(ledger))[0][2] == "responded_held"


@pytest.mark.parametrize("repair", [False, True])
async def test_complete_agent_protocol_uses_native_paired_ledger(rig, profile, repair):
    ledger, _, _ = rig
    bad = fixture()
    bad["output"][0]["content"][0]["text"] = "{"
    backend = Backend([fixture("tool"), *([bad] if repair else []), fixture()])
    replay = ResponsesReplay(
        httpx.MockTransport(backend),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    agent = await make_agent(profile, provider=replay)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "plan", result.diagnostic
    n = 3 if repair else 2
    state = await rows(ledger)
    assert len(state) == result.wire_requests == n * 2
    assert sum(r[3] for r in state if r[1] == "count") == n * 1000
    assert all(r[2] == "responded_held" and r[4] is None for r in state if r[1] == "count")
    assert all(r[2] == "settled" and r[4] == 2770 for r in state if r[1] == "generation")
    assert sorted(r[6] for r in state) == list(range(1, n * 2 + 1))
    assert agent.candidates.stats()["lineages"] == 0


@pytest.mark.parametrize(
    "fault", ["count_connection", "malformed_count", "generation_connection", "missing_usage"]
)
async def test_real_ledger_retains_unknown_charges_and_releases_only_unsent(rig, profile, fault):
    ledger, _, _ = rig

    async def fail(request):
        raise httpx.ReadError("private-count-or-generation-error")

    value = fixture()
    if fault == "missing_usage":
        value.pop("usage")
    backend = Backend(
        [fail if fault == "generation_connection" else value],
        count=fail
        if fault == "count_connection"
        else (None if fault == "malformed_count" else 1000),
    )
    replay = ResponsesReplay(
        httpx.MockTransport(backend),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    agent = await make_agent(profile, provider=replay)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error"
    state = await rows(ledger)
    count_failed = fault in ("count_connection", "malformed_count")
    assert state[0][2:5] == ("sent" if count_failed else "responded_held", 1000, None)
    assert state[1][2] == ("not_sent" if count_failed else "sent")
    assert state[1][4] is None
    assert len(backend.paths) == (1 if count_failed else 2)
    assert not ledger._tickets and agent.candidates.stats()["lineages"] == 0


async def test_native_run_ordinals_and_inference_limits_cannot_reset(rig):
    ledger, _, _ = rig
    first = pair()
    await ledger.reserve_pair(first)
    await ledger.claim(first, "count")
    await ledger.accept_count(first, 16000)
    await ledger.claim(first, "generation")
    await ledger.settle_generation(first, USAGE.model_copy(update={"input_tokens": 16000}))
    with pytest.raises(LedgerFault, match="token_exhausted"):
        await ledger.reserve_pair(pair(run=first.run, ordinal=2, input_ceiling=1))
    with pytest.raises(LedgerFault, match="attempt_order"):
        await ledger.reserve_pair(pair(run=first.run, ordinal=3))
    with pytest.raises(ValueError):
        await ledger.reserve_pair(pair(ordinal=4))


async def test_cancellation_after_admission_releases_only_unsent_generation(rig, profile):
    ledger, _, _ = rig
    backend = Backend([fixture()])
    replay = ResponsesReplay(
        httpx.MockTransport(backend),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    entered = asyncio.Event()
    original = replay.for_request

    def for_request():
        session = original()
        admit = session.admit

        async def admitted(*args):
            await admit(*args)
            entered.set()
            await asyncio.Event().wait()

        session.admit = admitted
        return session

    replay.for_request = for_request
    agent = await make_agent(profile, provider=replay)
    task = asyncio.create_task(agent.generate(Principal.A, GenerateRequest(profile_revision=1)))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert [(r[2], r[3]) for r in await rows(ledger)] == [
        ("responded_held", 1000),
        ("not_sent", 22500),
    ]
    assert len(backend.paths) == 1 and not ledger._tickets
