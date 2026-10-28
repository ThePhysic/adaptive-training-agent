import asyncio

import pytest
from test_identity_profiles import client_for

from future_training.api import create_app
from future_training.config import Settings
from future_training.domain.catalog import load_catalog
from future_training.readiness import check_ready


def assets(tmp_path):
    (tmp_path / "assets").mkdir()
    for path in ("index.html", "assets/app.js", "assets/app.css"):
        (tmp_path / path).write_text("synthetic", encoding="utf-8")
    return tmp_path


async def test_disabled_readiness_never_contacts_database(tmp_path):
    async def forbidden():
        raise AssertionError("Disabled readiness must not connect")

    result = await check_ready(Settings(), load_catalog(), forbidden, assets(tmp_path))
    assert result.status == "unavailable"
    assert not result.checks.local_configuration and not result.checks.database_schema


@pytest.mark.parametrize("available", [True, False])
async def test_dependency_status_does_not_change_liveness(available, tmp_path):
    async def probe():
        return available

    app = create_app(
        settings=Settings(local_development="1"), database_check=probe, web_dist=assets(tmp_path)
    )
    async with client_for(app) as client:
        assert (await client.get("/health")).status_code == 200
        response = await client.get("/ready")
        assert response.status_code == (200 if available else 503)
        assert response.json()["checks"]["database_schema"] is available
        assert response.json()["mode"] == "single_process_synthetic_fake"


async def test_missing_assets_fail_readiness(tmp_path):
    async def probe():
        return True

    result = await check_ready(Settings(local_development="1"), load_catalog(), probe, tmp_path)
    assert result.status == "unavailable" and not result.checks.web_assets


async def test_database_probe_error_is_sanitized(tmp_path):
    async def probe():
        raise RuntimeError("synthetic-private-driver-message")

    result = await check_ready(
        Settings(local_development="1"), load_catalog(), probe, assets(tmp_path)
    )
    assert result.status == "unavailable"
    assert "private-driver" not in result.model_dump_json()


async def test_stalled_dependency_probe_is_cancelled_and_drained(tmp_path):
    entered, cleaned = asyncio.Event(), asyncio.Event()

    async def stalled():
        entered.set()
        try:
            await asyncio.Future()
        finally:
            cleaned.set()

    task = asyncio.create_task(
        check_ready(Settings(local_development="1"), load_catalog(), stalled, assets(tmp_path))
    )
    await entered.wait()
    assert (await task).status == "unavailable"
    assert cleaned.is_set()
