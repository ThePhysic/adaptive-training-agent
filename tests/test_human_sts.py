"""A1a synthetic protocol/process/storage checks; no AWS CLI or real credentials."""

import hashlib
import importlib.util
import json
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Thread

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sts(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    spec = importlib.util.spec_from_file_location("human_sts", ROOT / "infra/aws/human_sts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def expected():
    return {
        "Account": "000000000000",
        "Arn": "arn:aws:iam::000000000000:user/future-f4-human-admin",
        "UserId": "AIDASYNTHETIC000000001",
    }


@pytest.fixture
def now():
    return datetime(2030, 1, 1, tzinfo=UTC)


@pytest.fixture
def manifest(sts, expected, now, tmp_path):
    executable = tmp_path / "aws.exe"
    executable.write_bytes(b"not an executable; synthetic binary attestation only")
    return {
        "expected": expected,
        "profile": sts.PROFILE,
        "region": sts.REGION,
        "endpoint": sts.ENDPOINT,
        "window_start": now.isoformat().replace("+00:00", "Z"),
        "window_end": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "session_expires_at": (now + timedelta(minutes=15)).isoformat().replace("+00:00", "Z"),
        "cli_path": str(executable),
        "cli_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
    }


def configuration(sts, expected):
    return f"[profile {sts.PROFILE}]\nregion = {sts.REGION}\nlogin_session = {expected['Arn']}\n"


def policy(sts, *, claim=True):
    value = sts.runner.local("infra/aws/fixtures/sts_tunnel.py").TunnelPolicy(lambda: None)
    if claim:
        assert value.claim("CONNECT", "sts.us-east-1.amazonaws.com:443")
    return value


def capture(sts, body, code=0, status="completed", stderr=b""):
    return sts.runner.Capture(code, status, bytearray(body), bytearray(stderr))


def test_fixed_command_has_no_substitution_surface(sts, manifest):
    args = sts.command(manifest["cli_path"])
    assert args == (
        manifest["cli_path"],
        "sts",
        "get-caller-identity",
        "--profile",
        "future-f4-human-admin",
        "--region",
        "us-east-1",
        "--endpoint-url",
        "https://sts.us-east-1.amazonaws.com",
        "--output",
        "json",
        "--no-cli-pager",
        "--cli-connect-timeout",
        "5",
        "--cli-read-timeout",
        "15",
        "--no-cli-auto-prompt",
        "--no-paginate",
    )
    for name in ("endpoint", "profile", "action", "extra_args", "service"):
        with pytest.raises(TypeError):
            sts.command(manifest["cli_path"], **{name: "PRIVATE_CANARY"})


@pytest.mark.parametrize(
    "fault",
    [
        "account",
        "user",
        "root",
        "role",
        "federated",
        "missing",
        "extra",
        "type",
        "userid",
    ],
)
def test_expected_identity_rejected(sts, expected, fault):
    if fault == "account":
        expected["Account"] = "111111111111"
    elif fault == "user":
        expected["Arn"] = expected["Arn"].replace("human-admin", "preflight")
    elif fault == "root":
        expected["Arn"] = "arn:aws:iam::000000000000:root"
    elif fault in {"role", "federated"}:
        expected["Arn"] = "arn:aws:sts::000000000000:" + fault + "/PRIVATE_CANARY"
    elif fault == "missing":
        expected.pop("UserId")
    elif fault == "extra":
        expected["token"] = "PRIVATE_CANARY"
    elif fault == "type":
        expected["Account"] = 0
    else:
        expected["UserId"] = "PRIVATE_CANARY:role"
    with pytest.raises(ValueError, match="expected_identity_invalid") as error:
        sts.identity(expected)
    assert "PRIVATE_CANARY" not in str(error.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("profile", "default"),
        ("profile", "future-f4-state-operator"),
        ("profile", "future-f4-preflight"),
        ("profile", "future-f4-policy-administrator"),
        ("region", "us-west-2"),
        ("endpoint", "http://sts.us-east-1.amazonaws.com"),
        ("endpoint", "https://sts.amazonaws.com"),
        ("endpoint", "https://private-canary.invalid"),
        ("window_end", "2030-01-01T02:00:00Z"),
        ("window_end", "2030-01-01T00:04:59Z"),
        ("window_start", "2030-01-01T00:00:01Z"),
        ("session_expires_at", "2029-12-31T23:59:59Z"),
        ("session_expires_at", "2030-01-01T00:06:59Z"),
        ("cli_path", "aws.exe"),
        ("cli_path", "//server/private/aws.exe"),
        ("cli_sha256", "PRIVATE_CANARY"),
    ],
)
def test_manifest_binding_and_freshness_fail_closed(sts, manifest, now, field, value):
    manifest[field] = value
    with pytest.raises(ValueError) as error:
        sts.validate(manifest, now)
    assert "PRIVATE_CANARY" not in str(error.value)


def test_window_and_session_boundary(sts, manifest, now):
    manifest["session_expires_at"] = "2030-01-01T00:07:00Z"
    sts.validate(manifest, now)
    with pytest.raises(ValueError):
        sts.validate(manifest, now.replace(tzinfo=None))
    manifest["enable_live"] = True
    with pytest.raises(ValueError, match="shape"):
        sts.validate(manifest, now)


@pytest.mark.parametrize(
    "addition",
    [
        "credential_process = PRIVATE_CANARY",
        "source_profile = default",
        "role_arn = PRIVATE_CANARY",
        "credential_source = Environment",
        "aws_access_key_id = PRIVATE_CANARY",
        "sso_session = PRIVATE_CANARY",
        "endpoint_url = https://private-canary.invalid",
        "plugins = PRIVATE_CANARY",
        "ca_bundle = PRIVATE_CANARY",
        "\n[default]\nregion = us-east-1",
        "\n[profile other]\nregion = us-east-1",
        "\n[DEFAULT]\nregion = us-east-1",
        "region = us-west-2",
    ],
)
def test_only_selected_login_configuration_accepted(sts, expected, addition):
    text = configuration(sts, expected)
    assert sts.selected_configuration(text, expected) == text
    with pytest.raises(ValueError, match="selected_configuration_rejected") as error:
        sts.selected_configuration(text + addition + "\n", expected)
    assert "PRIVATE_CANARY" not in str(error.value)


@pytest.mark.parametrize(
    "name",
    [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
        "AWS_ENDPOINT_URL",
        "AWS_CA_BUNDLE",
        "AWS_CONFIG_FILE",
        "AWS_CSM_ENABLED",
        "AWS_ROLE_ARN",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI",
        "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
        "HTTPS_PROXY",
        "http_proxy",
        "NO_PROXY",
        "BOTO_CONFIG",
        "AWS_CREDENTIAL_FILE",
        "TF_LOG",
    ],
)
def test_inherited_sources_fail_closed(sts, tmp_path, name):
    with pytest.raises(ValueError, match="inherited_credential_or_route_override"):
        sts.environment({name: "PRIVATE_CANARY"}, tmp_path, "http://127.0.0.1:1234")


def test_environment_prevents_alternate_files_and_metrics(sts, tmp_path):
    env = sts.environment(
        {"PATH": "fixture", "PYTHONPATH": "PRIVATE_CANARY", "SSL_CERT_FILE": "PRIVATE_CANARY"},
        tmp_path,
        "http://127.0.0.1:1234",
    )
    assert "PRIVATE_CANARY" not in env.values()
    assert env["AWS_PROFILE"] == env["AWS_DEFAULT_PROFILE"] == sts.PROFILE
    assert env["AWS_MAX_ATTEMPTS"] == "1" and env["AWS_EC2_METADATA_DISABLED"] == "true"
    assert (
        env["AWS_CSM_ENABLED"] == "false" and env["AWS_IGNORE_CONFIGURED_ENDPOINT_URLS"] == "true"
    )
    assert env["BOTO_CONFIG"] == env["AWS_SHARED_CREDENTIALS_FILE"]
    assert env["NO_PROXY"] == "" and env["HTTPS_PROXY"] == env["ALL_PROXY"]
    for proxy in ("http://127.0.0.1:65536", "http://localhost:1234", "https://private.invalid"):
        with pytest.raises(ValueError):
            sts.environment({}, tmp_path, proxy)


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "wrong_account",
        "wrong_user",
        "root",
        "role",
        "federated",
        "userid",
        "malformed",
        "duplicate",
        "missing",
        "extra",
        "type",
        "nested",
        "stdout_limit",
        "stderr_limit",
        "stderr",
        "exit",
        "expired",
        "deadline",
        "cancelled",
        "cleanup",
    ],
)
def test_response_protocol_and_private_rejection(sts, expected, fault, capsys, caplog):
    value = dict(expected)
    if fault in {"wrong_account", "wrong_user", "root", "role", "federated", "userid"}:
        key = "Account" if fault == "wrong_account" else "UserId" if fault == "userid" else "Arn"
        value[key] = {
            "wrong_account": "111111111111",
            "wrong_user": "arn:aws:iam::000000000000:user/other",
            "root": "arn:aws:iam::000000000000:root",
            "role": "arn:aws:sts::000000000000:assumed-role/other/session",
            "federated": "arn:aws:sts::000000000000:federated-user/other",
            "userid": "AIDAPRIVATECANARY00000",
        }[fault]
    elif fault == "missing":
        value.pop("UserId")
    elif fault == "extra":
        value["secret"] = "PRIVATE_CANARY"
    elif fault == "type":
        value["Account"] = 0
    raw = json.dumps(value).encode()
    if fault == "malformed":
        raw = b"PRIVATE_CANARY invalid JSON"
    elif fault == "duplicate":
        raw = b'{"Account":"PRIVATE_CANARY","Account":"PRIVATE_CANARY"}'
    elif fault == "nested":
        raw = b"[" * 2000 + b"]" * 2000
    elif fault == "stdout_limit":
        raw = b"x" * (sts.STDOUT_LIMIT + 1)
    error = b"PRIVATE_CANARY" if fault in {"stderr", "expired"} else b""
    if fault == "stderr_limit":
        error = b"x" * (sts.STDERR_LIMIT + 1)
    status = {
        "deadline": "deadline",
        "cancelled": "cancelled",
        "cleanup": "cleanup_incomplete",
    }.get(fault, "completed")
    captured = capture(
        sts, raw, code=255 if fault in {"exit", "expired"} else 0, status=status, stderr=error
    )
    result = sts.evaluate_fixture(captured, expected, policy(sts))
    assert result["evidence"] == "offline_fixture"
    assert result["identity_matched"] == (fault is None)
    assert (result["safety_failure"] is None) == (fault is None)
    assert not captured.stdout and not captured.stderr
    assert all(
        secret not in str(result)
        for secret in (expected["Arn"], expected["Account"], expected["UserId"], "PRIVATE_CANARY")
    )
    if fault in {"deadline", "cancelled", "cleanup", "exit", "expired", "malformed"}:
        assert result["request_sent"] is None
    assert not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize(
    "destination",
    ["us-east-1.signin.aws.amazon.com:443", "iam.amazonaws.com:443", "169.254.169.254:80"],
)
def test_refresh_and_unexpected_destinations_block_before_sender(sts, expected, destination):
    guard = policy(sts, claim=False)
    guard.connector = lambda: pytest.fail("No sender")
    assert not guard.claim("CONNECT", destination)
    result = sts.evaluate_fixture(capture(sts, json.dumps(expected).encode()), expected, guard)
    assert result["request_sent"] is False and not result["identity_matched"]
    assert result["safety_failure"] == "transport_guard_rejected"


def test_second_connection_or_missing_guard_cannot_be_identity_success(sts, expected):
    guard = policy(sts)
    assert not guard.claim("CONNECT", "sts.us-east-1.amazonaws.com:443")
    for value in (guard, policy(sts, claim=False)):
        result = sts.evaluate_fixture(capture(sts, json.dumps(expected).encode()), expected, value)
        assert not result["identity_matched"] and result["safety_failure"]


def test_real_local_guard_has_no_default_sender(sts):
    tunnel = sts.runner.local("infra/aws/fixtures/sts_tunnel.py")
    guard = tunnel.TunnelPolicy()
    service = tunnel.server(guard)
    worker = Thread(target=service.serve_forever)
    worker.start()
    try:
        with socket.create_connection(service.server_address, timeout=2) as client:
            client.sendall(
                b"CONNECT sts.us-east-1.amazonaws.com:443 HTTP/1.1\r\n"
                b"Host: sts.us-east-1.amazonaws.com:443\r\n\r\n"
            )
            assert client.recv(4096).startswith(b"HTTP/1.0 403")
        assert guard.summary()["allowed_tunnels"] == 0
    finally:
        guard.abort.set()
        service.shutdown()
        service.server_close()
        worker.join(timeout=5)
        assert not worker.is_alive()


def test_private_preparation_never_reads_cache_or_launches_aws(
    sts, manifest, expected, now, tmp_path, monkeypatch, capsys
):
    manifest_path, config_path, output = (
        tmp_path / "manifest.json",
        tmp_path / "source-config",
        tmp_path / "prepared",
    )
    output.mkdir(mode=0o700)
    manifest_path.write_text(json.dumps(manifest))
    config_path.write_text(configuration(sts, expected))
    for path in (manifest_path, config_path):
        path.chmod(0o600)
    monkeypatch.setattr(
        sts.runner.subprocess, "Popen", lambda *a, **kw: pytest.fail("No AWS or subprocess launch")
    )
    # Windows private() calls an owned ACL checker. Simulate that checker here;
    # native ACL behavior is tested independently below and in the existing suite.
    monkeypatch.setattr(sts, "private", lambda path: path)
    assert sts.prepare(manifest_path, config_path, output, now=now)["live_execution"] is False
    result = json.loads((output / "preparation.json").read_text())
    assert result["manifest"] == manifest and set(result["source_sha256"]) == set(sts.SOURCES)
    assert result["argv"] == list(sts.command(manifest["cli_path"]))
    assert (output / "selected-config").read_text() == configuration(sts, expected)
    assert (output / "empty-credentials").read_bytes() == b"" and not list(
        (output / "login-cache").iterdir()
    )
    assert sts.verify_preparation(output, now=now)["result"] == "offline_preparation_verified"
    with pytest.raises(FileExistsError):
        sts.prepare(manifest_path, config_path, output, now=now)
    assert not capsys.readouterr().out


@pytest.mark.parametrize("fault", ["command", "sources", "credentials", "cache", "live", "expired"])
def test_re_attestation_rejects_changed_preparation(
    sts, manifest, expected, now, tmp_path, monkeypatch, fault
):
    source, config, output = tmp_path / "input.json", tmp_path / "config", tmp_path / "out"
    source.write_text(json.dumps(manifest))
    config.write_text(configuration(sts, expected))
    output.mkdir()
    monkeypatch.setattr(sts, "private", lambda path: path)
    sts.prepare(source, config, output, now=now)
    value = json.loads((output / "preparation.json").read_text())
    if fault == "command":
        value["argv"].append("--debug")
    elif fault == "sources":
        value["source_sha256"] = {}
    elif fault == "credentials":
        (output / "empty-credentials").write_text("PRIVATE_CANARY")
    elif fault == "cache":
        (output / "login-cache/unapproved.json").write_text("PRIVATE_CANARY")
    elif fault == "live":
        value["live_execution"] = True
    else:
        now += timedelta(minutes=31)
    (output / "preparation.json").write_text(json.dumps(value))
    with pytest.raises(ValueError) as error:
        sts.verify_preparation(output, now=now)
    assert "PRIVATE_CANARY" not in str(error.value)


def test_changed_binary_does_not_create_preparation(
    sts, manifest, expected, now, tmp_path, monkeypatch
):
    manifest["cli_sha256"] = "a" * 64
    source, config = tmp_path / "manifest.json", tmp_path / "config"
    source.write_text(json.dumps(manifest))
    config.write_text(configuration(sts, expected))
    monkeypatch.setattr(sts, "private", lambda path: path)
    with pytest.raises(ValueError, match="cli_binary_changed"):
        sts.prepare(source, config, tmp_path, now=now)
    assert not (tmp_path / "preparation.json").exists()


def test_native_private_storage_and_nonoverwriting_results(sts, expected, tmp_path):
    result = sts.evaluate_fixture(
        capture(sts, json.dumps(expected).encode()), expected, policy(sts)
    )
    target = tmp_path / "result.json"
    sts.save_fixture(target, result)
    assert json.loads(target.read_text()) == result
    with pytest.raises(FileExistsError):
        sts.save_fixture(target, result)
    with pytest.raises(ValueError):
        sts.save_fixture(tmp_path / "leak.json", {**result, "private": "PRIVATE_CANARY"})
    with pytest.raises(ValueError):
        sts.save_fixture(tmp_path / "leak.json", {**result, "safety_failure": "PRIVATE_CANARY"})
    assert not (tmp_path / "leak.json").exists()


def test_concurrent_result_write_has_one_winner(sts, expected, tmp_path, monkeypatch):
    monkeypatch.setattr(sts, "private", lambda path: path)
    result = sts.evaluate_fixture(
        capture(sts, json.dumps(expected).encode()), expected, policy(sts)
    )

    def write(_):
        try:
            sts.save_fixture(tmp_path / "one-result.json", result)
            return "written"
        except FileExistsError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, range(2))) == ["blocked", "written"]


def test_claimed_process_cancellation_and_output_overflow(sts, expected, tmp_path):
    env = {
        k: v
        for k, v in os.environ.items()
        if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    captured = sts.runner.capture_owned(
        [sys.executable, "-I", "-S", "-c", "print('PRIVATE_CANARY' * 10000)"],
        cwd=tmp_path,
        env=env,
        stdout_limit=sts.STDOUT_LIMIT,
        stderr_limit=sts.STDERR_LIMIT,
    )
    result = sts.evaluate_fixture(captured, expected, policy(sts))
    assert result["safety_failure"] == "output_limit" and result["request_sent"] is None
    abort = Event()
    abort.set()
    captured = sts.runner.capture_owned(
        [sys.executable, "-c", "raise SystemExit(1)"], cwd=tmp_path, env=env, abort=abort
    )
    assert (
        sts.evaluate_fixture(captured, expected, policy(sts, claim=False))["request_sent"] is False
    )


@pytest.mark.parametrize(
    "attempt", ["execute", "identity", "iam", "login", "enabled", "credentials"]
)
def test_live_barrier_cannot_be_activated(sts, monkeypatch, attempt):
    monkeypatch.setenv("HUMAN_STS_LIVE", "true")
    monkeypatch.setattr(sts.runner, "ACCOUNT_EXECUTION_ENABLED", True)
    monkeypatch.setattr(sts.runner.subprocess, "Popen", lambda *a, **kw: pytest.fail("No launch"))
    with pytest.raises(PermissionError, match="offline_only_no_live_executor"):
        sts.execute_live(attempt, enabled=True, credentials="PRIVATE_CANARY")
    with pytest.raises(PermissionError, match="account_execution_disabled"):
        sts.runner.execute_account(attempt)


def test_cli_argument_errors_do_not_echo_private_inputs(sts, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["human_sts", "--execute", "PRIVATE_CANARY"])
    with pytest.raises(SystemExit):
        sts.main()
    captured = capsys.readouterr()
    assert captured.err == "human_sts_arguments_rejected\n" and not captured.out


def test_native_preparation_checks_private_access_without_aws(
    sts, manifest, expected, now, tmp_path, monkeypatch
):
    source, config, output = (
        tmp_path / "manifest.json",
        tmp_path / "source-config",
        tmp_path / "private-output",
    )
    for path, body in ((source, json.dumps(manifest)), (config, configuration(sts, expected))):
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            stream.write(body)
    output.mkdir(mode=0o700)
    original = sts.runner.subprocess.Popen
    calls = []

    def only_acl(argv, **kwargs):
        assert argv[0] == "powershell.exe" and "private_state.ps1" in argv[4]
        calls.append("local_acl_check")
        return original(argv, **kwargs)

    monkeypatch.setattr(sts.runner.subprocess, "Popen", only_acl)
    assert sts.prepare(source, config, output, now=now)["result"] == "offline_prepared"
    assert bool(calls) == (os.name == "nt")
    for path in output.iterdir():
        sts.private(path)


def test_failed_private_write_is_retained_and_not_retried(sts, expected, tmp_path, monkeypatch):
    monkeypatch.setattr(sts, "private", lambda path: path)
    result = sts.evaluate_fixture(
        capture(sts, json.dumps(expected).encode()), expected, policy(sts)
    )
    path = tmp_path / "result.json"

    def fail(_):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(sts.os, "fsync", fail)
    with pytest.raises(OSError):
        sts.save_fixture(path, result)
    assert path.exists()
    with pytest.raises(FileExistsError):
        sts.save_fixture(path, result)


def test_private_inputs_duplicate_json_and_output_bounds(sts, tmp_path, monkeypatch):
    monkeypatch.setattr(sts, "private", lambda path: path)
    source = tmp_path / "input.json"
    source.write_bytes(b"x" * (sts.STDOUT_LIMIT + 1))
    with pytest.raises(ValueError, match="private_input_too_large"):
        sts.read_private(source)
    source.write_bytes(b'{"expected":{},"expected":{"secret":"PRIVATE_CANARY"}}')
    with pytest.raises(ValueError, match="private_json_invalid"):
        sts.prepare(source, source, tmp_path, now=datetime(2030, 1, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="private_output_too_large"):
        sts.write_private(tmp_path / "too-large", b"x" * (sts.STDOUT_LIMIT + 1))
    assert not (tmp_path / "too-large").exists()


@pytest.mark.parametrize(
    "field,value",
    [("identity_matched", False), ("operation_completed", False), ("request_sent", None)],
)
def test_inconsistent_success_summary_cannot_be_saved(sts, expected, tmp_path, field, value):
    result = sts.evaluate_fixture(
        capture(sts, json.dumps(expected).encode()), expected, policy(sts)
    )
    result[field] = value
    with pytest.raises(ValueError, match="fixture_result_rejected"):
        sts.save_fixture(tmp_path / "inconsistent.json", result)
    assert not (tmp_path / "inconsistent.json").exists()


@pytest.mark.parametrize("status", ["deadline", "cancelled"])
def test_native_stall_is_stopped_after_controlled_barrier(sts, expected, tmp_path, status):
    service = socket.socket()
    service.bind(("127.0.0.1", 0))
    service.listen(1)
    service.settimeout(5)
    ready, cancel, closed = Event(), Event(), Event()
    errors = []

    def controller():
        try:
            with service.accept()[0] as peer:
                assert peer.recv(1) == b"R"
                ready.set()
                if status == "cancelled":
                    cancel.set()
                peer.settimeout(5)
                try:
                    assert peer.recv(1) == b""  # Await termination of the owned process.
                except ConnectionResetError:  # Windows resets sockets when the Job is killed.
                    pass
                closed.set()
        except (OSError, AssertionError) as error:  # fmt: skip
            errors.append(type(error).__name__)
        finally:
            service.close()

    worker = Thread(target=controller)
    worker.start()
    env = {
        k: v
        for k, v in os.environ.items()
        if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    code = (
        "import socket; s=socket.socket(); "
        f"s.connect(('127.0.0.1',{service.getsockname()[1]})); "
        "s.sendall(b'R'); s.recv(1)"
    )
    started = time.monotonic()
    try:
        captured = sts.runner.capture_owned(
            [sys.executable, "-I", "-S", "-c", code],
            cwd=tmp_path,
            env=env,
            abort=cancel,
            clock=lambda: (
                121
                if (ready.is_set() and status == "deadline") or time.monotonic() - started > 10
                else 0
            ),
        )
        assert ready.is_set() and captured.status == status
        result = sts.evaluate_fixture(captured, expected, policy(sts))
        assert result["safety_failure"] == status and result["request_sent"] is None
    finally:
        cancel.set()
        worker.join(timeout=7)
        service.close()
        assert not worker.is_alive()
        assert not errors and closed.is_set()
