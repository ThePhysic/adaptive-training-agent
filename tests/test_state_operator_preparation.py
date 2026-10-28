"""Structural/private-file guards, not AWS IAM evaluation or cloud-plan evidence."""

import copy
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def helper():
    spec = importlib.util.spec_from_file_location(
        "operator_prepare", ROOT / "infra/aws/state_operator_prepare.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def spec():
    return {
        "account_id": "000000000000",
        "bucket_name": "fata-synthetic-state",
        "bootstrap_principal_arn": "arn:aws:iam::000000000000:user/future-f4-state-operator",
        "state_principal_arn": "arn:aws:iam::000000000000:user/future-f4-state-operator",
        "permission_starts_at": "2030-01-01T00:00:00Z",
        "permission_expires_at": "2030-01-01T01:00:00Z",
    }


@pytest.fixture
def policies(spec):
    arn = "arn:aws:s3:::" + spec["bucket_name"]
    conditions = {
        "ArnEquals": {"aws:PrincipalArn": spec["bootstrap_principal_arn"]},
        "Bool": {"aws:SecureTransport": "true"},
        "DateGreaterThanEquals": {"aws:CurrentTime": spec["permission_starts_at"]},
        "DateLessThan": {"aws:CurrentTime": spec["permission_expires_at"]},
        "StringEquals": {
            "aws:PrincipalAccount": spec["account_id"],
            "aws:RequestedRegion": "us-east-1",
        },
    }

    def statement(actions, resource):
        return {
            "Effect": "Allow",
            "Action": actions,
            "Resource": resource,
            "Condition": copy.deepcopy(conditions),
        }

    listing = statement(["s3:ListBucket"], arn)
    listing["Condition"]["StringEquals"]["s3:prefix"] = ["env:/"]
    return {
        "bootstrap_operator_policy": {
            "Version": "2012-10-17",
            "Statement": [statement(["s3:CreateBucket"], arn)],
        },
        "plan_operator_policy": {
            "Version": "2012-10-17",
            "Statement": [
                listing,
                statement(["s3:GetObject"], arn + "/ec2-demo/terraform.tfstate"),
                statement(
                    ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
                    arn + "/ec2-demo/terraform.tfstate.tflock",
                ),
            ],
        },
    }


@pytest.mark.parametrize(
    "principal", ["user/future-f4-preflight", "root", "role/future-f4-state-operator", "user/other"]
)
def test_only_selected_existing_operator_user_is_accepted(helper, spec, principal):
    spec["bootstrap_principal_arn"] = spec["state_principal_arn"] = (
        "arn:aws:iam::000000000000:" + principal
    )
    with pytest.raises(ValueError):
        helper.operator_spec(spec)


def test_operator_path_and_exact_two_hour_window_are_accepted(helper, spec):
    spec["bootstrap_principal_arn"] = spec["state_principal_arn"] = (
        "arn:aws:iam::000000000000:user/path/future-f4-state-operator"
    )
    spec["permission_expires_at"] = "2030-01-01T02:00:00Z"
    assert helper.operator_spec(spec) == spec
    spec["permission_expires_at"] = "2030-01-01T02:00:01Z"
    with pytest.raises(ValueError):
        helper.operator_spec(spec)


@pytest.mark.parametrize(
    "fault",
    [
        "principal",
        "account",
        "region",
        "tls",
        "window",
        "prefix",
        "state_write",
        "wildcard",
        "object_access",
        "broader_writer",
    ],
)
def test_expanded_or_unbound_proposals_are_rejected(helper, spec, policies, fault):
    assert helper.validate_policies(policies, spec) == policies
    bootstrap = policies["bootstrap_operator_policy"]["Statement"][0]
    plan = policies["plan_operator_policy"]["Statement"]
    if fault == "principal":
        bootstrap["Condition"]["ArnEquals"]["aws:PrincipalArn"] = "private-principal-canary"
    elif fault == "account":
        bootstrap["Condition"]["StringEquals"]["aws:PrincipalAccount"] = "111111111111"
    elif fault == "region":
        bootstrap["Condition"]["StringEquals"]["aws:RequestedRegion"] = "us-west-2"
    elif fault == "tls":
        bootstrap["Condition"]["Bool"]["aws:SecureTransport"] = "false"
    elif fault == "window":
        bootstrap["Condition"].pop("DateLessThan")
    elif fault == "prefix":
        plan[0]["Condition"]["StringEquals"]["s3:prefix"] = ["*"]
    elif fault == "state_write":
        plan[1]["Action"].append("s3:PutObject")
    elif fault == "wildcard":
        bootstrap["Action"] = ["s3:*"]
    elif fault == "object_access":
        bootstrap["Action"].append("s3:GetObject")
    elif fault == "broader_writer":
        policies["state_operator_policy"] = policies["plan_operator_policy"]
    with pytest.raises((ValueError, KeyError)) as error:
        helper.validate_policies(policies, spec)
    assert "canary" not in str(error.value)


@pytest.fixture
def plan(helper, spec, policies):
    values = {
        "aws_s3_bucket.this": {"bucket": spec["bucket_name"], "force_destroy": False},
        "aws_s3_bucket_public_access_block.this": {
            key: True
            for key in (
                "block_public_acls",
                "block_public_policy",
                "ignore_public_acls",
                "restrict_public_buckets",
            )
        },
        "aws_s3_bucket_ownership_controls.this": {
            "rule": [{"object_ownership": "BucketOwnerEnforced"}]
        },
        "aws_s3_bucket_versioning.this": {"versioning_configuration": [{"status": "Enabled"}]},
        "aws_s3_bucket_server_side_encryption_configuration.this": {
            "rule": [{"apply_server_side_encryption_by_default": [{"sse_algorithm": "AES256"}]}]
        },
        "aws_s3_bucket_policy.tls": {},
    }
    return {
        "terraform_version": "1.17.0",
        "variables": {key: {"value": value} for key, value in spec.items()},
        "resource_changes": [
            {
                "address": address,
                "mode": "managed",
                "change": {
                    "actions": ["create"],
                    "after": values[address.removeprefix("module.state.")],
                    "after_unknown": {"bucket": True, "policy": True},
                },
            }
            for address in sorted(helper.EXPECTED)
        ],
        "planned_values": {
            "outputs": {key: {"value": json.dumps(value)} for key, value in policies.items()}
        },
    }


def test_six_resource_review_is_sanitized_and_not_iam_evidence(helper, spec, plan):
    result = helper.review_plan(plan, spec)
    assert result["resources"] == 6 and result["source_review_required"]
    assert spec["bucket_name"] not in json.dumps(result) and spec["account_id"] not in json.dumps(
        result
    )


@pytest.mark.parametrize(
    "fault",
    [
        "extra",
        "missing",
        "delete",
        "update",
        "wrong_bucket",
        "unprotected",
        "versioning",
        "input",
        "provider_version",
    ],
)
def test_saved_plan_guard_rejects_unexpected_changes(helper, spec, plan, fault):
    if fault == "extra":
        plan["resource_changes"].append(plan["resource_changes"][0])
    elif fault == "missing":
        plan["resource_changes"].pop()
    elif fault in ("delete", "update"):
        plan["resource_changes"][0]["change"]["actions"] = [fault]
    elif fault == "input":
        plan["variables"]["permission_expires_at"]["value"] = "2030-01-02T00:00:00Z"
    elif fault == "provider_version":
        plan["terraform_version"] = "0.1.0"
    else:
        key = {
            "wrong_bucket": "aws_s3_bucket.this",
            "unprotected": "aws_s3_bucket_public_access_block.this",
            "versioning": "aws_s3_bucket_versioning.this",
        }[fault]
        after = next(
            r["change"]["after"]
            for r in plan["resource_changes"]
            if r["address"] == "module.state." + key
        )
        if fault == "wrong_bucket":
            after["bucket"] = "private-bucket-canary"
        elif fault == "unprotected":
            after["block_public_acls"] = False
        else:
            after["versioning_configuration"][0]["status"] = "Suspended"
    with pytest.raises(ValueError) as error:
        helper.review_plan(plan, spec)
    assert "canary" not in str(error.value)


def test_private_access_checks_owner_files_and_rejects_broad_read(helper, tmp_path):
    directory = tmp_path / "private"
    if os.name == "nt":
        script = ROOT / "infra/aws/private_state.ps1"
        # Path passed via environment, never interpolate private values into code.
        env = {
            **os.environ,
            "FATA_PRIVATE_TEST_PATH": str(directory),
            "FATA_PRIVATE_TEST_SCRIPT": str(script),
        }
        code = """
. $env:FATA_PRIVATE_TEST_SCRIPT
$d=New-FataPrivateDirectory $env:FATA_PRIVATE_TEST_PATH
Assert-FataPrivateAccess $d -DirectoryRoot
$acl=Get-Acl -LiteralPath $d
$rule=New-Object Security.AccessControl.FileSystemAccessRule(
    (New-Object Security.Principal.SecurityIdentifier('S-1-1-0')),
    'ReadAndExecute', 'Allow')
$acl.AddAccessRule($rule)
(New-Object IO.DirectoryInfo($d)).SetAccessControl($acl)
try { Assert-FataPrivateAccess $d; exit 2 }
catch { if($_.Exception.Message -ne 'private_access_too_broad'){exit 3} }
Write-Output 'private_acl_positive_and_negative_verified'
"""
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", code],
            env=env,
            capture_output=True,
            timeout=15,
            check=False,
        )
        assert (
            result.returncode == 0
            and "private_acl_positive_and_negative_verified" in result.stdout.decode()
        )
    else:
        directory.mkdir(mode=0o700)
        assert helper.private(directory) == directory.resolve()
        directory.chmod(0o755)
        with pytest.raises(ValueError, match="private_access"):
            helper.private(directory)


def test_private_input_size_and_cache_boundary(helper, tmp_path, monkeypatch):
    source = tmp_path / "bounded.json"
    source.write_bytes(b"x" * 8193)
    monkeypatch.setattr(helper, "private", lambda path: path)
    with pytest.raises(ValueError, match="too_large"):
        helper.private_json(source)
