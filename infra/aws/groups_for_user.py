"""State-03 offline-only preparation/validation. No launcher or live access switch."""

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

try:
    from . import attached_policies as base
except ImportError:
    import attached_policies as base

local = base.local
LIMIT = base.LIMIT
GROUP_LIMIT = 4
SOURCES = (
    "infra/aws/groups_for_user.py",
    "docs/implementation/f4-a2-state-03-supervised-procedure.md",
    *base.SOURCES,
)


def command(executable):
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        raise ValueError("a203_pinned_executable_required")
    return (
        executable,
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


def group_identities(value, account, *, observed=False):
    """Conservative supported paths; creation metadata is not an identity expectation."""
    if not isinstance(account, str) or not re.fullmatch(r"[0-9]{12}", account):
        raise ValueError("a203_group_account_invalid")
    if not isinstance(value, list) or len(value) > GROUP_LIMIT:
        raise ValueError("a203_group_count_or_shape")
    required = {"GroupName", "GroupId", "Arn", "Path"} | ({"CreateDate"} if observed else set())
    names, arns, ids, identities = set(), set(), set(), set()
    for group in value:
        if not isinstance(group, dict) or set(group) != required:
            raise ValueError("a203_group_shape_invalid")
        if (
            not isinstance(group["GroupName"], str)
            or not re.fullmatch(r"[A-Za-z0-9+=,.@_-]{1,128}", group["GroupName"])
            or not isinstance(group["GroupId"], str)
            or not re.fullmatch(r"[A-Za-z0-9_]{16,128}", group["GroupId"])
            or not isinstance(group["Path"], str)
            or not 1 <= len(group["Path"]) <= 512
            or not re.fullmatch(r"/(?:[A-Za-z0-9+=,.@_-]+/)*", group["Path"])
            or any(p in {".", ".."} for p in group["Path"].split("/"))
            or not isinstance(group["Arn"], str)
            or not 20 <= len(group["Arn"]) <= 2048
            or group["Arn"] != f"arn:aws:iam::{account}:group{group['Path']}{group['GroupName']}"
        ):
            raise ValueError("a203_group_identity_invalid")
        if observed:
            date = group["CreateDate"]
            if not isinstance(date, str) or not re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])",
                date,
            ):
                raise ValueError("a203_group_createdate_invalid")
            try:
                datetime.fromisoformat(date)
            except ValueError:
                raise ValueError("a203_group_createdate_invalid") from None
        if (
            group["GroupName"].casefold() in names
            or group["Arn"] in arns
            or group["GroupId"] in ids
        ):
            raise ValueError("a203_duplicate_group_identity")
        names.add(group["GroupName"].casefold())
        arns.add(group["Arn"])
        ids.add(group["GroupId"])
        identities.add((group["GroupName"], group["Path"], group["Arn"], group["GroupId"]))
    return identities


def sources():
    return {n: hashlib.sha256((local.ROOT / n).read_bytes()).hexdigest() for n in SOURCES}


def validate(spec, *, now):
    if not isinstance(spec, dict) or set(spec) != {
        "caller",
        "target",
        "caller_provenance",
        "target_provenance",
        "approved_groups",
        "cli_path",
        "cli_sha256",
        "login_cache_directory",
        "window_start",
        "window_end",
        "source_sha256",
    }:
        raise ValueError("a203_spec_shape_invalid")
    if spec["source_sha256"] != sources():
        raise ValueError("a203_reviewed_source_mismatch")
    context = {k: v for k, v in spec.items() if k != "approved_groups"}
    context["approved_policies"] = []
    context["source_sha256"] = {n: spec["source_sha256"][n] for n in base.SOURCES}
    base.validate(context, now=now)  # Existing private identity/binary/time checks only.
    group_identities(spec["approved_groups"], spec["target"]["Account"])


def prepare(spec, output, *, now):
    validate(spec, now=now)
    local.private(output)
    record = {"kind": "offline-a2-state-03-v1", "live_execution": False, "spec": spec}
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
        or record["kind"] != "offline-a2-state-03-v1"
        or record["live_execution"] is not False
    ):
        raise ValueError("a203_offline_record_invalid")
    spec = record["spec"]
    validate(spec, now=now)
    config = base.read_private(output / "human-config").decode("utf-8")
    if local.selected_configuration(config, spec["caller"]) != config:
        raise ValueError("a203_selected_configuration_changed")
    if base.read_private(output / "empty-credentials"):
        raise ValueError("a203_empty_credentials_required")
    for name in ("home", "tmp"):
        if any(local.private(output / name).iterdir()):
            raise ValueError("a203_preparation_directory_changed")
    return spec


def claim(output, *, now, reviewed_sha256):
    if (
        not isinstance(reviewed_sha256, str)
        or not re.fullmatch(r"[a-f0-9]{64}", reviewed_sha256)
        or hashlib.sha256(base.read_private(output / "preparation.json")).hexdigest()
        != reviewed_sha256
    ):
        raise ValueError("a203_reviewed_preparation_mismatch")
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
            raise ValueError("a203_private_identity_binding_invalid")
        allowed = group_identities(spec["approved_groups"], spec["target"]["Account"])
        if (
            capture.status != "completed"
            or capture.native_exit != 0
            or capture.stderr
            or len(capture.stdout) > LIMIT
        ):
            raise ValueError("a203_command_not_clean")
        page = local.runner.strict_json(capture.stdout)
        if not isinstance(page, dict) or set(page) != {"Groups", "IsTruncated"}:
            raise ValueError("a203_response_shape_invalid")
        if page["IsTruncated"] is not False:
            raise ValueError("a203_page_incomplete")
        observed = group_identities(page["Groups"], spec["target"]["Account"], observed=True)
        base.write_private(output / "observed-groups.json", (json.dumps(page) + "\n").encode())
        if not observed <= allowed:
            raise ValueError("a203_unexpected_group_private_review")
        return {
            "checkpoint": "F4-A2-state-03",
            "result": "metadata_page_verified",
            "group_count": len(observed),
            "mfa_verified": False,
            "http_request_count_verified": False,
        }
    finally:
        capture.clear()
