# F2-04 handoff — Completion, feedback and final F2 evidence

Date: 2026-10-24. Status: implemented and verified for owner review. F2-01 through
F2-03 are owner-accepted; this report does not approve F2 or authorize F3.

## Outcome and design decisions

The local workspace now supports **explicit Submit of a session record with
optional structured feedback against an actual owned approved plan**. Generation,
approval, viewing and selecting form values never record completion. PostgreSQL
atomically stores one immutable record and its idempotency binding. Matching
retries survive response loss and interpreter restart; conflicting submissions
cannot overwrite or duplicate a session. Approved-plan snapshots remain unchanged.

The [contract](../../contracts/completion-feedback.md) and strict schemas were
written/tested before persistence; the first 23 contract cases passed before the
migration/service were added. The design deliberately combines completion and
optional feedback into one atomic record rather than introducing separate edit
histories, dates/calendars or a second transaction.

- Status: `completed | partial | skipped`. Optional effort: `easy | moderate | hard`;
  optional session rating: integer 1–5. Skipped requires null feedback. There are
  no health notes, skip reasons, biometrics, clinical data or client timestamps.
- Identity: owned approved plan + actual day index from its immutable snapshot,
  with the reviewed candidate revision/hash. Today's profile/catalog is not an
  authority for rewriting historical records.
- Revision: create with integer `expected_revision=0`; the resulting record has
  immutable revision 1. No editing/correction/deletion or repeated occurrence for
  the same numbered session is implemented. This policy is explicit in the UI.
- Duplicates: only the first accepted owner/operation/key binds to a session.
  Same-key normalized matching retry returns the original full record. A different
  fingerprint returns 409 `idempotency_mismatch`; a new key for an existing session
  returns 409 `session_already_recorded`, even with identical values.
- Authority: server-derived owner, actual approved snapshot and SQL constraints.
  No model tool can read or write these records. No graph, cache or provider change.

## Files changed

| Paths | Purpose |
| --- | --- |
| `contracts/completion-feedback.md` | Bounded domain, Submit/readback, revision, duplicate, privacy, retention and transaction contract |
| `src/future_training/completion_contracts.py` | Additive strict submission/record/error schemas, including generated cross-field skipped-feedback checks |
| `migrations/004_session_records.sql` | Records/key tables, owned references, actual-session checks, unique constraints, deferred binding and append-only guards |
| `src/future_training/persistence/completions.py` | Native SQL Submit/readback, transaction ordering, conservative COMMIT failures and cancellation-safe owned writes |
| `src/future_training/api.py` | Three protected HTTP operations and typed completion error responses; injectable test repository |
| `src/future_training/identity.py` | Completion-only 4096-byte intake, duplicate/nonfinite JSON rejection and private no-store response headers |
| `src/future_training/observability.py` | Fixed metadata-only completion stages/routes/reasons; no content attributes |
| `src/future_training/readiness.py` | Require the new migration/columns for local dependency readiness |
| `scripts/export_contracts.py`, `contracts/openapi.json` | Additive implemented contracts; prior 31 components and nine paths remain structurally unchanged |
| `web/scripts/validators.mjs`, `web/src/api.generated.ts`, `web/src/validators.generated.{js,d.ts}` | Generated types and strict runtime validators; no handwritten generated edits |
| `web/src/api.ts`, `web/src/CompletionPanel.tsx`, `web/src/App.tsx`, `web/src/styles.css` | Bounded owned client calls, explicit forms, exact retry/readback, owner-switch cleanup and narrow responsive integration |
| `web/package.json` | Include the new component in existing formatting checks; dependencies/lock unchanged |
| `tests/test_completion_contracts.py`, `test_completion_http.py`, `test_completions_postgres.py` | 33 new routine and 31 new actual PostgreSQL/HTTP cases |
| `tests/test_browser_ui.py`, `web/scripts/browser-smoke.mjs` | Extend actual browser journey, inject lost successful session response and verify two durable records |
| `web/tests/completions.test.tsx`, `web/tests/ui.test.tsx` | 16 new client/React cases; existing UI fake rejects implicit writes |
| `tests/test_migrations.py`, `test_profile_postgres.py` | Extend exact expected table inventories for migration 004; preserve restart assertions |
| `README.md`, `docs/development.md`, `docs/runbook.md` | Current status, explicit workflow, migration/recovery/retention commands |
| `docs/implementation/evidence/f2-04-session-trace.json`, `f2-04-{desktop,mobile,mobile-error}.png` | New native fault trace and actual browser screenshots |
| This handoff and [F2 acceptance report](f2-acceptance-report.md) | Results, limitations, consolidated evidence and readiness |

Frozen `schemas.py`, domain/evaluation sources, corpus/catalog/results, root
Python/JS locks, existing migrations, approved planning and historical evidence
are unchanged. Additive models avoid invalidating frozen F1 source provenance.
No dependency was installed or updated during F2-04.

## Migration and HTTP contract

Migration 004 adds `session_records` and `session_idempotency` without altering
existing tables. Records have owned approved-plan foreign keys, day 1–4 bounds,
actual snapshot membership and revision/hash checks, nullable bounded feedback,
one record per owner/plan/day and a database-generated submission timestamp.
Keys have an independent `submit_session` namespace, unique owner/key and unique
owner/record. A deferred constraint prevents a record from committing without its
binding. UPDATE, DELETE and TRUNCATE are rejected for records and keys. Privileged
DDL/dev-volume reset remains outside this application authority.

Observed initial local migration command:

```powershell
.venv/Scripts/python.exe scripts/migrate.py
```

Result: `{'applied': ['004_session_records.sql']}`. Final repeat returned
`{'applied': []}` with all four migration checksums accepted. The existing
readiness checker now verifies the new tables/columns; process liveness remains
independent of dependency readiness. Health's historical foundation stage marker
is preserved, not repurposed as an F2 acceptance claim.

| Method/path | Behavior |
| --- | --- |
| POST `/api/v1/plans/{plan_id}/sessions/{day_index}/completion` | Explicit first Submit or matching retry; 200 returns full durable record |
| GET same path | Owned record; 404 if unsubmitted |
| GET `/api/v1/plans/{plan_id}/completions` | Owned plan's at most four records, strictly sorted by session |

Wrong-owner and absent plans both return 404. Invalid session membership is 422;
wrong reviewed snapshot revision/hash is 409 `plan_mismatch`. Query parameters,
extra owner/plan/notes fields, unsupported categories, bool/noninteger ratings or
revisions, skipped feedback and ambiguous JSON are rejected. Byte-counted chunked
intake accepts the tested 4096-byte boundary and rejects 4097 bytes with 413.
New completion success/error responses carry no-store/referrer/nosniff headers.
Browser requests also omit credentials, disable redirects and use no-store.

Existing API/identity/approval contracts remain intact. The additive OpenAPI
workflow was regenerated and checked; a structural comparison against HEAD found
all prior 31 component schemas and nine paths unchanged.

## Transaction, cancellation and recovery

The SQL order is owner/key advisory transaction lock → committed-binding lookup
→ owned immutable plan `FOR KEY SHARE` → owner/plan/session transaction lock →
session duplicate check → record + key inserts → COMMIT. READ COMMITTED takes a
fresh lookup snapshot after waiting. SQL predicates/foreign keys establish
ownership; hashes of lock identities merely coordinate ordering. No profile row
lock, candidate guard or reverse lock path is introduced.

Matching key retries are resolved before requiring a fresh profile/catalog or
transient candidate. Different keys for the same session serialize at its SQL
guard and cannot create key aliases. Independent sessions can progress together:
a deterministic two-connection barrier reaches both key inserts before release.
Unique constraints remain a database backstop.

Explicit writes reuse the existing `finish_owned` helper: shield **and await**
bounded critical work despite repeated caller cancellation, then propagate that
cancellation. A Submit may commit after disconnect/navigation. Transaction/slot
waiting is bounded to ten seconds plus up to three seconds of connection cleanup;
the existing native connection has statement/lock limits. No owned task is detached.
Generation's separate 30-second/token/tool/admission policy remains unchanged.

Primary references for these mechanisms: PostgreSQL 18
[transaction locks](https://www.postgresql.org/docs/18/explicit-locking.html),
[READ COMMITTED snapshots](https://www.postgresql.org/docs/18/transaction-iso.html),
and [deferred constraint triggers](https://www.postgresql.org/docs/18/sql-createtrigger.html).
The native tests below verify their use in this schema.

A COMMIT failure is conservatively retryable `reconciliation_pending`, including
a deferred constraint failure whose final absence is later established. There is
no transient memory authority to finalize or quarantine. Same-key retry acquires
the original authoritative SQL key lock, waits for the original transaction to
settle, then returns its committed record or inserts once after rollback. It never
assumes that an error or socket close proves rollback. No automatic request retry,
recovery daemon or background transaction manager was added.

## Native concurrency/fault evidence

The **31 new integration cases execute actual PostgreSQL and the real repository**.
`Controls` wraps real connections to inject exact failures/barriers; it does not
emulate SQL. Lock waits are observed using `pg_blocking_pids`. Cancellation uses
events and cooperative scheduling yields, not elapsed-time race assertions.

| Scenario | Observed/asserted result |
| --- | --- |
| Matching same-key race, direct and HTTP | Both receive identical record; `(records,keys)=(1,1)` |
| Same key, altered feedback or another session | First succeeds, contender gets `idempotency_mismatch`; `(1,1)` |
| Different keys, same session, same/different values | First succeeds, contender gets `session_already_recorded`; `(1,1)` |
| Different keys, independent sessions | Both reach barrier concurrently and succeed; `(2,2)` |
| Owner isolation, same key under two owners | Other owner's plan is 404; independently owned plans accept separate records |
| Invalid session, stale snapshot revision/hash | No record/key insert; invalid request or `plan_mismatch` |
| Fault between record and key insertion | Rollback leaves `(0,0)`; explicit normal retry reaches `(1,1)` |
| Actual deferred COMMIT-trigger failure | Both rows absent; conservatively pending response; retry after removing injected fault succeeds |
| Lost successful COMMIT acknowledgement | Initial 503 pending, actual `(1,1)`; same-key retry returns original |
| Uncertain original transaction still open | Retry demonstrably blocks on its SQL lock; after original commit returns its record, after rollback inserts a new record; final `(1,1)` |
| Repeated cancellation before/after COMMIT | Caller stays pending until critical work/cleanup settle, then cancellation propagates; retry reads the one committed record |
| HTTP cancellation | HTTP task cancellation cannot detach the explicit transaction; following same-key POST recovers `(1,1)` |
| Fresh interpreter after lost acknowledgement | New process submits/reads the same key/result using PostgreSQL alone; no memory dependency |
| Direct SQL mutation or unbound/nonexistent session | Database rejects UPDATE/DELETE/TRUNCATE, missing binding at COMMIT and nonexistent day; original rows remain |
| Later profile change | Approved snapshot and original session record remain identical; no current-catalog dependency in completion reads |

These are tested single-process application semantics using concurrent SQL
connections and a fresh-interpreter retry. They do not establish whole-app
multi-worker support, physical power-loss behavior or every network failure.

### Diagnosed lost-COMMIT trace

[Eight metadata-only spans](evidence/f2-04-session-trace.json) cover three actual
ASGI HTTP requests and native SQL. The fault deliberately raises after native
COMMIT succeeds. Initial response is 503 `reconciliation_pending`; explicit retry
and GET are both 200 and return the same record. Counts remain one record/one key.
Root cause is lost acknowledgement, not a rollback or duplicate. The correction
is the designed same-key authoritative lookup; no application defect or new
recovery infrastructure was required.

| Observed operation | HTTP ms | Nested transaction/read ms |
| --- | ---: | ---: |
| Submit with lost acknowledgement | 34.500 | 31.072 |
| Explicit same-key retry | 18.204 | 15.079 |
| Durable GET | 20.357 | 18.043 |

Each row is one local observation, not a percentile, SLO or production latency
claim. Nested durations overlap and must not be summed. Trace attributes contain
only fixed route/stage/outcome/reason/status metadata with opaque correlation IDs;
no record/plan/session/owner identity, key, fingerprint, status choice, rating,
effort, SQL or content. Canary tests separately inspect both configured local
trace and console sinks. No hosted export or provider call occurs.

## React/browser evidence

The panel mounts only for independently checked durable approved readback. Status
starts unselected; feedback is optional. It keeps the exact pending request/key
while uncertain and requires explicit retry. Confirmed POST is followed by GET
and exact matching readback before displaying success. Definite conflicts require
owned reload; plan-identity conflict requires reopening the plan. Principal change
or unmount aborts client work and rejects late results. Page-local keys are not
stored in browser storage.

Six new React cases and ten new client validation cases passed. They cover no
implicit Submit, unchanged retry body/key, readback failure, optional/cleared
skipped feedback, failed initial read, conflict reload, owner-switch cancellation,
malformed/oversized collections, invalid ratings, mismatched snapshot/receipt,
and absence of automatic POST replay.

The installed Chrome journey exercised Save → Generate → Review → Revise →
Approve → lost approval response/retry → durable readback → explicit completed
session with moderate effort/rating 4 → lost successful session response → exact
retry → profile change → immutable saved plan/session readback → mobile skipped
session → owner switch → failed Save/recovery. Native fixture counts were exactly
`(approved,approval-key,audit,session,session-key)=(1,1,1,2,2)`.

Observed: zero page runtime errors/external requests/horizontal overflow. Both
approval and session retry succeeded with the original keys. Desktop/mobile
screenshots were visually inspected; the mobile error screenshot captures the
existing owned-profile Save failure state:
[desktop](evidence/f2-04-desktop.png), [mobile](evidence/f2-04-mobile.png),
[mobile error](evidence/f2-04-mobile-error.png).

## Exact commands and final results

From repository root, using installed tools and the existing cached image:

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
.venv/Scripts/ruff.exe format src scripts tests --no-cache
.venv/Scripts/ruff.exe check src scripts tests --no-cache
.venv/Scripts/python.exe scripts/export_contracts.py
npm --prefix web run generate
npm --prefix web run format
Remove-Item Env:FATA_F2_EVIDENCE -ErrorAction SilentlyContinue
$env:FATA_F204_EVIDENCE='1'
$env:FATA_BROWSER_EVIDENCE_STAGE='f2-04'
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser
experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q --junitxml=.cache/f204-graph.xml
```

Final shared runner and separate graph suite exited zero. The runner executed:

| Command/check | Final observed result |
| --- | --- |
| Python/Node/npm/Ruff versions; `npm --prefix web ls --depth=0` | Installed supported versions resolved |
| `ruff check src scripts tests --no-cache` | Passed |
| `ruff format --check src scripts tests --no-cache` | Passed, 82 files |
| `python scripts/export_contracts.py --check` | Passed; no drift |
| `npm --prefix web run check` | TypeScript passed |
| `npm --prefix web run format:check` | Prettier passed |
| `npm --prefix web run check:generated` | Generated TS/runtime validators passed |
| `npm --prefix web run test` | **85 passed**, no skips/cancellations; 5.014 s reported duration |
| `npm --prefix web run build` | Passed, approximately 372.3 KiB JS/5.9 KiB CSS before compression |
| `python -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **604 passed**, 105 integration tests deselected, 15.95 s |
| `python scripts/smoke_local.py` | Health/readiness 200, rejected canary 422, correlated/safe console true; own API child stopped |
| `python -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **105 passed**, 604 routine tests deselected, 39.10 s; includes native SQL and required Chrome |
| `python scripts/evaluate_baseline.py --check` | Unchanged **24/24 development, 16/16 held-out** |
| `python scripts/measure_async_reads.py` | Both modes 5/5 correct; three requests/trial; no retries; peak inflight 1/3 |
| Separate graph command above | **47 passed in 15.98 s**, no skips |

The runner resolves Python/Ruff to `.venv/Scripts` and npm to installed `npm.cmd`.
Its summed child-command elapsed time was 81.537 s, separate from the graph run.
Ignored runner/JUnit evidence remains under `.cache/f107/` plus the explicit
graph XML. Totals are **709 root Python tests**, **47 isolated graph tests** and
**85 frontend tests** in separate populations; the 40 evaluation cases are not
pooled with these tests. Existing six specification/reference cases remain distinct
from native PostgreSQL proof. No test was removed or skipped to achieve this result.

Targeted checkpoints also passed: initial contract 23/23; native completion suite
31/31 in 13.86 s; installed-browser case 1/1 in 3.90 s. Final runs supersede earlier
formatting findings, a browser-driver lexical redeclaration and stale F1 table
inventory assertions. Those test-driver/inventory issues were corrected without
weakening restart/immutability assertions. An initial non-escalated pytest run
could not access its temporary directory; normal local process access resolved
that environment issue.

No `--evidence` flag or old `FATA_F2_EVIDENCE` was used in acceptance; historical
F1/F2 artifacts are preserved. The new `FATA_F204_EVIDENCE` explicitly writes only
the session trace. The existing shared check runner already discovers all new
application tests; no extra CI service/dependency or timing threshold was added.
Hosted CI was not dispatched.

## Preservation, cleanup and remaining limits

Frozen evaluation source/catalog/corpus/results and both lock hashes remain
unchanged. Root Python lock SHA-256:
`a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a`;
JS lock: `cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf`.
Prior planning, three migrations, application domain rules and F2 experimental
sources are unchanged. All F1 approval/profile/revision/SSE/budget/privacy/native
fault tests pass. LangGraph remains isolated; the application remains uncached.

Final SQL inspection found four applied migrations, zero leftover fixture schemas
and development approved/key/audit/session/session-key counts `(0,0,0,0,0)`.
Migration repeat was a no-op. PostgreSQL was stopped with image/volume preserved;
the API smoke and browser shut down their owned processes. No development reset,
commit or push was performed. `AGENTS.md` remains local and ignored.

Environment: Windows 11 build 10.0.26200, AMD64 Family 25 Model 116 Stepping 1,
16 logical CPUs; Python 3.14.9; pytest 9.1.1; Ruff 0.17.2; FastAPI 0.162.0;
Pydantic 2.14.1; Psycopg 3.3.6; Uvicorn 0.54.0; Node 24.22.1; npm 11.19.1;
PostgreSQL 18.6; installed Chrome 155.0.8059.85. No dependency/image acquisition,
live provider, hosted telemetry, cloud provisioning or external-user data.

Records and key bindings share the local synthetic PostgreSQL-volume retention
of their approved plans. No automatic expiry, correction/deletion API, calendar,
production backup/deletion policy or real authentication was added. Ratings are
synthetic self-reports and do not establish physical completion, plan quality or
clinical suitability. Controlled driver faults and interpreter restarts do not
simulate every packet/power/disk failure. No production scale, multi-worker,
real-model quality/cost, hosted observability or AWS operation is claimed.

No known F2-04 blocker remains. [Final F2 acceptance evidence](f2-acceptance-report.md)
consolidates the four units and identifies separately gated F3 planning needs.
Stop for owner review; do not begin F3 without separate authorization.
