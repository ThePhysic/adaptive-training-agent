# F3-03D handoff — offline transport and safety hardening

Date: 2026-10-24. Scope: **F3-03D only**, after owner acceptance of the
[F3-03C documentation review](f3-03c-pre-live-review.md). Its live **NO-GO** remains
in force. This implementation creates no live sender, financial authority,
monetary permit, account authorization, provider/counting request, hosted export,
cloud resource or deployment. No credentials, SDK installation, commit or push.
Stop after this work unit for review; no F3-04 work is authorized or implemented.

## Result and architectural decisions

The accepted count-aware replay now durably retains numerical discrepancies
atomically with project freeze, checks completed native stream items against
terminal output, and owns one bounded async HTTP client for the entire request.
The new socket connector is **hardwired to literal loopback**. TLS/socket tests
exercise actual local connections without enabling a provider transport. Existing
synthetic identity, typed Agent, independent validator, approval/Submit transactions,
terminal-only publication and transient candidates retain their boundaries.

The smallest transport preparation was chosen: existing HTTPX, exact mocks or
fixed-loopback TLS, no network-provider constructor or credential lookup. The
application remains fake-only and `LiveGate.check()` still unconditionally denies.
Replay SQL mode and synthetic quote checks remain intact. No SDK/framework,
additional service, queue, Redis, graph adoption or durable generation state.

Request limits remain **3 counts / 3 generations / 6 combined**, 16,000 inference
input / 4,000 output, at most 2,000 output per attempt, 30 seconds, four reads,
one shared retry, one repair, one run/principal and two globally. SQL cleanup may
drain the existing bounded critical section after deadline, without another send.

## Files changed

| File/group | Change |
| --- | --- |
| `migrations/008_spending_observations.sql` | Empty bounded numerical observation table; no grants/mode changes |
| `src/future_training/providers/observations.py` | Salvage only validated allowlisted numbers; classify model/tier without retaining raw strings |
| `persistence/spending.py`, `persistence/counted_spending.py` | Atomic observation/freeze in both ledger paths, immutable first observation, no corrected-report refund, unpriced/missing usage handling |
| `providers/native.py`, `providers/responses.py` | Completed native validation, event/terminal consistency, bounded preserved state, owned HTTP lifecycle |
| `providers/http.py` | Exact logical destination policy, mock/loopback-only connectors, verified TLS, no redirects/proxy/retries, encoding/actual-byte bounds |
| `providers/counted.py`, `agent/orchestration.py` | Shared client through counts/continuations, numerical evidence on usage failure, shutdown task ownership and awaited cleanup |
| `providers/gates.py` | Durable disable plus cancellation/await of owned tasks, cancellation precedence, no self-wait; unconditional live denial retained |
| `providers/accounting.py` | Conservative `GENERATION_RUN_MICRO=80002` and proposed arithmetic only |
| `observability.py` | Fixed allowlisted transport failure reasons; no new sink or content attributes |
| `tests/test_provider_hardening.py`, `test_provider_tls.py`, `local_tls_doubles.py` | Native/HTTP/TLS/privacy/rounding/shutdown tests and ephemeral local certificate fixtures |
| `tests/test_discrepancy_postgres.py` | Native SQL observation/fault/race/restart/shutdown tests, including real loopback TLS after claims |
| `tests/responses_doubles.py`, `experiments/token_admission.py`, `scripts/measure_token_admission.py` | Emit complete synthetic item events for the stricter parser; original outcomes/frozen historical evidence unchanged |
| `tests/test_migrations.py`, `test_profile_postgres.py` | Additive table inventory updates; existing restart/migration assertions retained |
| `.github/workflows/offline.yml` | Explicit OpenSSL prerequisite check for existing offline CI job |
| `web/scripts/browser-smoke.mjs`, new `evidence/f3-03d-*.png` | New screenshot namespace, no application UI change or historical overwrite |
| `contracts/provider-safety.md`, planning `17–19`, `README.md`, `docs/development.md`, `docs/runbook.md` | Implemented offline safeguards, rounding refinement, local reproduction and remaining gates |
| This handoff | Commands/results, fault evidence and honest readiness boundary |

Paths without a prefix in the source rows above are relative to
`src/future_training/`. No dependency/lock, domain/schema, generated public API,
catalog/corpus/baseline artifact, approval transaction or historical handoff was
changed. Original migrations 001–007 are unchanged.

## Durable discrepancy evidence

Migration 008 adds `spend_observations`, scoped by project, legacy/mixed source
and operation identity. A project foreign key, unique key, fixed reason/class
enums, <=1,024-byte numeric JSON, allowlisted keys, integer/nonnegative/upper-bound
checks and a financial-evidence fingerprint constrain storage. There is one first
observation per operation, not an unbounded event list. No raw effective-model
string, service-tier string, exception, provider receipt, payload hash or native
content is stored. Model/tier become `expected|unexpected|missing`.

The existing project lock orders reserve/claim/observe/settle/stop. An unsettled
pricing or usage discrepancy commits freeze and observation together, leaving
the original sent/held maximum intact. Identical observations return the same
state; changed numbers/classification conflict without replacing evidence.
A subsequently corrected report cannot settle an observed operation silently.
Missing/malformed/unpriced usage preserves only individually valid numbers and
classified cause; nonzero cache writes without TTL partition remain unpriced.
No guessing, zero-cost inference or release follows an accounting exception.

Native PostgreSQL assertions (not reference SQL or in-memory ledgers):

| Scenario | Observed result |
| --- | --- |
| Model/tier/input/output/12h-cache discrepancy | One durable reason/number record and project freeze; generation stays `sent`, **22,500 microdollars**, `actual_micro=NULL`; count remains held |
| Identical duplicate | One observation, unchanged maximum hold; changed duplicate gives `observation_conflict` and preserves first record |
| Concurrent duplicate/conflict | Second connection visibly waits on actual project row lock; one observation after both finish, classified duplicate/conflict outcomes |
| Freeze versus new reservation | New reservation blocks on real lock, then rejects `spending_disabled` after freeze commits |
| Write failure before observation insert | Freeze/observation rollback together; sent maximum retained; reconciliation fence required, then explicit identical observation retry succeeds |
| Lost commit ACK / rollback uncertainty | Ordered reconciliation finds one/zero observations as appropriate; no automatic refund/send; retry commits one observation |
| Original transaction left open | Reconciliation blocks on real PostgreSQL lock until controlled commit/rollback; observes one/zero records afterward |
| Repeated cancellation during commit | Owned transaction drains before cancellation propagates; observation/freeze and original hold survive |
| Fresh child interpreter | Reads committed freeze and 1,000-token numeric observation after original runtime exits; no native state or ticket restoration |
| Missing usage / nonzero writes without TTL / invalid reasoning partition | Actual Agent returns error; two mock requests only, persisted `usage_missing` / `cache_details` / `usage_invalid`; no repricing/refund |
| Count quote exceeded while held | `count_price` observation and freeze; **1,000 microdollars** remains `responded_held`; paired generation cannot claim |
| Direct invalid JSON values | Database rejects negative, fractional, >1e9, textual/private and unknown-key observations |
| Legacy generation-only ledger | Same bounded observation/freeze authority; original **22,500** sent hold retained |

Known previously committed settlements retain their existing immutable
fingerprint/conflict behavior. No invoice reconciliation, automatic unfreeze,
receipt collector or billing worker was introduced. SQL reconciliation establishes
database state only; provider costs remain unknown without authoritative evidence.

## Streaming, local transport and shutdown evidence

`read_stream` requires each terminal output item to have exactly one corresponding
completed-item event. IDs, indices, supported fields, status and terminal content
must agree. Added items are optional, but their identities must match completion.
Partial encrypted state is never used for continuation; complete bounded native
items and allowed assistant phase are preserved in request memory and cleared
on exit. Deltas never dispatch tools. Missing/duplicate/unsupported/inconsistent
items, late deltas, bad indices/status, summaries and oversize fail closed.
Refusal and incomplete outputs keep their existing abstention/failure outcomes.

Synthetic stream producers now emit the required completed-item events. The
historical F3-03A check still reproduces its total-three reference experiment,
including historical unratified flags; it is not the current F3-03D policy.
No frozen fixture JSON, experiment result or evaluation outcome was regenerated.

`OfflineHTTP` permits only logical POST to `https://api.openai.com:443` with the
two exact count/generation paths, no query/fragment/userinfo/alternate path.
There are only two constructible test connectors: exact HTTPX MockTransport and
`LocalTLS`. The latter connects only to `127.0.0.1:<test-port>` and cannot contact
the provider, regardless of a credential or live flag. TLS context verification
and hostname checks are required at construction and rechecked before use.

| Actual local test | Observed result |
| --- | --- |
| Trusted valid loopback certificate | Successful HTTPS read with one POST |
| Wrong SAN/hostname, expired or untrusted certificate | Rejected before a completed HTTP request; no retry |
| Verification disabled at construction or later mutation | Connector rejects; no socket dispatch |
| Invalid proxy/CA/key environment | Explicit verified local context/client works without proxy/credential inheritance |
| Redirect | Rejected; no redirected request |
| Connection interruption / stalled response | Sanitized failure or caller cancellation; socket/client cleanup awaited |
| Compressed response | Rejected before decoding; identity encoding is requested but never trusted blindly |
| Oversized Content-Length, cached or streamed bytes | Rejected at fixed count/generation bounds, including chunked bodies |
| Session client ownership | Same client for multiple operations; closed on exit; cannot reopen after closure |
| Real local TLS count + generation with native SQL | Paired reserve/committed count claim precede HTTPS count; accepted `N=1000`, generation claim precedes HTTPS generation; valid terminal stream settles **2,770**, count stays held; two local requests only |

The TLS fixture creates ephemeral self-signed keys/certificates using existing
OpenSSL in ignored test directories. It validates the **loopback test hostname**,
not OpenAI's certificate/account/model. No provider credential is loaded. The
full typed Agent is tested through mocks; the SQL/TLS boundary is also tested
directly without giving it candidate or approved-plan authority.

Emergency stop first marks the supervisor stopped, then commits ledger disable
and cancels/awaits owned runs. If disable is uncertain, local cancellation still
finishes and the ledger fence/maximum liabilities remain. Stop initiated by an
owned task excludes that task from self-wait, then propagates cancellation.
Caller cancellation wins after cleanup even if the disable ACK was lost.
Repeated stop is safe; future run entry is denied without cancelling its caller.

Native tests pause after reservation, after count claim, after generation claim
and in transport. Observed states respectively preserve only proven-unsent
release, unknown sent count, held count/sent generation, and held count/sent
generation. No HTTP request reaches the transport while paused before its send.
The lost-disable-ACK plus cancelled-stop test retains count `sent` **1,000** plus
unreleased generation `reserved` **60,000** pending explicit reconciliation; it
does not infer free work. Already committed send claims may charge after stop.

## Financial arithmetic and privacy

`proposed_probe_micro(Cµ)` performs arithmetic only: **80,002 + 3*Cµ** integer
microdollars. It rejects unknown/noninteger/negative count bounds, verifies no
tariff and creates no grant. Zero is accepted only as an arithmetic input; the
existing synthetic quote still requires positivity. No approved spending policy
or inference limit was changed.

The hand-calculated three-generation all-30m-write example remains **80,001**
microdollars after per-attempt upward rounding. Five hundred reproducible mixed
cache workloads check that each rounding is less than one microdollar and the
run total never exceeds the conservative **80,002** bound. Counting still needs
an independently verified tariff/maximum; the fixture's $0.001 is invented.
All live monetary and outbound-call permissions remain **zero**.

Synthetic secret/PII canaries run against both configured sinks: safe local
console and bounded trace ring, including result representations. Untrusted
model/tier canaries are absent from persisted observations. Numeric salvage and
database constraints exclude arbitrary text. HTTP failures use fixed reasons;
no raw prompts, profiles, workout plans, native reasoning, credentials, payload
hashes or private billing IDs enter ordinary logs/traces. No new sink, debug/body
instrumentation, hosted exporter or account setup was added.

## Commands, results and environment

All final checks ran locally on 2026-10-24 using existing dependencies. OpenAI
Docs were consulted read-only for [reasoning/native state](https://developers.openai.com/api/docs/guides/reasoning),
[streaming](https://developers.openai.com/api/docs/guides/streaming-responses) and
[cache accounting](https://developers.openai.com/api/docs/guides/prompt-caching).
This was not a provider API request or new pricing/retention verification.

```powershell
docker desktop start
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-03d'
.venv/Scripts/python.exe scripts/check.py --integration --browser

# Existing separate environment, from experiments/langgraph:
.venv/Scripts/python.exe -m pytest -q --basetemp=../../.cache/pytest-f303d-graph-final --junitxml=../../.cache/f303d-graph-final.xml

# Root repeatability/boundary checks:
.venv/Scripts/python.exe scripts/migrate.py
git diff --check
git check-ignore AGENTS.md
docker compose stop postgres
```

The final shared runner exited **0**, all **20 children passed**, summed elapsed
time **151.935 s** (not model latency). Exact child commands/results:

| Command | Final observed result |
| --- | --- |
| `.venv/Scripts/python.exe --version` | Python **3.14.9** |
| `node --version` | **24.22.1** |
| `npm.cmd --version` | **11.19.1** |
| `.venv/Scripts/ruff.exe --version` | **0.17.2** |
| `npm.cmd --prefix web ls --depth=0` | Existing locked tree resolved, no acquisition |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | **109** files formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Passed; public contracts unchanged |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Five existing assets match, live false |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Preserved F3-03A historical experiment matches; no evidence rewrite |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | Generated TypeScript/runtime validators match OpenAPI |
| `npm.cmd --prefix web run test` | **85/85 passed**, zero skipped/cancelled; 5.803 s |
| `npm.cmd --prefix web run build` | Passed |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **819 passed / 206 deselected**, zero errors/skips; 21.87 s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200 / readiness200 / invalid422; safe correlated console and owned child stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **206 passed / 819 deselected**, zero errors/skips; 98.44 s; actual PostgreSQL/HTTP/installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 development + 16/16 legacy held-out**, zero failures; frozen baseline unchanged |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Both modes **5/5 correct**, three 40ms fake reads/trial, zero retries; medians **138.412 / 45.906 ms**, peaks **1 / 3** in flight |

The disjoint root population is **1,025 Python tests**: this unit adds **53 routine
(41 protocol/HTTP/privacy/rounding + 12 local TLS)** and **32 native SQL/fault**
cases. Existing seven reference/specification tests remain separate from native
SQL proof. The additional 500 rounding workloads are samples inside one test,
not 500 extra test cases. The isolated graph suite passed **47/47**, 17.25 s.
Do not pool targeted reruns or benchmark samples into these denominators. Hosted
CI was not dispatched; its existing job adds only an OpenSSL prerequisite check.

Targeted development commands included:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_responses.py tests/test_token_admission.py tests/test_counted_responses.py --basetemp=.cache/pytest-f303d-regression
# 162 passed after the synthetic stream emitter correction
.venv/Scripts/python.exe -m pytest -q tests/test_provider_hardening.py tests/test_provider_tls.py --basetemp=.cache/pytest-f303d-transport-r2
# 48 passed at that development revision; final runner includes all 53
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_discrepancy_postgres.py tests/test_counted_spending_postgres.py tests/test_spending_postgres.py --basetemp=.cache/pytest-f303d-db-r2
# 91 passed at that development revision
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_discrepancy_postgres.py -k 'shutdown_cancellation or real_tls_count' --basetemp=.cache/pytest-f303d-final-edge
# 2 passed / 30 deselected; final runner includes all 32 new native cases
```

Early development failures were corrected, not hidden: legacy synthetic emitters
omitted required completion events; the loopback connector initially omitted
Content-Length; a test constructed a disallowed default HTTP transport under a
deliberately invalid CA environment; settled count input validation needed to
preserve its existing error; and task callback timing/cancelled-stop exception
precedence required explicit cleanup. The final cancellation regression proves
cancellation wins after draining shutdown even with a lost disable commit ACK.
An initial native run hit the engine's startup interval; the final run has no
skips or database errors. The first full run passed before the last edge cases;
the final complete rerun above includes the final application source and expanded
edge cases. After that run, the restart test was strengthened so the **writing
child commits the discrepancy and exits**, then a separate fresh reader process
checks the observation/freeze. All **32/32** native hardening cases passed again,
18.97 s, with no application change or added test denominator:

```powershell
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_discrepancy_postgres.py --basetemp=.cache/pytest-f303d-discrepancy-final --junitxml=.cache/f303d-discrepancy-final.xml
.venv/Scripts/python.exe -m ruff check src tests scripts --no-cache
.venv/Scripts/python.exe -m ruff format src tests scripts
```

Docker Desktop initially was stopped and its installation was under the user's
local Programs directory, rather than Program Files. `docker desktop start`
started the installed engine without a pull/install. Native tests create/drop
isolated synthetic schemas; migration 008 alone was newly applied in development,
then the repeat command returned `{'applied': []}`. All **eight** migration
checksums match; original migrations are unchanged. PostgreSQL **18.6** reports
`fsync=on`, `synchronous_commit=on`, `full_page_writes=on`; this is configuration
inspection, not a power-loss test. Public project/grant/session/legacy attempt/
pair/operation/observation row counts are **all zero**, with no live authority.

Python's TLS backend reports **OpenSSL 3.5.9 (29 Sep 2026)**. The existing Git for
Windows certificate-generation CLI reports **OpenSSL 3.2.1 (30 Jan 2024)**; it is
used only offline to generate disposable synthetic test material, not as the TLS
client backend or a recommended live dependency. No new OpenSSL version/package
was pinned or installed. A non-elevated CLI-version invocation encountered MSYS
sandbox process restrictions; the normal-process read and actual TLS checks pass.

Detailed ignored output is `.cache/f107/check-results.json`, unit/integration
JUnit files, `.cache/f303d-graph-final.xml` and local launcher output. New browser
evidence: [desktop](evidence/f3-03d-desktop.png),
[mobile](evidence/f3-03d-mobile.png), [mobile error](evidence/f3-03d-mobile-error.png).
The installed browser verified the existing synthetic Save/generate/revise/approve/
same-key retry/immutable readback/history/completion journey and owner switch:
**zero runtime errors, zero external page requests, no horizontal overflow**.
This remains **fake-provider UI evidence**, not real-model or provider TLS evidence.
No historical evidence flag or `--evidence` option was used.

Frozen-path checks confirm unchanged domain/schema/Budget/approval implementation,
generated contracts, data/catalog/corpus/results, original migrations, graph source/
lock and historical review/handoff/evidence. Dependency lock SHA-256 values remain:

```text
uv.lock: a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a
web/package-lock.json: cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf
```

Documentation validation passed for **eight** changed/new Markdown files, UTF-8,
balanced fences, whitespace and **78 local links**. Zero fixture schemas remain.
`AGENTS.md` remains ignored/untracked. No commit/push or external deployment was
performed. The task's PostgreSQL container is stopped after checks, preserving
its volume, and test/launcher/browser children are cleaned up.

## Remaining limits and readiness

Ready for **F3-03D owner review**, not execution. The
[updated pre-live checklist](../planning/19-f3-03c-pre-live-readiness.md) distinguishes
implemented offline safeguards from remaining gates. The accepted C report is
unchanged and its NO-GO stands.

Still unresolved: counting tariff/maximum/retention and account policy; actual
model access, schema/native/usage compatibility, token-count equivalence and
latency; explicit numerical/privacy approval; and a separately reviewed real
sender with live capability/financial authority. The current fake/replay gate
must not be removed merely because TLS tests pass. No replay row is live authority.
The known literal model/tier checks and strict cache parser may reject legitimate
provider variants; stop and review rather than silently widening support.

No production-scale, real-user, multi-worker, arbitrary power-loss, real-model
quality, provider-invoice cap, hosted observability or AWS claim is made. Existing
local PostgreSQL trust authentication remains a synthetic-development boundary.
A future live probe needs the separate implementation/execution and spending
approvals enumerated in the checklist; no F3-04 evaluation follows from completion.
