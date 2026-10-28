"""Bounded local dependency readiness; never a production readiness certificate."""

import asyncio
import hashlib
from pathlib import Path
from typing import Literal

from future_training.observability import annotate, traced
from future_training.persistence.profiles import connect_local
from future_training.schemas import Contract

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"


class DependencyChecks(Contract):
    local_configuration: bool
    database_schema: bool
    catalog: bool
    web_assets: bool


class ReadinessStatus(Contract):
    status: Literal["ready_local", "unavailable"]
    mode: Literal["single_process_synthetic_fake"] = "single_process_synthetic_fake"
    checks: DependencyChecks


class DatabaseCheck:
    def __init__(self, connect=connect_local):
        self.connect = connect

    async def __call__(self):
        async with asyncio.timeout(2), await self.connect() as connection:
            await connection.execute("SET TRANSACTION READ ONLY")
            await connection.execute("SET LOCAL statement_timeout='1000ms'")
            await connection.execute("SET LOCAL lock_timeout='500ms'")
            cursor = await connection.execute("SELECT name,checksum FROM schema_migrations")
            actual = dict(await cursor.fetchall())
            expected = {
                path.name: hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
                for path in sorted((ROOT / "migrations").glob("*.sql"))
            }
            if actual != expected:
                return False
            # Verify required columns/permissions too, without reading user rows.
            await connection.execute("SELECT owner_id,revision,preferences FROM profiles LIMIT 0")
            await connection.execute(
                "SELECT p.plan_id,p.owner_id,p.candidate_id,p.candidate_revision,p.content_hash,"
                "p.profile_revision,p.catalog_revision,p.validator_revision,p.plan_bytes,"
                "k.operation,k.idempotency_key,k.fingerprint,a.approved_at "
                "FROM approved_plans p JOIN approval_idempotency k "
                "ON k.owner_id=p.owner_id AND k.plan_id=p.plan_id "
                "JOIN approval_audit a ON a.owner_id=p.owner_id AND a.plan_id=p.plan_id LIMIT 0"
            )
            await connection.execute(
                "SELECT r.record_id,r.owner_id,r.plan_id,r.day_index,r.revision,r.plan_revision,"
                "r.plan_content_hash,r.status,r.effort,r.rating,r.submitted_at,k.fingerprint "
                "FROM session_records r JOIN session_idempotency k "
                "ON k.owner_id=r.owner_id AND k.record_id=r.record_id LIMIT 0"
            )
            return True


@traced("readiness")
async def check_ready(settings, catalog, database_check, assets=WEB_DIST):
    local = settings.local_development == "1" and settings.provider == "fake"
    database = False
    if local:
        try:
            async with asyncio.timeout(3):
                database = await database_check() is True
        except Exception:
            database = False
    checks = DependencyChecks(
        local_configuration=local,
        database_schema=database,
        catalog=len(catalog.ids) > 0,
        web_assets=all(
            (assets / name).is_file() for name in ("index.html", "assets/app.js", "assets/app.css")
        ),
    )
    ready = all(checks.model_dump().values())
    annotate(
        outcome="ok" if ready else "error",
        reason="dependency_unavailable" if not ready else "validated_unpublished",
    )
    return ReadinessStatus(status="ready_local" if ready else "unavailable", checks=checks)
