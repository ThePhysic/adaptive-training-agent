"""Offline R2 guard tests; synthetic metadata only, never real AWS config/cache."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "infra/aws/fixtures/identity_contract.py"


def contract():
    spec = importlib.util.spec_from_file_location("identity_contract", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def expected():
    return {
        "Account": "000000000000",
        "Arn": "arn:aws:iam::000000000000:user/synthetic",
        "UserId": "SYNTHETIC",
    }


def test_binding_is_exact_iam_user(expected):
    contract().verify_source({"region": "us-east-1", "login_session": expected["Arn"]}, expected)


@pytest.mark.parametrize(
    "field,value",
    [
        ("region", "us-west-2"),
        ("login_session", "arn:aws:iam::000000000000:root"),
        ("credential_process", "synthetic"),
        ("source_profile", "default"),
        ("role_arn", "synthetic"),
        ("endpoint_url", "https://unapproved.invalid"),
    ],
)
def test_source_configuration_cannot_change_identity_or_route(expected, field, value):
    section = {"region": "us-east-1", "login_session": expected["Arn"], field: value}
    with pytest.raises(ValueError):
        contract().verify_source(section, expected)


def test_probe_has_one_data_source_and_no_backend_or_resources(tmp_path, expected):
    module = contract()
    raw = module.configuration(tmp_path / "config", tmp_path / "credentials", expected)
    assert raw.count('data "aws_caller_identity"') == 1
    assert 'resource "' not in raw and 'backend "' not in raw
    assert "skip_credentials_validation = true" in raw
    assert "skip_requesting_account_id = true" in raw
    assert "max_retries = 1" in raw and 'profile = "future-f4-preflight"' in raw
    assert "postcondition" in raw and "self.arn" in raw and "self.user_id" in raw
    with pytest.raises(ValueError):
        module.configuration(tmp_path, tmp_path, expected, "https://unapproved.invalid")


def test_parent_credentials_and_logs_cannot_survive(tmp_path):
    module = contract()
    poison = {
        k: "synthetic-canary"
        for k in (
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "AWS_PROFILE",
            "AWS_ROLE_ARN",
            "AWS_WEB_IDENTITY_TOKEN_FILE",
            "AWS_CONTAINER_CREDENTIALS_FULL_URI",
            "HTTPS_PROXY",
            "AWS_CA_BUNDLE",
            "TF_LOG",
            "TF_CLI_ARGS",
            "AWS_ENDPOINT_URL",
        )
    }
    env = module.environment(
        poison,
        tmp_path,
        tmp_path / "config",
        tmp_path / "empty",
        tmp_path / "cache",
        tmp_path / "rc",
        "http://127.0.0.1:1234",
    )
    assert "synthetic-canary" not in env.values()
    assert env["AWS_PROFILE"] == env["AWS_DEFAULT_PROFILE"] == module.PROFILE
    assert env["AWS_EC2_METADATA_DISABLED"] == "true" and env["AWS_MAX_ATTEMPTS"] == "1"
