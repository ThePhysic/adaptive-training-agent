"""State-02 synthetic-only evidence. No native AWS or real identity/cache access."""

import ast
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
DOC = ROOT / "docs/implementation/f4-a2-state-02-supervised-procedure.md"


@pytest.fixture
def a(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    s = importlib.util.spec_from_file_location(
        "inline_policies", ROOT / "infra/aws/inline_policies.py"
    )
    module = importlib.util.module_from_spec(s)
    s.loader.exec_module(module)
    return module


@pytest.fixture
def now():
    return datetime(2030, 1, 1, tzinfo=UTC)


@pytest.fixture
def spec(a, tmp_path):
    binary = tmp_path / "aws.exe"
    binary.write_bytes(b"SYNTHETIC non-executable")
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
        "approved_policy_names": ["SyntheticRead", "SyntheticWrite"],
        "cli_path": str(binary),
        "cli_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "login_cache_directory": str(tmp_path / "SYNTHETIC-never-read-cache"),
        "window_start": "2030-01-01T00:00:00Z",
        "window_end": "2030-01-01T00:30:00Z",
        "source_sha256": a.sources(),
    }


@pytest.fixture
def prepared(a, spec, tmp_path, now):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    a.prepare(spec, root, now=now)
    return root


def digest(root):
    return (root / "preparation.sha256").read_text().strip()


def capture(a, value, code=0, status="completed", stderr=b""):
    body = value if isinstance(value, bytes) else json.dumps(value).encode()
    return a.local.runner.Capture(code, status, bytearray(body), bytearray(stderr))


def page(spec):
    return {"PolicyNames": spec["approved_policy_names"][:], "IsTruncated": False}


def test_fixed_command_no_substitution(a, spec):
    assert a.command(spec["cli_path"]) == (
        spec["cli_path"],
        "iam",
        "list-user-policies",
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
    for field in ("action", "profile", "target", "endpoint", "extra_args"):
        with pytest.raises(TypeError):
            a.command(spec["cli_path"], **{field: "PRIVATE_CANARY"})
    with pytest.raises(ValueError):
        a.command("aws")


def test_positive_private_observation_and_finite_summary(a, spec, prepared):
    c = capture(a, page(spec))
    result = a.verify_capture(c, spec, output=prepared)
    assert result == {
        "checkpoint": "F4-A2-state-02",
        "result": "metadata_page_verified",
        "policy_count": 2,
        "mfa_verified": False,
        "http_request_count_verified": False,
    }
    assert json.loads((prepared / "observed-policy-names.json").read_text()) == page(spec)
    assert all(n not in json.dumps(result) for n in spec["approved_policy_names"])
    assert not c.stdout and not c.stderr


@pytest.mark.parametrize("count", [0, 40])
def test_empty_and_count_boundary_order_independence(a, spec, monkeypatch, count):
    spec["approved_policy_names"] = [f"P{i}" for i in range(count)]
    value = page(spec)
    value["PolicyNames"].reverse()
    monkeypatch.setattr(a.base, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, value), spec, output=Path("SYNTHETIC-unused"))["policy_count"]
        == count
    )


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
        "array_type",
        "entry_type",
        "empty_name",
        "long_name",
        "control",
        "unicode",
        "path",
        "duplicate",
        "count",
        "size",
        "duplicate_json",
        "managed_shape",
        "case",
    ],
)
def test_invalid_pages_stop_without_metadata_or_leak(a, spec, monkeypatch, capsys, caplog, fault):
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
    elif fault == "array_type":
        value["PolicyNames"] = "SyntheticRead"
    elif fault == "entry_type":
        value["PolicyNames"] = [None]
    elif fault == "empty_name":
        value["PolicyNames"] = [""]
    elif fault == "long_name":
        value["PolicyNames"] = ["P" * 129]
    elif fault == "control":
        value["PolicyNames"] = ["P\nSecret"]
    elif fault == "unicode":
        value["PolicyNames"] = ["P\u00e9"]
    elif fault == "path":
        value["PolicyNames"] = ["path/P"]
    elif fault == "duplicate":
        value["PolicyNames"] *= 2
    elif fault == "count":
        value["PolicyNames"] = [f"P{i}" for i in range(41)]
    elif fault == "size":
        value = b" " * 65537
    elif fault == "duplicate_json":
        value = b'{"PolicyNames":[],"IsTruncated":true,"IsTruncated":false}'
    elif fault == "managed_shape":
        value = {"AttachedPolicies": [], "IsTruncated": False}
    else:
        value = {"policynames": [], "IsTruncated": False}
    monkeypatch.setattr(a.base, "write_private", lambda *_: pytest.fail("invalid_page_written"))
    c = capture(a, value)
    with pytest.raises(ValueError) as error:
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert "PRIVATE_CANARY" not in str(error.value)
    assert not c.stdout and not c.stderr and not capsys.readouterr().out and not caplog.text


def test_name_and_exact_byte_boundary(a, spec, monkeypatch):
    spec["approved_policy_names"] = ["P" * 128]
    body = json.dumps(page(spec)).encode()
    body += b" " * (a.LIMIT - len(body))
    monkeypatch.setattr(a.base, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, body), spec, output=Path("SYNTHETIC-unused"))["policy_count"]
        == 1
    )


@pytest.mark.parametrize(
    "fault", ["code", "stderr", "deadline", "cancelled", "interrupted", "cleanup_incomplete"]
)
def test_failed_capture_cleared_no_success(a, spec, monkeypatch, fault):
    monkeypatch.setattr(a.base, "write_private", lambda *_: pytest.fail("failed_capture_written"))
    c = capture(
        a,
        page(spec),
        code=1 if fault == "code" else 0,
        status=fault if fault not in {"code", "stderr"} else "completed",
        stderr=b"PRIVATE_CANARY" if fault == "stderr" else b"",
    )
    with pytest.raises(ValueError):
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert not c.stdout and not c.stderr


@pytest.mark.parametrize(
    "fault", ["caller", "target", "uid", "source", "binary", "expired", "provenance", "extra"]
)
def test_private_bindings_and_reviewed_context(a, spec, now, fault):
    if fault == "caller":
        spec["caller"]["Arn"] = spec["target"]["Arn"]
    elif fault == "target":
        spec["target"]["Account"] = "111111111111"
    elif fault == "uid":
        spec["target"]["UserId"] = spec["caller"]["UserId"]
    elif fault == "source":
        spec["source_sha256"] = {}
    elif fault == "binary":
        Path(spec["cli_path"]).write_bytes(b"changed")
    elif fault == "expired":
        now += timedelta(hours=1)
    elif fault == "provenance":
        spec["target_provenance"] = "unverified_response"
    else:
        spec["action"] = "get-user-policy"
    with pytest.raises(ValueError):
        a.validate(spec, now=now)


def test_concurrent_claim_restart_and_no_cross_unit_reuse(a, prepared, now):
    approved = digest(prepared)
    barrier = Barrier(2)

    def contender():
        barrier.wait()
        try:
            a.claim(prepared, now=now, reviewed_sha256=approved)
            return "claimed"
        except FileExistsError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: contender(), range(2))) == ["claimed", "rejected"]
    fresh = a.local.runner.local("infra/aws/inline_policies.py")
    with pytest.raises(FileExistsError):
        fresh.claim(prepared, now=now, reviewed_sha256=approved)
    with pytest.raises(ValueError):
        a.base.review(prepared, now=now)


def test_failed_fsync_claim_remains(a, prepared, now, monkeypatch):
    approved = digest(prepared)
    with monkeypatch.context() as patch:
        patch.setattr(
            a.base.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY"))
        )
        with pytest.raises(OSError):
            a.claim(prepared, now=now, reviewed_sha256=approved)
    assert (prepared / "attempt.claim").exists()
    with pytest.raises(FileExistsError):
        a.claim(prepared, now=now, reviewed_sha256=approved)


def test_partial_claim_remains(a, prepared, now):
    (prepared / "attempt.claim").write_bytes(b"partial")
    with pytest.raises(FileExistsError):
        a.claim(prepared, now=now, reviewed_sha256=digest(prepared))
    assert (prepared / "attempt.claim").read_bytes() == b"partial"


def test_post_review_identity_or_name_tampering(a, prepared, now):
    approved = digest(prepared)
    record = json.loads((prepared / "preparation.json").read_text())
    record["spec"]["target"]["UserId"] = "AIDASYNTHETICCHANGED01"
    record["spec"]["approved_policy_names"] = []
    (prepared / "preparation.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="a202_reviewed_preparation_mismatch"):
        a.claim(prepared, now=now, reviewed_sha256=approved)
    assert not (prepared / "attempt.claim").exists()


def test_environment_and_config_isolation(a, prepared, spec, now):
    poisoned = {
        k: "PRIVATE_CANARY"
        for k in (
            "AWS_PROFILE",
            "AWS_ACCESS_KEY_ID",
            "AWS_ENDPOINT_URL",
            "HTTPS_PROXY",
            "PATH",
            "PYTHONPATH",
            "AWS_CA_BUNDLE",
        )
    }
    env = a.environment(prepared, spec, poisoned)
    assert "PRIVATE_CANARY" not in json.dumps(env)
    assert env["AWS_PROFILE"] == "future-f4-human-admin" and env["AWS_MAX_ATTEMPTS"] == "1"
    with (prepared / "human-config").open("a") as f:
        f.write("credential_process = PRIVATE_CANARY\n")
    with pytest.raises(ValueError):
        a.claim(prepared, now=now, reviewed_sha256=digest(prepared))
    assert not (prepared / "attempt.claim").exists()


@pytest.mark.parametrize("fault", [None, "command", "interrupt", "unexpected", "persistence"])
def test_documented_assembly_synthetic_only_no_replay(
    a, prepared, spec, now, monkeypatch, capsys, fault
):
    monkeypatch.setenv("FATA_A202_DIRECTORY", str(prepared))
    monkeypatch.setenv("FATA_A202_PREPARATION_DIGEST", digest(prepared))
    monkeypatch.setitem(sys.modules, "inline_policies", a)
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
        assert (
            kwargs["timeout"] == 120
            and kwargs["stdout_limit"] == 65536
            and kwargs["stderr_limit"] == 4096
        )
        assert kwargs["env"]["AWS_PROFILE"] == "future-f4-human-admin"
        if fault == "interrupt":
            raise KeyboardInterrupt
        value = page(spec)
        if fault == "unexpected":
            value["PolicyNames"] = ["Unexpected"]
        return capture(a, value, code=1 if fault == "command" else 0)

    monkeypatch.setattr(a.local.runner, "capture_owned", synthetic_only)
    write = a.base.write_private

    def save(path, body):
        if fault == "persistence" and path.name == "result.json":
            raise OSError("PRIVATE_CANARY")
        return write(path, body)

    monkeypatch.setattr(a.base, "write_private", save)
    block = re.findall(r"@'\n(.*?)\n'@", DOC.read_text(encoding="utf-8"), re.S)[1]
    if fault:
        with pytest.raises(SystemExit):
            exec(compile(block, "synthetic-only-procedure", "exec"), {})
        assert not (prepared / "result.json").exists()
    else:
        exec(compile(block, "synthetic-only-procedure", "exec"), {})
        assert json.loads((prepared / "result.json").read_text())["policy_count"] == 2
    if fault == "unexpected":
        assert json.loads((prepared / "observed-policy-names.json").read_text())["PolicyNames"] == [
            "Unexpected"
        ]
    with pytest.raises(SystemExit):
        exec(compile(block, "synthetic-only-procedure", "exec"), {})
    assert len(calls) == 1
    report = capsys.readouterr().out
    assert "PRIVATE_CANARY" not in report and "Unexpected" not in report
    assert all(n not in report for n in spec["approved_policy_names"])
    assert all(v not in report for i in (spec["caller"], spec["target"]) for v in i.values())


def test_no_launcher_and_existing_fences(a):
    tree = ast.parse((ROOT / "infra/aws/inline_policies.py").read_bytes())
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
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
        assert len(fn.body) == 1 and isinstance(fn.body[0], ast.Raise)


@pytest.mark.parametrize("names", [[], ["P"], ["P", "Q"]])
def test_actual_local_preparation_block_decodes_names_without_powershell_wrapping(
    a, spec, now, tmp_path, monkeypatch, capsys, names
):
    root = tmp_path / "local-preparation"
    root.mkdir(mode=0o700)
    inputs = {k: v for k, v in spec.items() if k not in {"approved_policy_names", "source_sha256"}}
    inputs["approved_policy_names_json"] = json.dumps(names)
    a.base.write_private(root / "input.json", json.dumps(inputs).encode())
    a.base.write_private(
        root / "reviewed-public-manifest.json",
        json.dumps({"format": "working-tree-review-v1", "files": a.sources()}).encode(),
    )
    monkeypatch.setenv("FATA_A202_DIRECTORY", str(root))
    monkeypatch.setenv("FATA_A202_REVIEW_MANIFEST", str(root / "reviewed-public-manifest.json"))
    monkeypatch.setitem(sys.modules, "inline_policies", a)
    original = a.prepare
    monkeypatch.setattr(a, "prepare", lambda spec, output, **_: original(spec, output, now=now))
    block = re.findall(r"@'\n(.*?)\n'@", DOC.read_text(encoding="utf-8"), re.S)[0]
    exec(compile(block, "synthetic-only-local-preparation", "exec"), {})
    assert a.review(root, now=now)["approved_policy_names"] == names
    assert not (root / "attempt.claim").exists()
    assert "no_execution_authorized" in capsys.readouterr().out


def test_native_powershell_preserves_masked_json_text_shape(tmp_path):
    exe = shutil.which("powershell")
    if not exe:
        pytest.skip("Windows PowerShell unavailable")
    script = tmp_path / "synthetic-json-roundtrip.ps1"
    script.write_text(
        "foreach($text in @('[]','[\"P\"]','[\"P\",\"Q\"]')) {\n"
        "  @{approved_policy_names_json=$text} | ConvertTo-Json -Compress\n}\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-File", str(script)],
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0
    rows = [json.loads(line) for line in result.stdout.decode().splitlines()]
    assert [json.loads(row["approved_policy_names_json"]) for row in rows] == [
        [],
        ["P"],
        ["P", "Q"],
    ]


def test_document_syntax_only():
    text = DOC.read_text(encoding="utf-8")
    for b in re.findall(r"@'\n(.*?)\n'@", text, re.S):
        ast.parse(b, feature_version=(3, 13))
    exe = shutil.which("powershell")
    if not exe:
        pytest.skip("Windows PowerShell parser unavailable")
    code = r"""
$doc=[IO.File]::ReadAllText('docs/implementation/f4-a2-state-02-supervised-procedure.md')
$blocks=[regex]::Matches($doc,'(?s)```powershell\r?\n(.*?)```')
foreach($b in $blocks){
    $t=$null;$e=$null
    $null=[Management.Automation.Language.Parser]::ParseInput($b.Groups[1].Value,[ref]$t,[ref]$e)
    if($e.Count){throw 'syntax_invalid'}
}
Write-Output ('parsed_blocks='+$blocks.Count)
"""
    p = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", code],
        cwd=ROOT,
        capture_output=True,
        timeout=15,
    )
    assert p.returncode == 0 and b"parsed_blocks=2" in p.stdout
