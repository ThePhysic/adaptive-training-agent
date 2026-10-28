"""A1a offline preparation only; no AWS launcher, sender or credential loader.

Preparation files are not permits. Real execution requires a separately reviewed
single-purpose executor and owner authorization, not a configuration switch.
"""

import argparse
import configparser
import hashlib
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

try:
    from . import private_command_runner as runner
except ImportError:  # Direct local CLI, not an AWS command launcher.
    import private_command_runner as runner

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "future-f4-human-admin"
REGION = "us-east-1"
ENDPOINT = "https://sts.us-east-1.amazonaws.com"
TIMEOUT = 120
STDOUT_LIMIT = 8192
STDERR_LIMIT = 4096
SOURCES = (
    "infra/aws/human_sts.py",
    "infra/aws/private_command_runner.py",
    "infra/aws/fixtures/identity_contract.py",
    "infra/aws/fixtures/sts_tunnel.py",
    "infra/aws/state_operator_prepare.py",
    "infra/aws/private_state.ps1",
    "tests/browser_runner.py",
)


def identity(expected):
    """Only the privately selected exact IAM user, never root/role/federation."""
    if not isinstance(expected, dict) or set(expected) != {"Account", "Arn", "UserId"}:
        raise ValueError("expected_identity_invalid")
    if not all(isinstance(value, str) for value in expected.values()):
        raise ValueError("expected_identity_invalid")
    account = expected["Account"]
    if (
        not re.fullmatch(r"[0-9]{12}", account)
        or len(expected["Arn"]) > 2048
        or not re.fullmatch(
            rf"arn:aws:iam::{account}:user/(?:[A-Za-z0-9+=,.@_-]+/)*{PROFILE}",
            expected["Arn"],
        )
        or not re.fullmatch(r"[A-Za-z0-9]{16,128}", expected["UserId"])
    ):
        raise ValueError("expected_identity_invalid")


def selected_configuration(text, expected):
    identity(expected)
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(text)
        if parser.defaults() or parser.sections() != ["profile " + PROFILE]:
            raise ValueError
        section = dict(parser["profile " + PROFILE])
        runner.local("infra/aws/fixtures/identity_contract.py").verify_source(section, expected)
    except (configparser.Error, ValueError, TypeError):  # fmt: skip
        raise ValueError("selected_configuration_rejected") from None
    return f"[profile {PROFILE}]\nregion = {REGION}\nlogin_session = {expected['Arn']}\n"


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}(-\d\d){2}T\d\d(:\d\d){2}Z", value):
        raise ValueError("utc_time_invalid")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("utc_time_invalid") from None


def validate(manifest, now):
    if not isinstance(manifest, dict) or set(manifest) != {
        "expected",
        "profile",
        "region",
        "endpoint",
        "window_start",
        "window_end",
        "session_expires_at",
        "cli_path",
        "cli_sha256",
    }:
        raise ValueError("preparation_shape_invalid")
    identity(manifest["expected"])
    if (manifest["profile"], manifest["region"], manifest["endpoint"]) != (
        PROFILE,
        REGION,
        ENDPOINT,
    ):
        raise ValueError("fixed_operation_binding_rejected")
    start, end = (instant(manifest[key]) for key in ("window_start", "window_end"))
    if (
        not isinstance(now, datetime)
        or now.utcoffset() != timedelta(0)
        or not timedelta(0) < end - start <= timedelta(minutes=30)
        or not start <= now
        or now + timedelta(minutes=5) > end
    ):
        raise ValueError("preparation_window_rejected")
    # Metadata attestation only, not a cache inspection or proof CLI will not refresh.
    if instant(manifest["session_expires_at"]) < now + timedelta(seconds=TIMEOUT + 300):
        raise ValueError("authentication_expired_or_too_close")
    path, digest = manifest["cli_path"], manifest["cli_sha256"]
    if (
        not isinstance(path, str)
        or not Path(path).is_absolute()
        or path.startswith(("\\\\", "//"))
        or len(path) > 4096
        or any(ord(char) < 32 for char in path)
        or Path(path).name.lower() not in {"aws", "aws.exe"}
        or not isinstance(digest, str)
        or not re.fullmatch(r"[a-f0-9]{64}", digest)
    ):
        raise ValueError("pinned_cli_required")


def command(executable):
    """No service/action/profile/endpoint/extra-arguments parameter exists."""
    args = runner.command("identity", executable=executable, profile=PROFILE)
    return tuple(args + ["--no-cli-auto-prompt", "--no-paginate"])


def environment(inherited, root, guard_proxy):
    if any(key.upper().startswith("BOTO") for key in inherited):
        raise ValueError("inherited_credential_or_route_override")
    match = re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})", guard_proxy)
    if not match or int(match[1]) > 65535:
        raise ValueError("owned_guard_proxy_required")
    env = runner.environment(
        inherited,
        profile=PROFILE,
        home=root / "home",
        config=root / "selected-config",
        empty_credentials=root / "empty-credentials",
        cache=root / "login-cache",
        rc=root / "unused.rc",
        proxy=guard_proxy,
    )
    # Also suppress legacy boto/system files and client metrics; never read /etc/boto.cfg.
    env.update(
        BOTO_CONFIG=str(root / "empty-credentials"),
        AWS_CSM_ENABLED="false",
        TEMP=str(root / "tmp"),
        TMP=str(root / "tmp"),
    )
    return {key: value for key, value in env.items() if not key.startswith("TF_")}


def private(path):
    return runner.local("infra/aws/state_operator_prepare.py").private(path)


def read_private(path):
    with private(path).open("rb") as stream:
        body = stream.read(STDOUT_LIMIT + 1)
    if len(body) > STDOUT_LIMIT:
        raise ValueError("private_input_too_large")
    return body


def write_private(path, body):
    if len(body) > STDOUT_LIMIT:
        raise ValueError("private_output_too_large")
    private(path.parent)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    private(path)


def verify_binary(manifest):
    executable = Path(manifest["cli_path"])
    if any(p.is_symlink() or p.is_junction() for p in (executable, *executable.parents)):
        raise ValueError("cli_link_rejected")
    with executable.open("rb") as stream:
        if os.fstat(stream.fileno()).st_size > 128 * 1024 * 1024:
            raise ValueError("cli_binary_too_large")
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != manifest["cli_sha256"]:
        raise ValueError("cli_binary_changed")
    return executable


def prepare(manifest_path, configuration_path, output, *, now):
    """Inspect protected identity/config metadata only; never load a login cache."""
    manifest = runner.strict_json(read_private(manifest_path))
    validate(manifest, now)
    config = selected_configuration(
        read_private(configuration_path).decode("utf-8"), manifest["expected"]
    )
    executable = verify_binary(manifest)
    private(output)
    # Exclusive creates intentionally leave partial preparation on any failure.
    # Never overwrite/reuse it or interpret it as a consumed/active live permit.
    write_private(
        output / "preparation.json",
        (
            json.dumps(
                {
                    "kind": "offline-human-sts-preparation-v1",
                    "live_execution": False,
                    "manifest": manifest,
                    "argv": command(executable),
                    "source_sha256": {
                        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                        for name in SOURCES
                    },
                },
                indent=2,
            )
            + "\n"
        ).encode(),
    )
    write_private(output / "selected-config", config.encode())
    write_private(output / "empty-credentials", b"")
    for name in ("home", "login-cache", "tmp"):
        (output / name).mkdir(mode=0o700)
        private(output / name)
    return {"result": "offline_prepared", "live_execution": False, "credentials_loaded": False}


def verify_preparation(output, *, now):
    """Offline re-attestation only. A copied READY/JSON file grants no authority."""
    value = runner.strict_json(read_private(output / "preparation.json"))
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "live_execution", "manifest", "argv", "source_sha256"}
        or value["kind"] != "offline-human-sts-preparation-v1"
        or value["live_execution"] is not False
    ):
        raise ValueError("offline_preparation_invalid")
    validate(value["manifest"], now)
    verify_binary(value["manifest"])
    if value["argv"] != list(command(value["manifest"]["cli_path"])) or value["source_sha256"] != {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES
    }:
        raise ValueError("preparation_source_or_command_changed")
    config = read_private(output / "selected-config").decode("utf-8")
    if selected_configuration(config, value["manifest"]["expected"]) != config:
        raise ValueError("selected_configuration_changed")
    if read_private(output / "empty-credentials"):
        raise ValueError("empty_credentials_required")
    for name in ("home", "login-cache", "tmp"):
        if any(private(output / name).iterdir()):
            raise ValueError("offline_preparation_directory_not_empty")
    return {"result": "offline_preparation_verified", "live_execution": False}


def claim_offline_attempt(output, *, now, abort=None):
    """Testable one-shot fence, not a permit or process-release mechanism.

    A created/partially written claim is never removed on cancellation, I/O error,
    process failure or restart. No real executor consumes this offline record.
    """
    if abort is not None and abort.is_set():
        raise ValueError("attempt_cancelled_before_claim")
    verify_preparation(output, now=now)
    record = {
        "kind": "human-sts-offline-attempt-fence-v1",
        "operation": "sts:GetCallerIdentity",
        "profile": PROFILE,
        "preparation_sha256": hashlib.sha256(read_private(output / "preparation.json")).hexdigest(),
        "state": "possibly_started",
        "live_execution": False,
    }
    try:
        write_private(output / "attempt.claim.json", (json.dumps(record) + "\n").encode())
        if os.name != "nt":
            descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except FileExistsError:
        raise ValueError("attempt_already_claimed") from None
    except (OSError, ValueError, runner.subprocess.SubprocessError):  # fmt: skip
        raise ValueError("attempt_claim_failed_do_not_release") from None
    if abort is not None and abort.is_set():
        raise ValueError("attempt_cancelled_after_claim_hold_retained")
    return {"result": "offline_attempt_claim_held", "live_execution": False}


def evaluate_fixture(capture, expected, policy):
    """Synthetic protocol evidence only; no raw stdout/stderr or identifiers escape.

    A tunnel claim is not a send acknowledgement. A failed process after a claim
    stays uncertain, even when it reports expired authentication or cancellation.
    """
    summary = policy.summary()
    claimed = summary["allowed_tunnels"] != 0
    public = {
        "evidence": "offline_fixture",
        "operation_completed": False,
        "identity_matched": False,
        "safety_failure": None,
        "request_sent": None if claimed else False,
    }
    try:
        identity(expected)
        if summary["blocked_reasons"] or policy.abort.is_set():
            public["safety_failure"] = "transport_guard_rejected"
        elif summary["allowed_tunnels"] != 1 or summary["connection_attempts"] != 1:
            public["safety_failure"] = "single_attempt_evidence_missing"
        elif len(capture.stdout) > STDOUT_LIMIT or len(capture.stderr) > STDERR_LIMIT:
            public["safety_failure"] = "output_limit"
        elif capture.status != "completed":
            public["safety_failure"] = {
                "deadline": "deadline",
                "cancelled": "cancelled",
                "cancelled_before_start": "cancelled",
                "cancelled_before_release": "cancelled",
                "output_limit": "output_limit",
            }.get(capture.status, "capture_or_cleanup_failed")
        elif capture.native_exit != 0 or capture.stderr:
            public["safety_failure"] = "process_or_authentication_failed"
        else:
            value = runner.strict_json(capture.stdout)
            if (
                not isinstance(value, dict)
                or set(value) != {"Account", "Arn", "UserId"}
                or not all(
                    isinstance(value[key], str) and 0 < len(value[key]) <= limit
                    for key, limit in (("Account", 12), ("Arn", 2048), ("UserId", 128))
                )
            ):
                raise ValueError
            public["operation_completed"] = True
            public["request_sent"] = True  # Synthetic response, not evidence AWS received anything.
            public["identity_matched"] = value == expected
            if value != expected:
                public["safety_failure"] = "identity_mismatch"
    except (ValueError, TypeError, RecursionError):  # fmt: skip
        public["safety_failure"] = "identity_or_response_invalid"
    finally:
        capture.clear()
    return public


def save_fixture(path, result):
    """Only finite synthetic summaries can be persisted, once, privately."""
    if (
        not isinstance(result, dict)
        or set(result)
        != {"evidence", "operation_completed", "identity_matched", "safety_failure", "request_sent"}
        or result["evidence"] != "offline_fixture"
        or any(type(result[key]) is not bool for key in ("operation_completed", "identity_matched"))
        or not (result["request_sent"] is None or type(result["request_sent"]) is bool)
        or result["safety_failure"]
        not in {
            None,
            "transport_guard_rejected",
            "single_attempt_evidence_missing",
            "output_limit",
            "deadline",
            "cancelled",
            "capture_or_cleanup_failed",
            "process_or_authentication_failed",
            "identity_mismatch",
            "identity_or_response_invalid",
        }
    ):
        raise ValueError("fixture_result_rejected")
    if (
        result["operation_completed"] != (result["request_sent"] is True)
        or result["identity_matched"] != (result["safety_failure"] is None)
        or (result["identity_matched"] and not result["operation_completed"])
    ):
        raise ValueError("fixture_result_rejected")
    write_private(path, (json.dumps(result) + "\n").encode())


def execute_live(*args, **kwargs):
    # Deliberately unconditional: no env/config/credential/flag can activate this.
    raise PermissionError("human_sts_offline_only_no_live_executor")


def main():
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            self.exit(2, "human_sts_arguments_rejected\n")

    parser = Parser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--selected-config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.verify_only:
            if args.manifest or args.selected_config:
                raise ValueError("verification_arguments_rejected")
            result = verify_preparation(args.output, now=datetime.now(UTC))
        else:
            if not args.manifest or not args.selected_config:
                raise ValueError("preparation_arguments_required")
            result = prepare(
                args.manifest, args.selected_config, args.output, now=datetime.now(UTC)
            )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        runner.subprocess.SubprocessError,
    ):
        print("human_sts_preparation_rejected")
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
