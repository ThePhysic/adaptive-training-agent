"""A2-state-01 synthetic-only metadata tests. No AWS executable/account/cache access."""

import ast
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/implementation/f4-a2-state-01-supervised-procedure.md"


@pytest.fixture
def a(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    spec = importlib.util.spec_from_file_location(
        "attached_policies", ROOT / "infra/aws/attached_policies.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def spec(a, tmp_path):
    executable = tmp_path / "aws.exe"
    executable.write_bytes(b"SYNTHETIC non-executable")
    return {
        "caller": {
            "Account": "000000000000",
            "Arn": "arn:aws:iam::000000000000:user/human/future-f4-human-admin",
            "UserId": "AIDASYNTHETICHUMAN0001",
        },
        "target": {
            "Account": "000000000000",
            "Arn": "arn:aws:iam::000000000000:user/state/future-f4-state-operator",
            "UserId": "AIDASYNTHETICSTATE0001",
        },
        "caller_provenance": "owner_attested_A1a",
        "target_provenance": "owner_attested_A1b",
        "approved_policies": [
            {"PolicyName": "ReadOnlyAccess", "PolicyArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"},
            {
                "PolicyName": "Synthetic",
                "PolicyArn": "arn:aws:iam::000000000000:policy/example/Synthetic",
            },
        ],
        "cli_path": str(executable),
        "cli_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "login_cache_directory": str(tmp_path / "SYNTHETIC-never-read-login-cache"),
        "window_start": "2030-01-01T00:00:00Z",
        "window_end": "2030-01-01T00:30:00Z",
        "source_sha256": a.sources(),
    }


@pytest.fixture
def now():
    return datetime(2030, 1, 1, tzinfo=UTC)


@pytest.fixture
def prepared(a, spec, now, tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    a.prepare(spec, root, now=now)
    return root


def capture(a, body, *, code=0, status="completed", stderr=b""):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    return a.local.runner.Capture(code, status, bytearray(raw), bytearray(stderr))


def receipt(root):
    return (root / "preparation.sha256").read_text().strip()


def page(spec):
    return {"AttachedPolicies": copy.deepcopy(spec["approved_policies"]), "IsTruncated": False}


def test_exact_command_has_no_other_surface(a, spec):
    assert a.command(spec["cli_path"]) == (
        spec["cli_path"],
        "iam",
        "list-attached-user-policies",
        "--user-name",
        "future-f4-state-operator",
        "--profile",
        "future-f4-human-admin",
        "--region",
        "us-east-1",
        "--endpoint-url",
        "https://iam.amazonaws.com",
        "--output",
        "json",
        "--no-cli-pager",
        "--no-cli-auto-prompt",
        "--no-paginate",
        "--cli-connect-timeout",
        "5",
        "--cli-read-timeout",
        "15",
    )
    for key in ("action", "profile", "endpoint", "target", "extra_args"):
        with pytest.raises(TypeError):
            a.command(spec["cli_path"], **{key: "PRIVATE_CANARY"})
    with pytest.raises(ValueError):
        a.command("aws")


def test_aws_customer_policies_private_evidence_and_sanitized_summary(a, spec, prepared):
    c = capture(a, page(spec))
    result = a.verify_capture(c, spec, output=prepared)
    assert result == {
        "checkpoint": "F4-A2-state-01",
        "result": "metadata_page_verified",
        "policy_count": 2,
        "mfa_verified": False,
        "http_request_count_verified": False,
    }
    assert json.loads((prepared / "observed-policies.json").read_text()) == page(spec)
    assert all(p["PolicyArn"] not in json.dumps(result) for p in spec["approved_policies"])
    assert not c.stdout and not c.stderr


def test_empty_page_empty_allowlist_valid(a, spec, monkeypatch):
    spec["approved_policies"] = []
    writes = []
    monkeypatch.setattr(a, "write_private", lambda path, body: writes.append(body))
    result = a.verify_capture(capture(a, page(spec)), spec, output=Path("SYNTHETIC-unused"))
    assert result["policy_count"] == 0 and len(writes) == 1


@pytest.mark.parametrize(
    "fault",
    [
        "json",
        "utf8",
        "null",
        "missing",
        "extra",
        "truncated",
        "flag_type",
        "marker",
        "next_token",
        "wrong_array",
        "missing_entry_field",
        "entry_extra",
        "foreign_account",
        "wrong_service",
        "wrong_partition",
        "wrong_name",
        "bad_name",
        "bad_path",
        "bad_length",
        "duplicate_arn",
        "duplicate_name",
        "too_many",
        "too_large",
        "duplicate_json",
    ],
)
def test_strict_page_rejections_never_write_or_leak(a, spec, monkeypatch, capsys, caplog, fault):
    value = page(spec)
    if fault == "json":
        value = b"{PRIVATE_CANARY"
    elif fault == "utf8":
        value = b"\xff"
    elif fault == "null":
        value = None
    elif fault == "missing":
        value.pop("IsTruncated")
    elif fault == "extra":
        value["PRIVATE_CANARY"] = "PRIVATE_CANARY"
    elif fault == "truncated":
        value["IsTruncated"] = True
    elif fault == "flag_type":
        value["IsTruncated"] = 0
    elif fault == "marker":
        value["Marker"] = ""
    elif fault == "next_token":
        value["NextToken"] = "PRIVATE_CANARY"
    elif fault == "wrong_array":
        value["AttachedPolicies"] = {}
    elif fault == "missing_entry_field":
        value["AttachedPolicies"][0].pop("PolicyArn")
    elif fault == "entry_extra":
        value["AttachedPolicies"][0]["PRIVATE_CANARY"] = "private"
    elif fault == "foreign_account":
        value["AttachedPolicies"][1]["PolicyArn"] = (
            "arn:aws:iam::111111111111:policy/example/Synthetic"
        )
    elif fault == "wrong_service":
        value["AttachedPolicies"][0]["PolicyArn"] = "arn:aws:s3::aws:policy/ReadOnlyAccess"
    elif fault == "wrong_partition":
        value["AttachedPolicies"][0]["PolicyArn"] = "arn:aws-cn:iam::aws:policy/ReadOnlyAccess"
    elif fault == "wrong_name":
        value["AttachedPolicies"][0]["PolicyName"] = "PRIVATE_CANARY"
    elif fault == "bad_name":
        value["AttachedPolicies"][0]["PolicyName"] = "a b"
    elif fault == "bad_path":
        value["AttachedPolicies"][0]["PolicyArn"] = "arn:aws:iam::aws:policy/../ReadOnlyAccess"
    elif fault == "bad_length":
        value["AttachedPolicies"][0]["PolicyArn"] = "x" * 2049
    elif fault == "duplicate_arn":
        value["AttachedPolicies"] *= 2
    elif fault == "duplicate_name":
        value["AttachedPolicies"].append(
            {
                "PolicyName": "ReadOnlyAccess",
                "PolicyArn": "arn:aws:iam::000000000000:policy/ReadOnlyAccess",
            }
        )
    elif fault == "too_many":
        value["AttachedPolicies"] *= 7
    elif fault == "too_large":
        value = b" " * 65537
    elif fault == "duplicate_json":
        value = b'{"AttachedPolicies":[],"IsTruncated":true,"IsTruncated":false}'
    monkeypatch.setattr(a, "write_private", lambda *args: pytest.fail("invalid_page_written"))
    c = capture(a, value)
    with pytest.raises(ValueError) as error:
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert "PRIVATE_CANARY" not in str(error.value)
    assert not c.stdout and not c.stderr and not capsys.readouterr().out and not caplog.text


def test_unexpected_valid_policy_stops_with_private_observation(a, spec, prepared):
    value = page(spec)
    value["AttachedPolicies"].append(
        {"PolicyName": "Unexpected", "PolicyArn": "arn:aws:iam::aws:policy/Unexpected"}
    )
    with pytest.raises(ValueError, match="^a2_unexpected_policy_private_review$"):
        a.verify_capture(capture(a, value), spec, output=prepared)
    assert json.loads((prepared / "observed-policies.json").read_text()) == value


@pytest.mark.parametrize(
    "fault",
    ["caller", "target", "account", "userid", "source", "binary", "expired", "provenance", "field"],
)
def test_preparation_binding_rejection(a, spec, now, fault):
    if fault == "caller":
        spec["caller"]["Arn"] = spec["target"]["Arn"]
    elif fault == "target":
        spec["target"]["Arn"] = spec["caller"]["Arn"]
    elif fault == "account":
        spec["caller"]["Account"] = "111111111111"
    elif fault == "userid":
        spec["target"]["UserId"] = spec["caller"]["UserId"]
    elif fault == "source":
        spec["source_sha256"] = {}
    elif fault == "binary":
        Path(spec["cli_path"]).write_bytes(b"changed")
    elif fault == "expired":
        now += timedelta(hours=1)
    elif fault == "provenance":
        spec["target_provenance"] = "unverified_sts"
    else:
        spec["endpoint"] = "https://unapproved.invalid"
    with pytest.raises(ValueError):
        a.validate(spec, now=now)


def test_twelve_policy_boundary_and_order_independence(a, spec, monkeypatch):
    spec["approved_policies"] = [
        {"PolicyName": f"P{i}", "PolicyArn": f"arn:aws:iam::aws:policy/P{i}"} for i in range(12)
    ]
    value = page(spec)
    value["AttachedPolicies"].reverse()
    monkeypatch.setattr(a, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, value), spec, output=Path("SYNTHETIC-unused"))["policy_count"]
        == 12
    )


@pytest.mark.parametrize(
    "fault", ["code", "stderr", "deadline", "cancelled", "cleanup_incomplete", "output_limit"]
)
def test_failed_command_rejects_clears_and_never_saves(a, spec, monkeypatch, fault):
    c = capture(
        a,
        page(spec),
        code=1 if fault == "code" else 0,
        stderr=b"PRIVATE_CANARY" if fault == "stderr" else b"",
        status=fault if fault not in {"code", "stderr"} else "completed",
    )
    monkeypatch.setattr(a, "write_private", lambda *_: pytest.fail("failed_capture_written"))
    with pytest.raises(ValueError):
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert not c.stdout and not c.stderr


def test_concurrent_one_shot_restart_and_partial_claim(a, prepared, now, monkeypatch):
    barrier = Barrier(2)

    def contender():
        barrier.wait()
        try:
            a.claim(prepared, now=now, reviewed_sha256=receipt(prepared))
            return "claimed"
        except FileExistsError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: contender(), range(2))) == ["claimed", "rejected"]
    fresh = a.local.runner.local("infra/aws/attached_policies.py")
    with pytest.raises(FileExistsError):
        fresh.claim(prepared, now=now, reviewed_sha256=receipt(prepared))
    assert (prepared / "attempt.claim").read_bytes() == b"possibly_started\n"


def test_partial_fsync_failure_is_retained_and_blocks_replay(a, prepared, now, monkeypatch):
    real_fsync = a.os.fsync
    with monkeypatch.context() as patch:
        patch.setattr(a.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY")))
        with pytest.raises(OSError):
            a.claim(prepared, now=now, reviewed_sha256=receipt(prepared))
    assert a.os.fsync is real_fsync and (prepared / "attempt.claim").exists()
    with pytest.raises(FileExistsError):
        a.claim(prepared, now=now, reviewed_sha256=receipt(prepared))


def test_poisoned_config_and_environment(a, prepared, spec, now):
    inherited = {
        key: "PRIVATE_CANARY"
        for key in (
            "AWS_ACCESS_KEY_ID",
            "AWS_PROFILE",
            "HTTPS_PROXY",
            "AWS_ENDPOINT_URL",
            "AWS_CA_BUNDLE",
            "PYTHONPATH",
            "PATH",
        )
    }
    env = a.environment(prepared, spec, inherited)
    assert "PRIVATE_CANARY" not in json.dumps(env)
    assert env["AWS_PROFILE"] == env["AWS_DEFAULT_PROFILE"] == a.PROFILE
    assert env["AWS_MAX_ATTEMPTS"] == "1" and env["AWS_EC2_METADATA_DISABLED"] == "true"
    with (prepared / "human-config").open("a") as f:
        f.write("credential_process = PRIVATE_CANARY\n")
    with pytest.raises(ValueError):
        a.claim(prepared, now=now, reviewed_sha256=receipt(prepared))
    assert not (prepared / "attempt.claim").exists()


@pytest.mark.parametrize("field", ["UserId", "Arn", "approved_policies"])
def test_changed_private_binding_rejected_by_separately_reviewed_digest(a, prepared, now, field):
    approved_digest = receipt(prepared)
    record = json.loads((prepared / "preparation.json").read_text())
    if field == "UserId":
        record["spec"]["target"][field] = "AIDASYNTHETICCHANGED01"
    elif field == "Arn":
        record["spec"]["target"][field] = (
            "arn:aws:iam::000000000000:user/changed/future-f4-state-operator"
        )
    else:
        record["spec"][field] = []
    (prepared / "preparation.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="a2_reviewed_preparation_mismatch"):
        a.claim(prepared, now=now, reviewed_sha256=approved_digest)
    assert not (prepared / "attempt.claim").exists()


def test_partial_marker_never_releases_another_attempt(a, prepared, now):
    (prepared / "attempt.claim").write_bytes(b"partial")
    with pytest.raises(FileExistsError):
        a.claim(prepared, now=now, reviewed_sha256=receipt(prepared))
    assert (prepared / "attempt.claim").read_bytes() == b"partial"


def test_exact_response_byte_boundary(a, spec, monkeypatch):
    value = json.dumps(page(spec)).encode()
    value += b" " * (a.LIMIT - len(value))
    monkeypatch.setattr(a, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, value), spec, output=Path("SYNTHETIC-unused"))["policy_count"]
        == 2
    )


@pytest.mark.parametrize("fault", [None, "command", "interrupted", "unexpected", "persistence"])
def test_actual_documented_assembly_mock_only_never_replays(
    a, prepared, spec, now, monkeypatch, capsys, fault
):
    monkeypatch.setenv("FATA_A2_DIRECTORY", str(prepared))
    monkeypatch.setenv("FATA_A2_PREPARATION_DIGEST", receipt(prepared))
    monkeypatch.setitem(sys.modules, "attached_policies", a)
    original = a.claim
    monkeypatch.setattr(
        a,
        "claim",
        lambda root, **kw: original(root, now=now, reviewed_sha256=kw["reviewed_sha256"]),
    )
    calls = []

    def synthetic_only(argv, **kwargs):
        calls.append(argv)
        assert argv == a.command(spec["cli_path"])
        assert kwargs["timeout"] == 120 and kwargs["stdout_limit"] == 65536
        assert kwargs["stderr_limit"] == 4096
        assert kwargs["env"]["AWS_PROFILE"] == a.PROFILE
        if fault == "interrupted":
            raise KeyboardInterrupt
        value = page(spec)
        if fault == "unexpected":
            value["AttachedPolicies"] = [
                {"PolicyName": "Surprise", "PolicyArn": "arn:aws:iam::aws:policy/Surprise"}
            ]
        return capture(a, value, code=1 if fault == "command" else 0)

    monkeypatch.setattr(a.local.runner, "capture_owned", synthetic_only)
    write = a.write_private

    def save(path, body):
        if fault == "persistence" and path.name == "result.json":
            raise OSError("PRIVATE_CANARY")
        return write(path, body)

    monkeypatch.setattr(a, "write_private", save)
    block = re.findall(r"@'\n(.*?)\n'@", DOC.read_text(encoding="utf-8"), re.S)[1]
    if fault:
        with pytest.raises(SystemExit):
            exec(compile(block, "synthetic-assembly", "exec"), {})
        assert not (prepared / "result.json").exists()
    else:
        exec(compile(block, "synthetic-assembly", "exec"), {})
        assert json.loads((prepared / "result.json").read_text())["policy_count"] == 2
    with pytest.raises(SystemExit):
        exec(compile(block, "synthetic-assembly", "exec"), {})
    assert len(calls) == 1 and (prepared / "attempt.claim").exists()
    report = capsys.readouterr().out
    assert "PRIVATE_CANARY" not in report and "ReadOnlyAccess" not in report
    assert all(
        v not in report for identity in (spec["caller"], spec["target"]) for v in identity.values()
    )


def test_no_launcher_and_prior_live_executors_still_raise(a):
    tree = ast.parse((ROOT / "infra/aws/attached_policies.py").read_bytes())
    assert not any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"Popen", "run", "capture_owned", "execute_live", "execute_account"}
        for n in ast.walk(tree)
    )
    for path, name in (
        ("infra/aws/human_sts.py", "execute_live"),
        ("infra/aws/private_command_runner.py", "execute_account"),
    ):
        tree = ast.parse((ROOT / path).read_bytes())
        f = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
        assert len(f.body) == 1 and isinstance(f.body[0], ast.Raise)


def test_procedure_parse_only_and_embedded_python_syntax():
    text = DOC.read_text(encoding="utf-8")
    for block in re.findall(r"@'\n(.*?)\n'@", text, re.S):
        ast.parse(block, feature_version=(3, 13))
    executable = shutil.which("powershell")
    if executable is None:
        pytest.skip("Windows PowerShell parser unavailable")
    code = r"""
$doc=[IO.File]::ReadAllText('docs/implementation/f4-a2-state-01-supervised-procedure.md')
$blocks=[regex]::Matches($doc,'(?s)```powershell\r?\n(.*?)```')
foreach($b in $blocks){
    $t=$null; $e=$null
    $null=[Management.Automation.Language.Parser]::ParseInput($b.Groups[1].Value,[ref]$t,[ref]$e)
    if($e.Count){throw 'syntax_invalid'}
}
Write-Output ('parsed_blocks='+$blocks.Count)
"""
    result = subprocess.run(
        [executable, "-NoProfile", "-NonInteractive", "-Command", code],
        cwd=ROOT,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0 and b"parsed_blocks=2" in result.stdout
