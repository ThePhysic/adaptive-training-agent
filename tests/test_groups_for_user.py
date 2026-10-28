"""State-03 synthetic only: no native AWS, real IAM identity or cache access."""

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
DOC = ROOT / "docs/implementation/f4-a2-state-03-supervised-procedure.md"


@pytest.fixture
def a(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    s = importlib.util.spec_from_file_location(
        "groups_for_user", ROOT / "infra/aws/groups_for_user.py"
    )
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def group(number=0, path="/"):
    name = f"Synthetic{number}"
    return {
        "GroupName": name,
        "GroupId": f"AGPASYNTHETIC{number:08d}",
        "Path": path,
        "Arn": f"arn:aws:iam::000000000000:group{path}{name}",
    }


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
        "approved_groups": [group(), group(1, "/project/nested/")],
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


def page(spec):
    return {
        "Groups": [g | {"CreateDate": "2029-01-02T03:04:05Z"} for g in spec["approved_groups"]],
        "IsTruncated": False,
    }


def capture(a, value, *, code=0, status="completed", stderr=b""):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return a.local.runner.Capture(code, status, bytearray(raw), bytearray(stderr))


def test_exact_fixed_command(a, spec):
    assert a.command(spec["cli_path"]) == (
        spec["cli_path"],
        "iam",
        "list-groups-for-user",
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


def test_nonzero_groups_private_evidence_and_sanitized_result(a, spec, prepared):
    c = capture(a, page(spec))
    result = a.verify_capture(c, spec, output=prepared)
    assert result == {
        "checkpoint": "F4-A2-state-03",
        "result": "metadata_page_verified",
        "group_count": 2,
        "mfa_verified": False,
        "http_request_count_verified": False,
    }
    assert json.loads((prepared / "observed-groups.json").read_text()) == page(spec)
    assert not c.stdout and not c.stderr
    assert all(v not in json.dumps(result) for g in spec["approved_groups"] for v in g.values())


@pytest.mark.parametrize("count", [0, 4])
def test_empty_four_group_boundary_and_order(a, spec, monkeypatch, count):
    spec["approved_groups"] = [group(i) for i in range(count)]
    value = page(spec)
    value["Groups"].reverse()
    monkeypatch.setattr(a.base, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, value), spec, output=Path("SYNTHETIC-unused"))["group_count"]
        == count
    )


@pytest.mark.parametrize("date", ["2029-01-02T03:04:05+00:00", "2029-01-02T04:04:05.123456+01:00"])
def test_supported_native_date_shapes(a, spec, monkeypatch, date):
    value = page(spec)
    value["Groups"][0]["CreateDate"] = date
    monkeypatch.setattr(a.base, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, value), spec, output=Path("SYNTHETIC-unused"))["group_count"]
        == 2
    )


@pytest.mark.parametrize("date", ["2029-01-02T03:04:05+01:99", "2029-01-02T03:04:05+24:00"])
def test_invalid_offset_components_never_normalized_into_valid_metadata(a, spec, monkeypatch, date):
    response = page(spec)
    response["Groups"][0]["CreateDate"] = date
    monkeypatch.setattr(
        a.base, "write_private", lambda *_: pytest.fail("invalid_timestamp_written")
    )
    with pytest.raises(ValueError, match="a203_group_createdate_invalid"):
        a.verify_capture(capture(a, response), spec, output=Path("SYNTHETIC-unused"))


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
        "token",
        "array",
        "count",
        "size",
        "duplicate_json",
        "missing_id",
        "extra_group",
        "foreign",
        "partition",
        "service",
        "region",
        "aws_account",
        "path",
        "path_mismatch",
        "name",
        "id",
        "date_missing",
        "date_invalid",
        "date_naive",
        "duplicate",
        "duplicate_id",
        "duplicate_name",
        "case_ambiguity",
    ],
)
def test_malformed_group_pages_never_promoted(a, spec, monkeypatch, capsys, caplog, fault):
    value = page(spec)
    g = value["Groups"][0]
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
    elif fault == "token":
        value["NextToken"] = "PRIVATE_CANARY"
    elif fault == "array":
        value["Groups"] = {}
    elif fault == "count":
        value["Groups"] = [group(i) | {"CreateDate": "2029-01-02T03:04:05Z"} for i in range(5)]
    elif fault == "size":
        value = b" " * 65537
    elif fault == "duplicate_json":
        value = b'{"Groups":[],"IsTruncated":true,"IsTruncated":false}'
    elif fault == "missing_id":
        g.pop("GroupId")
    elif fault == "extra_group":
        g["PRIVATE_CANARY"] = "private"
    elif fault == "foreign":
        g["Arn"] = g["Arn"].replace("000000000000", "111111111111")
    elif fault == "partition":
        g["Arn"] = g["Arn"].replace("arn:aws:", "arn:aws-cn:")
    elif fault == "service":
        g["Arn"] = g["Arn"].replace(":iam:", ":s3:")
    elif fault == "region":
        g["Arn"] = g["Arn"].replace("iam::", "iam:us-east-1:")
    elif fault == "aws_account":
        g["Arn"] = g["Arn"].replace("000000000000", "aws")
    elif fault == "path":
        g["Path"] = "/../"
    elif fault == "path_mismatch":
        g["Path"] = "/other/"
    elif fault == "name":
        g["GroupName"] = "bad name"
    elif fault == "id":
        g["GroupId"] = "short"
    elif fault == "date_missing":
        g.pop("CreateDate")
    elif fault == "date_invalid":
        g["CreateDate"] = "2029-02-30T03:04:05Z"
    elif fault == "date_naive":
        g["CreateDate"] = "2029-01-02T03:04:05"
    elif fault == "duplicate":
        value["Groups"] = [g, copy.deepcopy(g)]
    elif fault == "duplicate_id":
        value["Groups"][1]["GroupId"] = g["GroupId"]
    elif fault == "duplicate_name":
        value["Groups"][1].update(
            GroupName=g["GroupName"],
            Arn="arn:aws:iam::000000000000:group/project/nested/" + g["GroupName"],
        )
    else:
        value["Groups"][1].update(
            GroupName=g["GroupName"].lower(),
            Arn="arn:aws:iam::000000000000:group/project/nested/" + g["GroupName"].lower(),
        )
    monkeypatch.setattr(a.base, "write_private", lambda *_: pytest.fail("invalid_page_written"))
    c = capture(a, value)
    with pytest.raises(ValueError) as error:
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert "PRIVATE_CANARY" not in str(error.value)
    assert not c.stdout and not c.stderr and not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize("mismatch", ["GroupId", "Path", "new_group"])
def test_well_formed_unexpected_identity_retained_privately(a, spec, monkeypatch, mismatch):
    value = page(spec)
    if mismatch == "GroupId":
        value["Groups"][0]["GroupId"] = "AGPASYNTHETICDIFFERENT"
    elif mismatch == "Path":
        value["Groups"][0].update(
            Path="/new/", Arn="arn:aws:iam::000000000000:group/new/Synthetic0"
        )
    else:
        value["Groups"] = [group(3) | {"CreateDate": "2029-01-02T03:04:05Z"}]
    written = []
    monkeypatch.setattr(a.base, "write_private", lambda p, b: written.append((p.name, b)))
    with pytest.raises(ValueError, match="^a203_unexpected_group_private_review$"):
        a.verify_capture(capture(a, value), spec, output=Path("SYNTHETIC-unused"))
    assert len(written) == 1 and json.loads(written[0][1]) == value


def test_empty_allowlist_does_not_assume_empty_membership(a, spec, monkeypatch):
    response = page(spec)
    spec["approved_groups"] = []
    observations = []
    monkeypatch.setattr(a.base, "write_private", lambda p, b: observations.append(json.loads(b)))
    with pytest.raises(ValueError, match="a203_unexpected_group_private_review"):
        a.verify_capture(capture(a, response), spec, output=Path("SYNTHETIC-unused"))
    assert observations == [response] and len(response["Groups"]) == 2


@pytest.mark.parametrize(
    "fault",
    [
        "caller",
        "target",
        "userid",
        "source",
        "binary",
        "expired",
        "window",
        "provenance",
        "extra",
        "groups",
    ],
)
def test_preparation_context_fail_closed(a, spec, now, fault):
    if fault == "caller":
        spec["caller"]["Arn"] = spec["target"]["Arn"]
    elif fault == "target":
        spec["target"]["Account"] = "111111111111"
    elif fault == "userid":
        spec["target"]["UserId"] = spec["caller"]["UserId"]
    elif fault == "source":
        spec["source_sha256"] = {}
    elif fault == "binary":
        Path(spec["cli_path"]).write_bytes(b"changed")
    elif fault == "expired":
        now += timedelta(hours=1)
    elif fault == "window":
        spec["window_end"] = "2030-01-01T01:00:00Z"
    elif fault == "provenance":
        spec["target_provenance"] = "unverified_response"
    elif fault == "extra":
        spec["action"] = "get-group"
    else:
        spec["approved_groups"] = [group(i) for i in range(5)]
    with pytest.raises(ValueError):
        a.validate(spec, now=now)


@pytest.mark.parametrize(
    "fault", ["code", "stderr", "deadline", "cancelled", "interrupted", "cleanup_incomplete"]
)
def test_failed_capture_cleared(a, spec, monkeypatch, fault):
    c = capture(
        a,
        page(spec),
        code=1 if fault == "code" else 0,
        stderr=b"PRIVATE_CANARY" if fault == "stderr" else b"",
        status=fault if fault not in {"code", "stderr"} else "completed",
    )
    monkeypatch.setattr(a.base, "write_private", lambda *_: pytest.fail("failed_capture_written"))
    with pytest.raises(ValueError):
        a.verify_capture(c, spec, output=Path("SYNTHETIC-unused"))
    assert not c.stdout and not c.stderr


def test_claim_concurrency_restart_and_old_kind_rejection(a, prepared, now):
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
    fresh = a.local.runner.local("infra/aws/groups_for_user.py")
    with pytest.raises(FileExistsError):
        fresh.claim(prepared, now=now, reviewed_sha256=approved)
    with pytest.raises(ValueError):
        a.base.review(prepared, now=now)


def test_failed_fsync_and_partial_claim_never_replay(a, prepared, now, monkeypatch):
    approved = digest(prepared)
    with monkeypatch.context() as patch:
        patch.setattr(
            a.base.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY"))
        )
        with pytest.raises(OSError):
            a.claim(prepared, now=now, reviewed_sha256=approved)
    assert (prepared / "attempt.claim").exists()
    (prepared / "attempt.claim").write_bytes(b"partial")
    with pytest.raises(FileExistsError):
        a.claim(prepared, now=now, reviewed_sha256=approved)
    assert (prepared / "attempt.claim").read_bytes() == b"partial"


def test_private_binding_mutation_and_environment(a, prepared, spec, now):
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
    assert "PRIVATE_CANARY" not in json.dumps(env) and env["AWS_PROFILE"] == "future-f4-human-admin"
    approved = digest(prepared)
    record = json.loads((prepared / "preparation.json").read_text())
    record["spec"]["approved_groups"][0]["GroupId"] = "AGPASYNTHETICCHANGED1"
    (prepared / "preparation.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="a203_reviewed_preparation_mismatch"):
        a.claim(prepared, now=now, reviewed_sha256=approved)
    assert not (prepared / "attempt.claim").exists()


@pytest.mark.parametrize("fault", ["config", "credentials"])
def test_prepared_login_overrides_fail_before_claim(a, prepared, now, fault):
    approved = digest(prepared)
    if fault == "config":
        with (prepared / "human-config").open("a") as f:
            f.write("credential_process = PRIVATE_CANARY\n")
    else:
        (prepared / "empty-credentials").write_text("PRIVATE_CANARY")
    with pytest.raises(ValueError):
        a.claim(prepared, now=now, reviewed_sha256=approved)
    assert not (prepared / "attempt.claim").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("GroupName", "N" * 129),
        ("GroupId", "I" * 129),
        ("Path", "/" + "p" * 511 + "/"),
        ("Arn", "a" * 2049),
        ("GroupName", None),
        ("GroupId", 3),
        ("Path", []),
        ("Arn", {}),
        ("CreateDate", 0),
    ],
)
def test_group_field_types_and_upper_bounds(a, spec, monkeypatch, field, value):
    response = page(spec)
    response["Groups"][0][field] = value
    monkeypatch.setattr(a.base, "write_private", lambda *_: pytest.fail("invalid_group_written"))
    with pytest.raises(ValueError):
        a.verify_capture(capture(a, response), spec, output=Path("SYNTHETIC-unused"))


@pytest.mark.parametrize("fault", [None, "command", "interrupt", "unexpected", "persistence"])
def test_documented_capture_mocked_before_execution_no_replay(
    a, prepared, spec, now, monkeypatch, capsys, fault
):
    monkeypatch.setenv("FATA_A203_DIRECTORY", str(prepared))
    monkeypatch.setenv("FATA_A203_PREPARATION_DIGEST", digest(prepared))
    monkeypatch.setitem(sys.modules, "groups_for_user", a)
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
            value["Groups"] = [group(3) | {"CreateDate": "2029-01-02T03:04:05Z"}]
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
            exec(compile(block, "synthetic-only-capture", "exec"), {})
        assert not (prepared / "result.json").exists()
    else:
        exec(compile(block, "synthetic-only-capture", "exec"), {})
        assert json.loads((prepared / "result.json").read_text())["group_count"] == 2
    with pytest.raises(SystemExit):
        exec(compile(block, "synthetic-only-capture", "exec"), {})
    assert len(calls) == 1
    report = capsys.readouterr().out
    assert "PRIVATE_CANARY" not in report
    assert all(v not in report for g in spec["approved_groups"] for v in g.values())
    assert all(v not in report for i in (spec["caller"], spec["target"]) for v in i.values())


@pytest.mark.parametrize("count", [0, 1, 4])
def test_local_preparation_block_preserves_group_json(
    a, spec, now, tmp_path, monkeypatch, capsys, count
):
    root = tmp_path / "local-preparation"
    root.mkdir(mode=0o700)
    inputs = {k: v for k, v in spec.items() if k not in {"approved_groups", "source_sha256"}}
    expected = [group(i) for i in range(count)]
    inputs["approved_groups_json"] = json.dumps(expected)
    a.base.write_private(root / "input.json", json.dumps(inputs).encode())
    a.base.write_private(
        root / "reviewed-manifest.json",
        json.dumps({"format": "working-tree-review-v1", "files": a.sources()}).encode(),
    )
    monkeypatch.setenv("FATA_A203_DIRECTORY", str(root))
    monkeypatch.setenv("FATA_A203_REVIEW_MANIFEST", str(root / "reviewed-manifest.json"))
    monkeypatch.setitem(sys.modules, "groups_for_user", a)
    original = a.prepare
    monkeypatch.setattr(a, "prepare", lambda spec, output, **_: original(spec, output, now=now))
    block = re.findall(r"@'\n(.*?)\n'@", DOC.read_text(encoding="utf-8"), re.S)[0]
    exec(compile(block, "synthetic-only-preparation", "exec"), {})
    assert a.review(root, now=now)["approved_groups"] == expected
    assert not (root / "attempt.claim").exists()
    assert "no_execution_authorized" in capsys.readouterr().out


def test_byte_and_field_length_boundaries(a, spec, monkeypatch):
    identity = group()
    identity.update(GroupName="G" * 128, GroupId="I" * 128, Path="/" + "x" * 510 + "/")
    identity["Arn"] = "arn:aws:iam::000000000000:group" + identity["Path"] + identity["GroupName"]
    spec["approved_groups"] = [identity]
    body = json.dumps(page(spec)).encode()
    body += b" " * (a.LIMIT - len(body))
    monkeypatch.setattr(a.base, "write_private", lambda *_: None)
    assert (
        a.verify_capture(capture(a, body), spec, output=Path("SYNTHETIC-unused"))["group_count"]
        == 1
    )


def test_no_launcher_and_previous_fences_unchanged(a):
    tree = ast.parse((ROOT / "infra/aws/groups_for_user.py").read_bytes())
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


def test_document_syntax_only():
    for b in re.findall(r"@'\n(.*?)\n'@", DOC.read_text(encoding="utf-8"), re.S):
        ast.parse(b, feature_version=(3, 13))
    exe = shutil.which("powershell")
    if not exe:
        pytest.skip("Windows PowerShell parser unavailable")
    code = r"""
$doc=[IO.File]::ReadAllText('docs/implementation/f4-a2-state-03-supervised-procedure.md')
$blocks=[regex]::Matches($doc,'(?s)```powershell\r?\n(.*?)```')
foreach($b in $blocks){
    $t=$null;$e=$null
    $null=[Management.Automation.Language.Parser]::ParseInput($b.Groups[1].Value,[ref]$t,[ref]$e)
    if($e.Count){throw 'syntax_invalid'}
}
Write-Output ('parsed_blocks='+$blocks.Count)
"""
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", code],
        cwd=ROOT,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0 and b"parsed_blocks=2" in result.stdout
