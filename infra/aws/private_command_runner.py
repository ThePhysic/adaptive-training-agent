"""Offline preparation and synthetic process tests; account execution stays closed.

No command-line AWS launcher, credential loader, login/refresh or network sender.
Private stdout/stderr are memory-only, excluded from repr and ordinary diagnostics.
"""

import argparse
import configparser
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event, Lock, Thread

ROOT = Path(__file__).resolve().parents[2]
REGION = "us-east-1"
ADMIN_USER = "future-f4-policy-administrator"  # Proposal, not an existing identity.
OPERATOR_USER = "future-f4-state-operator"
ACCOUNT_EXECUTION_ENABLED = False  # Source-review barrier. No environment override.
OPERATIONS = {"identity", "policy_read", "policy_install", "policy_remove", "bootstrap_plan"}
WRITES = {"policy_install", "policy_remove"}
BOOTSTRAP = """
import json, subprocess, sys
value = json.loads(sys.stdin.buffer.readline(65537))
if set(value) != {'argv'}: raise SystemExit(124)
child = subprocess.Popen(value['argv'], stdin=subprocess.DEVNULL, shell=False)
raise SystemExit(child.wait())
"""


def local(relative):
    spec = importlib.util.spec_from_file_location("private_runner_dependency", ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate_json_field")
            value[key] = item
        return value

    try:
        return json.loads(raw, object_pairs_hook=unique)
    except (
        ValueError,
        UnicodeError,
    ):
        raise ValueError("private_json_invalid") from None


def window(spec, now):
    local("infra/aws/state_bundle.py").render(spec)
    start, end = (
        datetime.fromisoformat(spec[key])
        for key in ("permission_starts_at", "permission_expires_at")
    )
    if now.tzinfo is None or not start <= now or now + timedelta(minutes=5) > end:
        raise ValueError("permission_window_inactive_or_insufficient")


def binding(profile, section, expected, *, administrator=False):
    if (
        not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile)
        or profile.lower() in {"default", "future-f4-preflight"}
        or set(expected) != {"Account", "Arn", "UserId"}
    ):
        raise ValueError("explicit_identity_required")
    local("infra/aws/fixtures/identity_contract.py").verify_source(section, expected)
    user = ADMIN_USER if administrator else OPERATOR_USER
    if not re.fullmatch(
        rf"arn:aws:iam::{expected['Account']}:user/(?:[A-Za-z0-9+=,.@_-]+/)*{user}",
        expected["Arn"],
    ):
        raise ValueError("wrong_selected_user")
    return f"[profile {profile}]\nregion = {REGION}\nlogin_session = {expected['Arn']}\n"


def selected_configuration(text, profile, expected, *, administrator=False):
    """Validate a selected-only snapshot, never inherit default/other profiles."""
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(text)
        if parser.defaults() or parser.sections() != ["profile " + profile]:
            raise ValueError
        section = dict(parser["profile " + profile])
    except (
        configparser.Error,
        ValueError,
    ):
        raise ValueError("selected_only_configuration_required") from None
    return binding(profile, section, expected, administrator=administrator)


def environment(inherited, *, profile, home, config, empty_credentials, cache, rc, proxy):
    """Only OS basics plus reviewed explicit sources; never inherit AWS/TF/proxy knobs."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile) or profile.lower() in {
        "default",
        "future-f4-preflight",
    }:
        raise ValueError("explicit_profile_required")
    if any(key.upper().startswith(("AWS_", "TF_")) or "PROXY" in key.upper() for key in inherited):
        raise ValueError("inherited_credential_or_route_override")
    if not re.fullmatch(r"http://127\.0\.0\.1:[1-9][0-9]{0,4}", proxy):
        raise ValueError("owned_guard_proxy_required")
    env = local("infra/aws/fixtures/identity_contract.py").environment(
        inherited, home, config, empty_credentials, cache, rc, proxy
    )
    env.update(
        AWS_PROFILE=profile,
        AWS_DEFAULT_PROFILE=profile,
        AWS_PAGER="",
        AWS_CLI_AUTO_PROMPT="off",
        NO_PROXY="",  # Even link-local/loopback AWS destinations cannot bypass the guard.
        ALL_PROXY=proxy,
    )
    return env


def administrator_proposal(spec, administrator_arn):
    """Three IAM actions on one user; named-policy/body limits are client-side only."""
    local("infra/aws/state_operator_prepare.py").operator_spec(spec)
    binding(
        "synthetic-admin-selection",
        {"region": REGION, "login_session": administrator_arn},
        {"Account": spec["account_id"], "Arn": administrator_arn, "UserId": "PRIVATE"},
        administrator=True,
    )
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iam:GetUserPolicy", "iam:PutUserPolicy", "iam:DeleteUserPolicy"],
                "Resource": spec["bootstrap_principal_arn"],
                "Condition": {
                    "ArnEquals": {"aws:PrincipalArn": administrator_arn},
                    "StringEquals": {
                        "aws:PrincipalAccount": spec["account_id"],
                        "aws:RequestedRegion": REGION,
                    },
                    "Bool": {
                        "aws:SecureTransport": "true",
                        "aws:MultiFactorAuthPresent": "true",
                    },
                    "DateGreaterThanEquals": {"aws:CurrentTime": spec["permission_starts_at"]},
                    "DateLessThan": {"aws:CurrentTime": spec["permission_expires_at"]},
                },
            }
        ],
    }


def command(operation, *, executable, profile, administrator=False, policy=None, label=None):
    """Closed AWS command vocabulary; Terraform is prepared separately, never apply."""
    if operation not in OPERATIONS - {"bootstrap_plan"}:
        raise ValueError("unsupported_command")
    if not Path(executable).is_absolute() or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", profile):
        raise ValueError("explicit_executable_and_profile_required")
    if profile.lower() in {"default", "future-f4-preflight"}:
        raise ValueError("read_only_or_default_profile_rejected")
    if operation != "identity" and not administrator:
        raise ValueError("administrator_selection_required")
    if operation == "identity":
        args = ["sts", "get-caller-identity"]
        endpoint = "https://sts.us-east-1.amazonaws.com"
    else:
        if not label or not re.fullmatch(r"cb-[a-f0-9]{32}", label):
            raise ValueError("opaque_policy_label_required")
        args = [
            "iam",
            {
                "policy_read": "get-user-policy",
                "policy_install": "put-user-policy",
                "policy_remove": "delete-user-policy",
            }[operation],
            "--user-name",
            OPERATOR_USER,
            "--policy-name",
            "FataBootstrap-" + label,
        ]
        if operation == "policy_install":
            if (
                not policy
                or not Path(policy).is_absolute()
                or Path(policy).name != "bootstrap_operator_policy.json"
            ):
                raise ValueError("reviewed_bootstrap_policy_required")
            args += ["--policy-document", "file://" + str(policy)]
        endpoint = "https://iam.amazonaws.com"
    return [
        str(executable),
        *args,
        "--profile",
        profile,
        "--region",
        REGION,
        "--endpoint-url",
        endpoint,
        "--output",
        "json",
        "--no-cli-pager",
        "--cli-connect-timeout",
        "5",
        "--cli-read-timeout",
        "15",
    ]


def prepare_bootstrap_plan(
    *,
    spec_path,
    label,
    expected,
    profile,
    executable,
    inherited,
    home,
    config,
    empty_credentials,
    cache,
    rc,
    proxy,
):
    """Prepare only the accepted local-state root/vector; never start Terraform.

    No provider override or new data resource is added to the six-resource plan.
    Selected-only config + explicit empty credential file prevent alternate SDK
    sources; actual identity still needs a fresh, separately approved private STS
    postcondition before any future execution with this same immutable context.
    """
    helper = local("infra/aws/state_operator_prepare.py")
    spec = helper.operator_spec(helper.private_json(spec_path))
    helper.verify_source(label, spec)
    if (
        expected["Account"] != spec["account_id"]
        or expected["Arn"] != spec["bootstrap_principal_arn"]
    ):
        raise ValueError("operator_plan_identity_mismatch")
    canonical = selected_configuration(
        helper.private(config).read_text(encoding="utf-8"), profile, expected
    )
    if helper.private(config).read_text(encoding="utf-8") != canonical:
        raise ValueError("noncanonical_selected_configuration")
    if helper.private(empty_credentials).read_bytes():
        raise ValueError("empty_credential_file_required")
    for path in (home, cache):
        helper.private(path)
    review = ROOT / ".cache/r5b-checkpoint-b" / label
    if rc != review / "offline.rc" or helper.private(rc).read_text(encoding="utf-8") != (
        "disable_checkpoint = true\nprovider_installation { filesystem_mirror { path = "
        + json.dumps((ROOT / "infra/aws/state-bootstrap/.terraform/providers").as_posix())
        + " } }\n"
    ):
        raise ValueError("reviewed_cached_only_plugin_configuration_required")
    source = review / "source/infra/aws/state-bootstrap"
    # Empty initial bootstrap only; recovery is a separately reviewed operation.
    if any(source.glob("*.tfstate*")):
        raise ValueError("existing_state_recovery_required")
    saved = review / "bootstrap.tfplan"
    if saved.exists() or not Path(executable).is_absolute():
        raise ValueError("fresh_saved_plan_and_explicit_binary_required")
    env = environment(
        inherited,
        profile=profile,
        home=home,
        config=config,
        empty_credentials=empty_credentials,
        cache=cache,
        rc=rc,
        proxy=proxy,
    )
    argv = [
        str(executable),
        f"-chdir={source}",
        "plan",
        "-input=false",
        "-no-color",
        "-detailed-exitcode",
        "-lock-timeout=0s",
        f"-var-file={ROOT / '.cache/state-backend' / label / 'bootstrap.tfvars.json'}",
        f"-out={saved}",
    ]
    return argv, env  # Private in-memory values; never serialize to normal logs.


@dataclass(repr=False)
class Capture:
    native_exit: int | None
    status: str
    stdout: bytearray = field(repr=False)
    stderr: bytearray = field(repr=False)
    # Local wrapper evidence only, never HTTP delivery or credential classification.
    process_release: str = "unknown"
    cleanup_state: str = "unknown"

    def __repr__(self):
        return f"Capture(native_exit={self.native_exit!r}, status={self.status!r})"

    def clear(self):
        for stream in (self.stdout, self.stderr):
            stream[:] = b"\0" * len(stream)
            stream.clear()


def capture_owned(
    argv,
    *,
    cwd,
    env,
    timeout=120,
    abort=None,
    clock=time.monotonic,
    stdout_limit=1048576,
    stderr_limit=65536,
):
    """Bounded private memory, stdin release after OS ownership, no shell/retry.

    Generic internal primitive tested with synthetic Python children only. It is
    not exposed as an account command-line entrypoint. The future account gate is
    separate. Windows ownership reuses the reviewed browser harness Job Object.
    """
    if not 0 < timeout <= 120 or not 0 < stdout_limit <= 1048576 or not 0 < stderr_limit <= 65536:
        raise ValueError("capture_bounds_invalid")
    abort = abort or Event()
    if abort.is_set():
        return Capture(
            None, "cancelled_before_start", bytearray(), bytearray(), "not_released", "not_started"
        )
    release = json.dumps({"argv": list(map(str, argv))}).encode() + b"\n"
    if len(release) > 65536:
        raise ValueError("command_too_large")
    job = local("tests/browser_runner.py").WindowsJob() if os.name == "nt" else None
    child = None
    readers = []
    overflow, read_failure = Event(), Event()
    buffers = [bytearray(), bytearray()]
    lock = Lock()
    end = clock() + timeout
    status = "completed"
    process_release = "not_released"
    cleanup_uncertain = False

    def read(stream, target, limit):
        try:
            while chunk := stream.read(4096):
                with lock:
                    remaining = limit - len(target)
                    target.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    overflow.set()
                    return
        except (
            OSError,
            ValueError,
        ):
            read_failure.set()
        finally:
            stream.close()

    def release_owned():
        try:
            child.stdin.write(release)
            child.stdin.flush()
        except (
            OSError,
            ValueError,
        ):
            read_failure.set()
        finally:
            child.stdin.close()

    try:
        child = subprocess.Popen(
            [sys.executable, "-I", "-S", "-c", BOOTSTRAP],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if job:
            job.attach(child.pid)
        for stream, buffer, limit in zip(
            (child.stdout, child.stderr), buffers, (stdout_limit, stderr_limit), strict=True
        ):
            thread = Thread(target=read, args=(stream, buffer, limit), daemon=True)
            readers.append(thread)
            thread.start()
        if abort.is_set() or clock() >= end:
            status = "cancelled_before_release"
        else:
            # Conservative before starting the writer: full/partial stdin release
            # can permit native launch; it does not acknowledge launch or a socket.
            process_release = "may_have_released"
            writer = Thread(target=release_owned, daemon=True)
            readers.append(writer)
            writer.start()
            while True:
                if abort.is_set():
                    status = "cancelled"
                    break
                if overflow.is_set():
                    status = "output_limit"
                    break
                if read_failure.is_set():
                    status = "capture_failed"
                    break
                if clock() >= end:
                    status = "deadline"
                    break
                if child.poll() is not None:
                    break
                abort.wait(0.01)
    except (
        OSError,
        RuntimeError,
    ):
        status = "launch_or_ownership_failed"
    except BaseException:
        status = "interrupted"
        raise
    finally:
        if job:
            job.close()  # Kill all descendants even if the parent has exited.
        elif child:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if child:
            if child.poll() is None:
                child.kill()  # Covers Windows attach failure before release.
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cleanup_uncertain = True
                status = "cleanup_incomplete"
            if child.stdin and not child.stdin.closed and not readers:
                child.stdin.close()
        cleanup_end = time.monotonic() + 5
        for thread in readers:
            thread.join(timeout=max(0, cleanup_end - time.monotonic()))
        if any(thread.is_alive() for thread in readers):
            cleanup_uncertain = True
            status = "cleanup_incomplete"
        elif overflow.is_set():
            status = "output_limit"
        elif read_failure.is_set():
            status = "capture_failed"
        if child and not any(thread.is_alive() for thread in readers):
            for pipe in (child.stdin, child.stdout, child.stderr):
                if pipe and not pipe.closed:
                    pipe.close()
        if status != "completed":
            for buffer in buffers:
                buffer[:] = b"\0" * len(buffer)
                buffer.clear()
    return Capture(
        child.returncode if child else None,
        status,
        *buffers,
        process_release,
        "uncertain" if cleanup_uncertain else "completed",
    )


def verify_identity(result, expected):
    if (
        result.status != "completed"
        or result.native_exit != 0
        or strict_json(result.stdout) != expected
    ):
        raise ValueError("private_identity_postcondition_failed")


def classify(operation, result, *, expected=None, policy_name=None, policy=None):
    """Only finite labels escape; raw service exceptions/identifiers never do."""
    try:
        if operation not in OPERATIONS:
            return "unsupported_command"
        accepted_exit = {0, 2} if operation == "bootstrap_plan" else {0}
        if result.status != "completed" or result.native_exit not in accepted_exit:
            if operation in WRITES:
                return "reconcile_required"
            if (
                operation == "policy_read"
                and result.status == "completed"
                and re.match(
                    rb"\s*An error occurred \(NoSuchEntity\) "
                    rb"when calling the GetUserPolicy operation:",
                    result.stderr,
                )
            ):
                return "policy_absent"
            return "read_or_plan_failed"
        if operation == "identity":
            verify_identity(result, expected)
            return "identity_verified"
        if operation == "policy_read":
            document = strict_json(result.stdout)
            if document != {
                "UserName": OPERATOR_USER,
                "PolicyName": policy_name,
                "PolicyDocument": policy,
            }:
                return "policy_mismatch"
            return "policy_matches"
        if operation in WRITES:
            # Even an empty success needs separately authorized readback.
            return "readback_required" if not result.stdout.strip() else "reconcile_required"
        return "saved_plan_review_required" if result.native_exit == 2 else "unexpected_plan_result"
    except (
        ValueError,
        TypeError,
    ):
        return "private_response_invalid"
    finally:
        result.clear()


def claim(path, operation):
    """Local one-shot fence, not AWS idempotency or a financial permit.

    Claim survives crash/ambiguous result. Never overwrite/remove to retry writes.
    Callers must use an owner-protected ignored directory verified by private().
    """
    if operation not in OPERATIONS:
        raise ValueError("unsupported_command")
    local("infra/aws/state_operator_prepare.py").private(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(json.dumps({"operation": operation, "status": "possibly_started"}) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    local("infra/aws/state_operator_prepare.py").private(path)


def execute_account(*args, **kwargs):
    # Deliberately no active orchestration from proposal -> send in this unit.
    # Credentials, manifests and environment cannot activate the runner.
    raise PermissionError("offline_preparation_only_account_execution_disabled")


def prepare_administrator(spec_path, identity_path, output):
    helper = local("infra/aws/state_operator_prepare.py")
    spec = helper.operator_spec(helper.private_json(spec_path))
    expected = helper.private_json(identity_path)
    binding(
        "proposed-admin",
        {"region": REGION, "login_session": expected.get("Arn", "")},
        expected,
        administrator=True,
    )
    if expected["Account"] != spec["account_id"]:
        raise ValueError("administrator_account_mismatch")
    proposal = administrator_proposal(spec, expected["Arn"])
    helper.private(output.parent)
    # Exclusive, private, non-overwriting proposal; no IAM attachment.
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(proposal, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    helper.private(output)
    return {"result": "offline_administrator_proposal_only", "actions": 3, "target_users": 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-administrator", action="store_true")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.prepare_administrator or not all((args.spec, args.identity, args.output)):
        print("offline_preparation_only_account_execution_disabled")
        return 1
    try:
        result = prepare_administrator(args.spec, args.identity, args.output)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
    ):
        print("offline_administrator_preparation_rejected")
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
