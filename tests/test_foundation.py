import importlib.util
import json
import socket
from pathlib import Path

import httpx
import pytest

from future_training.api import create_app
from future_training.config import Settings


async def test_local_asgi_startup_and_disabled_business_access():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        assert (await client.get("/health")).json() == {"status": "alive", "stage": "F1-07"}
        assert (await client.get("/ready")).status_code == 503
        assert (await client.get("/api/v1/profile")).status_code == 403
        assert (await client.post("/api/v1/drafts/c1/approve", json={})).status_code == 403


def test_credentials_alone_have_no_effect(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-canary-not-a-real-key")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://198.51.100.1")
    assert Settings.from_env().provider == "fake"
    create_app()
    assert importlib.util.find_spec("openai") is None
    assert importlib.util.find_spec("opentelemetry.exporter") is None


@pytest.mark.parametrize(
    "name,value",
    [
        ("FATA_HOST", "0.0.0.0"),
        ("FATA_WORKERS", "2"),
        ("FATA_PROVIDER", "live"),
        ("FATA_TELEMETRY_EXPORTER", "otlp"),
    ],
)
def test_unsafe_settings_fail_closed(name, value):
    with pytest.raises(RuntimeError, match="Unsupported F1-01 configuration"):
        Settings.from_env({name: value})


def test_external_network_and_dns_are_blocked():
    from pytest_socket import SocketConnectBlockedError

    with socket.socket() as connection:
        with pytest.warns(UserWarning, match="A test tried to use"):
            with pytest.raises(SocketConnectBlockedError):
                connection.connect(("198.51.100.1", 443))
    with pytest.raises(OSError, match="External DNS disabled"):
        socket.getaddrinfo("external.invalid", 443)


def test_generated_contract_is_marked_specification_only():
    spec = json.loads(Path("contracts/openapi.json").read_text(encoding="utf-8"))
    for path, operations in spec["paths"].items():
        for operation in operations.values():
            expected = "implemented-foundation"
            if path.startswith("/api/"):
                expected = "implemented-local"
            assert operation["x-implementation"] == expected
    approval = spec["paths"]["/api/v1/drafts/{candidate_id}/approve"]["post"]
    assert "AGAIN after guard wait" in approval["description"]


def test_all_openapi_component_references_resolve():
    spec = json.loads(Path("contracts/openapi.json").read_text(encoding="utf-8"))

    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                target = spec
                for part in value["$ref"].removeprefix("#/").split("/"):
                    target = target[part]
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(spec)
