"""Two independent group-policy protocols; synthetic metadata only, no AWS process."""

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


@pytest.fixture
def p(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    s = importlib.util.spec_from_file_location(
        "group_policy_inventory", ROOT / "infra/aws/group_policy_inventory.py"
    )
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(params=["Managed", "Inline"])
def a(p, request):
    return p.Managed if request.param == "Managed" else p.Inline


@pytest.fixture
def now():
    return datetime(2030, 1, 1, tzinfo=UTC)


@pytest.fixture
def spec(p, a, tmp_path):
    exe = tmp_path / "aws.exe"
    exe.write_bytes(b"SYNTHETIC non-executable")
    values = (
        [
            {
                "PolicyName": "SyntheticManaged",
                "PolicyArn": "arn:aws:iam::aws:policy/SyntheticManaged",
            }
        ]
        if a is p.Managed
        else ["SyntheticInline"]
    )
    return {
        "caller": {
            "Account": "000000000000",
            "Arn": "arn:aws:iam::000000000000:user/human/future-f4-human-admin",
            "UserId": "AIDASYNTHETICHUMAN0001",
        },
        "group": {
            "GroupName": "FutureStateOperators",
            "Path": "/synthetic/",
            "Arn": "arn:aws:iam::000000000000:group/synthetic/FutureStateOperators",
            "GroupId": "AGPASYNTHETIC00000001",
        },
        "caller_provenance": "owner_attested_A1a",
        "group_provenance": "owner_prospectively_reviewed_group",
        "policy_expectations_provenance": "owner_independently_reviewed",
        a.ALLOW_FIELD: values,
        "cli_path": str(exe),
        "cli_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
        "login_cache_directory": str(tmp_path / "SYNTHETIC-never-read-cache"),
        "window_start": "2030-01-01T00:00:00Z",
        "window_end": "2030-01-01T00:30:00Z",
        "source_sha256": p.sources(),
    }


@pytest.fixture
def prepared(a, spec, now, tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    a.prepare(spec, root, now=now)
    return root


def digest(root):
    return (root / "preparation.sha256").read_text().strip()


def page(a, spec):
    return {a.RESPONSE_FIELD: copy.deepcopy(spec[a.ALLOW_FIELD]), "IsTruncated": False}


def capture(p, value, *, status="completed", code=0, stderr=b""):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return p.local.runner.Capture(code, status, bytearray(raw), bytearray(stderr))


def doc(a):
    return ROOT / ("docs/implementation/" + a.UNIT.lower() + "-supervised-procedure.md")


def test_fixed_commands_no_other_operation(p, a, spec):
    expected_action = "list-attached-group-policies" if a is p.Managed else "list-group-policies"
    assert a.command(spec["cli_path"]) == (
        spec["cli_path"],
        "iam",
        expected_action,
        "--group-name",
        "FutureStateOperators",
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
    for field in ("action", "operation", "profile", "group", "endpoint", "extra_args"):
        with pytest.raises(TypeError):
            a.command(spec["cli_path"], **{field: "PRIVATE_CANARY"})
    with pytest.raises(ValueError):
        a.command("aws")


def test_nonempty_and_empty_pages_private_only(p, a, spec, monkeypatch):
    writes = []
    monkeypatch.setattr(p.base, "write_private", lambda f, b: writes.append(json.loads(b)))
    c = capture(p, page(a, spec))
    result = a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert result == {
        "checkpoint": a.UNIT,
        "result": "metadata_page_verified",
        "policy_count": 1,
        "mfa_verified": False,
        "http_request_count_verified": False,
    }
    assert writes == [page(a, spec)] and not c.stdout and not c.stderr
    assert "Synthetic" not in json.dumps(result) and "000000000000" not in json.dumps(result)
    spec[a.ALLOW_FIELD] = []
    spec["policy_expectations_provenance"] = "owner_explicit_deny_all"
    assert (
        a.verify_capture(capture(p, page(a, spec)), spec, output=Path("SYNTHETIC-unused"))[
            "policy_count"
        ]
        == 0
    )


@pytest.mark.parametrize(
    "fault",
    [
        "json",
        "utf8",
        "null",
        "missing",
        "extra",
        "flag_type",
        "truncated",
        "marker",
        "next_token",
        "array_type",
        "entry_type",
        "duplicate",
        "count",
        "size",
        "duplicate_json",
        "wrong_kind",
    ],
)
def test_invalid_pages_never_retained(p, a, spec, monkeypatch, capsys, caplog, fault):
    value = page(a, spec)
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
    elif fault == "flag_type":
        value["IsTruncated"] = 0
    elif fault == "truncated":
        value["IsTruncated"] = True
    elif fault == "marker":
        value["Marker"] = ""
    elif fault == "next_token":
        value["NextToken"] = "PRIVATE_CANARY"
    elif fault == "array_type":
        value[a.RESPONSE_FIELD] = {}
    elif fault == "entry_type":
        value[a.RESPONSE_FIELD] = [None]
    elif fault == "duplicate":
        value[a.RESPONSE_FIELD] *= 2
    elif fault == "count":
        value[a.RESPONSE_FIELD] *= 41
    elif fault == "size":
        value = b" " * 65537
    elif fault == "duplicate_json":
        value = (
            "{" + '"' + a.RESPONSE_FIELD + '":[],"IsTruncated":true,"IsTruncated":false}'
        ).encode()
    else:
        value = {"PolicyNames" if a is p.Managed else "AttachedPolicies": [], "IsTruncated": False}
    monkeypatch.setattr(p.base, "write_private", lambda *_: pytest.fail("invalid_page_saved"))
    c = capture(p, value)
    with pytest.raises(ValueError) as error:
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert "PRIVATE_CANARY" not in str(error.value)
    assert not c.stdout and not c.stderr and not capsys.readouterr().out and not caplog.text


def test_unexpected_observation_is_not_expectation(p, a, spec, monkeypatch):
    value = page(a, spec)
    spec[a.ALLOW_FIELD] = []
    spec["policy_expectations_provenance"] = "owner_explicit_deny_all"
    writes = []
    monkeypatch.setattr(p.base, "write_private", lambda f, b: writes.append(json.loads(b)))
    with pytest.raises(ValueError, match="group_inventory_unexpected_policy_private_review"):
        a.verify_capture(capture(p, value), spec, output=Path("SYNTHETIC-unused"))
    assert writes == [value] and spec[a.ALLOW_FIELD] == []


def test_limits_and_exact_byte_boundary(p, a, spec, monkeypatch):
    maximum = 12 if a is p.Managed else 40
    values = (
        [
            {"PolicyName": f"P{i}", "PolicyArn": f"arn:aws:iam::aws:policy/P{i}"}
            for i in range(maximum)
        ]
        if a is p.Managed
        else [f"P{i}" for i in range(maximum)]
    )
    spec[a.ALLOW_FIELD] = values
    body = json.dumps(page(a, spec)).encode()
    body += b" " * (65536 - len(body))
    monkeypatch.setattr(p.base, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(p, body), spec, output=Path("SYNTHETIC-unused"))["policy_count"]
        == maximum
    )
    with pytest.raises(ValueError):
        a.entries(values + [values[0]], spec["caller"]["Account"])


def test_exact_managed_namespaces_and_inline_name_bounds(p, a, spec):
    if a is p.Managed:
        valid = [
            {
                "PolicyName": "CustomerSynthetic",
                "PolicyArn": "arn:aws:iam::000000000000:policy/project/CustomerSynthetic",
            }
        ]
        assert len(a.entries(valid, spec["caller"]["Account"])) == 1
        invalid = copy.deepcopy(valid)
        invalid[0]["PolicyArn"] = invalid[0]["PolicyArn"].replace("000000000000", "111111111111")
        with pytest.raises(ValueError):
            a.entries(invalid, spec["caller"]["Account"])
    else:
        assert a.entries(["N" * 128], spec["caller"]["Account"]) == {"N" * 128}
        for invalid in (["N" * 129], ["path/Name"], ["P\u00e9"], ["bad name"]):
            with pytest.raises(ValueError):
                a.entries(invalid, spec["caller"]["Account"])


def test_unavailable_or_implicit_policy_expectations_block_preparation(p, a, spec, now):
    absent = {k: v for k, v in spec.items() if k != a.ALLOW_FIELD}
    with pytest.raises(ValueError):
        a.validate(absent, now=now)
    spec[a.ALLOW_FIELD] = []
    with pytest.raises(ValueError, match="independent_policy_expectations_required"):
        a.validate(spec, now=now)
    spec["policy_expectations_provenance"] = "owner_explicit_deny_all"
    a.validate(spec, now=now)


@pytest.mark.parametrize(
    "fault",
    [
        "caller",
        "group_name",
        "group_account",
        "group_path",
        "group_id",
        "source",
        "binary",
        "window",
        "expired",
        "provenance",
        "expectation",
        "extra",
    ],
)
def test_identity_source_and_expectation_binding(p, a, spec, now, fault):
    if fault == "caller":
        spec["caller"]["Arn"] = "arn:aws:iam::000000000000:root"
    elif fault == "group_name":
        spec["group"]["GroupName"] = "Other"
    elif fault == "group_account":
        spec["group"]["Arn"] = spec["group"]["Arn"].replace("000000000000", "111111111111")
    elif fault == "group_path":
        spec["group"]["Path"] = "/other/"
    elif fault == "group_id":
        spec["group"]["GroupId"] = "short"
    elif fault == "source":
        spec["source_sha256"] = {}
    elif fault == "binary":
        Path(spec["cli_path"]).write_bytes(b"changed")
    elif fault == "window":
        spec["window_end"] = "2030-01-01T01:00:00Z"
    elif fault == "expired":
        now += timedelta(hours=1)
    elif fault == "provenance":
        spec["group_provenance"] = "state03_passed"
    elif fault == "expectation":
        spec["policy_expectations_provenance"] = "same_response"
    else:
        spec["action"] = "get-group-policy"
    with pytest.raises(ValueError):
        a.validate(spec, now=now)


@pytest.mark.parametrize(
    "fault", ["code", "stderr", "deadline", "cancelled", "interrupted", "cleanup_incomplete"]
)
def test_failed_capture_no_metadata(p, a, spec, monkeypatch, fault):
    monkeypatch.setattr(p.base, "write_private", lambda *_: pytest.fail("failed_capture_saved"))
    c = capture(
        p,
        page(a, spec),
        code=1 if fault == "code" else 0,
        status=fault if fault not in {"code", "stderr"} else "completed",
        stderr=b"PRIVATE_CANARY" if fault == "stderr" else b"",
    )
    with pytest.raises(ValueError):
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert not c.stdout and not c.stderr


def test_concurrent_claim_restart_and_cross_unit_rejection(p, a, prepared, now):
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
    fresh = p.local.runner.local("infra/aws/group_policy_inventory.py")
    with pytest.raises(FileExistsError):
        getattr(fresh, a.__name__).claim(prepared, now=now, reviewed_sha256=approved)
    other = p.Inline if a is p.Managed else p.Managed
    with pytest.raises(ValueError):
        other.claim(prepared, now=now, reviewed_sha256=approved)
    assert (prepared / "attempt.claim").read_bytes() == b"possibly_started\n"


def test_partial_fsync_claim_and_private_mutation(p, a, prepared, now, monkeypatch):
    approved = digest(prepared)
    with monkeypatch.context() as patch:
        patch.setattr(
            p.base.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY"))
        )
        with pytest.raises(OSError):
            a.claim(prepared, now=now, reviewed_sha256=approved)
    assert (prepared / "attempt.claim").exists()
    (prepared / "attempt.claim").write_bytes(b"partial")
    with pytest.raises(FileExistsError):
        a.claim(prepared, now=now, reviewed_sha256=approved)
    record = json.loads((prepared / "preparation.json").read_text())
    record["spec"]["group"]["GroupId"] = "AGPASYNTHETICCHANGED1"
    (prepared / "preparation.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="group_inventory_reviewed_preparation_mismatch"):
        a.claim(prepared, now=now, reviewed_sha256=approved)


def test_environment_and_config_isolation(p, a, prepared, spec, now):
    inherited = {
        k: "PRIVATE_CANARY"
        for k in (
            "AWS_PROFILE",
            "AWS_ACCESS_KEY_ID",
            "AWS_ENDPOINT_URL",
            "HTTPS_PROXY",
            "AWS_CA_BUNDLE",
            "PYTHONPATH",
            "PATH",
        )
    }
    env = a.environment(prepared, spec, inherited)
    assert "PRIVATE_CANARY" not in json.dumps(env)
    assert env["AWS_PROFILE"] == "future-f4-human-admin" and env["AWS_MAX_ATTEMPTS"] == "1"
    with (prepared / "human-config").open("a") as f:
        f.write("credential_process = PRIVATE_CANARY\n")
    with pytest.raises(ValueError):
        a.claim(prepared, now=now, reviewed_sha256=digest(prepared))
    assert not (prepared / "attempt.claim").exists()


@pytest.mark.parametrize("fault", [None, "interrupt", "unexpected", "persistence"])
def test_actual_capture_blocks_mocked_no_other_call(
    p, a, prepared, spec, now, monkeypatch, capsys, fault
):
    prefix = "FATA_GP_MANAGED" if a is p.Managed else "FATA_GP_INLINE"
    monkeypatch.setenv(prefix + "_DIRECTORY", str(prepared))
    monkeypatch.setenv(prefix + "_DIGEST", digest(prepared))
    monkeypatch.setitem(sys.modules, "group_policy_inventory", p)
    original = a.claim
    monkeypatch.setattr(
        a,
        "claim",
        lambda root, **kw: original(
            root,
            now=now,
            reviewed_sha256=kw["reviewed_sha256"],
            diagnostics=kw.get("diagnostics"),
        ),
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
        value = page(a, spec)
        if fault == "unexpected":
            value[a.RESPONSE_FIELD] = (
                [{"PolicyName": "Unexpected", "PolicyArn": "arn:aws:iam::aws:policy/Unexpected"}]
                if a is p.Managed
                else ["Unexpected"]
            )
        return capture(p, value)

    monkeypatch.setattr(p.local.runner, "capture_owned", synthetic_only)
    write = p.base.write_private

    def save(path, body):
        if fault == "persistence" and path.name == "result.json":
            raise OSError("PRIVATE_CANARY")
        return write(path, body)

    monkeypatch.setattr(p.base, "write_private", save)
    block = re.findall(r"@'\n(.*?)\n'@", doc(a).read_text(encoding="utf-8"), re.S)[1]
    if fault:
        with pytest.raises(SystemExit):
            exec(compile(block, "synthetic-only-capture", "exec"), {})
        assert not (prepared / "result.json").exists()
    else:
        exec(compile(block, "synthetic-only-capture", "exec"), {})
        assert json.loads((prepared / "result.json").read_text())["checkpoint"] == a.UNIT
    with pytest.raises(SystemExit):
        exec(compile(block, "synthetic-only-capture", "exec"), {})
    assert len(calls) == 1
    report = capsys.readouterr().out
    assert (
        "Synthetic" not in report and "Unexpected" not in report and "PRIVATE_CANARY" not in report
    )
    assert all(v not in report for v in spec["caller"].values())
    assert all(v not in report for v in spec["group"].values())


@pytest.mark.parametrize("empty", [False, True])
def test_actual_local_preparation_json_text(p, a, spec, now, tmp_path, monkeypatch, capsys, empty):
    root = tmp_path / "new-private"
    root.mkdir(mode=0o700)
    inputs = {k: v for k, v in spec.items() if k not in {a.ALLOW_FIELD, "source_sha256"}}
    expected = [] if empty else spec[a.ALLOW_FIELD]
    inputs["policy_allowlist_json"] = json.dumps(expected)
    if empty:
        inputs["policy_expectations_provenance"] = "owner_explicit_deny_all"
    p.base.write_private(root / "input.json", json.dumps(inputs).encode())
    p.base.write_private(
        root / "reviewed-manifest.json",
        json.dumps({"format": "working-tree-review-v1", "files": p.sources()}).encode(),
    )
    prefix = "FATA_GP_MANAGED" if a is p.Managed else "FATA_GP_INLINE"
    monkeypatch.setenv(prefix + "_DIRECTORY", str(root))
    monkeypatch.setenv(prefix + "_MANIFEST", str(root / "reviewed-manifest.json"))
    monkeypatch.setitem(sys.modules, "group_policy_inventory", p)
    original = a.prepare
    monkeypatch.setattr(a, "prepare", lambda spec, output, **_: original(spec, output, now=now))
    block = re.findall(r"@'\n(.*?)\n'@", doc(a).read_text(encoding="utf-8"), re.S)[0]
    exec(compile(block, "synthetic-only-local-preparation", "exec"), {})
    assert a.review(root, now=now)[a.ALLOW_FIELD] == expected
    assert not (root / "attempt.claim").exists()
    assert "no_execution_authorized" in capsys.readouterr().out


def test_no_launcher_and_prior_live_fences(p):
    tree = ast.parse((ROOT / "infra/aws/group_policy_inventory.py").read_bytes())
    assert not any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"Popen", "run", "capture_owned", "execute_live", "execute_account"}
        for n in ast.walk(tree)
    )
    for file, name in (
        ("infra/aws/human_sts.py", "execute_live"),
        ("infra/aws/private_command_runner.py", "execute_account"),
    ):
        tree = ast.parse((ROOT / file).read_bytes())
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
        assert len(fn.body) == 1 and isinstance(fn.body[0], ast.Raise)


def test_unknown_or_modified_contract_cannot_build_any_command(p, monkeypatch):
    class Other(p.Managed):
        ACTION = "put-group-policy"

    for contract in (Other, p._Inventory):
        with pytest.raises(ValueError, match="closed_contract_required"):
            contract.command(str(ROOT / "SYNTHETIC-aws.exe"))
    with monkeypatch.context() as patch:
        patch.setattr(p.Managed, "ACTION", "put-group-policy")
        with pytest.raises(ValueError, match="closed_contract_required"):
            p.Managed.command(str(ROOT / "SYNTHETIC-aws.exe"))


def test_both_procedures_syntax_only(p, a):
    for block in re.findall(r"@'\n(.*?)\n'@", doc(a).read_text(encoding="utf-8"), re.S):
        ast.parse(block, feature_version=(3, 13))
    exe = shutil.which("powershell")
    if not exe:
        pytest.skip("Windows PowerShell unavailable")
    path = doc(a).relative_to(ROOT).as_posix()
    code = """
$text=[IO.File]::ReadAllText('@@PATH@@')
$blocks=[regex]::Matches($text,'(?s)```powershell\r?\n(.*?)```')
foreach($b in $blocks){
    $t=$null;$e=$null
    $null=[Management.Automation.Language.Parser]::ParseInput($b.Groups[1].Value,[ref]$t,[ref]$e)
    if($e.Count){throw 'syntax_invalid'}
}
Write-Output ('parsed_blocks='+$blocks.Count)
""".replace("@@PATH@@", path)
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", code],
        cwd=ROOT,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0 and b"parsed_blocks=2" in result.stdout
