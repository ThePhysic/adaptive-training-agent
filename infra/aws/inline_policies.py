"""A2-state-02 offline-only ListUserPolicies preparation. No process launcher."""

import hashlib
import json
import os
import re
from pathlib import Path

try:
    from . import attached_policies as base
except ImportError:
    import attached_policies as base

local = base.local
LIMIT = base.LIMIT
NAME_LIMIT = 40  # Existing per-response inventory bound; not a service quota.
SOURCES = (
    "infra/aws/inline_policies.py",
    "docs/implementation/f4-a2-state-02-supervised-procedure.md",
    *base.SOURCES,
)


def command(executable):
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        raise ValueError("a202_pinned_executable_required")
    return (
        executable,
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


def policy_names(value):
    if not isinstance(value, list) or len(value) > NAME_LIMIT:
        raise ValueError("a202_name_count_or_shape")
    if any(
        not isinstance(n, str) or not re.fullmatch(r"[A-Za-z0-9+=,.@_-]{1,128}", n) for n in value
    ):
        raise ValueError("a202_policy_name_invalid")
    if len(set(value)) != len(value):
        raise ValueError("a202_duplicate_policy_name")
    return set(value)


def sources():
    return {n: hashlib.sha256((local.ROOT / n).read_bytes()).hexdigest() for n in SOURCES}


def validate(spec, *, now):
    if not isinstance(spec, dict) or set(spec) != {
        "caller",
        "target",
        "caller_provenance",
        "target_provenance",
        "approved_policy_names",
        "cli_path",
        "cli_sha256",
        "login_cache_directory",
        "window_start",
        "window_end",
        "source_sha256",
    }:
        raise ValueError("a202_spec_shape_invalid")
    if spec["source_sha256"] != sources():
        raise ValueError("a202_reviewed_source_mismatch")
    policy_names(spec["approved_policy_names"])
    # Reuse only reviewed metadata checks; never reuse state-01 records/commands.
    context = {k: v for k, v in spec.items() if k != "approved_policy_names"}
    context["approved_policies"] = []
    context["source_sha256"] = {n: spec["source_sha256"][n] for n in base.SOURCES}
    base.validate(context, now=now)


def prepare(spec, output, *, now):
    validate(spec, now=now)
    local.private(output)
    record = {"kind": "offline-a2-state-02-v1", "live_execution": False, "spec": spec}
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


def review(output, *, now):
    record = local.runner.strict_json(base.read_private(output / "preparation.json"))
    if (
        not isinstance(record, dict)
        or set(record) != {"kind", "live_execution", "spec"}
        or record["kind"] != "offline-a2-state-02-v1"
        or record["live_execution"] is not False
    ):
        raise ValueError("a202_offline_record_invalid")
    spec = record["spec"]
    validate(spec, now=now)
    config = base.read_private(output / "human-config").decode("utf-8")
    if local.selected_configuration(config, spec["caller"]) != config:
        raise ValueError("a202_selected_configuration_changed")
    if base.read_private(output / "empty-credentials"):
        raise ValueError("a202_empty_credentials_required")
    for name in ("home", "tmp"):
        if any(local.private(output / name).iterdir()):
            raise ValueError("a202_preparation_directory_changed")
    return spec


def claim(output, *, now, reviewed_sha256):
    if (
        not isinstance(reviewed_sha256, str)
        or not re.fullmatch(r"[a-f0-9]{64}", reviewed_sha256)
        or hashlib.sha256(base.read_private(output / "preparation.json")).hexdigest()
        != reviewed_sha256
    ):
        raise ValueError("a202_reviewed_preparation_mismatch")
    spec = review(output, now=now)
    base.write_private(output / "attempt.claim", b"possibly_started\n")
    if os.name != "nt":
        fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return spec


def environment(output, spec, inherited):
    return base.environment(output, spec, inherited)


def verify_capture(capture, spec, *, output):
    try:
        local.identity(spec["caller"])
        base.state.identity(spec["target"])
        if spec["caller"]["Account"] != spec["target"]["Account"]:
            raise ValueError("a202_private_identity_binding_invalid")
        allowed = policy_names(spec["approved_policy_names"])
        if (
            capture.status != "completed"
            or capture.native_exit != 0
            or capture.stderr
            or len(capture.stdout) > LIMIT
        ):
            raise ValueError("a202_command_not_clean")
        page = local.runner.strict_json(capture.stdout)
        if not isinstance(page, dict) or set(page) != {"PolicyNames", "IsTruncated"}:
            raise ValueError("a202_response_shape_invalid")
        if page["IsTruncated"] is not False:
            raise ValueError("a202_page_incomplete")
        observed = policy_names(page["PolicyNames"])
        base.write_private(
            output / "observed-policy-names.json", (json.dumps(page) + "\n").encode()
        )
        if not observed <= allowed:
            raise ValueError("a202_unexpected_policy_name_private_review")
        return {
            "checkpoint": "F4-A2-state-02",
            "result": "metadata_page_verified",
            "policy_count": len(observed),
            "mfa_verified": False,
            "http_request_count_verified": False,
        }
    finally:
        capture.clear()
