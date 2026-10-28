# F2-02 catalog audit and measurement plan

Status: audit before optimization, 2026-10-24. F1 and F2-01 are owner-accepted.
Only F2-02 is authorized. Historical evidence and frozen domain sources stay intact.

## Actual paths and repeated work

- `create_app()` loads the 20-record catalog once. `Catalog` already retains
  canonical record bytes in an immutable mapping. No per-request filesystem or
  remote catalog lookup exists. Measure `load_catalog` separately as startup work;
  do not claim per-request file-load savings.
- `records()` reparses 20 records into fresh Pydantic models on every call.
  `eligible()` calls it, filters goal/equipment/experience/exclusions, then sorts.
  Copies prevent a caller from mutating the shared catalog. A cache must preserve
  that behavior, not return shared mutable models.
- The catalog HTTP route uses `records()` with public query filters/cursor/limit.
  It has no personalized profile or exclusions. Model read dispatch and its
  independent result check both call `eligible()` using the captured profile.
  The baseline calls eligibility again. This is actual repeated decode/filter
  work, but each pass scans only 20 in-memory records.
- Independent plan validation reparses the proposal and calls `Catalog.get` for
  every block. Validation outcomes/approval/freshness must not be cached. Measure
  validation separately; a filter cache cannot be credited for eliminating it.
- `_options` already has a four-entry arithmetic `lru_cache` from accepted F1.
  It contains bounded prescription options, not profiles/plans. Keep it unchanged
  and prewarm all four goal/experience combinations equally in measured planner
  trials. Do not confuse that existing memoization with an F2 catalog cache.

## Baseline before deciding

Use the existing eight goal/equipment/experience combinations, all three duration
presets and 2/3/4-day profiles. Add explicit ID/tag exclusion variants. Profile
content stays synthetic. Measure raw load, records, eligibility, independent
validation, complete baseline planning and actual read-tool dispatch/result-check
work; record raw per-operation samples, failures, warm-up and percentile method.

Use `perf_counter_ns` for unprofiled timings; separately use `cProfile` to attribute
CPU/repeated calls. Report instrumented profiles separately from latency samples.
For concurrency use the supported one-process/event-loop design at two logical
clients, with cooperative scheduling between operations. Catalog CPU work does
not gain parallel CPU execution from asyncio; do not invent network delay or
benchmark an enlarged catalog to justify a cache.

Consider an isolated bounded catalog-only candidate only if the measured repeated
work merits comparison. Favor retention of the current path if absolute savings
are sub-millisecond and do not materially affect a representative application
operation. This is a local complexity/value judgement, not a new performance SLO.
No profile, candidate, plan, owner history, approval/idempotency decision or model
output is eligible for new caching. No dependency or service is required.

If a candidate is evaluated, run uncached/cold/warm against the identical workload,
preserve output order/copies and document all normalized key inputs, content/version
identity, bounds, invalidation, eviction and cooperative concurrency behavior.
No main-path adoption follows from a microbenchmark alone.
