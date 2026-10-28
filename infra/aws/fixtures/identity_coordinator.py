"""Offline-tested result collection for the fixed identity-only contract.

No launcher, credentials, networking or retry. The caller owns an already started
process and its process-tree stop callback. Never use this as an infrastructure
plan collector: identity evidence assumes the unchanged identity_contract HCL.
"""

import re
import subprocess
import time
from typing import NamedTuple


class IdentityResult(NamedTuple):
    native_exit_code: int | None
    completed_before_stop: bool
    identity_output_matches: bool | None
    coordinator_status: str
    stop_requested: bool

    @property
    def private_postconditions_passed(self):
        # Only for the fixed HCL: do not infer identity from arbitrary processes.
        return self.completed_before_stop and self.native_exit_code == 0

    @property
    def private_identity_verified(self):
        # Output is extra corroboration, independent of the hard postconditions.
        return self.private_postconditions_passed and self.identity_output_matches is True


def collect_identity(child, *, abort, stop_owned, deadline, clock=time.monotonic):
    """Retain native evidence separately from guard/deadline/cleanup outcomes.

    Raw output remains private in memory and is discarded, never returned/logged.
    The supplied stop callback must target only this child's owned process tree.
    It must not return until a stop has been requested. No process is restarted.
    """

    def status():
        if abort.is_set():
            return "transport_guard"
        if clock() >= deadline:
            return "deadline"
        return "completed"

    def result(out, stopped, outcome):
        markers = re.findall(rb"(?m)^\s*identity_matches\s*=\s*(true|false)\s*$", out)
        marker = markers == [b"true"]
        return IdentityResult(child.returncode, not stopped, marker, outcome, stopped)

    def finished(outcome):
        try:
            out, _ = child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # A completed parent can still have inherited pipes held open. Keep
            # its native evidence while reporting that output collection failed.
            return IdentityResult(child.returncode, True, None, "cleanup_incomplete", False)
        return result(out, False, outcome)

    while True:
        # Collect a finished child's exit/postcondition evidence before reacting
        # to a simultaneously signalled guard. Keep the guard outcome as well.
        outcome = status()
        if child.poll() is not None:
            return finished(outcome)
        if outcome != "completed":
            # Recheck immediately before stopping; do not label completed work
            # as killed. A completion racing the actual stop is conservative.
            if child.poll() is not None:
                return finished(outcome)
            cleanup_incomplete = False
            try:
                stop_owned(child)
            finally:
                try:
                    out, _ = child.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    cleanup_incomplete = True
            if cleanup_incomplete:
                return IdentityResult(child.poll(), False, None, "cleanup_incomplete", True)
            return result(out, True, outcome)
        try:
            out, _ = child.communicate(timeout=min(0.25, max(0.001, deadline - clock())))
        except subprocess.TimeoutExpired:
            continue
        return result(out, False, status())
