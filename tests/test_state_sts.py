"""A1b offline/synthetic evidence only. Never invoke AWS or read real identity files."""

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, Event

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/implementation/f4-a1b-supervised-sts-procedure.md"


@pytest.fixture
def s(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    spec = importlib.util.spec_from_file_location("state_sts", ROOT / "infra/aws/state_sts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def expected():
    return {
        "Account": "000000000000",
        "Arn": "arn:aws:iam::000000000000:user/synthetic/future-f4-state-operator",
        "UserId": "AIDASYNTHETIC000000001",
    }


@pytest.fixture
def setup(s, expected, tmp_path):
    executable = tmp_path / "aws.exe"
    executable.write_bytes(b"SYNTHETIC - not executable")
    output = tmp_path / "private"
    output.mkdir(mode=0o700)
    # Existing ACL helpers require the repository ignored cache, including in tests.
    # pytest basetemp is explicitly under .cache for this suite.
    now = datetime(2030, 1, 1, tzinfo=UTC)
    spec = {
        "expected": expected,
        "provenance": "owner_confirmed_existing",
        "cli_path": str(executable),
        "cli_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "login_cache_directory": str(tmp_path / "synthetic-never-read-cache"),
        "window_start": now.isoformat().replace("+00:00", "Z"),
        "window_end": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
    }
    s.prepare(spec, output, now=now)
    return output, spec, now


def capture(s, value, *, status="completed", code=0, stderr=b""):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return s.local.runner.Capture(code, status, bytearray(raw), bytearray(stderr))


def test_positive_exact_private_identity_no_identifiers_in_result(s, expected):
    result = s.verify_capture(capture(s, expected), expected)
    assert result == {
        "checkpoint": "F4-A1b",
        "result": "identity_matched",
        "mfa_verified": False,
        "http_request_count_verified": False,
    }
    assert all(v not in json.dumps(result) for v in expected.values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("Account", "111111111111"),
        ("Arn", "arn:aws:iam::000000000000:user/synthetic/future-f4-human-admin"),
        ("Arn", "arn:aws:iam::000000000000:user/other/future-f4-state-operator"),
        ("Arn", "arn:aws:iam::000000000000:user/Synthetic/future-f4-state-operator"),
        ("Arn", "arn:aws:iam::000000000000:root"),
        ("Arn", "arn:aws:sts::000000000000:assumed-role/synthetic/session"),
        ("Arn", "arn:aws:sts::000000000000:federated-user/synthetic"),
        ("UserId", "AIDASYNTHETIC000000002"),
    ],
)
def test_wrong_private_identity_rejected(s, expected, field, value):
    actual = expected | {field: value}
    c = capture(s, actual)
    with pytest.raises(ValueError):
        s.verify_capture(c, expected)
    assert not c.stdout and not c.stderr


@pytest.mark.parametrize(
    "value",
    [
        b"{",
        b"null",
        b"[]",
        b"{}",
        b'{"Account":"a","Account":"b"}',
        b"\xff",
        b"x" * 8193,
        {"Account": 0, "Arn": "PRIVATE_CANARY", "UserId": "PRIVATE_CANARY"},
    ],
)
def test_malformed_or_oversized_result_rejected_and_cleared(s, expected, value):
    c = capture(s, value)
    with pytest.raises((ValueError, TypeError)):
        s.verify_capture(c, expected)
    assert not c.stdout and not c.stderr


@pytest.mark.parametrize("fault", ["missing", "extra"])
def test_response_exact_fields(s, expected, fault):
    actual = expected.copy()
    if fault == "missing":
        actual.pop("UserId")
    else:
        actual["Secret"] = "PRIVATE_CANARY"
    with pytest.raises(ValueError):
        s.verify_capture(capture(s, actual), expected)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"code": 1},
        {"stderr": b"PRIVATE_CANARY"},
        {"status": "deadline"},
        {"status": "cancelled"},
        {"status": "interrupted"},
        {"status": "cleanup_incomplete"},
        {"status": "launch_or_ownership_failed"},
    ],
)
def test_failure_never_reports_identity_success(s, expected, kwargs):
    c = capture(s, expected, **kwargs)
    with pytest.raises(ValueError) as error:
        s.verify_capture(c, expected)
    assert "PRIVATE_CANARY" not in str(error.value)
    assert not c.stdout and not c.stderr


def test_fixed_commands_accept_no_substitution(s, setup):
    _, spec, _ = setup
    args = s.command(spec["cli_path"])
    assert args[1:3] == ("sts", "get-caller-identity")
    assert args[args.index("--profile") + 1] == s.PROFILE
    assert args[args.index("--endpoint-url") + 1] == s.ENDPOINT
    assert len(args) == 18
    reference = s.reference_command(spec["cli_path"])
    assert reference[1:5] == ("iam", "get-user", "--user-name", s.PROFILE)
    assert reference[reference.index("--profile") + 1] == "future-f4-human-admin"
    assert reference[reference.index("--endpoint-url") + 1] == "https://iam.amazonaws.com"
    for key in ("profile", "endpoint", "action", "extra_args"):
        with pytest.raises(TypeError):
            s.command(spec["cli_path"], **{key: "PRIVATE_CANARY"})


@pytest.mark.parametrize(
    "poison",
    [
        "credential_process = synthetic",
        "role_arn = synthetic",
        "source_profile = default",
        "endpoint_url = http://127.0.0.1",
        "aws_access_key_id = synthetic",
        "ca_bundle = synthetic",
        "sso_session = synthetic",
        "max_attempts = 4",
    ],
)
def test_profile_fallback_and_overrides_rejected(s, setup, poison):
    root, spec, now = setup
    config = (root / "selected-config").read_text() + poison + "\n"
    (root / "selected-config").write_text(config)
    with pytest.raises(ValueError):
        s.claim(root, now=now)
    assert not (root / "attempt.claim").exists()


def test_selected_config_wrong_login_and_other_profile_rejected(s, expected):
    config = f"[profile {s.PROFILE}]\nregion = us-east-1\nlogin_session = {expected['Arn']}\n"
    assert s.selected_configuration(config, expected) == config
    for bad in (
        config.replace("/synthetic/", "/other/"),
        config + "[default]\nregion = us-east-1\n",
        config.replace(s.PROFILE, "future-f4-preflight", 1),
    ):
        with pytest.raises(ValueError):
            s.selected_configuration(bad, expected)


def test_child_environment_discards_inherited_credentials_and_proxies(s, setup):
    root, spec, _ = setup
    inherited = {
        key: "PRIVATE_CANARY"
        for key in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_PROFILE",
            "AWS_CONTAINER_CREDENTIALS_FULL_URI",
            "AWS_ENDPOINT_URL",
            "HTTPS_PROXY",
            "NO_PROXY",
            "BOTO_CONFIG",
            "PATH",
            "PYTHONPATH",
            "AWS_CA_BUNDLE",
            "REQUESTS_CA_BUNDLE",
            "TF_VAR_secret",
        )
    }
    env = s.environment(root, spec, inherited)
    assert "PRIVATE_CANARY" not in json.dumps(env)
    assert env["AWS_PROFILE"] == env["AWS_DEFAULT_PROFILE"] == s.PROFILE
    assert env["AWS_MAX_ATTEMPTS"] == "1" and env["AWS_EC2_METADATA_DISABLED"] == "true"
    assert env["AWS_CONFIG_FILE"] == str(root / "selected-config")


def test_one_shot_claim_survives_restart_and_concurrent_calls(s, setup):
    root, spec, now = setup
    barrier = Barrier(2)

    def contender():
        barrier.wait()
        try:
            s.claim(root, now=now)
            return "claimed"
        except FileExistsError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: contender(), range(2))) == ["claimed", "rejected"]
    marker = (root / "attempt.claim").read_bytes()
    assert marker == b"possibly_started\n"
    fresh = s.local.runner.local("infra/aws/state_sts.py")
    with pytest.raises(FileExistsError):
        fresh.claim(root, now=now)
    assert s.review(root, now=now) == spec


def test_partial_claim_or_interruption_cannot_be_reused(s, setup, monkeypatch):
    root, _, now = setup
    original = s.local.write_private

    def interrupted(path, body):
        if path.name == "attempt.claim":
            path.write_bytes(b"partial")
            raise OSError("SYNTHETIC interruption")
        return original(path, body)

    with monkeypatch.context() as patch:
        patch.setattr(s.local, "write_private", interrupted)
        with pytest.raises(OSError):
            s.claim(root, now=now)
    with pytest.raises(FileExistsError):
        s.claim(root, now=now)
    assert (root / "attempt.claim").read_bytes() == b"partial"


@pytest.mark.parametrize("fault", ["provenance", "binary", "expired", "source", "fields"])
def test_preparation_changed_or_untrusted_stops_before_claim(s, setup, fault):
    root, spec, now = setup
    record = json.loads((root / "preparation.json").read_text())
    if fault == "provenance":
        record["spec"]["provenance"] = "same_unverified_sts"
    elif fault == "binary":
        Path(spec["cli_path"]).write_bytes(b"changed")
    elif fault == "expired":
        now += timedelta(hours=1)
    elif fault == "source":
        record["sources"] = {}
    else:
        record["spec"]["profile"] = "future-f4-human-admin"
    (root / "preparation.json").write_text(json.dumps(record))
    with pytest.raises(ValueError):
        s.claim(root, now=now)
    assert not (root / "attempt.claim").exists()


def test_reference_read_validates_exact_target_then_returns_private_expectation(s, expected):
    user = {
        "Arn": expected["Arn"],
        "UserId": expected["UserId"],
        "Path": "/synthetic/",
        "UserName": s.PROFILE,
        "CreateDate": "synthetic",
    }
    assert (
        s.reference_identity(capture(s, {"User": user}), expected["Account"], expected["Arn"])
        == expected
    )
    for field in ("Arn", "UserName", "Path", "UserId"):
        bad = user | {field: "PRIVATE_CANARY"}
        with pytest.raises(ValueError):
            s.reference_identity(capture(s, {"User": bad}), expected["Account"], expected["Arn"])


def test_capture_primitive_cleans_up_synthetic_stall_without_retry(s, setup):
    root, _, now = setup
    s.claim(root, now=now)
    c = s.local.runner.capture_owned(
        [sys.executable, "-I", "-S", "-c", "import time; time.sleep(60)"],
        cwd=ROOT,
        env=os.environ.copy(),
        timeout=0.2,
        stdout_limit=8192,
        stderr_limit=4096,
    )
    assert c.status == "deadline" and c.native_exit is not None
    with pytest.raises(FileExistsError):
        s.claim(root, now=now)
    abort = Event()
    abort.set()
    c = s.local.runner.capture_owned(
        ["NOT_A_REAL_PROGRAM"],
        cwd=ROOT,
        env={},
        abort=abort,
    )
    assert c.status == "cancelled_before_start"


def test_disabled_executors_and_offline_module_has_no_launch(s):
    for module, name in ((s.local, "execute_live"), (s.local.runner, "execute_account")):
        tree = ast.parse(Path(module.__file__).read_bytes())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
        assert len(node.body) == 1 and isinstance(node.body[0], ast.Raise)
    tree = ast.parse((ROOT / "infra/aws/state_sts.py").read_bytes())
    assert not any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"Popen", "run", "capture_owned", "execute_account", "execute_live"}
        for n in ast.walk(tree)
    )


def test_powershell_review_blocks_parse_without_execution():
    executable = shutil.which("powershell")
    if not executable:
        pytest.skip("Windows PowerShell parser unavailable on this review host")
    # ParseInput only; never invoke the procedure or native AWS executable.
    command = r"""
$doc = [IO.File]::ReadAllText('docs/implementation/f4-a1b-supervised-sts-procedure.md')
$blocks = [regex]::Matches($doc, '(?s)```powershell\r?\n(.*?)```')
foreach ($block in $blocks) {
    $tokens=$null; $errors=$null
    $null=[Management.Automation.Language.Parser]::ParseInput($block.Groups[1].Value,[ref]$tokens,[ref]$errors)
    if ($errors.Count) { throw 'powershell_syntax_invalid' }
}
Write-Output ('parsed_blocks=' + $blocks.Count)
"""
    result = subprocess.run(
        [executable, "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=ROOT,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, "powershell_syntax_invalid"
    assert b"parsed_blocks=4" in result.stdout


def procedure_blocks():
    return re.findall(r"@'\n(.*?)\n'@", DOC.read_text(encoding="utf-8"), re.S)


@pytest.mark.parametrize("fault", [None, "command", "partial", "wrong_identity"])
def test_documented_sts_assembly_synthetic_only_no_second_launch(
    s, setup, monkeypatch, capsys, fault
):
    root, spec, now = setup
    monkeypatch.setenv("FATA_A1B_DIRECTORY", str(root))
    monkeypatch.setitem(sys.modules, "state_sts", s)
    original_claim = s.claim
    monkeypatch.setattr(s, "claim", lambda root, **_: original_claim(root, now=now))
    calls = []

    def synthetic_only(argv, **kwargs):
        calls.append((argv, kwargs))
        assert argv == s.command(spec["cli_path"])
        assert kwargs["timeout"] == 120
        assert kwargs["stdout_limit"] == 8192 and kwargs["stderr_limit"] == 4096
        assert kwargs["env"]["AWS_PROFILE"] == s.PROFILE
        if fault == "partial":
            raise KeyboardInterrupt
        actual = spec["expected"].copy()
        if fault == "wrong_identity":
            actual["UserId"] = "AIDASYNTHETIC000000002"
        return capture(s, actual, code=1 if fault == "command" else 0)

    monkeypatch.setattr(s.local.runner, "capture_owned", synthetic_only)
    block = compile(procedure_blocks()[1], "future-sts-block-synthetic-only", "exec")
    if fault:
        with pytest.raises(SystemExit):
            exec(block, {})
        assert not (root / "result.json").exists()
    else:
        exec(block, {})
        assert json.loads((root / "result.json").read_text())["result"] == "identity_matched"
    assert len(calls) == 1 and (root / "attempt.claim").exists()
    # A second execution cannot release another command, including after interruption.
    with pytest.raises(SystemExit):
        exec(block, {})
    assert len(calls) == 1
    printed = capsys.readouterr().out
    assert all(v not in printed for v in spec["expected"].values())


def test_documented_reference_assembly_and_cross_account_rejection(s, setup, monkeypatch, capsys):
    root, spec, now = setup
    human = spec["expected"] | {"Arn": "arn:aws:iam::000000000000:user/future-f4-human-admin"}
    reference = {
        k: spec[k]
        for k in ("cli_path", "cli_sha256", "login_cache_directory", "window_start", "window_end")
    }
    reference.update(
        human=human,
        target_account=spec["expected"]["Account"],
        target_arn=spec["expected"]["Arn"],
        sources={n: hashlib.sha256((s.local.ROOT / n).read_bytes()).hexdigest() for n in s.SOURCES},
    )
    s.local.write_private(root / "reference.json", (json.dumps(reference) + "\n").encode())
    config = (
        "[profile future-f4-human-admin]\nregion = us-east-1\nlogin_session = "
        + human["Arn"]
        + "\n"
    )
    s.local.write_private(root / "human-config", config.encode())
    monkeypatch.setitem(sys.modules, "state_sts", s)
    monkeypatch.setenv("FATA_A1B_REFERENCE_DIRECTORY", str(root))
    validate = s.validate_reference
    monkeypatch.setattr(s, "validate_reference", lambda v, **_: validate(v, now=now))
    with pytest.raises(ValueError):
        validate(reference | {"target_account": "111111111111"}, now=now)
    calls = []

    def synthetic_only(argv, **kwargs):
        calls.append(argv)
        assert argv == s.reference_command(spec["cli_path"])
        assert kwargs["env"]["AWS_PROFILE"] == "future-f4-human-admin"
        return capture(
            s,
            {
                "User": {
                    "UserName": s.PROFILE,
                    "Arn": spec["expected"]["Arn"],
                    "Path": "/synthetic/",
                    "UserId": spec["expected"]["UserId"],
                }
            },
        )

    monkeypatch.setattr(s.local.runner, "capture_owned", synthetic_only)
    block = compile(procedure_blocks()[3], "future-reference-block-synthetic-only", "exec")
    exec(block, {})
    assert json.loads((root / "expected-state.json").read_text()) == spec["expected"]
    with pytest.raises(SystemExit):
        exec(block, {})
    assert len(calls) == 1
    assert all(v not in capsys.readouterr().out for v in spec["expected"].values())
