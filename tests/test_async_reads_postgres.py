import asyncio

import httpx
import pytest
from test_identity_profiles import client_for
from test_profile_postgres import approval_repository as approval_repository
from test_profile_postgres import pg_schema as pg_schema
from test_profile_postgres import repository as repository

from future_training.agent.budget import Budget, Deadline, SystemClock
from future_training.api import create_app
from future_training.config import Settings
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.experiments.async_reads import LocalReads, read_context
from future_training.identity import Principal
from future_training.schemas import ProfileSaveRequest

pytestmark = pytest.mark.integration


async def test_typed_parallel_reads_against_actual_api_and_owned_postgres(
    repository, approval_repository, profile
):
    for principal in Principal:
        await repository.save(
            principal,
            ProfileSaveRequest(
                expected_revision=0,
                preferences={**profile, "session_minutes": 20 if principal == Principal.A else 30},
            ),
        )
    app = create_app(
        settings=Settings(local_development="1"), profiles=repository, approvals=approval_repository
    )
    snapshot = await app.state.candidates.publish_initial(
        Principal.A, plan_week(profile, load_catalog()).plan, expected_profile_revision=1
    )
    async with client_for(app) as client:
        approved = await client.post(
            f"/api/v1/drafts/{snapshot.candidate_id}/approve",
            headers={"X-Synthetic-Principal": "synthetic-a"},
            json={**snapshot.identity().model_dump(), "idempotency_key": "f201-setup"},
        )
        assert approved.status_code == 200

    async def owned(principal):
        deadline, budget = Deadline(SystemClock()), Budget()
        async with LocalReads(httpx.ASGITransport(app=app), principal, load_catalog()) as reads:
            async with deadline.scope():
                return await read_context(reads, deadline, budget)

    a, b = await asyncio.gather(owned(Principal.A), owned(Principal.B))
    assert (
        a.profile.preferences.session_minutes == 20 and b.profile.preferences.session_minutes == 30
    )
    assert len(a.history.plans) == 1 and a.history.plans[0].plan == snapshot.proposal()
    assert b.history.plans == () and a.history.unavailable is b.history.unavailable is None
    async with await approval_repository._connect() as connection:
        assert (await (await connection.execute("SELECT count(*) FROM approved_plans")).fetchone())[
            0
        ] == 1
