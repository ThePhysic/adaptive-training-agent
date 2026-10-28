import httpx
import pytest
from profile_doubles import MemoryProfiles

from future_training.api import create_app
from future_training.config import Settings


def client_for(app, *, address="127.0.0.1", url="http://127.0.0.1:8000"):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(address, 12345)), base_url=url
    )


@pytest.fixture
def local_app():
    return create_app(settings=Settings(local_development="1"), profiles=MemoryProfiles())


async def test_requires_explicit_local_opt_in():
    app = create_app(settings=Settings(), profiles=MemoryProfiles())
    async with client_for(app) as client:
        response = await client.get(
            "/api/v1/profile", headers={"X-Synthetic-Principal": "synthetic-a"}
        )
    assert response.status_code == 403
    assert app.state.profiles.rows == {}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Synthetic-Principal": "unknown"},
        [("X-Synthetic-Principal", "synthetic-a"), ("X-Synthetic-Principal", "synthetic-b")],
    ],
)
async def test_no_missing_unknown_or_ambiguous_principal(local_app, headers):
    async with client_for(local_app) as client:
        assert (await client.get("/api/v1/profile", headers=headers)).status_code == 401


@pytest.mark.parametrize(
    "address,url,extra",
    [
        ("198.51.100.1", "http://127.0.0.1:8000", {}),
        ("127.0.0.1", "http://0.0.0.0:8000", {}),
        ("127.0.0.1", "http://127.0.0.1:8000", {"Host": "attacker.invalid"}),
        ("127.0.0.1", "http://127.0.0.1:8000", {"Origin": "http://attacker.invalid"}),
        ("127.0.0.1", "http://127.0.0.1:8000", {"Origin": "null"}),
        ("127.0.0.1", "http://127.0.0.1:8000", {"Origin": "http://127.0.0.1:9999"}),
        ("127.0.0.1", "http://127.0.0.1:8000", {"X-Forwarded-For": "127.0.0.1"}),
        ("127.0.0.1", "http://127.0.0.1:8000", {"Forwarded": "for=127.0.0.1"}),
    ],
)
async def test_nonlocal_rebinding_cross_origin_and_proxy_fail_closed(
    local_app, address, url, extra
):
    async with client_for(local_app, address=address, url=url) as client:
        response = await client.get(
            "/api/v1/profile", headers={"X-Synthetic-Principal": "synthetic-a", **extra}
        )
    assert response.status_code == 403
    assert local_app.state.profiles.rows == {}


@pytest.mark.parametrize(
    "env",
    [
        {"FATA_ENV": "production"},
        {"FATA_LOCAL_DEV": "true"},
        {"FATA_HOST": "0.0.0.0"},
        {"FATA_WORKERS": "2"},
    ],
)
def test_nonlocal_runtime_config_rejected(env):
    with pytest.raises(RuntimeError):
        Settings.from_env(env)


async def test_explicit_save_read_isolation_and_optimistic_conflicts(local_app, profile):
    a, b = {"X-Synthetic-Principal": "synthetic-a"}, {"X-Synthetic-Principal": "synthetic-b"}
    async with client_for(local_app) as client:
        assert (await client.get("/api/v1/profile", headers=a)).status_code == 404
        assert not local_app.state.profiles.rows
        saved = await client.put(
            "/api/v1/profile",
            headers={**a, "Origin": "http://127.0.0.1:8000"},
            json={"expected_revision": 0, "preferences": profile},
        )
        assert saved.status_code == 200 and saved.json()["revision"] == 1
        assert (await client.get("/api/v1/profile", headers=b)).status_code == 404
        assert (
            await client.get("/api/v1/profile?owner_id=synthetic-a", headers=b)
        ).status_code == 422
        modified = {**profile, "session_minutes": 30}
        saved_b = await client.put(
            "/api/v1/profile", headers=b, json={"expected_revision": 0, "preferences": modified}
        )
        assert saved_b.status_code == 200
        assert (await client.get("/api/v1/profile", headers=a)).json()[
            "preferences"
        ] == saved.json()["preferences"]
        conflict = await client.put(
            "/api/v1/profile", headers=a, json={"expected_revision": 0, "preferences": modified}
        )
        assert conflict.status_code == 409 and conflict.json()["code"] == "stale_profile"
        assert (await client.get("/api/v1/profile", headers=b)).json()["preferences"][
            "session_minutes"
        ] == 30
        assert (
            await client.post("/api/v1/drafts/c1/approve", headers=a, json={})
        ).status_code == 422
        assert (await client.get("/api/v1/plans")).status_code == 401


async def test_validation_errors_do_not_echo_input(local_app, profile, capsys):
    async with client_for(local_app) as client:
        headers = {"X-Synthetic-Principal": "synthetic-a"}
        body = {
            "expected_revision": 0,
            "preferences": profile,
            "owner_id": "synthetic-private-canary",
        }
        response = await client.put("/api/v1/profile", headers=headers, json=body)
        assert response.status_code == 422 and response.json()["code"] == "invalid_request"
        assert "synthetic-private-canary" not in response.text
        response = await client.put(
            "/api/v1/profile", headers=headers, content='{"private":"synthetic-private-canary"'
        )
        assert response.status_code == 422 and "synthetic-private-canary" not in response.text
    capture = capsys.readouterr()
    assert "synthetic-private-canary" not in capture.out + capture.err


async def test_chunked_body_cap_is_counted_before_json(local_app):
    async def chunks():
        yield b"x" * 8000
        yield b"x" * 9000

    async with client_for(local_app) as client:
        response = await client.put(
            "/api/v1/profile", headers={"X-Synthetic-Principal": "synthetic-a"}, content=chunks()
        )
    assert response.status_code == 413
    assert local_app.state.profiles.rows == {}
