"""Explicit local experiment commands. Default comparison does not write evidence."""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import time
import uuid
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from spike import AREA, SCENARIOS, GraphRuntime, fixture, offline  # noqa: E402

from future_training.agent.orchestration import State  # noqa: E402
from future_training.agent.protocol import canonical  # noqa: E402
from future_training.identity import Principal  # noqa: E402
from future_training.runtime import loop_factory  # noqa: E402


def clean(path):
    resolved = path.resolve()
    if not resolved.is_relative_to(AREA.resolve()) or resolved.suffix != ".sqlite":
        raise ValueError("Unsafe experiment cleanup")
    for target in (resolved, Path(str(resolved) + "-wal"), Path(str(resolved) + "-shm")):
        target.unlink(missing_ok=True)


async def phase(action, path, scenario="plan"):
    async with GraphRuntime(path, scenario, pause=True) as runtime:
        restored = await runtime.inspect() if action in ("resume", "repeat") else None
        if action != "inspect":
            data = await runtime.invoke(start=action == "start", resume=action == "resume")
        else:
            data = None
        result = await runtime.inspect()
        result["pid"] = os.getpid()
        if restored is not None:
            result["restored_before_execution"] = restored
        if data and data.output_json:
            result["output_sha256"] = hashlib.sha256(
                canonical(json.loads(data.output_json))
            ).hexdigest()
        return result


def demo():
    path = AREA / f"restart-{uuid.uuid4().hex}.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    reports = []
    try:
        for action in ("start", "resume", "repeat"):
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                action,
                "--database",
                path.stem,
            ]
            result = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=25, check=True
            )
            reports.append(json.loads(result.stdout))
        before, after, repeated = reports
        assert before["stage"] == "gate" and before["next"] == ["gate"]
        assert before["metrics"]["provider_requests"] == 1
        assert before["metrics"]["tool_dispatches"] == 1
        assert after["stage"] == repeated["stage"] == "end"
        assert after["metrics"]["provider_requests"] == 2
        assert before["context_sha256"] == after["restored_before_execution"]["context_sha256"]
        assert before["metrics"] == after["restored_before_execution"]["metrics"]
        assert after["metrics"] == repeated["metrics"]
        assert after["output_sha256"] == repeated["output_sha256"]
        assert len({row["pid"] for row in reports}) == 3
        with closing(sqlite3.connect(path)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
            ]
        return {
            "version": "graph-restart-v1",
            "phases": reports,
            "sqlite_integrity": integrity,
            "tables": tables,
            "original_process_exited": True,
            "independent_processes": 3,
            "cleanup": "experiment database and sidecars deleted",
        }
    finally:
        clean(path)


async def compare():
    rows = []
    for scenario in SCENARIOS:
        agent, request = fixture(scenario)
        with offline():
            typed = await agent.generate(Principal.A, request)
        path = AREA / f"compare-{uuid.uuid4().hex}.sqlite"
        try:
            async with GraphRuntime(path, scenario) as runtime:
                graph = await runtime.invoke(start=True)
                inspection = await runtime.inspect()
            left = typed.output().model_dump()
            right = json.loads(graph.output_json)
            equal = canonical(left) == canonical(right)
            metrics_equal = asdict(typed.metrics) == asdict(graph.ledger.restore().metrics())
            assert equal and metrics_equal, (scenario, typed.diagnostic, graph.reason)
            rows.append(
                {
                    "scenario": scenario,
                    "output_equal": equal,
                    "metrics_equal": metrics_equal,
                    "outcome": left["outcome"],
                    "typed_reason": typed.diagnostic,
                    "graph_reason": graph.reason,
                    "metrics": inspection["metrics"],
                    "checkpoint_counts": inspection["tables"],
                    "typed_states": [state.value for state in typed.states],
                    "graph_stages": inspection["history_stages"],
                }
            )
        finally:
            clean(path)
    return rows


async def measure():
    # Same fake plan case, no intentional pauses/delays. Five warmups, 20 samples
    # per mode, alternating pair order. Graph includes opening/setup/closing SQLite.
    samples = {"typed": [], "graph_sqlite": []}
    for index in range(25):
        for mode in ("typed", "graph_sqlite") if index % 2 else ("graph_sqlite", "typed"):
            path = AREA / f"timing-{uuid.uuid4().hex}.sqlite"
            try:
                started = time.perf_counter_ns()
                if mode == "typed":
                    agent, request = fixture("plan")
                    with offline():
                        result = await agent.generate(Principal.A, request)
                    assert result.output().outcome == "plan"
                else:
                    async with GraphRuntime(path) as runtime:
                        result = await runtime.invoke(start=True)
                    assert json.loads(result.output_json)["outcome"] == "plan"
                elapsed = time.perf_counter_ns() - started
                if index >= 5:
                    samples[mode].append(elapsed)
            finally:
                clean(path)
    return {
        "warmup_per_mode": 5,
        "samples_per_mode": 20,
        "scope": (
            "fresh fixture/app agent per trial; graph includes SQLite open/setup/checkpoints/close"
        ),
        "intentional_io_delay": False,
        "failures": 0,
        "modes": {
            mode: {
                "raw_ns": values,
                "median_ms": statistics.median(values) / 1e6,
                "p95_ms": sorted(values)[18] / 1e6,
            }
            for mode, values in samples.items()
        },
    }


async def typed_interruption():
    agent, request = fixture("plan")
    reached = asyncio.Event()
    captured = []
    models = 0

    async def progress(state):
        nonlocal models
        if state is State.MODEL:
            models += 1
            if models == 2:
                reached.set()
                await asyncio.Event().wait()

    async def execute():
        async with agent.session(Principal.A, request, progress=progress) as run:
            captured.append(run)
            await run.execute()

    with offline():
        task = asyncio.create_task(execute())
        try:
            await reached.wait()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        stopped = captured[0]
        assert stopped.closed and stopped.states[-1] is State.CANCELLED
        try:
            await stopped.execute()
        except RuntimeError:
            pass
        else:
            raise AssertionError("Closed typed run resumed")
        restarted = await agent.generate(Principal.A, request)
    return {
        "cancelled_metrics": asdict(stopped.budget.metrics()),
        "closed_run_rejected": True,
        "new_request_metrics": asdict(restarted.metrics),
        "new_request_outcome": restarted.output().outcome,
        "meaning": "new explicit request; no checkpoint or resumption in typed application",
    }


def provenance():
    paths = [
        ROOT / "experiments/langgraph" / name
        for name in (
            "spike.py",
            "run.py",
            "pyproject.toml",
            "uv.lock",
            "tests/conftest.py",
            "tests/test_spike.py",
        )
    ]
    return {
        "experiment_sources": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(
                path.read_text(encoding="utf-8").encode()
            ).hexdigest()
            for path in paths
        },
        "application_locks": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("uv.lock", "web/package-lock.json")
        },
        "physical_source_lines": {
            str(path.relative_to(ROOT)).replace("\\", "/"): len(
                path.read_text(encoding="utf-8").splitlines()
            )
            for path in paths
            if path.suffix == ".py"
        },
        "typed_orchestration_lines": len(
            (ROOT / "src/future_training/agent/orchestration.py").read_text().splitlines()
        ),
    }


def versions():
    return {dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=("start", "resume", "repeat", "inspect", "cleanup", "demo", "compare")
    )
    parser.add_argument("--database", default="manual-demo")
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9-]{1,64}", args.database):
        parser.error("Database must be a bounded experiment name")
    if args.action == "cleanup":
        clean(AREA / f"{args.database}.sqlite")
        report = {"cleanup": "experiment database and sidecars deleted"}
    elif args.action == "demo":
        report = demo()
    else:
        with asyncio.Runner(loop_factory=loop_factory) as runner:
            if args.action == "compare":

                async def comparisons():
                    return {
                        "cases": await compare(),
                        "typed_interruption": await typed_interruption(),
                        "timing": await measure(),
                        "dependencies": versions(),
                        "python": sys.version.split()[0],
                        "provenance": provenance(),
                    }

                report = runner.run(comparisons())
            else:
                report = runner.run(phase(args.action, AREA / f"{args.database}.sqlite"))
    if args.write_evidence:
        if args.action not in ("demo", "compare"):
            parser.error("Evidence export permits only bounded demo/comparison reports")
        output = ROOT / f"docs/implementation/evidence/f2-03-{args.action}.json"
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
