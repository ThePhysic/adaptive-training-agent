"""Opt-in synthetic Linux firewall/PG fixture. No host firewall or AWS traffic.

Requires previously built fata-f403a-network image and cached pinned PostgreSQL.
Only owned namespace containers are removed; PostgreSQL data is disposable tmpfs.
"""

import json
import subprocess
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PG = (
    "postgres:18.6-bookworm@sha256:bbf83594798e144bff365a9c191c5d779f181fb3135902064ab8ff11918020fc"
)


def run(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, check=check, timeout=60)


def main():
    token = uuid4().hex[:8]
    namespace, pg = "fata-f403a-net-" + token, "fata-f403a-pg-" + token
    evidence = {
        "type": "actual_Linux_owner_firewall_and_PostgreSQL_synthetic_namespace",
        "host_network_used": False,
        "external_network": "none",
        "phases": {},
    }
    try:
        run(
            "run",
            "-d",
            "--name",
            namespace,
            "--network",
            "none",
            "--cap-drop",
            "ALL",
            "--cap-add",
            "NET_ADMIN",
            "--cap-add",
            "SETUID",
            "--cap-add",
            "SETGID",
            "--cap-add",
            "NET_BIND_SERVICE",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--sysctl",
            "net.ipv6.conf.all.disable_ipv6=0",
            "--sysctl",
            "net.ipv6.conf.default.disable_ipv6=0",
            "--mount",
            f"type=bind,source={ROOT},target=/source,readonly",
            "fata-f403a-network",
            "serve",
        )
        end = time.monotonic() + 20
        while b"ready" not in run("logs", namespace).stdout:
            if time.monotonic() > end:
                raise RuntimeError("namespace_fixture_not_ready")
            time.sleep(0.1)
        lock = run(
            "exec", namespace, "python", "/source/infra/aws/fixtures/network_probe.py", "lock"
        )
        assert b"exclusive_lock_waited_then_recovered" in lock.stdout
        evidence["actual_preparation_lock_barrier"] = True
        run(
            "exec",
            namespace,
            "python",
            "/source/infra/aws/fixtures/network_probe.py",
            "guard-app-only",
        )
        evidence["baseline"] = "F4-02 app-only fence; PostgreSQL unprotected"
        run(
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
            "-c",
            "log_min_error_statement=panic",
        )
        end = time.monotonic() + 30
        while run(
            "exec", pg, "pg_isready", "-h", "127.0.0.1", "-p", "55432", check=False
        ).returncode:
            if time.monotonic() > end:
                raise RuntimeError("postgres_fixture_not_ready")
            time.sleep(0.1)
        for phase in ("before", "after"):
            if phase == "after":
                run(
                    "exec",
                    namespace,
                    "python",
                    "/source/infra/aws/fixtures/network_probe.py",
                    "guard",
                )
            probes = [
                json.loads(
                    run(
                        "exec",
                        namespace,
                        "python",
                        "/source/infra/aws/fixtures/network_probe.py",
                        "probe",
                        str(uid),
                    ).stdout
                )
                for uid in (0, 10001, 999)
            ]
            sql = (
                "COPY (SELECT '') TO PROGRAM 'timeout 2 bash -c ''set -e; "
                "exec 3<>/dev/tcp/169.254.169.254/80; cat >/dev/null''';"
            )
            copy = run(
                "exec",
                pg,
                "psql",
                "-h",
                "127.0.0.1",
                "-p",
                "55432",
                "-U",
                "training_dev",
                "-d",
                "training_dev",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                sql,
                check=False,
            )
            pg_connected = copy.returncode == 0
            assert probes[0]["ipv4_metadata"] and probes[0]["ipv6_metadata"]
            for probe in probes:
                assert probe["loopback"]
                if probe["uid"]:
                    expected = phase == "before" and probe["uid"] == 999
                    assert probe["ipv4_metadata"] == expected
                    assert probe["ipv6_metadata"] == expected
            assert pg_connected == (phase == "before")
            # Success of this SQL query itself also proves retained loopback DB I/O.
            uid = (
                run(
                    "exec",
                    pg,
                    "psql",
                    "-h",
                    "127.0.0.1",
                    "-p",
                    "55432",
                    "-U",
                    "training_dev",
                    "-d",
                    "training_dev",
                    "-At",
                    "-c",
                    "SELECT (regexp_match(pg_read_file('/proc/self/status'), "
                    "'Uid:[[:space:]]+([0-9]+)'))[1];",
                )
                .stdout.decode()
                .strip()
            )
            assert uid == "999"
            evidence["phases"][phase] = {
                "probes": probes,
                "postgres_program_metadata_connected": pg_connected,
                "postgres_backend_uid": 999,
                "postgres_loopback_query": True,
            }
        path = ROOT / ".cache/f4-03a"
        path.mkdir(parents=True, exist_ok=True)
        (path / "network.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        for name in (pg, namespace):
            run("rm", "-f", name, check=False)


if __name__ == "__main__":
    main()
