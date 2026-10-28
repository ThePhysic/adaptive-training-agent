"""Synthetic children only: never execute Terraform, read credentials or send AWS traffic."""

import importlib.util
import subprocess
import sys
import time
from pathlib import Path
from threading import Event

import pytest

ROOT = Path(__file__).resolve().parents[1]


def coordinator():
    path = ROOT / "infra/aws/fixtures/identity_coordinator.py"
    spec = importlib.util.spec_from_file_location("identity_coordinator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Child:
    def __init__(self, code=0, output=b"identity_matches = true\n", pending=False):
        self.returncode = None if pending else code
        self.code = code
        self.output = output
        self.awaited = 0

    def poll(self):
        return self.returncode

    def communicate(self, timeout):
        self.awaited += 1
        if self.returncode is None:
            raise subprocess.TimeoutExpired("synthetic", timeout)
        return self.output, b"synthetic-private-stderr-canary"


@pytest.mark.parametrize("code", [0, 1])
def test_completed_native_result_survives_simultaneous_guard(code, capsys, caplog):
    abort = Event()
    abort.set()
    child = Child(code, b"private-account-canary\nidentity_matches = true\n")
    result = coordinator().collect_identity(
        child,
        abort=abort,
        stop_owned=lambda _: pytest.fail("Already completed"),
        deadline=10,
        clock=lambda: 0,
    )
    assert result.native_exit_code == code and result.completed_before_stop
    assert result.private_postconditions_passed is (code == 0)
    assert result.private_identity_verified is (code == 0)
    assert result.coordinator_status == "transport_guard" and not result.stop_requested
    assert child.awaited == 1
    assert "canary" not in repr(result) and not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize(
    "output",
    [
        b"",
        b"identity_matches = false",
        b"xidentity_matches = true",
        b"identity_matches = true\nidentity_matches = false\n",
    ],
)
def test_exit_zero_without_exact_private_output_marker_is_not_verified(output):
    result = coordinator().collect_identity(
        Child(output=output),
        abort=Event(),
        stop_owned=lambda _: pytest.fail("No stop"),
        deadline=10,
        clock=lambda: 0,
    )
    assert result.native_exit_code == 0 and not result.private_identity_verified


@pytest.mark.parametrize("reason", ["transport_guard", "deadline"])
def test_running_child_is_stopped_awaited_and_cannot_supply_success(reason):
    child = Child(pending=True)
    abort = Event()
    if reason == "transport_guard":
        abort.set()
    stops = []

    def stop(owned):
        assert owned is child
        stops.append(owned)
        owned.returncode = 0  # Even a zero code after intervention is insufficient.

    result = coordinator().collect_identity(
        child,
        abort=abort,
        stop_owned=stop,
        deadline=10,
        clock=lambda: 10 if reason == "deadline" else 0,
    )
    assert len(stops) == child.awaited == 1
    assert result.native_exit_code == 0 and not result.private_identity_verified
    assert result.stop_requested and not result.completed_before_stop
    assert result.coordinator_status == reason


def test_completion_between_guard_and_stop_is_collected_without_kill():
    child = Child(pending=True)
    abort = Event()
    abort.set()
    polls = []

    def poll():
        polls.append(1)
        if len(polls) == 2:
            child.returncode = 0
        return child.returncode

    child.poll = poll
    result = coordinator().collect_identity(
        child,
        abort=abort,
        stop_owned=lambda _: pytest.fail("Finished before stop"),
        deadline=10,
        clock=lambda: 0,
    )
    assert result.private_identity_verified and result.coordinator_status == "transport_guard"
    assert not result.stop_requested


def test_unawaitable_child_retains_uncertainty():
    abort = Event()
    abort.set()
    result = coordinator().collect_identity(
        Child(pending=True),
        abort=abort,
        stop_owned=lambda _: None,
        deadline=10,
        clock=lambda: 0,
    )
    assert result.native_exit_code is None and not result.private_identity_verified
    assert result.coordinator_status == "cleanup_incomplete" and result.stop_requested


def test_stop_callback_failure_still_awaits_and_is_not_hidden():
    abort = Event()
    abort.set()
    child = Child(pending=True)

    def stop(_):
        raise RuntimeError("synthetic_stop_failure")

    with pytest.raises(RuntimeError, match="synthetic_stop_failure"):
        coordinator().collect_identity(
            child,
            abort=abort,
            stop_owned=stop,
            deadline=10,
            clock=lambda: 0,
        )
    assert child.awaited == 1


def test_completed_native_postconditions_survive_output_collection_timeout():
    child = Child()

    def communicate(timeout):
        assert timeout == 5
        raise subprocess.TimeoutExpired("synthetic", timeout)

    child.communicate = communicate
    result = coordinator().collect_identity(
        child,
        abort=Event(),
        stop_owned=lambda _: pytest.fail("Parent completed"),
        deadline=10,
        clock=lambda: 0,
    )
    assert result.native_exit_code == 0 and result.private_postconditions_passed
    assert result.identity_output_matches is None and not result.private_identity_verified
    assert result.coordinator_status == "cleanup_incomplete" and not result.stop_requested


def test_guard_arriving_during_communicate_cannot_erase_native_result():
    child = Child(pending=True)
    abort = Event()

    def communicate(timeout):
        abort.set()
        child.returncode = 0
        return b"identity_matches = true\n", b""

    child.communicate = communicate
    result = coordinator().collect_identity(
        child,
        abort=abort,
        stop_owned=lambda _: pytest.fail("Already finished"),
        deadline=10,
        clock=lambda: 0,
    )
    assert result.private_identity_verified and result.coordinator_status == "transport_guard"


def test_completed_native_evidence_does_not_silently_pass_expired_deadline():
    result = coordinator().collect_identity(
        Child(),
        abort=Event(),
        stop_owned=lambda _: pytest.fail("Already finished"),
        deadline=10,
        clock=lambda: 10,
    )
    assert result.private_identity_verified and result.coordinator_status == "deadline"


def test_poll_timeout_does_not_create_another_process_or_retry():
    child = Child(pending=True)
    original = child.communicate

    def communicate(timeout):
        if child.awaited:
            child.returncode = 0
        return original(timeout)

    child.communicate = communicate
    result = coordinator().collect_identity(
        child,
        abort=Event(),
        stop_owned=lambda _: pytest.fail("No stop"),
        deadline=10,
        clock=lambda: 0,
    )
    assert result.private_identity_verified and child.awaited == 2


def test_harmless_native_python_child_result_is_collected_without_network(capsys):
    # No executable/profile/config overrides; this only prints a synthetic marker.
    with subprocess.Popen(
        [sys.executable, "-I", "-c", "print('identity_matches = true')"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as child:
        result = coordinator().collect_identity(
            child,
            abort=Event(),
            stop_owned=lambda p: p.kill(),
            deadline=time.monotonic() + 5,
        )
    assert result.private_identity_verified and result.coordinator_status == "completed"
    assert not result.stop_requested and not capsys.readouterr().out
