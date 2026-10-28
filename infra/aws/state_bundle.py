"""Prepare private local inputs only. No AWS, Terraform, credentials or cloud executor."""

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = {
    "account_id",
    "bucket_name",
    "bootstrap_principal_arn",
    "state_principal_arn",
    "permission_starts_at",
    "permission_expires_at",
}


def render(spec):
    if (
        not isinstance(spec, dict)
        or set(spec) != FIELDS
        or not all(isinstance(value, str) for value in spec.values())
    ):
        raise ValueError("invalid_bundle_fields")
    if not re.fullmatch(r"[0-9]{12}", spec["account_id"]):
        raise ValueError("invalid_account_binding")
    if not re.fullmatch(r"fata-[a-z0-9-]{3,45}-state", spec["bucket_name"]):
        raise ValueError("invalid_state_bucket_name")
    for field in ("bootstrap_principal_arn", "state_principal_arn"):
        if not re.fullmatch(
            rf"arn:aws:iam::{spec['account_id']}:(user|role)/[A-Za-z0-9+=,.@_/-]+",
            spec[field],
        ) or spec[field].lower().endswith("/future-f4-preflight"):
            raise ValueError("invalid_write_principal")
    try:
        if not all(
            re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", spec[field])
            for field in ("permission_starts_at", "permission_expires_at")
        ):
            raise ValueError
        start, end = (
            datetime.fromisoformat(spec[field])
            for field in ("permission_starts_at", "permission_expires_at")
        )
        if not timedelta(0) < end - start <= timedelta(hours=2):
            raise ValueError
    except ValueError:
        raise ValueError("invalid_permission_window") from None
    backend = {
        "bucket": spec["bucket_name"],
        "key": "ec2-demo/terraform.tfstate",
        "region": "us-east-1",
        "encrypt": True,
        "use_lockfile": True,
        "allowed_account_ids": [spec["account_id"]],
        "workspace_key_prefix": "env:",
        "max_retries": 1,
        "retry_mode": "standard",
    }
    return {
        "bootstrap.tfvars.json": json.dumps(spec, sort_keys=True, indent=2) + "\n",
        "deployment.tfbackend": "".join(
            f"{key} = {json.dumps(value)}\n" for key, value in backend.items()
        ),
        "READY": "offline-state-bundle-v1\n",
    }


def prepare(spec_path, name, workspace=ROOT):
    cache = (workspace / ".cache").resolve()
    source = spec_path.resolve()
    if not cache.is_relative_to(workspace.resolve()) or not source.is_relative_to(cache):
        raise ValueError("private_cache_path_required")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", name):
        raise ValueError("invalid_bundle_label")
    base = cache / "state-backend"
    destination = base / name
    if destination.resolve() != destination or base.resolve() != base:
        raise ValueError("private_bundle_link_rejected")
    with source.open("rb") as stream:
        raw = stream.read(8193)
    if len(raw) > 8192:
        raise ValueError("bundle_input_too_large")
    try:
        spec = json.loads(raw)
    except (
        ValueError,
        UnicodeError,
    ):
        raise ValueError("invalid_bundle_json") from None
    files = render(spec)
    if destination.exists():
        if {p.name for p in destination.iterdir()} != set(files) or any(
            not (destination / key).is_file()
            or (destination / key).is_symlink()
            or (destination / key).read_text(encoding="utf-8") != value
            for key, value in files.items()
        ):
            raise ValueError("existing_bundle_mismatch_or_incomplete")
        return "unchanged"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination.mkdir(mode=0o700)
    # READY is last. A crash leaves an incomplete, non-overwritable bundle.
    for key, value in files.items():
        path = destination / key
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            path.chmod(0o600)
            stream.write(value)
    return "created"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        outcome = prepare(args.spec, args.name)
    except (
        OSError,
        ValueError,
    ):
        print("private_state_bundle_rejected")
        return 1
    print("private_state_bundle_" + outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
