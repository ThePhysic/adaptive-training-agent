import pytest
from test_identity_profiles import client_for
from test_profile_postgres import approval_repository as approval_repository
from test_profile_postgres import pg_schema as pg_schema
from test_profile_postgres import repository as repository

from future_training.api import create_app
from future_training.config import Settings
from future_training.identity import Principal

pytestmark = pytest.mark.integration


async def test_real_saved_profile_to_stream_and_revision_no_approval_writes(
    repository, approval_repository, profile
):
    app = create_app(
        settings=Settings(local_development="1"), profiles=repository, approvals=approval_repository
    )
    headers = {"X-Synthetic-Principal": "synthetic-a"}
    async with client_for(app) as client:
        saved = await client.put(
            "/api/v1/profile",
            headers=headers,
            json={"expected_revision": 0, "preferences": profile},
        )
        assert saved.status_code == 200
        snapshot = await repository.get(Principal.A)
        first = await client.post(
            "/api/v1/drafts/stream", headers=headers, json={"profile_revision": 1}
        )
        assert first.status_code == 200
        import json

        events = [
            json.loads(block.split("\ndata: ", 1)[1]) for block in first.text.strip().split("\n\n")
        ]
        candidate = events[-1]["payload"]["candidate"]
        assert (
            "candidate_id" not in next(e for e in events if e["event_type"] == "draft")["payload"]
        )
        revised = await client.post(
            f"/api/v1/drafts/{candidate['candidate_id']}/revise/stream",
            headers=headers,
            json={"profile_revision": 1, "candidate": candidate},
        )
        assert revised.status_code == 200 and '"revision":2' in revised.text
        assert (await repository.get(Principal.A)) == snapshot
        history = await client.get("/api/v1/plans", headers=headers)
        assert history.status_code == 200 and history.json() == []
