import asyncio
import json
from pathlib import Path

import pytest
from stream_doubles import Exchange, stream_app
from test_identity_profiles import client_for
from test_streaming import revision, seed, terminal

from future_training.candidates import encode_snapshot
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.schemas import ProfileSaveRequest
from future_training.streaming import MAX_EVENTS, Frames


@pytest.mark.parametrize("revise", [False, True])
async def test_final_deadline_check_occurs_inside_store_mutation_boundary(
    profile, monkeypatch, revise
):
    app = await stream_app(profile)
    old = await seed(app) if revise else None
    publication_read = False
    original = app.state.profiles.get

    async def get(principal):
        value = await original(principal)
        if publication_read:
            # Advance synchronously inside the FINAL awaited read. The watchdog
            # has no scheduling opportunity before mutation; the store callback
            # must reject equality at the deadline without publishing anything.
            app.state.agent.clock.advance(30)
        return value

    monkeypatch.setattr(app.state.profiles, "get", get)

    async def hook(message, event):
        nonlocal publication_read
        if event and event["event_type"] == "draft":
            publication_read = True

    exchange = (
        await Exchange(
            app,
            hook=hook,
            path=f"/api/v1/drafts/{old.candidate_id}/revise/stream"
            if old
            else "/api/v1/drafts/stream",
            body=revision(old) if old else None,
        )
        .start()
        .finish()
    )
    assert terminal(exchange)["error"]["code"] == "budget_exceeded"
    assert app.state.candidates.stats()["lineages"] == int(revise)
    monkeypatch.setattr(app.state.profiles, "get", original)
    if old:
        assert (await app.state.candidates.get(Principal.A, old.candidate_id)) == old
        async with app.state.candidates.revision(Principal.A, old.identity()):
            pass


async def test_initial_sweep_cannot_allow_stale_profile_insertion(profile, monkeypatch):
    app = await stream_app(profile)
    store = app.state.candidates
    original = store.expire

    async def sweep_with_save():
        await original()
        await app.state.profiles.save(
            Principal.A,
            ProfileSaveRequest(expected_revision=1, preferences={**profile, "session_minutes": 30}),
        )

    monkeypatch.setattr(store, "expire", sweep_with_save)
    exchange = await Exchange(app).start().finish()
    assert terminal(exchange)["error"]["code"] == "stale_profile"
    assert store.stats()["lineages"] == 0


async def test_publication_fault_after_draft_is_error_then_done_and_no_candidate(
    profile, monkeypatch
):
    app = await stream_app(profile)

    async def fail(*_, **__):
        raise ServiceError(429, "capacity_exceeded", retryable=True)

    monkeypatch.setattr(app.state.candidates, "publish_initial", fail)
    exchange = await Exchange(app).start().finish()
    assert [e["event_type"] for e in exchange.events][-3:] == ["draft", "error", "done"]
    assert terminal(exchange)["error"] == {"code": "capacity_exceeded", "retryable": True}
    assert app.state.candidates.stats()["lineages"] == 0


async def test_catalog_http_bounds_and_web_locality(profile):
    app = await stream_app(profile)
    headers = {"X-Synthetic-Principal": "synthetic-a"}
    async with client_for(app) as client:
        response = await client.get(
            "/api/v1/exercises?limit=2&goal=general_conditioning&equipment=bodyweight",
            headers=headers,
        )
        assert response.status_code == 200 and len(response.json()) == 2
        assert all(r["mode"] == "timed" and r["equipment"] == "bodyweight" for r in response.json())
        for query in ("limit=21", "owner_id=synthetic-b", "cursor=unknown", "goal=medical"):
            assert (
                await client.get("/api/v1/exercises?" + query, headers=headers)
            ).status_code == 422
        root = await client.get("/")
        assert root.status_code in (200, 503)
        csp = root.headers["content-security-policy"]
        assert "script-src 'self'" in csp and "unsafe-eval" not in csp
        assert (
            await client.get("/", headers={"Origin": "http://hostile.invalid"})
        ).status_code == 403
        assert (await client.get("/assets/../../AGENTS.md")).status_code == 404
    async with client_for(app, address="198.51.100.1") as client:
        assert (await client.get("/")).status_code == 403


async def test_missing_saved_profile_has_no_stream_or_implicit_save(profile):
    app = await stream_app(profile)
    app.state.profiles.rows.clear()
    exchange = await Exchange(app).start().finish()
    assert exchange.status == 404 and exchange.events == []
    assert app.state.profiles.rows == {}


async def test_invalid_identity_source_cannot_publish_before_done_framing(profile, monkeypatch):
    app = await stream_app(profile)
    monkeypatch.setattr(app.state.candidates, "_new_id", lambda: "invalid identity with spaces")
    exchange = await Exchange(app).start().finish()
    assert terminal(exchange)["error"]["code"] == "internal_error"
    assert app.state.candidates.stats()["lineages"] == 0


async def test_server_frame_and_event_caps_are_enforced():
    async def send(_):
        pass

    frames = Frames(send)
    with pytest.raises(ServiceError, match="internal_error"):
        frames.encode(
            "done", {"outcome": "clarify", "fields": ["equipment"], "choices": ["🏋" * 512] * 12}
        )
    for _ in range(MAX_EVENTS):
        await frames.emit("status", {"stage": "context"})
    with pytest.raises(RuntimeError):
        await frames.emit("status", {"stage": "context"})


def test_frontend_plan_fixture_is_the_accepted_baseline_and_server_hash(profile):
    import hashlib

    fixture = json.loads(Path("web/tests/server-plan.json").read_text(encoding="utf-8"))
    plan = plan_week(profile, load_catalog()).plan
    assert fixture["plan"] == plan.model_dump()
    assert fixture["candidate"]["content_hash"] == hashlib.sha256(encode_snapshot(plan)).hexdigest()


@pytest.mark.parametrize("revise", [False, True])
async def test_publication_failure_keeps_admission_and_reservation_until_done(
    profile, monkeypatch, revise
):
    app = await stream_app(profile)
    old = await seed(app) if revise else None
    entered, release = asyncio.Event(), asyncio.Event()

    async def fail(*_, **__):
        raise ServiceError(429, "capacity_exceeded", retryable=True)

    monkeypatch.setattr(
        app.state.candidates, "publish_revision" if revise else "publish_initial", fail
    )

    async def hold_done(message, event):
        if event and event["event_type"] == "done":
            entered.set()
            await release.wait()

    first = Exchange(
        app,
        hook=hold_done,
        path=f"/api/v1/drafts/{old.candidate_id}/revise/stream" if old else "/api/v1/drafts/stream",
        body=revision(old) if old else None,
    ).start()
    await entered.wait()
    second = await Exchange(app).start().finish()
    assert second.status == 429
    if old:
        with pytest.raises(ServiceError, match="revision_in_progress"):
            async with app.state.candidates.revision(Principal.A, old.identity()):
                pytest.fail("Reservation released before terminal error")
    release.set()
    await first.finish()
    assert terminal(first)["outcome"] == "error"
    assert app.state.candidates.stats()["lineages"] == int(revise)
    if old:
        async with app.state.candidates.revision(Principal.A, old.identity()):
            pass
