"""Synthetic AWS protocol/process fixtures only; no CLI, cache or real AWS calls."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Event, Thread

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location(
        "private_command_runner", ROOT / "infra/aws/private_command_runner.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def expected():
    return {
        "Account": "000000000000",
        "Arn": "arn:aws:iam::000000000000:user/future-f4-state-operator",
        "UserId": "SYNTHETIC_PRIVATE_ID",
    }


@pytest.fixture
def authority(expected):
    return {
        "account_id": expected["Account"],
        "bucket_name": "fata-synthetic-state",
        "bootstrap_principal_arn": expected["Arn"],
        "state_principal_arn": expected["Arn"],
        "permission_starts_at": "2030-01-01T00:00:00Z",
        "permission_expires_at": "2030-01-01T02:00:00Z",
    }


def captured(runner, data=b"", code=0, status="completed", error=b""):
    return runner.Capture(code, status, bytearray(data), bytearray(error))


def selected(runner, expected):
    return runner.binding(
        "synthetic-operator", {"region": "us-east-1", "login_session": expected["Arn"]}, expected
    )


def synthetic_env():
    # Child fixtures need OS basics only. Never inherit host AWS/credential values.
    return {
        k: v
        for k, v in os.environ.items()
        if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}
    }


def test_approved_operator_and_proposed_admin_remain_distinct(runner, expected, authority):
    text = selected(runner, expected)
    assert runner.selected_configuration(text, "synthetic-operator", expected) == text
    admin = expected["Arn"].replace("future-f4-state-operator", runner.ADMIN_USER)
    policy = runner.administrator_proposal(authority, admin)["Statement"][0]
    assert set(policy["Action"]) == {
        "iam:GetUserPolicy",
        "iam:PutUserPolicy",
        "iam:DeleteUserPolicy",
    }
    assert policy["Resource"] == expected["Arn"]
    assert policy["Condition"]["ArnEquals"] == {"aws:PrincipalArn": admin}
    assert policy["Condition"]["Bool"] == {
        "aws:SecureTransport": "true",
        "aws:MultiFactorAuthPresent": "true",
    }
    assert (
        policy["Condition"]["DateLessThan"]["aws:CurrentTime"] == authority["permission_expires_at"]
    )
    assert policy["Condition"]["StringEquals"]["aws:RequestedRegion"] == "us-east-1"
    assert "PolicyName" not in repr(policy)  # No invented IAM condition key.


@pytest.mark.parametrize(
    "fault",
    [
        "default",
        "preflight",
        "root",
        "role",
        "wrong_account",
        "wrong_user",
        "wrong_region",
        "other_profile",
        "extra_default",
        "static_key",
        "process",
        "source",
        "sso",
        "endpoint",
    ],
)
def test_source_selection_fails_closed(runner, expected, fault):
    text = selected(runner, expected)
    profile = "synthetic-operator"
    if fault in {"default", "preflight"}:
        profile = "default" if fault == "default" else "future-f4-preflight"
        text = text.replace("synthetic-operator", profile)
    elif fault in {"root", "role", "wrong_account", "wrong_user"}:
        expected = copy.deepcopy(expected)
        expected["Arn"] = {
            "root": "arn:aws:iam::000000000000:root",
            "role": "arn:aws:sts::000000000000:assumed-role/operator/session",
            "wrong_account": "arn:aws:iam::111111111111:user/future-f4-state-operator",
            "wrong_user": "arn:aws:iam::000000000000:user/future-f4-policy-administrator",
        }[fault]
    elif fault == "wrong_region":
        text = text.replace("us-east-1", "us-west-2")
    elif fault == "other_profile":
        text += "\n[profile other]\nregion = us-east-1\n"
    elif fault == "extra_default":
        text += "\n[DEFAULT]\nrole_arn = synthetic\n"
    else:
        key = {
            "static_key": "aws_access_key_id",
            "process": "credential_process",
            "source": "source_profile",
            "sso": "sso_session",
            "endpoint": "endpoint_url",
        }[fault]
        text += f"{key} = PRIVATE_CANARY\n"
    with pytest.raises(ValueError) as error:
        runner.selected_configuration(text, profile, expected)
    assert "CANARY" not in str(error.value)


@pytest.mark.parametrize(
    "poison",
    [
        "AWS_ACCESS_KEY_ID",
        "AWS_PROFILE",
        "AWS_CONFIG_FILE",
        "AWS_ENDPOINT_URL",
        "AWS_ROLE_ARN",
        "AWS_CA_BUNDLE",
        "AWS_WEB_IDENTITY_TOKEN_FILE",
        "AWS_CONTAINER_CREDENTIALS_FULL_URI",
        "TF_CLI_ARGS_plan",
        "TF_VAR_account_id",
        "TF_LOG",
        "https_proxy",
    ],
)
def test_environment_override_rejected_not_printed(runner, tmp_path, poison):
    with pytest.raises(ValueError, match="inherited_credential_or_route_override"):
        runner.environment(
            {poison: "PRIVATE_CANARY"},
            profile="operator",
            home=tmp_path,
            config=tmp_path / "config",
            empty_credentials=tmp_path / "empty",
            cache=tmp_path / "cache",
            rc=tmp_path / "rc",
            proxy="http://127.0.0.1:1234",
        )


def test_environment_pins_explicit_sources_no_metadata_or_proxy_bypass(runner, tmp_path):
    env = runner.environment(
        {"PATH": "synthetic", "UNRELATED_SECRET": "CANARY"},
        profile="operator",
        home=tmp_path,
        config=tmp_path / "config",
        empty_credentials=tmp_path / "empty",
        cache=tmp_path / "cache",
        rc=tmp_path / "rc",
        proxy="http://127.0.0.1:1234",
    )
    assert env["AWS_PROFILE"] == env["AWS_DEFAULT_PROFILE"] == "operator"
    assert env["AWS_EC2_METADATA_DISABLED"] == "true" and env["AWS_MAX_ATTEMPTS"] == "1"
    assert env["NO_PROXY"] == "" and env["AWS_CLI_AUTO_PROMPT"] == "off"
    assert "CANARY" not in env.values() and env["AWS_SHARED_CREDENTIALS_FILE"].endswith("empty")


@pytest.mark.parametrize(
    "now,accepted",
    [
        ("2029-12-31T23:59:59Z", False),
        ("2030-01-01T00:00:00Z", True),
        ("2030-01-01T01:55:00Z", True),
        ("2030-01-01T01:55:01Z", False),
        ("2030-01-01T02:00:00Z", False),
    ],
)
def test_window_boundaries_do_not_extend_authority(runner, authority, now, accepted):
    if accepted:
        runner.window(authority, datetime.fromisoformat(now))
    else:
        with pytest.raises(ValueError):
            runner.window(authority, datetime.fromisoformat(now))


def test_commands_have_exact_user_endpoint_profile_and_no_shell(runner, tmp_path):
    executable = tmp_path / "aws.exe"
    policy = tmp_path / "private path" / "bootstrap_operator_policy.json"
    command = runner.command(
        "policy_install",
        executable=executable,
        profile="admin",
        administrator=True,
        policy=policy,
        label="cb-" + "a" * 32,
    )
    assert command[1:3] == ["iam", "put-user-policy"]
    assert command[command.index("--user-name") + 1] == runner.OPERATOR_USER
    assert command[command.index("--endpoint-url") + 1] == "https://iam.amazonaws.com"
    assert command[command.index("--policy-document") + 1] == "file://" + str(policy)
    assert "--no-verify-ssl" not in command and "--debug" not in command
    with pytest.raises(ValueError):
        runner.command("policy_install", executable=executable, profile="operator", policy=policy)
    with pytest.raises(ValueError):
        runner.command("apply", executable=executable, profile="operator")


@pytest.mark.parametrize(
    "fault",
    [
        "root",
        "preflight",
        "admin",
        "account",
        "user_id",
        "duplicate",
        "invalid_json",
        "exit",
        "cancelled",
    ],
)
def test_identity_postconditions_reject_wrong_principal_and_ambiguous_results(
    runner, expected, fault
):
    data = dict(expected)
    code, status = 0, "completed"
    if fault in {"root", "preflight", "admin"}:
        data["Arn"] = (
            "arn:aws:iam::000000000000:"
            + {
                "root": "root",
                "preflight": "user/future-f4-preflight",
                "admin": "user/future-f4-policy-administrator",
            }[fault]
        )
    elif fault == "account":
        data["Account"] = "111111111111"
    elif fault == "user_id":
        data["UserId"] = "DIFFERENT"
    elif fault == "exit":
        code = 1
    elif fault == "cancelled":
        status = "cancelled"
    raw = json.dumps(data).encode()
    if fault == "duplicate":
        raw = raw.replace(b"{", b'{"Account":"PRIVATE_CANARY",', 1)
    elif fault == "invalid_json":
        raw = b"PRIVATE_CANARY"
    result = captured(runner, raw, code, status, b"PRIVATE_STDERR_CANARY")
    assert runner.classify("identity", result, expected=expected) == (
        "read_or_plan_failed" if fault in {"exit", "cancelled"} else "private_response_invalid"
    )
    assert result.stdout == result.stderr == b"" and "CANARY" not in repr(result)


def test_mock_sts_and_iam_readback_share_private_classifier(runner, expected):
    assert (
        runner.classify(
            "identity", captured(runner, json.dumps(expected).encode()), expected=expected
        )
        == "identity_verified"
    )
    policy = {"Version": "2012-10-17", "Statement": []}
    response = {
        "UserName": runner.OPERATOR_USER,
        "PolicyName": "synthetic",
        "PolicyDocument": policy,
    }
    assert (
        runner.classify(
            "policy_read",
            captured(runner, json.dumps(response).encode()),
            policy_name="synthetic",
            policy=policy,
        )
        == "policy_matches"
    )
    response["UserName"] = "other"
    assert (
        runner.classify(
            "policy_read",
            captured(runner, json.dumps(response).encode()),
            policy_name="synthetic",
            policy=policy,
        )
        == "policy_mismatch"
    )
    assert (
        runner.classify(
            "policy_read",
            captured(
                runner,
                code=254,
                error=(
                    b"An error occurred (NoSuchEntity) "
                    b"when calling the GetUserPolicy operation: PRIVATE"
                ),
            ),
        )
        == "policy_absent"
    )
    assert (
        runner.classify(
            "policy_read",
            captured(
                runner,
                code=254,
                error=(
                    b"An error occurred (AccessDenied) "
                    b"when calling the GetUserPolicy operation: NoSuchEntity"
                ),
            ),
        )
        == "read_or_plan_failed"
    )


@pytest.mark.parametrize("operation", ["policy_install", "policy_remove"])
@pytest.mark.parametrize(
    "status,code,outcome",
    [
        ("completed", 0, "readback_required"),
        ("completed", 254, "reconcile_required"),
        ("deadline", 0, "reconcile_required"),
        ("cancelled", None, "reconcile_required"),
    ],
)
def test_write_results_require_reconciliation_not_automatic_replay(
    runner, operation, status, code, outcome
):
    assert runner.classify(operation, captured(runner, code=code, status=status)) == outcome


def test_one_shot_claim_survives_restart_and_does_not_store_private_values(
    runner, tmp_path, monkeypatch
):
    # Native ACL behavior is exercised by test_state_operator_preparation; here
    # isolate atomic exclusive-create/fsync and simulated process-restart semantics.
    dependency = runner.local("infra/aws/state_operator_prepare.py")
    monkeypatch.setattr(dependency, "private", lambda path: path)
    monkeypatch.setattr(runner, "local", lambda _: dependency)
    path = tmp_path / "attempt.json"
    runner.claim(path, "policy_install")
    assert json.loads(path.read_text()) == {
        "operation": "policy_install",
        "status": "possibly_started",
    }
    with pytest.raises(FileExistsError):
        runner.claim(path, "policy_install")


def test_claim_fsync_failure_leaves_hold_not_reusable(runner, tmp_path, monkeypatch):
    dependency = runner.local("infra/aws/state_operator_prepare.py")
    monkeypatch.setattr(dependency, "private", lambda path: path)
    monkeypatch.setattr(runner, "local", lambda _: dependency)
    monkeypatch.setattr(runner.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("CANARY")))
    path = tmp_path / "attempt.json"
    with pytest.raises(OSError):
        runner.claim(path, "policy_install")
    assert path.exists()
    with pytest.raises(FileExistsError):
        runner.claim(path, "policy_install")


def test_concurrent_claims_have_exactly_one_winner(runner, tmp_path, monkeypatch):
    dependency = runner.local("infra/aws/state_operator_prepare.py")
    monkeypatch.setattr(dependency, "private", lambda path: path)
    monkeypatch.setattr(runner, "local", lambda _: dependency)

    def attempt(_):
        try:
            runner.claim(tmp_path / "one-shot.json", "policy_install")
            return "claimed"
        except FileExistsError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["blocked", "claimed"]


def test_native_private_administrator_proposal_never_attaches_and_never_overwrites(
    runner, tmp_path, authority, expected, capsys
):
    identity = dict(expected)
    identity["Arn"] = identity["Arn"].replace(runner.OPERATOR_USER, runner.ADMIN_USER)
    spec_path, identity_path, output = (
        tmp_path / name for name in ("spec.json", "admin.json", "proposal.json")
    )
    for path, data in ((spec_path, authority), (identity_path, identity)):
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            json.dump(data, stream)
    assert runner.prepare_administrator(spec_path, identity_path, output) == {
        "result": "offline_administrator_proposal_only",
        "actions": 3,
        "target_users": 1,
    }
    policy = json.loads(output.read_text())
    assert policy["Statement"][0]["Resource"] == expected["Arn"]
    with pytest.raises(FileExistsError):
        runner.prepare_administrator(spec_path, identity_path, output)
    assert json.loads(output.read_text()) == policy and not capsys.readouterr().out


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "preflight",
        "admin",
        "default",
        "wrong_account",
        "static_credentials",
        "source_profile",
        "extra_tf_flag",
        "existing_state",
        "saved_plan",
        "plugin_override",
    ],
)
def test_bootstrap_plan_preparation_pins_operator_sources_without_launching(
    runner, tmp_path, authority, expected, monkeypatch, fault
):
    dependency = runner.local("infra/aws/state_operator_prepare.py")
    source_checks = []
    monkeypatch.setattr(dependency, "private", lambda path: path)
    monkeypatch.setattr(
        dependency, "verify_source", lambda label, spec: source_checks.append(label)
    )
    identity_dependency = runner.local("infra/aws/fixtures/identity_contract.py")
    monkeypatch.setattr(
        runner,
        "local",
        lambda name: (
            dependency if name.endswith("state_operator_prepare.py") else identity_dependency
        ),
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(
        runner.subprocess, "Popen", lambda *a, **k: pytest.fail("No Terraform launch")
    )
    label = "cb-" + "a" * 32
    review = tmp_path / ".cache/r5b-checkpoint-b" / label
    root = review / "source/infra/aws/state-bootstrap"
    root.mkdir(parents=True)
    spec_path, config, credentials, rc = (
        review / name for name in ("spec.json", "config", "empty", "offline.rc")
    )
    spec_path.write_text(json.dumps(authority))
    config.write_text(selected(runner, expected))
    credentials.write_bytes(b"")
    rc.write_text(
        "disable_checkpoint = true\nprovider_installation { filesystem_mirror { path = "
        + json.dumps((tmp_path / "infra/aws/state-bootstrap/.terraform/providers").as_posix())
        + " } }\n"
    )
    profile, inherited = "synthetic-operator", {}
    if fault in {"preflight", "default"}:
        profile = "future-f4-preflight" if fault == "preflight" else "default"
    elif fault == "admin":
        expected = {
            **expected,
            "Arn": expected["Arn"].replace(runner.OPERATOR_USER, runner.ADMIN_USER),
        }
    elif fault == "wrong_account":
        expected = {**expected, "Account": "111111111111"}
    elif fault == "static_credentials":
        credentials.write_text("PRIVATE_STATIC_CANARY")
    elif fault == "source_profile":
        config.write_text(config.read_text() + "source_profile = default\n")
    elif fault == "extra_tf_flag":
        inherited = {"TF_CLI_ARGS_plan": "PRIVATE_CANARY"}
    elif fault == "existing_state":
        (root / "terraform.tfstate").write_text("PRIVATE_STATE_CANARY")
    elif fault == "saved_plan":
        (review / "bootstrap.tfplan").write_text("PRIVATE_PLAN_CANARY")
    elif fault == "plugin_override":
        rc.write_text('provider_installation { dev_overrides { "hashicorp/aws" = "/tmp" } }')
    args = dict(
        spec_path=spec_path,
        label=label,
        expected=expected,
        profile=profile,
        executable=tmp_path / "terraform",
        inherited=inherited,
        home=review,
        config=config,
        empty_credentials=credentials,
        cache=review,
        rc=rc,
        proxy="http://127.0.0.1:1234",
    )
    if fault:
        with pytest.raises(ValueError) as error:
            runner.prepare_bootstrap_plan(**args)
        assert "CANARY" not in str(error.value)
    else:
        command, env = runner.prepare_bootstrap_plan(**args)
        assert command[1] == "-chdir=" + str(root) and command[2] == "plan"
        assert env["AWS_PROFILE"] == profile and "-detailed-exitcode" in command
        assert "-lock=false" not in command and not any(value == "apply" for value in command)
    assert source_checks == [label]


def run_child(runner, tmp_path, code, **kwargs):
    return runner.capture_owned(
        [sys.executable, "-I", "-S", "-c", code], cwd=tmp_path, env=synthetic_env(), **kwargs
    )


def test_native_process_capture_keeps_private_output_in_memory_only(
    runner, tmp_path, capsys, caplog
):
    result = run_child(
        runner, tmp_path, "import sys; print('PRIVATE_CANARY'); print('SECRET', file=sys.stderr)"
    )
    assert result.status == "completed" and result.native_exit == 0
    assert result.stdout.strip() == b"PRIVATE_CANARY" and result.stderr.strip() == b"SECRET"
    assert list(tmp_path.iterdir()) == [] and "CANARY" not in repr(result)
    assert not capsys.readouterr().out and not caplog.text
    result.clear()
    assert result.stdout == result.stderr == b""


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_output_flood_is_bounded_and_partial_output_discarded(runner, tmp_path, stream):
    result = run_child(
        runner,
        tmp_path,
        f"import sys; sys.{stream}.write('CANARY' * 100000)",
        stdout_limit=4096,
        stderr_limit=4096,
    )
    assert result.status == "output_limit" and result.stdout == result.stderr == b""


def test_cancel_before_start_launches_nothing(runner, tmp_path, monkeypatch):
    abort = Event()
    abort.set()
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **k: pytest.fail("No spawn"))
    result = run_child(runner, tmp_path, "raise SystemExit(1)", abort=abort)
    assert result.status == "cancelled_before_start" and result.native_exit is None


def test_owned_start_failure_never_releases_the_target(runner, tmp_path, monkeypatch):
    if os.name != "nt":
        # A failed POSIX session/process creation likewise launches no target.
        monkeypatch.setattr(
            runner.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(OSError("CANARY"))
        )
    else:

        class FailedJob:
            def attach(self, pid):
                raise RuntimeError("PRIVATE_CANARY")

            def close(self):
                pass

        class Owner:
            WindowsJob = FailedJob

        monkeypatch.setattr(runner, "local", lambda _: Owner)
    marker = tmp_path / "must-not-start"
    result = run_child(runner, tmp_path, f"from pathlib import Path; Path({str(marker)!r}).touch()")
    assert result.status == "launch_or_ownership_failed" and not marker.exists()
    assert not result.stdout and not result.stderr and "CANARY" not in repr(result)


@pytest.mark.parametrize("mode", ["deadline", "cancelled", "early_exit"])
def test_owned_descendants_terminated_after_barrier_and_unrelated_sibling_survives(
    runner, tmp_path, mode
):
    marker = tmp_path / "spawned.json"
    code = (
        "import json,os,subprocess,sys,time; from pathlib import Path; "
        "child=subprocess.Popen([sys.executable,'-I','-S','-c','import time;time.sleep(90)']); "
        f"Path({str(marker)!r}).write_text(json.dumps({{'pid':child.pid}})); "
        + ("raise SystemExit(7)" if mode == "early_exit" else "time.sleep(90)")
    )
    abort = Event()

    def clock():
        return 121 if marker.exists() and mode == "deadline" else 0

    sibling = subprocess.Popen(
        [sys.executable, "-I", "-S", "-c", "import time;time.sleep(90)"],
        env=synthetic_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def cancel_at_barrier():
        end = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < end:
            Event().wait(0.01)
        if mode == "cancelled":
            abort.set()

    worker = Thread(target=cancel_at_barrier)
    worker.start()
    try:
        result = run_child(runner, tmp_path, code, clock=clock, abort=abort)
        worker.join(timeout=10)
        assert not worker.is_alive() and marker.exists()
        assert result.status == ("completed" if mode == "early_exit" else mode)
        if mode == "early_exit":
            assert result.native_exit == 7
        browser_spec = importlib.util.spec_from_file_location(
            "browser_owner_test", ROOT / "tests/test_browser_runner.py"
        )
        # Use the existing OS process-liveness helper without running browser tests.
        module = importlib.util.module_from_spec(browser_spec)
        browser_spec.loader.exec_module(module)
        pid = json.loads(marker.read_text())["pid"]
        end = time.monotonic() + 5
        while module.running(pid) and time.monotonic() < end:
            Event().wait(0.01)
        assert not module.running(pid) and sibling.poll() is None
    finally:
        abort.set()
        worker.join(timeout=10)
        sibling.kill()
        sibling.wait(timeout=5)


def test_future_account_gate_cannot_be_enabled_with_environment_or_flags(runner, monkeypatch):
    monkeypatch.setenv("AWS_PROFILE", "synthetic-admin")
    monkeypatch.setenv("FATA_ALLOW_AWS", "1")
    monkeypatch.setattr(
        runner.subprocess, "Popen", lambda *a, **k: pytest.fail("No account execution")
    )
    with pytest.raises(PermissionError, match="offline_preparation_only"):
        runner.execute_account(operation="identity", owner_approved=True)
    assert runner.ACCOUNT_EXECUTION_ENABLED is False


@pytest.mark.parametrize(
    "exit_code,classification",
    [(2, "saved_plan_review_required"), (0, "unexpected_plan_result"), (1, "read_or_plan_failed")],
)
def test_plan_exit_is_separate_from_six_resource_acceptance(runner, exit_code, classification):
    assert runner.classify("bootstrap_plan", captured(runner, code=exit_code)) == classification
