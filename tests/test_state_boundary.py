"""Independent structural checks + deliberately limited IAM-rule illustrations.

Not an AWS authorizer: no Access Analyzer/simulator, real credentials or API calls.
The matcher supports only this fixture's scalar conditions/action/resource rules.
"""

import ast
import copy
import importlib.util
import json
import subprocess
import sys
from fnmatch import fnmatchcase
from hashlib import sha256
from pathlib import Path
from threading import Thread

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "infra/aws/state-bootstrap/tests/fixtures/state-operator-boundary.synthetic.json"


def load(name):
    spec = importlib.util.spec_from_file_location("boundary_test_module", ROOT / "infra/aws" / name)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture
def policy():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def spec():
    return {
        "account_id": "000000000000",
        "bucket_name": "fata-synthetic-state",
        "bootstrap_principal_arn": "arn:aws:iam::000000000000:user/future-f4-human-admin",
        "state_principal_arn": "arn:aws:iam::000000000000:user/future-f4-state-operator",
        "permission_starts_at": "2030-01-01T00:00:00Z",
        "permission_expires_at": "2030-01-01T01:00:00Z",
    }


@pytest.fixture
def context(spec):
    return {
        "aws:PrincipalArn": spec["state_principal_arn"],
        "aws:PrincipalAccount": spec["account_id"],
        "aws:RequestedRegion": "us-east-1",
        "aws:SecureTransport": "true",
        "s3:prefix": "env:/",
    }


def sid(policy, name):
    return next(s for s in policy["Statement"] if s["Sid"] == name)


def illustrates_permission(
    policy, action, resource, context, *, identity=False, direct_resource=False
):
    """Limited rule example, not a general IAM evaluator or API result oracle."""

    def values(value):
        return value if isinstance(value, list) else [value]

    def condition(operator, key, expected):
        if operator == "BoolIfExists" and key not in context:
            return True
        equal = key in context and context[key] in values(expected)
        if operator in {"StringEquals", "ArnEquals", "Bool", "BoolIfExists"}:
            return equal
        if operator in {"StringNotEquals", "ArnNotEquals"}:
            return not equal
        pytest.fail("Unsupported condition in deliberately limited illustration")

    matched = []
    for statement in policy["Statement"]:
        action_key = "Action" if "Action" in statement else "NotAction"
        resource_key = "Resource" if "Resource" in statement else "NotResource"
        am = any(fnmatchcase(action.lower(), a.lower()) for a in values(statement[action_key]))
        rm = any(fnmatchcase(resource, r) for r in values(statement[resource_key]))
        if (
            (am if action_key == "Action" else not am)
            and (rm if resource_key == "Resource" else not rm)
            and all(
                condition(operator, key, value)
                for operator, conditions in statement.get("Condition", {}).items()
                for key, value in conditions.items()
            )
        ):
            matched.append(statement["Effect"])
    return "Deny" not in matched and (direct_resource or identity and "Allow" in matched)


def test_generated_fixture_is_exact_valid_persistent_and_deterministic(policy, spec):
    boundary = load("state_boundary.py")
    before = FIXTURE.read_bytes()
    assert boundary.validate(policy, spec) is policy
    assert boundary.POLICY_NAME == "future-f4-state-operator-boundary"
    assert len(json.dumps(policy, separators=(",", ":"))) == 3300
    assert len([s for s in policy["Statement"] if s["Effect"] == "Allow"]) == 4
    assert not any("Date" in op for s in policy["Statement"] for op in s.get("Condition", {}))
    spec["permission_expires_at"] = "2030-01-01T02:00:00Z"
    boundary.validate(policy, spec)
    assert FIXTURE.read_bytes() == before


@pytest.mark.parametrize(
    "action,key",
    [
        ("s3:GetObject", "ec2-demo/terraform.tfstate"),
        ("s3:PutObject", "ec2-demo/terraform.tfstate"),
        ("s3:GetObject", "ec2-demo/terraform.tfstate.tflock"),
        ("s3:PutObject", "ec2-demo/terraform.tfstate.tflock"),
        ("s3:DeleteObject", "ec2-demo/terraform.tfstate.tflock"),
    ],
)
def test_exact_state_and_lock_access_survives_all_deny_statements(policy, context, action, key):
    assert illustrates_permission(
        policy, action, "arn:aws:s3:::fata-synthetic-state/" + key, context, identity=True
    )
    assert not illustrates_permission(
        policy, action, "arn:aws:s3:::fata-synthetic-state/" + key, context
    )


@pytest.mark.parametrize("action", ["signin:AuthorizeOAuth2Access", "signin:CreateOAuth2Token"])
@pytest.mark.parametrize("client", ["localhost", "remote"])
def test_documented_login_scope_needs_no_s3_context_or_mfa_key(policy, action, client):
    resource = "arn:aws:signin:us-east-1:000000000000:oauth2/public-client/" + client
    assert illustrates_permission(policy, action, resource, {}, identity=True)
    assert not illustrates_permission(policy, action, resource, {})


@pytest.mark.parametrize(
    "action,resource",
    [
        ("s3:GetObject", "arn:aws:s3:::other-bucket/ec2-demo/terraform.tfstate"),
        ("s3:PutObject", "arn:aws:s3:::fata-synthetic-state/other.tfstate"),
        ("s3:GetObject", "arn:aws:s3:::fata-synthetic-state/env:/other/ec2-demo/terraform.tfstate"),
        ("s3:DeleteObject", "arn:aws:s3:::fata-synthetic-state/ec2-demo/terraform.tfstate"),
        ("s3:DeleteObject", "arn:aws:s3:::fata-synthetic-state/other.tflock"),
        ("s3:GetObjectVersion", "arn:aws:s3:::fata-synthetic-state/ec2-demo/terraform.tfstate"),
        ("s3:CreateBucket", "arn:aws:s3:::fata-synthetic-state"),
        ("s3:DeleteBucket", "arn:aws:s3:::fata-synthetic-state"),
        ("s3:PutBucketPolicy", "arn:aws:s3:::fata-synthetic-state"),
        ("iam:PutUserPolicy", "arn:aws:iam::000000000000:user/future-f4-state-operator"),
        (
            "iam:DeleteUserPermissionsBoundary",
            "arn:aws:iam::000000000000:user/future-f4-state-operator",
        ),
        ("iam:CreatePolicyVersion", "*"),
        ("iam:PassRole", "*"),
        ("ec2:RunInstances", "*"),
        ("sts:AssumeRole", "*"),
        ("sts:GetSessionToken", "*"),
        ("sts:GetFederationToken", "*"),
        (
            "s3:GetObject",
            "arn:aws:s3:us-east-1:000000000000:accesspoint/other/object/ec2-demo/terraform.tfstate",
        ),
        ("signin:CreateOAuth2Token", "arn:aws:signin:us-east-1:000000000000:other/resource"),
    ],
)
def test_explicit_deny_illustrations_resist_identity_or_direct_resource_grants(
    policy, context, action, resource
):
    assert not illustrates_permission(
        policy, action, resource, context, identity=True, direct_resource=True
    )


@pytest.mark.parametrize(
    "prefix", ["", "ec2-demo/", "ec2-demo/terraform.tfstate", "env:", "env:/other/", None]
)
def test_listing_is_not_generalized_to_unobserved_prefixes(policy, context, prefix):
    if prefix is None:
        context.pop("s3:prefix")
    else:
        context["s3:prefix"] = prefix
    assert not illustrates_permission(
        policy, "s3:ListBucket", "arn:aws:s3:::fata-synthetic-state", context, direct_resource=True
    )


def test_exact_discovery_only_and_other_bucket_denied(policy, context):
    assert illustrates_permission(
        policy, "s3:ListBucket", "arn:aws:s3:::fata-synthetic-state", context, identity=True
    )
    assert not illustrates_permission(
        policy, "s3:ListBucket", "arn:aws:s3:::other-bucket", context, direct_resource=True
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("aws:PrincipalArn", "arn:aws:iam::000000000000:user/other"),
        ("aws:PrincipalAccount", "111111111111"),
        ("aws:RequestedRegion", "us-west-2"),
        ("aws:SecureTransport", "false"),
        ("aws:PrincipalArn", None),
        ("aws:PrincipalAccount", None),
        ("aws:RequestedRegion", None),
        ("aws:SecureTransport", None),
    ],
)
def test_each_bad_or_missing_s3_condition_denies_even_direct_grant(policy, context, key, value):
    if value is None:
        context.pop(key)
    else:
        context[key] = value
    assert not illustrates_permission(
        policy,
        "s3:GetObject",
        "arn:aws:s3:::fata-synthetic-state/ec2-demo/terraform.tfstate",
        context,
        direct_resource=True,
    )


def test_implicit_boundary_denies_are_insufficient_and_remaining_direct_grant_limitation(
    policy, context
):
    only_allow = {**policy, "Statement": [s for s in policy["Statement"] if s["Effect"] == "Allow"]}
    other = "arn:aws:s3:::other-bucket/private"
    assert illustrates_permission(only_allow, "s3:GetObject", other, context, direct_resource=True)
    assert not illustrates_permission(policy, "s3:GetObject", other, context, direct_resource=True)
    # A direct grant WITHIN the ceiling can still bypass identity-policy implicit
    # denies, including an expired/absent identity grant. Trusted resource policies
    # remain essential; the persistent boundary does not invent an approval window.
    exact = "arn:aws:s3:::fata-synthetic-state/ec2-demo/terraform.tfstate"
    assert illustrates_permission(policy, "s3:GetObject", exact, context, direct_resource=True)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_auth",
        "auth_star",
        "narrow_broken_auth",
        "condition_on_auth",
        "object_star",
        "extra_action",
        "delete_state",
        "wrong_region",
        "wrong_principal",
        "wrong_account",
        "expiry",
        "mfa_if_exists",
        "prefix_star",
        "missing_deny",
        "deny_auth",
        "deny_exemption_star",
        "deny_resource_scoped",
        "extra_statement",
        "oversize",
        "unknown_field",
    ],
)
def test_independent_validator_rejects_permission_drift(policy, spec, fault):
    if fault == "missing_auth":
        sid(policy, "BrowserLogin")["Action"].pop()
    elif fault == "auth_star":
        sid(policy, "BrowserLogin")["Resource"] = "*"
    elif fault == "narrow_broken_auth":
        sid(policy, "BrowserLogin")["Resource"] = (
            "arn:aws:signin:us-east-1:000000000000:oauth2/public-client/localhost"
        )
    elif fault == "condition_on_auth":
        sid(policy, "BrowserLogin")["Condition"] = {"Bool": {"aws:MultiFactorAuthPresent": "true"}}
    elif fault == "object_star":
        sid(policy, "StateReadWrite")["Resource"] += "*"
    elif fault == "extra_action":
        sid(policy, "StateReadWrite")["Action"].append("iam:PutUserPolicy")
    elif fault == "delete_state":
        sid(policy, "StateReadWrite")["Action"].append("s3:DeleteObject")
    elif fault in {"wrong_region", "wrong_account"}:
        key = "aws:RequestedRegion" if fault == "wrong_region" else "aws:PrincipalAccount"
        sid(policy, "StateReadWrite")["Condition"]["StringEquals"][key] = "PRIVATE_CANARY"
    elif fault == "wrong_principal":
        sid(policy, "StateReadWrite")["Condition"]["ArnEquals"]["aws:PrincipalArn"] += "-other"
    elif fault == "expiry":
        sid(policy, "StateReadWrite")["Condition"]["DateLessThan"] = {
            "aws:CurrentTime": spec["permission_expires_at"]
        }
    elif fault == "mfa_if_exists":
        sid(policy, "StateReadWrite")["Condition"]["BoolIfExists"] = {
            "aws:MultiFactorAuthPresent": "true"
        }
    elif fault == "prefix_star":
        sid(policy, "WorkspaceDiscovery")["Condition"]["StringEquals"]["s3:prefix"] = ["*"]
    elif fault == "missing_deny":
        policy["Statement"].remove(sid(policy, "DenyStateDeletion"))
    elif fault == "deny_auth":
        sid(policy, "DenyOtherActions")["NotAction"].remove("signin:CreateOAuth2Token")
    elif fault == "deny_exemption_star":
        sid(policy, "DenyOtherActions")["NotAction"] = ["*"]
    elif fault == "deny_resource_scoped":
        sid(policy, "DenyOtherActions")["Resource"] = sid(policy, "StateReadWrite")["Resource"]
    elif fault == "extra_statement":
        policy["Statement"].append(copy.deepcopy(sid(policy, "BrowserLogin")))
    elif fault == "oversize":
        policy["extra"] = "x" * 6145
    else:
        sid(policy, "StateReadWrite")["NotPrincipal"] = "*"
    with pytest.raises(ValueError, match="boundary_policy_rejected") as error:
        load("state_boundary.py").validate(policy, spec)
    assert "CANARY" not in str(error.value)


@pytest.mark.parametrize(
    "arn",
    [
        "arn:aws:iam::000000000000:root",
        "arn:aws:iam::000000000000:role/operator",
        "arn:aws:iam::000000000000:user/future-f4-preflight",
        "arn:aws:iam::111111111111:user/future-f4-state-operator",
        "arn:aws:iam::000000000000:user/future-f4-human-admin",
    ],
)
def test_boundary_input_requires_actual_same_account_operator(spec, arn):
    spec["state_principal_arn"] = arn
    with pytest.raises(ValueError):
        load("state_boundary.py").validate_spec(spec)


@pytest.mark.parametrize(
    "error_type", [OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError]
)
def test_corrected_preparation_exception_handler_is_executable_and_private(
    monkeypatch, capsys, error_type
):
    helper = load("state_operator_prepare.py")
    tree = ast.parse((ROOT / "infra/aws/state_operator_prepare.py").read_text())
    assert any(
        isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Tuple)
        for node in ast.walk(tree)
    )
    monkeypatch.setattr(
        sys, "argv", ["state_operator_prepare.py", "--spec", "synthetic.json", "--verify-source"]
    )

    def fail(_):
        raise error_type("PRIVATE_CANARY")

    monkeypatch.setattr(helper, "private_json", fail)
    assert helper.main() == 1
    assert capsys.readouterr().out == "private_operator_preparation_rejected\n"


@pytest.mark.parametrize("missing_status,discovery_status", [(404, 200), (403, 200), (404, 403)])
def test_loopback_fixture_preserves_missing_state_and_discovery_error_boundaries(
    missing_status, discovery_status
):
    probe = load("fixtures/backend_probe.py")
    auth = probe.fixture("authentication_probe")
    server = probe.service(
        auth,
        empty=True,
        missing_status=missing_status,
        failure="discovery_denied" if discovery_status == 403 else None,
    )
    worker = Thread(target=server.serve_forever)
    worker.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        headers = {
            "Authorization": "AWS4-HMAC-SHA256 Credential=" + auth.ACCESS + "/synthetic",
            "X-Amz-Security-Token": auth.TOKEN,
        }
        with httpx.Client(trust_env=False, headers=headers, timeout=3) as client:
            listing = client.get(
                base + "/" + probe.BUCKET, params={"list-type": "2", "prefix": "env:/"}
            )
            assert listing.status_code == discovery_status
            target = base + "/" + probe.BUCKET + "/" + probe.KEY
            assert client.head(target).status_code == missing_status
            assert client.get(target).status_code == missing_status
            denied = client.get(base + "/" + probe.BUCKET, params={"list-type": "2", "prefix": ""})
            assert denied.status_code == 403
        assert server.listing_prefixes == ["env:/", "unapproved_prefix"]
        assert server.state_methods == ["HEAD", "GET"]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        assert not worker.is_alive()


def test_boundary_source_fingerprint_and_mode_separation(tmp_path, monkeypatch, policy, spec):
    helper = load("state_operator_prepare.py")
    monkeypatch.setattr(helper, "ROOT", tmp_path)
    monkeypatch.setattr(helper, "private", lambda path: path)
    work = tmp_path / ".cache/r5b-checkpoint-b/boundary-proof"
    work.mkdir(parents=True)
    manifest = {}
    for relative in helper.SOURCE_FILES:
        source, copied = tmp_path / relative, work / "source" / relative
        for path in (source, copied):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        manifest[relative] = sha256(source.read_bytes()).hexdigest()
    bundle = tmp_path / ".cache/state-backend/boundary-proof/bootstrap.tfvars.json"
    bundle.parent.mkdir(parents=True)
    bundle.write_text(json.dumps(spec))
    (work / "state_operator_boundary_policy.json").write_text(json.dumps(policy))
    (work / "source-manifest.json").write_text(json.dumps(manifest))
    (work / "READY").write_text("offline-state-operator-boundary-only-v1\n")
    assert helper.verify_source("boundary-proof", spec, boundary_only=True)["source_files"] == 5
    with pytest.raises(ValueError, match="readiness_mismatch"):
        helper.verify_source("boundary-proof", spec)
    boundary_source = work / "source/infra/aws/state-bootstrap/boundary.tf"
    boundary_source.write_text(boundary_source.read_text() + "\n# synthetic drift\n")
    with pytest.raises(ValueError, match="source_changed"):
        helper.verify_source("boundary-proof", spec, boundary_only=True)
