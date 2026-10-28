import asyncio
import json

import pytest
from agent_doubles import Hanging, valid_final
from pydantic import TypeAdapter
from stream_doubles import Exchange, stream_app
from test_identity_profiles import client_for

from future_training.agent.fake import ScriptedFake, response_bytes
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.schemas import ProfileSaveRequest, StreamEvent
from future_training.streaming import MAX_FRAME_BYTES, Frames


def terminal(exchange):
    return exchange.events[-1]["payload"]


def revision(snapshot):
    return {
        "profile_revision": snapshot.profile_revision,
        "candidate": snapshot.identity().model_dump(),
    }


async def seed(app):
    exchange = await Exchange(app).start().finish()
    identity = terminal(exchange)["candidate"]
    return await app.state.candidates.get(Principal.A, identity["candidate_id"])


@pytest.mark.parametrize("spec", ["2.0", "2.4"])
async def test_actual_post_stream_framing_and_owned_terminal_publication(profile, spec):
    app = await stream_app(profile)

    async def hook(message, event):
        if event and event["event_type"] == "draft":
            assert app.state.candidates.stats()["lineages"] == 0
            assert "candidate" not in event["payload"]
            assert b"candidate_id" not in message["body"]
        if event and event["event_type"] == "done":
            assert app.state.candidates.stats()["lineages"] == 1

    exchange = await Exchange(app, hook=hook, spec=spec).start().finish()
    assert exchange.status == 200
    headers = dict(exchange.messages[0]["headers"])
    assert headers[b"content-type"].startswith(b"text/event-stream")
    assert headers[b"cache-control"] == b"no-store"
    assert b"content-length" not in headers
    assert [e["sequence"] for e in exchange.events] == list(range(len(exchange.events)))
    assert len({e["request_id"] for e in exchange.events}) == 1
    assert all(e["schema_version"] == "1" for e in exchange.events)
    assert [e["event_type"] for e in exchange.events].count("draft") == 1
    assert [e["event_type"] for e in exchange.events].count("done") == 1
    for event in exchange.events:
        TypeAdapter(StreamEvent).validate_python(event)
    for message in exchange.messages[1:-1]:
        assert len(message["body"]) <= MAX_FRAME_BYTES
        assert message["body"].endswith(b"\n\n")
    snapshot = await app.state.candidates.get(
        Principal.A, terminal(exchange)["candidate"]["candidate_id"]
    )
    assert snapshot.identity().model_dump() == terminal(exchange)["candidate"]
    with pytest.raises(ServiceError, match="not_found"):
        await app.state.candidates.get(Principal.B, snapshot.candidate_id)


@pytest.mark.parametrize("outcome", ["clarify", "abstain", "error"])
async def test_nonplan_outcomes_have_no_preview_or_candidate(profile, outcome, caplog):
    provider = None
    body = {"profile_revision": 1}
    if outcome == "clarify":
        body["preferences_text"] = "SYNTHETIC_PRIVATE_CANARY"
    elif outcome == "abstain":
        provider = ScriptedFake([lambda r: response_bytes(r, kind="refusal", reason="policy")])
    else:
        provider = ScriptedFake([b"malformed SYNTHETIC_PRIVATE_CANARY"])
    app = await stream_app(profile, provider=provider)
    exchange = await Exchange(app, body=body).start().finish()
    assert terminal(exchange)["outcome"] == outcome
    assert not any(e["event_type"] == "draft" for e in exchange.events)
    assert any(e["event_type"] == "error" for e in exchange.events) == (outcome == "error")
    assert b"SYNTHETIC_PRIVATE_CANARY" not in exchange.body
    assert "SYNTHETIC_PRIVATE_CANARY" not in caplog.text
    assert app.state.candidates.stats()["lineages"] == 0


@pytest.mark.parametrize(
    "body,status",
    [
        ({"profile_revision": 2}, 409),
        ({"profile_revision": True}, 422),
        ({"profile_revision": 1, "owner_id": "synthetic-b"}, 422),
    ],
)
async def test_preheader_validation_uses_ordinary_http(profile, body, status):
    app = await stream_app(profile)
    exchange = await Exchange(app, body=body).start().finish()
    assert exchange.status == status
    assert not exchange.events
    assert json.loads(exchange.body)["code"] in ("invalid_request", "stale_profile")
    assert app.state.candidates.stats()["lineages"] == 0


async def test_httpx_route_identity_body_cap_and_no_replay(profile):
    app = await stream_app(profile)
    async with client_for(app) as client:
        headers = {"X-Synthetic-Principal": "synthetic-a"}
        assert (
            await client.post("/api/v1/drafts/stream", json={"profile_revision": 1})
        ).status_code == 401
        assert (
            await client.post(
                "/api/v1/drafts/stream",
                headers={**headers, "Origin": "http://hostile.invalid"},
                json={"profile_revision": 1},
            )
        ).status_code == 403
        assert (
            await client.post("/api/v1/drafts/stream", headers=headers, content=b"x" * 16385)
        ).status_code == 413
        assert (
            await client.post(
                "/api/v1/drafts/stream?replay=1", headers=headers, json={"profile_revision": 1}
            )
        ).status_code == 422
        assert (
            await client.post(
                "/api/v1/drafts/stream",
                headers={**headers, "Last-Event-ID": "old"},
                json={"profile_revision": 1},
            )
        ).status_code == 422
        response = await client.post(
            "/api/v1/drafts/stream", headers=headers, json={"profile_revision": 1}
        )
        assert response.status_code == 200
        assert b"event: done" in response.content
        assert (
            await client.post("/api/v1/drafts/missing/approve", headers=headers, json={})
        ).status_code == 422
        assert (await client.get("/api/v1/plans")).status_code == 401


async def test_revision_new_identity_single_success_and_path_owner_hash_enforcement(profile):
    app = await stream_app(profile)
    old = await seed(app)
    path = f"/api/v1/drafts/{old.candidate_id}/revise/stream"
    before = app.state.candidates.stats()
    other = (
        await Exchange(app, path=path, body=revision(old), principal="synthetic-b").start().finish()
    )
    assert other.status == 404 and not other.events
    forged = revision(old)
    forged["candidate"]["content_hash"] = "0" * 64
    mismatch = await Exchange(app, path=path, body=forged).start().finish()
    assert mismatch.status == 409
    wrong_path = (
        await Exchange(app, path="/api/v1/drafts/another/revise/stream", body=revision(old))
        .start()
        .finish()
    )
    assert wrong_path.status == 422
    assert app.state.candidates.stats() == before
    revised = await Exchange(app, path=path, body=revision(old)).start().finish()
    assert terminal(revised)["outcome"] == "plan"
    candidate = terminal(revised)["candidate"]
    assert candidate["revision"] == 2 and candidate["candidate_id"] != old.candidate_id
    with pytest.raises(ServiceError, match="candidate_superseded"):
        await app.state.candidates.get(Principal.A, old.candidate_id)
    snapshot = await app.state.candidates.get(Principal.A, candidate["candidate_id"])
    again = (
        await Exchange(
            app,
            path=f"/api/v1/drafts/{snapshot.candidate_id}/revise/stream",
            body=revision(snapshot),
        )
        .start()
        .finish()
    )
    assert terminal(again)["outcome"] == "error"
    assert terminal(again)["error"]["code"] == "candidate_mismatch"


@pytest.mark.parametrize("point", ["before_draft", "draft_send", "after_draft"])
async def test_disconnect_before_terminalization_never_publishes(profile, point):
    hanging = Hanging()
    app = await stream_app(
        profile, provider=ScriptedFake([hanging]) if point == "before_draft" else None
    )
    entered, release = asyncio.Event(), asyncio.Event()

    async def hook(message, event):
        if event and event["event_type"] == "draft":
            entered.set()
            if point == "draft_send":
                await release.wait()
            elif point == "after_draft":
                exchange.disconnect()

    exchange = Exchange(app, hook=hook).start()
    if point == "before_draft":
        await hanging.started.wait()
    else:
        await entered.wait()
    exchange.disconnect()
    await exchange.finish()
    assert app.state.candidates.stats()["lineages"] == 0
    assert not exchange.seen["done"].is_set()
    assert not app.state.agent.clock.waiters
    if point == "before_draft":
        assert hanging.cleaned.is_set()
    app.state.agent.provider = ScriptedFake([valid_final])
    assert terminal(await Exchange(app).start().finish())["outcome"] == "plan"


async def test_lost_terminal_delivery_leaves_only_an_undisclosed_orphan(profile):
    app = await stream_app(profile)

    async def lose_done(message, event):
        if event and event["event_type"] == "done":
            assert app.state.candidates.stats()["lineages"] == 1
            raise OSError("Synthetic connection lost")

    exchange = await Exchange(app, hook=lose_done).start().finish()
    assert exchange.seen["draft"].is_set()
    assert not exchange.seen["done"].is_set()
    assert b"candidate_id" not in exchange.body
    assert app.state.candidates.stats()["lineages"] == 1
    app.state.agent.clock.advance(1800)
    await app.state.candidates.expire()
    assert app.state.candidates.stats()["lineages"] == 0


@pytest.mark.parametrize("stop", ["disconnect", "external_cancel", "deadline"])
async def test_cancelled_revision_cleans_up_and_preserves_original(profile, stop):
    app = await stream_app(profile)
    old = await seed(app)
    hanging = Hanging()
    app.state.agent.provider = ScriptedFake([hanging])
    exchange = Exchange(
        app, path=f"/api/v1/drafts/{old.candidate_id}/revise/stream", body=revision(old)
    ).start()
    await hanging.started.wait()
    if stop == "disconnect":
        exchange.disconnect()
        exchange.disconnect()  # Repeated browser Stop is harmless.
        await exchange.finish()
    elif stop == "external_cancel":
        exchange.task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await exchange.finish()
    else:
        app.state.agent.clock.advance(30)
        await exchange.finish()
        assert terminal(exchange)["outcome"] == "error"
        assert terminal(exchange)["error"]["code"] == "budget_exceeded"
    assert hanging.cleaned.is_set()
    assert not app.state.agent.clock.waiters
    assert (await app.state.candidates.get(Principal.A, old.candidate_id)) == old
    app.state.agent.provider = ScriptedFake([valid_final])
    retry = (
        await Exchange(
            app, path=f"/api/v1/drafts/{old.candidate_id}/revise/stream", body=revision(old)
        )
        .start()
        .finish()
    )
    assert terminal(retry)["candidate"]["revision"] == 2


async def test_expiry_during_revision_generation_no_new_candidate(profile):
    app = await stream_app(profile)
    old = await seed(app)
    clock = app.state.agent.clock
    clock.advance(old.expires_at_monotonic - clock.now() - 10)
    hanging = Hanging()
    app.state.agent.provider = ScriptedFake([hanging])
    exchange = Exchange(
        app, path=f"/api/v1/drafts/{old.candidate_id}/revise/stream", body=revision(old)
    ).start()
    await hanging.started.wait()
    clock.advance(10)
    hanging.release.set()
    await exchange.finish()
    assert terminal(exchange)["error"]["code"] == "candidate_expired"
    assert app.state.candidates.stats()["lineages"] == 0


async def test_profile_save_after_preview_is_rechecked_at_publication(profile):
    app = await stream_app(profile)

    async def save_after_preview(message, event):
        if event and event["event_type"] == "draft":
            await app.state.profiles.save(
                Principal.A,
                ProfileSaveRequest(
                    expected_revision=1, preferences={**profile, "session_minutes": 30}
                ),
            )

    exchange = await Exchange(app, hook=save_after_preview).start().finish()
    assert terminal(exchange)["error"]["code"] == "stale_profile"
    assert exchange.seen["draft"].is_set()
    assert app.state.candidates.stats()["lineages"] == 0


async def test_backpressure_deadline_does_not_publish(profile):
    app = await stream_app(profile)
    entered = asyncio.Event()

    async def hang_draft(message, event):
        if event and event["event_type"] == "draft":
            entered.set()
            await asyncio.Event().wait()

    exchange = Exchange(app, hook=hang_draft).start()
    await entered.wait()
    app.state.agent.clock.advance(30)
    await exchange.finish()
    assert terminal(exchange)["error"]["code"] == "budget_exceeded"
    assert app.state.candidates.stats()["lineages"] == 0


async def test_stream_admission_held_through_terminal_send(profile):
    app = await stream_app(profile)
    entered, release = asyncio.Event(), asyncio.Event()

    async def hold_done(message, event):
        if event and event["event_type"] == "done":
            entered.set()
            await release.wait()

    first = Exchange(app, hook=hold_done).start()
    await entered.wait()
    second = await Exchange(app).start().finish()
    assert second.status == 429 and not second.events
    other = await Exchange(app, principal="synthetic-b").start().finish()
    assert terminal(other)["outcome"] == "plan"
    release.set()
    await first.finish()
    assert terminal(await Exchange(app).start().finish())["outcome"] == "plan"


async def test_writer_rejects_bad_order_and_oversize():
    async def send(_):
        pass

    frames = Frames(send)
    with pytest.raises(RuntimeError):
        frames.encode("done", {"outcome": "plan", "candidate": {}})
    await frames.emit("error", {"code": "provider_failure", "retryable": False})
    with pytest.raises(RuntimeError):
        frames.encode("draft", {})
    with pytest.raises(RuntimeError):
        frames.encode("done", {"outcome": "clarify", "fields": ["equipment"], "choices": ["x"]})
    await frames.emit(
        "done", {"outcome": "error", "error": {"code": "provider_failure", "retryable": False}}
    )
    with pytest.raises(RuntimeError):
        frames.encode("status", {"stage": "context"})
