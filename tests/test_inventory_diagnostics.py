"""Synthetic-only failure evidence; never execute AWS CLI or read historical records."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from threading import Event, Thread

import pytest
import test_group_policy_inventory as fixtures

# Reuse only synthetic fixture contracts; do not copy a second identity generator.
a, p, spec, now, prepared = fixtures.a, fixtures.p, fixtures.spec, fixtures.now, fixtures.prepared
capture, digest, page = fixtures.capture, fixtures.digest, fixtures.page


@pytest.fixture
def d(p):
    return p.diagnostic


@pytest.mark.parametrize(
    "code",
    [
        "cancelled",
        "timeout",
        "capture_overflow",
        "wrapper_launch_or_ownership_failed",
        "cleanup_uncertain",
        "native_exit_nonzero",
        "native_exit_unknown",
        "stderr_present",
        "invalid_json",
        "response_schema",
        "incomplete_page",
        "invalid_policy_metadata",
        "unexpected_policy",
        "observation_persistence_failed",
        "capture_failure",
    ],
)
def test_finite_codes_never_echo_private_exception_or_output(d, code, capsys, caplog):
    trace = d.FailureDiagnostics("F4-A2-group-managed-01")
    trace.begin_capture()
    error = d.InventoryFailure(code)
    error.args = ("PRIVATE_CANARY_TOKEN_ACCOUNT_POLICY",)
    private, public = trace.records(error)
    assert private["failure_code"] == code
    assert public["outcome_uncertain"] is True
    assert "PRIVATE_CANARY" not in json.dumps([private, public])
    assert not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("PRIVATE_CANARY"),
        KeyboardInterrupt(),
        asyncio.CancelledError(),
        TimeoutError("PRIVATE_CANARY"),
    ],
)
def test_escaping_capture_exception_never_implies_not_released(d, error):
    trace = d.FailureDiagnostics("F4-A2-group-managed-01")
    trace.mark("pre_release_review")
    assert trace.records(ValueError())[0]["process_release"] == "not_released"
    trace.begin_capture()
    private, public = trace.records(error)
    assert private["process_release"] == "may_have_released"
    assert private["cleanup"] == "unknown"
    assert "PRIVATE_CANARY" not in json.dumps(public)
    with pytest.raises(ValueError, match="stage_reversal"):
        trace.mark("pre_release_review")


@pytest.mark.parametrize(
    "status,code",
    [
        ("deadline", "timeout"),
        ("cancelled", "cancelled"),
        ("output_limit", "capture_overflow"),
        ("launch_or_ownership_failed", "wrapper_launch_or_ownership_failed"),
        ("cleanup_incomplete", "cleanup_uncertain"),
        ("PRIVATE_CANARY", "capture_failure"),
    ],
)
def test_capture_classification_uses_only_finite_metadata(p, d, status, code):
    c = capture(p, b"PRIVATE_CANARY", status=status, stderr=b"AccessDenied PRIVATE_CANARY")
    assert d.capture_failure(c) == code
    trace = d.FailureDiagnostics("F4-A2-group-managed-01")
    trace.observe_capture(c)
    assert "PRIVATE_CANARY" not in json.dumps(trace.records(RuntimeError())[0])
    c.cleanup_state = "uncertain"
    assert d.capture_failure(c) == "cleanup_uncertain"


@pytest.mark.parametrize(
    "exit_code,stderr,expected",
    [
        (7, b"ExpiredToken PRIVATE_CANARY", "native_exit_nonzero"),
        (0, b"AccessDenied PRIVATE_CANARY", "stderr_present"),
        (None, b"", "native_exit_unknown"),
        (0, b"", None),
    ],
)
def test_native_exit_does_not_diagnose_authentication(p, d, exit_code, stderr, expected):
    assert d.capture_failure(capture(p, b"", code=exit_code, stderr=stderr)) == expected


@pytest.mark.parametrize(
    "fault,expected",
    [
        ("json", "invalid_json"),
        ("duplicate", "invalid_json"),
        ("schema", "response_schema"),
        ("page", "incomplete_page"),
        ("metadata", "invalid_policy_metadata"),
        ("unexpected", "unexpected_policy"),
        ("save", "observation_persistence_failed"),
    ],
)
def test_parser_and_persistence_failure_stages(p, d, a, spec, monkeypatch, fault, expected):
    value = page(a, spec)
    if fault == "json":
        value = b"{PRIVATE_CANARY"
    elif fault == "duplicate":
        value = b'{"IsTruncated":false,"IsTruncated":false}'
    elif fault == "schema":
        value["PRIVATE_CANARY"] = 1
    elif fault == "page":
        value["IsTruncated"] = True
    elif fault == "metadata":
        value[a.RESPONSE_FIELD] = [None]
    elif fault == "unexpected":
        spec[a.ALLOW_FIELD] = []
    writes = []

    def save(path, data):
        if fault == "save":
            raise OSError("PRIVATE_CANARY")
        writes.append(path.name)

    monkeypatch.setattr(p.base, "write_private", save)
    trace = d.FailureDiagnostics(a.UNIT)
    trace.begin_capture()
    c = capture(p, value)
    with pytest.raises(d.InventoryFailure) as error:
        a.verify_capture(c, spec, output=Path("SYNTHETIC"), diagnostics=trace)
    private, public = trace.records(error.value)
    assert private["failure_code"] == expected
    assert bool(writes) == (fault == "unexpected")
    assert not c.stdout and not c.stderr
    assert "PRIVATE_CANARY" not in json.dumps([private, public])
    if fault == "unexpected":
        assert public["failure_code"] == "response_validation_failed"
        assert private["stage"] == "allowlist_comparison"


def test_success_and_result_persistence_remain_separate(p, d, a, spec, monkeypatch):
    writes = []
    monkeypatch.setattr(p.base, "write_private", lambda path, data: writes.append(path.name))
    trace = d.FailureDiagnostics(a.UNIT)
    trace.begin_capture()
    result = a.verify_capture(
        capture(p, page(a, spec)), spec, output=Path("SYNTHETIC"), diagnostics=trace
    )
    assert result["result"] == "metadata_page_verified"
    assert writes == ["observed-policies.json"]
    trace.mark("result_persistence")
    assert (
        trace.records(OSError("PRIVATE_CANARY"))[0]["failure_code"] == "result_persistence_failed"
    )


def test_claim_partial_failure_is_retained_and_not_retryable(p, d, a, prepared, now, monkeypatch):
    original = p.base.write_private

    def partial(path, data):
        original(path, data)
        if path.name == "attempt.claim":
            raise OSError("SYNTHETIC failure after durable write")

    monkeypatch.setattr(p.base, "write_private", partial)
    trace = d.FailureDiagnostics(a.UNIT)
    with pytest.raises(OSError):
        a.claim(prepared, now=now, reviewed_sha256=digest(prepared), diagnostics=trace)
    assert (prepared / "attempt.claim").exists()
    record = trace.records(OSError())[0]
    assert record["failure_code"] == "claim_failed"
    assert record["process_release"] == "not_released"
    monkeypatch.setattr(p.base, "write_private", original)
    with pytest.raises((ValueError, OSError)):
        a.claim(prepared, now=now, reviewed_sha256=digest(prepared))


def test_diagnostic_write_is_exclusive_and_failure_never_replaces_original(
    p, d, tmp_path, monkeypatch
):
    tmp_path.chmod(0o700)
    trace = d.FailureDiagnostics("F4-A2-group-managed-01")
    trace.begin_capture()
    error = d.InventoryFailure("timeout")
    first = trace.failure_report(error, output=tmp_path)
    assert first["diagnostic_record"] == "saved"
    path = tmp_path / "failure-diagnostic.json"
    saved = path.read_bytes()
    second = trace.failure_report(ValueError("PRIVATE_CANARY"), output=tmp_path)
    assert second["diagnostic_record"] == "not_saved" and path.read_bytes() == saved
    monkeypatch.setattr(
        p.base, "write_private", lambda *_: (_ for _ in ()).throw(OSError("PRIVATE_CANARY"))
    )
    assert trace.failure_report(error, output=tmp_path)["failure_code"] == "timeout_or_cancellation"


def test_wrong_trace_cannot_instrument_other_unit(p, d, a, spec):
    other = "F4-A2-group-inline-01" if a is p.Managed else "F4-A2-group-managed-01"
    c = capture(p, page(a, spec))
    with pytest.raises(ValueError, match="unit_mismatch"):
        a.verify_capture(c, spec, output=Path("SYNTHETIC"), diagnostics=d.FailureDiagnostics(other))
    assert not c.stdout and not c.stderr


@pytest.mark.parametrize("value", ["PRIVATE_CANARY", None, []])
def test_rejected_diagnostic_fields_are_not_echoed(d, value):
    with pytest.raises(ValueError, match="code_rejected"):
        d.InventoryFailure(value)
    trace = d.FailureDiagnostics("F4-A2-group-managed-01")
    with pytest.raises(ValueError, match="stage_rejected"):
        trace.mark(value)


def test_actual_synthetic_child_release_and_cleanup(p, tmp_path):
    runner = p.local.runner
    env = {
        k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    result = runner.capture_owned(
        [sys.executable, "-I", "-S", "-c", "print('SYNTHETIC')"], cwd=tmp_path, env=env, timeout=10
    )
    assert result.status == "completed" and result.native_exit == 0
    assert result.process_release == "may_have_released"
    assert result.cleanup_state == "completed"
    assert b"SYNTHETIC" in result.stdout
    result.clear()
    abort = Event()
    abort.set()
    result = runner.capture_owned([], cwd=tmp_path, env=env, abort=abort)
    assert result.process_release == "not_released" and result.cleanup_state == "not_started"


def test_actual_wrapper_popen_failure_is_not_native_auth_failure(p, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(p.local.runner.subprocess, "Popen", fail)
    result = p.local.runner.capture_owned(["SYNTHETIC"], cwd=tmp_path, env={}, timeout=5)
    assert result.status == "launch_or_ownership_failed"
    assert result.process_release == "not_released"
    assert result.cleanup_state == "completed"
    assert not result.stdout and not result.stderr


@pytest.mark.parametrize("mode", ["deadline", "cancelled", "output_limit"])
def test_synthetic_released_process_faults_have_cleanup_evidence(p, tmp_path, mode):
    marker = tmp_path / "synthetic-started"
    code = (
        "import pathlib,time; pathlib.Path("
        + repr(str(marker))
        + ").touch(); "
        + ("print('x'*4096,flush=True); " if mode == "output_limit" else "")
        + "time.sleep(60)"
    )
    abort, done = Event(), Event()
    start = time.monotonic()

    def clock():
        return start + 11 if mode == "deadline" and marker.exists() else time.monotonic()

    def cancel():
        while not done.is_set() and time.monotonic() - start < 10:
            if marker.exists():
                if mode == "cancelled":
                    abort.set()
                return
            done.wait(0.01)

    watcher = Thread(target=cancel)
    watcher.start()
    env = {
        k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
    }
    try:
        c = p.local.runner.capture_owned(
            [sys.executable, "-I", "-S", "-c", code],
            cwd=tmp_path,
            env=env,
            timeout=10,
            abort=abort,
            clock=clock,
            stdout_limit=256,
        )
    finally:
        done.set()
        watcher.join(timeout=2)
    assert not watcher.is_alive() and marker.exists()
    assert c.status == mode
    assert c.process_release == "may_have_released" and c.cleanup_state == "completed"
    assert not c.stdout and not c.stderr
