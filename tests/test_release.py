import errno
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


def release_module():
    path = Path(__file__).resolve().parents[1] / "scripts/check_release.py"
    spec = importlib.util.spec_from_file_location("release_drill", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_drill_uses_explicit_images_without_retagging_historical_builds(monkeypatch):
    monkeypatch.setenv("FATA_RELEASE_IMAGE", "fata-release:f5-d1")
    monkeypatch.setenv("FATA_RELEASE_BASELINE_IMAGE", "fata-release:f5-d1-baseline")
    module = release_module()
    assert module.IMAGE == "fata-release:f5-d1"
    assert module.BASELINE_IMAGE == "fata-release:f5-d1-baseline"
    calls = []
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    module.compose("fata-f5-test", "up", "--pull", "never")
    assert calls[0][1]["env"]["FATA_RELEASE_IMAGE"] == "fata-release:f5-d1"
    assert calls[0][0][-2:] == ("--pull", "never")


@pytest.mark.parametrize("busy_port", [8000, 55432])
def test_release_waits_for_delayed_port_release_without_address_reuse(monkeypatch, busy_port):
    module = release_module()
    clock, opened = [0.0], []

    class Probe:
        def __enter__(self):
            opened.append(self)
            return self

        def __exit__(self, *args):
            opened.remove(self)

        def bind(self, address):
            if address[1] == busy_port and clock[0] < 0.5:
                raise OSError(errno.EADDRINUSE, "synthetic close-state hold")

        def setsockopt(self, *args):
            pytest.fail("Release must not enable address reuse")

    monkeypatch.setattr(module.socket, "socket", Probe)

    def pause(duration):
        assert not opened  # Partial reservations are released before waiting.
        clock[0] += duration

    module.require_free_ports(timeout=1, now=lambda: clock[0], pause=pause)
    assert clock[0] == 0.5 and not opened


@pytest.mark.parametrize("busy_port", [8000, 55432])
def test_release_refuses_persistent_owner_and_reports_exact_port(monkeypatch, busy_port):
    module = release_module()
    clock = [0.0]

    class Probe:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def bind(self, address):
            if address[1] == busy_port:
                raise OSError(errno.EADDRINUSE, "synthetic live listener")

    monkeypatch.setattr(module.socket, "socket", Probe)
    monkeypatch.setattr(
        module.subprocess, "run", lambda *a, **k: pytest.fail("No cleanup of an owner")
    )
    with pytest.raises(OSError, match=f"127.0.0.1:{busy_port}") as error:
        module.require_free_ports(
            timeout=1,
            now=lambda: clock[0],
            pause=lambda delay: clock.__setitem__(0, clock[0] + delay),
        )
    assert error.value.errno == errno.EADDRINUSE and clock[0] == 1


def test_release_other_bind_errors_fail_immediately(monkeypatch):
    module = release_module()

    class Probe:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def bind(self, address):
            raise OSError(errno.EACCES, "synthetic permission denied")

    monkeypatch.setattr(module.socket, "socket", Probe)
    with pytest.raises(OSError) as error:
        module.require_free_ports(pause=lambda _: pytest.fail("Must not retry a permissions error"))
    assert error.value.errno == errno.EACCES


@pytest.mark.parametrize(
    "changes", [{}, {"FATA_HOST": "0.0.0.0"}, {"FATA_PROVIDER": "live"}, {"FATA_WORKERS": "2"}]
)
def test_release_default_or_unsafe_configuration_never_binds(changes):
    env = {
        **os.environ,
        "FATA_RELEASE_ACK": "local-synthetic-only",
        "FATA_LOCAL_DEV": "1",
        "FATA_HOST": "127.0.0.1",
        "FATA_PROVIDER": "fake",
        "FATA_WORKERS": "1",
    }
    if not changes:
        env.pop("FATA_RELEASE_ACK")
    result = subprocess.run(
        [sys.executable, "scripts/release.py", "serve"],
        env={**env, **changes},
        capture_output=True,
        timeout=4,
    )
    assert result.returncode != 0 and b"Traceback" not in result.stderr


def test_fake_generation_does_not_import_optional_http_transports():
    code = """import asyncio,builtins,sys
sys.path.insert(0,'src')
original=builtins.__import__
def blocked(name,*args,**kwargs):
 if name=='httpx' or name.startswith('httpx.'):
  raise AssertionError('Dev transport in fake runtime')
 return original(name,*args,**kwargs)
builtins.__import__=blocked
from future_training.agent.orchestration import Agent
from future_training.domain.catalog import load_catalog
from future_training.identity import Principal
from future_training.schemas import SavedProfile,GenerateRequest
class Profiles:
 async def get(self,principal):
  return SavedProfile(revision=1,preferences=dict(
   adult=True,goal='general_strength',equipment='bodyweight',
   experience='beginner',days_per_week=2,session_minutes=20))
async def main():
 agent=Agent(Profiles(),load_catalog())
 result=await agent.generate(Principal.A,GenerateRequest(profile_revision=1))
 assert result.output().outcome=='plan'
asyncio.run(main(),loop_factory=asyncio.SelectorEventLoop)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
