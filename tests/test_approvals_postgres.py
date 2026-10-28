import asyncio
import json
import subprocess
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass

import psycopg
import pytest
from agent_doubles import ManualClock
from approval_db_doubles import Controls
from psycopg import sql
from test_profile_postgres import pg_schema as pg_schema

from future_training.approval import Approvals
from future_training.candidates import CandidateStore, GuardedLineage
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import Catalog, load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.approvals import PostgresApprovals
from future_training.persistence.plans import OwnedPlanReader
from future_training.persistence.profiles import PostgresProfiles
from future_training.schemas import ApprovalRequest, ProfileSaveRequest

pytestmark = pytest.mark.integration


@dataclass
class Rig:
    controls: Controls
    profiles: PostgresProfiles
    database: PostgresApprovals
    store: CandidateStore
    service: Approvals
    clock: ManualClock
    dsn: str

    async def candidate(self, principal=Principal.A):
        saved = await self.profiles.get(principal)
        plan = plan_week(saved.preferences, self.database.catalog).plan
        return await self.store.publish_initial(
            principal, plan, expected_profile_revision=saved.revision
        )

    async def counts(self):
        async with await psycopg.AsyncConnection.connect(self.dsn) as connection:
            return await self._counts(connection)

    async def _counts(self, connection):
        counts = []
        for table in ("approved_plans", "approval_idempotency", "approval_audit"):
            row = await (
                await connection.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
                )
            ).fetchone()
            counts.append(row[0])
        return tuple(counts)


@pytest.fixture
async def rig(pg_schema, profile):
    dsn = pg_schema[1]

    async def connect():
        return await psycopg.AsyncConnection.connect(dsn)

    catalog = load_catalog()
    profiles = PostgresProfiles(catalog, connect=connect)
    for principal in Principal:
        await profiles.save(principal, ProfileSaveRequest(expected_revision=0, preferences=profile))
    controls = Controls(dsn)
    database = PostgresApprovals(catalog, connect=controls.connect)
    clock = ManualClock()
    store = CandidateStore(profiles, catalog, clock=clock.now)
    service = Approvals(store, database)
    result = Rig(controls, profiles, database, store, service, clock, dsn)
    try:
        yield result
    finally:
        await controls.settle_retained(commit=False)


def request(snapshot, key="key-a"):
    return ApprovalRequest(**snapshot.identity().model_dump(), idempotency_key=key)


async def error_code(coroutine):
    try:
        return await coroutine
    except ServiceError as exc:
        return exc.code


def observe_guard_wait(store):
    original = store.lineage_guard
    waiting = asyncio.Event()

    @asynccontextmanager
    async def observed(principal, candidate_id):
        if store._find(principal, candidate_id).guard.locked():
            waiting.set()
        async with original(principal, candidate_id) as guard:
            yield guard

    store.lineage_guard = observed
    return waiting


async def test_real_atomic_snapshot_retries_fingerprints_and_owner_isolation(rig):
    a, b = await rig.candidate(), await rig.candidate(Principal.B)
    result = await rig.service.approve(Principal.A, request(a))
    assert await rig.counts() == (1, 1, 1)
    assert await rig.service.approve(Principal.A, request(a)) == result
    assert (
        await error_code(rig.service.approve(Principal.A, request(a, "another")))
        == "candidate_already_approved"
    )
    forged = request(a).model_copy(update={"candidate_id": "absent"})
    assert await error_code(rig.service.approve(Principal.A, forged)) == "idempotency_mismatch"
    assert await error_code(rig.service.approve(Principal.B, request(a))) == "not_found"
    other = await rig.service.approve(Principal.B, request(b))
    assert other.plan_id != result.plan_id
    assert await rig.counts() == (2, 2, 2)
    reader = OwnedPlanReader(rig.database)
    saved = await reader.get(Principal.A, result.plan_id)
    assert saved.plan == a.proposal() and saved.versions == a.versions()
    assert await error_code(reader.get(Principal.B, result.plan_id)) == "not_found"
    saved.plan.days.clear()
    assert len((await reader.get(Principal.A, result.plan_id)).plan.days) == 2


@pytest.mark.parametrize("same_key", [True, False])
async def test_initial_misses_wait_then_durable_recheck_wins(rig, same_key):
    snapshot = await rig.candidate()
    original = rig.database.committed
    barrier = asyncio.Barrier(2)
    calls = 0

    async def committed(*args):
        nonlocal calls
        calls += 1
        value = await original(*args)
        if calls <= 2:
            await barrier.wait()
        return value

    rig.database.committed = committed
    waiting = observe_guard_wait(rig.store)
    rig.controls.point = "before"
    first = asyncio.create_task(error_code(rig.service.approve(Principal.A, request(snapshot))))
    second = asyncio.create_task(
        error_code(
            rig.service.approve(Principal.A, request(snapshot, "key-a" if same_key else "key-b"))
        )
    )
    await rig.controls.entered.wait()
    await waiting.wait()
    rig.controls.release.set()
    results = await asyncio.gather(first, second)
    successes = [r for r in results if not isinstance(r, str)]
    assert len(successes) == (2 if same_key else 1)
    if same_key:
        assert successes[0] == successes[1]
    else:
        assert "candidate_already_approved" in results
    assert rig.controls.commit_calls == 1 and await rig.counts() == (1, 1, 1)


async def test_same_key_different_lineages_uses_sql_unique_and_rolls_back_loser(rig):
    first, second = await rig.candidate(), await rig.candidate()
    barrier = asyncio.Barrier(2)
    original = rig.database.committed
    calls = 0

    async def committed(*args):
        nonlocal calls
        calls += 1
        current = calls
        value = await original(*args)
        if current <= 2:
            await barrier.wait()
        return value

    rig.database.committed = committed
    original_write = rig.database.write
    writers = asyncio.Barrier(2)
    binding_attempts = 0

    async def write(*args):
        await writers.wait()
        return await original_write(*args)

    async def before(query, connection):
        nonlocal binding_attempts
        if "INSERT INTO approval_idempotency" in query:
            binding_attempts += 1

    rig.database.write = write
    rig.controls.before_execute = before
    results = await asyncio.gather(
        error_code(rig.service.approve(Principal.A, request(first))),
        error_code(rig.service.approve(Principal.A, request(second))),
    )
    assert sum(not isinstance(r, str) for r in results) == 1
    assert "idempotency_mismatch" in results
    assert await rig.counts() == (1, 1, 1)
    assert binding_attempts == 2


async def test_sql_candidate_unique_is_last_guard_even_without_same_memory_store(rig):
    snapshot = await rig.candidate()
    await rig.database.write(Principal.A, request(snapshot), snapshot)
    with pytest.raises(psycopg.errors.UniqueViolation):
        await rig.database.write(Principal.A, request(snapshot, "key-b"), snapshot)
    assert await rig.counts() == (1, 1, 1)


@pytest.mark.parametrize("point", ["before", "after"])
async def test_repeated_cancellation_waits_for_real_commit_and_memory_finalization(rig, point):
    snapshot = await rig.candidate()
    rig.controls.point = point
    task = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
    await rig.controls.entered.wait()
    assert await rig.counts() == ((0, 0, 0) if point == "before" else (1, 1, 1))
    task.cancel()
    waiting = observe_guard_wait(rig.store)
    revise = asyncio.create_task(error_code(rig.store.get(Principal.A, snapshot.candidate_id)))
    await waiting.wait()
    task.cancel()  # Another cancellation after the owner resumed its shield loop.
    assert not task.done() and not revise.done()
    rig.controls.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert await revise == "candidate_already_approved"
    assert await rig.counts() == (1, 1, 1)
    assert (
        await rig.service.approve(Principal.A, request(snapshot))
    ).candidate == snapshot.identity()


@pytest.mark.parametrize("mode", ["lost_after", "cancel_after", "rollback_uncertain", "fail_audit"])
async def test_real_commit_faults_reconcile_or_rollback_without_partial_rows(rig, mode):
    snapshot = await rig.candidate()
    rig.controls.mode = mode
    result = await error_code(rig.service.approve(Principal.A, request(snapshot)))
    committed = mode in ("lost_after", "cancel_after")
    assert await rig.counts() == ((1, 1, 1) if committed else (0, 0, 0))
    if committed:
        assert result.candidate == snapshot.identity()
    else:
        assert result == "internal_error"
        assert (await rig.store.get(Principal.A, snapshot.candidate_id)) == snapshot
    rig.controls.mode = "normal"
    await rig.service.approve(Principal.A, request(snapshot))
    assert await rig.counts() == (1, 1, 1)


@pytest.mark.parametrize("commits", [True, False])
async def test_inflight_uncertainty_is_quarantined_until_authoritative_outcome(rig, commits):
    snapshot = await rig.candidate()
    async with rig.store.revision(Principal.A, snapshot.identity()) as reservation:
        rig.controls.mode = "open_uncertain"
        assert (
            await error_code(rig.service.approve(Principal.A, request(snapshot)))
            == "reconciliation_pending"
        )
        assert await rig.counts() == (0, 0, 0)  # Invisible uncommitted rows, not proof of rollback.
        assert (
            await error_code(
                rig.store.publish_revision(Principal.A, reservation, snapshot.proposal())
            )
            == "reconciliation_pending"
        )
        assert (
            await error_code(rig.service.approve(Principal.A, request(snapshot, "new-key")))
            == "reconciliation_pending"
        )
        await rig.store.expire()
        assert rig.store.stats()["lineages"] == 1
        rig.controls.mode = "normal"
        await rig.controls.settle_retained(commit=commits)
        if commits:
            assert (
                await error_code(rig.store.get(Principal.A, snapshot.candidate_id))
                == "candidate_already_approved"
            )
            assert (
                await rig.service.approve(Principal.A, request(snapshot))
            ).candidate == snapshot.identity()
        else:
            assert await rig.store.get(Principal.A, snapshot.candidate_id) == snapshot
            await rig.service.approve(Principal.A, request(snapshot))
        assert await rig.counts() == (1, 1, 1)


async def test_reconciliation_outage_pins_expired_lineage_and_allows_later_recovery(rig):
    snapshot = await rig.candidate()
    rig.controls.mode = "open_uncertain"
    rig.controls.reconcile_unavailable = True
    assert (
        await error_code(rig.service.approve(Principal.A, request(snapshot)))
        == "reconciliation_pending"
    )
    rig.clock.advance(1800)
    await rig.store.expire()
    assert rig.store.stats()["lineages"] == 1
    with pytest.raises(ServiceError, match="reconciliation_pending"):
        async with rig.store.revision(Principal.A, snapshot.identity()):
            pass
    rig.controls.mode = "normal"
    rig.controls.reconcile_unavailable = False
    await rig.controls.settle_retained(commit=True)
    result = await rig.service.approve(Principal.A, request(snapshot))
    assert result.candidate == snapshot.identity()
    await rig.store.expire()
    assert rig.store.stats()["lineages"] == 0


async def test_memory_finalization_fault_is_reconciled_under_guard(rig, monkeypatch):
    snapshot = await rig.candidate()
    original = GuardedLineage.mark_approved
    calls = 0

    def once(guard):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("Synthetic memory finalization failure")
        original(guard)

    monkeypatch.setattr(GuardedLineage, "mark_approved", once)
    assert (
        await rig.service.approve(Principal.A, request(snapshot))
    ).candidate == snapshot.identity()
    assert calls == 2 and await rig.counts() == (1, 1, 1)


async def test_approval_wins_guard_pending_revision_cannot_publish(rig):
    snapshot = await rig.candidate()
    async with rig.store.revision(Principal.A, snapshot.identity()) as reservation:
        rig.controls.point = "before"
        task = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
        await rig.controls.entered.wait()
        waiting = observe_guard_wait(rig.store)
        publish = asyncio.create_task(
            error_code(rig.store.publish_revision(Principal.A, reservation, snapshot.proposal()))
        )
        await waiting.wait()
        rig.controls.release.set()
        await task
        assert await publish == "candidate_already_approved"
    assert await rig.counts() == (1, 1, 1)


async def test_revision_wins_guard_old_approval_is_superseded(rig):
    old = await rig.candidate()
    async with rig.store.revision(Principal.A, old.identity()) as reservation:
        updated = await rig.store.publish_revision(Principal.A, reservation, old.proposal())
    assert (
        await error_code(rig.service.approve(Principal.A, request(old))) == "candidate_superseded"
    )
    assert await rig.counts() == (0, 0, 0)
    result = await rig.service.approve(Principal.A, request(updated))
    assert result.candidate.revision == 2


@pytest.mark.parametrize("edge", ["equal", "before_finish_after", "wait_past"])
async def test_expiry_acceptance_is_guard_acquisition_not_commit_time(rig, edge):
    snapshot = await rig.candidate()
    rig.clock.advance(
        snapshot.expires_at_monotonic - rig.clock.now() - (0 if edge == "equal" else 1)
    )
    if edge == "equal":
        assert (
            await error_code(rig.service.approve(Principal.A, request(snapshot)))
            == "candidate_expired"
        )
        assert await rig.counts() == (0, 0, 0)
    elif edge == "wait_past":
        waiting = observe_guard_wait(rig.store)
        async with rig.store.lineage_guard(Principal.A, snapshot.candidate_id):
            task = asyncio.create_task(
                error_code(rig.service.approve(Principal.A, request(snapshot)))
            )
            await waiting.wait()
            rig.clock.advance(1)
        assert await task == "candidate_expired"
        assert await rig.counts() == (0, 0, 0)
    else:
        rig.controls.point = "before"
        task = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
        await rig.controls.entered.wait()
        rig.clock.advance(1)
        await rig.store.expire()
        assert rig.store.stats()["lineages"] == 1
        rig.controls.release.set()
        result = await task
        await rig.store.expire()
        assert rig.store.stats()["lineages"] == 0
        assert await rig.service.approve(Principal.A, request(snapshot)) == result
        assert (
            await error_code(rig.service.approve(Principal.A, request(snapshot, "new")))
            == "candidate_expired"
        )


async def test_history_pagination_and_later_context_changes_do_not_rewrite_snapshots(rig, profile):
    results = []
    for _ in range(3):
        results.append(
            await rig.service.approve(
                Principal.A, request(await rig.candidate(), f"key-{len(results)}")
            )
        )
    reader = OwnedPlanReader(rig.database)
    before = await reader.get(Principal.A, results[0].plan_id)
    await rig.profiles.save(
        Principal.A,
        ProfileSaveRequest(expected_revision=1, preferences={**profile, "session_minutes": 30}),
    )
    newer = PostgresApprovals(Catalog("catalog-v2", []), connect=rig.controls.connect)
    assert await OwnedPlanReader(newer).get(Principal.A, results[0].plan_id) == before
    ids = []
    cursor = None
    for _ in range(4):
        page = await reader.history(Principal.A, limit=1, cursor=cursor)
        if not page:
            break
        ids.append(page[0].approval.plan_id)
        cursor = ids[-1]
    assert ids == sorted(r.plan_id for r in results)
    assert await reader.history(Principal.B) == ()


async def test_true_process_restart_recovers_key_without_any_candidate(rig):
    snapshot = await rig.candidate()
    bound = request(snapshot)
    result = await rig.service.approve(Principal.A, bound)
    code = """
import asyncio,json,sys
sys.path.insert(0,'src')
import psycopg
from future_training.approval import Approvals
from future_training.candidates import CandidateStore
from future_training.domain.catalog import load_catalog
from future_training.identity import Principal
from future_training.persistence.approvals import PostgresApprovals
from future_training.persistence.profiles import PostgresProfiles
from future_training.schemas import ApprovalRequest
async def main():
 async def connect():return await psycopg.AsyncConnection.connect(sys.argv[1])
 catalog=load_catalog();profiles=PostgresProfiles(catalog,connect=connect)
 store=CandidateStore(profiles,catalog);db=PostgresApprovals(catalog,connect=connect)
 request=ApprovalRequest.model_validate_json(sys.argv[2])
 result=await Approvals(store,db).approve(Principal.A,request)
 assert store.stats()['lineages']==0
 print(result.model_dump_json())
with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(main())
"""
    child = subprocess.run(
        [sys.executable, "-c", code, rig.dsn, bound.model_dump_json()],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == result.model_dump()


async def wait_for_block(dsn, pid):
    async with await psycopg.AsyncConnection.connect(dsn) as connection:
        async with asyncio.timeout(3):
            while not (
                await (await connection.execute("SELECT pg_blocking_pids(%s)", (pid,))).fetchone()
            )[0]:
                await asyncio.sleep(0)


@pytest.mark.parametrize("save_first", [True, False])
async def test_real_profile_row_lock_serializes_save_and_approval(rig, profile, save_first):
    snapshot = await rig.candidate()
    if save_first:
        async with await psycopg.AsyncConnection.connect(rig.dsn) as saving:
            await saving.execute(
                "UPDATE profiles SET revision=2,"
                "preferences=jsonb_set(preferences,'{session_minutes}','30') "
                "WHERE owner_id='synthetic-a'"
            )
            about_to_lock = asyncio.Event()
            pid = []

            async def before(query, connection):
                if "FOR UPDATE" in query:
                    pid.append(connection.info.backend_pid)
                    about_to_lock.set()

            rig.controls.before_execute = before
            approval = asyncio.create_task(
                error_code(rig.service.approve(Principal.A, request(snapshot)))
            )
            await about_to_lock.wait()
            await wait_for_block(rig.dsn, pid[0])
            await saving.commit()
            assert await approval == "stale_profile"
        assert await rig.counts() == (0, 0, 0)
    else:
        rig.controls.point = "before"
        approval = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
        await rig.controls.entered.wait()
        pid = []
        connected = asyncio.Event()

        async def connect():
            connection = await psycopg.AsyncConnection.connect(rig.dsn)
            pid.append(connection.info.backend_pid)
            connected.set()
            return connection

        saving_repo = PostgresProfiles(rig.database.catalog, connect=connect)
        saving = asyncio.create_task(
            saving_repo.save(
                Principal.A,
                ProfileSaveRequest(
                    expected_revision=1, preferences={**profile, "session_minutes": 30}
                ),
            )
        )
        await connected.wait()
        await wait_for_block(rig.dsn, pid[0])
        rig.controls.release.set()
        approved = await approval
        assert (await saving).revision == 2
        saved = await OwnedPlanReader(rig.database).get(Principal.A, approved.plan_id)
        assert saved.versions.profile_revision == 1 and saved.plan.profile.session_minutes == 20


async def test_deferred_database_commit_failure_rolls_back_all_three_rows(rig):
    async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
        await connection.execute(
            """CREATE FUNCTION fail_commit_test() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'synthetic deferred failure'; END; $$"""
        )
        await connection.execute(
            """CREATE CONSTRAINT TRIGGER fail_commit_test AFTER INSERT ON approval_audit
            DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fail_commit_test()"""
        )
    snapshot = await rig.candidate()
    assert await error_code(rig.service.approve(Principal.A, request(snapshot))) == "internal_error"
    assert await rig.counts() == (0, 0, 0)
    assert await rig.store.get(Principal.A, snapshot.candidate_id) == snapshot
    async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
        await connection.execute("DROP TRIGGER fail_commit_test ON approval_audit")
        await connection.execute("DROP FUNCTION fail_commit_test()")
    await rig.service.approve(Principal.A, request(snapshot))
    assert await rig.counts() == (1, 1, 1)


@pytest.mark.parametrize("table", ["approved_plans", "approval_idempotency", "approval_audit"])
@pytest.mark.parametrize("action", ["UPDATE", "DELETE", "TRUNCATE"])
async def test_approved_state_is_immutable_in_postgres(rig, table, action):
    await rig.service.approve(Principal.A, request(await rig.candidate()))
    query = {
        "UPDATE": sql.SQL("UPDATE {} SET owner_id=owner_id"),
        "DELETE": sql.SQL("DELETE FROM {}"),
        "TRUNCATE": sql.SQL("TRUNCATE {} CASCADE"),
    }[action]
    with pytest.raises(psycopg.Error) as exc:
        async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
            await connection.execute(query.format(sql.Identifier(table)))
    assert exc.value.sqlstate == "55000"
    assert await rig.counts() == (1, 1, 1)


async def test_database_rejects_plan_bytes_hash_mismatch(rig):
    result = await rig.service.approve(Principal.A, request(await rig.candidate()))
    with pytest.raises(psycopg.errors.CheckViolation):
        async with await psycopg.AsyncConnection.connect(rig.dsn) as connection:
            await connection.execute(
                """INSERT INTO approved_plans SELECT 'forged-plan',owner_id,'forged-candidate',
                candidate_revision,content_hash,profile_revision,catalog_revision,validator_revision,
                plan_bytes || ' '::bytea FROM approved_plans WHERE plan_id=%s""",
                (result.plan_id,),
            )
    assert await rig.counts() == (1, 1, 1)


async def test_cancellation_during_actual_postgres_commit_keeps_guard(rig):
    from future_training.persistence.approvals import identity_lock

    snapshot = await rig.candidate()
    gate = identity_lock("commit-test", snapshot.candidate_id)
    async with await psycopg.AsyncConnection.connect(rig.dsn) as setup:
        await setup.execute(
            sql.SQL("""CREATE FUNCTION wait_commit_test() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock({});
            RETURN NEW; END; $$""").format(sql.Literal(gate))
        )
        await setup.execute("""CREATE CONSTRAINT TRIGGER wait_commit_test
            AFTER INSERT ON approval_audit DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION wait_commit_test()""")
    async with await psycopg.AsyncConnection.connect(rig.dsn) as blocker:
        await blocker.execute("SELECT pg_advisory_lock(%s)", (gate,))
        rig.controls.point = "during"
        task = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
        await rig.controls.entered.wait()
        await wait_for_block(rig.dsn, rig.controls.commit_pid)
        task.cancel()
        waiting = observe_guard_wait(rig.store)
        read = asyncio.create_task(error_code(rig.store.get(Principal.A, snapshot.candidate_id)))
        await waiting.wait()
        task.cancel()
        assert not task.done() and await rig.counts() == (0, 0, 0)
        await blocker.execute("SELECT pg_advisory_unlock(%s)", (gate,))
        with pytest.raises(asyncio.CancelledError):
            await task
        assert await read == "candidate_already_approved"
    assert await rig.counts() == (1, 1, 1)


async def test_matching_retry_after_initial_miss_and_expired_guard_wait(rig):
    snapshot = await rig.candidate()
    rig.clock.advance(snapshot.expires_at_monotonic - rig.clock.now() - 1)
    original = rig.database.committed
    barrier = asyncio.Barrier(2)
    calls = 0

    async def committed(*args):
        nonlocal calls
        calls += 1
        current = calls
        result = await original(*args)
        if current <= 2:
            await barrier.wait()
        return result

    rig.database.committed = committed
    waiting = observe_guard_wait(rig.store)
    rig.controls.point = "before"
    first = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
    second = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
    await rig.controls.entered.wait()
    await waiting.wait()
    rig.clock.advance(1)
    rig.controls.release.set()
    results = await asyncio.gather(first, second)
    assert results[0] == results[1] and rig.controls.commit_calls == 1
    assert await rig.counts() == (1, 1, 1)


@pytest.mark.parametrize("matching", [True, False])
async def test_commit_and_eviction_between_lookup_and_guard_preserves_binding(rig, matching):
    snapshot = await rig.candidate()
    original = rig.database.committed
    missed, resume = asyncio.Event(), asyncio.Event()
    first = True

    async def committed(*args):
        nonlocal first
        pause = first
        first = False
        result = await original(*args)
        if pause:
            assert result is None
            missed.set()
            await resume.wait()
        return result

    rig.database.committed = committed
    retry_request = request(snapshot)
    if not matching:
        retry_request = retry_request.model_copy(update={"revision": 2})
    retry = asyncio.create_task(error_code(rig.service.approve(Principal.A, retry_request)))
    await missed.wait()
    winner = await rig.service.approve(Principal.A, request(snapshot))
    rig.clock.advance(snapshot.expires_at_monotonic - rig.clock.now())
    await rig.store.expire()
    assert rig.store.stats()["lineages"] == 0
    resume.set()
    assert await retry == (winner if matching else "idempotency_mismatch")
    assert await rig.counts() == (1, 1, 1)


async def test_transaction_independently_validates_locked_profile_and_domain(rig):
    import hashlib
    from dataclasses import replace

    from future_training.candidates import encode_snapshot

    snapshot = await rig.candidate()
    plan = snapshot.proposal()
    plan.days[0].planned_seconds += 1
    encoded = encode_snapshot(plan)
    forged = replace(
        snapshot, canonical_bytes=encoded, content_hash=hashlib.sha256(encoded).hexdigest()
    )
    assert (
        await error_code(rig.database.write(Principal.A, request(forged), forged))
        == "invalid_request"
    )
    assert await rig.counts() == (0, 0, 0)


async def test_cancellation_before_initial_lookup_finishes_has_no_write(rig):
    snapshot = await rig.candidate()
    entered = asyncio.Event()
    original = rig.database.committed

    async def pending(*args):
        result = await original(*args)
        entered.set()
        await asyncio.Event().wait()
        return result

    rig.database.committed = pending
    task = asyncio.create_task(rig.service.approve(Principal.A, request(snapshot)))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert rig.controls.commit_calls == 0 and await rig.counts() == (0, 0, 0)
    assert await rig.store.get(Principal.A, snapshot.candidate_id) == snapshot


async def test_sql_uniqueness_conflict_is_classified_from_durable_identity(rig):
    snapshot = await rig.candidate()
    await rig.database.write(Principal.A, request(snapshot), snapshot)
    assert (
        await error_code(rig.service.approve(Principal.A, request(snapshot, "new-key")))
        == "candidate_already_approved"
    )
    assert await rig.counts() == (1, 1, 1)


async def test_known_rollback_allows_existing_revision_reservation_to_publish(rig):
    snapshot = await rig.candidate()
    async with rig.store.revision(Principal.A, snapshot.identity()) as reservation:
        rig.controls.mode = "open_uncertain"
        assert (
            await error_code(rig.service.approve(Principal.A, request(snapshot)))
            == "reconciliation_pending"
        )
        await rig.controls.settle_retained(commit=False)
        rig.controls.mode = "normal"
        revised = await rig.store.publish_revision(Principal.A, reservation, snapshot.proposal())
    result = await rig.service.approve(Principal.A, request(revised, "after-revision"))
    assert result.candidate.revision == 2 and await rig.counts() == (1, 1, 1)
