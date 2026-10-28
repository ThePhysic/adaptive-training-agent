"""Identical synthetic delayed read workload; measured times are not test thresholds."""

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import httpx  # noqa: E402

from future_training.agent.budget import Budget, Deadline, SystemClock  # noqa: E402
from future_training.domain.catalog import load_catalog  # noqa: E402
from future_training.experiments.async_reads import LocalReads, read_context  # noqa: E402
from future_training.identity import Principal  # noqa: E402
from future_training.runtime import loop_factory  # noqa: E402
from future_training.schemas import SavedProfile  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


async def measure():
    catalog = load_catalog()
    profile = SavedProfile(
        revision=1,
        preferences={
            "adult": True,
            "goal": "general_strength",
            "equipment": "bodyweight",
            "experience": "beginner",
            "days_per_week": 2,
            "session_minutes": 20,
        },
    )
    payloads = {
        "/api/v1/profile": profile.model_dump(),
        "/api/v1/exercises": [r.model_dump() for r in catalog.records()],
        "/api/v1/plans": [],
    }
    report = {
        "version": "async-read-experiment-v1",
        "transport": "in_process_httpx_mock",
        "httpx_version": httpx.__version__,
        "samples_per_mode": 5,
        "delay_seconds_per_read": 0.04,
        "reads_per_trial": 3,
        "catalog_revision": catalog.revision,
        "modes": {},
    }
    reference = None
    for concurrent in (False, True):
        times, counts, peaks = [], [], []
        for _ in range(5):
            active = peak = requests = 0

            async def handler(request):
                nonlocal active, peak, requests
                assert request.method == "GET" and request.url.path in payloads
                requests += 1
                active += 1
                peak = max(peak, active)
                try:
                    await asyncio.sleep(0.04)  # Deliberate benchmark I/O, not a correctness test.
                    return httpx.Response(200, json=payloads[request.url.path])
                finally:
                    active -= 1

            budget, deadline = Budget(), Deadline(SystemClock())
            started = time.perf_counter()
            async with LocalReads(httpx.MockTransport(handler), Principal.A, catalog) as reads:
                async with deadline.scope():
                    result = await read_context(reads, deadline, budget, concurrent=concurrent)
            times.append(round((time.perf_counter() - started) * 1000, 3))
            reference = result if reference is None else reference
            assert result == reference and requests == 3 and active == 0
            assert budget.metrics().tool_dispatches == 3 and budget.metrics().provider_requests == 0
            counts.append(requests)
            peaks.append(peak)
        report["modes"]["concurrent" if concurrent else "sequential"] = {
            "elapsed_ms": times,
            "median_ms": statistics.median(times),
            "requests_per_trial": counts,
            "maximum_inflight_per_trial": peaks,
            "correct_results": 5,
            "retried_requests": 0,
        }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        report = runner.run(measure())
    if args.write_evidence:
        (ROOT / "docs/implementation/evidence/f2-01-async-comparison.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report))
