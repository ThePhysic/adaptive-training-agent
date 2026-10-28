# F3-03B handoff — offline count-aware integration and mixed spending

Date: 2026-10-24. Scope: **F3-03B only**, after owner acceptance of F3-03A and
ratification of document 18 amendments A–C **for offline implementation/testing**.
Recommendation: review the completed local integration. Live provider compatibility,
counting tariff/maximum charge and counting retention remain unverified. All live
allowances remain **USD 0**. There is no live transport, active monetary permit,
provider/counting request, hosted export, cloud provision, commit or push.
No F3-03C implementation or real-model evidence is claimed.

## Result and architecture

The existing typed Agent now supports explicit count-aware Responses **replay**
using exactly HTTPX `MockTransport`, the existing read tools and authoritative
domain validator. Each initial generation, continuation, repair and permitted
retry independently counts its immutable payload. Separate counters enforce
**three generation / three counting / six combined attempts**. The existing
`BudgetLimits.provider_attempts=3`, 16,000 input / 4,000 output inference limits,
2,000 per-attempt output maximum, four reads, one repair, one shared retry,
30-second request deadline, one/principal and two/global admission remain.

The new `CountedSpendingLedger` extends the existing project-first transactional
ledger. It atomically reserves a count plus its worst-case paired generation,
retains acknowledged counts with unknown costs, settles known generation usage,
and discards authorization tickets on cancellation/restart. Legacy generation-only
and new mixed liabilities share all financial ceilings. No parallel planner,
model write tool, queue, worker, service or production graph was introduced.
Application settings and ordinary HTTP/browser workflows stay fake-by-default.

## Changed files

| Files | Purpose |
| --- | --- |
| `providers/counting.py` | Shared immutable payload projection/binding extracted from the accepted F3-03A experiment; no new business schemas |
| `providers/counted.py` | Request-local exact-count admission, single-use native/context binding, 3/3/6 counters, typed failure/usage handling and awaited cleanup |
| `providers/responses.py` | Explicit counted replay factory and shared bounded mock-only generation transport; legacy replay retained |
| `agent/orchestration.py` | Count before inference reservation, existing single retry owner, request-owned async cleanup, internal numeric count/wire/byte measures |
| `observability.py` | Allowlisted `provider.count` stage, safe fixed reasons and numeric counters; no exporter/content logging |
| `persistence/counted_spending.py` | Atomic pairs, distinct operations/ordinals, held costs, exactly-once settlement, request-memory tickets and explicit reconciliation |
| `persistence/spending.py` | Both operation tables included in financial ceilings; reject mixing protocols within one run |
| `migrations/006_counted_spending.sql`, `007_counted_rate_version.sql` | Empty paired/operation tables and additive fixed rate-version provenance |
| `experiments/token_admission.py` | Reuse the pure binding helper; original F3-03A total-three experiment/evidence remains unchanged |
| `tests/counted_doubles.py`, `test_counted_responses.py` | Explicit protocol recorder and 36 actual-Agent/mock-HTTP cases; **not native accounting proof** |
| `tests/test_counted_spending_postgres.py` | 37 real PostgreSQL accounting, concurrency, fault, restart and Agent/transport cases |
| `tests/test_migrations.py`, `test_profile_postgres.py` | Updated table inventories; original migration/restart assertions retained |
| `web/scripts/browser-smoke.mjs` | New screenshot namespace `f3-03b`; no application UI changes |
| `README.md`, `docs/development.md`, `docs/runbook.md` | Current status and reproducible local checks/recovery |
| `contracts/provider-safety.md`, planning `14`, `17`, `18` | Offline ratification/current contracts, financial and call semantics; original proposal body and historical reports retained |
| Planning `19-f3-03c-pre-live-readiness.md`, this handoff and new browser evidence | Outstanding approval gates and measured evidence |

Source paths above are relative to `src/future_training/` unless otherwise given.
No dependencies, locks, public schemas/routes, domain rules, catalog, frozen
corpus/results, approved-plan/session models or historical handoffs were changed.
Existing versioned F3-02 prompts/tools/output/configuration/manifest are reused.

## Protocol and budget evidence

Every generation body is serialized once and frozen; counting receives exactly
the nine allowed common fields. Generation-only transport/storage/output/cache
settings are fixed and bound. Unsupported input-affecting fields/references are
rejected. The same completed ordered native items and checked function results
are carried into recounting without decoding or persisting reasoning state.
Context/history/attempt/allowance mutations after count stop before generation.
No ticket is reusable for a retry, repair, continuation or another runtime.

| Executed synthetic sequence | Count / generation / total | Observed result |
| --- | --- | --- |
| Count → model-selected catalog tool → checked local result → recount → final plan | 2 / 2 / 4 | Independently valid unpublished plan; 2,000 input / 200 output; one read |
| Above → invalid structured result → one repair → recount → corrected plan | 3 / 3 / 6 | Valid unpublished plan; 3,000 / 300; one read and one repair; no seventh call |
| Tool sequence → known terminal server failure → one retry with fresh count | 3 / 3 / 6 | Valid plan; exactly one shared retry; known usage retained |
| Third generation needs another repair | 3 / 3 / 6 | Typed error; no fourth count/generation |
| Missing/invalid/duplicate/oversized/unavailable count or count connection loss | 1 / 0 / 1 | No generation and no hidden retry |
| Connection interruption on continuation | 2 / 2 / 4 | Error; last generation unknown, no automatic resend |
| Count/report 16,000 followed by needed continuation | 1 / 1 / 2 | First actual usage retained; next count avoided because inference input is exhausted |
| Count 16,000, report 16,001 | 1 / 1 / 2 | Error; **16,001 preserved**, never clamped or claimed retrospectively prevented |
| Hanging count or generation | At most 1 / 1 / 2 | Caller cancellation or controlled 30-second clock cancels/awaits transport; same-principal overlap denied; admission released after cleanup |
| Unknown tool/bad arguments/duplicate native call/refusal/incomplete output | Bounded by available pairs | Existing dispatch/result validation, duplicate rejection, abstention and failure rules retained |

Count JSON is <=1,024 bytes, strict integer with exact object/field set; inference
request/stream bounds remain 65,536 bytes, normalized output 16,384. Internal
count/generation outgoing byte totals and fixed count-stage durations are traced
separately from inference usage. Cumulative stream usage is still settled once.
Count failures consume count/combined capacity, not an invented generation usage.
Counter values conservatively include attempted claims even if transport was not
reached. No counting retry is implemented; the shared maximum does not require it.

The original F3-03A `measure_token_admission.py --check` still emits the preserved
**historical** unratified/total-three experiment and pure six-call reference model.
It is a frozen provenance check, not the current F3-03B policy or SQL evidence.
The new tests execute actual six-call mock sequences through the existing Agent.

## PostgreSQL migration and fault evidence

Migration 006 adds two tables with foreign-key ownership of financial scope,
unique pair/operation identities, unique run/kind ordinals 1–3 and combined claims
1–6, bounded fields and checked states. Migration 007 adds fixed generation-rate
provenance; fingerprints bind that rate and the positive synthetic count quote.
Both are additive; historical migrations 001–005 are byte-unchanged. No migration
inserts a project, grant, session, permit or funded allowance. Business snapshots
are untouched. SQL holds integer microdollars with exact upward-rounded pricing.

Native fixtures create isolated schemas and apply all migrations. Each test
creates only synthetic replay grants; teardown drops its schema. Protocol recorder
assertions and seven existing `contract_spec` reference cases are separate from
these native tests. The following results are observed assertions against actual
PostgreSQL, including explicit transaction/row-lock inspection:

| Scenario / native test | Observed result |
| --- | --- |
| Atomic pair + count acknowledgment | Two rows reserved together: count 1,000 + generation 60,000 microdollars; no partial pair. Count `N=1000` changes count to `responded_held` at **1,000**, generation to 22,500 |
| Generation settlement | Fixture usage costs **2,770** microdollars per generation. Identical settlement returns 2,770; changed settlement conflicts |
| Two-/three-generation Agent sequences | Four/six rows, unique combined ordinals 1–4/1–6; generations settled 2,770 each; count holds remain **2,000/3,000 total** with `actual_micro=NULL` |
| Explicit synthetic count-charge evidence | Held count settles to an explicitly supplied 250; identical settlement returns 250; changed cost conflicts and cost above quote rejects. Adapter never calls this from a count number |
| Project/day/grant/session races | Three barrier-synchronized competing 61,000 reservations: **one accepted, two spend_exhausted**, exactly two operation rows, in each dimension |
| Legacy/mixed interaction | Legacy attempts consume the same ceilings; neither path bypasses the other's holds. Reusing a run across protocols rejects |
| Matching pair concurrency | Second repository demonstrably blocks on real project row lock, then returns matching reservation without duplicates; changed fingerprint conflicts |
| Commit ACK lost / rollback ACK uncertain | Project fenced; authoritative read finds exactly two/zero rows. No send permitted before reconciliation |
| Transaction left open | Reconciliation demonstrably blocks on actual database lock until injected commit/rollback resolves; finds two/zero rows |
| Lost count-claim / count-accept / generation-claim / generation-settlement ACK | Committed state retained; restart has no reusable count ticket. Known settlement retry returns existing cost exactly once |
| Repeated cancellation during reserve/accept/generation claim | Owned transaction completes before cancellation propagates. Only unclaimed reservations release; sent/held liabilities survive |
| Cancellation after successful admission, before generation entry | Awaited session cleanup leaves count `responded_held` 1,000 and generation `not_sent`; one HTTP count only, no ticket |
| Abrupt original process exit after count acknowledgment | Fresh runtime reads held count plus reserved generation; durable number cannot mint a generation ticket, even via repeated accept. Explicit abandonment releases only generation |
| Missing count response / malformed count | Count `sent` at 1,000, generation `not_sent`; no free-count inference |
| Missing generation usage / generation connection loss | Count `responded_held` 1,000 and generation `sent` 22,500; full unknown hold retained |
| Midnight | Already claimed count stays on original UTC date; generation rebasing checks new day's capacity. Failed claim consumes ticket; no automatic retry |
| Expired session/grant or shutdown after count | Generation denied; count liability retained. New day/session does not erase earlier project/grant liabilities |
| Input lower/higher than count, output overrun, unexpected model/tier | Project frozen durably; unresolved generation hold retained. No clamp, repricing shortcut or further admission |
| Run order/token exhaustion | New key cannot skip ordinal, exceed third generation or reset cumulative inference allowances |

Emergency disable linearizes at committed claim: future claims are blocked, but
an already claimed/in-flight operation may charge. No software shutdown can retract
that claim. Generation unknowns and unknown/no-response counts block the next pair;
acknowledged successful counts with held costs permit progress only within ceilings.
Database reconciliation reads authoritative state, never provider billing. Unknown
sent count costs cannot currently be settled automatically; retain them indefinitely
pending separately designed trusted billing evidence. No worker/recovery replay exists.

## Validation commands and observed results

All final checks ran locally on 2026-10-24 using existing installations; no SDK or
dependency installation occurred. Official documentation browsing was read-only.
The compact [official count reference](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count)
was reopened to verify supported fields/reply; no count/API request was sent.
No tariff or retention guarantee was inferred from that reference.

```powershell
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-03b'
.venv/Scripts/python.exe scripts/check.py --integration --browser

# Separate existing experimental environment, from experiments/langgraph:
.venv/Scripts/python.exe -m pytest -q --basetemp=../../.cache/pytest-f303b-graph-r2

# Root, final repeatability check:
.venv/Scripts/python.exe scripts/migrate.py
git diff --check
git check-ignore AGENTS.md
docker compose stop postgres
```

The shared runner exited **0**, all **20 children passed**. Summed child elapsed
time was **174.177 s**, not model latency. Exact children and observed results:

| Command | Final observed result |
| --- | --- |
| `.venv/Scripts/python.exe --version` | Python **3.14.9** |
| `node --version` | **24.22.1** |
| `npm.cmd --version` | **11.19.1** |
| `.venv/Scripts/ruff.exe --version` | **0.17.2** |
| `npm.cmd --prefix web ls --depth=0` | Existing locked tree resolved; no installation |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | **102** files formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Passed; public contracts unchanged |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Five versioned assets match; live false |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Historical F3-03A experiment matches exactly; not current policy/SQL evidence |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | OpenAPI/TypeScript/runtime validators match |
| `npm.cmd --prefix web run test` | **85/85 passed**, zero skipped/cancelled; 35.850 s |
| `npm.cmd --prefix web run build` | Passed |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **766 passed / 174 deselected**, zero errors/skips; 23.06 s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200 / readiness200 / invalid422, safe correlated console, owned API process stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **174 passed / 766 deselected**, zero errors/skips; 75.17 s; actual PostgreSQL, HTTP and installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 development + 16/16 legacy held-out**, zero failures; frozen results unchanged |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Sequential/concurrent **5/5 correct** each, three 40ms fake reads/trial, zero retries; medians **138.051 / 46.642 ms**, peaks **1 / 3** in flight |

The disjoint root selections total **940 Python tests**, including **36 new
routine and 37 new native** cases. Existing seven reference/specification cases
are included but do not establish database correctness. The isolated graph suite
passed **47/47**, 19.99 s. Do not pool targeted reruns/benchmark samples into these
denominators. Hosted CI was not dispatched. Async timing remains localhost/mock
evidence; no real count/model latency or production speedup is claimed.

Targeted commands/results during development:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_responses.py tests/test_token_admission.py
# 126 passed
.venv/Scripts/python.exe -m pytest -q tests/test_counted_responses.py --basetemp=.cache/pytest-f303b-protocol-r3
# 36 passed
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_counted_spending_postgres.py tests/test_spending_postgres.py tests/test_migrations.py --basetemp=.cache/pytest-f303b-sql-r2
# 66 passed, 1 deselected at that development revision
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_counted_spending_postgres.py --basetemp=.cache/pytest-f303b-sql-r3
# 36 passed before the final cancellation-boundary case; final shared run covers all 37
```

Early runs exposed harness mistakes (wrong admission/tracer access, missing `src`
path/Windows selector loop in the restart child), formatting issues, and an initial
graph invocation from the wrong working directory. These were corrected; the final
complete run above passes. A non-elevated run also encountered Windows temporary
directory permissions; isolated cache paths and the normal local test permission
resolved this without deleting/resetting project data.

The migration checksum safeguard correctly rejected changing 006 after its first
local application during development. Its applied contents/checksum were restored;
rate provenance was moved to additive **007** rather than rewriting migration
history. That migration returned `{'applied': ['007_counted_rate_version.sql']}`;
final repeat returned `{'applied': []}`. The native runner had first applied 006.
All **seven** recorded migration checksums now match their files. PostgreSQL is
**18.6**, with zero leftover fixture schemas and public spending-table counts
**(0,0,0,0,0,0)** for project/grant/session/legacy attempt/pair/operation. There is
no active/funded provider permit or default grant.

New browser evidence: [desktop](evidence/f3-03b-desktop.png),
[mobile](evidence/f3-03b-mobile.png), [mobile error](evidence/f3-03b-mobile-error.png).
The installed browser reports **zero runtime errors, zero external page requests,
no horizontal overflow**, same-key approval/completion recovery, owner switch and
immutable history. Mobile inspection shows the saved 20-minute snapshot retained
after profile changes to 30 minutes, with submitted session records. This is the
unchanged **fake-provider UI** regression, not live or counted-provider UI evidence.
No old evidence-writing flag or `--evidence` runner option was used.

Ignored detailed results remain in `.cache/f107/check-results.json`,
`unit.xml`/`integration.xml` and local launcher output. Historical screenshots,
traces, F1/F2/F3 handoffs, corpus/results and F3-02 assets are unchanged. Explicit
frozen-path checks also found no changes in domain/schema, core Budget/gates,
approval implementation, generated contracts or LangGraph source/lock.

Dependency lock SHA-256 values remain:

```text
uv.lock: a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a
web/package-lock.json: cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf
```

`AGENTS.md` remains ignored/untracked. No commit/push or external deployment was
performed. The local PostgreSQL container is stopped after checks, preserving its
volume; test/launcher children are cleaned up.
Final task-owned Chrome process count is **0**. `git diff --check` passes, and
all nine changed/new Markdown files pass UTF-8/fence/whitespace validation with
**68 local links** resolved. `git ls-files AGENTS.md` returns no tracked file.

## Privacy, limitations and readiness

Synthetic secret/PII canaries in opaque native state pass against safe console,
local trace ring and result representation. Only fixed labels, opaque correlations,
numeric usage/byte counters and approved versions enter ordinary telemetry. The
ledger contains numeric accounting/financial fingerprints, never prompts, plans,
native state, credentials, private billing IDs or raw exceptions. No payload hash
is exported. Existing external DNS/socket/fetch guards and credential-only enable
rejection run with the full suite. There is no external provider transport.

Count equality is conditional on a correct provider counter for unchanged input;
client code cannot prevent a lying/mismatched provider from consuming tokens.
Real model/tool/schema/stream/reasoning compatibility, counting tariff/retention,
charge reconciliation, provider-enforced limits and real latency remain unverified.
The synthetic quote is positive invented accounting, not provider pricing. This
work does not establish real-model quality, production scale, multi-worker safety,
cloud operations or operated hosted observability. SQL critical sections use the
existing cooperative five-second operation/statement/lock bounds; cleanup can drain
after the request deadline without permitting another dispatch. No hard outage or
power-loss timing guarantee is claimed.

Ready for owner review of F3-03B and **planning a separately authorized** live
compatibility experiment only after the [F3-03C checklist](../planning/19-f3-03c-pre-live-readiness.md)
is satisfied. No numerical spending permission, provider access or F3-03C work
follows from this handoff. Stop here for review.
