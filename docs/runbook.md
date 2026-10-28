# Local synthetic F1 runbook

For the current portfolio journey and disposable-data commands use the
[local demonstration](local-demonstration.md). Milestone status labels below are
historical; evidence-writing flags deliberately reproduce earlier artifacts and
must not be used for a publication check that preserves accepted evidence.

This setup supports one API process/event loop on `127.0.0.1:8000`, two developer
identity selectors, the deterministic fake provider and PostgreSQL on
`127.0.0.1:55432`. It is not production authentication or a participant deployment.
Use synthetic adult preferences only. No provider or telemetry credentials are
needed; supplying them cannot enable a live integration. F1 and F2 are
owner-accepted and closed; F3 through F3-05A is accepted for its authorized offline
scope. Live-provider and hosted-export NO-GO remains. F4-01's local container
release and F4-02 offline preparation are owner-accepted. F4-03A's
[targeted preflight](implementation/f4-03a-handoff.md) awaits review and authorizes
no cloud operation. The separate local
[release and recovery instructions](local-release.md) cover image builds, host
networking, startup, backups, restore, faults and rollback. Development and release
use the same loopback ports and must not run simultaneously. AWS is planned only.

## Acquire the pinned environment once

Run from the repository root in PowerShell. Prerequisites: uv 0.13.5, Node 24.x,
Docker Desktop with a working Linux engine. Installation/image acquisition needs
network access; routine tests do not acquire dependencies or call providers.

```powershell
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.tools/python'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
uv python install 3.14.9 --install-dir .tools/python --no-bin --no-registry
uv sync --frozen
npm --prefix web ci --ignore-scripts --cache .cache/npm
docker compose pull postgres
```

Keep `.env`, local credentials, caches and `AGENTS.md` ignored. `.env` is not loaded.
Use the existing Python/JS lockfiles; do not run unrestricted dependency upgrades.
On Linux substitute `.venv/bin/python` and `.venv/bin/ruff` for Windows paths.

## Start and migrate

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
npm --prefix web run build
$env:FATA_ENV = 'local'
$env:FATA_LOCAL_DEV = '1'
.venv/Scripts/python.exe scripts/serve.py
```

Migration startup is explicit. The runner verifies normalized source checksums and
atomically applies missing migrations/history under a database advisory lock.
001/002/003 create foundation metadata, saved profiles and approved snapshot/key/
audit records. Repeat execution applies nothing. Never edit a migration already
applied to the volume; investigate a checksum mismatch before starting the app.
No downgrade or automatic schema repair is provided.

The launcher fixes one worker, loopback bind, proxy headers disabled, fake provider
and no exporter. Unsafe configuration fails closed. Open
`http://127.0.0.1:8000/`; select profile A or B, attest synthetic adult preferences
and explicitly Save. Generate, review, optionally revise once, then explicitly
Approve. Successful approval requires owned durable readback. Saved history shows
the original snapshot even after a later profile Save.

Use Ctrl+C to stop the API. Do not expose it through a proxy, public bind or
additional workers. There is no separate frontend service.

## Liveness and readiness

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
```

`/health` is process liveness and stays 200 during database failures. `/ready`
returns `ready_local`/200 only if local fake configuration, loaded catalog, built
index/JS/CSS and the database probe pass. The probe is read-only, bounded to
three seconds overall (native SQL/connect path two), and checks migration history
checksums plus required columns and read permissions. Failure returns a fixed
`unavailable`/503 body with boolean checks, never a connection string or exception.
It does not inspect all user rows, certify every constraint, indicate available
generation slots, or resolve quarantined candidate lineages.

If readiness fails: check `docker compose ps`, start Docker's engine if needed,
run migrations, rebuild web assets, and confirm `FATA_LOCAL_DEV=1`. Do not disable
ownership, version checks, body limits or SQL timeouts to obtain a green result.

## Reproduce checks

Routine checks need installed dependencies, no DB, no credentials and no web
build beforehand. The shared runner builds assets before running tests:

```powershell
.venv/Scripts/python.exe scripts/check.py
```

For full evidence, migrate/start the DB first and use an already installed Chrome:

```powershell
$env:FATA_BROWSER_EXECUTABLE = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser --evidence
```

The full runner refuses a missing browser and rejects skipped integration cases.
It runs Python lint/format, OpenAPI and TS/validator drift, strict TypeScript,
frontend formatting/tests/build, routine pytest, real-launcher smoke, native SQL/
browser integration, then the frozen baseline check. Native fixtures create/drop
isolated schemas on the dedicated local synthetic database. The launcher smoke
only reads the development database, refuses an occupied port 8000, and stops only
its own child process. It does not approve anything or change profiles.

Results/durations: `.cache/f107/check-results.json`; JUnit denominators:
`.cache/f107/unit.xml` and `integration.xml`. `--evidence` explicitly refreshes
`docs/implementation/evidence/f1-07-*-trace.json` and browser screenshots using
synthetic fixtures. Trace timings/opaque IDs vary; frozen baseline checks remain
byte/source-hash reproducible. No browser download happens during tests.

Focused commands remain available:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest -q -m integration --basetemp=.cache/pytest-local
.venv/Scripts/python.exe scripts/smoke_local.py
.venv/Scripts/python.exe scripts/export_contracts.py --check
npm --prefix web run check:generated
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
```

Unset `FATA_BROWSER_EXECUTABLE` only when deliberately excluding the optional
standalone browser test. This is not complete F1 acceptance evidence. Test temp
files stay in `.cache`; use distinct `--basetemp` directories for simultaneous
manual suites. The runner bounds ordinary checks to 180 seconds, the expanded
routine Python suite to 2400 seconds and the native integration suite to 900
seconds. F5-D1 measured the Windows aggregate above 20 minutes and native
integration at 412s; these test-phase allowances do not change application or
browser deadlines. Failures still stop subsequent checks. See the
[current demonstration](local-demonstration.md).

CI uses `.github/workflows/offline.yml`, Ubuntu 24.04, pinned action SHAs, Python
3.14.9/uv 0.13.5, Node 24.22.1 and the Compose image digest. Acquisition precedes
offline checks. The installed system Chrome is required; absence fails rather
than downloading or silently skipping. CI has read-only repository permission,
no provider secrets, deploy step, hosted exporter or paid-service requirement.
The workflow has been parsed and its check sequence run locally; a hosted job is
not claimed until an authorized push/dispatch actually runs it.

## Diagnose a request without content capture

Every HTTP response gets a server-generated opaque `X-Request-ID`. Generation's
SSE envelope uses that same ID. Caller `X-Request-ID`/`traceparent` values are not
trusted. Each request has its own trace; there is no persistent user/session
correlation identity. Owned COMMIT tasks inherit request context.

The supported launcher has one JSON console logging sink. To keep a local copy,
create the directory first and explicitly redirect stderr:

```powershell
New-Item -ItemType Directory -Force .cache/f107 | Out-Null
.venv/Scripts/python.exe scripts/serve.py 2> .cache/f107/runtime.jsonl
```

Use the response header from browser network tools; filter locally:

```powershell
$requestTraceId = 'replace-with-response-x-request-id'
Get-Content .cache/f107/runtime.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object trace_id -EQ $requestTraceId
```

The application also keeps the newest 2048 completed spans in
`app.state.tracer.snapshot()` (hard configurable construction cap 4096). Snapshot
returns copies. `tracer.dropped` counts overwritten spans; a partial trace does
not prove missing work did not happen. No trace HTTP endpoint, exporter, file
exporter, background collector or new service exists. Restart loses the ring.

Allowed fields include static stage/route/tool/outcome/reason, durations, attempt/
tool/retry/repair counters, conservative simulated token consumption and known
profile/catalog/validator/prompt/tool/output/model revisions. IDs in a trace are
random correlation IDs only. Raw prompts, plan/exercise content, request headers,
URL/query, credentials, owner/user/candidate/plan IDs, hashes and idempotency keys
are omitted. Versions are value-allowlisted, not arbitrary provider strings.
Unrecognized runtime logs become level-only records; raw exception/SQL text and
access logs are intentionally omitted. This is a privacy tradeoff, not a full
debugger. Custom embedding handlers are outside the supported launcher configuration.

For SSE, HTTP 200 can still carry `done(error)`. Inspect `stream.terminal` and
`agent.execute` business outcomes, not status alone. `terminal_complete` means the
ASGI send returned, not guaranteed browser receipt. `cancelled_cleanup` separates
a late transport cleanup cancellation from the already sent business outcome.

The saved induced-failure trace shows `http -> agent.session -> agent.execute`,
three provider spans, a read tool and two rejected validation spans, followed by
`done(error)`. `semantic_repair_exhausted` explains why a second invalid proposal
could not repair again. Budgets and versions are present; invalid proposal bodies
are absent. Reproduce with:

```powershell
$env:FATA_WRITE_EVIDENCE='1'
.venv/Scripts/python.exe -m pytest tests/test_observability.py -q
Remove-Item Env:FATA_WRITE_EVIDENCE
```

## Failure and restart recovery

| Symptom | Action and invariant |
| --- | --- |
| Stalled request body | Intake is bounded to five seconds/16 KiB; typed 503 on timeout. Generation's 30-second deadline starts before intake and includes that time. No admission/provider work starts from an incomplete body. |
| 429 generation capacity | One active run per principal, two globally. Stop an active generation or wait; never enable extra workers. |
| Stream disconnect/EOF/deadline | Incomplete preview is non-approvable; no automatic replay. Explicitly generate/revise again within the existing lifecycle rules. |
| Stale profile or superseded/expired candidate | Reload profile, generate and review fresh output. Do not alter a hash/revision to force approval. |
| Database unavailable | Health can stay green, readiness and business calls fail closed. Restore DB, run readiness, then retry deliberately. No in-memory durable-plan fallback. |
| Save response lost | GET current profile revision. Do not assume rollback or blindly overwrite a newer revision. |
| Approval response/readback lost | Retry exactly the same page-local approval key/request. Never invent a new key to resolve uncertainty. |
| `reconciliation_pending` | Restore authoritative DB access and retry the same key. Lineage stays blocked against approval, revision publication and eviction until its transaction lock/state is resolved. No background worker or force-reset button. |
| API restart | Candidates/reservations/UI context disappear. Committed key bindings and snapshots survive; a retained matching key can recover without a candidate. Otherwise use owned saved history. Unapproved drafts require fresh review. |

Stop API first with Ctrl+C, then stop PostgreSQL:

```powershell
docker compose stop postgres
```

This preserves the image and volume. Restart using the startup sequence. The
browser's idempotency attempt lives only in page memory; reload loses it, while
history remains authoritative. Approved records are append-only and never updated
when the current profile/catalog changes. History uses opaque ID keyset order,
not approval time; Refresh finds inserts before an existing page cursor.

## F2-01 offline async-read experiment

This developer experiment is separate from the application path and uses the
existing development HTTPX dependency. It accepts only explicitly injected
`MockTransport`/`ASGITransport`, fixed GET routes and a captured synthetic principal;
there is no socket/live-source configuration. Profile, raw catalog and a bounded
owned-history page are independent reads. Filtering follows the required reads.
Required failures cancel/await siblings; optional history availability failures
are explicit. Authorization, redirects and integrity failures are fatal.

The caller must keep its existing `Deadline.scope()` or `Agent.session()` open
around `read_context(reads, deadline, budget)`. The batch reserves three dispatches
from the supplied budget before starting any child; it never resets the parent
deadline or retries a read. It is not a generation entry point or a new model tool.
Do not call these local API routes over real loopback HTTP from the application
merely to manufacture parallelism; its direct services remain the supported path.

```powershell
.venv/Scripts/python.exe scripts/measure_async_reads.py --write-evidence
$env:FATA_F2_EVIDENCE = '1'
.venv/Scripts/python.exe -m pytest tests/test_async_reads.py tests/test_async_diagnostics.py -q
```

The comparison uses identical three-read synthetic workloads, five trials per
mode and 40 ms deliberately simulated I/O per read. It reports request counts,
inflight peaks, equivalent outcomes and elapsed samples; timing is never a pass
threshold. Separate controlled-clock/gate tests prove overlap and cleanup.

For all regressions, use the existing DB/migration/browser setup, then:

```powershell
$env:FATA_BROWSER_EVIDENCE_STAGE = 'f2-01'
.venv/Scripts/python.exe scripts/check.py --integration --browser
Remove-Item Env:FATA_F2_EVIDENCE
Remove-Item Env:FATA_BROWSER_EVIDENCE_STAGE
```

Do not pass `--evidence` here: that flag refreshes historical F1 trace fixtures.
F2's explicit variables write new F2 traces/screenshots. Shared check/JUnit paths
remain `.cache/f107/` for compatibility and are ignored, not historical records.
`scripts/check.py` now also runs the async comparison without overwriting its
saved measurement. The [F2-01 handoff](implementation/f2-01-handoff.md) and
[async audit](implementation/f2-01-async-audit.md) distinguish these experiments
from native SQL regressions and real-network behavior.

## F2-02 profiling and rejected cache prototype

The application remains uncached. The catalog is already loaded once into
canonical in-memory bytes; a tested catalog-only projection prototype remains
off the application path. It is not enabled by any setting or API parameter.
See the [decision](implementation/f2-02-cache-decision.md) before considering adoption.

These commands perform real local work without artificial delays. Evidence writes
are explicit; new timings will vary and are not CI pass/fail thresholds:

```powershell
.venv/Scripts/python.exe scripts/measure_catalog.py --write-baseline
.venv/Scripts/python.exe scripts/measure_catalog.py --compare --write-comparison
.venv/Scripts/python.exe scripts/measure_catalog.py --profile --write-profile
```

For the native API comparison, start/migrate local PostgreSQL first, then:

```powershell
.venv/Scripts/python.exe scripts/measure_catalog.py --api --write-api
.venv/Scripts/python.exe scripts/measure_catalog.py --manifest
```

The native comparison uses actual generation endpoints, two synthetic principals,
real PostgreSQL in one uniquely named disposable schema and the fake provider.
Profile Saves are explicit setup outside the generation timer. It never approves;
all unapproved candidates stay transient. The fixture schema is dropped on exit.
It benchmarks ASGI delivery, not TCP/TLS, browser paint or a real model. No service,
cache daemon or dependency installation is needed. Avoid other benchmark/test jobs
while collecting samples. The eight baseline plans and per-episode warm-ups prime
the existing arithmetic memo equally before the measured modes.

Raw timings/profiles and the reproduction/lock hashes are under
`docs/implementation/evidence/f2-02-*.json`. The full regression command retains
the existing DB/browser prerequisites and avoids overwriting historical traces:

```powershell
$env:FATA_BROWSER_EVIDENCE_STAGE='f2-02'
.venv/Scripts/python.exe scripts/check.py --integration --browser
Remove-Item Env:FATA_BROWSER_EVIDENCE_STAGE
```

Do not set `FATA_F2_EVIDENCE` or pass the runner's `--evidence` flag for this unit;
those explicitly refresh older F2-01/F1 diagnostic fixtures. No performance
threshold is installed in CI. Normal pytest discovers the cache correctness and
measurement-accounting cases. F2-02 is owner-accepted; its evidence is preserved.

## F2-03 isolated LangGraph experiment

The application continues using typed orchestration. This experiment requires a
separate environment/lock and is not imported or discovered by routine app tests.
For first acquisition (PyPI network required), then offline execution:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
uv sync --project experiments/langgraph --frozen --python .venv/Scripts/python.exe
experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py demo
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py compare
```

After acquisition use `uv sync --project experiments/langgraph --frozen --offline
--python .venv/Scripts/python.exe`. Never add LangGraph to root dependencies or
regenerate the frozen baseline. `demo` exits the original interpreter and launches
fresh interpreters to resume and repeat-read real SQLite state. It removes its
unique database and sidecars afterward; `compare` does likewise for each trial.
Add `--write-evidence` only to these two commands to explicitly replace their new
F2-03 JSON reports. Historical evidence is never refreshed.

For an individually inspected synthetic checkpoint, all within 30 seconds:

```powershell
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py start --database manual-demo
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py inspect --database manual-demo
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py resume --database manual-demo
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py cleanup --database manual-demo
```

The pause is a synthetic preview gate, never user approval. Pausing releases active
admission but preserves the original deadline and counters. An expired checkpoint
cannot resume; cleanup remains possible. Pending provider/tool operations fail
closed rather than silently replay. Only fixed synthetic fixtures are accepted;
never copy real profiles, prompts or credentials into checkpoint files.
Restoration uses the larger of wall/monotonic elapsed time and rejects negative
elapsed values; only same-machine, same-boot process restart is supported.

Files live only in ignored `.cache/f203/`, one fixed thread per database. The
16 MiB SQLite main-page limit excludes WAL/SHM and Python memory. State is limited
to 128 KiB; graph execution has a 64-step recursion bound. No TTL worker, application
checkpoint store, external endpoint or multi-process concurrency guarantee is
introduced. Manual files persist until explicit cleanup; there is no secure-erasure
claim. Process crash leftovers require the same named cleanup command after the
owning process exits.

The isolated lock includes transitive LangSmith/SDK dependencies; hosted callbacks
are explicitly disabled and experiment invocation denies sockets/DNS. Environment
credentials cannot activate a live provider. No model integration is supplied.
Use the full application check runner separately with browser evidence stage
`f2-03`, without `FATA_F2_EVIDENCE` or `--evidence`. See the
[F2-03 handoff](implementation/f2-03-handoff.md). F2-04 requires separate authorization.

## F2-04 explicit completion and feedback

Start/migrate the existing local PostgreSQL instance before launching the app:

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
```

Migration `004_session_records.sql` adds `session_records` and `session_idempotency`,
owned approved-plan foreign keys, actual-session/snapshot checks, unique key and
session constraints, deferred key binding and append-only guards. Existing
migrations/checksums stay unchanged. Readiness requires the new schema; liveness
does not imply database readiness. There is no automatic downgrade/reset.

Use the actual UI: Save → Generate → Review → optional Revise → Approve → durable
readback/history → choose session status and optional feedback → **Submit session
record**. Forms appear only for an approved saved snapshot. Viewing, approval,
selecting status and selecting ratings never submit. Status starts unselected.
Supported statuses are completed/partial/skipped; perceived effort and 1–5 session
rating are optional, and unavailable for skipped sessions. No notes or health data.
These are synthetic self-reports, not verification that exercise occurred.

Each numbered session of that saved weekly snapshot has at most one immutable
revision-1 record; there is no correction or recurring-occurrence calendar in
this unit. Submit expects revision 0 plus the approved snapshot's revision/hash.
Current profile/catalog changes cannot rewrite the plan or its session records.
To review older records, open their saved plan from owned history.

On response loss, **Retry the same submission** uses the retained exact request/key;
there is no automatic POST retry. While uncertain, inputs are disabled. Explicit
Submit may finish after disconnect/navigation. After reload, inspect saved records
before submitting again; keys are page-local, never written to browser storage.
A different key for an existing session conflicts rather than overwriting or
creating a duplicate. A key reused with a different fingerprint conflicts even
across sessions. Open/reload owned records after definite conflicts.

Endpoints: POST/GET `/api/v1/plans/{plan_id}/sessions/{day_index}/completion`, GET
`/api/v1/plans/{plan_id}/completions` (at most four sorted records). Local identity
and ownership apply. JSON extra fields, health notes, duplicate keys, nonfinite
numbers and skipped feedback fail closed. POST bodies are capped at 4096 bytes;
completion responses carry `Cache-Control: no-store`. No plan body or client owner
is accepted, and no LLM tool can submit or access these records.

Native transactions serialize owner/key before owner/plan/session, with one
bounded transaction and no profile lock. A COMMIT error returns retryable
`reconciliation_pending`; retry the same key. PostgreSQL locking and committed key
lookup decide the result. Do not invent a new key to bypass a pending outcome.
No in-memory finalization, recovery worker, graph or queue is involved.

Current full acceptance commands (installed dependencies/Chrome required):

```powershell
Remove-Item Env:FATA_F2_EVIDENCE -ErrorAction SilentlyContinue
$env:FATA_F204_EVIDENCE='1'
$env:FATA_BROWSER_EVIDENCE_STAGE='f2-04'
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser
experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q
Remove-Item Env:FATA_F204_EVIDENCE
Remove-Item Env:FATA_BROWSER_EVIDENCE_STAGE
```

`FATA_F204_EVIDENCE` writes only the new session fault trace. Do not pass
`--evidence`, which refreshes historical F1 artifacts. The old F2-01 evidence switch
also stays unset. Ordinary tests do not rewrite recorded evidence. The shared
runner exercises the F2-01 reads, F2-02 correctness tests and frozen baseline;
the separately locked graph suite verifies F2-03 without installing it in the app.
Native tests use disposable owned test schemas. Stop the database afterward with
`docker compose stop postgres`, preserving the volume.

See [F2-04 handoff](implementation/f2-04-handoff.md) and
[final F2 evidence](implementation/f2-acceptance-report.md) for actual denominators,
fault scope and the retained no-cache/no-production-graph decisions.

## Retention and evidence limits

Unapproved payloads have a 30-minute monotonic TTL and bounded memory; expiry is
lazy/on access, not secure erasure. Saved synthetic profiles and approved records
persist in the local Docker volume until the owner deliberately resets that
disposable environment. There is no participant deletion endpoint or production
retention policy. Test fixture cleanup drops only its uniquely named test schema.
Completion/feedback and their key bindings share this synthetic local retention;
they are not automatically expired. A production deletion/correction/backup policy
must be designed before any real-user enrollment. No reset was executed here.
Do not use `docker compose down --volumes` for routine cleanup: it destroys all
local profiles, plans, audit and retry bindings. No such reset was performed here.
Real-user enrollment requires separately designed access/consent/deletion rules.

Python test guards deny external TCP, alternate connects, UDP and DNS paths;
frontend unit guards deny fetch/sockets/DNS. Installed-browser page requests are
restricted to localhost, with background-network features disabled. These are
cooperative process/test restrictions, not an OS-wide firewall against malicious
plugins, arbitrary child processes, or every browser-internal network feature.
No live-capable provider transport/SDK or telemetry exporter exists. F3-02's
Responses wire adapter accepts only in-memory MockTransport replay.

Local/fake measurements establish software constraints and tested SQL behavior,
not personalized training quality, exercise safety, real token charges, production
scale, hosted observability operation or AWS experience. See the acceptance report
for denominators, measured timings, fault injection methods and remaining limits.

## Offline Responses and spending controls

Current hardening: F3-03D adds migration 008, one bounded numerical observation per
operation and atomic project freeze. Preserve unknown holds; SQL reconciliation
does not settle billing or unfreeze. Conflicting observations never overwrite
the first; there is no automatic correction/refund. No provider/native content
is stored. Current browser evidence stage is `f3-03d`, without historical
evidence-writing flags. Run the ordinary migration/check commands below with
that stage. No real provider connector, positive live permit or credential setup
exists. Counting price/retention and separate execution approval remain blockers.

TLS/socket checks require local OpenSSL (Ubuntu CI, or Git for Windows' bundled
binary) and loopback sockets. They generate synthetic keys/certificates only in
ignored test directories, never Git. All compressed provider-shaped replies are
rejected before decoding; requesting identity encoding does not imply trusting a
server to honor it. Emergency `await replay.stop()` disables future claims under
the ledger guard and cancels/awaits owned runs. A claimed send can remain charged
after stop. Do not delete holds or restart/replay a request as recovery. See the
[handoff](implementation/f3-03d-handoff.md) for exact fault/transport evidence.

**Current F3-03B usage:** the old F3-02 evidence commands below are historical
reproduction instructions. For current checks, set browser evidence stage
`f3-03b` and leave all historical evidence-writing flags unset. Migrations 006–007
add empty `spend_pairs`/`spend_operations` and fixed quote provenance; migrate normally.

```powershell
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-03b'
.venv/Scripts/python.exe scripts/check.py --integration --browser
Remove-Item Env:FATA_BROWSER_EVIDENCE_STAGE
docker compose stop postgres
```

The count-aware mocked harness needs explicit trusted replay ledger setup; normal
startup still creates no grant or permit. Use `await ledger.reconcile_mixed(project)`
for mixed numeric state; the legacy `reconcile` reads only generation-only rows.
Both paths' financial ceilings include all liabilities under the project lock.
Unknown count state `sent` and successful-but-unbilled `responded_held` retain
their full synthetic maxima. Neither a count number nor database reconciliation
establishes a refund. Restart discards native/ticket state; do not replay generation.
Only still-reserved operations can be released after an explicit abandoned run.
Known synthetic count costs can settle a held count explicitly, never automatically.
Stop prevents new claims; already committed claims can remain uncertain/charged.
There is no worker, billing lookup, automatic unfreeze or live transport.
See [provider safety](../contracts/provider-safety.md),
[handoff](implementation/f3-03b-handoff.md) and
[next approval checklist](planning/19-f3-03c-pre-live-readiness.md).

See [the handoff](implementation/f3-02-handoff.md) and
[provider safety contract](../contracts/provider-safety.md). Install no extra
package: the existing dev group pins HTTPX 0.28.1. Application configuration is
still fake-only; credentials, `LivePermit` values and an enable flag cannot pass
the unresolved real-input admission gate. There is no live transport constructor,
permit file, activation command or funded default grant.

With the existing cached local PostgreSQL container available:

```powershell
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
.venv/Scripts/python.exe scripts/prepare_responses.py --check
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-02'
$env:FATA_F302_EVIDENCE='1'
.venv/Scripts/python.exe scripts/check.py --integration --browser
Remove-Item Env:FATA_F302_EVIDENCE
Remove-Item Env:FATA_BROWSER_EVIDENCE_STAGE
docker compose stop postgres
```

Do not pass `--evidence` or set old F1/F2 evidence flags when preserving historical
reports. F3-02 writes only its own replay failure trace and browser screenshots.
`prepare_responses.py` without `--check` deliberately regenerates the five
versioned assets; review diffs, including case eligibility and fixture digests.
Never regenerate the frozen baseline to accommodate a provider schema.

Migration 005 adds four empty replay-only spending tables, no business-record
changes or live permit. Native tests create/drop isolated synthetic schemas;
normal startup never creates a grant. The trusted Python ledger API is not an
HTTP endpoint or LLM tool. Inspect unresolved attempts using
`await ledger.reconcile(project_id)` in a controlled offline harness. It acquires
the project lock and returns numeric state; it does not query provider billing,
refund unknown charges, replay requests or release sent claims.

If a transaction acknowledgement is uncertain, resolve its database ordering by
reconciliation before retrying. If the state is `sent`, retain its full allowance
until known authoritative usage can settle it. Missing usage, restart, elapsed
time and cancellation do not prove a free request. A pricing discrepancy freezes
the project; no automatic unfreeze or alternate pricing is provided. There is
no cleanup daemon: retain unresolved metadata; review resolved synthetic billing
records for manual cleanup after 90 days. Do not delete tables/rows as recovery.

The ordinary launcher remains unchanged: no provider sockets, hosted telemetry
or new service. Five-second cooperative ledger-operation timeout and SQL limits
bound owned transaction work; cancellation drains it before returning and before
another dispatch. Emergency stop disables new send claims, while preserving
pending liabilities. No claim is made about real billing/transport or physical
power-loss recovery. F3-03 live experiments remain blocked pending the documented
input-count decision and separate owner/provider/privacy/numeric authorization.
