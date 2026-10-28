"""Real 20-record catalog workloads, unprofiled latency and separate CPU attribution.

Offline measurement only. No synthetic I/O delay or application cache installation.
"""

import asyncio
import cProfile
import math
import platform
import pstats
import sys
import time
from collections import Counter
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from future_training.agent.protocol import ToolCall
from future_training.agent.tools import ReadTools
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import Catalog, load_catalog
from future_training.domain.validator import validate_plan
from future_training.experiments.catalog_cache import CachedCatalog, ProjectionCache
from future_training.identity import Principal
from future_training.schemas import ProfilePreferences, SavedProfile

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Case:
    case_id: str
    profile: ProfilePreferences


def workload(catalog: Catalog) -> tuple[Case, ...]:
    cases = []
    for row, (goal, equipment, experience) in enumerate(
        product(
            ("general_strength", "general_conditioning"),
            ("bodyweight", "dumbbells_and_bodyweight"),
            ("beginner", "intermediate"),
        )
    ):
        base = ProfilePreferences(
            adult=True,
            goal=goal,
            equipment=equipment,
            experience=experience,
            days_per_week=2,
            session_minutes=20,
        )
        eligible = catalog.eligible(base)
        tags = Counter(tag for record in eligible for tag in record.exclusion_tags)
        tag = min(tags, key=lambda value: (tags[value], value))
        for minutes, days, variant in product(
            (20, 30, 45), (2, 3, 4), ("none", "one_id", "one_tag")
        ):
            profile = base.model_copy(
                update={
                    "session_minutes": minutes,
                    "days_per_week": days,
                    "excluded_ids": [eligible[0].exercise_id] if variant == "one_id" else [],
                    "excluded_tags": [tag] if variant == "one_tag" else [],
                }
            )
            cases.append(Case(f"row-{row}-m{minutes}-d{days}-{variant}", profile))
    return tuple(cases)


def distribution(samples):
    values = sorted(samples)
    return {
        "count": len(values),
        **{
            name: values[max(0, math.ceil(q * len(values)) - 1)]
            for name, q in (("p50_ns", 0.50), ("p95_ns", 0.95), ("p99_ns", 0.99))
        },
        "min_ns": values[0],
        "max_ns": values[-1],
    }


async def timed(operation, count, clients):
    elapsed, service = [0] * count, [0] * count
    outcomes, failures = ["failed"] * count, [None] * count
    started = time.perf_counter_ns()

    async def worker(client):
        for index in range(client, count, clients):
            arrival = time.perf_counter_ns()
            await asyncio.sleep(0)  # Cooperative dispatch boundary; no simulated I/O delay.
            invoked = time.perf_counter_ns()
            try:
                outcomes[index] = await operation(index)
            except Exception:
                failures[index] = "operation_failed"
            finished = time.perf_counter_ns()
            service[index], elapsed[index] = finished - invoked, finished - arrival

    async with asyncio.TaskGroup() as tasks:
        for client in range(clients):
            tasks.create_task(worker(client))
    return {
        "clients": clients,
        "samples": count,
        "failure_count": sum(v is not None for v in failures),
        "failure_indices": [i for i, value in enumerate(failures) if value],
        "outcomes": dict(Counter(outcomes)),
        "wall_ns": time.perf_counter_ns() - started,
        "elapsed": distribution(elapsed),
        "service": distribution(service),
        "raw_elapsed_ns": elapsed,
        "raw_service_ns": service,
    }


class Operations:
    def __init__(self, catalog: Catalog, cases: tuple[Case, ...]):
        self.catalog, self.cases = catalog, cases
        # Validator input fixtures, never an application plan cache. Every timed
        # planning invocation below still computes its own result.
        fixtures = [plan_week(case.profile, catalog) for case in cases]
        self.validation = [
            (case, result.plan)
            for case, result in zip(cases, fixtures, strict=True)
            if result.plan is not None
        ]
        self.expected_outcomes = [value.outcome for value in fixtures]
        self.tools = ReadTools(None, catalog)  # search_exercises never reads profile service.
        self.call = ToolCall(
            call_id="catalog-measurement", name="search_exercises", arguments_json='{"limit":20}'
        )

    async def records(self, index):
        records = self.catalog.records()
        if len(records) != 20:
            raise ValueError("Expected frozen seed")
        return "ok"

    async def eligible(self, index):
        case = self.cases[index % len(self.cases)]
        values = self.catalog.eligible(case.profile)
        if len({r.exercise_id for r in values}) != len(values):
            raise ValueError("Duplicate eligibility result")
        return "ok"

    async def validation_run(self, index):
        case, plan = self.validation[index % len(self.validation)]
        if not validate_plan(plan, case.profile, self.catalog).valid:
            raise ValueError("Invalid fixture result")
        return "valid"

    async def planning(self, index):
        position = index % len(self.cases)
        case = self.cases[position]
        result = plan_week(case.profile, self.catalog)
        if result.outcome != self.expected_outcomes[position]:
            raise ValueError("Outcome changed")
        return result.outcome

    async def tool_roundtrip(self, index):
        case = self.cases[index % len(self.cases)]
        profile = SavedProfile(revision=1, preferences=case.profile)
        result = await self.tools.dispatch(Principal.A, profile, self.call)
        self.tools.checked_bytes(profile, self.call, result)
        return result.status

    async def pipeline(self, index):
        await self.tool_roundtrip(index)
        position = index % len(self.cases)
        case = self.cases[position]
        result = plan_week(case.profile, self.catalog)
        if result.outcome != self.expected_outcomes[position] or result.plan is None:
            raise ValueError("Changed pipeline outcome")
        if not validate_plan(result.plan, case.profile, self.catalog).valid:
            raise ValueError("Changed independent validation")
        return "valid"


def cpu_profile(operations):
    profiler = cProfile.Profile()
    profiler.enable()
    for case in operations.cases:
        result = plan_week(case.profile, operations.catalog)
        if result.plan:
            validate_plan(result.plan, case.profile, operations.catalog)
    profiler.disable()
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line, function), (primitive, calls, own, cumulative, _) in stats.stats.items():
        path = Path(filename)
        name = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name
        rows.append(
            {
                "file": name,
                "line": line,
                "function": function,
                "calls": calls,
                "primitive_calls": primitive,
                "own_seconds": own,
                "cumulative_seconds": cumulative,
            }
        )
    rows.sort(key=lambda row: row["cumulative_seconds"], reverse=True)
    return {
        "workload": "216 planning calls plus independent revalidation of returned plans",
        "total_calls": stats.total_calls,
        "total_seconds": stats.total_tt,
        "top_cumulative": rows[:30],
        "catalog_functions": [r for r in rows if r["file"].endswith("domain/catalog.py")],
    }


async def baseline(rounds=5):
    catalog = load_catalog()
    cases = workload(catalog)
    operations = Operations(catalog, cases)
    report = {
        "version": "catalog-performance-v1",
        "phase": "uncached_baseline",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "clock": "perf_counter_ns",
        "percentiles": "nearest rank, inclusive failures",
        "catalog_revision": catalog.revision,
        "catalog_fingerprint": catalog.fingerprint(),
        "catalog_records": len(catalog.ids),
        "rounds": rounds,
        "case_ids": [c.case_id for c in cases],
        "validation_case_ids": [c.case_id for c, _ in operations.validation],
        "warmup": (
            "one full case sweep per operation; all four existing arithmetic option entries primed"
        ),
        "concurrency": (
            "one event loop; 1/2 logical clients, sleep(0) dispatch boundary; no I/O delay"
        ),
        "operations": {},
    }
    startup = []
    for _ in range(5):
        load_catalog()
    for _ in range(100):
        started = time.perf_counter_ns()
        load_catalog()
        startup.append(time.perf_counter_ns() - started)
    report["startup_load"] = {
        "samples": 100,
        "warmup_calls": 5,
        "distribution": distribution(startup),
        "raw_ns": startup,
        "note": "Repeated startup loads with OS filesystem cache; not cold disk or request path",
    }
    for name in ("records", "eligible", "validation_run", "planning", "tool_roundtrip"):
        operation = getattr(operations, name)
        size = len(operations.validation) if name == "validation_run" else len(cases)
        for index in range(size):
            await operation(index)
        report["operations"][name] = [
            await timed(operation, size * rounds, clients) for clients in (1, 2)
        ]
    report["cpu_profile"] = cpu_profile(operations)
    return report


def profile_comparison():
    source = load_catalog()
    cases = workload(source)
    uncached = Operations(source, cases)
    cache = ProjectionCache()
    warm = Operations(CachedCatalog(source, cache), cases)
    return {
        "version": "catalog-cpu-profile-v1",
        "note": "instrumented CPU, not latency samples",
        "uncached": cpu_profile(uncached),
        "warm": cpu_profile(warm),
    }


async def comparison(rounds=5):
    source = load_catalog()
    cases = workload(source)
    Operations(source, cases)  # Prime existing arithmetic options before mode rotation.
    report = {
        "version": "catalog-performance-v1",
        "phase": "isolated_cache_comparison",
        "catalog_revision": source.revision,
        "catalog_fingerprint": source.fingerprint(),
        "rounds": rounds,
        "case_ids": [c.case_id for c in cases],
        "mode_order": "rotate uncached/cold/warm by round; same case order; 1 then 2 clients",
        "cold": (
            "clear projection entries inside each logical operation; "
            "source binding already initialized"
        ),
        "warm": "prefill all eight common projections before each pass",
        "scope": "prototype only, not application composition; same authoritative validation",
        "bounds": {"entries": 8, "logical_bytes": 65536},
        "construction_ns": [],
        "operations": {},
    }
    modes = ("uncached", "cold", "warm")
    for name in ("eligible", "planning", "tool_roundtrip", "pipeline"):
        results = []
        for clients in (1, 2):
            for round_index in range(rounds):
                for offset in range(3):
                    mode = modes[(round_index + offset) % 3]
                    cache = ProjectionCache()
                    constructed = time.perf_counter_ns()
                    catalog = source if mode == "uncached" else CachedCatalog(source, cache)
                    if mode != "uncached":
                        report["construction_ns"].append(time.perf_counter_ns() - constructed)
                    operations = Operations(catalog, cases)
                    operation = getattr(operations, name)
                    # Same warm-up count and original F1 arithmetic prewarming in all modes.
                    for index in range(len(cases)):
                        await operation(index)
                    if mode == "cold":
                        cache.clear()
                    before = cache.stats()

                    async def invoke(index, mode=mode, cache=cache, operation=operation):
                        if mode == "cold":
                            cache.clear()
                        return await operation(index)

                    row = await timed(invoke, len(cases), clients)
                    row.update(
                        {
                            "mode": mode,
                            "round": round_index,
                            "cache": cache.stats(),
                            "cache_delta": {
                                k: cache.stats()[k] - before[k]
                                for k in ("hits", "misses", "evictions", "bypasses")
                            },
                        }
                    )
                    results.append(row)
        report["operations"][name] = results
    # Semantic equality is measured independently of time and covers exclusions,
    # all day/preset combinations, plans and authoritative validation.
    cache = ProjectionCache()
    view = CachedCatalog(source, cache)
    checks = {"eligibility": 0, "plans": 0, "validation": 0}
    for case in cases:
        if source.eligible(case.profile) != view.eligible(case.profile):
            raise ValueError("Eligibility differs")
        checks["eligibility"] += 1
        left, right = plan_week(case.profile, source), plan_week(case.profile, view)
        if left != right:
            raise ValueError("Plan differs")
        checks["plans"] += 1
        if validate_plan(left.plan, case.profile, source) != validate_plan(
            right.plan, case.profile, view
        ):
            raise ValueError("Validation differs")
        checks["validation"] += 1
    report["equivalence"] = checks
    report["resident_cache"] = cache.stats()
    return report
