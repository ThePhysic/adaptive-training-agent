"""Opt-in real Linux PostgreSQL close-state reproduction; no host ports/firewall.

Uses cached test/PG images in one Docker network-none namespace, synthetic DB,
tmpfs data, and uniquely named containers. No user volume or unrelated process.
"""

import errno
import importlib.util
import json
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PG = (
    "postgres:18.6-bookworm@sha256:bbf83594798e144bff365a9c191c5d779f181fb3135902064ab8ff11918020fc"
)


def states(port):
    rows = []
    for row in Path("/proc/net/tcp").read_text().splitlines()[1:]:
        fields = row.split()
        if int(fields[1].split(":")[1], 16) == port:
            rows.append(fields[3])
    return rows


def seed():
    # Normal PostgreSQL startup/Terminate protocol, with a controlled server-first
    # TCP close. This is local trust-auth synthetic input, not a provider request.
    with socket.create_connection(("127.0.0.1", 55432), timeout=5) as client:
        packet = struct.pack("!I", 196608) + b"user\0training_dev\0database\0training_dev\0\0"
        client.sendall(struct.pack("!I", len(packet) + 4) + packet)

        def read(size):
            result = b""
            while len(result) < size:
                part = client.recv(size - len(result))
                assert part
                result += part
            return result

        while True:
            kind = read(1)
            length = struct.unpack("!I", read(4))[0]
            assert 4 <= length <= 16384 and kind != b"E"
            read(length - 4)
            if kind == b"Z":
                break
        client.sendall(b"X" + struct.pack("!I", 4))
        assert client.recv(1) == b""  # Server FIN observed before client close.
    assert "06" in states(55432)
    print("seeded")


def check():
    spec = importlib.util.spec_from_file_location("release", ROOT / "scripts/check_release.py")
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    evidence = {"type": "real_Linux_PostgreSQL_TIME_WAIT_handoff", "ports": [8000, 55432]}
    evidence["after_pg_stop_ss"] = subprocess.check_output(
        ["ss", "-H", "-tanp", "( sport = :8000 or sport = :55432 )"], text=True
    ).splitlines()
    assert "0A" not in states(55432) and "06" in states(55432)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 8000))
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", 55432))
        except OSError as error:
            assert error.errno == errno.EADDRINUSE
            evidence["original_probe_failure"] = {"port": 55432, "errno": error.errno}
        else:
            raise AssertionError("The original check must reproduce the failure")
    started = time.monotonic()
    release.require_free_ports()
    evidence["passive_wait_seconds"] = round(time.monotonic() - started, 3)
    evidence["strict_binds_succeeded_after_close_state"] = True
    # A real unrelated listener is still refused, and is never stopped/reused.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 8000))
        listener.listen()
        try:
            release.require_free_ports(timeout=0)
        except OSError as error:
            assert error.errno == errno.EADDRINUSE and ":8000" in str(error)
        else:
            raise AssertionError("Live listener must be refused")
        assert listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
    evidence["unrelated_listener_refused_and_left_listening"] = True
    print("EVIDENCE " + json.dumps(evidence))


def docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, check=check, timeout=120)


def main():
    token = uuid4().hex[:8]
    namespace, pg = "fata-ci-ports-" + token, "fata-ci-pg-" + token
    owned = []
    try:
        docker(
            "run",
            "-d",
            "--name",
            namespace,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--mount",
            f"type=bind,source={ROOT},target=/source,readonly",
            "--tmpfs",
            "/source/.cache/f4-01",
            "--entrypoint",
            "python",
            "fata-f403a-network",
            "-c",
            "import threading; threading.Event().wait()",
        )
        owned.append(namespace)
        docker(
            "run",
            "-d",
            "--name",
            pg,
            "--network",
            "container:" + namespace,
            "--user",
            "999:999",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--read-only",
            "--tmpfs",
            "/var/lib/postgresql:uid=999,gid=999,mode=0700",
            "--tmpfs",
            "/var/run/postgresql:uid=999,gid=999,mode=0700",
            "--tmpfs",
            "/tmp",
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "--env",
            "POSTGRES_USER=training_dev",
            "--env",
            "POSTGRES_DB=training_dev",
            PG,
            "postgres",
            "-p",
            "55432",
            "-c",
            "listen_addresses=127.0.0.1",
        )
        owned.append(pg)
        deadline = time.monotonic() + 30
        while docker(
            "exec", pg, "pg_isready", "-h", "127.0.0.1", "-p", "55432", check=False
        ).returncode:
            if time.monotonic() >= deadline:
                raise RuntimeError("Synthetic PostgreSQL failed to start")
            time.sleep(0.1)
        owner = docker("top", pg, "-eo", "pid,comm").stdout.decode().splitlines()
        before = (
            docker("exec", namespace, "ss", "-H", "-ltnp", "sport = :55432")
            .stdout.decode()
            .splitlines()
        )
        docker("exec", namespace, "python", "/source/scripts/check_release_port_handoff.py", "seed")
        docker("stop", "--timeout", "10", pg)
        result = docker(
            "exec", namespace, "python", "/source/scripts/check_release_port_handoff.py", "check"
        )
        evidence = json.loads(
            next(
                row.removeprefix("EVIDENCE ")
                for row in result.stdout.decode().splitlines()
                if row.startswith("EVIDENCE ")
            )
        )
        evidence.update(
            {
                "before_stop_postgres_processes": owner,
                "before_stop_ss": before,
                "pg_container_stopped_before_check": True,
                "network": "none",
                "host_ports_used": False,
                "volumes_deleted": False,
            }
        )
        dest = ROOT / ".cache/f4-03a/ci-port-handoff.json"
        dest.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        for name in reversed(owned):
            docker("rm", "-f", name, check=False)


if __name__ == "__main__":
    if sys.argv[1:] == ["seed"]:
        seed()
    elif sys.argv[1:] == ["check"]:
        check()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit("Fixed local fixture only")
