"""A2-state-01 offline preparation/validation only: no process launcher or live flag."""

import hashlib
import json
import os
import re
from pathlib import Path

try:
    from . import state_sts as state
except ImportError:
    import state_sts as state

local = state.local
PROFILE = "future-f4-human-admin"
TARGET = "future-f4-state-operator"
ENDPOINT = "https://iam.amazonaws.com"
LIMIT = 65536
POLICY_LIMIT = 12
SOURCES = (
    "infra/aws/attached_policies.py",
    "infra/aws/state_sts.py",
    *local.SOURCES,
    "docs/implementation/f4-a2-state-01-supervised-procedure.md",
)


def command(executable):
    if not isinstance(executable, str) or not Path(executable).is_absolute():
        raise ValueError("a2_pinned_executable_required")
    return (
        executable,
        "iam",
        "list-attached-user-policies",
        "--user-name",
        TARGET,
        "--profile",
        PROFILE,
        "--region",
        "us-east-1",
        "--endpoint-url",
        ENDPOINT,
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


def policy_entries(value, account):
    """Conservative supported IAM policy paths; identifiers never returned publicly."""
    if not isinstance(value, list) or len(value) > POLICY_LIMIT:
        raise ValueError("a2_policy_count_or_shape")
    names, arns = set(), set()
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {"PolicyName", "PolicyArn"}
            or not isinstance(item["PolicyName"], str)
            or not re.fullmatch(r"[A-Za-z0-9+=,.@_-]{1,128}", item["PolicyName"])
            or not isinstance(item["PolicyArn"], str)
            or not 20 <= len(item["PolicyArn"]) <= 2048
        ):
            raise ValueError("a2_policy_entry_invalid")
        match = re.fullmatch(
            r"arn:aws:iam::(aws|[0-9]{12}):policy/((?:[A-Za-z0-9+=,.@_-]+/)*[A-Za-z0-9+=,.@_-]+)",
            item["PolicyArn"],
        )
        if (
            not match
            or match[1] not in {"aws", account}
            or match[2].split("/")[-1] != item["PolicyName"]
            or any(part in {".", ".."} for part in match[2].split("/"))
            or len("/" + match[2].rsplit("/", 1)[0] + "/") > 512
            and "/" in match[2]
        ):
            raise ValueError("a2_policy_arn_invalid")
        if item["PolicyName"] in names or item["PolicyArn"] in arns:
            raise ValueError("a2_duplicate_policy")
        names.add(item["PolicyName"])
        arns.add(item["PolicyArn"])
    return {(item["PolicyName"], item["PolicyArn"]) for item in value}


def sources():
    return {name: hashlib.sha256((local.ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def validate(spec, *, now):
    if not isinstance(spec, dict) or set(spec) != {
        "caller",
        "target",
        "caller_provenance",
        "target_provenance",
        "approved_policies",
        "cli_path",
        "cli_sha256",
        "login_cache_directory",
        "window_start",
        "window_end",
        "source_sha256",
    }:
        raise ValueError("a2_spec_shape_invalid")
    local.identity(spec["caller"])
    state.identity(spec["target"])
    if (
        spec["caller"]["Account"] != spec["target"]["Account"]
        or spec["caller"]["UserId"] == spec["target"]["UserId"]
        or spec["caller_provenance"] != "owner_attested_A1a"
        or spec["target_provenance"] != "owner_attested_A1b"
    ):
        raise ValueError("a2_private_identity_binding_invalid")
    # Reuse metadata/binary/window checks only, never STS commands/records/claims.
    state.validate(
        {
            **{
                key: spec[key]
                for key in (
                    "cli_path",
                    "cli_sha256",
                    "login_cache_directory",
                    "window_start",
                    "window_end",
                )
            },
            "expected": spec["target"],
            "provenance": "owner_confirmed_existing",
        },
        now=now,
    )
    if spec["source_sha256"] != sources():
        raise ValueError("a2_reviewed_source_mismatch")
    policy_entries(spec["approved_policies"], spec["target"]["Account"])


def read_private(path):
    with local.private(path).open("rb") as stream:
        body = stream.read(LIMIT + 1)
    if len(body) > LIMIT:
        raise ValueError("a2_private_input_limit")
    return body


def write_private(path, body):
    if len(body) > LIMIT:
        raise ValueError("a2_private_output_limit")
    local.private(path.parent)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    local.private(path)


def prepare(spec, output, *, now):
    validate(spec, now=now)
    local.private(output)
    record = {"kind": "offline-a2-state-01-v1", "live_execution": False, "spec": spec}
    write_private(output / "preparation.json", (json.dumps(record) + "\n").encode())
    config = f"[profile {PROFILE}]\nregion = us-east-1\nlogin_session = {spec['caller']['Arn']}\n"
    local.selected_configuration(config, spec["caller"])
    write_private(output / "human-config", config.encode())
    write_private(output / "empty-credentials", b"")
    for name in ("home", "tmp"):
        (output / name).mkdir(mode=0o700)
        local.private(output / name)
    write_private(
        output / "preparation.sha256",
        (hashlib.sha256(read_private(output / "preparation.json")).hexdigest() + "\n").encode(),
    )


def review(output, *, now):
    record = local.runner.strict_json(read_private(output / "preparation.json"))
    if (
        not isinstance(record, dict)
        or set(record) != {"kind", "live_execution", "spec"}
        or record["kind"] != "offline-a2-state-01-v1"
        or record["live_execution"] is not False
    ):
        raise ValueError("a2_offline_record_invalid")
    spec = record["spec"]
    validate(spec, now=now)
    config = read_private(output / "human-config").decode("utf-8")
    if local.selected_configuration(config, spec["caller"]) != config:
        raise ValueError("a2_selected_configuration_changed")
    if read_private(output / "empty-credentials"):
        raise ValueError("a2_empty_credentials_required")
    for name in ("home", "tmp"):
        if any(local.private(output / name).iterdir()):
            raise ValueError("a2_preparation_directory_changed")
    return spec


def environment(output, spec, inherited):
    # Fresh reviewed human environment, not state or preflight credentials.
    return state.reference_environment(
        output, spec["caller"], spec["login_cache_directory"], spec["target"]["Account"], inherited
    )


def claim(output, *, now, reviewed_sha256):
    # The operator supplies this from separate private review, never recompute it
    # as the expectation at release. It binds identities, allowlist, window/sources.
    if (
        not isinstance(reviewed_sha256, str)
        or not re.fullmatch(r"[a-f0-9]{64}", reviewed_sha256)
        or hashlib.sha256(read_private(output / "preparation.json")).hexdigest() != reviewed_sha256
    ):
        raise ValueError("a2_reviewed_preparation_mismatch")
    spec = review(output, now=now)
    write_private(output / "attempt.claim", b"possibly_started\n")
    if os.name != "nt":
        descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return spec


def verify_capture(capture, spec, *, output):
    """Only finite summary escapes. Supported observations remain owner-private.

    Unexpected well-formed entries are retained privately before rejection so the
    owner can investigate without replay. Malformed/truncated data is never promoted
    to verified evidence. A successful list does not prove caller or target identity.
    """
    try:
        local.identity(spec["caller"])
        state.identity(spec["target"])
        if spec["caller"]["Account"] != spec["target"]["Account"]:
            raise ValueError("a2_private_identity_binding_invalid")
        allowed = policy_entries(spec["approved_policies"], spec["target"]["Account"])
        if (
            capture.status != "completed"
            or capture.native_exit != 0
            or capture.stderr
            or len(capture.stdout) > LIMIT
        ):
            raise ValueError("a2_command_not_clean")
        page = local.runner.strict_json(capture.stdout)
        if not isinstance(page, dict) or set(page) != {"AttachedPolicies", "IsTruncated"}:
            raise ValueError("a2_response_shape_invalid")
        if page["IsTruncated"] is not False:
            raise ValueError("a2_page_incomplete")
        observed = policy_entries(page["AttachedPolicies"], spec["target"]["Account"])
        write_private(output / "observed-policies.json", (json.dumps(page) + "\n").encode())
        if not observed <= allowed:
            raise ValueError("a2_unexpected_policy_private_review")
        return {
            "checkpoint": "F4-A2-state-01",
            "result": "metadata_page_verified",
            "policy_count": len(observed),
            "mfa_verified": False,
            "http_request_count_verified": False,
        }
    finally:
        capture.clear()
