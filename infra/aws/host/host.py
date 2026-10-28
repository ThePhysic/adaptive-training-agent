"""Root-only future EC2 operations. Never imported by the application or offline checker.

No AWS invocation during import or test. Executed only by a separately authorized
host operator. Ordinary output is classified metadata; private artifacts stay local.
"""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

BASE = Path("/opt/fata")
DATA = Path("/srv/fata")
ENV = {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "HOME": "/root",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_MAX_ATTEMPTS": "1",
    "AWS_PAGER": "",
    "DOCKER_CONFIG": "/run/fata/docker",
    "AWS_SHARED_CREDENTIALS_FILE": "/run/fata/no-credentials",
    "AWS_CONFIG_FILE": "/run/fata/no-config",
}
TOOLS = {
    "docker": ["docker", "--version"],
    "compose": ["docker", "compose", "version"],
    "aws": ["aws", "--version"],
    "ssm": ["amazon-ssm-agent", "-version"],
    "iptables": ["iptables", "--version"],
}


def run(*args, data=None, timeout=90, stdout=subprocess.PIPE, check=True):
    result = subprocess.run(
        list(args),
        input=data,
        stdin=subprocess.DEVNULL if data is None else None,
        stdout=stdout,
        stderr=subprocess.PIPE,
        env=ENV,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError("host_operation_failed")
    return result


def config():
    return json.loads((BASE / "config.json").read_text())


def window(c, now=None):
    start, end = [
        datetime.fromisoformat(c[k].replace("Z", "+00:00")) for k in ("starts_at", "expires_at")
    ]
    if (
        not start <= (now or datetime.now(UTC)) < end
        or not 0 < (end - start).total_seconds() <= 86400
    ):
        raise RuntimeError("execution_window_closed")


def guard():
    # IMDSv2/hop=1 alone does NOT protect host-network containers. Fence all
    # non-loopback app UID traffic, including IMDS, independently of Python guards.
    for uid in ("10001", "999"):
        for binary, tail in (
            (
                "iptables",
                ["-m", "owner", "--uid-owner", uid, "!", "-d", "127.0.0.0/8", "-j", "REJECT"],
            ),
            ("ip6tables", ["-m", "owner", "--uid-owner", uid, "-j", "REJECT"]),
        ):
            if run(binary, "-w", "5", "-C", "OUTPUT", *tail, check=False).returncode:
                run(binary, "-w", "5", "-I", "OUTPUT", "1", *tail)
            run(binary, "-w", "5", "-C", "OUTPUT", *tail)


def compose(*args, stdout=subprocess.PIPE, timeout=90):
    return run(
        "docker",
        "compose",
        "-p",
        "fata-release",
        "-f",
        str(BASE / "compose.release.yaml"),
        "-f",
        str(BASE / "images.json"),
        *args,
        stdout=stdout,
        timeout=timeout,
    )


def attest_tools(c):
    raw = Path("/etc/fata-host-tools.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != c["host_tools_sha256"]:
        raise RuntimeError("unreviewed_host_tools")
    expected = json.loads(raw)
    if set(expected) != set(TOOLS):
        raise RuntimeError("invalid_host_manifest")
    for key, args in TOOLS.items():
        if run(*args).stdout.decode().strip() != expected[key]:
            raise RuntimeError("host_tool_version_mismatch")
    ssm_version = re.search(r"\b(\d+\.\d+\.\d+\.\d+)\b", expected["ssm"])
    if not ssm_version or tuple(map(int, ssm_version[1].split("."))) < (3, 3, 4851, 0):
        raise RuntimeError("unpatched_ssm_agent")


def atomic_text(path, text):
    staging = path.with_name(path.name + ".new")
    with staging.open("w", encoding="utf-8") as out:
        out.write(text)
        out.flush()
        os.fsync(out.fileno())
    os.replace(staging, path)


def attest_bundle():
    manifest = json.loads((BASE / "bundle.json").read_text())
    if set(manifest) != {"config.json", "host.py", "compose.release.yaml"}:
        raise RuntimeError("incomplete_bootstrap_bundle")
    for name, digest in manifest.items():
        if hashlib.sha256((BASE / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("bootstrap_bundle_mismatch")


@contextmanager
def host_lock():
    import fcntl

    folder = Path("/run/fata")
    folder.mkdir(mode=0o700, exist_ok=True)
    with (folder / "prepare.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def data_device(c):
    if not re.fullmatch(r"vol-[0-9a-f]{17}", c["volume_id"]):
        raise RuntimeError("invalid_volume_identity")
    return Path(
        "/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_" + c["volume_id"].replace("-", "")
    )


def wait_device(c, attempts=90, pause=None):
    device = data_device(c)
    for _ in range(attempts):
        if device.exists():
            return device
        (pause or time.sleep)(2)
    raise RuntimeError("data_volume_missing")


def disk_uuid(device):
    value = run("blkid", "-s", "UUID", "-o", "value", str(device)).stdout.decode().strip()
    if not re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", value):
        raise RuntimeError("invalid_volume_uuid")
    return value


def mounted_volume(device, uuid):
    result = run(
        "findmnt", "-n", "-o", "SOURCE,UUID,FSTYPE", "--mountpoint", str(DATA), check=False
    )
    if result.returncode:
        return False
    fields = result.stdout.decode().split()
    if (
        len(fields) != 3
        or fields[1:] != [uuid, "ext4"]
        or Path(fields[0]).resolve() != device.resolve()
    ):
        raise RuntimeError("incorrect_mounted_volume")
    return True


def prepare_storage(c):
    device = wait_device(c)
    if run("lsblk", "-dn", "-o", "TYPE,RO", str(device)).stdout.decode().split() != ["disk", "0"]:
        raise RuntimeError("unrecognized_data_device")
    signatures = json.loads(run("wipefs", "--no-act", "--json", str(device)).stdout)["signatures"]
    fstab = Path("/etc/fstab")
    existing = fstab.read_text()
    if not signatures:
        # Intent survives process/OS restart. An interrupted, still-blank or
        # unrecognized format is never retried automatically.
        if (BASE / "format-intent.json").exists() or " /srv/fata " in existing:
            raise RuntimeError("uncertain_volume_initialization")
        atomic_text(BASE / "format-intent.json", json.dumps({"volume_id": c["volume_id"]}))
        run("mkfs.ext4", str(device))  # No force flag; recognized ext4 never enters this branch.
    elif len(signatures) != 1 or signatures[0]["type"] != "ext4":
        raise RuntimeError("unrecognized_data_volume")
    uuid = disk_uuid(device)
    DATA.mkdir(mode=0o700, exist_ok=True)
    entry = f"UUID={uuid} /srv/fata ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2\n"
    entries = [line for line in existing.splitlines() if " /srv/fata " in line]
    if entries and entries != [entry.rstrip()]:
        raise RuntimeError("mount_configuration_conflict")
    if not entries:
        atomic_text(fstab, existing + "\n" + entry)
    if not mounted_volume(device, uuid):
        run("mount", "--target", str(DATA))
    if not mounted_volume(device, uuid):
        raise RuntimeError("data_not_mounted")
    return {"volume_id": c["volume_id"], "uuid": uuid}


def mount_check(c):
    attest_bundle()
    record = json.loads((BASE / "storage.json").read_text())
    device = data_device(c)
    if record["volume_id"] != c["volume_id"] or not device.exists():
        raise RuntimeError("unverified_data_mount")
    uuid = disk_uuid(device)
    if record["uuid"] != uuid or not mounted_volume(device, uuid):
        raise RuntimeError("unverified_data_mount")


def prepare(c):
    with host_lock():
        run("systemctl", "mask", "docker.service", "docker.socket")
        if run("systemctl", "is-active", "--quiet", "docker.service", check=False).returncode == 0:
            raise RuntimeError("preparation_requires_stopped_docker")
        attest_bundle()
        window(c)
        attest_tools(c)
        guard()
        record = prepare_storage(c)
        configure_host(c)
        atomic_text(BASE / "storage.json", json.dumps(record))
        mount_check(c)
        run("systemctl", "daemon-reload")
        run(
            "systemctl",
            "reset-failed",
            "srv-fata.mount",
            "docker.service",
            "docker.socket",
            check=False,
        )
        run(
            "systemctl", "enable", "fata-prepare.service", "fata-guard.service", "fata-expiry.timer"
        )
        run("systemctl", "start", "fata-expiry.timer")
        run("systemctl", "unmask", "docker.service", "docker.socket")


def configure_host(c):
    if Path("/var/lib/docker").exists() and any(Path("/var/lib/docker").iterdir()):
        raise RuntimeError("nonempty_ami_docker_state")
    Path("/etc/docker").mkdir(exist_ok=True)
    daemon = Path("/etc/docker/daemon.json")
    settings = {
        "data-root": "/srv/fata/docker",
        "log-driver": "json-file",
        "log-opts": {"max-size": "1m", "max-file": "2"},
    }
    if daemon.exists() and json.loads(daemon.read_text()) not in ({}, settings):
        raise RuntimeError("unreviewed_docker_configuration")
    atomic_text(daemon, json.dumps(settings))
    atomic_text(
        BASE / "images.json",
        json.dumps(
            {
                "services": {
                    "app": {"image": c["app_image"], "user": "10001:10001"},
                    "postgres": {
                        "image": c["postgres_image"],
                        "user": "999:999",
                        "cap_drop": ["ALL"],
                        "security_opt": ["no-new-privileges:true"],
                    },
                }
            }
        ),
    )
    units = {
        "fata-prepare.service": PREPARE_UNIT,
        "fata-guard.service": """[Unit]
Before=docker.service fata-release.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/python3 /opt/fata/host.py guard
[Install]
WantedBy=multi-user.target
""",
        "fata-release.service": """[Unit]
Requires=docker.service fata-guard.service fata-prepare.service
After=docker.service fata-guard.service fata-prepare.service network-online.target
RequiresMountsFor=/srv/fata
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/python3 /opt/fata/host.py launch
ExecStop=/usr/bin/python3 /opt/fata/host.py halt
TimeoutStartSec=180
TimeoutStopSec=90
Restart=no
""",
        "fata-expiry.service": "[Service]\nType=oneshot\nExecStart=/usr/bin/systemctl poweroff\n",
        "fata-expiry.timer": (
            "[Timer]\nOnCalendar="
            + datetime.fromisoformat(c["expires_at"].replace("Z", "+00:00")).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            + "\nPersistent=true\nUnit=fata-expiry.service\n[Install]\nWantedBy=timers.target\n"
        ),
    }
    for name, content in units.items():
        atomic_text(Path("/etc/systemd/system", name), content)
    dropin = Path("/etc/systemd/system/docker.service.d")
    dropin.mkdir(exist_ok=True)
    atomic_text(
        dropin / "fata.conf",
        "[Unit]\nRequires=fata-guard.service fata-prepare.service\n"
        "After=fata-guard.service fata-prepare.service\nRequiresMountsFor=/srv/fata\n"
        "[Service]\nExecStartPre=/usr/bin/python3 /opt/fata/host.py mount-check\n",
    )
    # Explicit future Start is required after image publication; never starts
    # application containers just because infrastructure bootstrap completed.
    run("systemctl", "disable", "--now", "sshd.service", check=False)


def verify():
    mount_check(config())
    guard()
    for path in ("/health", "/ready"):
        with urllib.request.urlopen("http://127.0.0.1:8000" + path, timeout=4) as result:
            if result.status != 200:
                raise RuntimeError("application_not_ready")
    containers = json.loads(run("docker", "inspect", "fata-release-app-1").stdout)
    app = containers[0]
    host = app["HostConfig"]
    if not (
        app["Config"]["User"] == "10001:10001"
        and host["ReadonlyRootfs"]
        and host["NetworkMode"] == "host"
        and not host["Privileged"]
        and host["CapDrop"] == ["ALL"]
        and not host["Binds"]
    ):
        raise RuntimeError("unsafe_container_configuration")
    pg = json.loads(run("docker", "inspect", "fata-release-postgres-1").stdout)[0]
    if not (
        pg["Config"]["User"] == "999:999"
        and pg["HostConfig"]["NetworkMode"] == "host"
        and pg["HostConfig"]["CapDrop"] == ["ALL"]
        and not pg["HostConfig"]["Privileged"]
        and any(
            s in ("no-new-privileges", "no-new-privileges:true")
            for s in pg["HostConfig"]["SecurityOpt"]
        )
    ):
        raise RuntimeError("unsafe_database_container_configuration")
    listeners = run("ss", "-H", "-lnt").stdout.decode().splitlines()
    for port in (8000, 55432):
        matching = [line.split()[3] for line in listeners if line.split()[3].endswith(f":{port}")]
        if matching != [f"127.0.0.1:{port}"]:
            raise RuntimeError("unsafe_listener")


def verify_daemon():
    info = json.loads(run("docker", "info", "--format", "{{json .}}").stdout)
    if info["DockerRootDir"].rstrip("/") != (DATA / "docker").as_posix() or any(
        "userns" in s or "rootless" in s for s in info["SecurityOptions"]
    ):
        raise RuntimeError("unreviewed_docker_identity_or_storage")


def start(c):
    window(c)
    attest_tools(c)
    guard()
    mount_check(c)
    Path(ENV["DOCKER_CONFIG"]).mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        verify_daemon()
        token = run("aws", "ecr", "get-login-password").stdout
        run("docker", "login", "--username", "AWS", "--password-stdin", c["registry"], data=token)
        del token
        compose("pull")
        window(c)
        compose("up", "-d", "--pull", "never", "--wait")
        verify()
    except BaseException:
        compose("stop", "--timeout", "40")
        raise
    finally:
        # Exact ephemeral credential file only; no recursive deletion.
        Path(ENV["DOCKER_CONFIG"], "config.json").unlink(missing_ok=True)


def backup(c):
    # Expired windows still permit explicit recovery. Leave application stopped.
    mount_check(c)
    guard()
    verify_daemon()
    run("systemctl", "stop", "fata-release.service")
    compose("up", "-d", "--pull", "never", "--wait", "postgres")
    folder = DATA / "backups"
    folder.mkdir(mode=0o700, exist_ok=True)
    name = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex + ".pgcustom"
    archive = folder / name
    with archive.open("xb") as out:
        compose(
            "exec",
            "-T",
            "postgres",
            "pg_dump",
            "-h",
            "127.0.0.1",
            "-p",
            "55432",
            "-U",
            "training_dev",
            "-d",
            "training_dev",
            "-Fc",
            stdout=out,
        )
    if not 0 < archive.stat().st_size <= 1024**3:
        raise RuntimeError("backup_size_rejected")
    sha = hashlib.sha256()
    with archive.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            sha.update(chunk)
    result = run(
        "aws",
        "s3api",
        "put-object",
        "--bucket",
        c["bucket"],
        "--key",
        "backups/" + name,
        "--body",
        str(archive),
        "--server-side-encryption",
        "AES256",
        "--checksum-algorithm",
        "SHA256",
    )
    private = {"sha256": sha.hexdigest(), "s3": json.loads(result.stdout)}
    archive.with_suffix(".receipt.json").write_text(json.dumps(private))
    compose("stop", "--timeout", "30", "postgres")


def main():
    os.umask(0o077)
    if platform.system() != "Linux" or os.geteuid() != 0 or len(sys.argv) != 2:
        raise RuntimeError("unsupported_host_operator")
    operation = sys.argv[1]
    c = config()
    if operation == "guard":
        attest_bundle()
        guard()
    elif operation == "prepare":
        run("systemctl", "stop", "fata-release.service", "docker.socket", "docker.service")
        run("systemctl", "mask", "docker.service", "docker.socket")
        run("systemctl", "restart", "fata-prepare.service", timeout=240)
    elif operation == "prepare-host":
        prepare(c)
    elif operation == "mount-check":
        mount_check(c)
    elif operation == "start":
        window(c)
        run("systemctl", "start", "fata-release.service", timeout=180)
    elif operation == "launch":
        start(c)
    elif operation == "stop":
        run("systemctl", "stop", "fata-release.service")
    elif operation == "halt":
        compose("stop", "--timeout", "40", "app")
        compose("stop", "--timeout", "30", "postgres")
    elif operation == "verify":
        verify()
    elif operation == "backup":
        backup(c)
    else:
        raise RuntimeError("unsupported_operation")
    print('{"event":"host_operation_complete"}')


PREPARE_UNIT = """[Unit]
Description=Verify the reviewed bundle and attached data volume; never start app
After=network-online.target
Before=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/python3 /opt/fata/host.py prepare-host
TimeoutStartSec=240
Restart=no
[Install]
WantedBy=multi-user.target
"""


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        print('{"event":"host_operation_failed"}', file=sys.stderr)
        raise SystemExit(1) from None
