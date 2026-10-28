# F2-02 architectural decision: retain the uncached application

Date: 2026-10-24. Status: measured decision awaiting owner review.

**Do not install a new catalog cache in the application.** Retain the bounded
prototype only under `future_training.experiments` as reproducible comparison and
correctness evidence. Existing canonical catalog storage and the accepted four-entry
arithmetic-options memoization remain unchanged.

## Evidence behind the decision

The [audit](f2-02-catalog-audit.md) preceded optimization. The 20-record catalog is
already loaded once per app; there is no catalog network/database read or
per-request disk load to eliminate. Fresh model parsing/copying is repeated, but
is small. The initial unprofiled eligibility service p50/p95 were 0.110/0.223 ms.
Independent validation still must run and is deliberately outside cache scope.

The isolated comparison used all eight matrix rows × three presets × three day
counts × three exclusion variants: 216 cases, five rounds, one/two logical clients.
It rotated mode order and compared identical workloads with fresh results:

| One-client component | Uncached p50 ms | Cold p50 ms | Warm p50 ms |
| --- | ---: | ---: | ---: |
| Eligibility | 0.1101 | 0.5858 | 0.0657 |
| Planning | 0.7530 | 1.2936 | 0.6665 |
| Tool dispatch + result checking | 0.6287 | 1.0832 | 0.4995 |
| Tool + planner + independent validation | 1.6877 | 2.1657 | 1.4815 |

Warm operation saves real repeated work: 0.2062 ms (~12.2%) in that component
pipeline. Cold operation costs 0.4780 ms more. This is useful microbenchmark
evidence, not evidence of a comparable application speedup.

The actual generation API was then measured using native isolated PostgreSQL,
the existing fake provider and all authoritative validation/publication. Five
rotated rounds ×24 representative profiles gave 120 samples per mode/client level,
720 measured generations total, all successful:

| API clients | Mode | p50 ms | p95 ms | p99 ms |
| ---: | --- | ---: | ---: | ---: |
| 1 | Uncached | 90.147 | 123.316 | 137.226 |
| 1 | Cold | 90.500 | 126.325 | 136.422 |
| 1 | Warm | 91.519 | 132.313 | 144.241 |
| 2 | Uncached | 129.903 | 168.368 | 172.585 |
| 2 | Cold | 134.173 | 193.023 | 207.565 |
| 2 | Warm | 130.924 | 167.616 | 197.882 |

Warm pooled p50 is 1.372 ms slower with one client and 1.021 ms slower with two;
paired round p50 differences change sign. The two-client warm p99 is also worse.
These small, variable
differences do not establish a consistent application benefit. The experiment is
local ASGI + real SQL, not browser/network/real-model latency, and is not a
statistical significance or production-scale study.

## Cost and correctness tradeoff

The prototype is bounded and correct in the tested scope: eight default entries,
64 KiB logical payload cap, LRU eviction, immutable-source binding, fresh model
copies and per-call exclusions/validation. Filling the eight current projections
retains 37,264 logical bytes, duplicating existing metadata. It adds version/key
maintenance, byte accounting, eviction, invalidation and state inspection for
sub-millisecond component savings without a demonstrated user-facing bottleneck.
Cold binding/fingerprint construction also has a separately measured cost.

It does not speed the current catalog-list HTTP route, which uses raw `records()`;
does not avoid profile SQL; and never skips validation. A simpler memo of shared
mutable models could be faster but would break mutation isolation. Caching
personalized plans, profiles, approval decisions or owner history would introduce
freshness/authorization risks and is outside this unit.

Therefore no main-path cache, new deployment switch, service, invalidation job or
new dependency is justified now. This follows the predeclared complexity/value
criterion in the audit; no new SLO or ratified request limit was invented to label
the result successful.

Reconsider only if measured catalog CPU dominates a real supported workload,
catalog size/source changes, or a concrete latency/CPU objective is missed. Repeat
the same comparison and review bounds, source identity and copy semantics first.
Do not enlarge the catalog, add simulated I/O, increase admission limits or skip
correctness checks merely to make caching look valuable.

Raw evidence and full methodology are linked in the
[F2-02 handoff](f2-02-handoff.md). F2-03 and later work remain unauthorized.
