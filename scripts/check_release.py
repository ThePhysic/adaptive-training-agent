"""Opt-in real Docker drill; unique synthetic volumes, binary backups, no cloud.

Refuses occupied localhost ports. Keeps scoped volumes and private backup/state
under .cache for review; stops/removes only its own uniquely named containers.
"""

import concurrent.futures
import errno
import hashlib
import http.client
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".cache/f4-01"
STAGE.mkdir(parents=True, exist_ok=True)
IMAGE = os.environ.get("FATA_RELEASE_IMAGE", "fata-release:f4-01")
BASELINE_IMAGE = os.environ.get("FATA_RELEASE_BASELINE_IMAGE", "fata-release:f4-01-baseline")


def run(*args, data=None, timeout=180, check=True, env=None):
    result = subprocess.run(
        list(args),
        cwd=ROOT,
        input=data,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    if check and result.returncode:
        raise RuntimeError("Local release command failed: " + args[0])
    return result


def compose(project, *args, image=IMAGE):
    return run(
        "docker",
        "compose",
        "-f",
        "compose.release.yaml",
        "-p",
        project,
        *args,
        env={**os.environ, "FATA_RELEASE_IMAGE": image},
    )


def container(project, service):
    return project + "-" + service + "-1"


def app(project, *args, data=None):
    return run("docker", "exec", "-i", container(project, "app"), *args, data=data)


def probe(project, mode, state=None):
    return json.loads(
        app(
            project,
            "python",
            "scripts/release_probe.py",
            mode,
            data=json.dumps(state).encode() if state else None,
        ).stdout
    )


def sql(project, query):
    return (
        run(
            "docker",
            "exec",
            "--user",
            "postgres",
            container(project, "postgres"),
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
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            query,
        )
        .stdout.decode()
        .strip()
    )


def http_status(path):
    c = http.client.HTTPConnection("127.0.0.1", 8000, timeout=4)
    try:
        c.request("GET", path)
        r = c.getresponse()
        return r.status
    finally:
        c.close()


def wait_for(check, timeout=20):
    end = time.monotonic() + timeout
    while True:
        try:
            if check():
                return
        except (
            OSError,
            RuntimeError,
        ):
            pass
        if time.monotonic() >= end:
            raise RuntimeError("Local operation did not reach expected state")
        time.sleep(0.05)  # Operational startup/SQL-condition polling, not a race assertion.


def locked_request(project, *, restart=False):
    code = """import psycopg
c=psycopg.connect('host=127.0.0.1 port=55432 dbname=training_dev user=training_dev')
c.execute('LOCK TABLE profiles IN ACCESS EXCLUSIVE MODE')
print('locked',flush=True)
input()
c.rollback();c.close()
"""
    lock = subprocess.Popen(
        ["docker", "exec", "-i", container(project, "app"), "python", "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        assert lock.stdout.readline() == b"locked\n"
        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            pending = pool.submit(
                run,
                "docker",
                "exec",
                container(project, "app"),
                "python",
                "scripts/release_probe.py",
                "generate",
                check=False,
            )
            waiting = (
                "wait_event_type='Lock' AND "
                "query LIKE 'SELECT revision, preferences FROM profiles%'"
            )
            query = "SELECT count(*) FROM pg_stat_activity WHERE " + waiting
            wait_for(lambda: int(sql(project, query)) > 0, timeout=4)
            started = time.perf_counter()
            if restart:
                compose(project, "stop", "app")
            else:
                assert (
                    sql(
                        project,
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE " + waiting,
                    )
                    == "t"
                )
            result = pending.result(timeout=15)
            elapsed = time.perf_counter() - started
            if result.returncode == 0:
                value = json.loads(result.stdout)
                assert value["outcome"] != "plan"
                outcome = value["outcome"]
            else:
                outcome = "client_process_interrupted"
            return {
                "barrier": "native_pg_lock_wait_observed",
                "outcome": outcome,
                "seconds": elapsed,
            }
    finally:
        if lock.poll() is None:
            try:
                lock.communicate(b"\n", timeout=10)
            except (
                BrokenPipeError,
                subprocess.TimeoutExpired,
            ):
                lock.kill()
                lock.wait(timeout=5)


def require_free_ports(ports=(8000, 55432), *, timeout=75, now=None, pause=None):
    """Wait for strict exclusive binds, including Linux TCP close-state cleanup.

    Never reuse a busy port, enable address sharing, or stop its owner. Both
    sockets remain held until the complete pair has been checked. Docker's later
    bind remains authoritative if another process wins the unavoidable handoff.
    """
    now, pause = now or time.monotonic, pause or time.sleep
    deadline = now() + timeout
    reported = set()
    while True:
        with ExitStack() as sockets:
            try:
                for port in ports:
                    probe = sockets.enter_context(socket.socket())
                    probe.bind(("127.0.0.1", port))
            except OSError as error:
                if error.errno != errno.EADDRINUSE:
                    raise
                if port not in reported:
                    print(
                        json.dumps({"release_port_wait": port, "timeout_seconds": timeout}),
                        flush=True,
                    )
                    reported.add(port)
                if now() >= deadline:
                    raise OSError(
                        error.errno,
                        f"Release requires free 127.0.0.1:{port}; still busy after {timeout}s",
                    ) from None
            else:
                return
        pause(min(0.25, max(0, deadline - now())))


def main():
    if len(sys.argv) != 1:
        raise SystemExit("Fixed local drill only")
    require_free_ports()
    token = uuid4().hex[:8]
    source = "fata-f401-" + token + "-source"
    restored = "fata-f401-" + token + "-restore"
    evidence = {
        "version": "local-release-drill-v1",
        "source": "actual_Docker_PostgreSQL_HTTP_fake",
        "projects": [source, restored],
        "image": IMAGE,
        "faults": {},
    }
    run_dir = STAGE / token
    run_dir.mkdir()
    try:
        compose(source, "up", "-d", "--pull", "never", "--wait")
        wait_for(lambda: http_status("/ready") == 200)
        state = probe(source, "seed")
        (run_dir / "private-state.json").write_text(json.dumps(state), encoding="utf-8")
        evidence["initial"] = probe(source, "verify", state)
        evidence["cold_request_observation"] = state["timings"]
        evidence["performance"] = probe(source, "measure")
        evidence["resources"] = (
            run(
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{json .}}",
                container(source, "app"),
                container(source, "postgres"),
            )
            .stdout.decode()
            .splitlines()
        )
        evidence["faults"]["connection_terminated"] = locked_request(source)
        evidence["faults"]["graceful_inflight_stop"] = locked_request(source, restart=True)
        evidence["graceful_exit"] = (
            run("docker", "inspect", "--format", "{{.State.ExitCode}}", container(source, "app"))
            .stdout.decode()
            .strip()
        )
        compose(source, "up", "-d", "--pull", "never", "--wait", "app")
        evidence["after_restart"] = probe(source, "verify", state)
        compose(source, "stop", "postgres")
        evidence["faults"]["db_unavailable"] = {
            "health": http_status("/health"),
            "ready": http_status("/ready"),
        }
        assert evidence["faults"]["db_unavailable"] == {"health": 200, "ready": 503}
        compose(source, "up", "-d", "--pull", "never", "--wait", "postgres")
        wait_for(lambda: http_status("/ready") == 200)
        evidence["after_db_recovery"] = probe(source, "verify", state)
        # Idle application SIGKILL is deliberately different from graceful drain.
        compose(source, "kill", "-s", "SIGKILL", "app")
        compose(source, "up", "-d", "--pull", "never", "--wait", "app")
        evidence["after_crash"] = probe(source, "verify", state)
        compose(source, "stop", "app")
        backup = run_dir / "synthetic.pgcustom"
        started = time.perf_counter()
        with backup.open("wb") as output:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "--user",
                    "postgres",
                    container(source, "postgres"),
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
                ],
                stdout=output,
                stderr=subprocess.PIPE,
                timeout=60,
                check=True,
            )
        evidence["backup"] = {
            "bytes": backup.stat().st_size,
            "sha256": hashlib.sha256(backup.read_bytes()).hexdigest(),
            "seconds": time.perf_counter() - started,
            "quiesced": True,
        }
        compose(source, "stop", "postgres")
        compose(restored, "up", "-d", "--pull", "never", "--wait", "postgres")
        assert sql(restored, "SELECT count(*) FROM pg_tables WHERE schemaname='public'") == "0"
        started = time.perf_counter()
        with backup.open("rb") as data:
            subprocess.run(
                [
                    "docker",
                    "exec",
                    "-i",
                    "--user",
                    "postgres",
                    container(restored, "postgres"),
                    "pg_restore",
                    "-h",
                    "127.0.0.1",
                    "-p",
                    "55432",
                    "-U",
                    "training_dev",
                    "-d",
                    "training_dev",
                    "--exit-on-error",
                    "--single-transaction",
                    "--no-owner",
                    "--no-privileges",
                ],
                stdin=data,
                capture_output=True,
                timeout=60,
                check=True,
            )
        evidence["restore_seconds"] = time.perf_counter() - started
        compose(restored, "up", "-d", "--pull", "never", "--wait", "app")
        evidence["restored"] = probe(restored, "verify", state)
        evidence["row_counts"] = sql(
            restored,
            "SELECT (SELECT count(*) FROM approved_plans),"
            "(SELECT count(*) FROM approval_idempotency),(SELECT count(*) FROM approval_audit),"
            "(SELECT count(*) FROM session_records),(SELECT count(*) FROM session_idempotency)",
        )
        assert evidence["row_counts"] == "1|1|1|1|1"
        assert sql(restored, "SELECT count(*) FROM probe_authorities") == "0"
        evidence["migration_count"] = int(sql(restored, "SELECT count(*) FROM schema_migrations"))
        assert evidence["migration_count"] == 9
        compose(restored, "stop", "app")
        compose(
            restored,
            "up",
            "-d",
            "--pull",
            "never",
            "--wait",
            "app",
            image=BASELINE_IMAGE,
        )
        evidence["rollback_same_schema"] = probe(restored, "verify", state)
        compose(restored, "stop", "app")
        bad = run_dir / "changed-migration.sql"
        bad.write_text(
            (ROOT / "migrations/009_probe_authority.sql").read_text(encoding="utf-8")
            + "\n-- mismatch fixture\n",
            encoding="utf-8",
        )
        result = run(
            "docker",
            "run",
            "--rm",
            "--network",
            "host",
            "--read-only",
            "--env",
            "FATA_RELEASE_ACK=local-synthetic-only",
            "--env",
            "FATA_LOCAL_DEV=1",
            "--mount",
            f"type=bind,source={bad.resolve()},target=/app/migrations/009_probe_authority.sql,readonly",
            IMAGE,
            check=False,
        )
        assert result.returncode != 0 and b"release_start_failed" in result.stderr
        evidence["incompatible_migration_start_rejected"] = True
        compose(restored, "up", "-d", "--pull", "never", "--wait", "app")
        evidence["forward_again"] = probe(restored, "verify", state)
        evidence["image_metadata"] = json.loads(run("docker", "image", "inspect", IMAGE).stdout)[0][
            "Id"
        ]
        (run_dir / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    finally:
        for project in (source, restored):
            compose(project, "stop", "--timeout", "40")
            compose(project, "down")  # No --volumes: backup/recovery state retained for review.


if __name__ == "__main__":
    main()
