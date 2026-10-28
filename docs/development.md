# Local environment, contracts and offline domain baseline

For the current application, start with the [architecture](architecture.md),
[local demonstration](local-demonstration.md) and [release readiness](portfolio-readiness.md).
The milestone inventory below preserves earlier implementation history; its old
review-status labels are not the current authorization state.

F0 and the complete F1 slice are owner-accepted and closed; historical evidence is retained.
F2 is owner-accepted and closed. F3 through F3-05A is accepted for its offline
scope; live-provider/export gates remain blocked. F4-01 local release is
owner-accepted; F4-02 offline infrastructure is accepted and F4-03A
[targeted preflight](implementation/f4-03a-handoff.md) awaits review.
No subsequent unit or cloud operation is
authorized. See [container release/recovery](local-release.md),
[F4-01 evidence](implementation/f4-01-handoff.md) and the
[AWS design proposal](planning/22-f4-deployment-and-cost-plan.md).
See the complete [local runbook](runbook.md) for setup, diagnosis and recovery.

## Implemented versus specified

- Implemented: strict Pydantic structures and static matrix bounds, fixed limit
  descriptors, fail-closed local settings, process `/health`, dependency `/ready`,
  a checksum-checked transactional bootstrap migration, offline contract export,
  generated TypeScript types, and local foundational tests.
- F1-03 implemented: protected `GET/PUT /api/v1/profile`, PostgreSQL optimistic
  Save, internal in-memory candidate lifecycle, and owner-scoped plan-read
  interfaces. The design OpenAPI marks implemented routes `implemented-local`.
- Reference tests only: `tests/specification` models the guard recheck and
  cancellation/reconciliation obligations in `contracts/approval-safety.md`.
  Their passing is not a PostgreSQL approval/concurrency/restart proof.
- F1-02 implemented: contract-12 duration arithmetic, independent catalog/business
  validator, 20-record versioned catalog, deterministic template planner and
  frozen 40-task corpus/report. Use the pure functions in `future_training.domain`;
  no HTTP route, user identity, candidate publication or database write is added.
- F1-04 implemented: fake-only internal typed orchestration, bounded catalog and
  owned profile reads, authoritative domain validation, one semantic repair and
  whole-request budgets. It creates no candidate identities and exposes no new
  HTTP routes. Its tests exercise the implementation, not a specification model.
- F1-05 implemented: direct POST initial/revision SSE, protected bounded catalog
  reads, same-origin React workspace, strict browser framing/schema/hash checks,
  explicit Stop and terminal-only transient publication.
- F1-06 implemented: native PostgreSQL atomic approval, durable idempotency,
  guarded commit reconciliation, immutable snapshots, owned readback/history and
  React consent/retry/readback. Native integration tests exercise actual SQL
  locks, constraints, commit faults and process restart. Reference models above
  remain separately labeled. No LLM SDK or exporter is installed or enabled.
- F1-07 implemented: bounded local metadata traces and safe console formatting,
  readiness probes, request-intake bounds, shared offline check runner, CI workflow,
  privacy/egress tests and final browser/native-SQL acceptance evidence.
- F2-01 implemented: contained typed async HTTP reads with explicit local transports,
  shared deadline/read budget, structured child cleanup and sequential/concurrent
  evidence. The application does not route its internal reads over HTTP. This
  offline experiment uses existing development HTTPX; no dependency lock changes.
  Cancellation trace state/cause ordering is corrected without changing the
  accepted cancellation or approval transaction policy.
- F2-03 implemented in a separate environment: synthetic LangGraph/SQLite workflow,
  persisted interruption/restart/resumption, conservative replay accounting and
  comparison tests. No application imports, dependency-lock changes or graph authority
  over candidates/approval. See the [experiment](../experiments/langgraph/README.md)
  and [handoff](implementation/f2-03-handoff.md). Retain typed application orchestration.
- F2-04 implemented: additive strict completion/feedback schemas, owned immutable
  session Submit/readback, atomic PostgreSQL key binding, concurrency/unknown-commit
  recovery, and a narrow explicit React workflow. Contracts are in
  [completion-feedback.md](../contracts/completion-feedback.md); no model write tool
  or automatic completion is available. Apply migration 004 before startup.

The F1-01 provenance seed remains a synthetic schema fixture and is not loaded
by the F1-02 catalog. See `data/catalog/README.md` for actual metadata provenance
and remaining human-review requirements. Unknown IDs/tags, duration arithmetic
and constraint feasibility are independently checked by `domain.validator`;
schema parsing alone still proves none of these and never proves consent/auth.
Pydantic model instances are transport data; immutable candidate snapshots and
agent results use canonical server-owned bytes rather than mutable containers.

## Install once (network required for dependency acquisition)

Prerequisites: uv 0.13.5, Node 24.x/npm, Docker Desktop with its Linux engine.
All commands below run from the repository root in PowerShell. No `.env` or live
provider credentials are required. Never put real user data in this environment.

```powershell
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.tools/python'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
uv python install 3.14.9 --install-dir .tools/python --no-bin --no-registry
uv sync --frozen
npm --prefix web ci --ignore-scripts --cache .cache/npm
docker compose pull postgres
```

Python/venv/cache stay in the workspace. `uv.lock` locks transitive packages and
hashes; `web/package-lock.json` locks JS packages and integrity. Run `uv sync
--frozen --offline` after acquisition, and use `.venv/Scripts/python.exe` directly
for routine offline checks. Dependencies are not downloaded by test execution.
Python 3.14.9 is the selected runtime; other Python minors are outside this lock's
tested project envelope. Do not run unrestricted upgrades as part of routine tests.

## Offline checks

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/ruff.exe check src scripts tests --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests --no-cache
.venv/Scripts/python.exe scripts/export_contracts.py --check
npm --prefix web run check
npm --prefix web run check:generated
npm --prefix web run format:check
npm --prefix web run test
npm --prefix web run build
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
```

Default pytest excludes `integration`, blocks non-loopback sockets and external
DNS, and uses no wall-clock-dependent data or provider. Loopback control sockets
are permitted for the Windows asyncio event loop; no database is required by the
default suite. This is an in-process test-network guard, not an OS firewall for
arbitrary child processes. Actual external providers remain absent.

To regenerate contracts after an authorized schema edit:

```powershell
.venv/Scripts/python.exe scripts/export_contracts.py
npm --prefix web run generate
```

OpenAPI marks implemented business operations `x-implementation: implemented-local`. JSON
Schema/TypeScript describe shapes, not authorization, stream sequence or catalog
validation. The sequence and approval guarantees are normative in planning 13/14
and `contracts/approval-safety.md`; F1-05/F1-06 runtime tests enforce them.

## Offline domain baseline

```powershell
.venv/Scripts/python.exe scripts/evaluate_baseline.py
.venv/Scripts/python.exe -m pytest tests/test_domain.py tests/test_evaluation.py -q
```

`data/evaluation/README.md` describes the frozen split, outcome scoring and report.
The template uses all allowable integer prescriptions from contract 12, preferring
4/5/6 distinct exercises for 20/30/45-minute presets, then other feasible counts.
Within a count it chooses the closest estimate to the target (ties shorter).
It prefers three-set prescriptions, then fixed rest/work ordering, and rotates
eligible IDs across days. A finite bitset feasibility table keeps the search
bounded; it does not invent exercise rules or claim fitness optimization.

Always call `validate_plan(proposal, expected_profile, catalog)` with separately
supplied application constraints. The validator never treats the proposed embedded
profile or a preconstructed Pydantic object as authoritative. The planner uses
that same validator before returning a plan. It never relaxes exclusions or fills
time with invented blocks. Uninterpreted free text requests clarification; if
the user declines changes the baseline abstains. This is not an NL or medical
classifier and has no tool calls. F1-04 composes it through the fake provider.

## Local PostgreSQL bootstrap (opt-in integration checks)

```powershell
docker compose up -d --wait postgres
.venv/Scripts/python.exe scripts/migrate.py
.venv/Scripts/python.exe -m pytest -q -m integration --basetemp=.cache/pytest-f106
docker compose stop postgres
```

Only `127.0.0.1:55432` is published, using Docker's standard bridge network.
Routine test egress is blocked by pytest, not a Docker firewall. Trust
authentication intentionally avoids a checked-in password for this
synthetic local database; any local process can access it. It is not an external
deployment configuration. Database/user are `training_dev`; the migration command
can connect only to its fixed local target. Migration 001 creates schema history
and foundation metadata; 002 adds `profiles` (owner PK, positive revision, JSONB
preferences). Migration 003 adds append-only `approved_plans`,
`approval_idempotency` and `approval_audit`. Hash/identity checks, owner-scoped
uniques and composite foreign keys protect the atomic approval records.
UPDATE/DELETE/TRUNCATE triggers reject mutation; privileged schema changes remain
outside this local application's threat boundary. No draft/checkpoint table exists.
Application startup does not run migrations or automatically save profiles.
Migration checksums
normalize line endings for Windows/Linux portability. Failed migrations roll back
their SQL and history together. New migrations require a later authorized unit.

`stop` preserves the project volume; `docker compose down` also preserves it.
Do not use `down --volumes` unless deliberately deleting disposable project data.
No destructive reset is needed for these tests. No database downgrade is provided
for the initial bootstrap. Schema rollback strategy for real product releases
remains later work.

## Run the local workspace

```powershell
$env:FATA_ENV = 'local'
$env:FATA_LOCAL_DEV = '1'
npm --prefix web run build
.venv/Scripts/python.exe scripts/serve.py
```

This launcher fixes one worker and host-loopback binding, with access logs off.
It disables proxy headers and selects a Windows-compatible selector event loop
for native async Psycopg. Only this single-process launcher is supported; do not
add workers, expose a proxy or override the bind flags.
`GET /health` returns 200 for process liveness. `/ready` returns 200 `ready_local`
only with local opt-in, fake mode, a matching/reachable database schema, loaded
catalog and built web assets; otherwise 503 `unavailable`. It certifies none of
production security, multi-worker support or provider quality. Use the supported
launcher. `FATA_HOST`, `FATA_WORKERS`, `FATA_PROVIDER`, `FATA_ENV` and
`FATA_TELEMETRY_EXPORTER` reject unsafe values. API access defaults to disabled
unless `FATA_LOCAL_DEV=1`. `.env` is not loaded. Supplying an
LLM key or an OTel endpoint cannot create a live provider/exporter path.

## Synthetic identity and explicit profile Save

`X-Synthetic-Principal` must be exactly `synthetic-a` or `synthetic-b`, once.
Missing/unknown/duplicate identity is 401. Disabled/nonlocal mode, non-loopback
peer/listener, hostile Host/Origin and forwarded headers are 403. No proxy-derived
identity is trusted. Browser requests must be same-origin; CORS is not enabled.
This header is a **local developer identity selector**, not a credential: a local
process can select either principal. Do not expose this setup to external users.

Example in a separate terminal (synthetic preferences only):

```powershell
$principalHeaders = @{ 'X-Synthetic-Principal' = 'synthetic-a' }
# Read only; 404 if no profile has been explicitly saved.
Invoke-RestMethod http://127.0.0.1:8000/api/v1/profile -Headers $principalHeaders
# Deliberate Save: expected_revision=0 creates only if this owner has no profile.
$syntheticSave = @{
  expected_revision = 0
  preferences = @{
    adult = $true; goal = 'general_strength'; equipment = 'bodyweight'
    experience = 'beginner'; days_per_week = 2; session_minutes = 20
  }
} | ConvertTo-Json -Depth 4
Invoke-RestMethod http://127.0.0.1:8000/api/v1/profile -Method Put `
  -Headers $principalHeaders -ContentType application/json -Body $syntheticSave
```

Only the server identity selects the owner. Owner fields/query parameters are
rejected. Updates require the currently observed revision; one successful Save
increments it, including an explicit Save of identical preferences. Concurrent
stale requests get 409 `stale_profile`; unknown exclusions are 422. All failures
are sanitized. Request bodies, including chunked bodies, are capped at 16 KiB
before JSON parsing, with a five-second total intake bound. Generation's same
30-second deadline starts before body intake; that time is not added afterward.
Database errors/timeouts return 503; there is no automatic
in-memory profile fallback. After an uncertain/lost Save response, GET the current
revision rather than assuming rollback or automatically choosing a newer revision.

Native DB operations use independent short-lived connections, four concurrent
slots, a ten-second overall operation timeout and fixed local DSN/query limits.
Profile Save never acquires a candidate guard. Approval acquires its lineage
guard, transaction-scoped advisory identity lock, then owned profile-row lock;
Save and Approve serialize on that row without reversing the guard order.

## Candidate lifecycle (internal store, used by POST streams)

`app.state.candidates` is one process-local `CandidateStore`. Initial publication
requires a saved owner profile/revision and an independently valid plan. Immutable
canonical JSON bytes are SHA-256 hashed; returned models are fresh copies.
`publish_initial` and `publish_revision` are called by F1-05 only at successful
stream terminalization. Their optional `before_publish` callback checks the same
request deadline after all awaited work and immediately before mutation. Initial
expiry sweeping precedes the final profile read so Save cannot interleave with
insertion through a later sweep await. IDs are validated before any mutation.

Use the `revision(principal, identity)` async context manager to reserve and
automatically release a pending token after failure/cancellation. Generation stays
outside the lineage guard. Successful publication alone consumes the one-revision
allowance and supersedes the old ID; each ID retains its own expiry. A stale
profile rejects reservation/publication and requires fresh generation/review.

TTL is 1800 monotonic seconds; equality is expired. Expiry is checked on access
and swept on initial publication or explicit `expire()`, without a background
timer. This guarantees eligibility, not immediate wall-clock secure erasure or a
process-RSS ceiling. At most 200 active lineages, 64 KiB per canonical payload,
16 MiB aggregate canonical payload and two IDs per lineage are retained. The
body-free expired-ID cache is capped at 400; older forgotten IDs return 404 rather
than 410. Memory outside the store and Python allocator overhead are not counted
as payload bytes. Rejected capacity never evicts an active guarded operation.

`lineage_guard` deliberately yields before status/expiry validation so the
approval coordinator can recheck committed idempotency **after waiting**. Its
guarded readiness check can use acquisition time for approval TTL acceptance.
`block_for_reconciliation` blocks publication and eviction until authoritative
resolution. F1-06 stores a bounded identity/key intent and reconciles under the
same guard. Losing a process loses candidates/reservations/gates; saved profiles,
approved snapshots and key bindings remain in PostgreSQL.

`OwnedPlanReader`/`ApprovedPlanSource` define owner-filtered, bounded readback and
history, with ownership rechecked on returned immutable rows. `PostgresApprovals`
implements the source using owned SQL predicates. Readback verifies canonical
bytes/hash and uses stored versions, without rewriting or revalidating historical
plans against the current profile/catalog.

## Atomic approval and durable readback

`POST /api/v1/drafts/{candidate_id}/approve` accepts only the strict
`ApprovalRequest`: candidate ID, revision, canonical hash and a 1–128 character
idempotency key. It never accepts a client plan or owner. The server checks the
committed owner/operation/key binding before requiring a candidate, then again
after acquiring the lineage guard, including after waiting. Matching retries
return the original approval even after expiry or process restart; different
fingerprints get 409. A new key cannot approve the same candidate twice.

First-time eligibility uses the instant the guard is acquired (TTL equality is
expired). The bounded transaction may finish after that boundary. It locks the
owned profile row, checks captured revisions and independently validates the
server snapshot before inserting snapshot/key/audit in one transaction. Successful
revision publication and expiry use the same lineage guard. A pending revision
does not invalidate the current candidate; whichever successful operation takes
the guard first determines the outcome.

An owned, shielded task holds the guard through COMMIT and memory finalization,
even if the HTTP caller is repeatedly cancelled. Any uncertain COMMIT quarantines
the lineage. Reconciliation first obtains the same transaction-scoped advisory
identity lock using `pg_try_advisory_xact_lock`; failure stays 503
`reconciliation_pending`. Only after that lock and a fresh READ COMMITTED query
can absence establish rollback. A lone missing row is insufficient while the
original transaction might commit. Recovery is attempted on subsequent guarded
operations; there is no background queue or durable draft recovery service.

Lookup/read operations are bounded at ten seconds, guard waiting at five,
transaction work at ten plus up to three seconds for close, and reconciliation
at five. Native connection statement/lock/idle-transaction limits remain enabled.
These are per-operation bounds, not a new generation budget. Generation retains
the ratified 30-second request-wide deadline.

`GET /api/v1/plans/{plan_id}` returns the owned immutable saved plan.
`GET /api/v1/plans?limit=5&cursor=<last-plan-id>` returns an owner-filtered bounded
page (server maximum 20). Pagination is ascending opaque plan ID, not approval
time; inserts before the cursor require Refresh to appear. A wrong owner gets
404 for an individual plan and cannot read another owner's page.

## Typed fake orchestration (internal API)

`future_training.agent.orchestration.Agent(profiles, catalog, candidates=store)`
composes the existing `ProfileAccess`, `Catalog` and optional `CandidateStore`.
The default provider is `FakeModel`; `ScriptedFake` supplies deterministic fault
fixtures. No provider SDK, credential lookup, live-mode switch or exporter exists.
Use the supported single-process, single-event-loop design. Admission is shared
between Agent instances: one active session per synthetic principal, two total.

```python
from future_training.agent.orchestration import Agent
from future_training.identity import Principal
from future_training.schemas import GenerateRequest

# profiles/catalog/store are the existing application dependencies, not new services.
agent = Agent(profiles, catalog, candidates=store)
result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
output = result.output()  # plan preview, clarify, abstain, or sanitized error
```

`generate()` is an offline/library convenience. It never publishes or saves.
`session()` is the integration interface used by the SSE adapter:

```python
async with agent.session(principal, request, revise=identity, progress=on_state) as run:
    result = await run.execute()  # exactly once, on the session's owning task
    preview = result.output()    # fresh copy; no candidate identity
    # F1-05 transport work stays inside this context.
    # run.reservation is live only here; run.deadline.check() checks the same deadline.
```

For initial generation omit `revise`. The context keeps admission, the original
30-second deadline and any revision reservation alive after execution. Exit,
failure or cancellation releases resources without publication or consuming the
successful-revision allowance. External cancellation propagates; generation
failures become typed results. Entry/transport failures of `session()` remain
exceptions for the adapter to translate. Progress callbacks receive only `State`
enums and execute under the same deadline. They must not log raw request data.

F1-05 emits only validated previews, handles incomplete EOF/cancellation, and
publishes using the existing store only at successful terminalization immediately
before `done(plan)`. It rechecks the deadline and publish-time freshness;
`ready_unpublished` and `RunResult` do not establish approval eligibility. The SSE
implementation is in `streaming.py`; approval SQL/reconciliation are separate
F1-06 components and never run as a side effect of generation.

Only `search_exercises` and `get_user_preferences` are exposed. Arguments cannot
select an owner or loosen the captured profile. Unknown tools/arguments return
fixed error codes and consume the read budget. Results are schema/identity/content
checked before reaching the provider. There is no approved-history tool until a
real source exists. All unstructured preference text requires clarification in
this fake-only implementation; provider prose is not forwarded as instructions.

The fake counts simulated tokens as `ceil(UTF-8 bytes / 4)`, including schemas and
accumulated tool context. Each call reserves its entire known input and up to
2,000 output tokens (or remaining allowance) before invocation. Unknown usage
retains reservations; known usage settles them. Underreports retain conservative
reservations; reported overages are preserved and fail closed. The cumulative
caps remain 16,000 input / 4,000 output, three provider attempts, four tool
dispatches, one selected retry and one selected repair. Continuations and failed
attempts count; retry/repair selection cannot authorize a fourth request. These
are simulated accounting tests, not measurements of a real tokenizer or charges.

## React workspace and direct POST SSE

After building the web bundle and starting the approved local launcher, open
`http://127.0.0.1:8000/`. The API serves the compiled assets itself; there is no
separate frontend server or CORS proxy. UI/asset access also requires local opt-in,
a loopback peer/listener and a valid Host/Origin. Choose Local profile A or B; API
requests use the existing synthetic principal header. No browser storage, cookies,
provider credentials, external fonts or external assets are used.

1. Choose supported synthetic adult preferences/exclusions and explicitly Save.
2. Generate a preview and review estimated duration and each exercise prescription.
3. Optionally request one revision using the same saved preferences. The fake
   baseline may return identical content with a new revision identity. Free text
   produces clarification; supported constraint changes require Save and a fresh
   generation. A failed/stopped revision retains its previous retry target, subject
   to server freshness, TTL and lineage checks, while clearing the incomplete view.
4. Stop aborts fetch, clears the incomplete preview and never reconnects or replays.
   Changing identity aborts outstanding work and discards old UI state. Stale Save
   requires explicit Reload; the UI does not automatically overwrite newer data.

5. A complete validated terminal enables Approve. The click rechecks the displayed
   plan hash and sends only its reviewed identity plus one new idempotency key.
   Successful approval is shown only after durable GET readback matches the
   preview and captured profile revision.
6. After a lost response or interrupted readback, explicitly Retry approval uses
   the exact same request/key. There is no automatic replay. Profile changes and
   generation stay disabled while the result is unresolved. Approval is not
   cancelled by Stop; its transaction may finish after connection loss.
7. Refresh/load more/open saved history reads actual PostgreSQL records. Later
   profile edits do not rewrite a saved plan. Identity switching aborts local work
   and clears old state. Keys live only in page memory; after a reload use history
   to recover durable results rather than inventing a new approval.

`POST /api/v1/drafts/stream` accepts `GenerateRequest`.
`POST /api/v1/drafts/{candidate_id}/revise/stream` accepts `ReviseRequest`; path
and body identity must match. Extra query/owner parameters and Last-Event-ID are
rejected. `GET /api/v1/exercises` supplies a bounded, protected catalog list with
supported filters and cursor/limit, without a database write.

Each SSE frame contains `event: <type>` and JSON `data: <StreamEvent>`, separated
by a blank line. Schema version is `1`; request ID is stable and sequences are
contiguous from zero. Limits are 16 KiB per frame, 64 events, and a 1 MiB browser
aggregate cap (including comments). The browser accepts LF/CRLF/CR, multi-line
data and split UTF-8, but rejects malformed schemas, order, identity disclosure
in draft, extra events after done and unframed/incomplete EOF. A complete plan
also requires the displayed draft's canonical SHA-256 to match done's hash and
the expected initial/revision number. Draft parsing alone never establishes a
complete result. At expiry, only immediately writable error/done frames are
attempted; backpressure receives no extra deadline allowance.

OpenAPI, TS and standalone browser validators share one generation workflow:

```powershell
.venv/Scripts/python.exe scripts/export_contracts.py
npm --prefix web run generate
.venv/Scripts/python.exe scripts/export_contracts.py --check
npm --prefix web run check:generated
```

Ajv runs at generation time. Its standalone output is checked in and bundled, so
the browser uses no runtime schema compilation or `unsafe-eval`. TypeScript strict
and unused-code checks plus Prettier cover handwritten frontend sources; Ruff
covers Python. The production bundle is ignored under `web/dist/`.

The routine frontend tests block sockets, DNS and fetch outside injected fakes.
The optional installed-Chromium smoke uses a fresh workspace browser profile and
an isolated PostgreSQL schema; it blocks nonlocal page requests and writes the
synthetic screenshots under `docs/implementation/evidence/`. It downloads no browser.
With PostgreSQL running and the bundle built:

```powershell
$env:FATA_BROWSER_EXECUTABLE = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe -m pytest tests/test_browser_ui.py -q -s -m integration --basetemp=.cache/pytest-f106-browser
```

Leave the variable unset to skip that optional test. Its startup/UI condition
polling is smoke evidence; concurrency/ordering assertions use separate ASGI
barriers, events and fake clocks. The F1-07 browser journey injects loss after an
actual successful approval response, explicitly retries the same key, verifies
durable readback after a later profile Save, and switches principals. See the
F1-07 handoff for exact results and the distinct fault-injection limits. It also
checks mobile Save failure/recovery and desktop/mobile horizontal overflow.

## Shared checks and local diagnostics

F2-02 profiling and the bounded catalog-projection prototype are isolated under
`future_training.experiments`. The [measured decision](implementation/f2-02-cache-decision.md)
keeps the application uncached. The [handoff](implementation/f2-02-handoff.md) links
raw component/native-API measurements, exact keys/bounds and correctness evidence.

`scripts/check.py` runs the same offline commands as `.github/workflows/offline.yml`.
Use `--integration --browser` with local PostgreSQL/migrations and an installed
Chrome path to require every integration case; missing required browser evidence
or any skip fails the run. `--evidence` explicitly refreshes synthetic F1-07 trace
artifacts. See [the runbook](runbook.md) for exact commands and trace diagnosis.
The supported launcher emits only allowlisted JSON metadata to stderr. No raw
access logs, exception text, HTTP body/header/query data, user/plan/candidate IDs,
content hashes or idempotency keys enter its tracing sinks. There is no exporter.

F3-01 is owner-accepted. F3-02 adds an explicitly labeled Responses **replay**
adapter and native PostgreSQL replay spending ledger. Default application
configuration remains fake-only; no live transport is enabled. See the
[F3-02 handoff](implementation/f3-02-handoff.md) and
[provider safety contract](../contracts/provider-safety.md). The shared check
runner verifies versioned prompt/tool/output/config/eligibility assets using
`scripts/prepare_responses.py --check`. Current native fixtures include migration
005; no default project, active permit or allowance is created. Real-input
admission remains unverified for live use and blocks live work regardless of credentials.

F3-03B adds migrations 006–007's empty mixed-operation tables/rate binding and the explicit
Python-only `ResponsesReplay(..., counted=True, ledger=CountedSpendingLedger(...),
scope=(project, grant, session), count_ceiling_micro=1000)` offline harness.
Use an exact HTTPX `MockTransport`, isolated replay project and a positive
synthetic quote; these are test setup, not an application configuration or permit.
Every generation independently counts its frozen payload, including tool
continuation, repair and the single retry when safe. Internal counters distinguish
generation/count/combined claims and their outgoing byte counts; inference metrics
retain 16,000/4,000 ceilings and reported replay provenance.
See [F3-03B handoff](implementation/f3-03b-handoff.md),
[provider safety](../contracts/provider-safety.md) and the
[pre-live checklist](planning/19-f3-03c-pre-live-readiness.md).

F3-03D adds migration 008's empty `spend_observations` metadata table, completed
native-item/terminal checks and one owned HTTP client per replay session. The
socket test connector always targets literal loopback; it cannot contact a
provider. TLS tests generate ephemeral synthetic certificates/keys under ignored
test directories using installed OpenSSL (PATH, or Git for Windows' bundled
`C:/Program Files/Git/usr/bin/openssl.exe`). CI explicitly verifies OpenSSL exists;
missing tools fail checks rather than silently skipping evidence. No SDK or new
Python package is needed. See [F3-03D handoff](implementation/f3-03d-handoff.md).

F3-04A adds offline evaluation checks to the shared runner:
`scripts/prepare_model_evaluation.py --check` and
`scripts/evaluate_models.py --check`. For a new timestamped synthetic run and
blank practice review packets, use `scripts/evaluate_models.py` without flags.
Detailed output stays in ignored `.cache/f3-04a/<UTC-run>/`; hand only its
`reviewer/` directory to an internal reviewer, withholding `private/` and the
source report until scores are frozen. There are no scores or actual-model
outputs now. The explicit `--record-offline` maintenance flag replaces only
the new synthetic score artifact; never use it to bless an unexplained failure.
See [protocol 20](planning/20-f3-model-evaluation-protocol.md) for split/exposure,
hard-failure and N/A clarity rules. The frozen F1 corpus and live NO-GO remain.

F3-04B's counted replay accepts either exact MockTransport or explicit LocalTLS
with the existing replay ledger/scope. `ClaimedHTTP` now owns the acknowledged
claim→send boundary for both. `OpenAIHTTPS` is dormant and cannot be passed to
replay or application configuration; credentials/environment cannot activate it.
Its live and financial barriers are unconditional. F3-04B introduced no live
authority schema or grant. Its additive `offline-scores-f3-04b.json` and original F3-04A evidence stay
unchanged and all 150 case/summary results must match. See
[handoff](implementation/f3-04b-handoff.md) and
[remaining authorization gates](planning/19-f3-03c-pre-live-readiness.md).

F3-04C adds migration 009's empty `probe_*` tables, separate from replay records.
Run the existing `scripts/migrate.py` before current PostgreSQL checks. No default
project, grant, session or active authority is inserted. `AuthorityLedger.prepare`
stores a zero-limit proposal; `simulate` is nonmonetary fixture setup. Live
activation always fails both source-review gates and is not an application mode.
No live CLI or environment activation exists. The fixed `SingleProbe` harness
returns unpublished results and uses the same Agent/counting/tools/validator.
Tests supply only local MockTransport/LocalTLS and isolated synthetic accounting.
Private recovery uses `AuthorityLedger.load` and explicit `reconcile_mixed`;
neither creates tickets, refunds unknown costs nor releases a revoked authority.
Never edit applied migrations or reset accounting to retry an uncertain request.

Current evaluation provenance is additive `offline-scores-f3-04c.json`; every
case/summary must still equal earlier snapshots. No corpus/scorer feature changed.
For final offline checks, set the installed browser path and
`FATA_BROWSER_EVIDENCE_STAGE=f3-04c`, then run
`scripts/check.py --integration --browser`. See the
[F3-04C handoff](implementation/f3-04c-handoff.md) and
[operator procedure](planning/19-f3-03c-pre-live-readiness.md). These commands do
not require provider credentials or authorize traffic, permits or spending.

F3-05A adds local metadata projection with no SDK import in application execution.
Its optional SDK environment is separately locked under `experiments/langfuse`:

```powershell
uv sync --frozen --directory experiments/langfuse --python "$PWD/.venv/Scripts/python.exe"
.venv/Scripts/python.exe scripts/prepare_langfuse.py
# From experiments/langfuse:
$env:PYTHONPATH='../../src'
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe run.py
```

The SDK process permanently seals sockets/DNS and SDK environment defaults, uses
fixed in-process mocks and closes owned SDK consumers. Do not import that harness
into the application or run it inside a shared Python process. It accepts no live
destination/credential options. Detailed metadata evidence stays in ignored
`.cache/f3-05a/`. Its score API is mocked; no Langfuse project/dataset is created.
The [specification](planning/21-f3-langfuse-offline-integration.md) records limits,
private pinned-SDK cleanup hooks, truthful experiment evidence and separate hosted
privacy/retention/network/spending gates. Full regression evidence is in the
[handoff](implementation/f3-05a-handoff.md).
