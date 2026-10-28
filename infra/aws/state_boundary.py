"""Independent structural validation, not policy generation or AWS IAM evaluation.

Terraform is the single generator. Deliberate independent security assertions
reject additional actions/resources/conditions rather than trusting its output.
"""

import importlib.util
import json
import re
from pathlib import Path

POLICY_NAME = "future-f4-state-operator-boundary"
OUTPUT = "state_operator_boundary_policy"
LOGIN_ACTIONS = ["signin:AuthorizeOAuth2Access", "signin:CreateOAuth2Token"]
LOGIN_RESOURCE = "arn:aws:signin:*:*:oauth2/public-client/*"
OBJECT_ACTIONS = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
S3_ACTIONS = ["s3:ListBucket", *OBJECT_ACTIONS]


def validate_spec(spec):
    module = importlib.util.spec_from_file_location(
        "boundary_bundle", Path(__file__).with_name("state_bundle.py")
    )
    bundle = importlib.util.module_from_spec(module)
    module.loader.exec_module(bundle)
    bundle.render(spec)  # Existing account, bucket, principal and temporary-window checks.
    if not re.fullmatch(
        rf"arn:aws:iam::{spec['account_id']}:user/(?:[A-Za-z0-9+=,.@_-]+/)*future-f4-state-operator",
        spec["state_principal_arn"],
    ):
        raise ValueError("boundary_state_operator_required")
    # Bootstrap principal may be the human administrator. It receives no boundary
    # or permission from this generator; legacy equal-principal mode is unchanged.
    return spec


def validate(policy, spec):
    validate_spec(spec)
    try:
        compact = json.dumps(policy, separators=(",", ":"), ensure_ascii=True)
        if len(compact) > 6144:
            raise ValueError
        if set(policy) != {"Version", "Statement"} or policy["Version"] != "2012-10-17":
            raise ValueError
        bucket = "arn:aws:s3:::" + spec["bucket_name"]
        state = bucket + "/ec2-demo/terraform.tfstate"
        lock = state + ".tflock"
        conditions = {
            "ArnEquals": {"aws:PrincipalArn": spec["state_principal_arn"]},
            "StringEquals": {
                "aws:PrincipalAccount": spec["account_id"],
                "aws:RequestedRegion": "us-east-1",
            },
            "Bool": {"aws:SecureTransport": "true"},
        }
        listing = {
            **conditions,
            "StringEquals": {**conditions["StringEquals"], "s3:prefix": ["env:/"]},
        }
        # SID -> exact permitted statement fields. NotAction/NotResource are
        # deny-only; the only resource wildcard Allow is documented OAuth scope.
        rules = {
            "BrowserLogin": ("Allow", "Action", LOGIN_ACTIONS, "Resource", LOGIN_RESOURCE, None),
            "WorkspaceDiscovery": (
                "Allow",
                "Action",
                ["s3:ListBucket"],
                "Resource",
                bucket,
                listing,
            ),
            "StateReadWrite": (
                "Allow",
                "Action",
                OBJECT_ACTIONS[:2],
                "Resource",
                state,
                conditions,
            ),
            "LockLifecycle": ("Allow", "Action", OBJECT_ACTIONS, "Resource", lock, conditions),
            "DenyOtherActions": (
                "Deny",
                "NotAction",
                LOGIN_ACTIONS + S3_ACTIONS,
                "Resource",
                "*",
                None,
            ),
            "DenyOtherLoginResources": (
                "Deny",
                "Action",
                LOGIN_ACTIONS,
                "NotResource",
                LOGIN_RESOURCE,
                None,
            ),
            "DenyOtherBuckets": ("Deny", "Action", ["s3:ListBucket"], "NotResource", bucket, None),
            "DenyOtherObjectKeys": (
                "Deny",
                "Action",
                OBJECT_ACTIONS,
                "NotResource",
                [state, lock],
                None,
            ),
            "DenyStateDeletion": ("Deny", "Action", ["s3:DeleteObject"], "Resource", state, None),
            "DenyOtherPrefixes": (
                "Deny",
                "Action",
                ["s3:ListBucket"],
                "Resource",
                bucket,
                {"StringNotEquals": {"s3:prefix": ["env:/"]}},
            ),
            "DenyWrongPrincipal": (
                "Deny",
                "Action",
                S3_ACTIONS,
                "Resource",
                "*",
                {"ArnNotEquals": {"aws:PrincipalArn": spec["state_principal_arn"]}},
            ),
            "DenyWrongAccount": (
                "Deny",
                "Action",
                S3_ACTIONS,
                "Resource",
                "*",
                {"StringNotEquals": {"aws:PrincipalAccount": spec["account_id"]}},
            ),
            "DenyWrongRegion": (
                "Deny",
                "Action",
                S3_ACTIONS,
                "Resource",
                "*",
                {"StringNotEquals": {"aws:RequestedRegion": "us-east-1"}},
            ),
            "DenyInsecureOrMissingTransport": (
                "Deny",
                "Action",
                S3_ACTIONS,
                "Resource",
                "*",
                {"BoolIfExists": {"aws:SecureTransport": "false"}},
            ),
        }
        statements = policy["Statement"]
        if len(statements) != len(rules) or {s["Sid"] for s in statements} != set(rules):
            raise ValueError
        for statement in statements:
            effect, action_key, actions, resource_key, resources, condition = rules[
                statement["Sid"]
            ]
            expected = {
                "Sid": statement["Sid"],
                "Effect": effect,
                action_key: actions,
                resource_key: resources,
            }
            if condition is not None:
                expected["Condition"] = condition
            if statement != expected:
                raise ValueError
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        raise ValueError("boundary_policy_rejected") from None
    return policy
