"""Actual PG claims + installed loopback TLS; no live authority or provider traffic."""

import asyncio
import copy
import gzip
import json

import httpx
import pytest
from agent_doubles import make_agent
from local_tls_doubles import server, trusted
from responses_doubles import fixture, frames
from test_counted_spending_postgres import pair, rows
from test_counted_spending_postgres import rig as rig
from test_profile_postgres import pg_schema as pg_schema
from test_provider_tls import certs as certs
from test_token_admission import prepared

from future_training.identity import Principal
from future_training.persistence.counted_spending import CountedSpendingLedger
from future_training.persistence.spending import LedgerFault
from future_training.providers.counting import COMMON
from future_training.providers.http import LocalTLS
from future_training.providers.responses import ResponsesReplay
from future_training.providers.sender import ClaimedHTTP
from future_training.schemas import GenerateRequest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("repair", [False, True])
async def test_actual_agent_full_counted_tls_sequence_after_committed_claims(
    rig, profile, certs, repair
):
    ledger, controls, _ = rig
    seen = []
    native = [fixture("tool"), fixture()]
    if repair:
        invalid = copy.deepcopy(fixture())
        envelope = json.loads(invalid["output"][0]["content"][0]["text"])
        envelope["result"]["plan"]["days"][0]["blocks"][0]["exercise_id"] = "unknown_exercise"
        invalid["output"][0]["content"][0]["text"] = json.dumps(envelope)
        native = [fixture("tool"), invalid, fixture()]
    generations = 0

    async def capture(head, body):
        nonlocal generations
        kind = "count" if b"/input_tokens " in head.split(b"\r\n")[0] else "generation"
        async with await controls.connect() as c:
            record = await (
                await c.execute(
                    "SELECT state,wire_ordinal FROM spend_operations WHERE kind=%s "
                    "ORDER BY wire_ordinal DESC NULLS LAST LIMIT 1",
                    (kind,),
                )
            ).fetchone()
        assert record[0] == "sent" and record[1] == len(seen) + 1
        assert b"authorization:" not in head.lower()
        seen.append((kind, json.loads(body)))

    def reply(line):
        nonlocal generations
        if b"/input_tokens " in line:
            return b'{"object":"response.input_tokens","input_tokens":1000}', "application/json"
        value = native[generations]
        generations += 1
        return frames(value), "text/event-stream"

    async with server(certs["valid"], body=reply, on_request=capture) as (
        port,
        entered,
        closed,
        requests,
    ):
        provider = ResponsesReplay(
            LocalTLS(port, trusted(certs["valid"][0])),
            counted=True,
            ledger=ledger,
            scope=("project", "grant", "session"),
            count_ceiling_micro=1000,
        )
        agent = await make_agent(profile, provider=provider)
        async with agent.session(Principal.A, GenerateRequest(profile_revision=1)) as run:
            result = await run.execute()
            state = run.provider
            client = await state.http.client()
            assert await state.http.client() is client
        n = 3 if repair else 2
        assert result.output().outcome == "plan"
        assert (result.count_requests, result.metrics.provider_requests, result.wire_requests) == (
            n,
            n,
            2 * n,
        )
        assert result.metrics.semantic_repairs == int(repair)
        assert result.metrics.input_tokens == n * 1000 and result.metrics.output_tokens == n * 100
        assert state.closed and state.http.closed and client.is_closed
        assert not state.history and not state.pending and state._ticket is None
        assert len(requests) == 2 * n and agent.candidates.stats()["lineages"] == 0
    for index in range(0, len(seen), 2):
        assert seen[index][0] == "count" and seen[index + 1][0] == "generation"
        counted, generation = seen[index][1], seen[index + 1][1]
        assert counted == {k: generation[k] for k in sorted(COMMON)}
    saved = await rows(ledger)
    assert sum(r[3] for r in saved if r[1] == "count") == 1000 * n
    assert all(r[2] == "responded_held" and r[4] is None for r in saved if r[1] == "count")
    assert all(r[2] == "settled" and r[4] == 2770 for r in saved if r[1] == "generation")


@pytest.mark.parametrize(
    "mode,expected", [("lost_after", "sent"), ("rollback_uncertain", "reserved")]
)
async def test_unknown_claim_ack_has_no_http_and_no_refund(rig, profile, mode, expected):
    ledger, controls, clock = rig
    body = pair()
    await ledger.reserve_pair(body)
    controls.mode = mode
    wire = ClaimedHTTP(
        httpx.MockTransport(lambda r: pytest.fail("cannot send after uncertain commit")),
        ledger=ledger,
        scope=("project", "grant", "session"),
    )
    try:
        with pytest.raises(LedgerFault, match="reconciliation_pending"):
            async with wire.counted_stream(body, "count", prepared(profile), check=lambda: None):
                pass
        assert wire._client is None and wire.count_request_bytes == 0
        assert "project" in ledger._uncertain
        controls.mode = "normal"
        fresh = CountedSpendingLedger(connect=controls.connect, now=lambda: clock[0])
        assert (await rows(fresh))[0][2:4] == (expected, 1000)
        assert (await rows(ledger))[0][2:4] == (expected, 1000)
        await ledger.abandon_pair(body)
        assert (await rows(ledger))[0][2] == ("sent" if expected == "sent" else "not_sent")
    finally:
        controls.mode = "normal"
        await wire.aclose()


@pytest.mark.parametrize("stage", ["before_claim", "after_claim"])
async def test_shutdown_at_claim_boundary_without_socket_refund(rig, profile, stage):
    ledger, _, _ = rig
    body = pair()
    await ledger.reserve_pair(body)
    if stage == "before_claim":
        await ledger.stop("project")
    check_calls = 0

    def check():
        nonlocal check_calls
        check_calls += 1
        if stage == "after_claim" and check_calls == 2:
            raise asyncio.CancelledError

    wire = ClaimedHTTP(
        httpx.MockTransport(lambda r: pytest.fail("no transport allowed")),
        ledger=ledger,
        scope=("project", "grant", "session"),
    )
    try:
        with pytest.raises((LedgerFault, asyncio.CancelledError)):
            async with wire.counted_stream(body, "count", prepared(profile), check=check):
                pass
        await ledger.abandon_pair(body)
        assert (await rows(ledger))[0][2] == ("not_sent" if stage == "before_claim" else "sent")
        assert wire._client is None
    finally:
        await wire.aclose()


async def test_emergency_stop_cancels_awaits_actual_claimed_tls_socket(rig, profile, certs):
    ledger, _, _ = rig
    async with server(certs["valid"], mode="stall") as (port, entered, closed, requests):
        provider = ResponsesReplay(
            LocalTLS(port, trusted(certs["valid"][0])),
            counted=True,
            ledger=ledger,
            scope=("project", "grant", "session"),
            count_ceiling_micro=1000,
        )
        agent = await make_agent(profile, provider=provider)
        states = []

        async def run():
            async with agent.session(Principal.A, GenerateRequest(profile_revision=1)) as session:
                states.append(session.provider)
                return await session.execute()

        task = asyncio.create_task(run())
        await entered.wait()
        assert (await rows(ledger))[0][2] == "sent"
        await provider.stop()
        await provider.stop()
        with pytest.raises(asyncio.CancelledError):
            await task
        await closed.wait()
        assert len(requests) == 1 and not provider.supervisor._tasks
        state = states[0]
        assert state.closed and state.http.closed and not state.history and state._ticket is None
        assert [(r[1], r[2], r[3]) for r in await rows(ledger)] == [
            ("count", "sent", 1000),
            ("generation", "not_sent", 60000),
        ]


async def test_stop_during_claimed_generation_keeps_both_liabilities(rig, profile, certs):
    ledger, _, _ = rig
    generating = asyncio.Event()

    async def capture(head, body):
        if b"/input_tokens " not in head.split(b"\r\n")[0]:
            generating.set()

    def mode(line):
        return "ok" if b"/input_tokens " in line else "stall"

    body = b'{"object":"response.input_tokens","input_tokens":1000}'
    async with server(certs["valid"], mode=mode, body=body, on_request=capture) as (
        port,
        entered,
        closed,
        requests,
    ):
        provider = ResponsesReplay(
            LocalTLS(port, trusted(certs["valid"][0])),
            counted=True,
            ledger=ledger,
            scope=("project", "grant", "session"),
            count_ceiling_micro=1000,
        )
        agent = await make_agent(profile, provider=provider)
        task = asyncio.create_task(agent.generate(Principal.A, GenerateRequest(profile_revision=1)))
        await generating.wait()
        await provider.stop()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(requests) == 2 and not provider.supervisor._tasks
    assert [(r[1], r[2], r[3], r[4]) for r in await rows(ledger)] == [
        ("count", "responded_held", 1000, None),
        ("generation", "sent", 22500, None),
    ]


async def test_two_competing_senders_cannot_duplicate_one_sql_claim(rig, profile):
    ledger, controls, clock = rig
    other = CountedSpendingLedger(connect=controls.connect, now=lambda: clock[0])
    body = pair()
    await ledger.reserve_pair(body)
    barrier = asyncio.Barrier(2)
    sends = []

    def transport(request):
        sends.append(request.content)
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 1000})

    async def run(repository):
        wire = ClaimedHTTP(
            httpx.MockTransport(transport), ledger=repository, scope=("project", "grant", "session")
        )
        try:
            await barrier.wait()
            try:
                async with wire.counted_stream(
                    body, "count", prepared(profile), check=lambda: None
                ) as r:
                    await r.aread()
                return "sent"
            except LedgerFault:
                return "denied"
        finally:
            await wire.aclose()

    assert sorted(await asyncio.gather(run(ledger), run(other))) == ["denied", "sent"]
    assert len(sends) == 1 and (await rows(ledger))[0][2] == "sent"


async def test_exhausted_grant_cannot_reach_tls_connector(rig, profile):
    ledger, controls, _ = rig
    async with await controls.connect() as c:
        await c.execute("UPDATE spend_grants SET limit_micro=0")
    provider = ResponsesReplay(
        httpx.MockTransport(lambda r: pytest.fail("no send")),
        counted=True,
        ledger=ledger,
        scope=("project", "grant", "session"),
        count_ceiling_micro=1000,
    )
    agent = await make_agent(profile, provider=provider)
    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.output().outcome == "error" and result.wire_requests == 0
    assert await rows(ledger) == []


@pytest.mark.parametrize("fault", ["wrong_host", "redirect", "interrupt", "oversize", "gzip"])
async def test_real_tls_fault_keeps_claimed_count_and_never_retries(rig, profile, certs, fault):
    ledger, controls, clock = rig
    material = certs["wrong"] if fault == "wrong_host" else certs["valid"]
    body = (
        b"x" * 1025
        if fault == "oversize"
        else (gzip.compress(b"x" * 100000) if fault == "gzip" else b"{}")
    )
    headers = (
        {"Content-Encoding": "gzip"}
        if fault == "gzip"
        else ({"Location": "https://evil.invalid"} if fault == "redirect" else None)
    )
    async with server(
        material,
        mode=fault if fault in ("redirect", "interrupt") else "ok",
        body=body,
        headers=headers,
    ) as (port, entered, closed, requests):
        provider = ResponsesReplay(
            LocalTLS(port, trusted(material[0])),
            counted=True,
            ledger=ledger,
            scope=("project", "grant", "session"),
            count_ceiling_micro=1000,
        )
        agent = await make_agent(profile, provider=provider)
        result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
        assert result.output().outcome == "error"
        assert (result.count_requests, result.metrics.provider_requests, result.wire_requests) == (
            1,
            0,
            1,
        )
        assert result.metrics.transport_retries == 0
        assert len(requests) == (0 if fault == "wrong_host" else 1)
    fresh = CountedSpendingLedger(connect=controls.connect, now=lambda: clock[0])
    saved = await rows(fresh)
    assert [(r[1], r[2], r[3], r[4]) for r in saved] == [
        ("count", "sent", 1000, None),
        ("generation", "not_sent", 60000, None),
    ]
