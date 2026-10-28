"""Synthetic process/environment tests; never loads AWS CLI or real credential files."""

import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "infra/aws/fixtures/authentication_probe.py"


def probe():
    spec = importlib.util.spec_from_file_location("offline_auth_fixture", PROBE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "name",
    [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_ROLE_ARN",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
        "AWS_CONFIG_FILE",
        "AWS_SHARED_CREDENTIALS_FILE",
        "AWS_LOGIN_CACHE_DIRECTORY",
        "AWS_ENDPOINT_URL",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "TF_LOG",
        "TF_CLI_ARGS",
    ],
)
def test_synthetic_child_cannot_inherit_credentials_or_redirects(tmp_path, name):
    module = probe()
    env = module.environment(tmp_path, {name: "synthetic-secret-canary", "PATH": "fixture-bin"})
    assert "synthetic-secret-canary" not in env.values()
    assert env["AWS_PROFILE"] == env["AWS_DEFAULT_PROFILE"] == "fixture-process"
    assert env["AWS_EC2_METADATA_DISABLED"] == "true"
    assert env["AWS_CONFIG_FILE"] == str(tmp_path / "config")
    assert env["AWS_SHARED_CREDENTIALS_FILE"] == str(tmp_path / "credentials")
    assert env["HOME"] == env["USERPROFILE"] == str(tmp_path)


@pytest.mark.parametrize("mode", ["valid", "failed", "malformed", "unsupported_version"])
def test_real_child_process_emits_only_synthetic_protocol(tmp_path, mode, capsys, caplog):
    module = probe()
    counter = tmp_path / "count"
    before = datetime.now(UTC)
    result = subprocess.run(
        [sys.executable, str(PROBE), "synthetic-process", mode, str(counter)],
        env=module.environment(tmp_path, {}),
        capture_output=True,
        timeout=5,
    )
    assert counter.read_text() == "invoked\n"
    if mode == "failed":
        assert result.returncode == 1 and not result.stdout
        assert result.stderr.splitlines() == [b"synthetic_process_unavailable"]
    elif mode == "malformed":
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)
    else:
        value = json.loads(result.stdout)
        assert set(value) == {
            "Version",
            "AccessKeyId",
            "SecretAccessKey",
            "SessionToken",
            "Expiration",
        }
        assert value["Version"] == (1 if mode == "valid" else 2)
        assert value["AccessKeyId"] == module.ACCESS and value["SessionToken"] == module.TOKEN
        # Native SDK needs wall time; no sleeps or latency assertion.
        assert datetime.fromisoformat(value["Expiration"]) > before
    assert not capsys.readouterr().out and not caplog.text


def test_native_probe_rejects_nonisolated_execution(monkeypatch):
    module = probe()
    monkeypatch.setattr(module.sys, "platform", "linux")
    monkeypatch.setattr(module.os, "listdir", lambda _: ["lo", "eth0"])
    with pytest.raises(SystemExit, match="network none"):
        module.native()


def test_probe_cannot_select_arbitrary_process_commands():
    source = PROBE.read_text()
    assert "aws.exe" not in source and "export-credentials" not in source
    assert "subprocess.Popen" in source and "start_new_session=True" in source


def test_native_timeout_kills_and_awaits_only_its_owned_group(monkeypatch, tmp_path):
    module = probe()
    calls = []

    class Child:
        pid = 12345

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def communicate(self, timeout=None):
            calls.append(("await", timeout))
            if timeout is not None:
                raise subprocess.TimeoutExpired("synthetic", timeout)
            return b"", b""

    monkeypatch.setattr(module.subprocess, "Popen", lambda *a, **k: Child())
    monkeypatch.setattr(module.signal, "SIGKILL", 9, raising=False)
    monkeypatch.setattr(
        module.os, "killpg", lambda pid, sig: calls.append((pid, sig)), raising=False
    )
    with pytest.raises(RuntimeError, match="offline_auth_timeout"):
        module.run(["synthetic"], tmp_path, {}, timeout=1)
    assert calls == [("await", 1), (12345, 9), ("await", None)]


def test_proposed_read_policy_has_no_write_or_wildcard_authority():
    draft = json.loads(
        (ROOT / "docs/planning/proposals/f4-03b-r1-read-permissions.json").read_text()
    )
    assert draft["Version"] == "2012-10-17"
    statements = draft["Statement"]
    assert len(statements) == 2
    assert {s["Action"] for s in statements} == {"iam:GetUser", "servicequotas:GetServiceQuota"}
    for statement in statements:
        assert statement["Effect"] == "Allow"
        resources = statement["Resource"]
        for resource in [resources] if isinstance(resources, str) else resources:
            assert "*" not in resource and "<APPROVED_ACCOUNT>" in resource
    quotas = next(s for s in statements if s["Action"] == "servicequotas:GetServiceQuota")
    assert len(quotas["Resource"]) == 2
    assert {r.split(":")[-1] for r in quotas["Resource"]} == {"ec2/L-1216C47A", "vpc/L-F678F1CE"}
    assert quotas["Condition"] == {"StringEquals": {"aws:RequestedRegion": "us-east-1"}}
