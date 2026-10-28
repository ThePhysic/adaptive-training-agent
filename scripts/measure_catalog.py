"""Offline catalog profiling; writes new evidence only with an explicit flag."""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from future_training.experiments.catalog_performance import (  # noqa: E402
    baseline,
    comparison,
    distribution,
    profile_comparison,
)
from future_training.runtime import loop_factory  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--write-comparison", action="store_true")
    parser.add_argument("--api", action="store_true")
    parser.add_argument("--write-api", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--write-profile", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    if args.manifest:
        paths = [
            ROOT / "scripts/measure_catalog.py",
            *sorted((ROOT / "src/future_training/experiments").glob("catalog_*.py")),
        ]
        artifacts = sorted((ROOT / "docs/implementation/evidence").glob("f2-02-*.json"))
        manifest = {
            "version": "catalog-measurement-manifest-v1",
            "environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "processor": platform.processor(),
                "logical_cpus": os.cpu_count(),
                "dependencies": {
                    name: importlib.metadata.version(name)
                    for name in (
                        "pydantic",
                        "fastapi",
                        "httpx",
                        "psycopg",
                        "uvicorn",
                        "pytest",
                        "ruff",
                    )
                },
            },
            "reproduction_sources": {
                p.relative_to(ROOT).as_posix(): hashlib.sha256(
                    p.read_text(encoding="utf-8").encode()
                ).hexdigest()
                for p in paths
            },
            "artifacts": {
                p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in artifacts
                if p.name != "f2-02-measurement-manifest.json"
            },
            "locks": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in ("uv.lock", "web/package-lock.json")
            },
            "note": (
                "Final reproduction-source hashes; initial baseline preceded prototype code. "
                "Timings vary, frozen F1 hashes do not."
            ),
        }
        (ROOT / "docs/implementation/evidence/f2-02-measurement-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(manifest["environment"]))
        raise SystemExit(0)
    if args.profile:
        report = profile_comparison()
        if args.write_profile:
            (ROOT / "docs/implementation/evidence/f2-02-cpu-profile.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        print(
            json.dumps({mode: report[mode]["catalog_functions"] for mode in ("uncached", "warm")})
        )
        raise SystemExit(0)
    if args.api:
        from future_training.experiments.catalog_api_measure import api_comparison

        with asyncio.Runner(loop_factory=loop_factory) as runner:
            report = runner.run(api_comparison())
        if args.write_api:
            (ROOT / "docs/implementation/evidence/f2-02-native-api-comparison.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        print(
            json.dumps(
                {
                    "phase": report["phase"],
                    "approved_rows": report["approved_rows"],
                    "modes": {
                        f"{mode}-{clients}": distribution(
                            [
                                value
                                for row in report["results"]
                                if row["mode"] == mode and row["clients"] == clients
                                for value in row["raw_elapsed_ns"]
                            ]
                        )
                        for mode in ("uncached", "cold", "warm")
                        for clients in (1, 2)
                    },
                    "failures": sum(row["failure_count"] for row in report["results"]),
                }
            )
        )
        raise SystemExit(1 if any(row["failure_count"] for row in report["results"]) else 0)
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        report = runner.run(comparison() if args.compare else baseline())
    if args.compare:
        if args.write_comparison:
            (ROOT / "docs/implementation/evidence/f2-02-cache-comparison.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        print(
            json.dumps(
                {
                    "phase": report["phase"],
                    "equivalence": report["equivalence"],
                    "resident_cache": report["resident_cache"],
                    "operations": {
                        name: {
                            f"{mode}-{clients}": distribution(
                                [
                                    value
                                    for row in rows
                                    if row["mode"] == mode and row["clients"] == clients
                                    for value in row["raw_service_ns"]
                                ]
                            )
                            for mode in ("uncached", "cold", "warm")
                            for clients in (1, 2)
                        }
                        for name, rows in report["operations"].items()
                    },
                }
            )
        )
        raise SystemExit(
            1
            if any(r["failure_count"] for rows in report["operations"].values() for r in rows)
            else 0
        )
    if args.write_baseline:
        (ROOT / "docs/implementation/evidence/f2-02-uncached-baseline.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "phase": report["phase"],
                "cases": len(report["case_ids"]),
                "startup_load": report["startup_load"]["distribution"],
                "operations": {
                    name: [
                        {
                            "clients": r["clients"],
                            "samples": r["samples"],
                            "failure_count": r["failure_count"],
                            "outcomes": r["outcomes"],
                            "service": r["service"],
                            "elapsed": r["elapsed"],
                        }
                        for r in rows
                    ]
                    for name, rows in report["operations"].items()
                },
                "profile_catalog": report["cpu_profile"]["catalog_functions"],
            }
        )
    )
    raise SystemExit(
        1
        if any(row["failure_count"] for rows in report["operations"].values() for row in rows)
        else 0
    )
