import asyncio
import hashlib
import json
import os
from pathlib import Path

import psycopg
import pytest
from test_approvals_postgres import rig as rig
from test_identity_profiles import client_for
from test_profile_postgres import approval_repository as approval_repository
from test_profile_postgres import pg_schema as pg_schema
from test_profile_postgres import repository as repository
from test_readiness import assets

from future_training.api import create_app
from future_training.config import Settings
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.profiles import PostgresProfiles
from future_training.readiness import DatabaseCheck

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]
A = {"X-Synthetic-Principal": "synthetic-a"}
B = {"X-Synthetic-Principal": "synthetic-b"}


@pytest.mark.parametrize("fault", ["none", "missing_history", "checksum", "missing_table"])
async def test_real_readiness_schema_checks_and_recovery(pg_schema, fault, tmp_path):
    async def connect():
        return await psycopg.AsyncConnection.connect(pg_schema[1])

    async with await connect() as connection:
        if fault != "missing_history":
            await connection.execute("CREATE TABLE schema_migrations (name text, checksum text)")
            for path in sorted((ROOT / "migrations").glob("*.sql")):
                checksum = hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
                await connection.execute(
                    "INSERT INTO schema_migrations VALUES (%s,%s)",
                    (path.name, "wrong" if fault == "checksum" else checksum),
                )
        if fault == "missing_table":
            await connection.execute("ALTER TABLE profiles RENAME TO profiles_missing")
    app = create_app(
        settings=Settings(local_development="1"),
        database_check=DatabaseCheck(connect),
        web_dist=assets(tmp_path),
    )
    async with client_for(app) as client:
        assert (await client.get("/health")).status_code == 200
        response = await client.get("/ready")
        assert response.status_code == (200 if fault == "none" else 503)
        assert response.json()["checks"]["database_schema"] is (fault == "none")
        if fault == "checksum":
            async with await connect() as connection:
                for path in sorted((ROOT / "migrations").glob("*.sql")):
                    await connection.execute(
                        "UPDATE schema_migrations SET checksum=%s WHERE name=%s",
                        (
                            hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest(),
                            path.name,
                        ),
                    )
            assert (await client.get("/ready")).status_code == 200


async def test_actual_database_connection_interruption_recovers_without_state_loss(rig):
    entered, release = asyncio.Event(), asyncio.Event()
    connection = await psycopg.AsyncConnection.connect(rig.dsn)

    async def connect_once():
        entered.set()
        await release.wait()
        return connection

    broken = PostgresProfiles(load_catalog(), connect=connect_once)
    task = asyncio.create_task(broken.get(Principal.A))
    await entered.wait()
    async with await psycopg.AsyncConnection.connect(rig.dsn) as admin:
        assert (
            await (
                await admin.execute(
                    "SELECT pg_terminate_backend(%s)", (connection.info.backend_pid,)
                )
            ).fetchone()
        )[0]
    release.set()
    with pytest.raises(ServiceError, match="internal_error"):
        await task
    assert (await rig.profiles.get(Principal.A)).revision == 1
    assert await rig.counts() == (0, 0, 0)


def terminal(response):
    return json.loads(response.text.strip().split("\n\n")[-1].split("\ndata: ")[1])["payload"]


async def test_actual_http_vertical_slice_has_owned_sql_and_trace_evidence(
    repository, approval_repository, profile
):
    app = create_app(
        settings=Settings(local_development="1"), profiles=repository, approvals=approval_repository
    )
    async with client_for(app) as client:
        assert (
            await client.put(
                "/api/v1/profile", headers=A, json={"expected_revision": 0, "preferences": profile}
            )
        ).status_code == 200
        initial = terminal(
            await client.post("/api/v1/drafts/stream", headers=A, json={"profile_revision": 1})
        )["candidate"]
        revised = terminal(
            await client.post(
                f"/api/v1/drafts/{initial['candidate_id']}/revise/stream",
                headers=A,
                json={"profile_revision": 1, "candidate": initial},
            )
        )["candidate"]
        approved = await client.post(
            f"/api/v1/drafts/{revised['candidate_id']}/approve",
            headers=A,
            json={**revised, "idempotency_key": "vertical-slice"},
        )
        saved_path = f"/api/v1/plans/{approved.json()['plan_id']}"
        saved = (await client.get(saved_path, headers=A)).json()
        assert (await client.get("/api/v1/plans", headers=A)).json() == [saved]
        assert (await client.get(saved_path, headers=B)).status_code == 404
        await client.put(
            "/api/v1/profile",
            headers=A,
            json={"expected_revision": 1, "preferences": {**profile, "session_minutes": 30}},
        )
        assert (await client.get(saved_path, headers=A)).json() == saved
    records = app.state.tracer.snapshot()
    stages = {r["stage"] for r in records}
    assert stages >= {
        "http",
        "profile.save",
        "agent.execute",
        "provider",
        "tool",
        "validation",
        "candidate.initial",
        "candidate.revision",
        "approval.transaction",
        "plan.read",
    }
    approval_trace = [r for r in records if r["trace_id"] == approved.headers["x-request-id"]]
    assert {r["stage"] for r in approval_trace} >= {
        "approval",
        "approval.lookup",
        "approval.transaction",
        "validation",
        "http",
    }
    all_ids = {r["span_id"] for r in records}
    assert all(r["parent_id"] in all_ids for r in records if r["parent_id"])
    assert "synthetic-a" not in json.dumps(records)
    if os.environ.get("FATA_WRITE_EVIDENCE") == "1":
        (ROOT / "docs/implementation/evidence/f1-07-vertical-trace.json").write_text(
            json.dumps(records, indent=2) + "\n", encoding="utf-8"
        )
