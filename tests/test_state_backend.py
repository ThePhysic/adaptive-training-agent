"""Offline private-input/loopback boundary tests, never AWS or real credential files."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(relative):
    spec = importlib.util.spec_from_file_location("state_fixture", ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def spec():
    return {
        "account_id": "000000000000",
        "bucket_name": "fata-synthetic-state",
        "bootstrap_principal_arn": "arn:aws:iam::000000000000:role/synthetic-bootstrap",
        "state_principal_arn": "arn:aws:iam::000000000000:role/synthetic-state",
        "permission_starts_at": "2030-01-01T00:00:00Z",
        "permission_expires_at": "2030-01-01T01:00:00Z",
    }


def test_private_bundle_roundtrip_idempotency_and_no_logging(tmp_path, spec, capsys, caplog):
    helper = module("infra/aws/state_bundle.py")
    cache = tmp_path / ".cache"
    cache.mkdir()
    source = cache / "spec.json"
    source.write_text(json.dumps(spec))
    assert helper.prepare(source, "review", tmp_path) == "created"
    target = cache / "state-backend/review"
    assert json.loads((target / "bootstrap.tfvars.json").read_text()) == spec
    backend = (target / "deployment.tfbackend").read_text()
    assert 'key = "ec2-demo/terraform.tfstate"' in backend
    assert "use_lockfile = true" in backend and "dynamodb" not in backend
    assert helper.prepare(source, "review", tmp_path) == "unchanged"
    spec["bucket_name"] = "fata-different-state"
    source.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="mismatch_or_incomplete"):
        helper.prepare(source, "review", tmp_path)
    assert (
        json.loads((target / "bootstrap.tfvars.json").read_text())["bucket_name"]
        == "fata-synthetic-state"
    )
    assert not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize(
    "field,value",
    [
        ("account_id", "private-account-canary"),
        ("bucket_name", "invalid.Private"),
        ("state_principal_arn", "arn:aws:iam::000000000000:root"),
        ("state_principal_arn", "arn:aws:iam::111111111111:role/wrong"),
        ("state_principal_arn", "arn:aws:iam::000000000000:user/future-f4-preflight"),
        ("state_principal_arn", "arn:aws:iam::000000000000:user/FUTURE-F4-PREFLIGHT"),
        ("bootstrap_principal_arn", "arn:aws:iam::000000000000:user/path/future-f4-preflight"),
        ("permission_expires_at", "2030-01-01T02:00:01Z"),
        ("permission_expires_at", "2030-01-01T00:00:00Z"),
        ("permission_expires_at", "2030-01-01T00:00:00+00:00"),
        ("permission_expires_at", "private-canary"),
        ("permission_starts_at", "invalidZ"),
        ("permission_expires_at", 42),
    ],
)
def test_bundle_rejects_wrong_identity_unbounded_authority_and_invalid_fields(spec, field, value):
    helper = module("infra/aws/state_bundle.py")
    spec[field] = value
    with pytest.raises(ValueError) as error:
        helper.render(spec)
    assert "canary" not in str(error.value)


def test_unknown_fields_and_exact_two_hour_boundary(spec):
    helper = module("infra/aws/state_bundle.py")
    spec["permission_expires_at"] = "2030-01-01T02:00:00Z"
    assert "READY" in helper.render(spec)
    with pytest.raises(ValueError, match="fields"):
        helper.render({**spec, "credential": "synthetic-secret-canary"})


@pytest.mark.parametrize("label", ["../tracked", "C:/outside", "private space", "", "x" * 41])
def test_bundle_label_cannot_escape_private_cache(tmp_path, spec, label):
    helper = module("infra/aws/state_bundle.py")
    source = tmp_path / ".cache/spec.json"
    with pytest.raises(ValueError, match="label"):
        helper.prepare(source, label, tmp_path)
    assert not (tmp_path / ".cache/state-backend").exists()


def test_public_source_and_incomplete_or_extra_bundle_cannot_be_reused(tmp_path, spec):
    helper = module("infra/aws/state_bundle.py")
    public = tmp_path / "public.json"
    public.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="private_cache"):
        helper.prepare(public, "review", tmp_path)
    cache = tmp_path / ".cache"
    cache.mkdir()
    private = cache / "spec.json"
    private.write_text(json.dumps(spec))
    target = cache / "state-backend/review"
    target.mkdir(parents=True)
    (target / "bootstrap.tfvars.json").write_text("partial")
    with pytest.raises(ValueError, match="incomplete"):
        helper.prepare(private, "review", tmp_path)
    assert (target / "bootstrap.tfvars.json").read_text() == "partial"


def test_oversized_private_spec_is_bounded(tmp_path):
    helper = module("infra/aws/state_bundle.py")
    source = tmp_path / ".cache/spec.json"
    source.parent.mkdir()
    source.write_bytes(b"x" * 8193)
    with pytest.raises(ValueError, match="too_large"):
        helper.prepare(source, "review", tmp_path)


@pytest.mark.parametrize(
    "url",
    [
        "https://s3.us-east-1.amazonaws.com",
        "http://127.0.0.1:1/private",
        "http://localhost:1",
        "http://synthetic-credential@127.0.0.1:1",
        "http://127.0.0.1:1?x=y",
    ],
)
def test_native_fixture_refuses_external_or_modified_endpoints(url):
    probe = module("infra/aws/fixtures/backend_probe.py")
    with pytest.raises(ValueError):
        probe.local_url(url)
    assert probe.local_url("http://127.0.0.1:4321") == "http://127.0.0.1:4321"


def test_private_aws_and_terraform_artifacts_are_ignored():
    paths = [
        ".aws/config",
        ".aws/login/cache/synthetic.json",
        "private.tfstate",
        "private.tfstate.backup",
        "private.tfplan",
        "private.tfplan.json",
        "private.tfvars.json",
        "private.tfbackend",
        ".cache/state-backend/review/READY",
        "infra/aws/deployment/.terraform/terraform.tfstate",
        "AGENTS.md",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"],
        cwd=ROOT,
        input=("\0".join(paths) + "\0").encode(),
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0 and set(result.stdout.decode().strip("\0").split("\0")) == set(
        paths
    )
