import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import psycopg
import pytest
from psycopg import sql
from test_approvals_postgres import request as approval_request
from test_approvals_postgres import rig as rig
from test_approvals_postgres import wait_for_block
from test_profile_postgres import pg_schema as pg_schema

from future_training.api import create_app
from future_training.completion_contracts import SessionSubmission
from future_training.config import Settings
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.completions import PostgresCompletions
from future_training.persistence.plans import OwnedPlanReader
from future_training.schemas import ProfileSaveRequest

pytestmark = pytest.mark.integration


@pytest.fixture
async def submitted(rig):
    result = await rig.service.approve(Principal.A, approval_request(await rig.candidate()))
    reader = OwnedPlanReader(rig.database)
    saved = await reader.get(Principal.A, result.plan_id)
    backend = PostgresCompletions(connect=rig.controls.connect)
    body = SessionSubmission(
        expected_revision=0,
        plan_revision=result.candidate.revision,
        plan_content_hash=result.candidate.content_hash,
        status="completed",
        effort="moderate",
        rating=4,
        idempotency_key="session-key",
    )
    return rig, backend, saved, body


async def counts(rig):
    async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
        return await (
            await connection.execute(
                "SELECT (SELECT count(*) FROM session_records), "
                "(SELECT count(*) FROM session_idempotency)"
            )
        ).fetchone()


async def outcome(coroutine):
    try:
        return await coroutine
    except ServiceError as exc:
        return exc.code


async def test_submit_readback_versions_and_immutable_original_after_profile_change(
    submitted, profile
):
    rig, backend, saved, body = submitted
    pid = saved.approval.plan_id
    assert await backend.read(Principal.A, pid) == []
    result = await backend.submit(Principal.A, pid, 1, body)
    assert await counts(rig) == (1, 1)
    assert result.rating == 4 and result.status == "completed" and result.revision == 1
    assert await backend.read(Principal.A, pid, 1) == result
    assert await backend.read(Principal.A, pid) == [result]
    assert await backend.submit(Principal.A, pid, 1, body) == result
    await rig.profiles.save(
        Principal.A,
        ProfileSaveRequest(expected_revision=1, preferences={**profile, "session_minutes": 30}),
    )
    assert await backend.submit(Principal.A, pid, 1, body) == result
    assert await OwnedPlanReader(rig.database).get(Principal.A, pid) == saved
    assert (
        await outcome(backend.submit(Principal.A, pid, 1, body.model_copy(update={"rating": 5})))
        == "idempotency_mismatch"
    )
    assert (
        await outcome(
            backend.submit(
                Principal.A, pid, 1, body.model_copy(update={"idempotency_key": "new-key"})
            )
        )
        == "session_already_recorded"
    )
    assert await counts(rig) == (1, 1)


@pytest.mark.parametrize("status", ["completed", "partial", "skipped"])
async def test_optional_feedback_and_normalized_null_retry(submitted, status):
    rig, backend, saved, body = submitted
    body = body.model_copy(update={"status": status, "rating": None, "effort": None})
    result = await backend.submit(Principal.A, saved.approval.plan_id, 1, body)
    omitted = SessionSubmission.model_validate(body.model_dump(exclude={"rating", "effort"}))
    assert await backend.submit(Principal.A, saved.approval.plan_id, 1, omitted) == result
    assert result.status == status and result.rating is result.effort is None
    assert await counts(rig) == (1, 1)


async def test_ownership_and_real_session_references(submitted):
    rig, backend, saved, body = submitted
    pid = saved.approval.plan_id
    for actual in (pid, "absent"):
        assert await outcome(backend.submit(Principal.B, actual, 1, body)) == "not_found"
        assert await outcome(backend.read(Principal.B, actual)) == "not_found"
    assert await outcome(backend.submit(Principal.A, pid, 3, body)) == "invalid_request"
    assert await outcome(backend.read(Principal.A, pid, 3)) == "invalid_request"
    assert await outcome(backend.read(Principal.A, pid, 1)) == "not_found"
    for change in ({"plan_revision": 2}, {"plan_content_hash": "b" * 64}):
        assert (
            await outcome(backend.submit(Principal.A, pid, 1, body.model_copy(update=change)))
            == "plan_mismatch"
        )
    assert await counts(rig) == (0, 0)
    other = await rig.service.approve(
        Principal.B, approval_request(await rig.candidate(Principal.B))
    )
    other_body = body.model_copy(
        update={
            "plan_revision": other.candidate.revision,
            "plan_content_hash": other.candidate.content_hash,
        }
    )
    a = await backend.submit(Principal.A, pid, 1, body)
    b = await backend.submit(Principal.B, other.plan_id, 1, other_body)
    assert a.record_id != b.record_id and await counts(rig) == (2, 2)
    assert await outcome(backend.read(Principal.B, pid, 1)) == "not_found"


@pytest.mark.parametrize(
    "same_key,different_body,second_day",
    [
        (True, False, 1),
        (True, True, 1),
        (False, False, 1),
        (False, True, 1),
        (True, False, 2),
    ],
)
async def test_actual_postgres_concurrent_key_and_session_order(
    submitted, same_key, different_body, second_day
):
    rig, backend, saved, body = submitted
    rig.controls.point = "before"
    pid = saved.approval.plan_id
    first = asyncio.create_task(backend.submit(Principal.A, pid, 1, body))
    await rig.controls.entered.wait()
    second_seen = asyncio.Event()
    waiting = []

    async def before(query, connection):
        if (
            "pg_advisory_xact_lock" in query
            and connection.info.backend_pid != rig.controls.commit_pid
        ):
            waiting.append(connection.info.backend_pid)
            second_seen.set()

    rig.controls.before_execute = before
    altered = body.model_copy(
        update={
            "idempotency_key": body.idempotency_key if same_key else "key-two",
            "rating": 5 if different_body else 4,
        }
    )
    second = asyncio.create_task(outcome(backend.submit(Principal.A, pid, second_day, altered)))
    await second_seen.wait()
    await wait_for_block(rig.dsn, waiting[0])
    rig.controls.release.set()
    accepted = await first
    other = await second
    if same_key and not different_body and second_day == 1:
        assert other == accepted
    else:
        assert other == ("idempotency_mismatch" if same_key else "session_already_recorded")
    assert await counts(rig) == (1, 1)


async def test_rollback_between_record_and_key_and_safe_retry(submitted):
    rig, backend, saved, body = submitted

    async def fail(query, connection):
        if "INSERT INTO session_idempotency" in query:
            raise psycopg.OperationalError("synthetic-secret-do-not-log")

    rig.controls.before_execute = fail
    assert (
        await outcome(backend.submit(Principal.A, saved.approval.plan_id, 1, body))
        == "internal_error"
    )
    assert await counts(rig) == (0, 0)
    rig.controls.before_execute = None
    await backend.submit(Principal.A, saved.approval.plan_id, 1, body)
    assert await counts(rig) == (1, 1)


@pytest.mark.parametrize("commit_original", [True, False])
async def test_uncertain_commit_retry_waits_for_authoritative_original_transaction(
    submitted, commit_original
):
    rig, backend, saved, body = submitted
    rig.controls.mode = "open_uncertain"
    assert (
        await outcome(backend.submit(Principal.A, saved.approval.plan_id, 1, body))
        == "reconciliation_pending"
    )
    assert await counts(rig) == (0, 0)
    original = rig.controls.retained[0]
    original_id = (
        await (await original.execute("SELECT record_id FROM session_records")).fetchone()
    )[0]
    rig.controls.mode = "normal"
    waiting, seen = [], asyncio.Event()

    async def before(query, connection):
        if "pg_advisory_xact_lock" in query:
            waiting.append(connection.info.backend_pid)
            seen.set()

    rig.controls.before_execute = before
    retry = asyncio.create_task(backend.submit(Principal.A, saved.approval.plan_id, 1, body))
    await seen.wait()
    await wait_for_block(rig.dsn, waiting[0])
    assert not retry.done()
    await rig.controls.settle_retained(commit=commit_original)
    result = await retry
    assert (result.record_id == original_id) is commit_original
    assert await counts(rig) == (1, 1)


@pytest.mark.parametrize("point", ["before", "after"])
async def test_repeated_cancellation_does_not_detach_explicit_submit(submitted, point):
    rig, backend, saved, body = submitted
    rig.controls.point = point
    task = asyncio.create_task(backend.submit(Principal.A, saved.approval.plan_id, 1, body))
    await rig.controls.entered.wait()
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    assert await counts(rig) == ((0, 0) if point == "before" else (1, 1))
    rig.controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    result = await backend.submit(Principal.A, saved.approval.plan_id, 1, body)
    assert result.status == "completed" and await counts(rig) == (1, 1)


async def test_lost_commit_response_and_true_interpreter_restart(submitted):
    rig, backend, saved, body = submitted
    rig.controls.mode = "lost_after"
    assert (
        await outcome(backend.submit(Principal.A, saved.approval.plan_id, 1, body))
        == "reconciliation_pending"
    )
    assert await counts(rig) == (1, 1)
    rig.controls.mode = "normal"
    expected = await backend.read(Principal.A, saved.approval.plan_id, 1)
    code = """
import asyncio,json,sys
sys.path.insert(0,'src')
import psycopg
from future_training.completion_contracts import SessionSubmission
from future_training.persistence.completions import PostgresCompletions
from future_training.identity import Principal
async def main():
 async def connect():return await psycopg.AsyncConnection.connect(sys.argv[1])
 backend=PostgresCompletions(connect=connect)
 request=SessionSubmission.model_validate_json(sys.argv[3])
 result=await backend.submit(Principal.A,sys.argv[2],1,request)
 assert await backend.read(Principal.A,sys.argv[2],1)==result
 print(result.model_dump_json())
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(main())
"""
    child = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-c", code, rig.dsn, saved.approval.plan_id, body.model_dump_json()],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == expected.model_dump()
    assert await counts(rig) == (1, 1)


@pytest.mark.parametrize("table", ["session_records", "session_idempotency"])
@pytest.mark.parametrize("action", ["UPDATE", "DELETE", "TRUNCATE"])
async def test_sql_record_and_key_immutability(submitted, table, action):
    rig, backend, saved, body = submitted
    await backend.submit(Principal.A, saved.approval.plan_id, 1, body)
    query = {
        "UPDATE": "UPDATE {} SET owner_id=owner_id",
        "DELETE": "DELETE FROM {}",
        "TRUNCATE": "TRUNCATE {} CASCADE",
    }[action]
    with pytest.raises(psycopg.Error) as error:
        async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
            await connection.execute(sql.SQL(query).format(sql.Identifier(table)))
    assert error.value.sqlstate == "55000" and await counts(rig) == (1, 1)


@pytest.mark.parametrize("day", [2, 3])
async def test_database_itself_rejects_unbound_or_nonexistent_session(submitted, day):
    rig, backend, saved, body = submitted
    await backend.submit(Principal.A, saved.approval.plan_id, 1, body)
    with pytest.raises(psycopg.errors.CheckViolation):
        async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
            await connection.execute(
                "INSERT INTO session_records SELECT 'forged',owner_id,plan_id,%s,revision,"
                "plan_revision,plan_content_hash,status,effort,rating,submitted_at "
                "FROM session_records",
                (day,),
            )
    assert await counts(rig) == (1, 1)


async def test_actual_http_strict_submit_readback_and_owner_isolation(submitted):
    rig, backend, saved, body = submitted
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=rig.profiles,
        approvals=rig.database,
        completions=backend,
    )
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 12345))
    path = f"/api/v1/plans/{saved.approval.plan_id}/sessions/1/completion"
    headers = {"X-Synthetic-Principal": "synthetic-a"}
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as client:
        assert (await client.post(path, json=body.model_dump())).status_code == 401
        assert (await client.get(path, headers=headers)).status_code == 404
        for bad in (
            {"notes": "synthetic-pii-canary"},
            {"expected_revision": 1},
            {"rating": True},
            {"owner_id": "synthetic-b"},
        ):
            response = await client.post(path, json={**body.model_dump(), **bad}, headers=headers)
            assert response.status_code == 422 and "canary" not in response.text
        assert (await client.post(path, content=b"x" * 4097, headers=headers)).status_code == 413
        assert (
            await client.post(
                path,
                content='{"status":"completed","status":"skipped"}',
                headers={**headers, "Content-Type": "application/json"},
            )
        ).status_code == 422
        response = await client.post(path, json=body.model_dump(), headers=headers)
        assert response.status_code == 200
        assert (
            await client.post(path, json=body.model_dump(), headers=headers)
        ).json() == response.json()
        assert (await client.get(path, headers=headers)).json() == response.json()
        rows = await client.get(
            f"/api/v1/plans/{saved.approval.plan_id}/completions", headers=headers
        )
        assert rows.json() == [response.json()]
        assert (
            await client.get(path, headers={"X-Synthetic-Principal": "synthetic-b"})
        ).status_code == 404
        conflict = await client.post(
            path, json={**body.model_dump(), "idempotency_key": "different"}, headers=headers
        )
        assert conflict.status_code == 409 and conflict.json()["code"] == "session_already_recorded"
    assert await counts(rig) == (1, 1)


async def test_independent_sessions_overlap_without_owner_wide_write_lock(submitted):
    rig, backend, saved, body = submitted
    barrier = asyncio.Barrier(2)

    async def before(query, connection):
        if "INSERT INTO session_idempotency" in query:
            await barrier.wait()

    rig.controls.before_execute = before
    results = await asyncio.gather(
        backend.submit(Principal.A, saved.approval.plan_id, 1, body),
        backend.submit(
            Principal.A,
            saved.approval.plan_id,
            2,
            body.model_copy(update={"idempotency_key": "second"}),
        ),
    )
    assert {r.day_index for r in results} == {1, 2} and await counts(rig) == (2, 2)


async def test_deferred_actual_commit_failure_rolls_back_both_rows(submitted):
    rig, backend, saved, body = submitted
    async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
        await connection.execute("""CREATE FUNCTION reject_session_commit()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'synthetic deferred fault'; END; $$""")
        await connection.execute("""CREATE CONSTRAINT TRIGGER reject_session_commit
            AFTER INSERT ON session_idempotency
            DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION reject_session_commit()""")
    assert (
        await outcome(backend.submit(Principal.A, saved.approval.plan_id, 1, body))
        == "reconciliation_pending"
    )
    assert await counts(rig) == (0, 0)
    async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
        await connection.execute("DROP TRIGGER reject_session_commit ON session_idempotency")
    await backend.submit(Principal.A, saved.approval.plan_id, 1, body)
    assert await counts(rig) == (1, 1)


async def test_actual_http_lost_commit_diagnosis_and_explicit_key_retry(submitted):
    rig, backend, saved, body = submitted
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=rig.profiles,
        approvals=rig.database,
        completions=backend,
    )
    path = f"/api/v1/plans/{saved.approval.plan_id}/sessions/1/completion"
    rig.controls.mode = "lost_after"
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1",
        headers={"X-Synthetic-Principal": "synthetic-a"},
    ) as client:
        lost = await client.post(path, json=body.model_dump())
        assert lost.status_code == 503 and lost.json()["code"] == "reconciliation_pending"
        assert await counts(rig) == (1, 1)
        rig.controls.mode = "normal"
        retry = await client.post(path, json=body.model_dump())
        read = await client.get(path)
    assert retry.status_code == read.status_code == 200 and retry.json() == read.json()
    assert await counts(rig) == (1, 1)
    traces = app.state.tracer.snapshot()
    if os.environ.get("FATA_F204_EVIDENCE") == "1":
        Path("docs/implementation/evidence/f2-04-session-trace.json").write_text(
            json.dumps(
                {
                    "fault": "lost acknowledgement after native COMMIT",
                    "statuses": [503, 200, 200],
                    "record_and_key_counts": [1, 1],
                    "trace": traces,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


@pytest.mark.parametrize("same_key", [True, False])
async def test_actual_http_concurrent_submissions_use_transaction_guards(submitted, same_key):
    rig, backend, saved, body = submitted
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=rig.profiles,
        approvals=rig.database,
        completions=backend,
    )
    path = f"/api/v1/plans/{saved.approval.plan_id}/sessions/1/completion"
    rig.controls.point = "before"
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1",
        headers={"X-Synthetic-Principal": "synthetic-a"},
    ) as client:
        first = asyncio.create_task(client.post(path, json=body.model_dump()))
        await rig.controls.entered.wait()
        seen = asyncio.Event()
        waiting = []

        async def before(query, connection):
            if (
                "pg_advisory_xact_lock" in query
                and connection.info.backend_pid != rig.controls.commit_pid
            ):
                waiting.append(connection.info.backend_pid)
                seen.set()

        rig.controls.before_execute = before
        second = asyncio.create_task(
            client.post(
                path,
                json={
                    **body.model_dump(),
                    "idempotency_key": body.idempotency_key if same_key else "second-key",
                },
            )
        )
        await seen.wait()
        await wait_for_block(rig.dsn, waiting[0])
        rig.controls.release.set()
        a, b = await asyncio.gather(first, second)
        assert a.status_code == 200 and b.status_code == (200 if same_key else 409)
        if same_key:
            assert a.json() == b.json()
        else:
            assert b.json()["code"] == "session_already_recorded"
    assert await counts(rig) == (1, 1)


async def test_actual_http_cancellation_waits_for_submit_and_retry_recovers(submitted):
    rig, backend, saved, body = submitted
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=rig.profiles,
        approvals=rig.database,
        completions=backend,
    )
    path = f"/api/v1/plans/{saved.approval.plan_id}/sessions/1/completion"
    rig.controls.point = "before"
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1",
        headers={"X-Synthetic-Principal": "synthetic-a"},
    ) as client:
        sending = asyncio.create_task(client.post(path, json=body.model_dump()))
        await rig.controls.entered.wait()
        sending.cancel()
        await asyncio.sleep(0)
        assert not sending.done()
        rig.controls.release.set()
        with pytest.raises(asyncio.CancelledError):
            await sending
        retry = await client.post(path, json=body.model_dump())
        assert retry.status_code == 200
    assert await counts(rig) == (1, 1)
