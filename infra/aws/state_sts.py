"""A1b local preparation and synthetic verification; deliberately no process launcher.

The supervised capture assembly exists only as a future review block in the A1b
procedure. Neither preparation, a claim nor environment configuration grants access.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

try:
    from . import human_sts as local
except ImportError:
    import human_sts as local

PROFILE = "future-f4-state-operator"
REGION = "us-east-1"
ENDPOINT = "https://sts.us-east-1.amazonaws.com"
SOURCES = (
    "infra/aws/state_sts.py",
    *local.SOURCES,
    "docs/implementation/f4-a1b-supervised-sts-procedure.md",
)


def identity(expected):
    if (
        not isinstance(expected, dict)
        or set(expected) != {"Account", "Arn", "UserId"}
        or not all(isinstance(v, str) for v in expected.values())
        or not re.fullmatch(r"[0-9]{12}", expected["Account"])
        or len(expected["Arn"]) > 2048
        or not re.fullmatch(
            rf"arn:aws:iam::{expected['Account']}:user/(?:[A-Za-z0-9+=,.@_-]+/)*{PROFILE}",
            expected["Arn"],
        )
        or not re.fullmatch(r"[A-Za-z0-9]{16,128}", expected["UserId"])
    ):
        raise ValueError("state_identity_expectation_rejected")


def target(account, arn):
    if (
        not isinstance(account, str)
        or not re.fullmatch(r"[0-9]{12}", account)
        or not isinstance(arn, str)
        or len(arn) > 2048
        or not re.fullmatch(rf"arn:aws:iam::{account}:user/(?:[A-Za-z0-9+=,.@_-]+/)*{PROFILE}", arn)
    ):
        raise ValueError("state_reference_target_rejected")


def command(executable):
    return tuple(
        local.runner.command("identity", executable=executable, profile=PROFILE)
        + ["--no-cli-auto-prompt", "--no-paginate"]
    )


def reference_command(executable):
    # Separate vocabulary: no caller-supplied operation, profile or target.
    args = list(command(executable))
    args[1:3] = ["iam", "get-user", "--user-name", PROFILE]
    args[args.index("--profile") + 1] = local.PROFILE
    args[args.index("--endpoint-url") + 1] = "https://iam.amazonaws.com"
    return tuple(args)


def selected_configuration(text, expected):
    identity(expected)
    return local.runner.selected_configuration(text, PROFILE, expected)


def validate(spec, *, now):
    """Explicit private metadata only. Never read profiles, credentials or login cache."""
    if not isinstance(spec, dict) or set(spec) != {
        "expected",
        "provenance",
        "cli_path",
        "cli_sha256",
        "login_cache_directory",
        "window_start",
        "window_end",
    }:
        raise ValueError("state_preparation_shape_rejected")
    identity(spec["expected"])
    if spec["provenance"] not in {"owner_confirmed_existing", "separately_authorized_get_user"}:
        raise ValueError("authoritative_expectation_required")
    _context(spec, now)


def _context(spec, now):
    start, end = (local.instant(spec[k]) for k in ("window_start", "window_end"))
    if (
        not isinstance(now, datetime)
        or now.utcoffset() != timedelta(0)
        or not timedelta(0) < end - start <= timedelta(minutes=30)
        or not start <= now
        or now + timedelta(minutes=5) > end
    ):
        raise ValueError("state_window_rejected")
    cache = spec["login_cache_directory"]
    if (
        not isinstance(cache, str)
        or not Path(cache).is_absolute()
        or cache.startswith(("\\\\", "//"))
        or any(ord(c) < 32 for c in cache)
        or len(cache) > 4096
        or any(p.is_symlink() or p.is_junction() for p in (Path(cache), *Path(cache).parents))
    ):
        raise ValueError("explicit_local_cache_location_required")
    executable = spec["cli_path"]
    if (
        not isinstance(executable, str)
        or not Path(executable).is_absolute()
        or executable.startswith(("\\\\", "//"))
        or Path(executable).name.lower() not in {"aws", "aws.exe"}
        or len(executable) > 4096
        or any(ord(c) < 32 for c in executable)
        or not isinstance(spec["cli_sha256"], str)
        or not re.fullmatch(r"[a-f0-9]{64}", spec["cli_sha256"])
    ):
        raise ValueError("pinned_cli_required")
    local.verify_binary(spec)


def validate_reference(spec, *, now):
    if not isinstance(spec, dict) or set(spec) != {
        "human",
        "target_account",
        "target_arn",
        "cli_path",
        "cli_sha256",
        "login_cache_directory",
        "window_start",
        "window_end",
        "sources",
    }:
        raise ValueError("state_reference_preparation_rejected")
    local.identity(spec["human"])
    target(spec["target_account"], spec["target_arn"])
    if spec["human"]["Account"] != spec["target_account"] or spec["sources"] != {
        n: hashlib.sha256((local.ROOT / n).read_bytes()).hexdigest() for n in SOURCES
    }:
        raise ValueError("state_reference_binding_changed")
    _context(spec, now)


def prepare(spec, output, *, now):
    validate(spec, now=now)
    local.private(output)
    config = f"[profile {PROFILE}]\nregion = {REGION}\nlogin_session = {spec['expected']['Arn']}\n"
    selected_configuration(config, spec["expected"])
    record = {
        "kind": "offline-state-sts-preparation-v1",
        "live_execution": False,
        "spec": spec,
        "sources": {n: hashlib.sha256((local.ROOT / n).read_bytes()).hexdigest() for n in SOURCES},
    }
    local.write_private(output / "preparation.json", (json.dumps(record) + "\n").encode())
    local.write_private(output / "selected-config", config.encode())
    local.write_private(output / "empty-credentials", b"")
    for name in ("home", "tmp"):
        (output / name).mkdir(mode=0o700)
        local.private(output / name)


def review(output, *, now):
    """Re-attest without overwriting any file, authorizing execution or reading tokens."""
    record = local.runner.strict_json(local.read_private(output / "preparation.json"))
    if (
        not isinstance(record, dict)
        or set(record) != {"kind", "live_execution", "spec", "sources"}
        or record["kind"] != "offline-state-sts-preparation-v1"
        or record["live_execution"] is not False
        or record["sources"]
        != {n: hashlib.sha256((local.ROOT / n).read_bytes()).hexdigest() for n in SOURCES}
    ):
        raise ValueError("state_preparation_changed")
    spec = record["spec"]
    validate(spec, now=now)
    config = local.read_private(output / "selected-config").decode("utf-8")
    if selected_configuration(config, spec["expected"]) != config:
        raise ValueError("state_configuration_changed")
    if local.read_private(output / "empty-credentials"):
        raise ValueError("empty_credentials_required")
    for name in ("home", "tmp"):
        if any(local.private(output / name).iterdir()):
            raise ValueError("state_preparation_directory_changed")
    return spec


def environment(output, spec, inherited):
    """Fresh allowlisted child environment; explicit selected-only login profile.

    Native refresh can still use this login cache. No claim of network containment.
    """
    identity(spec["expected"])
    return _environment(output, spec["login_cache_directory"], inherited)


def _environment(output, cache, inherited):
    env = {k: v for k, v in inherited.items() if k in {"SYSTEMROOT", "WINDIR"}}
    env.update(
        HOME=str(output / "home"),
        USERPROFILE=str(output / "home"),
        TEMP=str(output / "tmp"),
        TMP=str(output / "tmp"),
        AWS_PROFILE=PROFILE,
        AWS_DEFAULT_PROFILE=PROFILE,
        AWS_REGION=REGION,
        AWS_DEFAULT_REGION=REGION,
        AWS_CONFIG_FILE=str(output / "selected-config"),
        AWS_SHARED_CREDENTIALS_FILE=str(output / "empty-credentials"),
        AWS_CREDENTIAL_FILE=str(output / "empty-credentials"),
        BOTO_CONFIG=str(output / "empty-credentials"),
        AWS_LOGIN_CACHE_DIRECTORY=cache,
        AWS_MAX_ATTEMPTS="1",
        AWS_RETRY_MODE="standard",
        AWS_EC2_METADATA_DISABLED="true",
        AWS_CSM_ENABLED="false",
        AWS_IGNORE_CONFIGURED_ENDPOINT_URLS="true",
        AWS_STS_REGIONAL_ENDPOINTS="regional",
        AWS_CLI_AUTO_PROMPT="off",
        AWS_PAGER="",
    )
    return env


def reference_environment(output, human, cache, target_account, inherited):
    # Only the separately approved human reference unit; no arbitrary profile API.
    local.identity(human)
    if human["Account"] != target_account:
        raise ValueError("reference_caller_account_mismatch")
    config = local.read_private(output / "human-config").decode("utf-8")
    if local.selected_configuration(config, human) != config:
        raise ValueError("reference_caller_configuration_changed")
    env = _environment(output, cache, inherited)
    env.update(
        AWS_PROFILE=local.PROFILE,
        AWS_DEFAULT_PROFILE=local.PROFILE,
        AWS_CONFIG_FILE=str(output / "human-config"),
    )
    return env


def claim(output, *, now):
    spec = review(output, now=now)
    # CreateNew + fsync; partial/error claims are retained. No release/retry API.
    local.write_private(output / "attempt.claim", b"possibly_started\n")
    if os.name != "nt":
        descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return spec


def verify_capture(capture, expected):
    """Same strict verifier for synthetic tests and future supervised private capture."""
    try:
        identity(expected)
        if (
            capture.status != "completed"
            or capture.native_exit != 0
            or capture.stderr
            or len(capture.stdout) > 8192
        ):
            raise ValueError("state_command_not_clean")
        actual = local.runner.strict_json(capture.stdout)
        identity(actual)
        if actual != expected:
            raise ValueError("state_identity_mismatch")
        return {
            "checkpoint": "F4-A1b",
            "result": "identity_matched",
            "mfa_verified": False,
            "http_request_count_verified": False,
        }
    finally:
        capture.clear()


def reference_identity(capture, account, arn):
    """Validate ONLY the state-user portion of a future separately approved GetUser."""
    try:
        if (
            capture.status != "completed"
            or capture.native_exit != 0
            or capture.stderr
            or len(capture.stdout) > 8192
        ):
            raise ValueError("state_reference_not_clean")
        result = local.runner.strict_json(capture.stdout)
        if not isinstance(result, dict) or set(result) != {"User"}:
            raise ValueError("state_reference_invalid")
        user = result["User"]
        if not isinstance(user, dict) or user.get("UserName") != PROFILE:
            raise ValueError("state_reference_invalid")
        expected = {"Account": account, "Arn": arn, "UserId": user.get("UserId")}
        identity(expected)
        if (
            user.get("Arn") != arn
            or user.get("Path") != arn.split(":user", 1)[1].rsplit(PROFILE, 1)[0]
        ):
            raise ValueError("state_reference_invalid")
        return expected  # Private return only; never console/report this object.
    finally:
        capture.clear()
