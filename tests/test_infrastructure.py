"""Offline policy mutations and host-command fakes; no AWS/systemd/firewall calls."""

import importlib.util
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(path):
    spec = importlib.util.spec_from_file_location("infra_test", ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture
def host():
    return module("infra/aws/host/host.py")


def test_sources_and_test_provider_seal():
    check = module("scripts/check_infrastructure.py")
    assert check.inspect_sources()["resource_blocks"] > 20


@pytest.mark.parametrize(
    "body",
    [
        'resource "aws_security_group_ingress_rule" "public" {}',
        'resource "aws_nat_gateway" "idle" {}',
        'data "aws_caller_identity" "account" {}',
        'variable "provider_secret_key" {}',
        'provider "aws" { access_key = "canary" }',
        'module "remote" { source = "https://unapproved.invalid/module" }',
    ],
)
def test_policy_mutations_rejected(tmp_path, body):
    check = module("scripts/check_infrastructure.py")
    (tmp_path / "bad.tf").write_text(body)
    with pytest.raises(ValueError):
        check.inspect_sources(tmp_path)


@pytest.mark.parametrize(
    "body",
    [
        'provider "aws" {}\nrun "bad" { command = plan }',
        'mock_provider "aws" {}\nrun "bad" { command = apply }',
        'mock_provider "aws" {}\nrun "bad" {}',
    ],
)
def test_nonmocked_or_implicit_apply_tests_rejected(tmp_path, body):
    check = module("scripts/check_infrastructure.py")
    (tmp_path / "bad.tftest.hcl").write_text(body)
    with pytest.raises(ValueError):
        check.inspect_sources(tmp_path)


def test_guard_both_families_installs_and_checks_before_release(host, monkeypatch):
    calls = []

    def run(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(
            args, int("-C" in args and len(calls) in (1, 4, 7, 10)), b"", b""
        )

    monkeypatch.setattr(host, "run", run)
    host.guard()
    assert [r[0] for r in calls] == (["iptables"] * 3 + ["ip6tables"] * 3) * 2
    assert "10001" in calls[1] and "127.0.0.0/8" in calls[1]
    assert calls[1][3:6] == ("-I", "OUTPUT", "1")
    assert "999" in calls[7]


def test_failed_guard_never_claims_success(host, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("firewall_unavailable")

    monkeypatch.setattr(host, "run", fail)
    with pytest.raises(RuntimeError):
        host.guard()


@pytest.mark.parametrize(
    "now,accepted",
    [
        ("2030-01-01T00:00:00+00:00", True),
        ("2029-12-31T23:59:59+00:00", False),
        ("2030-01-02T00:00:00+00:00", False),
    ],
)
def test_execution_window_exact_boundaries(host, now, accepted):
    config = {"starts_at": "2030-01-01T00:00:00Z", "expires_at": "2030-01-02T00:00:00Z"}
    if accepted:
        host.window(config, datetime.fromisoformat(now))
    else:
        with pytest.raises(RuntimeError):
            host.window(config, datetime.fromisoformat(now))


def test_expired_start_does_not_pull_or_send(host, monkeypatch):
    monkeypatch.setattr(host, "run", lambda *a, **k: pytest.fail("outbound work"))
    with pytest.raises(RuntimeError):
        host.start({"starts_at": "2000-01-01T00:00:00Z", "expires_at": "2000-01-02T00:00:00Z"})


def test_host_subprocess_environment_never_inherits_credentials_or_proxies(host, monkeypatch):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "synthetic-secret-canary")
    monkeypatch.setenv("HTTPS_PROXY", "http://synthetic-credential-canary.invalid")

    def run(args, **kwargs):
        assert "AWS_SECRET_ACCESS_KEY" not in kwargs["env"] and "HTTPS_PROXY" not in kwargs["env"]
        assert kwargs["env"]["AWS_MAX_ATTEMPTS"] == "1"
        assert kwargs["stdin"] == subprocess.DEVNULL
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(host.subprocess, "run", run)
    host.run("synthetic-no-op")


def test_checker_clears_aws_and_injected_terraform_arguments(monkeypatch):
    check = module("scripts/check_infrastructure.py")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "synthetic-canary")
    monkeypatch.setenv("TF_CLI_ARGS_test", "-cloud-run=unexpected")
    monkeypatch.setenv("TF_VAR_account_id", "111111111111")
    monkeypatch.setenv("TF_LOG", "TRACE")
    env = check.clean_env()
    assert not any(
        k in env for k in ("AWS_ACCESS_KEY_ID", "TF_CLI_ARGS_test", "TF_VAR_account_id", "TF_LOG")
    )
    assert env["AWS_EC2_METADATA_DISABLED"] == "true"


def test_tool_attestation_fails_before_host_changes(host, monkeypatch, tmp_path):
    monkeypatch.setattr(host, "Path", lambda p: tmp_path / "manifest")
    (tmp_path / "manifest").write_text("{}")
    monkeypatch.setattr(host, "run", lambda *a, **k: pytest.fail("host mutation"))
    with pytest.raises(RuntimeError):
        host.attest_tools({"host_tools_sha256": "0" * 64})


@pytest.mark.parametrize("version,accepted", [("3.3.4850.0", False), ("3.3.4851.0", True)])
def test_even_pinned_ssm_agent_must_include_security_fix(
    host, monkeypatch, tmp_path, version, accepted
):
    import hashlib
    import json

    expected = {key: "synthetic-version" for key in host.TOOLS}
    expected["ssm"] = "SSM Agent version: " + version
    raw = json.dumps(expected).encode()
    manifest = tmp_path / "manifest"
    manifest.write_bytes(raw)
    monkeypatch.setattr(host, "Path", lambda p: manifest)

    def run(*args):
        key = next(k for k, value in host.TOOLS.items() if value == list(args))
        return subprocess.CompletedProcess(args, 0, expected[key].encode(), b"")

    monkeypatch.setattr(host, "run", run)
    config = {"host_tools_sha256": hashlib.sha256(raw).hexdigest()}
    if accepted:
        host.attest_tools(config)
    else:
        with pytest.raises(RuntimeError):
            host.attest_tools(config)


def test_public_start_routes_through_owned_systemd_unit(host, monkeypatch):
    monkeypatch.setattr(host.platform, "system", lambda: "Linux")
    monkeypatch.setattr(host.os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(host, "config", lambda: {})
    monkeypatch.setattr(host, "window", lambda c: None)
    monkeypatch.setattr(host.sys, "argv", ["host.py", "start"])
    calls = []
    monkeypatch.setattr(host, "run", lambda *a, **k: calls.append(a))
    host.main()
    assert calls == [("systemctl", "start", "fata-release.service")]


@pytest.mark.parametrize("failure", ["login", "pull", "expired_after_pull", "verify"])
def test_start_failure_stops_owned_containers_and_clears_login(
    host, monkeypatch, tmp_path, failure
):
    config = {"registry": "synthetic.invalid"}
    credential = tmp_path / "config.json"
    monkeypatch.setitem(host.ENV, "DOCKER_CONFIG", str(tmp_path))
    monkeypatch.setattr(host, "attest_tools", lambda c: None)
    monkeypatch.setattr(host, "guard", lambda: None)
    monkeypatch.setattr(host, "mount_check", lambda c: None)
    monkeypatch.setattr(host, "verify_daemon", lambda: None)
    calls = []
    windows = []

    def window(c):
        windows.append(c)
        if failure == "expired_after_pull" and len(windows) == 2:
            raise RuntimeError("expired")

    def run(*args, **kwargs):
        if args[:2] == ("docker", "login"):
            credential.write_text("synthetic-credential-canary")
            assert kwargs["data"] == b"synthetic-credential-canary"
            assert "synthetic-credential-canary" not in args
            if failure == "login":
                raise RuntimeError("login_failed")
        return subprocess.CompletedProcess(args, 0, b"synthetic-credential-canary", b"")

    def compose(*args, **kwargs):
        calls.append(args)
        if args == ("pull",) and failure == "pull":
            raise RuntimeError("pull_failed")

    def verify():
        if failure == "verify":
            raise RuntimeError("not_ready")

    monkeypatch.setattr(host, "window", window)
    monkeypatch.setattr(host, "run", run)
    monkeypatch.setattr(host, "compose", compose)
    monkeypatch.setattr(host, "verify", verify)
    with pytest.raises(RuntimeError):
        host.start(config)
    assert calls[-1] == ("stop", "--timeout", "40")
    assert not credential.exists()
    if failure in ("login", "pull", "expired_after_pull"):
        assert not any(row[0] == "up" for row in calls)
