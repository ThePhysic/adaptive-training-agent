"""Opt-in actual API/fake-provider/native SQL benchmark in one disposable schema."""

import asyncio
import hashlib
import json
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from future_training.api import create_app
from future_training.candidates import encode_snapshot
from future_training.config import Settings
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.domain.validator import validate_plan
from future_training.experiments.catalog_cache import CachedCatalog, ProjectionCache
from future_training.experiments.catalog_performance import distribution, workload
from future_training.persistence.profiles import LOCAL_DSN, PostgresProfiles
from future_training.schemas import PlanProposal

ROOT = Path(__file__).resolve().parents[3]


@contextmanager
def isolated_database():
    name = "f202_perf_" + uuid4().hex
    with psycopg.connect(LOCAL_DSN) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        connection.execute(sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(name)))
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            connection.execute(path.read_text(encoding="utf-8"))
    dsn = make_conninfo(
        LOCAL_DSN, options=f"-c search_path={name} -c statement_timeout=5000 -c lock_timeout=2000"
    )

    async def connect():
        return await psycopg.AsyncConnection.connect(dsn)

    try:
        yield connect
    finally:
        with psycopg.connect(LOCAL_DSN) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(name)))


async def api_comparison(rounds=5):
    source = load_catalog()
    full = workload(source)
    cases = tuple(full[row * 27 + offset] for offset in (0, 13, 26) for row in range(8))
    # Equalize the pre-existing four-entry arithmetic memo before the first
    # measured mode, including both conditioning experience bands.
    for case in cases[:8]:
        if plan_week(case.profile, source).plan is None:
            raise RuntimeError("Unsupported benchmark fixture")
    report = {
        "version": "catalog-api-performance-v1",
        "phase": "native_api_comparison",
        "transport": "ASGITransport, actual PostgreSQL, deterministic fake model",
        "rounds": rounds,
        "catalog_revision": source.revision,
        "catalog_fingerprint": source.fingerprint(),
        "case_ids": [case.case_id for case in cases],
        "warmup": (
            "eight untimed baseline plans prime all four arithmetic entries; "
            "two untimed generations per app episode; common keys primed for warm mode"
        ),
        "cold": "clear once before each 1/2-request wave; peer cold requests may share fills",
        "ordering": "rotate modes each round; one API process, 1/2 admitted synthetic principals",
        "timing": (
            "generation POST including terminal delivery; explicit profile Save outside timer"
        ),
        "results": [],
    }
    revisions = {"synthetic-a": 0, "synthetic-b": 0}
    with isolated_database() as connect:
        repository = PostgresProfiles(source, connect=connect)
        for clients in (1, 2):
            for round_index in range(rounds):
                for offset in range(3):
                    mode = ("uncached", "cold", "warm")[(round_index + offset) % 3]
                    cache = ProjectionCache()
                    catalog = source if mode == "uncached" else CachedCatalog(source, cache)
                    # Experiment-only composition substitution. No production factory,
                    # API route or deployment switch is added for this prototype.
                    with patch("future_training.api.load_catalog", return_value=catalog):
                        app = create_app(
                            settings=Settings(local_development="1"), profiles=repository
                        )
                    elapsed, failures, outcomes = [], [], []
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app),
                        base_url="http://127.0.0.1:8000",
                        trust_env=False,
                    ) as client:

                        async def save(case, principal):
                            response = await client.put(
                                "/api/v1/profile",
                                headers={"X-Synthetic-Principal": principal},
                                json={
                                    "expected_revision": revisions[principal],
                                    "preferences": case.profile.model_dump(),
                                },
                            )
                            if response.status_code != 200:
                                raise RuntimeError("Benchmark setup Save failed")
                            revisions[principal] = response.json()["revision"]

                        async def generate(case, principal):
                            started = time.perf_counter_ns()
                            response = await client.post(
                                "/api/v1/drafts/stream",
                                headers={"X-Synthetic-Principal": principal},
                                json={"profile_revision": revisions[principal]},
                            )
                            duration = time.perf_counter_ns() - started
                            try:
                                if response.status_code != 200:
                                    raise ValueError("HTTP generation failed")
                                events = [
                                    json.loads(frame.split("\ndata: ")[1])
                                    for frame in response.text.strip().split("\n\n")
                                ]
                                done = events[-1]["payload"]
                                proposal = PlanProposal.model_validate(
                                    next(e["payload"] for e in events if e["event_type"] == "draft")
                                )
                                if (
                                    done["outcome"] != "plan"
                                    or not validate_plan(proposal, case.profile, source).valid
                                    or hashlib.sha256(encode_snapshot(proposal)).hexdigest()
                                    != done["candidate"]["content_hash"]
                                ):
                                    raise ValueError("Non-equivalent generation")
                                return duration, None, "plan"
                            except Exception:
                                return duration, "generation_failed", "error"

                        # Warm app routing, native SQL and model/validator code outside timing.
                        for case in cases[:2]:
                            await save(case, "synthetic-a")
                            if (await generate(case, "synthetic-a"))[1] is not None:
                                raise RuntimeError("Benchmark warmup failed")
                        if mode == "warm":
                            for case in cases:
                                catalog.eligible(case.profile)
                        before = cache.stats()
                        for position in range(0, len(cases), clients):
                            wave = cases[position : position + clients]
                            principals = ("synthetic-a", "synthetic-b")[: len(wave)]
                            async with asyncio.TaskGroup() as tasks:
                                for case, principal in zip(wave, principals, strict=True):
                                    tasks.create_task(save(case, principal))
                            if mode == "cold":
                                cache.clear()
                            async with asyncio.TaskGroup() as tasks:
                                reads = [
                                    tasks.create_task(generate(case, principal))
                                    for case, principal in zip(wave, principals, strict=True)
                                ]
                            for task in reads:
                                duration, failure, outcome = task.result()
                                elapsed.append(duration)
                                failures.append(failure)
                                outcomes.append(outcome)
                    report["results"].append(
                        {
                            "mode": mode,
                            "clients": clients,
                            "round": round_index,
                            "samples": len(elapsed),
                            "raw_elapsed_ns": elapsed,
                            "latency": distribution(elapsed),
                            "failure_count": sum(value is not None for value in failures),
                            "outcomes": outcomes,
                            "cache": cache.stats(),
                            "cache_delta": {
                                key: cache.stats()[key] - before[key]
                                for key in ("hits", "misses", "evictions", "bypasses")
                            },
                        }
                    )
        async with await connect() as connection:
            result = await connection.execute("SELECT count(*) FROM approved_plans")
            report["approved_rows"] = (await result.fetchone())[0]
    report["fixture_cleanup"] = "isolated schema dropped"
    return report
