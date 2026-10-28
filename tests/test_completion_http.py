import json

import httpx
import psycopg
import pytest
from test_observability import CANARIES, assert_private
from test_observability import console as console

from future_training.agent.protocol import ToolCall
from future_training.agent.tools import tool_definitions
from future_training.api import create_app
from future_training.completion_contracts import SessionRecord
from future_training.config import Settings
from future_training.identity import Principal
from future_training.persistence.completions import PostgresCompletions

A = {"X-Synthetic-Principal": "synthetic-a"}
PATH = "/api/v1/plans/synthetic-plan/sessions/1/completion"
BODY = {
    "expected_revision": 0,
    "plan_revision": 1,
    "plan_content_hash": "a" * 64,
    "idempotency_key": "key-a",
    "status": "completed",
}


class Stub:
    def __init__(self):
        self.writes = []

    async def submit(self, principal, plan_id, day_index, request):
        self.writes.append(request)
        return SessionRecord(
            record_id="record",
            plan_id=plan_id,
            day_index=day_index,
            **request.model_dump(exclude={"idempotency_key", "expected_revision"}),
        )

    async def read(self, *args):
        return []


def client(app, peer="127.0.0.1"):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(peer, 1234)), base_url="http://127.0.0.1"
    )


@pytest.mark.parametrize("size,status", [(4096, 200), (4097, 413)])
async def test_exact_body_byte_boundary_including_chunked_data(size, status):
    backend = Stub()
    app = create_app(settings=Settings(local_development="1"), completions=backend)
    raw = json.dumps(BODY).encode()
    raw += b" " * (size - len(raw))

    async def chunks():
        for offset in range(0, len(raw), 257):
            yield raw[offset : offset + 257]

    async with client(app) as transport:
        response = await transport.post(
            PATH, content=chunks(), headers={**A, "Content-Type": "application/json"}
        )
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    assert len(backend.writes) == (1 if status == 200 else 0)


@pytest.mark.parametrize(
    "raw", [b'{"status":"completed","status":"skipped"}', b'{"rating":NaN}', b"\xff"]
)
async def test_ambiguous_nonfinite_or_invalid_utf8_never_reaches_submit(raw):
    backend = Stub()
    app = create_app(settings=Settings(local_development="1"), completions=backend)
    async with client(app) as transport:
        response = await transport.post(
            PATH, content=raw, headers={**A, "Content-Type": "application/json"}
        )
    assert response.status_code == 422 and backend.writes == []


@pytest.mark.parametrize(
    "local,peer,headers,status",
    [
        ("0", "127.0.0.1", A, 403),
        ("1", "192.0.2.1", A, 403),
        ("1", "127.0.0.1", {}, 401),
    ],
)
async def test_new_routes_retain_fail_closed_identity(local, peer, headers, status):
    backend = Stub()
    app = create_app(settings=Settings(local_development=local), completions=backend)
    async with client(app, peer) as transport:
        assert (await transport.post(PATH, json=BODY, headers=headers)).status_code == status
    assert backend.writes == []


async def test_new_routes_and_all_local_sinks_keep_canaries_and_feedback_private(console):
    async def unavailable():
        raise psycopg.OperationalError(" ".join(CANARIES))

    app = create_app(
        settings=Settings(local_development="1"),
        completions=PostgresCompletions(connect=unavailable),
    )
    async with client(app) as transport:
        bad = await transport.post(PATH, json={**BODY, "notes": " ".join(CANARIES)}, headers=A)
        failed = await transport.post(PATH, json=BODY, headers=A)
        read = await transport.get("/api/v1/plans/synthetic-plan/completions", headers=A)
    assert bad.status_code == 422 and failed.status_code == read.status_code == 503
    assert failed.json() == {"code": "internal_error", "retryable": True}
    traces = app.state.tracer.snapshot()
    assert {r["stage"] for r in traces} >= {
        "http",
        "completion.submit",
        "completion.transaction",
        "completion.read",
    }
    output = json.dumps(traces) + console.getvalue() + bad.text + failed.text + read.text
    assert_private(output)
    for forbidden in (
        "plan_id",
        "day_index",
        "rating",
        "effort",
        "plan_content_hash",
        "synthetic-plan",
    ):
        assert forbidden not in output


async def test_session_submit_is_not_an_agent_tool():
    backend = Stub()
    app = create_app(settings=Settings(local_development="1"), completions=backend)
    assert {tool["name"] for tool in tool_definitions()} == {
        "search_exercises",
        "get_user_preferences",
    }
    result = await app.state.agent.tools.dispatch(
        Principal.A,
        None,
        ToolCall(call_id="write-attempt", name="submit_session", arguments_json="{}"),
    )
    assert result.status == "error" and result.error == "unknown_tool" and backend.writes == []
