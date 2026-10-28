"""Offline SDK compatibility exercise; only fixed local metadata files."""

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

from offline_sdk import Capture

ROOT = Path(__file__).resolve().parents[2]


def main():
    if len(sys.argv) != 1:
        raise SystemExit("No activation, endpoint, credential or live options")
    path = ROOT / ".cache/f3-05a/packet.json"
    if path.stat().st_size > 8 * 1024 * 1024:
        raise SystemExit("Oversized local packet")
    packet = json.loads(path.read_text(encoding="utf-8"))
    with Capture() as capture:
        capture.experiments(packet["experiment"])
        capture.observations(packet["observations"])
        failure = path.parent / "failure.json"
        if failure.exists() and failure.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("Oversized failure metadata")
        failure_rows = json.loads(failure.read_text(encoding="utf-8")) if failure.exists() else []
        capture.observations(failure_rows)
        capture.scores(packet["experiment"])
        spans = capture.flush()
        scores = [s for batch in capture.requests for s in batch]
        result = {
            "sdk": importlib.metadata.version("langfuse"),
            "otel": importlib.metadata.version("opentelemetry-sdk"),
            "sdk_lock_sha256": hashlib.sha256(
                (Path(__file__).parent / "uv.lock").read_bytes()
            ).hexdigest(),
            "bridge_sha256": hashlib.sha256(
                (Path(__file__).parent / "offline_sdk.py").read_bytes()
            ).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "manifest": packet["manifest"],
            "summary": packet["summary"],
            "observations": spans,
            "scores": scores,
            "failed": capture.failed,
            "dropped": capture.dropped,
            "network_requests": 0,
            "evidence": "offline_sdk_mock_not_hosted",
        }
    (path.parent / "sdk-result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps({k: result[k] for k in ("sdk", "otel", "failed", "dropped", "network_requests")})
    )
    print(json.dumps({"observations": len(spans), "scores": len(scores)}))
    assert len(spans) == len(packet["observations"]) + len(failure_rows) and len(scores) == 300


if __name__ == "__main__":
    main()
