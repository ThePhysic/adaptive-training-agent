"""Restricted R2 identity-only configuration; no executor, credentials or live entrypoint."""

import json
import re

PROFILE = "future-f4-preflight"
REGION = "us-east-1"
DESTINATION = "sts.us-east-1.amazonaws.com:443"


def verify_source(section, expected):
    if set(section) != {"region", "login_session"} or section["region"] != REGION:
        raise ValueError("unapproved_profile_configuration")
    account, arn, user_id = (expected.get(k, "") for k in ("Account", "Arn", "UserId"))
    if (
        not re.fullmatch(r"[0-9]{12}", account)
        or not re.fullmatch(r"arn:aws:iam::" + account + r":user/[A-Za-z0-9+=,.@_/-]+", arn)
        or not re.fullmatch(r"[A-Za-z0-9:_-]+", user_id)
        or section["login_session"] != arn
    ):
        raise ValueError("approved_identity_binding_mismatch")


def environment(inherited, home, config, credentials, cache, rc, proxy):
    # Every source of AWS/SDK/TF/proxy settings is replaced; only OS basics survive.
    env = {
        k: v for k, v in inherited.items() if k in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
    }
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        AWS_PROFILE=PROFILE,
        AWS_DEFAULT_PROFILE=PROFILE,
        AWS_REGION=REGION,
        AWS_DEFAULT_REGION=REGION,
        AWS_CONFIG_FILE=str(config),
        AWS_SHARED_CREDENTIALS_FILE=str(credentials),
        AWS_LOGIN_CACHE_DIRECTORY=str(cache),
        AWS_EC2_METADATA_DISABLED="true",
        AWS_MAX_ATTEMPTS="1",
        AWS_RETRY_MODE="standard",
        AWS_IGNORE_CONFIGURED_ENDPOINT_URLS="true",
        AWS_STS_REGIONAL_ENDPOINTS="regional",
        HTTPS_PROXY=proxy,
        HTTP_PROXY=proxy,
        NO_PROXY="127.0.0.1,localhost,::1",
        CHECKPOINT_DISABLE="1",
        TF_IN_AUTOMATION="1",
        TF_CLI_CONFIG_FILE=str(rc),
    )
    return env


def configuration(config, credentials, expected, endpoint=None):
    # Private identifiers are written only into the caller's disposable directory.
    def q(value):
        return json.dumps(str(value).replace("\\", "/"))

    endpoint = endpoint or "https://sts.us-east-1.amazonaws.com"
    if endpoint != "https://sts.us-east-1.amazonaws.com":
        raise ValueError("unapproved_identity_endpoint")
    return f"""terraform {{
  required_version = "= 1.17.0"
  required_providers {{
    aws = {{ source = "hashicorp/aws", version = "6.70.0" }}
  }}
}}
provider "aws" {{
  region = "us-east-1"
  profile = "future-f4-preflight"
  shared_config_files = [{q(config)}]
  shared_credentials_files = [{q(credentials)}]
  skip_credentials_validation = true
  skip_requesting_account_id = true
  skip_region_validation = true
  skip_metadata_api_check = true
  max_retries = 1
  endpoints {{
    sts = "https://sts.us-east-1.amazonaws.com"
  }}
}}
data "aws_caller_identity" "approved" {{
  lifecycle {{
    postcondition {{
      condition = (
        self.account_id == {q(expected["Account"])} &&
        self.arn == {q(expected["Arn"])} &&
        self.user_id == {q(expected["UserId"])}
      )
      error_message = "identity_binding_mismatch"
    }}
  }}
}}
output "identity_matches" {{
  value = data.aws_caller_identity.approved.arn == {q(expected["Arn"])}
}}
"""
