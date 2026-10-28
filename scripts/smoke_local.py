"""Read-only smoke of the supported launcher. Requires migrated local DB and web build."""

import http.client
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANARY = "synthetic-private-launcher-canary"


def request(path, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=1)
    try:
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        return response.status, json.loads(response.read()), response.getheader("X-Request-ID")
    finally:
        connection.close()


def main():
    # Refuse to reuse or terminate somebody else's API process.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 8000))
    cache = ROOT / ".cache/f107"
    cache.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "FATA_LOCAL_DEV": "1",
        "FATA_ENV": "local",
        "FATA_PROVIDER": "fake",
        "FATA_TELEMETRY_EXPORTER": "none",
        "FATA_HOST": "127.0.0.1",
        "FATA_WORKERS": "1",
    }
    with (cache / "runtime.jsonl").open("w", encoding="utf-8") as output:
        child = subprocess.Popen(
            [sys.executable, "scripts/serve.py"],
            cwd=ROOT,
            env=env,
            stdout=output,
            stderr=output,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            end = time.monotonic() + 10
            while True:
                try:
                    health = request("/health")
                    break
                except OSError:
                    if child.poll() is not None or time.monotonic() >= end:
                        raise RuntimeError("Local launcher unavailable") from None
                    time.sleep(0.025)  # Startup smoke only; not a concurrency assertion.
            ready = request("/ready")
            denied = request(
                "/api/v1/profile?ignored=" + CANARY,
                {"X-Synthetic-Principal": "synthetic-a", "Authorization": CANARY},
            )
            assert health[0] == 200 and ready[0] == 200 and denied[0] == 422
            assert ready[1]["status"] == "ready_local"
        finally:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
    text = (cache / "runtime.jsonl").read_text(encoding="utf-8")
    assert CANARY not in text and "synthetic-a" not in text
    records = [json.loads(line) for line in text.splitlines() if line.strip()]
    assert any(r.get("trace_id") == denied[2] for r in records)
    result = {
        "health": health[0],
        "readiness": ready[0],
        "rejected_request": denied[0],
        "correlated": True,
        "safe_console": True,
        "owned_process_stopped": child.poll() is not None,
    }
    (cache / "launcher-results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
