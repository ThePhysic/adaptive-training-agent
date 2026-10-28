"""Optional installed-browser smoke. Race correctness uses separate fake-clock tests."""

import asyncio
import hashlib
import json
import os
import socket
from pathlib import Path

import httpx
import pytest
import uvicorn
from browser_runner import run_browser
from test_profile_postgres import approval_repository as approval_repository
from test_profile_postgres import pg_schema as pg_schema
from test_profile_postgres import repository as repository

from future_training.api import create_app
from future_training.config import Settings
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.completions import PostgresCompletions
from future_training.readiness import DatabaseCheck

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    not os.environ.get("FATA_BROWSER_EXECUTABLE"), reason="Optional installed-browser smoke"
)
async def test_real_browser_local_save_stream_review_revision_and_owner_switch(
    repository, approval_repository
):
    class InterruptedProfiles:
        failed = False

        async def get(self, principal):
            return await repository.get(principal)

        async def save(self, principal, request):
            if principal == Principal.B and not self.failed:
                self.failed = True
                raise ServiceError(503, "internal_error", retryable=True)
            return await repository.save(principal, request)

    interrupted = InterruptedProfiles()
    # The browser must check its own disposable schema, never the developer DB.
    # pg_schema has already executed these exact migration files.
    async with await approval_repository._connect() as connection:
        await connection.execute("CREATE TABLE schema_migrations (name text, checksum text)")
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            await connection.execute(
                "INSERT INTO schema_migrations VALUES (%s,%s)",
                (path.name, hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()),
            )
    app = create_app(
        settings=Settings(local_development="1"),
        profiles=interrupted,
        approvals=approval_repository,
        completions=PostgresCompletions(connect=approval_repository._connect),
        database_check=DatabaseCheck(approval_repository._connect),
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host="127.0.0.1",
                port=port,
                log_level="error",
                access_log=False,
                proxy_headers=False,
            )
        )
        task = asyncio.create_task(server.serve(sockets=[listener]))
        try:
            async with asyncio.timeout(5):
                while not server.started:
                    if task.done():
                        task.result()
                    await asyncio.sleep(0)
            base = f"http://127.0.0.1:{port}"
            async with httpx.AsyncClient(trust_env=False, timeout=1) as client:
                assert (await client.get(base + "/health")).status_code == 200
                assert (await client.get(base + "/ready")).status_code == 200
            result = await asyncio.to_thread(
                run_browser,
                ROOT,
                base,
                os.environ["FATA_BROWSER_EXECUTABLE"],
                env={
                    **os.environ,
                    "FATA_BROWSER_EVIDENCE_STAGE": os.environ.get(
                        "FATA_BROWSER_EVIDENCE_STAGE", "f4-03b-r5a-ci"
                    ),
                },
            )
            if result.returncode:
                # Only structural state/status codes; no bodies, DB errors or identities.
                state = {"server_started": server.started, "server_task_done": task.done()}
                async with httpx.AsyncClient(trust_env=False, timeout=1) as client:
                    for path in ("health", "ready"):
                        try:
                            state[path] = (await client.get(base + "/" + path)).status_code
                        except httpx.HTTPError:
                            state[path] = 0
                pytest.fail(result.stdout + result.stderr + json.dumps(state))
            assert '"runtimeErrors":0' in result.stdout
            assert '"sameKeyRetry":true' in result.stdout
            assert '"completionSameKeyRetry":true' in result.stdout
            assert '"mobileErrorRecovery":true' in result.stdout
            assert '"horizontalOverflow":false' in result.stdout
            assert interrupted.failed
            assert (await repository.get(Principal.B)).revision == 1
            assert (await repository.get(Principal.A)).revision == 2
            saved = await app.state.plans.history(Principal.A)
            assert len(saved) == 1 and saved[0].plan.profile.session_minutes == 20
            assert await app.state.plans.history(Principal.B) == ()
            async with await approval_repository._connect() as connection:
                cursor = await connection.execute(
                    "SELECT (SELECT count(*) FROM approved_plans),"
                    "(SELECT count(*) FROM approval_idempotency),"
                    "(SELECT count(*) FROM approval_audit),"
                    "(SELECT count(*) FROM session_records),"
                    "(SELECT count(*) FROM session_idempotency)"
                )
                assert await cursor.fetchone() == (1, 1, 1, 2, 2)
            records = await app.state.completions.read(Principal.A, saved[0].approval.plan_id)
            assert [(r.status, r.effort, r.rating) for r in records] == [
                ("completed", "moderate", 4),
                ("skipped", None, None),
            ]
            print(result.stdout.strip())
            print(
                json.dumps(
                    {
                        "application": "actual_loopback_uvicorn_built_react_native_postgres_fake",
                        "health": 200,
                        "readiness": 200,
                        "approved_plans": 1,
                        "approval_keys": 1,
                        "approval_audits": 1,
                        "session_records": 2,
                        "session_keys": 2,
                        "other_owner_plans": 0,
                    }
                )
            )
        finally:
            server.should_exit = True
            await task
