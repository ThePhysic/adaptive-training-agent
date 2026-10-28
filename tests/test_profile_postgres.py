import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from future_training.api import create_app
from future_training.config import Settings
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.approvals import PostgresApprovals
from future_training.persistence.profiles import LOCAL_DSN, PostgresProfiles
from future_training.schemas import ProfileSaveRequest, SavedProfile

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def pg_schema():
    name = "f103_test_" + uuid4().hex
    with psycopg.connect(LOCAL_DSN) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        connection.execute(sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(name)))
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            connection.execute(path.read_text(encoding="utf-8"))
    dsn = make_conninfo(
        LOCAL_DSN, options=f"-c search_path={name} -c statement_timeout=5000 -c lock_timeout=2000"
    )
    try:
        yield name, dsn
    finally:
        with psycopg.connect(LOCAL_DSN) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(name)))


@pytest.fixture
def repository(pg_schema):
    async def connect():
        return await psycopg.AsyncConnection.connect(pg_schema[1])

    return PostgresProfiles(load_catalog(), connect=connect)


@pytest.fixture
def approval_repository(pg_schema):
    async def connect():
        return await psycopg.AsyncConnection.connect(pg_schema[1])

    return PostgresApprovals(load_catalog(), connect=connect)


async def test_real_save_read_owner_isolation_and_no_implicit_create(repository, profile):
    with pytest.raises(ServiceError, match="not_found"):
        await repository.get(Principal.A)
    saved = await repository.save(
        Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile)
    )
    assert saved.revision == 1
    with pytest.raises(ServiceError, match="not_found"):
        await repository.get(Principal.B)
    updated = await repository.save(
        Principal.A,
        ProfileSaveRequest(expected_revision=1, preferences={**profile, "session_minutes": 30}),
    )
    assert updated.revision == 2
    saved.preferences.session_minutes = 45
    assert (await repository.get(Principal.A)).preferences.session_minutes == 30
    with pytest.raises(ServiceError, match="stale_profile"):
        await repository.save(
            Principal.A, ProfileSaveRequest(expected_revision=1, preferences=profile)
        )
    with pytest.raises(ServiceError, match="stale_profile"):
        await repository.save(
            Principal.B, ProfileSaveRequest(expected_revision=1, preferences=profile)
        )
    with pytest.raises(ServiceError, match="unauthorized"):
        await repository.get("synthetic-a")


@pytest.mark.parametrize("initial_revision", [0, 1])
async def test_real_concurrent_create_and_update_have_one_winner(
    repository, profile, initial_revision
):
    if initial_revision:
        await repository.save(
            Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile)
        )
    barrier = asyncio.Barrier(2)

    async def attempt(minutes):
        # Both hold the same observed/precondition revision before either writes.
        if initial_revision:
            assert (await repository.get(Principal.A)).revision == initial_revision
        await barrier.wait()
        try:
            return await repository.save(
                Principal.A,
                ProfileSaveRequest(
                    expected_revision=initial_revision,
                    preferences={**profile, "session_minutes": minutes},
                ),
            )
        except ServiceError as error:
            return error

    results = await asyncio.gather(attempt(30), attempt(45))
    assert sum(isinstance(r, SavedProfile) for r in results) == 1
    failed = next(r for r in results if isinstance(r, ServiceError))
    assert (failed.status, failed.code) == (409, "stale_profile")
    assert (await repository.get(Principal.A)).revision == initial_revision + 1


async def test_two_principals_save_concurrently_without_cross_updates(repository, profile):
    barrier = asyncio.Barrier(2)

    async def save(principal, minutes):
        await barrier.wait()
        return await repository.save(
            principal,
            ProfileSaveRequest(
                expected_revision=0, preferences={**profile, "session_minutes": minutes}
            ),
        )

    results = await asyncio.gather(save(Principal.A, 20), save(Principal.B, 45))
    assert [r.revision for r in results] == [1, 1]
    assert (await repository.get(Principal.A)).preferences.session_minutes == 20
    assert (await repository.get(Principal.B)).preferences.session_minutes == 45


async def test_unknown_exclusion_or_forged_revision_never_saved(repository, profile):
    for preferences in (
        {**profile, "excluded_tags": ["unknown_tag"]},
        {**profile, "excluded_ids": ["unknown_id"]},
    ):
        with pytest.raises(ServiceError, match="invalid_request"):
            await repository.save(
                Principal.A, ProfileSaveRequest(expected_revision=0, preferences=preferences)
            )
    invalid = ProfileSaveRequest(expected_revision=0, preferences=profile)
    invalid.expected_revision = True
    with pytest.raises(ServiceError, match="invalid_request"):
        await repository.save(Principal.A, invalid)
    with pytest.raises(ServiceError, match="not_found"):
        await repository.get(Principal.A)


async def test_deferred_database_failure_rolls_back_and_never_reports_success(
    repository, pg_schema, profile
):
    with psycopg.connect(pg_schema[1]) as connection:
        connection.execute("""
          CREATE FUNCTION reject_profile_commit() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'synthetic-private-driver-canary'; END $$;
          CREATE CONSTRAINT TRIGGER reject_profile_commit AFTER INSERT OR UPDATE ON profiles
          DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION reject_profile_commit();
        """)
    with pytest.raises(ServiceError) as error:
        await repository.save(
            Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile)
        )
    assert (error.value.status, error.value.code) == (503, "internal_error")
    assert "synthetic-private-driver-canary" not in str(error.value)
    with psycopg.connect(pg_schema[1]) as connection:
        assert connection.execute("SELECT count(*) FROM profiles").fetchone() == (0,)


async def test_native_async_postgres_through_http_routes(repository, profile):
    app = create_app(settings=Settings(local_development="1"), profiles=repository)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000"
    ) as client:
        a, b = {"X-Synthetic-Principal": "synthetic-a"}, {"X-Synthetic-Principal": "synthetic-b"}
        saved = await client.put(
            "/api/v1/profile", headers=a, json={"expected_revision": 0, "preferences": profile}
        )
        assert saved.status_code == 200 and saved.json()["revision"] == 1
        assert (await client.get("/api/v1/profile", headers=b)).status_code == 404
        assert (await client.get("/api/v1/profile", headers=a)).json() == saved.json()


def test_actual_interpreter_restart_retains_profile_but_not_candidates(pg_schema, profile):
    script = """
import asyncio,json,sys
import psycopg
from future_training.runtime import loop_factory
from future_training.domain.catalog import load_catalog
from future_training.domain.baseline import plan_week
from future_training.persistence.profiles import PostgresProfiles
from future_training.candidates import CandidateStore
from future_training.schemas import ProfileSaveRequest
from future_training.identity import Principal
from future_training.errors import ServiceError
async def main():
    async def connect(): return await psycopg.AsyncConnection.connect(sys.argv[1])
    catalog=load_catalog()
    repo=PostgresProfiles(catalog,connect=connect)
    store=CandidateStore(repo,catalog)
    if sys.argv[2]=='create':
        prefs=json.loads(sys.argv[3])
        await repo.save(Principal.A,ProfileSaveRequest(expected_revision=0,preferences=prefs))
        candidate=await store.publish_initial(Principal.A,plan_week(prefs,catalog).plan,
                                             expected_profile_revision=1)
        print(json.dumps({'candidate_id':candidate.candidate_id,'profile_revision':1}))
    else:
        current=await repo.get(Principal.A)
        try: await store.get(Principal.A,sys.argv[3])
        except ServiceError as error:
            print(json.dumps({'profile_revision':current.revision,'candidate_status':error.status,'lineages':store.stats()['lineages']}))
with asyncio.Runner(loop_factory=loop_factory) as runner: runner.run(main())
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    first = subprocess.run(
        [sys.executable, "-c", script, pg_schema[1], "create", json.dumps(profile)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    identity = json.loads(first.stdout)["candidate_id"]
    second = subprocess.run(
        [sys.executable, "-c", script, pg_schema[1], "read", identity],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    assert json.loads(second.stdout) == {
        "profile_revision": 1,
        "candidate_status": 404,
        "lineages": 0,
    }
    with psycopg.connect(pg_schema[1]) as connection:
        tables = connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=%s",
            (pg_schema[0],),
        ).fetchall()
        assert {r[0] for r in tables} == {
            "profiles",
            "foundation_metadata",
            "approved_plans",
            "approval_idempotency",
            "approval_audit",
            "session_records",
            "session_idempotency",
            "spend_projects",
            "spend_grants",
            "spend_sessions",
            "spend_attempts",
            "spend_pairs",
            "spend_operations",
            "spend_observations",
            "probe_spend_projects",
            "probe_spend_grants",
            "probe_spend_sessions",
            "probe_spend_attempts",
            "probe_spend_pairs",
            "probe_spend_operations",
            "probe_spend_observations",
            "probe_authorities",
        }
