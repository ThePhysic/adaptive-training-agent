"""Two closed offline group-policy contracts. No command launcher or live selector."""

import hashlib
import json
import os
import re
from pathlib import Path

try:
    from . import groups_for_user as groups
    from . import inline_policies as inline
    from . import inventory_diagnostics as diagnostic
except ImportError:
    import groups_for_user as groups
    import inline_policies as inline
    import inventory_diagnostics as diagnostic

base = groups.base
local = base.local
TARGET = "FutureStateOperators"
SOURCES = tuple(
    dict.fromkeys(
        (
            "infra/aws/group_policy_inventory.py",
            "infra/aws/inventory_diagnostics.py",
            "docs/implementation/f4-a2-group-managed-01-supervised-procedure.md",
            "docs/implementation/f4-a2-group-inline-01-supervised-procedure.md",
            *groups.SOURCES,
            *inline.SOURCES,
        )
    )
)


def sources():
    return {n: hashlib.sha256((local.ROOT / n).read_bytes()).hexdigest() for n in SOURCES}


def group_binding(caller, group):
    local.identity(caller)
    groups.group_identities([group], caller["Account"])
    if group["GroupName"] != TARGET:
        raise ValueError("group_inventory_fixed_target_mismatch")


class _Inventory:
    """Common local mechanics only; concrete classes have fixed reviewed contracts."""

    @classmethod
    def _check_contract(cls):
        expected = {
            Managed: (
                "F4-A2-group-managed-01",
                "list-attached-group-policies",
                "approved_managed_policies",
                "AttachedPolicies",
            ),
            Inline: (
                "F4-A2-group-inline-01",
                "list-group-policies",
                "approved_inline_names",
                "PolicyNames",
            ),
        }.get(cls)
        if (
            expected is None
            or (cls.UNIT, cls.ACTION, cls.ALLOW_FIELD, cls.RESPONSE_FIELD) != expected
        ):
            raise ValueError("group_inventory_closed_contract_required")

    @classmethod
    def command(cls, executable):
        cls._check_contract()
        if not isinstance(executable, str) or not Path(executable).is_absolute():
            raise ValueError("group_inventory_pinned_executable_required")
        return (
            executable,
            "iam",
            cls.ACTION,
            "--group-name",
            TARGET,
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

    @classmethod
    def validate(cls, spec, *, now):
        cls._check_contract()
        if not isinstance(spec, dict) or set(spec) != {
            "caller",
            "group",
            "caller_provenance",
            "group_provenance",
            cls.ALLOW_FIELD,
            "policy_expectations_provenance",
            "cli_path",
            "cli_sha256",
            "login_cache_directory",
            "window_start",
            "window_end",
            "source_sha256",
        }:
            raise ValueError("group_inventory_spec_shape_invalid")
        group_binding(spec["caller"], spec["group"])
        if (
            spec["caller_provenance"] != "owner_attested_A1a"
            or spec["group_provenance"] != "owner_prospectively_reviewed_group"
        ):
            raise ValueError("group_inventory_provenance_invalid")
        if spec["source_sha256"] != sources():
            raise ValueError("group_inventory_reviewed_source_mismatch")
        base.state._context(spec, now)  # Reviewed local binary/cache-location/window checks only.
        approved = cls.entries(spec[cls.ALLOW_FIELD], spec["caller"]["Account"])
        expected_provenance = (
            "owner_independently_reviewed" if approved else "owner_explicit_deny_all"
        )
        if spec["policy_expectations_provenance"] != expected_provenance:
            raise ValueError("group_inventory_independent_policy_expectations_required")

    @classmethod
    def prepare(cls, spec, output, *, now):
        cls.validate(spec, now=now)
        local.private(output)
        record = {"kind": "offline-" + cls.UNIT + "-v1", "live_execution": False, "spec": spec}
        base.write_private(output / "preparation.json", (json.dumps(record) + "\n").encode())
        config = (
            "[profile future-f4-human-admin]\nregion = us-east-1\nlogin_session = "
            + spec["caller"]["Arn"]
            + "\n"
        )
        local.selected_configuration(config, spec["caller"])
        base.write_private(output / "human-config", config.encode())
        base.write_private(output / "empty-credentials", b"")
        for name in ("home", "tmp"):
            (output / name).mkdir(mode=0o700)
            local.private(output / name)
        base.write_private(
            output / "preparation.sha256",
            (
                hashlib.sha256(base.read_private(output / "preparation.json")).hexdigest() + "\n"
            ).encode(),
        )

    @classmethod
    def review(cls, output, *, now):
        record = local.runner.strict_json(base.read_private(output / "preparation.json"))
        if (
            not isinstance(record, dict)
            or set(record) != {"kind", "live_execution", "spec"}
            or record["kind"] != "offline-" + cls.UNIT + "-v1"
            or record["live_execution"] is not False
        ):
            raise ValueError("group_inventory_wrong_or_active_record")
        spec = record["spec"]
        cls.validate(spec, now=now)
        config = base.read_private(output / "human-config").decode("utf-8")
        if local.selected_configuration(config, spec["caller"]) != config:
            raise ValueError("group_inventory_selected_config_changed")
        if base.read_private(output / "empty-credentials"):
            raise ValueError("group_inventory_empty_credentials_required")
        for name in ("home", "tmp"):
            if any(local.private(output / name).iterdir()):
                raise ValueError("group_inventory_directory_changed")
        return spec

    @classmethod
    def claim(cls, output, *, now, reviewed_sha256, diagnostics=None):
        if diagnostics is not None:
            if diagnostics.checkpoint != cls.UNIT:
                raise ValueError("group_inventory_diagnostic_unit_mismatch")
            diagnostics.mark("pre_release_review")
        if (
            not isinstance(reviewed_sha256, str)
            or not re.fullmatch(r"[a-f0-9]{64}", reviewed_sha256)
            or hashlib.sha256(base.read_private(output / "preparation.json")).hexdigest()
            != reviewed_sha256
        ):
            raise ValueError("group_inventory_reviewed_preparation_mismatch")
        spec = cls.review(output, now=now)
        if diagnostics is not None:
            diagnostics.mark("claim_write")
        base.write_private(output / "attempt.claim", b"possibly_started\n")
        if os.name != "nt":
            fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        if diagnostics is not None:
            diagnostics.mark("claim_created")
        return spec

    @classmethod
    def environment(cls, output, spec, inherited):
        cls._check_contract()
        group_binding(spec["caller"], spec["group"])
        return base.state.reference_environment(
            output,
            spec["caller"],
            spec["login_cache_directory"],
            spec["caller"]["Account"],
            inherited,
        )

    @classmethod
    def verify_capture(cls, capture, spec, *, output, diagnostics=None):
        try:
            if diagnostics is not None:
                if diagnostics.checkpoint != cls.UNIT:
                    raise ValueError("group_inventory_diagnostic_unit_mismatch")
                diagnostics.observe_capture(capture)
                diagnostics.mark("response_context")
            cls._check_contract()
            group_binding(spec["caller"], spec["group"])
            allowed = cls.entries(spec[cls.ALLOW_FIELD], spec["caller"]["Account"])
            code = diagnostic.capture_failure(capture)
            if code is not None:
                raise diagnostic.InventoryFailure(code)
            if len(capture.stdout) > base.LIMIT:
                raise diagnostic.InventoryFailure("capture_overflow")
            if diagnostics is not None:
                diagnostics.mark("response_parse")
            try:
                page = local.runner.strict_json(capture.stdout)
            except (
                ValueError,
                TypeError,
                RecursionError,
            ):
                raise diagnostic.InventoryFailure("invalid_json") from None
            if diagnostics is not None:
                diagnostics.mark("response_schema")
            if not isinstance(page, dict) or set(page) != {cls.RESPONSE_FIELD, "IsTruncated"}:
                raise diagnostic.InventoryFailure("response_schema")
            if page["IsTruncated"] is not False:
                raise diagnostic.InventoryFailure("incomplete_page")
            if diagnostics is not None:
                diagnostics.mark("policy_validation")
            try:
                observed = cls.entries(page[cls.RESPONSE_FIELD], spec["caller"]["Account"])
            except (
                ValueError,
                TypeError,
            ):
                raise diagnostic.InventoryFailure("invalid_policy_metadata") from None
            if diagnostics is not None:
                diagnostics.mark("observation_persistence")
            try:
                base.write_private(
                    output / "observed-policies.json", (json.dumps(page) + "\n").encode()
                )
            except (
                OSError,
                ValueError,
                local.runner.subprocess.SubprocessError,
            ):
                raise diagnostic.InventoryFailure("observation_persistence_failed") from None
            if diagnostics is not None:
                diagnostics.mark("allowlist_comparison")
            if not observed <= allowed:
                raise diagnostic.InventoryFailure("unexpected_policy")
            return {
                "checkpoint": cls.UNIT,
                "result": "metadata_page_verified",
                "policy_count": len(observed),
                "mfa_verified": False,
                "http_request_count_verified": False,
            }
        finally:
            diagnostic.clear_capture(capture, diagnostics)


class Managed(_Inventory):
    UNIT = "F4-A2-group-managed-01"
    ACTION = "list-attached-group-policies"
    ALLOW_FIELD = "approved_managed_policies"
    RESPONSE_FIELD = "AttachedPolicies"

    @staticmethod
    def entries(value, account):
        return base.policy_entries(value, account)


class Inline(_Inventory):
    UNIT = "F4-A2-group-inline-01"
    ACTION = "list-group-policies"
    ALLOW_FIELD = "approved_inline_names"
    RESPONSE_FIELD = "PolicyNames"

    @staticmethod
    def entries(value, account):
        return inline.policy_names(value)
