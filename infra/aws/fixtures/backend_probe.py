"""Opt-in native Terraform-core experiment; fixed synthetic cache and local S3/STS only.

No AWS CLI, credentials export, provider plugin, managed resources or real backend.
The senderless deny proxy is independent of the explicitly loopback-only endpoints.
"""

import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[3]
BUCKET = "fata-synthetic-state"
KEY = "ec2-demo/terraform.tfstate"
STATE = json.dumps(
    {
        "version": 4,
        "terraform_version": "1.17.0",
        "serial": 1,
        "lineage": "00000000-0000-0000-0000-000000000001",
        "outputs": {},
        "resources": [],
    }
).encode()


def fixture(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def local_url(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise ValueError("loopback_fixture_endpoint_required")
    return url


def configuration(url, case, account):
    endpoint = json.dumps(local_url(url))

    def q(path):
        return json.dumps(path.as_posix())

    return f'''terraform {{
  required_version = "= 1.17.0"
  backend "s3" {{
    bucket = "{BUCKET}"
    key = "{KEY}"
    region = "us-east-1"
    encrypt = true
    use_lockfile = true
    workspace_key_prefix = "env:"
    profile = "future-f4-preflight"
    shared_config_files = [{q(case / "config")}]
    shared_credentials_files = [{q(case / "credentials")}]
    allowed_account_ids = ["{account}"]
    skip_metadata_api_check = true
    skip_region_validation = true
    use_path_style = true
    max_retries = 1
    retry_mode = "standard"
    endpoints = {{ s3 = {endpoint}, sts = {endpoint} }}
  }}
}}
'''


def service(auth, failure=None, empty=False, missing_status=404):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def reply(self, code, body=b"", content_type="application/xml"):
            self.send_response(code)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", content_type)
            self.send_header("x-amz-bucket-region", "us-east-1")
            self.send_header("x-amz-server-side-encryption", "AES256")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def operation(self):
            if len(self.server.observations) >= 64:
                return self.reply(403)
            if (
                f"Credential={auth.ACCESS}/" not in self.headers.get("Authorization", "")
                or self.headers.get("X-Amz-Security-Token") != auth.TOKEN
            ):
                self.server.observations.append("rejected_credentials")
                return self.reply(403)
            parsed = urlsplit(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 32768:
                return self.reply(403)
            body = self.rfile.read(length)
            if (
                self.command == "POST"
                and parsed.path == "/"
                and parse_qs(body.decode()).get("Action") == ["GetCallerIdentity"]
            ):
                self.server.observations.append("identity_read")
                return self.reply(
                    200,
                    (
                        '<GetCallerIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">'
                        f"<GetCallerIdentityResult><Arn>{auth.ARN}</Arn><UserId>synthetic</UserId>"
                        f"<Account>{auth.ACCOUNT}</Account></GetCallerIdentityResult>"
                        "<ResponseMetadata><RequestId>synthetic</RequestId></ResponseMetadata>"
                        "</GetCallerIdentityResponse>"
                    ).encode(),
                )
            query = parse_qs(parsed.query)
            if (
                self.command == "GET"
                and parsed.path == "/" + BUCKET
                and query.get("list-type") == ["2"]
            ):
                self.server.observations.append("workspace_list")
                self.server.listing_prefixes.append(
                    "env:/" if query.get("prefix") == ["env:/"] else "unapproved_prefix"
                )
                if query.get("prefix") != ["env:/"]:
                    self.server.observations.append("rejected_prefix")
                    return self.reply(403)
                if failure:
                    code, reason = (
                        (500, "InternalError") if failure == "transient" else (403, "AccessDenied")
                    )
                    return self.reply(code, f"<Error><Code>{reason}</Code></Error>".encode())
                return self.reply(
                    200,
                    b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>false</IsTruncated></ListBucketResult>',
                )
            if parsed.path == f"/{BUCKET}/{KEY}":
                if self.command in ("GET", "HEAD"):
                    self.server.observations.append("state_read")
                    self.server.state_methods.append(self.command)
                    if failure and failure != "discovery_denied":
                        return self.reply(403, b"<Error><Code>AccessDenied</Code></Error>")
                    if self.server.state_body is None:
                        return self.reply(
                            missing_status,
                            (
                                b"<Error><Code>NoSuchKey</Code></Error>"
                                if missing_status == 404
                                else b"<Error><Code>AccessDenied</Code></Error>"
                            ),
                        )
                    return self.reply(200, self.server.state_body)
                if self.command == "PUT":
                    self.server.observations.append("rejected_state_put")
                    return self.reply(403)
            if parsed.path == f"/{BUCKET}/{KEY}.tflock":
                if self.command == "PUT":
                    self.server.observations.append("lock_put")
                    if self.headers.get("If-None-Match") != "*" or self.server.lock_body:
                        return self.reply(412, b"<Error><Code>PreconditionFailed</Code></Error>")
                    # Real core output, kept only in memory; never logged/exported.
                    self.server.lock_body = body
                    return self.reply(200)
                if self.command == "GET":
                    self.server.observations.append("lock_read")
                    return self.reply(200, self.server.lock_body, "application/json")
                if self.command == "DELETE":
                    self.server.observations.append("lock_delete")
                    self.server.lock_body = b""
                    return self.reply(204)
            self.server.observations.append("rejected_operation")
            self.reply(403)

        do_GET = operation
        do_POST = operation
        do_HEAD = operation
        do_PUT = operation
        do_DELETE = operation

    value = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    value.observations = []
    value.listing_prefixes = []
    value.state_methods = []
    value.lock_body = b""
    value.state_body = None if empty else STATE
    return value


def run(command, cwd, env, stdin=None):
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name != "nt",
    ) as child:
        try:
            out, err = child.communicate(input=stdin, timeout=30)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                os.killpg(child.pid, signal.SIGKILL)
            child.communicate(timeout=5)
            raise RuntimeError("synthetic_backend_timeout") from None
    auth = fixture("authentication_probe")
    if any(value.encode() in out + err for value in (auth.ACCESS, auth.SECRET, auth.TOKEN)):
        raise RuntimeError("synthetic_output_privacy_failure")
    return child.returncode, out, err


def native():
    auth, contract, tunnel = (
        fixture(name) for name in ("authentication_probe", "identity_contract", "sts_tunnel")
    )
    terraform = ROOT / (
        ".tools/terraform/terraform.exe" if os.name == "nt" else ".tools/terraform-linux/terraform"
    )
    stage = ROOT / ".cache/f4-03b-r5a"
    stage.mkdir(parents=True, exist_ok=True)
    observations = []
    for mode in (
        "fresh_cache",
        "missing_cache",
        "wrong_account",
        "s3_denied",
        "missing_profile",
        "s3_transient",
        "empty_state",
        "lock_held",
        "discovery_denied",
        "missing_state_forbidden",
    ):
        policy = tunnel.TunnelPolicy()  # No real socket connector can be enabled here.
        failure = (
            "transient"
            if mode == "s3_transient"
            else "denied"
            if mode == "s3_denied"
            else "discovery_denied"
            if mode == "discovery_denied"
            else None
        )
        proxy, s3 = (
            tunnel.server(policy),
            service(
                auth,
                failure=failure,
                empty=mode in ("empty_state", "missing_state_forbidden"),
                missing_status=403 if mode == "missing_state_forbidden" else 404,
            ),
        )
        workers = [Thread(target=s.serve_forever) for s in (proxy, s3)]
        for worker in workers:
            worker.start()
        try:
            with tempfile.TemporaryDirectory(prefix="synthetic-backend-", dir=stage) as temporary:
                case = Path(temporary)
                selected = "missing" if mode == "missing_profile" else contract.PROFILE
                (case / "config").write_text(
                    f"[profile {selected}]\nregion = us-east-1\nlogin_session = {auth.ARN}\n"
                )
                (case / "credentials").write_text(
                    "[default]\naws_access_key_id = SYNTHETIC_POISON_DEFAULT\n"
                    "aws_secret_access_key = synthetic-poison\n"
                )
                cache = case / "cache"
                cache.mkdir()
                if mode != "missing_cache":
                    token = {
                        "accessToken": {
                            "accessKeyId": auth.ACCESS,
                            "secretAccessKey": auth.SECRET,
                            "sessionToken": auth.TOKEN,
                            "accountId": auth.ACCOUNT,
                            "expiresAt": auth.synthetic_reply()["Expiration"],
                        },
                        "clientId": "synthetic",
                        "refreshToken": "synthetic-unused",
                        "dpopKey": "synthetic-unused",
                    }
                    (cache / (sha256(auth.ARN.encode()).hexdigest() + ".json")).write_text(
                        json.dumps(token)
                    )
                (case / "offline.rc").write_text("disable_checkpoint = true\n")
                env = contract.environment(
                    os.environ,
                    case,
                    case / "config",
                    case / "credentials",
                    cache,
                    case / "offline.rc",
                    f"http://127.0.0.1:{proxy.server_port}",
                )
                env["AWS_REQUEST_CHECKSUM_CALCULATION"] = "WHEN_REQUIRED"
                (case / "main.tf").write_text(
                    configuration(
                        f"http://127.0.0.1:{s3.server_port}",
                        case,
                        "111111111111" if mode == "wrong_account" else auth.ACCOUNT,
                    )
                )
                version, out, _ = run([str(terraform), "version", "-json"], case, env)
                if version or json.loads(out)["terraform_version"] != "1.17.0":
                    raise RuntimeError("pinned_core_required")
                code, out, err = run(
                    [str(terraform), "init", "-input=false", "-no-color"], case, env
                )
                if (code == 0) != (
                    mode in ("fresh_cache", "empty_state", "lock_held", "discovery_denied")
                ):
                    raise RuntimeError("synthetic_backend_init_unexpected_disposition")
                if mode == "s3_transient" and s3.observations.count("workspace_list") != 1:
                    raise RuntimeError("synthetic_retry_owner_or_attempt_bound_failed")
                codes = [code]
                if mode == "fresh_cache":
                    for args in (
                        ["init", "-input=false", "-no-color"],
                        ["plan", "-input=false", "-no-color", "-lock-timeout=0s"],
                    ):
                        code, out, err = run([str(terraform), *args], case, env)
                        codes.append(code)
                        if code:
                            raise RuntimeError("synthetic_backend_repeat_or_lock_failed")
                    if (
                        s3.lock_body
                        or s3.observations.count("lock_put") != 1
                        or s3.observations.count("lock_delete") != 1
                    ):
                        raise RuntimeError("synthetic_lock_lifecycle_failed")
                if mode == "empty_state":
                    if any(x in s3.observations for x in ("state_put", "lock_put", "lock_delete")):
                        raise RuntimeError("synthetic_empty_init_unexpected_write")
                    code, out, err = run(
                        [
                            str(terraform),
                            "plan",
                            "-input=false",
                            "-no-color",
                            "-lock-timeout=0s",
                        ],
                        case,
                        env,
                    )
                    codes.append(code)
                    if (
                        code
                        or s3.state_body is not None
                        or s3.lock_body
                        or s3.observations.count("lock_put") != 1
                        or s3.observations.count("lock_delete") != 1
                    ):
                        raise RuntimeError("synthetic_empty_state_plan_boundary_failed")
                if mode == "lock_held":
                    s3.lock_body = json.dumps(
                        {
                            "ID": "synthetic-held-lock",
                            "Operation": "OperationTypePlan",
                            "Who": "synthetic",
                            "Version": "1.17.0",
                            "Created": "2030-01-01T00:00:00Z",
                            "Path": "synthetic",
                        }
                    ).encode()
                    code, out, err = run(
                        [
                            str(terraform),
                            "plan",
                            "-input=false",
                            "-no-color",
                            "-lock-timeout=0s",
                        ],
                        case,
                        env,
                    )
                    codes.append(code)
                    if code != 1 or not s3.lock_body or "lock_delete" in s3.observations:
                        raise RuntimeError("synthetic_held_lock_was_not_preserved")
                if any(
                    value.encode() in out + err for value in (auth.ACCESS, auth.SECRET, auth.TOKEN)
                ):
                    raise RuntimeError("synthetic_output_privacy_failure")
                if policy.summary()["connection_attempts"] or any(
                    x.startswith("rejected") for x in s3.observations
                ):
                    raise RuntimeError("synthetic_network_or_credential_boundary_failure")
                observations.append(
                    {
                        "case": mode,
                        "native_exit_codes": codes,
                        "operations": {
                            kind: s3.observations.count(kind)
                            for kind in sorted(set(s3.observations))
                        },
                        "external_proxy_attempts": 0,
                        "listing_prefixes": s3.listing_prefixes,
                        "state_methods": s3.state_methods,
                        "expected_disposition": True,
                    }
                )
        finally:
            policy.abort.set()
            for server in (proxy, s3):
                server.shutdown()
                server.server_close()
            for worker in workers:
                worker.join(timeout=5)
                if worker.is_alive():
                    raise RuntimeError("synthetic_worker_not_awaited")
    return {
        "evidence": "native_core_synthetic_login_cache_loopback_S3_STS",
        "terraform": "1.17.0",
        "real_AWS_requests": 0,
        "real_credentials": False,
        "cases": observations,
        "limits": (
            "No AWS IAM/TLS/refresh/Free-plan proof; Windows proxy isolation "
            "is not a kernel network namespace"
        ),
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["--native-offline"]:
        raise SystemExit("Explicit --native-offline required; fixed synthetic endpoints only")
    try:
        print(json.dumps(native(), indent=2))
    except (
        OSError,
        ValueError,
        RuntimeError,
    ):
        raise SystemExit("synthetic_backend_probe_failed_no_raw_output") from None
