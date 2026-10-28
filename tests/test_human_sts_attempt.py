"""One-shot local fence tests. No AWS CLI, account, credentials or external sockets."""

import hashlib
import importlib.util
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier, Event

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "infra/aws"))
    spec = importlib.util.spec_from_file_location(
        "human_sts_fence", ROOT / "infra/aws/human_sts.py"
    )
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture
def prepared(monkeypatch, tmp_path):
    sts = module(monkeypatch)
    now = datetime(2030, 1, 1, tzinfo=UTC)
    identity = {
        "Account": "000000000000",
        "Arn": "arn:aws:iam::000000000000:user/future-f4-human-admin",
        "UserId": "AIDASYNTHETIC000000001",
    }
    binary = tmp_path / "aws.exe"
    manifest, config, output = tmp_path / "manifest.json", tmp_path / "config", tmp_path / "out"
    binary.write_bytes(b"synthetic non-executable binary")
    value = {
        "expected": identity,
        "profile": sts.PROFILE,
        "region": sts.REGION,
        "endpoint": sts.ENDPOINT,
        "window_start": "2030-01-01T00:00:00Z",
        "window_end": "2030-01-01T00:30:00Z",
        "session_expires_at": "2030-01-01T00:15:00Z",
        "cli_path": str(binary),
        "cli_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
    }
    text = f"[profile {sts.PROFILE}]\nregion = us-east-1\nlogin_session = {identity['Arn']}\n"
    for path, body in ((manifest, json.dumps(value)), (config, text)):
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            stream.write(body)
    output.mkdir(mode=0o700)
    sts.prepare(manifest, config, output, now=now)
    return sts, now, output, identity


def test_claim_precedes_controlled_local_child_and_remains_after_success(prepared, capsys, caplog):
    sts, now, output, identity = prepared
    result = sts.claim_offline_attempt(output, now=now)
    assert result == {"result": "offline_attempt_claim_held", "live_execution": False}
    # Only a test-owned synthetic Python child reads the fence; no AWS process.
    code = (
        "import json; from pathlib import Path; "
        "r=json.loads(Path('attempt.claim.json').read_text()); "
        "assert r['state']=='possibly_started' and r['live_execution'] is False; "
        "print('synthetic_child_released_after_claim')"
    )
    capture = sts.runner.capture_owned(
        [sys.executable, "-I", "-S", "-c", code],
        cwd=output,
        env={k: v for k, v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR"}},
        timeout=5,
    )
    assert capture.status == "completed" and capture.native_exit == 0
    assert capture.stdout.strip() == b"synthetic_child_released_after_claim"
    capture.clear()
    record = json.loads((output / "attempt.claim.json").read_text())
    assert (
        record["preparation_sha256"]
        == hashlib.sha256((output / "preparation.json").read_bytes()).hexdigest()
    )
    assert all(value not in json.dumps(record) for value in identity.values())
    with pytest.raises(ValueError, match="already_claimed"):
        sts.claim_offline_attempt(output, now=now)
    assert not capsys.readouterr().out and not caplog.text


def test_restart_reloads_component_and_cannot_claim_again(prepared, monkeypatch):
    sts, now, output, _ = prepared
    sts.claim_offline_attempt(output, now=now)
    restarted = module(monkeypatch)
    with pytest.raises(ValueError, match="already_claimed"):
        restarted.claim_offline_attempt(output, now=now)


def test_abrupt_process_exit_then_fresh_process_cannot_reclaim(prepared):
    sts, _, output, _ = prepared
    common = (
        "import os,sys; from pathlib import Path; from datetime import UTC,datetime; "
        f"sys.path.insert(0,{str(ROOT / 'infra/aws')!r}); import human_sts; "
        f"directory=Path({str(output)!r}); now=datetime(2030,1,1,tzinfo=UTC);\n"
    )
    env = {k: v for k, v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR"}}
    first = sts.runner.capture_owned(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            common + "human_sts.claim_offline_attempt(directory,now=now); os._exit(23)",
        ],
        cwd=output,
        env=env,
        timeout=20,
    )
    assert first.status == "completed" and first.native_exit == 23
    first.clear()
    assert (output / "attempt.claim.json").exists()
    second = sts.runner.capture_owned(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            common + "try: human_sts.claim_offline_attempt(directory,now=now)\n"
            "except ValueError as e: assert str(e)=='attempt_already_claimed'\n"
            "else: raise SystemExit(1)\n",
        ],
        cwd=output,
        env=env,
        timeout=20,
    )
    assert second.status == "completed" and second.native_exit == 0
    assert not second.stdout and not second.stderr
    second.clear()


@pytest.mark.parametrize("partial", [b"", b'{"state":', b"corrupt", b'{"state":"completed"}'])
def test_ambiguous_or_partial_existing_record_never_releases(prepared, partial):
    sts, now, output, _ = prepared
    sts.write_private(output / "attempt.claim.json", partial)
    with pytest.raises(ValueError, match="already_claimed"):
        sts.claim_offline_attempt(output, now=now)
    assert (output / "attempt.claim.json").read_bytes() == partial


def test_fsync_failure_blocks_release_and_keeps_exclusive_fence(prepared, monkeypatch):
    sts, now, output, _ = prepared

    def fail(_):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(sts.os, "fsync", fail)
    with pytest.raises(ValueError, match="claim_failed_do_not_release") as error:
        sts.claim_offline_attempt(output, now=now)
    assert "CANARY" not in str(error.value) and (output / "attempt.claim.json").exists()
    with pytest.raises(ValueError, match="already_claimed"):
        sts.claim_offline_attempt(output, now=now)


def test_cancel_before_claim_creates_nothing(prepared):
    sts, now, output, _ = prepared
    abort = Event()
    abort.set()
    with pytest.raises(ValueError, match="cancelled_before_claim"):
        sts.claim_offline_attempt(output, now=now, abort=abort)
    assert not (output / "attempt.claim.json").exists()


def test_cancel_after_claim_retains_hold_and_launches_nothing(prepared, monkeypatch):
    sts, now, output, _ = prepared
    abort, write = Event(), sts.write_private

    def cancel(path, body):
        write(path, body)
        abort.set()

    monkeypatch.setattr(sts, "write_private", cancel)
    with pytest.raises(ValueError, match="cancelled_after_claim_hold_retained"):
        sts.claim_offline_attempt(output, now=now, abort=abort)
    assert (output / "attempt.claim.json").exists()
    with pytest.raises(ValueError, match="already_claimed"):
        sts.claim_offline_attempt(output, now=now)


def test_concurrent_attempts_have_one_exclusive_winner(prepared, monkeypatch):
    sts, now, output, _ = prepared
    # ACL/file checks were native in setup; place a deterministic barrier at write.
    original, barrier = sts.write_private, Barrier(2)

    def write(path, body):
        barrier.wait(timeout=10)
        original(path, body)

    monkeypatch.setattr(sts, "write_private", write)

    def attempt(_):
        try:
            return sts.claim_offline_attempt(output, now=now)["result"]
        except ValueError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["blocked", "offline_attempt_claim_held"]


@pytest.mark.parametrize("fault", ["expired", "command", "binary", "config", "live"])
def test_claim_re_attests_before_creating_record(prepared, fault):
    sts, now, output, _ = prepared
    value = json.loads((output / "preparation.json").read_text())
    if fault == "expired":
        now = now.replace(hour=1)
    elif fault == "command":
        value["argv"][1:3] = ["iam", "list-users"]
    elif fault == "binary":
        Path(value["manifest"]["cli_path"]).write_bytes(b"changed binary")
    elif fault == "config":
        (output / "selected-config").write_text("credential_process = PRIVATE_CANARY")
    else:
        value["live_execution"] = True
    (output / "preparation.json").write_text(json.dumps(value))
    with pytest.raises(ValueError):
        sts.claim_offline_attempt(output, now=now)
    assert not (output / "attempt.claim.json").exists()


def test_fence_never_enables_either_live_executor(prepared, monkeypatch):
    sts, now, output, _ = prepared
    sts.claim_offline_attempt(output, now=now)
    monkeypatch.setenv("AWS_PROFILE", sts.PROFILE)
    monkeypatch.setenv("FATA_ALLOW_AWS", "true")
    for executor in (sts.execute_live, sts.runner.execute_account):
        with pytest.raises(PermissionError):
            executor(output=output, claim=True, owner_approved=True)
