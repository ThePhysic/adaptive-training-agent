import json

import pytest
from stream_doubles import Exchange
from test_approvals_postgres import rig as rig
from test_identity_profiles import client_for
from test_profile_postgres import pg_schema as pg_schema

from future_training.api import create_app
from future_training.config import Settings

pytestmark = pytest.mark.integration
A = {"X-Synthetic-Principal": "synthetic-a"}
B = {"X-Synthetic-Principal": "synthetic-b"}


def application(rig):
    return create_app(
        settings=Settings(local_development="1"),
        profiles=rig.profiles,
        approvals=rig.database,
        clock=rig.clock,
    )


async def preview(client):
    response = await client.post("/api/v1/drafts/stream", headers=A, json={"profile_revision": 1})
    assert response.status_code == 200
    events = [
        json.loads(frame.split("\ndata: ")[1]) for frame in response.text.strip().split("\n\n")
    ]
    return events[-1]["payload"]["candidate"], next(
        e["payload"] for e in events if e["event_type"] == "draft"
    )


async def test_real_http_approval_readback_history_owner_and_restart(rig, profile):
    app = application(rig)
    async with client_for(app) as client:
        assert (await client.get("/api/v1/plans", headers=A)).json() == []
        candidate, plan = await preview(client)
        path = f"/api/v1/drafts/{candidate['candidate_id']}/approve"
        body = {**candidate, "idempotency_key": "http-key"}
        response = await client.post(path, headers=A, json=body)
        assert response.status_code == 200
        result = response.json()
        saved = await client.get(f"/api/v1/plans/{result['plan_id']}", headers=A)
        assert saved.status_code == 200 and saved.json()["plan"] == plan
        assert saved.json()["approval"] == result
        assert (await client.get("/api/v1/plans?limit=1", headers=A)).json() == [saved.json()]
        assert (
            await client.get(f"/api/v1/plans?cursor={result['plan_id']}", headers=A)
        ).json() == []
        assert (
            await client.get(f"/api/v1/plans/{result['plan_id']}", headers=B)
        ).status_code == 404
        assert (await client.get("/api/v1/plans", headers=B)).json() == []
        assert (await client.post(path, headers=B, json=body)).status_code == 404
        assert (await client.post(path, headers=A, json=body)).json() == result
        assert (
            await client.post(path, headers=A, json={**body, "idempotency_key": "different"})
        ).json()["code"] == "candidate_already_approved"
        assert (
            await client.put(
                "/api/v1/profile",
                headers=A,
                json={"expected_revision": 1, "preferences": {**profile, "session_minutes": 30}},
            )
        ).status_code == 200
        assert (
            await client.get(f"/api/v1/plans/{result['plan_id']}", headers=A)
        ).json() == saved.json()
    restarted = application(rig)
    assert restarted.state.candidates.stats()["lineages"] == 0
    async with client_for(restarted) as client:
        assert (await client.post(path, headers=A, json=body)).json() == result
        mismatch = {**body, "candidate_id": "absent"}
        assert (
            await client.post("/api/v1/drafts/absent/approve", headers=A, json=mismatch)
        ).json()["code"] == "idempotency_mismatch"
    assert await rig.counts() == (1, 1, 1)


async def test_lost_http_response_after_commit_retries_after_store_loss(rig):
    app = application(rig)
    async with client_for(app) as client:
        candidate, _ = await preview(client)
    body = {**candidate, "idempotency_key": "lost-response"}
    path = f"/api/v1/drafts/{candidate['candidate_id']}/approve"

    async def lose_response(message, event):
        if message["type"] == "http.response.body" and b'"plan_id"' in message.get("body", b""):
            raise OSError("Synthetic HTTP response loss")

    exchange = Exchange(app, path=path, body=body, hook=lose_response).start()
    with pytest.raises(OSError):
        await exchange.finish()
    assert await rig.counts() == (1, 1, 1)
    async with client_for(application(rig)) as client:
        recovered = await client.post(path, headers=A, json=body)
        assert recovered.status_code == 200
        assert (
            await client.get(f"/api/v1/plans/{recovered.json()['plan_id']}", headers=A)
        ).status_code == 200
    assert await rig.counts() == (1, 1, 1)


@pytest.mark.parametrize(
    "change",
    [
        {"idempotency_key": ""},
        {"idempotency_key": "x" * 129},
        {"idempotency_key": True},
        {"revision": True},
        {"content_hash": "bad"},
        {"owner_id": "synthetic-b"},
        {"plan": {"fake": "not-authoritative"}},
    ],
)
async def test_http_strict_body_never_accepts_authoritative_plan_or_owner(rig, change):
    app = application(rig)
    async with client_for(app) as client:
        candidate, _ = await preview(client)
        body = {**candidate, "idempotency_key": "key", **change}
        response = await client.post(
            f"/api/v1/drafts/{candidate['candidate_id']}/approve", headers=A, json=body
        )
        assert response.status_code == 422
        assert response.json() == {"code": "invalid_request", "retryable": False}
    assert await rig.counts() == (0, 0, 0)


async def test_http_query_bounds_and_local_boundary_still_fail_closed(rig):
    app = application(rig)
    async with client_for(app) as client:
        candidate, _ = await preview(client)
        body = {**candidate, "idempotency_key": "key"}
        assert (
            await client.post("/api/v1/drafts/another/approve", headers=A, json=body)
        ).status_code == 422
        assert (
            await client.post(f"/api/v1/drafts/{candidate['candidate_id']}/approve", json=body)
        ).status_code == 401
        for query in ("limit=21", "owner_id=synthetic-b", "cursor=../outside"):
            assert (await client.get("/api/v1/plans?" + query, headers=A)).status_code == 422
    disabled = create_app(settings=Settings(), profiles=rig.profiles, approvals=rig.database)
    async with client_for(disabled) as client:
        assert (
            await client.post(
                f"/api/v1/drafts/{candidate['candidate_id']}/approve", headers=A, json=body
            )
        ).status_code == 403
    assert await rig.counts() == (0, 0, 0)
