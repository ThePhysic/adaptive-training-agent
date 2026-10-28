"""Execute the documented blocks with synthetic files and a mandatory fake capture.

Bulk tests bypass only OS ACL attestation on their temporary synthetic paths.
Existing inventory/runner suites separately exercise real Windows ACL/ownership.
No AWS executable, login cache or native AWS response is used here.
"""

import asyncio
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
import test_group_policy_inventory as fixtures

a, p, spec, now = fixtures.a, fixtures.p, fixtures.spec, fixtures.now


@pytest.fixture
def workflow(p, a, spec, now, tmp_path, monkeypatch):
    # This temporary-only fixture isolates workflow logic from repeated icacls
    # subprocesses. No real records or system credential sources are accessed.
    monkeypatch.setattr(p.local, "private", lambda path: Path(path))
    root = tmp_path / "SYNTHETIC-preparation"
    root.mkdir(mode=0o700)
    a.prepare(spec, root, now=now)
    prefix = "FATA_GP_MANAGED" if a is p.Managed else "FATA_GP_INLINE"
    monkeypatch.setenv(prefix + "_DIRECTORY", str(root))
    monkeypatch.setenv(prefix + "_DIGEST", fixtures.digest(root))
    monkeypatch.setitem(sys.modules, "group_policy_inventory", p)
    claim = a.claim
    monkeypatch.setattr(a, "claim", lambda path, **kw: claim(path, **{**kw, "now": now}))
    script = re.findall(r"@'\n(.*?)\n'@", fixtures.doc(a).read_text(encoding="utf-8"), re.S)[1]
    code = compile(script, "synthetic-documented-group-workflow", "exec")
    calls, returned, events = [], [], []

    def fake(argv, **kwargs):
        calls.append(argv)
        events.append("capture")
        assert argv == a.command(spec["cli_path"])
        assert kwargs["timeout"] == 120 and kwargs["stdout_limit"] == 65536
        assert kwargs["stderr_limit"] == 4096
        assert kwargs["env"]["AWS_PROFILE"] == "future-f4-human-admin"
        assert kwargs["env"]["AWS_MAX_ATTEMPTS"] == "1"
        result = fixtures.capture(p, fixtures.page(a, spec))
        result.process_release = "may_have_released"
        result.cleanup_state = "completed"
        returned.append(result)
        return result

    # Every code execution in this module has a fake capture installed first.
    monkeypatch.setattr(p.local.runner, "capture_owned", fake)
    write = p.base.write_private

    def save(path, body):
        events.append(path.name)
        return write(path, body)

    monkeypatch.setattr(p.base, "write_private", save)
    return {
        "root": root,
        "code": code,
        "calls": calls,
        "returned": returned,
        "events": events,
        "write": save,
        "fake": fake,
        "prefix": prefix,
    }


def execute(workflow):
    try:
        exec(workflow["code"], {})
    except SystemExit as error:
        assert error.code == 1
        return False
    return True


def report(capsys):
    output = capsys.readouterr()
    assert not output.err
    assert "PRIVATE_CANARY" not in output.out
    assert "arn:" not in output.out and "000000000000" not in output.out
    assert "Synthetic" not in output.out and "Unexpected" not in output.out
    return json.loads(output.out)


def assert_blocked_reuse(workflow, capsys, *, diagnostic_record="not_attempted"):
    root = workflow["root"]
    before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    calls = len(workflow["calls"])
    assert not execute(workflow)
    result = report(capsys)
    assert result["result"] == "stopped" and result["diagnostic_record"] == diagnostic_record
    assert len(workflow["calls"]) == calls
    assert before == {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}


def test_documented_success_persists_only_after_cleanup(p, a, workflow, monkeypatch, capsys):
    original = workflow["fake"]

    def tracked(*args, **kwargs):
        c = original(*args, **kwargs)
        clear = c.clear

        def clear_and_note():
            workflow["events"].append("clear")
            clear()

        c.clear = clear_and_note
        return c

    monkeypatch.setattr(p.local.runner, "capture_owned", tracked)
    assert execute(workflow)
    result = report(capsys)
    assert result["checkpoint"] == a.UNIT and result["result"] == "metadata_page_verified"
    assert workflow["events"] == [
        "attempt.claim",
        "capture",
        "observed-policies.json",
        "clear",
        "clear",
        "result.json",
    ]
    assert not (workflow["root"] / "failure-diagnostic.json").exists()
    assert_blocked_reuse(workflow, capsys)


@pytest.mark.parametrize(
    "fault",
    ["digest", "identity", "source", "config", "expired", "binary", "other_unit", "credentials"],
)
def test_pre_release_failure_cannot_invoke_or_write_diagnostics(
    p, a, spec, workflow, monkeypatch, capsys, fault
):
    root = workflow["root"]
    if fault == "digest":
        monkeypatch.setenv(workflow["prefix"] + "_DIGEST", "a" * 64)
    elif fault == "config":
        (root / "human-config").write_text("credential_process = PRIVATE_CANARY")
    elif fault == "binary":
        Path(spec["cli_path"]).write_bytes(b"SYNTHETIC binary changed")
    elif fault == "credentials":
        (root / "empty-credentials").write_bytes(b"PRIVATE_CANARY")
    else:
        record = json.loads((root / "preparation.json").read_text())
        if fault == "identity":
            record["spec"]["caller"]["Arn"] = "PRIVATE_CANARY"
        elif fault == "source":
            record["spec"]["source_sha256"] = {}
        elif fault == "expired":
            record["spec"]["window_end"] = "2029-01-01T00:00:00Z"
        else:
            other = p.Inline if a is p.Managed else p.Managed
            record["kind"] = "offline-" + other.UNIT + "-v1"
        (root / "preparation.json").write_text(json.dumps(record))
        monkeypatch.setenv(workflow["prefix"] + "_DIGEST", fixtures.digest(root))
    assert not execute(workflow)
    result = report(capsys)
    assert result["failure_code"] == "pre_release_failure"
    assert result["process_release"] == "not_released"
    assert result["diagnostic_record"] == "not_attempted"
    assert not workflow["calls"] and not (root / "attempt.claim").exists()
    assert not (root / "failure-diagnostic.json").exists()


@pytest.mark.parametrize("fault", ["claim_partial", "claim_written", "claim_interrupt"])
def test_failed_claim_never_acquires_diagnostic_write_authority(
    p, workflow, monkeypatch, capsys, fault
):
    save = workflow["write"]

    def fail(path, body):
        if path.name == "attempt.claim":
            save(path, b"partial" if fault == "claim_partial" else body)
            if fault == "claim_interrupt":
                raise KeyboardInterrupt("PRIVATE_CANARY")
            raise OSError("PRIVATE_CANARY")
        return save(path, body)

    monkeypatch.setattr(p.base, "write_private", fail)
    assert not execute(workflow)
    result = report(capsys)
    assert result["process_release"] == "not_released"
    assert result["diagnostic_record"] == "not_attempted"
    assert not workflow["calls"] and (workflow["root"] / "attempt.claim").exists()
    assert_blocked_reuse(workflow, capsys)


FAULTS = [
    ("setup", "pre_release_validation_failed"),
    ("launch", "wrapper_launch_or_ownership_failed"),
    ("ownership", "wrapper_launch_or_ownership_failed"),
    ("timeout", "timeout"),
    ("cancel", "cancelled"),
    ("interrupt", "cancelled"),
    ("escaping", "capture_exception_unclassified"),
    ("nonzero", "native_exit_nonzero"),
    ("unknown_exit", "native_exit_unknown"),
    ("stderr", "stderr_present"),
    ("overflow", "capture_overflow"),
    ("json", "invalid_json"),
    ("duplicate_json", "invalid_json"),
    ("schema", "response_schema"),
    ("page", "incomplete_page"),
    ("metadata", "invalid_policy_metadata"),
    ("allowlist", "unexpected_policy"),
    ("observation", "observation_persistence_failed"),
    ("observation_partial", "observation_persistence_failed"),
    ("result", "result_persistence_failed"),
    ("result_partial", "result_persistence_failed"),
    ("result_written", "result_persistence_failed"),
    ("cleanup", "cleanup_uncertain"),
    ("clear_once", "validation_unclassified"),
    ("clear_twice", "validation_unclassified"),
]


@pytest.mark.parametrize("fault,expected", FAULTS)
def test_documented_failure_pipeline_is_one_shot_private_and_fail_closed(
    p, a, spec, workflow, monkeypatch, capsys, caplog, fault, expected
):
    root = workflow["root"]
    save = workflow["write"]
    if fault == "setup":
        monkeypatch.setattr(
            a, "environment", lambda *args: (_ for _ in ()).throw(ValueError("PRIVATE_CANARY"))
        )

    def failed_capture(argv, **kwargs):
        c = workflow["fake"](argv, **kwargs)
        if fault in {"interrupt", "cancel", "escaping"}:
            raise {
                "interrupt": KeyboardInterrupt,
                "cancel": asyncio.CancelledError,
                "escaping": RuntimeError,
            }[fault]("PRIVATE_CANARY")
        if fault in {"launch", "ownership"}:
            c.status, c.native_exit, c.process_release = (
                "launch_or_ownership_failed",
                None,
                "not_released",
            )
        elif fault == "timeout":
            c.status = "deadline"
        elif fault == "nonzero":
            c.native_exit = 254
        elif fault == "unknown_exit":
            c.native_exit = None
        elif fault == "stderr":
            c.stderr.extend(b"AccessDenied ExpiredToken PRIVATE_CANARY")
        elif fault == "overflow":
            c.status = "output_limit"
        elif fault == "cleanup":
            c.cleanup_state = "uncertain"
        elif fault == "json":
            c.stdout[:] = b"{PRIVATE_CANARY"
        elif fault == "duplicate_json":
            c.stdout[:] = b'{"IsTruncated":true,"IsTruncated":false}'
        elif fault in {"schema", "page", "metadata", "allowlist"}:
            value = fixtures.page(a, spec)
            if fault == "schema":
                value["PRIVATE_CANARY"] = 1
            elif fault == "page":
                value["IsTruncated"] = True
            elif fault == "metadata":
                value[a.RESPONSE_FIELD] = [None]
            else:
                value[a.RESPONSE_FIELD] = (
                    [
                        {
                            "PolicyName": "Unexpected",
                            "PolicyArn": "arn:aws:iam::aws:policy/Unexpected",
                        }
                    ]
                    if a is p.Managed
                    else ["Unexpected"]
                )
            c.stdout[:] = json.dumps(value).encode()
        if fault in {"clear_once", "clear_twice"}:
            clear = c.clear
            count = 0

            def broken_clear():
                nonlocal count
                count += 1
                clear()
                if count == 1 or fault == "clear_twice":
                    raise OSError("PRIVATE_CANARY")

            c.clear = broken_clear
        return c

    monkeypatch.setattr(p.local.runner, "capture_owned", failed_capture)

    def failed_write(path, body):
        stage = (
            "observation"
            if path.name == "observed-policies.json"
            else ("result" if path.name == "result.json" else "unused")
        )
        if fault in {stage, stage + "_partial", stage + "_written"}:
            if fault.endswith("partial"):
                save(path, body[:7])
            elif fault.endswith("written"):
                save(path, body)
            raise OSError("PRIVATE_CANARY")
        return save(path, body)

    monkeypatch.setattr(p.base, "write_private", failed_write)
    assert not execute(workflow)
    result = report(capsys)
    assert result["result"] == "stopped" and result["outcome_uncertain"] is True
    assert result["diagnostic_record"] == "saved"
    private = json.loads((root / "failure-diagnostic.json").read_text())
    assert private["failure_code"] == expected
    assert "PRIVATE_CANARY" not in json.dumps(private)
    if fault in {"cleanup", "clear_once", "clear_twice"}:
        assert result["cleanup"] == "uncertain"
    if fault in {"interrupt", "cancel", "escaping"}:
        assert result["process_release"] == "may_have_released" and result["cleanup"] == "unknown"
    assert len(workflow["calls"]) == (0 if fault == "setup" else 1)
    assert not (root / "result.json").exists() or fault in {"result_partial", "result_written"}
    assert not caplog.text
    assert_blocked_reuse(workflow, capsys)


@pytest.mark.parametrize("fault", ["error", "interrupt", "cancel", "partial", "written", "report"])
def test_failure_reporting_double_fault_never_enables_execution(
    p, workflow, monkeypatch, capsys, fault
):
    def capture(*args, **kwargs):
        workflow["calls"].append(args)
        raise KeyboardInterrupt("PRIVATE_CANARY")

    monkeypatch.setattr(p.local.runner, "capture_owned", capture)
    save = workflow["write"]

    def failed_write(path, body):
        if path.name == "failure-diagnostic.json":
            if fault in {"partial", "written"}:
                save(path, body[:9] if fault == "partial" else body)
            raise {"interrupt": KeyboardInterrupt, "cancel": asyncio.CancelledError}.get(
                fault, OSError
            )("PRIVATE_CANARY")
        return save(path, body)

    monkeypatch.setattr(p.base, "write_private", failed_write)
    if fault == "report":
        monkeypatch.setattr(
            p.diagnostic.FailureDiagnostics,
            "failure_report",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("PRIVATE_CANARY")),
        )
    assert not execute(workflow)
    result = report(capsys)
    assert result["result"] == "stopped" and result["diagnostic_record"] == "not_saved"
    assert (workflow["root"] / "attempt.claim").exists()
    assert not (workflow["root"] / "result.json").exists()
    assert_blocked_reuse(
        workflow, capsys, diagnostic_record="not_saved" if fault == "report" else "not_attempted"
    )


def test_existing_private_diagnostic_is_never_overwritten(p, workflow, monkeypatch, capsys):
    path = workflow["root"] / "failure-diagnostic.json"
    path.write_bytes(b"SYNTHETIC retained diagnostic")

    def capture(*args, **kwargs):
        workflow["calls"].append(args)
        raise RuntimeError("PRIVATE_CANARY")

    monkeypatch.setattr(p.local.runner, "capture_owned", capture)
    assert not execute(workflow)
    result = report(capsys)
    assert result["diagnostic_record"] == "not_saved"
    assert path.read_bytes() == b"SYNTHETIC retained diagnostic"
    assert_blocked_reuse(workflow, capsys)


def test_concurrent_documented_calls_have_one_capture_and_no_loser_diagnostic(
    p, workflow, monkeypatch, capsys
):
    entered, release = Event(), Event()

    def capture(*args, **kwargs):
        c = workflow["fake"](*args, **kwargs)
        entered.set()
        assert release.wait(10), "synthetic barrier was not released"
        return c

    monkeypatch.setattr(p.local.runner, "capture_owned", capture)
    with ThreadPoolExecutor(max_workers=1) as pool:
        winner = pool.submit(execute, workflow)
        try:
            assert entered.wait(10)
            assert not execute(workflow)
            result = report(capsys)
            assert result["diagnostic_record"] == "not_attempted"
            assert not (workflow["root"] / "failure-diagnostic.json").exists()
        finally:
            release.set()
        assert winner.result(timeout=10)
    assert report(capsys)["result"] == "metadata_page_verified"
    assert len(workflow["calls"]) == 1


def test_cleanup_uncertainty_is_latched_across_later_metadata(p, workflow):
    trace = p.diagnostic.FailureDiagnostics("F4-A2-group-managed-01")
    trace.cleanup_failed()
    c = p.local.runner.Capture(
        0, "completed", bytearray(), bytearray(), "may_have_released", "completed"
    )
    trace.observe_capture(c)
    assert trace.records(ValueError())[1]["cleanup"] == "uncertain"
