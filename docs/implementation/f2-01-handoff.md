# F2-01 — Asynchronous I/O and fault tolerance

Date: 2026-10-24. F1 is owner-accepted and closed. F2-01 is implemented and awaits
review. F2-02 and later units have not begun. No commits/pushes, live provider
calls, hosted telemetry, new infrastructure, dependency installation or real-user
data were used.

## Outcome and audit

The [pre-implementation audit](f2-01-async-audit.md) identified existing F1
cancellation/deadline/retry/approval safeguards and concrete gaps before new code.
Most fault handling already existed; it was retained and regression-tested.

Two diagnostic defects were reproduced: cancelled/deadline runs recorded the
preceding state, and generic cancellation formatting replaced the known deadline
cause. Both new regression cases initially failed with `state=model`. The
correction records CANCELLED/FAILED before tracing the result and preserves
`deadline_exceeded` through run cancellation and session timeout. Cancellation
still propagates, uncertain usage remains reserved, and admission/watchdog cleanup
is unchanged. No approval transaction or lifecycle policy was modified.

A contained typed Python async HTTP-read experiment now demonstrates structured
parallel reads, bounded responses, explicit optional degradation and sibling
cleanup. It uses existing API DTOs and the authoritative catalog. It is under
`future_training.experiments` and is **not registered in the application path**.
The app retains direct catalog/profile/history services: artificial loopback HTTP
would add cost without an integration need. This separation is intentional scope
control, not a claim that production generation became faster.

## Changed files

| Paths | Change |
| --- | --- |
| `src/future_training/experiments/__init__.py`, `experiments/async_reads.py` | Actual implemented offline HTTP read adapter, typed context/history/failure results and sequential/TaskGroup batch orchestration |
| `src/future_training/agent/orchestration.py` | Final cancellation state recorded before emitting diagnostic result; public cancellation/accounting behavior retained |
| `src/future_training/observability.py` | Preserve explicit deadline cause; classify session timeout; fixed allowlists for read stages/kinds, execution mode and bounded byte/request counters |
| `tests/async_read_doubles.py` | Cooperative streamed local transports with header/body/close gates, interruption and failure controls |
| `tests/test_async_reads.py` | 39 new routine cases covering overlap, dependencies, wire/result integrity, limits, failures, cancellation, recovery and parent-session budgets/admission |
| `tests/test_async_diagnostics.py` | Two reproduced/fixed cancellation/deadline tracing regressions |
| `tests/test_async_reads_postgres.py` | One actual API/PostgreSQL two-principal typed-read integration case |
| `scripts/measure_async_reads.py` | Reproducible identical-workload comparison; optional explicit evidence write |
| `scripts/check.py` | Shared offline/CI runner also executes the comparison, without overwriting its recorded evidence |
| `web/scripts/browser-smoke.mjs` | Explicit allowlisted screenshot stage selection; F2 browser regressions write new files rather than changing historical F1 PNGs |
| `docs/implementation/evidence/f2-01-async-comparison.json` | Measured five-trial sequential/concurrent report |
| `docs/implementation/evidence/f2-01-{cancel,deadline,read-fault}-trace.json` | Metadata-only diagnostic evidence |
| `docs/implementation/evidence/f2-01-{desktop,mobile,mobile-error}.png` | Accepted browser journey rerun as a regression, not new product behavior |
| `docs/implementation/f2-01-async-audit.md`, this handoff | Audit, decisions, fault evidence, commands and limits |
| `docs/planning/16-f2-work-unit-outline.md` | Outline only for separately authorized remaining F2 work |
| `README.md`, `docs/development.md`, `docs/runbook.md` | F1 closure/current authorization and experiment/reproduction instructions |

No migrations, API routes/DTOs, OpenAPI/TS schema artifacts, domain code, catalog,
evaluation source/data/results or dependency lockfiles changed. Historical F1
reports, trace fixtures and screenshots are preserved. `AGENTS.md` remains ignored
and untouched. No new backend service, queue, Redis, graph or cache was added.

## HTTP-read and task-lifetime contract

- The adapter accepts exactly an explicitly supplied HTTPX `MockTransport` or
  `ASGITransport`; there is no default socket client, arbitrary base URL, caller
  URL or live-source switch. `trust_env=False`, redirects disabled, GET only.
  The trusted synthetic `Principal` is captured per adapter instance and sent to
  the existing identity boundary; it cannot come from model arguments or text.
- Fixed independent reads: owned saved profile; raw catalog page (20 records);
  optional owned history page (five plans). Filtering waits for required results
  and uses `Catalog.eligible(profile.preferences)`, not another domain algorithm.
- Strict existing DTO validation, duplicate-key/nonfinite/UTF-8 rejection,
  profile exclusion checks, exact frozen catalog metadata/version checks and
  history canonical hash/order/uniqueness checks. Historical snapshots retain their
  stored versions; they are not revalidated against today's profile/catalog.
- Body caps: profile 16 KiB, catalog 32 KiB, history 5 × 69,632 bytes. Non-JSON
  content types and non-identity content encodings are rejected before body
  decoding. Caps bound retained logical response data, not process RSS or memory
  allocated internally by a transport before handing a chunk to the adapter.
- One caller-owned `Deadline.scope()`/`Agent.session()` and `Budget`; no new
  30-second clock. Each read has a two-second phase bound. The fixed batch reserves
  three read dispatches before creating children; insufficient remaining budget
  starts no HTTP work. Partially consumed reservations remain conservatively
  charged; the adapter never resets counters or refunds a failed read.
- Concurrent mode uses one `TaskGroup` for three children. Required failure cancels
  and awaits siblings before returning a typed fault. External cancellation is
  propagated; repeated cancellation/cleanup barriers are tested. Sequential mode
  executes exactly the same three reads and validations without overlap.
- Optional history can return `unavailable` for transport/timeout or HTTP
  408/429/5xx availability failure. This differs from successful empty history.
  Authorization, unexpected 4xx, redirects, malformed/hash-invalid results and
  internal adapter errors fail the batch. No partial context is returned when a
  required or integrity/authorization read fails.
- There are **zero adapter retries**. `Run._call` remains the only provider retry
  owner. These reads do not invoke a provider, create/publish a candidate, approve,
  save or submit anything. Reuse inside a parent session is explicitly tested;
  the experiment itself is not a generation/admission entry point.

The implementation follows the documented structured task lifetime in
[Python TaskGroup](https://docs.python.org/3.14/library/asyncio-task.html#task-groups)
and HTTPX's [async streaming/context management](https://www.python-httpx.org/async/)
and [in-process transports](https://www.python-httpx.org/advanced/transports/).
It reuses the existing development HTTPX **0.28.1** pin; no new dependency/version
was pinned or installed. It is not imported by a runtime-only application install.

## Independent workload comparison

Setup: one event loop, local in-process mock transport, fresh context-managed
client per trial, identical profile/catalog/history payloads and validation,
**40 ms deliberately delayed I/O per read**, three GETs per trial, five trials per
mode. The timed section includes client setup/close and parsing. Modes run in a
fixed sequential-then-concurrent order; this is a small demonstrative sample.

Deterministic correctness proof uses events/gates and a controlled clock: all
three concurrent reads enter before any is released; sequential mode admits one
at a time. The same workload advances **120 ms sequentially /40 ms concurrently**,
returns equivalent typed contexts and leaves zero active read tasks. No elapsed
real-time ratio is asserted by tests.

The [recorded measurement](evidence/f2-01-async-comparison.json) observed:

| Mode | Trials correct | GETs | Delayed reads/trial | Peak inflight | Median ms | Observed ms range |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sequential | 5/5 | 15 | 3 × 40 ms | 1 | 139.624 | 139.086–149.681 |
| Concurrent | 5/5 | 15 | 3 × 40 ms | 3 | 47.173 | 46.545–47.282 |

Both made exactly three requests per trial, zero retries, three dispatches and
zero provider attempts. Approximately 2.96× lower median elapsed time applies to
this synthetic I/O workload only. The final shared-check repeat observed medians
138.981/47.236 ms; normal scheduler variation does not affect the deterministic
overlap proof. No result or timing was cached. The application catalog is local,
so these artificial delays do not estimate its actual read cost or justify adding
HTTP/caching. There is no real-network, model-latency, p95/SLO or production-load claim.

## Fault and recovery evidence

| Scenario | Observed outcome |
| --- | --- |
| Required catalog version mismatch after HTTP 200 | Typed `read_invalid_result`; profile/history siblings cancelled and awaited; no context returned |
| Required response interrupted between chunks | Typed transport fault; all stream close callbacks finish; zero active children |
| Oversized streamed response | Typed oversize rejection; no retry, remaining work cancelled/drained |
| Malformed/duplicate-key/nonfinite/invalid UTF-8 response | Typed invalid result; required data never substituted |
| Wrong content type / compressed envelope | Rejected before using content |
| Optional history 503, connection failure, read timeout | Required context returned with explicit history unavailable, not fabricated successful empty history |
| Optional history 401, malformed data, redirect, 404/422, bad snapshot hash | Fatal typed failure, not degradation or redirect follow |
| Unexpected transport implementation exception | Sanitized internal read fault; raw synthetic secret absent |
| Stalled optional response | Two-second phase timeout, typed unavailable; close callbacks/children complete |
| Parent cancellation/deadline before headers or during body | All children cancelled/awaited; deadline watcher drained; a subsequent explicit batch succeeds |
| Repeated caller cancellation during gated body cleanup | Parent remains unfinished until cleanup release; no detached read tasks |
| Read budget already partly used | Reserve fails at the unchanged four-dispatch cap; zero new HTTP requests |
| Read batch inside actual Agent.session | Parent admission remains held; competing same-principal generation rejected; batch + model-selected read reach exactly four dispatches |
| Provider continuation requests excess reads | Shared tool cap fails before a fifth dispatch; no independent child budget |
| Provider transport failure after the batch | Existing provider owner retries once; HTTP reads are not replayed; conservative tokens/attempts remain within original caps |
| Provider fatal failure | Typed provider failure; no provider/HTTP retry or read-task leak |
| Nonlocal ASGI peer despite a synthetic header | Actual F1 identity middleware rejects; adapter cannot bypass it |
| Actual API + PostgreSQL A/B reads | Each receives its own saved profile; only A receives A's approved immutable history. One setup approval remains one plan; experiment performs GETs only |

The local fake tracks current child tasks and stream/handler closure. Assertions
check every tracked child is done, active count zero and fake-clock watchdog
waiters empty. Header/body/cleanup ordering uses events, not sleeps. The phase
timeout test waits for the actual timeout without asserting a fragile elapsed
duration. Benchmark sleeps are deliberately measured workload, not correctness
synchronization.

## Trace-driven investigations

1. **Real diagnostic correction:** a hanging fake provider is cancelled externally
   or by advancing the original controlled clock to its deadline. Before the fix,
   both regressions observed `agent.execute.state=model`; the explicit deadline
   cause could become generic cancellation. Root cause was result emission before
   final state transition plus generic span exception classification. After the
   correction, [cancel trace](evidence/f2-01-cancel-trace.json) shows cancelled/
   cancelled; [deadline trace](evidence/f2-01-deadline-trace.json) shows failed/
   deadline_exceeded in the run and deadline_exceeded in its session. Provider
   cancellation is correctly a child mechanism, not the overall diagnostic cause.
   Both retain **1 provider attempt, 1 uncertain attempt, 1634 reserved simulated
   input/2000 output tokens**, zero retries/reads and the original version IDs.
   Parent cancellation propagates, while deadline becomes typed budget exceeded.
   These are library/session invocations under a synthetic root span, not calls
   to an HTTP server or a live model.
2. **Partial read failure:** the controlled server returns HTTP 200 with altered
   catalog revision metadata while required profile and optional history wait.
   [Read fault trace](evidence/f2-01-read-fault-trace.json) shows successful bounded
   HTTP receipt, failed typed catalog validation, sibling cancellations, then
   `async.batch` failure `read_invalid_result`. Root cause is the injected response
   mismatch, not an HTTP outage. No application correction is needed: fail-closed
   behavior and cleanup are asserted regressions. Eight metadata-only spans link
   this experiment; no catalog records, prompts, principal or URL are recorded.

Existing ring/console policy and canary/egress tests pass. New trace attributes
have fixed allowlisted values and bounded counters; no owner/plan/candidate IDs,
hashes, request headers, payloads, URLs or exception text were added. Trace times
and opaque IDs vary; they are observations, not reproducible timing assertions.

## Exact commands and results

Windows/PowerShell, Python **3.14.9**, Node **24.22.1**, npm **11.19.1**,
HTTPX **0.28.1**, Ruff **0.17.2**, cached PostgreSQL **18.6**. Existing F1 Python/JS
pins and locks are unchanged. Installed Chrome **155.0.8059.85** was used without a browser download.
Full command sequence:

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_F2_EVIDENCE='1'
$env:FATA_BROWSER_EVIDENCE_STAGE='f2-01'
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser
.venv/Scripts/python.exe scripts/measure_async_reads.py --write-evidence
```

The comparison evidence was explicitly recorded during the targeted work; the
shared runner reruns it without overwriting that sample. No `--evidence` flag was
used on the shared runner, preserving historical F1 trace fixtures. Shared local
JSON/JUnit output remains under ignored `.cache/f107/` for compatibility.

| Exact check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_async_diagnostics.py -q --basetemp=.cache/pytest-f201-diagnostics` | Before correction: two failures (`model` vs cancelled/failed); after correction both pass |
| `.venv/Scripts/python.exe -m pytest tests/test_async_reads.py tests/test_async_diagnostics.py -q --basetemp=.cache/pytest-f201-reads` | **41 passed**, 3.83 s targeted run |
| `.venv/Scripts/python.exe -m pytest tests/test_async_reads_postgres.py -q -m integration --basetemp=.cache/pytest-f201-native` | **1 passed**, 1.53 s; real isolated SQL/API ownership case |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | 72 files formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | No OpenAPI drift; no route/schema regeneration needed |
| `npm --prefix web run check` | Strict TypeScript passed |
| `npm --prefix web run format:check` | Passed |
| `npm --prefix web run check:generated` | No TS/validator drift |
| `npm --prefix web run test` | **69 passed**, zero failures/skips; 4.939 s complete command elapsed time |
| `npm --prefix web run build` | Passed; about 343.7 KiB JS/5.7 KiB CSS before compression |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **545 passed, 74 deselected**, 14.72 s test duration |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | Actual launcher: liveness/readiness 200, rejected canary query 422, safe console/correlation and owned child cleanup passed |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **74 passed, 545 deselected**, 28.81 s; zero skips including installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | Frozen **24/24 development, 16/16 held-out**, no failed cases |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Ten correct trials, 30 total GETs, zero retries; timing evidence above |
| `.venv/Scripts/python.exe scripts/migrate.py` | `{'applied': []}`; no new migration |
| `git -c core.autocrlf=false diff --check` | Passed |
| `git check-ignore AGENTS.md` | Local instructions remain ignored |
| `docker compose stop postgres` | Container stopped; cached image and volume retained |

Final shared runner: all command exit codes 0, **70.601 s** summed child-command
elapsed time. Counts: **619 Python tests** =545 routine +74 integration; six
routine cases remain expressly reference-only approval obligations, not SQL
proof. F2-01 adds 41 routine and one native test to accepted F1's 577. The 69
frontend cases and 40-case domain evaluation are separate denominators.

All accepted native approval races, rollback, lost-response/restart, row-lock
ordering, uncertain-COMMIT reconciliation and streaming cancellation tests pass.
These use actual PostgreSQL where marked integration; new MockTransport tests do
not establish database/network correctness. The installed browser repeats the
accepted journey with zero runtime errors/external page requests, same-key retry,
immutable readback/history, owner switch and mobile error/recovery. New snapshots:
[desktop](evidence/f2-01-desktop.png), [mobile](evidence/f2-01-mobile.png),
[mobile error](evidence/f2-01-mobile-error.png). No frontend product behavior changed.

SQL aggregate checks after testing found zero leftover fixture schemas and
development approval/key/audit counts `(0,0,0)`. Normal local process access was
used for cached Docker, native SQL, npm subprocesses and installed Chrome. No
dependency acquisition or hosted CI dispatch was performed. Formatting findings
were corrected; no required final check remains failing. Process inspection found
zero remaining task-owned Chrome processes; the launcher smoke stopped its own
API child. PostgreSQL was stopped after checks, preserving its image/volume.

## Preserved boundaries, limitations and F2-02 readiness

- Contracts 12–14, API/schema artifacts, migrations, frozen corpus/catalog/report,
  baseline source hashes and dependency lock hashes are unchanged. Provider/tool/
  token/concurrency limits, terminal-only publication and approval guard/commit
  authority retain all accepted implementation tests.
- The offline experiment is fully implemented/tested but is not a production
  source or an application generation optimization. It requires the existing
  development dependency group. Real socket/TLS/proxy/pool behavior, backpressure
  on a wire and physical network failure are unverified. ASGITransport buffers
  server output; controlled stream fakes separately demonstrate body/cleanup bounds.
- The transport and caller are trusted cooperative code. A malicious/noncooperative
  callback that ignores cancellation cannot be forcibly killed by TaskGroup.
  There is no OS firewall or new sandbox claim; accepted test egress guards remain.
- Catalog reading currently requires the frozen 20-record seed to fit one page.
  Catalog expansion needs an explicit bounded-pagination/version design, not silent
  truncation. History is one bounded ID-ordered page, not a complete training history.
- Independent reads are not an atomic cross-resource snapshot. Server ownership
  is authoritative; DTOs do not carry an independently provable owner identity.
  Main-path publication/approval freshness checks remain required and unchanged.
- Required failures and optional integrity/authorization failures return no context.
  Availability degradation must be handled explicitly by a caller. Recovery is an
  explicit new read/batch, never an automatic request/model replay.
- Five samples/mode with injected I/O and fixed mode order do not establish a
  real-service speedup, production scale or caching value. No F2-02 cache was built.
- [Remaining F2 outline](../planning/16-f2-work-unit-outline.md) proposes separately
  authorized cache/performance, contained LangGraph comparison and explicit
  completion/feedback units. No related dependency, schema, endpoint or workflow
  has been implemented here. F2-02 should begin by establishing a real catalog-read
  cost/key/invalidation hypothesis rather than assuming this delayed workload
  justifies caching.

No known F2-01 blocker remains. Ready for owner review and, only with separate
authorization, F2-02. Stop after this work unit; no commit or push.
