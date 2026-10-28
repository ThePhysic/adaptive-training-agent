# F1-07 — Integration, local observability, CI and final offline evidence

Date: 2026-10-24. F1-01–F1-06 are owner-accepted. F1-07 is implemented and awaits
review. F2 has not begun. No commit, push, deployment, live provider call, hosted
telemetry export, dependency installation or cloud operation was performed.

## Delivered

- Correlated, allowlisted local spans across HTTP, orchestration, provider attempts,
  tools, independent validation, candidate publication, profiles, approval lookup/
  transaction/reconciliation and durable readback. Owned COMMIT tasks inherit the
  request trace without changing cancellation/guard behavior.
- A bounded process-local trace ring and one safe console logging configuration
  for the supported launcher. No exporter, collector or new service.
- Liveness separate from bounded, read-only local dependency readiness. Readiness
  verifies opt-in/fake configuration, catalog, web assets and schema/checksums.
- Bounded request-body intake with its elapsed time included in the original
  generation deadline; safe correlated pre-header errors.
- One fail-fast offline check runner used by local development and a pinned CI
  workflow, including a smoke of the actual supported launcher.
- Broader privacy/egress probes, native connection interruption/recovery, full HTTP
  journey traces, desktop/mobile browser consent/history/retry/error evidence.
- [Local runbook](../runbook.md) and [final F1 acceptance report](f1-acceptance-report.md).

## Changed paths

| Paths | Purpose |
| --- | --- |
| `src/future_training/observability.py` | Fixed stage/value/attribute allowlists, random correlation IDs, context propagation, bounded ring, spans, safe console formatter and HTTP correlation/error boundary |
| `src/future_training/readiness.py` | Read-only checksum/schema probe, asset checks and strict readiness response models |
| `src/future_training/api.py` | Trace middleware, readiness/liveness, explicit readiness/asset fixture injection and server-owned request start timestamp |
| `src/future_training/identity.py` | Five-second bounded body intake; record generation start before reading the body |
| `src/future_training/agent/budget.py`, `agent/orchestration.py` | Carry original HTTP start into the unchanged 30-second deadline; observe states, provider durations, attempts, conservative usage and versions |
| `src/future_training/agent/tools.py` | Allowlisted tool names and rejected-dispatch observation, without arguments/results |
| `src/future_training/candidates.py`, `approval.py`, `persistence/approvals.py`, `persistence/profiles.py` | Observe existing publication/validation/SQL operations; no new business rules, SQL writes or transaction ordering |
| `src/future_training/streaming.py` | Reuse server HTTP correlation ID in SSE; terminal send outcome observation and original deadline propagation |
| `scripts/serve.py` | Safe console configuration, raw access logging disabled and no Uvicorn logging override |
| `scripts/check.py`, `scripts/smoke_local.py` | Shared offline command runner/JUnit totals/durations; read-only actual-launcher smoke and owned child cleanup |
| `.github/workflows/offline.yml` | Pinned, read-only-permission CI, locked acquisition followed by offline checks and local DB cleanup |
| `tests/test_observability.py`, `tests/test_readiness.py` | 22 new routine cases: failure diagnosis, canaries/sinks, bounded ring, cancellation/context, egress, intake/deadline and dependency readiness |
| `tests/test_operations_postgres.py` | Six new native integration cases: schema faults/recovery, terminated connection, complete HTTP slice with correlated SQL evidence |
| `tests/conftest.py`, `pyproject.toml` | Deny alternate DNS/connect/UDP paths; workspace-local pytest temp default |
| `tests/test_browser_ui.py`, `web/scripts/browser-smoke.mjs` | Existing browser journey extended with mobile Save failure/recovery, overflow assertions and new evidence filenames |
| `tests/test_foundation.py` | Current health stage assertion; accepted business-boundary tests retained |
| `web/tests/offline.mjs`, `web/tests/network.test.ts` | Additional UDP/DNS guards and one explicit frontend egress test |
| `contracts/openapi.json`, `web/src/api.generated.ts` | Regenerated readiness contract; existing domain/SSE/approval shapes retained |
| `README.md`, `docs/development.md`, `docs/runbook.md`, this handoff, acceptance report | Current status, complete operations/recovery instructions and evidence limits |
| `docs/implementation/evidence/f1-07-{desktop,mobile,mobile-error}.png`, `f1-07-{failure,vertical}-trace.json` | New synthetic screenshot and metadata-only trace evidence |

No migrations or dependency pins changed. No edits to ratified planning,
historical handoffs/screenshots, `schemas.py`, domain sources, evaluation source,
catalog, frozen corpus/manifest/report or dependency lockfiles. `AGENTS.md` remains
ignored and untouched. Existing approval reference-model tests remain labeled.

## Observability design and privacy

`X-Request-ID` is generated server-side, reused by SSE, and maps to `trace_id` on
every completed span in that request. `span_id`/`parent_id` establish nesting,
including the shielded approval task. Client trace headers are ignored. Separate
HTTP requests have independent traces; there is no durable user-linked workflow
ID or durable agent run. The native vertical-slice fixture records the known
request sequence, not a hidden persistent user correlation table.

The default ring retains 2048 spans (constructor hard cap 4096), returns copies,
and counts overwritten records. Each record's attributes are bounded by fixed
keys, exact static string values, bounded non-boolean numeric counters and two
booleans. No owner, candidate/plan ID, content hash, idempotency key, URL/query,
headers, prompt, workout body, credentials, exception message or SQL text is
recorded. Recognized version IDs and profile revision numbers are allowed. A
catalog/version upgrade needs a deliberate allowlist update rather than allowing
arbitrary provider-supplied strings into telemetry.

`scripts/serve.py` configures a single safe JSON console sink. Third-party runtime
records become level-only events; raw stack/exception/access-log text is omitted.
This sacrifices some debugging detail to preserve the boundary. There is no
automatic file logging, network exporter or file-export API. Explicit local
stderr redirection is documented. Library embedding with custom handlers is not
claimed safe merely because this launcher configuration is safe.

Canaries cover synthetic secrets, email and phone patterns in request text,
headers, query/path, invalid bodies, provider exceptions and explicit runtime
logging. Both configured sinks (ring snapshots and rendered console) are checked.
Credential/export environment canaries cannot change the fake-only configuration.
Logger/clock sink failures do not alter the business result. Trace durations are
local monotonic measurements, not provider charges or a distributed clock.

SSE business outcome is separate from HTTP status. A successful ASGI terminal send
marks `terminal_complete`; it does not prove browser receipt. Late disconnect
cleanup can mark `cancelled_cleanup` without replacing an already sent business
outcome. Actual cancellation before terminalization remains cancellation. The
existing orphan/lost-terminal contract and parser requirements are unchanged.

## Induced failure explanation

[Failure trace](evidence/f1-07-failure-trace.json): one actual ASGI POST using a
deterministic scripted fake, ten spans. The provider first requests the catalog
read tool, then supplies an invalid catalog ID, then supplies another invalid
proposal after the single allowed repair. Both validations reject the plan;
`semantic_repair_exhausted` ends the run as `done(error)` with no candidate.

Observed budget: **3 provider requests, 1 tool dispatch, 1 semantic repair,
0 transport retries, 7308 simulated input / 787 simulated output tokens,
0 uncertain attempts**. The final run state is `failed`. Catalog, validator,
prompt, tool, output and fake-model versions are present. HTTP status is 200
because SSE headers were already sent; the trace business outcome is `error`.
The final saved HTTP span took **22.180 ms** on this run. Invalid proposal bodies,
exercise IDs, tool data and prompts are absent from the artifact.

## Health, readiness and transport bounds

- `/health`: 200 process liveness, stage F1-07; no DB/provider probe.
- `/ready`: 200 `ready_local` only for opted-in local fake configuration, loaded
  catalog, built index/JS/CSS, matching migration checksums and accessible required
  columns. Otherwise fixed 503 `unavailable` with boolean checks. No raw driver
  details. Native DB probe uses a read-only transaction and bounded SQL/connect
  path (two seconds); outer dependency check is bounded to three seconds.
- Request intake: 16 KiB retained; total body-read wait now bounded to five seconds.
  Generation/revision's original 30 seconds start before intake and include its
  elapsed time. A fake-clock test advances four seconds in body receive, then
  confirms provider cleanup at original time +30, not +34. No attempt/token,
  publication, reservation or approval limit was enlarged.
- Unknown pre-header exceptions become a correlated sanitized 503. Started
  responses are never replaced with a second JSON response. Approval shielding,
  uncertain-COMMIT quarantine and SQL authority remain intact.

Readiness is a local dependency signal, not a production/security certificate,
proof of all stored rows, or an available-generation-slot indicator. A particular
lineage can correctly return reconciliation pending while global dependencies
are ready.

## Fault and integration observations

| Scenario / evidence | Observed result and scope |
| --- | --- |
| Native readiness with correct schema/history | 200 ready_local |
| Missing migration history, wrong checksum, missing profile table | 503; health stays 200. Repairing checksum in the isolated fixture restores 200 |
| Native connection killed with `pg_terminate_backend` while blocked on a test event | Profile read returns sanitized 503; a fresh connection reads the original saved revision; approval counts stay `(0,0,0)` |
| Real DB container stopped after checks | Actual DB-backed ASGI readiness probe returns 503 with database_schema=false; liveness remains 200, other local checks true; no raw connection error |
| Stalled dependency probe | Cancelled/drained at its outer bound; readiness unavailable |
| Stalled body | Controlled zero-budget test cancels receive, returns typed 503, never enters business handler |
| Hanging provider / request cancellation | Controlled provider event confirms cleanup; next generation for that principal succeeds |
| Two concurrent trace contexts | Barrier-controlled operations have separate trace IDs and correct parent IDs |
| Generation/tool/token/admission exhaustion | Accepted F1-04/F1-05 implementations and all existing tests pass with tracing enabled; no cap changed |
| Same/different-key approval races, profile row ordering, expiry, rollback, lost response, actual restart, uncertain COMMIT | All accepted F1-06 native fault/constraint cases pass unchanged, including guard retention and pending-reconciliation closure |
| Complete native HTTP journey | Save → generate → revise → approve → readback → history; wrong-owner read 404; later Save cannot change stored snapshot; 48 correlated spans across nine requests |
| Actual launcher smoke | Health 200, ready 200, rejected canary query 422; correlation found in safe JSON console; own child process stopped |
| Installed Chrome | Real SQL approval/readback/history, lost-successful-response same-key retry, immutable snapshot after profile change, owner switch, mobile Save failure/recovery; zero page runtime errors/external page requests |

Native SQL faults use real Psycopg/PostgreSQL. Existing test proxies inject loss
or retain actual open transactions; they are not fake SQL. Reference-model tests
remain separate. The browser's lost response and first B-profile Save failure are
explicit test injections; recovery writes use actual PostgreSQL. They are not
packet-cut experiments or a PostgreSQL server crash.

All three screenshots were visually inspected:
[desktop](evidence/f1-07-desktop.png), [mobile](evidence/f1-07-mobile.png),
[mobile error](evidence/f1-07-mobile-error.png). Desktop width 1440 and mobile
width 390 passed no-horizontal-overflow assertions. Approval stays disabled for
the failed Save, incomplete stream and stored-history view. Browser fixture counts
remain exactly one approved plan/key/audit, A profile revision 2, saved snapshot
20 minutes at revision 1, B history empty; B's explicit Save recovery reaches 1.

## Exact checks and denominators

Environment: Windows/PowerShell, Python **3.14.9**, Node **24.22.1**, npm **11.19.1**,
PostgreSQL **18.6** cached Compose digest, installed Chrome **155.0.8059.85**.
Python pins: FastAPI 0.162.0, Pydantic 2.14.1, Psycopg 3.3.6, Uvicorn 0.54.0,
pytest 9.1.1, pytest-asyncio 1.4.0, pytest-socket 0.8.1, Ruff 0.17.2.
JS pins remain React/DOM 19.3.1, TypeScript 5.9.3, Ajv 8.20.0, esbuild 0.28.2,
jsdom 30.1.3, openapi-typescript 7.13.0, Prettier 3.9.10.

Primary command (no acquisition performed):

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser --evidence
```

The final runner completed all commands with exit 0, approximately **67.711 s**
summed child-command elapsed time. `.cache/f107/check-results.json` stores exact
argument vectors, exit codes and timings; JUnit files store denominators. The
core commands it executed and their observed results:

| Command | Result |
| --- | --- |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | 65 files formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | No drift |
| `npm --prefix web run check` | Strict TypeScript passed |
| `npm --prefix web run format:check` | Passed |
| `npm --prefix web run check:generated` | TypeScript and standalone validators match |
| `npm --prefix web run test` | **69/69 passed**, zero skipped/cancelled/todo, 4.342 s test duration |
| `npm --prefix web run build` | Passed; approximately 343.7 KiB JS / 5.7 KiB CSS before transfer compression |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **504 passed, 73 deselected**, 12.49 s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | Health/readiness/correlation/canary/owned process cleanup all passed |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **73 passed, 504 deselected**, 29.69 s, including required installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | Development **24/24**, held-out **16/16**, no failed cases; frozen artifacts unchanged |
| `.venv/Scripts/python.exe scripts/migrate.py` | `{'applied': []}`; existing migrations unchanged |
| `git -c core.autocrlf=false diff --check` | Passed |
| `git check-ignore AGENTS.md` | Remains ignored |
| `docker compose stop postgres` | Container stopped after validation; image and volume retained |

Total **577 Python tests**, zero skipped in the full run: 504 routine +73
integration. Six routine cases are expressly reference-only approval models;
they are not additional PostgreSQL proofs. F1-07 adds 22 routine Python, six
native integration and one frontend case over F1-06's accepted denominators.
The frozen 40-case domain evaluation is reported separately, not added to these
test totals or represented as 40 browser/real-model trials.

Additional commands: `scripts/export_contracts.py` and `npm --prefix web run
generate` regenerated readiness contracts; Ruff/Prettier formatting ran; a targeted
44-case observability/SSE/readiness run passed. Existing `js-yaml` parsed the CI
workflow (one job, eight steps, contents-read permission), with no new dependency.
Official action refs were read using `git ls-remote`; no remote job was dispatched.
Aggregate SQL checks found zero leftover fixture schemas and development approval
counts `(0,0,0)`. Process inspection found zero remaining test Chrome processes;
the actual launcher smoke confirms its owned API child exited. After stopping
PostgreSQL, a separate Python ASGI probe using the real `DatabaseCheck` observed
health 200 and ready 503 with only `database_schema=false`. Its sanitized result
is retained locally at `.cache/f107/database-down.json`; the launcher smoke result
is `.cache/f107/launcher-results.json`. No destructive volume reset was used.

Early targeted tests exposed tool-sandbox permission failures in default temp
locations; workspace temp configuration and normal local process access resolved
them. An optional YAML inspection initially selected the absent `yaml` package;
the installed `js-yaml` parser succeeded. Formatting findings were corrected.
Final required checks above pass. None of these were an approval/SQL correctness
failure, and no dependency was installed to resolve them.

## CI status and sources

`.github/workflows/offline.yml` uses read-only repository permission, no persisted
checkout credentials, one bounded job, fixed supported Python/Node/uv versions,
lockfiles and Compose digest. Acquisition is explicit before the offline check
phase; no live-provider secrets or hosted-export steps exist. Integration fixtures
are isolated; installed Chrome is mandatory and missing/skipped evidence fails.
DB cleanup runs with `always()`. No additional backend service is introduced.

Action SHAs were verified against official refs, rather than inferred from stale
examples: [checkout](https://github.com/actions/checkout),
[setup-node](https://github.com/actions/setup-node),
[setup-uv](https://github.com/astral-sh/setup-uv). The workflow pins the resolved
v7/v7/v10.3.2 SHAs and uv 0.13.5. Only its shared command sequence and YAML syntax
were verified here. **A hosted Linux run, image acquisition on a fresh runner,
runner Chrome availability and cross-platform results remain unverified.** No
commit/push/dispatch was performed to claim otherwise.

## Remaining limits and stop point

- No known local F1-07 blocker remains. Owner review of F1-07/final F1 acceptance
  is still separate from passing checks. F2 remains unauthorized.
- One process/event loop with cooperative async dependencies only. No distributed
  ordering, malicious-plugin sandbox, real-user identity, production load or
  shutdown/power-loss guarantee. Existing approval unknown-outcome limits remain.
- Egress guards cover tested Python TCP/alternate-connect/UDP/DNS and frontend
  socket/fetch/DNS paths; browser page requests are intercepted and background
  features disabled. This is not an OS-wide firewall for arbitrary subprocesses
  or every browser-internal feature. No live provider/export implementation exists.
- The latency evidence is one synthetic local journey, not a p95/p99/SLO, load
  benchmark or proof that real-model calls fit these times. Simulated tokens do
  not measure a real tokenizer or money.
- Ring truncation/restart loses diagnostics; no hosted observability, traces of
  private content, durable runs or background recovery were added. Version
  allowlists and future schema migrations need deliberate maintenance.
- Synthetic database records persist in the local volume. Deletion/reset semantics
  and participant limitations are explicit in the runbook; no real-user deletion
  service, exercise safety review or clinical suitability claim is introduced.

The final acceptance report contains the cross-F1 gate matrix and measured
latencies. Stop after F1-07 for owner review; no commit or push.
