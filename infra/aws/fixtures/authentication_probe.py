"""Offline-only credential-process probe. Never invokes AWS CLI or real credentials.

Native entrypoint requires a Linux network-none namespace, cached Terraform/provider
mounts, and disposable /work. It configures only a loopback STS fake, no resources
or remote backend. JSON stdout contains classified observations, never credentials.
"""

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs

PROFILE = "fixture-process"
ACCOUNT = "000000000000"
ARN = f"arn:aws:iam::{ACCOUNT}:user/synthetic-fixture"
ACCESS = "ASIASYNTHETIC00000001"
SECRET = "synthetic-secret-canary".ljust(40, "x")
TOKEN = "synthetic-session-canary"


def environment(root, inherited):
    """Test-only allowlist: no real HOME/config/cache/credential chain survives."""
    env = {k: v for k, v in inherited.items() if k in ("PATH", "SYSTEMROOT", "WINDIR")}
    env.update(
        HOME=str(root),
        USERPROFILE=str(root),
        AWS_PROFILE=PROFILE,
        AWS_DEFAULT_PROFILE=PROFILE,
        AWS_REGION="us-east-1",
        AWS_DEFAULT_REGION="us-east-1",
        AWS_CONFIG_FILE=str(root / "config"),
        AWS_SHARED_CREDENTIALS_FILE=str(root / "credentials"),
        AWS_LOGIN_CACHE_DIRECTORY=str(root / "no-login-cache"),
        AWS_EC2_METADATA_DISABLED="true",
        AWS_MAX_ATTEMPTS="1",
        AWS_RETRY_MODE="standard",
        TF_IN_AUTOMATION="1",
        CHECKPOINT_DISABLE="1",
    )
    return env


def synthetic_reply():
    return {
        "Version": 1,
        "AccessKeyId": ACCESS,
        "SecretAccessKey": SECRET,
        "SessionToken": TOKEN,
        "Expiration": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
    }


def process(mode, counter):
    """A synthetic executable stand-in, not an AWS CLI/credential-export wrapper."""
    with counter.open("a", encoding="utf-8") as output:
        output.write("invoked\n")
    if mode == "failed":
        print("synthetic_process_unavailable", file=sys.stderr)
        return 1
    if mode == "malformed":
        print("not-json")
    else:
        reply = synthetic_reply()
        if mode == "unsupported_version":
            reply["Version"] = 2
        elif mode != "valid":
            raise RuntimeError("unsupported_synthetic_mode")
        print(json.dumps(reply))
    return 0


def run(command, cwd, env, timeout=60):
    # Native fixture only: owned process group includes provider/helper children.
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    ) as child:
        try:
            out, err = child.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
            raise RuntimeError("offline_auth_timeout") from None
        return child.returncode, out, err


def native():
    if sys.platform != "linux" or set(os.listdir("/sys/class/net")) != {"lo"}:
        raise SystemExit("Requires disposable Linux Docker --network none")
    if not Path("/mirror/registry.terraform.io/hashicorp/aws").is_dir():
        raise SystemExit("Requires existing locked provider mirror")
    observations = []
    with tempfile.TemporaryDirectory(prefix="auth-", dir="/work") as temporary:
        root = Path(temporary)
        terraform = root / "terraform"
        shutil.copyfile("/tool/terraform", terraform)
        terraform.chmod(0o700)
        rc = root / "mirror.rc"
        rc.write_text(
            "disable_checkpoint = true\nprovider_installation {\n filesystem_mirror {\n"
            ' path = "/mirror"\n include = ["registry.terraform.io/hashicorp/aws"]\n }\n}\n'
        )
        (root / "plugin-cache").mkdir()
        for mode in (
            "valid",
            "valid_env_selection",
            "failed",
            "malformed",
            "unsupported_version",
            "missing_profile",
            "login_missing_cache",
            "login_cached",
        ):
            case = root / mode
            case.mkdir()
            counter = case / "process-count"
            requests = []

            class STS(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    self.connection.settimeout(5)
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 4096:
                        self.send_error(400)
                        return
                    body = parse_qs(self.rfile.read(length).decode())
                    valid = body.get("Action") == ["GetCallerIdentity"] and (
                        f"Credential={ACCESS}/" in self.headers.get("Authorization", "")
                    )
                    valid = valid and self.headers.get("X-Amz-Security-Token") == TOKEN
                    self.server.observations.append(valid)
                    if not valid:
                        self.send_error(403)
                        return
                    raw = (
                        f'<GetCallerIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">'
                        f"<GetCallerIdentityResult><Arn>{ARN}</Arn><UserId>synthetic</UserId>"
                        f"<Account>{ACCOUNT}</Account></GetCallerIdentityResult>"
                        "<ResponseMetadata><RequestId>synthetic</RequestId></ResponseMetadata>"
                        "</GetCallerIdentityResponse>"
                    ).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/xml")
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)

            server = ThreadingHTTPServer(("127.0.0.1", 0), STS)
            server.observations = requests
            worker = Thread(target=server.serve_forever)
            worker.start()
            try:
                # Poison default credentials make accidental default selection observable.
                (case / "credentials").write_text(
                    "[default]\naws_access_key_id = SYNTHETIC_POISON_DEFAULT\n"
                    "aws_secret_access_key = synthetic-poison-not-valid\n"
                )
                selected = PROFILE if mode != "missing_profile" else "fixture-missing"
                profile = f"[profile {selected}]\nregion = us-east-1\n"
                if mode in ("login_missing_cache", "login_cached"):
                    profile += f"login_session = {ARN}\n"
                    if mode == "login_cached":
                        cache = case / "no-login-cache"
                        cache.mkdir()
                        reply = synthetic_reply()
                        token = {
                            "accessToken": {
                                "accessKeyId": ACCESS,
                                "secretAccessKey": SECRET,
                                "sessionToken": TOKEN,
                                "accountId": ACCOUNT,
                                "expiresAt": reply["Expiration"],
                            },
                            "clientId": "synthetic-client",
                            "refreshToken": "synthetic-refresh",
                            "dpopKey": "synthetic-unused-key-no-refresh",
                            "tokenType": "synthetic",
                        }
                        (cache / (hashlib.sha256(ARN.encode()).hexdigest() + ".json")).write_text(
                            json.dumps(token)
                        )
                else:
                    # Avoid outer INI command quotes; owned /work paths have no spaces.
                    emitted_mode = "valid" if mode == "valid_env_selection" else mode
                    profile += (
                        f'credential_process = "{sys.executable}" "{Path(__file__).resolve()}" '
                        f"synthetic-process {emitted_mode} {counter}\n"
                    )
                (case / "config").write_text(profile)
                env = environment(case, {**os.environ, "AWS_ACCESS_KEY_ID": "SYNTHETIC_POISON_ENV"})
                env["TF_CLI_CONFIG_FILE"] = str(rc)
                env["TF_PLUGIN_CACHE_DIR"] = str(root / "plugin-cache")
                shutil.copyfile(
                    "/source/infra/aws/deployment/.terraform.lock.hcl", case / ".terraform.lock.hcl"
                )
                (case / "main.tf").write_text(
                    'terraform {\n required_version = "= 1.17.0"\n required_providers {\n'
                    ' aws = { source = "hashicorp/aws", version = "6.70.0" }\n }\n}\n'
                    'provider "aws" {\n region = "us-east-1"\n'
                    + ("" if mode == "valid_env_selection" else ' profile = "fixture-process"\n')
                    + ' shared_config_files = ["'
                    + str(case / "config")
                    + '"]\n'
                    ' shared_credentials_files = ["' + str(case / "credentials") + '"]\n'
                    " skip_metadata_api_check = true\n skip_region_validation = true\n"
                    " max_retries = 0\n"
                    ' endpoints {\n sts = "http://127.0.0.1:'
                    + str(server.server_port)
                    + '"\n }\n}\n'
                    'data "aws_caller_identity" "fixture" {}\n'
                    'output "identity_matches" {\n'
                    ' value = data.aws_caller_identity.fixture.arn == "' + ARN + '"\n}\n'
                )
                code, _, _ = run(
                    [
                        str(terraform),
                        "init",
                        "-backend=false",
                        "-input=false",
                        "-lockfile=readonly",
                    ],
                    case,
                    env,
                )
                if code:
                    raise RuntimeError("offline_provider_initialization_failed")
                code, out, err = run(
                    [str(terraform), "plan", "-input=false", "-no-color"], case, env
                )
                expected_success = mode in ("valid", "valid_env_selection", "login_cached")
                if (code == 0) != expected_success:
                    raise RuntimeError(
                        json.dumps(
                            {
                                "mode": mode,
                                "exit_code": code,
                                "STS_requests": len(requests),
                            }
                        )
                    )
                if expected_success:
                    assert re.search(rb"identity_matches\s+= true", out)
                assert all(requests), "Poison credentials reached the STS fake"
                assert bool(requests) == expected_success, (
                    "Failed process fell through to another credential source"
                )
                assert all(x.encode() not in out + err for x in (ACCESS, SECRET, TOKEN))
                count = len(counter.read_text().splitlines()) if counter.exists() else 0
                observations.append(
                    {
                        "mode": mode,
                        "exit_code": code,
                        "process_invocations": count,
                        "loopback_STS_requests": len(requests),
                        "expected_outcome": True,
                        "credentials_in_captured_Terraform_output": False,
                    }
                )
            finally:
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()
                assert not worker.is_alive()
    print(
        json.dumps(
            {
                "evidence": "native_Terraform_AWS_provider_synthetic_process_local_STS",
                "terraform": "1.17.0",
                "provider": "6.70.0",
                "network": "none; loopback only",
                "real_credentials_or_AWS_calls": False,
                "remote_backend_exercised": False,
                "cases": observations,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "synthetic-process":
        raise SystemExit(process(sys.argv[2], Path(sys.argv[3])))
    elif len(sys.argv) == 1:
        native()
    else:
        raise SystemExit("Fixed offline synthetic probe only")
