"""Bounded failure evidence only. No launcher, AWS parser, authority or retry API."""

import asyncio
import json

try:
    from . import attached_policies as base
except ImportError:
    import attached_policies as base

STAGES = (
    "not_started",
    "pre_release_review",
    "claim_write",
    "claim_created",
    "capture_preparation",
    "capture",
    "response_context",
    "response_parse",
    "response_schema",
    "policy_validation",
    "observation_persistence",
    "allowlist_comparison",
    "result_persistence",
    "finished",
)
CAPTURE_CODES = {
    "cancelled_before_start": "cancelled",
    "cancelled_before_release": "cancelled",
    "cancelled": "cancelled",
    "deadline": "timeout",
    "output_limit": "capture_overflow",
    "launch_or_ownership_failed": "wrapper_launch_or_ownership_failed",
    "cleanup_incomplete": "cleanup_uncertain",
    "capture_failed": "capture_failure",
    "interrupted": "cancelled",
}
MESSAGES = {
    "capture_failure": "group_inventory_command_not_clean",
    "cancelled": "group_inventory_command_not_clean",
    "timeout": "group_inventory_command_not_clean",
    "capture_overflow": "group_inventory_command_not_clean",
    "wrapper_launch_or_ownership_failed": "group_inventory_command_not_clean",
    "cleanup_uncertain": "group_inventory_command_not_clean",
    "native_exit_nonzero": "group_inventory_command_not_clean",
    "native_exit_unknown": "group_inventory_command_not_clean",
    "stderr_present": "group_inventory_command_not_clean",
    "invalid_json": "group_inventory_invalid_json",
    "response_schema": "group_inventory_response_shape_invalid",
    "incomplete_page": "group_inventory_incomplete_page",
    "invalid_policy_metadata": "group_inventory_policy_metadata_invalid",
    "unexpected_policy": "group_inventory_unexpected_policy_private_review",
    "observation_persistence_failed": "group_inventory_observation_persistence_failed",
}
FALLBACK = {
    "pre_release_review": "pre_release_validation_failed",
    "claim_write": "claim_failed",
    "claim_created": "pre_release_validation_failed",
    "capture_preparation": "pre_release_validation_failed",
    "capture": "capture_exception_unclassified",
    "observation_persistence": "observation_persistence_failed",
    "result_persistence": "result_persistence_failed",
}
PUBLIC_CODES = {
    "pre_release_validation_failed": "pre_release_failure",
    "claim_failed": "pre_release_failure",
    "wrapper_launch_or_ownership_failed": "process_failure",
    "native_exit_nonzero": "process_failure",
    "native_exit_unknown": "process_failure",
    "stderr_present": "process_failure",
    "cancelled": "timeout_or_cancellation",
    "timeout": "timeout_or_cancellation",
    "capture_overflow": "capture_failure",
    "capture_failure": "capture_failure",
    "capture_exception_unclassified": "capture_failure",
    "cleanup_uncertain": "cleanup_uncertain",
    "invalid_json": "response_validation_failed",
    "response_schema": "response_validation_failed",
    "incomplete_page": "response_validation_failed",
    "invalid_policy_metadata": "response_validation_failed",
    "unexpected_policy": "response_validation_failed",
    "validation_unclassified": "response_validation_failed",
    "observation_persistence_failed": "private_persistence_failed",
    "result_persistence_failed": "private_persistence_failed",
    "unknown": "unknown",
}


class InventoryFailure(ValueError):
    def __init__(self, code):
        if type(code) is not str or code not in MESSAGES:
            raise ValueError("inventory_diagnostic_code_rejected")
        self.code = code
        super().__init__(MESSAGES[code])  # Constant legacy-compatible text, never raw data.


def capture_failure(capture):
    if getattr(capture, "cleanup_state", "unknown") == "uncertain":
        return "cleanup_uncertain"
    if capture.status != "completed":
        return CAPTURE_CODES.get(capture.status, "capture_failure")
    if capture.native_exit is None:
        return "native_exit_unknown"
    if capture.native_exit != 0:
        return "native_exit_nonzero"
    if capture.stderr:
        return "stderr_present"
    return None


def clear_capture(capture, diagnostics=None):
    """Buffer cleanup only; never launch, retry or replace the execution claim."""
    try:
        capture.clear()
    except BaseException:
        if diagnostics is not None:
            diagnostics.cleanup_failed()
        raise


class FailureDiagnostics:
    """No raw exceptions, outputs, identifiers, counters or unbounded event history."""

    def __init__(self, checkpoint):
        if type(checkpoint) is not str or checkpoint not in {
            "F4-A2-group-managed-01",
            "F4-A2-group-inline-01",
        }:
            raise ValueError("inventory_diagnostic_checkpoint_rejected")
        self._checkpoint = checkpoint
        self._stage = "not_started"
        self._release = "unknown"
        self._cleanup = "unknown"
        self._capture_status = "unknown"
        self._capture_started = False
        self._cleanup_uncertain = False

    @property
    def checkpoint(self):
        return self._checkpoint

    def mark(self, stage):
        if type(stage) is not str or stage not in STAGES:
            raise ValueError("inventory_diagnostic_stage_rejected")
        if STAGES.index(stage) < STAGES.index(self._stage):
            raise ValueError("inventory_diagnostic_stage_reversal")
        self._stage = stage
        if stage == "pre_release_review" and not self._capture_started:
            self._release = "not_released"

    def begin_capture(self):
        self.mark("capture")
        self._capture_started = True
        # If capture raises before returning metadata, never assume no release.
        self._release = "may_have_released"

    def observe_capture(self, capture):
        release = getattr(capture, "process_release", "unknown")
        cleanup = getattr(capture, "cleanup_state", "unknown")
        self._release = (
            release
            if type(release) is str and release in {"not_released", "may_have_released"}
            else "unknown"
        )
        if cleanup == "uncertain" or capture.status == "cleanup_incomplete":
            self._cleanup_uncertain = True
        self._cleanup = (
            "uncertain"
            if self._cleanup_uncertain
            else (
                cleanup
                if type(cleanup) is str and cleanup in {"not_started", "completed", "uncertain"}
                else "unknown"
            )
        )
        self._capture_status = (
            capture.status
            if type(capture.status) is str and capture.status in {*CAPTURE_CODES, "completed"}
            else "unknown"
        )

    def cleanup_failed(self):
        # Latch: later metadata or a second successful clear cannot erase it.
        self._cleanup_uncertain = True
        self._cleanup = "uncertain"

    def records(self, error):
        code = "unknown"
        if (
            isinstance(error, InventoryFailure)
            and type(error.code) is str
            and error.code in MESSAGES
        ):
            code = error.code
        elif isinstance(error, (KeyboardInterrupt, asyncio.CancelledError)):
            code = "cancelled"
        elif isinstance(error, TimeoutError):
            code = "timeout"
        else:
            code = FALLBACK.get(
                self._stage,
                "validation_unclassified"
                if self._stage.startswith("response")
                or self._stage in {"policy_validation", "allowlist_comparison"}
                else "unknown",
            )
        private = {
            "version": "inventory-failure-v1",
            "checkpoint": self._checkpoint,
            "result": "stopped",
            "outcome_uncertain": True,
            "failure_code": code,
            "stage": self._stage,
            "process_release": self._release,
            "cleanup": self._cleanup,
            "capture_status": self._capture_status,
        }
        public = {
            k: private[k]
            for k in ("checkpoint", "result", "outcome_uncertain", "process_release", "cleanup")
        }
        public["failure_code"] = PUBLIC_CODES[code]
        return private, public

    def failure_report(self, error, *, output=None):
        private, public = self.records(error)
        public["diagnostic_record"] = "not_attempted"
        if output is not None:
            try:
                base.write_private(
                    output / "failure-diagnostic.json", (json.dumps(private) + "\n").encode()
                )
                public["diagnostic_record"] = "saved"
            except BaseException:
                # Diagnostic storage failure cannot change the original failure or
                # cause a replay. Never expose this exception or silently overwrite.
                public["diagnostic_record"] = "not_saved"
        return public
