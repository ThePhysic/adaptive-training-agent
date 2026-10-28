"""Offline policy preparation/review only. Never AWS CLI, plan, apply or S3 backend."""

import argparse
import importlib.util
import json
import os
import re
import subprocess
from hashlib import sha256
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "module.state.aws_s3_bucket.this",
    "module.state.aws_s3_bucket_public_access_block.this",
    "module.state.aws_s3_bucket_ownership_controls.this",
    "module.state.aws_s3_bucket_versioning.this",
    "module.state.aws_s3_bucket_server_side_encryption_configuration.this",
    "module.state.aws_s3_bucket_policy.tls",
}
OUTPUTS = {
    "bootstrap_operator_policy": "jsonencode(local.bootstrap_policy)",
    "plan_operator_policy": "jsonencode(local.plan_policy)",
}
BOUNDARY_OUTPUTS = {
    "state_operator_boundary_policy": (
        "var.include_state_operator_boundary ? jsonencode(local.state_operator_boundary) : null"
    ),
}
SOURCE_FILES = (
    "infra/aws/state-bootstrap/main.tf",
    "infra/aws/state-bootstrap/authority.tf",
    "infra/aws/state-bootstrap/boundary.tf",
    "infra/aws/state-bootstrap/.terraform.lock.hcl",
    "infra/aws/modules/protected-bucket/main.tf",
)


def local_module(name):
    spec = importlib.util.spec_from_file_location(
        "private_" + name.replace("/", "_"),
        Path(__file__).with_name(name + ".py")
        if "/" not in name
        else Path(__file__).parent / (name + ".py"),
    )
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def private(path):
    for component in (path.absolute(), *path.absolute().parents):
        if component.is_symlink() or component.is_junction():
            raise ValueError("private_link_rejected")
        if component == ROOT:
            break
    path = path.resolve(strict=True)
    if not path.is_relative_to(ROOT / ".cache"):
        raise ValueError("private_cache_path_required")
    if os.name == "nt":
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(Path(__file__).with_name("private_state.ps1")),
                "-Mode",
                "Check",
                "-Path",
                str(path),
            ],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if result.returncode:
            raise ValueError("private_access_required")
    elif path.stat().st_mode & 0o077:
        raise ValueError("private_access_required")
    return path


def private_json(path, limit=8192):
    with private(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("private_input_too_large")
    return json.loads(raw.decode("utf-8-sig"))


def operator_spec(spec):
    local_module("state_bundle").render(spec)
    user = (
        rf"arn:aws:iam::{spec['account_id']}:user/(?:[A-Za-z0-9+=,.@_-]+/)*future-f4-state-operator"
    )
    if (
        not all(
            re.fullmatch(user, spec[key])
            for key in ("bootstrap_principal_arn", "state_principal_arn")
        )
        or spec["bootstrap_principal_arn"] != spec["state_principal_arn"]
    ):
        raise ValueError("selected_operator_user_required")
    return spec


def validate_policies(policies, spec):
    if set(policies) != set(OUTPUTS):
        raise ValueError("unexpected_policy_output")
    arn = "arn:aws:s3:::" + spec["bucket_name"]
    for name, policy in policies.items():
        statements = policy["Statement"]
        if policy["Version"] != "2012-10-17" or len(statements) != (
            1 if name == "bootstrap_operator_policy" else 3
        ):
            raise ValueError("invalid_policy_shape")
        for statement in statements:
            condition = statement["Condition"]
            if (
                statement["Effect"] != "Allow"
                or condition["ArnEquals"] != {"aws:PrincipalArn": spec["bootstrap_principal_arn"]}
                or condition["Bool"] != {"aws:SecureTransport": "true"}
                or condition["DateGreaterThanEquals"]
                != {"aws:CurrentTime": spec["permission_starts_at"]}
                or condition["DateLessThan"] != {"aws:CurrentTime": spec["permission_expires_at"]}
            ):
                raise ValueError("invalid_authority_binding")
            exact = {"aws:PrincipalAccount": spec["account_id"], "aws:RequestedRegion": "us-east-1"}
            if name == "plan_operator_policy" and statement is statements[0]:
                exact["s3:prefix"] = ["env:/"]
            if condition["StringEquals"] != exact or set(condition) != {
                "ArnEquals",
                "Bool",
                "DateGreaterThanEquals",
                "DateLessThan",
                "StringEquals",
            }:
                raise ValueError("invalid_region_account_prefix")
        if name == "bootstrap_operator_policy":
            statement = statements[0]
            if statement["Resource"] != arn or any(
                not action.startswith("s3:")
                or "*" in action
                or "Delete" in action
                or "Object" in action
                and action != "s3:GetBucketObjectLockConfiguration"
                for action in statement["Action"]
            ):
                raise ValueError("bootstrap_scope_expanded")
        elif [s["Resource"] for s in statements] != [
            arn,
            arn + "/ec2-demo/terraform.tfstate",
            arn + "/ec2-demo/terraform.tfstate.tflock",
        ] or [set(s["Action"]) for s in statements] != [
            {"s3:ListBucket"},
            {"s3:GetObject"},
            {"s3:GetObject", "s3:PutObject", "s3:DeleteObject"},
        ]:
            raise ValueError("first_plan_scope_expanded")
    return policies


def review_plan(plan, spec):
    if plan["terraform_version"] != "1.17.0":
        raise ValueError("pinned_plan_version_required")
    if {key: value["value"] for key, value in plan["variables"].items()} != spec:
        raise ValueError("plan_input_mismatch")
    changes = plan["resource_changes"]
    if (
        len(changes) != 6
        or {r["address"] for r in changes} != EXPECTED
        or any(r["mode"] != "managed" or r["change"]["actions"] != ["create"] for r in changes)
    ):
        raise ValueError("unexpected_plan_inventory")
    values = {r["address"]: r["change"]["after"] for r in changes}
    for resource in changes:
        if resource["address"] != "module.state.aws_s3_bucket.this":
            bucket = resource["change"]["after"].get("bucket")
            if bucket != spec["bucket_name"] and not (
                bucket is None and resource["change"].get("after_unknown", {}).get("bucket") is True
            ):
                raise ValueError("plan_bucket_mismatch")
    tls = next(
        r["change"] for r in changes if r["address"] == "module.state.aws_s3_bucket_policy.tls"
    )
    if tls["after"].get("policy") is None:
        if tls.get("after_unknown", {}).get("policy") is not True:
            raise ValueError("missing_tls_deny")
    else:
        document = json.loads(tls["after"]["policy"])
        statements = document["Statement"]
        arn = "arn:aws:s3:::" + spec["bucket_name"]
        if (
            len(statements) != 1
            or statements[0]["Effect"] != "Deny"
            or statements[0]["Principal"] != "*"
            or statements[0]["Action"] != "s3:*"
            or set(statements[0]["Resource"]) != {arn, arn + "/*"}
            or statements[0]["Condition"] != {"Bool": {"aws:SecureTransport": "false"}}
        ):
            raise ValueError("missing_tls_deny")
    bucket = values["module.state.aws_s3_bucket.this"]
    block = values["module.state.aws_s3_bucket_public_access_block.this"]
    if (
        bucket["bucket"] != spec["bucket_name"]
        or bucket["force_destroy"] is not False
        or not all(
            block[k] is True
            for k in (
                "block_public_acls",
                "block_public_policy",
                "ignore_public_acls",
                "restrict_public_buckets",
            )
        )
    ):
        raise ValueError("missing_bucket_protection")
    if (
        values["module.state.aws_s3_bucket_ownership_controls.this"]["rule"][0]["object_ownership"]
        != "BucketOwnerEnforced"
        or values["module.state.aws_s3_bucket_versioning.this"]["versioning_configuration"][0][
            "status"
        ]
        != "Enabled"
        or values["module.state.aws_s3_bucket_server_side_encryption_configuration.this"]["rule"][
            0
        ]["apply_server_side_encryption_by_default"][0]["sse_algorithm"]
        != "AES256"
    ):
        raise ValueError("missing_bucket_protection")
    policies = {key: json.loads(plan["planned_values"]["outputs"][key]["value"]) for key in OUTPUTS}
    validate_policies(policies, spec)
    return {
        "resources": 6,
        "actions": "create_only",
        "addresses": sorted(EXPECTED),
        "source_review_required": True,
    }


def validate_outputs(policies, spec, boundary_only=False):
    if boundary_only:
        if set(policies) != set(BOUNDARY_OUTPUTS):
            raise ValueError("unexpected_boundary_output")
        local_module("state_boundary").validate(policies["state_operator_boundary_policy"], spec)
    else:
        validate_policies(policies, spec)


def verify_source(name, spec, *, boundary_only=False):
    if not name or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", name):
        raise ValueError("private_label_required")
    work = private(ROOT / ".cache/r5b-checkpoint-b" / name)
    if (
        private(work / "READY").read_text(encoding="utf-8")
        != (
            "offline-state-operator-boundary-only-v1\n"
            if boundary_only
            else "offline-operator-proposals-only-v1\n"
        )
        or private_json(ROOT / ".cache/state-backend" / name / "bootstrap.tfvars.json") != spec
    ):
        raise ValueError("private_input_or_readiness_mismatch")
    outputs = BOUNDARY_OUTPUTS if boundary_only else OUTPUTS
    validate_outputs(
        {
            key: private_json(work / (key + ".json"), 32768 if boundary_only else 8192)
            for key in outputs
        },
        spec,
        boundary_only,
    )
    manifest = private_json(work / "source-manifest.json")
    if set(manifest) != set(SOURCE_FILES):
        raise ValueError("source_manifest_mismatch")
    for relative, expected in manifest.items():
        if (
            sha256((ROOT / relative).read_bytes()).hexdigest() != expected
            or sha256(private(work / "source" / relative).read_bytes()).hexdigest() != expected
        ):
            raise ValueError("source_changed")
    for directory, names in (
        ("state-bootstrap", {"main.tf", "authority.tf", "boundary.tf"}),
        ("modules/protected-bucket", {"main.tf"}),
    ):
        for base in (ROOT / "infra/aws" / directory, work / "source/infra/aws" / directory):
            if (
                {p.name for p in base.glob("*.tf")} != names
                or list(base.glob("*.tf.json"))
                or list(base.glob("*.auto.tfvars*"))
            ):
                raise ValueError("unexpected_source_file")
    return {"source_files": len(manifest), "source_binding": "unchanged"}


def prepare(spec_path, name, terraform, *, boundary_only=False):
    validator = local_module("state_boundary").validate_spec if boundary_only else operator_spec
    spec = validator(private_json(spec_path))
    outputs = BOUNDARY_OUTPUTS if boundary_only else OUTPUTS
    private(ROOT / ".cache/state-backend")
    base = private(ROOT / ".cache/r5b-checkpoint-b")
    bundle_helper = local_module("state_bundle")
    bundle_helper.prepare(spec_path, name)
    bundle = ROOT / ".cache/state-backend" / name
    for path in bundle.iterdir():
        private(path)
    work = base / name
    work.mkdir(mode=0o700)  # Existing/partial preparation is never overwritten.
    private(work)
    source = work / "source/infra/aws/state-bootstrap"
    module = work / "source/infra/aws/modules/protected-bucket"
    source.mkdir(parents=True)
    module.mkdir(parents=True)
    paths = SOURCE_FILES
    fingerprints = {}
    for relative in paths:
        content = (ROOT / relative).read_bytes()
        (work / "source" / relative).write_bytes(content)
        fingerprints[relative] = sha256(content).hexdigest()
    main = (source / "main.tf").read_text(encoding="utf-8")
    if re.findall(r'backend\s+"([^"]+)"', main) != ["local"] or any(
        re.search(
            r'\b(data|provisioner|import)\s+"', (work / "source" / path).read_text(encoding="utf-8")
        )
        for path in paths
        if path.endswith(".tf")
    ):
        raise ValueError("local_only_source_required")
    root_sources = "\n".join(
        (source / p.name).read_text(encoding="utf-8")
        for p in map(Path, paths)
        if p.suffix == ".tf" and p.name != "main.tf"
    )
    # The module has its own main.tf; the root main is already read above.
    root_sources = main + "\n" + root_sources
    for name, expression in outputs.items():
        if not re.search(
            r'output "'
            + name
            + r'"\s*\{\s*value\s*=\s*'
            + re.escape(expression)
            + r"\s*sensitive\s*=\s*true"
            + ("" if boundary_only else r"\s*\}"),
            root_sources,
        ):
            raise ValueError("reviewed_output_expression_changed")
    config = work / "offline.rc"
    config.write_text(
        "disable_checkpoint = true\nprovider_installation { filesystem_mirror { path = "
        + json.dumps((ROOT / "infra/aws/state-bootstrap/.terraform/providers").as_posix())
        + " } }\n",
        encoding="utf-8",
        newline="\n",
    )
    proxy_module = local_module("fixtures/sts_tunnel")
    policy = proxy_module.TunnelPolicy()  # Senderless; never install a connector.
    proxy = proxy_module.server(policy)
    worker = Thread(target=proxy.serve_forever)
    worker.start()
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.upper().startswith(("AWS_", "TF_")) and "PROXY" not in k.upper()
    }
    endpoint = f"http://127.0.0.1:{proxy.server_port}"
    env.update(
        CHECKPOINT_DISABLE="1",
        TF_IN_AUTOMATION="1",
        TF_CLI_CONFIG_FILE=str(config),
        AWS_CONFIG_FILE=str(work / "no-config"),
        AWS_SHARED_CREDENTIALS_FILE=str(work / "no-credentials"),
        AWS_EC2_METADATA_DISABLED="true",
        HTTP_PROXY=endpoint,
        HTTPS_PROXY=endpoint,
        ALL_PROXY=endpoint,
        NO_PROXY="",
        HOME=str(work),
        USERPROFILE=str(work),
    )
    runner = local_module("fixtures/backend_probe")
    try:
        code, out, _ = runner.run([str(terraform), "version", "-json"], source, env)
        if code or json.loads(out)["terraform_version"] != "1.17.0":
            raise ValueError("pinned_terraform_required")
        code, _, _ = runner.run(
            [str(terraform), "init", "-input=false", "-no-color", "-lockfile=readonly"], source, env
        )
        if code:
            raise ValueError("offline_init_failed")
        expression = (
            "jsonencode({"
            + ", ".join(key + " = " + value for key, value in outputs.items())
            + "})\n"
        )
        # -plan is never used; console only locks/reads the empty local backend.
        code, out, _ = runner.run(
            [
                str(terraform),
                "console",
                "-no-color",
                "-var-file=" + str(bundle / "bootstrap.tfvars.json"),
                *(["-var=include_state_operator_boundary=true"] if boundary_only else []),
            ],
            source,
            env,
            stdin=expression.encode(),
        )
        if code or len(out) > 65536 or policy.attempts:
            raise ValueError("offline_console_or_egress_failed")
        policies = {key: json.loads(value) for key, value in json.loads(json.loads(out)).items()}
        validate_outputs(policies, spec, boundary_only)
        for key, value in policies.items():
            (work / (key + ".json")).write_text(
                json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
        (work / "source-manifest.json").write_text(
            json.dumps(fingerprints, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        for path in work.rglob("*"):
            if path.is_relative_to(source / ".terraform/providers"):
                continue  # Public pinned plugin links use the existing local cache.
            private(path)
        (work / "READY").write_text(
            "offline-state-operator-boundary-only-v1\n"
            if boundary_only
            else "offline-operator-proposals-only-v1\n",
            encoding="utf-8",
            newline="\n",
        )
        return {
            "result": "offline_policy_proposals_prepared",
            "policy_outputs": sorted(outputs),
            "external_proxy_attempts": policy.attempts,
        }
    finally:
        proxy.shutdown()
        proxy.server_close()
        worker.join(timeout=3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--name")
    parser.add_argument("--terraform", type=Path, default=ROOT / ".tools/terraform/terraform.exe")
    parser.add_argument("--review-plan", type=Path)
    parser.add_argument("--verify-source", action="store_true")
    parser.add_argument(
        "--boundary-only",
        action="store_true",
        help="Only the persistent state-operator ceiling; no bootstrap grant output",
    )
    args = parser.parse_args()
    try:
        if args.boundary_only and args.review_plan:
            raise ValueError("boundary_mode_does_not_prepare_bootstrap_plan")
        validator = (
            local_module("state_boundary").validate_spec if args.boundary_only else operator_spec
        )
        if args.verify_source:
            result = verify_source(
                args.name,
                validator(private_json(args.spec)),
                boundary_only=args.boundary_only,
            )
        elif args.review_plan:
            verify_source(
                args.name,
                operator_spec(private_json(args.spec)),
            )
            result = review_plan(
                private_json(args.review_plan, 1048576),
                operator_spec(private_json(args.spec)),
            )
        else:
            if not args.name:
                raise ValueError("private_label_required")
            result = prepare(
                args.spec, args.name, args.terraform.resolve(), boundary_only=args.boundary_only
            )
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):  # fmt: skip
        print("private_operator_preparation_rejected")
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
