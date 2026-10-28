"""Non-provisioning Terraform checks. No init, real plan, account or credentials.

Acquire the locked public plugin separately with init -backend=false. Tests are
required to mock every provider and use command=plan exclusively.
"""

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra/aws"
ROOTS = ("deployment", "state-bootstrap", "modules/protected-bucket")
ALLOWED_RESOURCES = {
    "aws_vpc",
    "aws_subnet",
    "aws_internet_gateway",
    "aws_route_table",
    "aws_route_table_association",
    "aws_security_group",
    "aws_vpc_security_group_egress_rule",
    "aws_ebs_volume",
    "aws_instance",
    "aws_volume_attachment",
    "aws_ecr_repository",
    "aws_iam_role",
    "aws_iam_instance_profile",
    "aws_iam_role_policy",
    "aws_ssm_document",
    "aws_s3_bucket",
    "aws_s3_bucket_public_access_block",
    "aws_s3_bucket_ownership_controls",
    "aws_s3_bucket_versioning",
    "aws_s3_bucket_server_side_encryption_configuration",
    "aws_s3_bucket_policy",
    "aws_s3_bucket_lifecycle_configuration",
}


def inspect_sources(directory=INFRA):
    files = list(directory.rglob("*.tf"))
    # Ignore downloaded modules/plugins; all module sources here are local.
    files = [p for p in files if ".terraform" not in p.parts]
    resources = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        kinds = re.findall(r'resource\s+"([^"]+)"', source)
        if not set(kinds) <= ALLOWED_RESOURCES:
            raise ValueError("unexpected_resource")
        resources.extend(kinds)
        if re.search(r'\b(data|provisioner)\s+"', source):
            raise ValueError("external_data_or_provisioner")
        if re.search(r'variable\s+"[^"\n]*(password|secret|token|credential|access_key)', source):
            raise ValueError("sensitive_terraform_input")
        if re.search(r"\b(access_key|secret_key|profile|endpoints)\s*[={]", source):
            raise ValueError("credential_or_endpoint_override")
        for module in re.findall(r'\bsource\s*=\s*"([^"]+)"', source):
            if module != "hashicorp/aws" and not module.startswith("../"):
                raise ValueError("unapproved_module")
    tests = list(directory.rglob("*.tftest.hcl"))
    for path in tests:
        text = path.read_text()
        if 'mock_provider "aws"' not in text or re.search(r'^provider\s+"', text, re.M):
            raise ValueError("nonmocked_test")
        if len(re.findall(r'\brun\s+"', text)) != len(re.findall(r"command\s*=\s*plan\b", text)):
            raise ValueError("nonplan_test")
    if not tests:
        raise ValueError("missing_tests")
    return {"source_files": len(files), "resource_blocks": len(resources), "test_files": len(tests)}


def clean_env():
    # Never inspect or print credential values. Provider plugin Configure is not
    # called by validate; terraform test is sealed to mock providers above.
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.upper().startswith(("AWS_", "TF_VAR_", "TF_LOG", "TF_CLI_ARGS"))
    }
    env.update(
        {
            "CHECKPOINT_DISABLE": "1",
            "TF_IN_AUTOMATION": "1",
            "AWS_EC2_METADATA_DISABLED": "true",
            "AWS_SHARED_CREDENTIALS_FILE": str(ROOT / ".cache/f4-02/no-credentials"),
            "AWS_CONFIG_FILE": str(ROOT / ".cache/f4-02/no-config"),
        }
    )
    config = ROOT / ".cache/f4-02/offline.rc"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("disable_checkpoint = true\n")
    env["TF_CLI_CONFIG_FILE"] = str(config)
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--terraform", type=Path, required=True)
    args = parser.parse_args()
    executable = str(args.terraform.resolve())
    report = {
        "evidence": "offline_schema_and_mock_only",
        "sources": inspect_sources(),
        "commands": [],
    }
    commands = [[executable, "fmt", "-check", "-recursive", "infra/aws"]]
    for directory in ROOTS:
        commands += [
            [executable, "-chdir=infra/aws/" + directory, "validate", "-json"],
            [executable, "-chdir=infra/aws/" + directory, "test", "-json", "-no-color"],
        ]
    destination = ROOT / ".cache/f4-02"
    destination.mkdir(parents=True, exist_ok=True)
    for index, command in enumerate(commands):
        start = time.perf_counter()
        result = subprocess.run(
            command, cwd=ROOT, env=clean_env(), capture_output=True, timeout=180
        )
        (destination / f"command-{index}.jsonl").write_bytes(result.stdout)
        row = {
            "command": command[1:],
            "exit_code": result.returncode,
            "seconds": round(time.perf_counter() - start, 3),
        }
        if "test" in command:
            for line in result.stdout.decode().splitlines():
                value = json.loads(line)
                if "test_summary" in value:
                    row["tests"] = value["test_summary"]
        report["commands"].append(row)
        if result.returncode:
            print(result.stdout.decode())
            print(result.stderr.decode())
            raise SystemExit(1)
    (destination / "checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
