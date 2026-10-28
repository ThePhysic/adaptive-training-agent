# F2-02 handoff — Bounded Caching and Performance

Date: 2026-10-24. Status: completed for owner review; F2-03 has not begun.

## Outcome and architectural decision

**Retain the uncached application.** The catalog is already loaded once into
immutable canonical bytes. Repeated parsing/filtering exists, but a bounded
projection prototype saved only 0.2062 ms at the median of the measured component
pipeline. Actual API measurements did not establish a consistent improvement.
The prototype remains exclusively in `future_training.experiments`; no runtime
factory, endpoint, deployment switch, dependency or application cache was added.

The [pre-optimization audit](f2-02-catalog-audit.md) identifies the repeated work
and measurement plan. The [cache decision](f2-02-cache-decision.md) records the
tradeoff and conditions for reconsideration. Rejecting adoption is the measured
F2-02 result, rather than an incomplete cache integration.

## Changed files

| Files | Purpose |
| --- | --- |
| `src/future_training/experiments/catalog_cache.py` | Off-path bounded LRU projection prototype; delegates authoritative validation inputs to the original catalog |
| `src/future_training/experiments/catalog_performance.py` | Reproducible workload, raw timing distributions, component comparison and separate CPU profiles |
| `src/future_training/experiments/catalog_api_measure.py` | Opt-in actual ASGI generation comparison using native isolated PostgreSQL and the existing fake provider |
| `scripts/measure_catalog.py` | Explicit measurement/evidence commands and source/artifact/lock manifest |
| `tests/test_catalog_cache_experiment.py` | 26 routine correctness, capacity, invalidation, concurrency and measurement tests |
| `web/scripts/browser-smoke.mjs` | Allows the `f2-02` screenshot prefix; existing product workflow/assertions preserved |
| `README.md`, `docs/development.md`, `docs/runbook.md` | Current status, commands and measured decision |
| `docs/implementation/f2-02-catalog-audit.md`, `f2-02-cache-decision.md`, this handoff | Audit, decision and review evidence |
| `docs/implementation/evidence/f2-02-*.json`, `f2-02-*.png` | Four raw reports, manifest and three new browser screenshots, linked below |

No migrations, domain rules, evaluation inputs/results, generated API artifacts,
dependency manifests/locks or historical review/handoff evidence were changed.
The existing check runner already discovers the new tests; it was not modified.

## Audit and measurement methodology

The 20-record seed has eight supported goal/equipment/experience rows. Application
construction loads it once; there is no per-generation catalog disk, SQL or network
read. `records()` materializes fresh models; `eligible()` filters and sorts those
models. Tool dispatch and its independent result checking repeat eligibility;
planning does so again. Independent plan validation resolves exercises with
`Catalog.get()` and must continue to do so. The existing four-entry arithmetic
options memo is retained, with all four entries equally warmed before comparison.

The component workload has **216 cases**: eight supported rows × three duration
presets (20/30/45 minutes) × three day counts (2/3/4) × three exclusions (none,
one eligible ID, one least-frequent eligible tag with lexical tie-breaking).
All 216 are feasible plans for this seed. Existing frozen evaluation and tests
separately preserve clarification, abstention, invalid and infeasible cases; the
performance workload does not represent their distribution.

Each component mode uses the same cases, 216 unmeasured warm-up operations and
five measured rounds, at one and two logical clients on one cooperative event
loop. Mode order rotates per round. Raw service time excludes the scheduling
boundary; elapsed time includes it. `asyncio.sleep(0)` permits cooperative
dispatch without an injected I/O delay. These CPU operations do not run in
parallel on two cores. No throughput scaling claim follows from two-client data.

Durations use monotonic integer `perf_counter_ns`; distributions use nearest-rank
p50/p95/p99, with every failed sample retained in the denominator. Timing does
not run under cProfile. Separate cProfile reports attribute calls and cumulative
time; nested cumulative times overlap and cannot be added. The Python references
for this distinction are [profiling](https://docs.python.org/3.14/library/profile.html)
and [the performance clock](https://docs.python.org/3.14/library/time.html#time.perf_counter_ns).

The first baseline was collected before the prototype was written. Startup-load
measurement uses five warm-ups and 100 samples, with the OS file cache warm; it
is neither per-request work nor a cold-disk benchmark. Component fixtures retain
plans solely as validation test inputs outside timing. Every timed planning call
recomputes its plan; there is no personalized plan cache.

## Raw measurements and interpretation

All reports contain raw nanosecond samples, case identifiers, settings,
distributions and failure counts:

- [Initial uncached baseline](evidence/f2-02-uncached-baseline.json): 10,800 measured component calls, zero failures.
- [Three-mode component comparison](evidence/f2-02-cache-comparison.json): 25,920 measured calls, zero failures; 216 eligibility, 216 full-plan and 216 independent-validation equivalence comparisons all equal.
- [Native API comparison](evidence/f2-02-native-api-comparison.json): 720 measured generation requests, zero failures; 120 samples per mode/client level.
- [Separate CPU profiles](evidence/f2-02-cpu-profile.json): top cumulative functions and catalog call statistics for 216 plans plus independent revalidation per mode.
- [Environment and hash manifest](evidence/f2-02-measurement-manifest.json): final reproduction-source hashes, raw-report hashes and unchanged lock hashes. These are final reproduction sources, not a claim that the prototype existed during the initial baseline.

Initial uncached one-client **service** times in milliseconds:

| Operation | Samples | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| Records | 1,080 | 0.0982 | 0.2154 | 0.3877 |
| Eligibility | 1,080 | 0.1102 | 0.2232 | 0.4121 |
| Independent validation | 1,080 | 0.2081 | 0.4665 | 0.6812 |
| Planning | 1,080 | 0.7549 | 1.4026 | 1.9743 |
| Tool dispatch and result checking | 1,080 | 0.5805 | 1.0478 | 1.4094 |

The same five operations each have 1,080 additional two-client samples, giving
10,800 total. Initial source loading had p50/p95 0.8125/1.4336 ms, outside request
work. Eligibility elapsed p50/p95 was 0.1171/0.2446 ms with one client and
0.2314/0.4070 ms with two, illustrating cooperative scheduling wait.

Comparison one-client **service** times, milliseconds (p50 / p95 / p99):

| Operation | Uncached | Cold cache | Warm cache |
| --- | --- | --- | --- |
| Eligibility | 0.1101 / 0.2177 / 0.3287 | 0.5858 / 1.0165 / 1.4115 | 0.0657 / 0.1552 / 0.2714 |
| Planning | 0.7530 / 1.3999 / 1.7760 | 1.2936 / 2.1543 / 2.6364 | 0.6665 / 1.3564 / 1.8859 |
| Tool + result checking | 0.6287 / 1.1707 / 1.5807 | 1.0832 / 1.8788 / 2.6735 | 0.4995 / 0.9119 / 1.1639 |
| Tool + planner + independent validator | 1.6877 / 2.6803 / 3.4054 | 2.1657 / 3.3356 / 3.9225 | 1.4815 / 2.3632 / 2.9794 |

Each cell contains 1,080 samples; four operations × three modes × two client
levels gives 25,920 calls. Cold mode clears entries before each logical operation;
multiple eligibility reads inside the tool/pipeline may then hit. Warm mode
preloads all eight common keys. Binding the immutable source fingerprint has
separately measured p50 cost 0.3889 ms outside hot-operation timings. The warm
pipeline saves 0.2062 ms (about 12.2%); cold pipeline costs 0.4780 ms more.

The separate CPU comparison retains **6,480 authoritative `Catalog.get()` calls
in both modes**. Warm eligibility cumulative time falls from 0.0388 to 0.0192 s
in that instrumented run, without bypassing independent validation. It is not
an uninstrumented latency or whole-application speedup.

### Actual API comparison

This experiment uses the actual application, real native SQL, synthetic local
identity, existing fake provider, domain validation, SSE terminalization and
candidate publication. A unique `f202_perf_<uuid>` schema receives all existing
migrations and is dropped in `finally`. A temporary benchmark-only patch supplies
the original/prototype catalog during synchronous app construction; there is no
runtime configuration switch. No approval is performed: approved rows remain zero.

The 24 representative profiles select offsets 0/13/26 from each row: 20-minute,
two-day/no-exclusion; 30-minute, three-day/one-ID; 45-minute, four-day/one-tag.
Eight unmeasured baseline plans prime **all four** existing arithmetic memo
entries before the first episode. Each of 30 app episodes has two additional
unmeasured generation warm-ups. Five rotated rounds × three modes × two client
levels × 24 measured generations yields **720 measured + 60 warm-up generations**.
Profile Save occurs before each generation, outside its timer. Concurrent waves
use two different principals, obey one generation per principal and two globally,
and complete profile Saves first. Each app holds only 26 candidates, below its
existing capacity. No admission or request budget is increased.

Cold mode clears once per request wave; a second concurrent request may share a
fill. Warm mode primes all eight keys. Each response is checked for complete
terminal plan delivery, source validation and matching content hash. This uses
HTTPX ASGI transport, which buffers output; it measures application + SQL locally,
not TCP/TLS delivery, browser latency or live-model quality.

| Clients | Mode | p50 ms | p95 ms | p99 ms |
| ---: | --- | ---: | ---: | ---: |
| 1 | Uncached | 90.1471 | 123.3156 | 137.2257 |
| 1 | Cold | 90.4995 | 126.3248 | 136.4220 |
| 1 | Warm | 91.5188 | 132.3133 | 144.2406 |
| 2 | Uncached | 129.9028 | 168.3681 | 172.5848 |
| 2 | Cold | 134.1728 | 193.0230 | 207.5654 |
| 2 | Warm | 130.9242 | 167.6164 | 197.8823 |

Warm-minus-uncached paired round medians (ms) were
`[1.3728, -4.5013, 1.9235, 0.1594, 2.3561]` with one client and
`[-11.5892, -0.7934, 19.8253, -4.1878, 25.9151]` with two. Warm was faster
in only 1/5 and 3/5 rounds respectively; pooled medians were slightly slower.
This does not demonstrate a consistent API benefit. An earlier API setup warmed
only one goal's arithmetic options; that imbalance was identified and corrected.
The saved API artifact and all values above are from the corrected rerun with
equal prewarming. The superseded run is not acceptance evidence.

## Prototype bounds and correctness evidence

The exact key is
`(catalog-projection-v1, catalog_revision, full_content_sha256, goal, equipment, experience)`.
It retains only common **unexcluded catalog metadata**, derived by the original
`Catalog.eligible()` from a supported neutral profile. Days and duration do not
affect that projection. Exclusions are deliberately absent from retained keys and
values and reapplied by original eligibility on every call. Tool-specific tag,
equipment and limit filters are applied afresh outside the cache; conflicting
goal filters retain their original error. No profile object, user ID, candidate,
generated plan, validation result, approval decision, history or idempotency
response is cached.

Default limits are eight entries and 65,536 **logical payload bytes**; construction
hard caps are 32 entries and 1,048,576 bytes. Logical cost is serialized key bytes
plus canonical projected record JSON bytes. This excludes Python object overhead,
RSS and the existing source reference. Filling all eight keys retains 37,264
logical bytes, duplicating metadata already available in the source. No physical
memory cap is claimed.

Hits update LRU order; insertion evicts until both bounds hold. An oversize entry
is computed but bypasses retention. Explicit clear releases entries/byte counts;
diagnostic counters are lifetime counters. There is no TTL, sweep or background
service. The source is process-lifetime immutable under the existing contract.
A newly bound source uses its revision **and content digest**, preventing reuse
even if a changed catalog accidentally retains its revision label. Older immutable
entries may remain within bounds until eviction/clear. In-place catalog mutation
is unsupported by the accepted source contract.

The 26 new routine tests cover:

- All 216 supported workload cases: exact eligibility, complete planner result and independent validation equality; one shared entry per matrix row.
- Fresh returned models: mutating titles/tags cannot contaminate subsequent calls; weak references establish no request-profile retention.
- New revision and same-label changed-content invalidation, explicit clear, LRU touch, entry and byte pressure, oversize bypass and invalid bounds.
- Two barrier-gated cooperative clients with different exclusions, 100 calls each: one miss, 199 hits, one common entry, equivalent isolated results throughout.
- A mutated plan duration is rejected after an earlier successful validation; validation does not change cache statistics. Source lookups remain authoritative.
- Four actual tool filter/conflict cases, including independent result checking; unchanged uncached application composition.
- Exact percentile calculation, failure-denominator preservation and sanitized failure reporting.

Cache access/build/publication is synchronous and cannot suspend midway in the
supported single event loop. No thread safety, multiworker or distributed
correctness is claimed. Routine correctness tests use assertions/barriers, not
wall-clock performance thresholds. Timing runs are explicit local experiments.

## Commands and observed checks

All commands ran at repository root using installed, supported dependencies.
No dependency installation, image pull, hosted CI dispatch or live API call was
performed. The cached PostgreSQL image was started with:

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/measure_catalog.py --write-baseline
.venv/Scripts/python.exe scripts/measure_catalog.py --compare --write-comparison
.venv/Scripts/python.exe scripts/measure_catalog.py --api --write-api
.venv/Scripts/python.exe scripts/measure_catalog.py --profile --write-profile
.venv/Scripts/python.exe scripts/measure_catalog.py --manifest
```

Every command exited zero. The API command was rerun after the equal-warmup
correction described above. The initial baseline file was preserved. Reproduction
need not overwrite reports: omit the explicit `--write-*` flags to print results.
`--manifest` explicitly writes the manifest. Native API measurement requires the
local database; routine prototype tests do not.

The targeted test run after adding four tool-filter cases reported 26 passed in
2.05 s. Final strengthened assertions were then included in the full run:

```powershell
.venv/Scripts/ruff.exe format src scripts tests --no-cache
.venv/Scripts/ruff.exe check src scripts tests --no-cache
Remove-Item Env:FATA_F2_EVIDENCE -ErrorAction SilentlyContinue
$env:FATA_BROWSER_EVIDENCE_STAGE='f2-02'
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser
```

The runner exited zero and executed these checks, with observed final results:

| Command/check | Result |
| --- | --- |
| Python/Node/npm/Ruff version checks; `npm --prefix web ls --depth=0` | Passed; installed versions resolved |
| `ruff check src scripts tests --no-cache` | Passed |
| `ruff format --check src scripts tests --no-cache` | Passed |
| `python scripts/export_contracts.py --check` | Passed; no drift |
| `npm --prefix web run check` | Passed TypeScript checks |
| `npm --prefix web run format:check` | Passed |
| `npm --prefix web run check:generated` | Passed strict generated-contract checks |
| `npm --prefix web run test` | **69 passed**, zero skipped/cancelled, 4.094 s reported test duration |
| `npm --prefix web run build` | Passed |
| `python -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **571 passed**, 74 integration tests deselected, 16.49 s |
| `python scripts/smoke_local.py` | Liveness/readiness 200; canary request 422; correlation/safe console true; owned API process stopped |
| `python -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **74 passed**, 571 routine tests deselected, 26.60 s; includes native SQL and installed-browser journey |
| `python scripts/evaluate_baseline.py --check` | **40/40 unchanged**: development 24/24, held-out 16/16 |
| `python scripts/measure_async_reads.py` | F2-01 regression: both modes 5/5 correct, three reads/trial, no retries, maximum inflight 1/3 respectively |

The runner resolves `python`/`ruff` to `.venv/Scripts` and npm to installed
`npm.cmd`. Its existing ignored reports remain under `.cache/f107/`, including
`check-results.json` and both JUnit files; this legacy path does not refresh
historical tracked F1 evidence. **645 Python tests passed across the two disjoint
selections, with zero failures/errors/skips.** Existing native PostgreSQL tests
remain distinct from routine reference-model/specification tests; no new
database-level guarantee is inferred from prototype equivalence tests.

The browser exercised Save → Generate → Review → Revise → lost approval response
→ same-key retry → durable readback → changed profile → immutable history → owner
switch. Observed: successful retry and mobile error recovery, zero horizontal
overflow, zero runtime errors and zero external page requests. New screenshots:
[desktop](evidence/f2-02-desktop.png), [mobile](evidence/f2-02-mobile.png),
[mobile error](evidence/f2-02-mobile-error.png). This is regression evidence;
frontend product behavior and approval enabling rules were unchanged.

Final local checks:

- `python scripts/migrate.py` returned `{'applied': []}`; existing migration checksums matched. No new migration was needed.
- Native SQL reported PostgreSQL 18.6, zero leftover `f103_test_%`/`f202_perf_%` schemas and public approval/idempotency/audit row counts `(0, 0, 0)`.
- Aggregate raw-report checks recomputed saved distributions from raw samples, verified denominators, zero failures, entry/byte bounds and common catalog fingerprint.
- Manifest source/artifact/lock hashes and `git diff --check` were checked; frozen source/data/contract/migration/lock paths remain unchanged. `AGENTS.md` remains ignored.
- Process inspection found zero task-owned Chrome processes. `docker compose stop postgres` completed, preserving image/volume. No task-owned API server remains.

## Environment, limitations and readiness

Measured on Windows 11 build 10.0.26200, AMD64 Family 25 Model 116 Stepping 1,
16 logical CPUs, one application event loop. Python 3.14.9; Node 24.22.1;
npm 11.19.1; Ruff 0.17.2; Pydantic 2.14.1; FastAPI 0.162.0; HTTPX 0.28.1;
Psycopg 3.3.6; Uvicorn 0.54.0; pytest 9.1.1; PostgreSQL 18.6; installed Chrome
155.0.8059.85. The existing PostgreSQL image digest and all lockfiles are unchanged.

Five rotated rounds on one workstation cannot eliminate load, scheduling,
thermal or SQL connection variability. Pooled percentiles are descriptive, not
confidence intervals or significance tests. The supported small catalog, synthetic
profiles, local SQL and fake provider establish no production scaling, real-model
quality/cost, hosted tracing, AWS or live-network performance result. Browser
checks establish workflow regression behavior, not browser performance gains.
Instrumentation and result checking have overhead, held consistent between modes.
No new production latency SLO or timing-dependent CI assertion was introduced.

F1/F2-01 budgets, egress/privacy checks, ownership, cancellation, request-scoped
traces, terminal publication, approval reconciliation, idempotency and SQL
transaction behavior retain their existing implementation and passing tests.
No profiles, candidate state, approval decisions, personalized outputs or history
are retained by the prototype. No Redis, queues, services or durable generation
state were added. No known F2-02 blocker remains.

Ready for owner review. F2-03 may use this measured uncached baseline when
separately authorized; no LangGraph dependency, graph experiment, feedback flow or
later work unit was begun. No commit or push was performed. Stop after F2-02.
