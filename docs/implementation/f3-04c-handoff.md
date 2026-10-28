# F3-04C handoff — offline live authority and final provider assembly

Date: **2026-10-25**. Scope: **F3-04C only**, following owner acceptance of offline
F3-04B. Prepared for review. F3-03C's live **NO-GO** remains in force. No live
generation/count request, positive monetary permit, active grant, spending,
hosted export, cloud provisioning, deployment, real-user data, commit or push.
Completion does not authorize source gate release, execution or later work.

## Result and audit

The remaining separate-authority model and single-request assembly are implemented
and exercised **only offline**. A new empty `probe_*` namespace cannot draw on
replay grants. The existing counted Responses adapter, native SQL transaction
algorithm, typed Agent, tools, independent validator and owned HTTP/TLS lifecycle
are reused. Both unconditional live-access barriers remain unchanged. Live
activation and actual-provider branches have intentionally not executed.

| Audited F3-04B boundary | F3-04C decision |
| --- | --- |
| `OpenAIHTTPS` prepares fixed HTTPS/auth but always denies | Preserve both hard denials; add explicit account/project binding and request-local acknowledged-send proof requirement |
| `ClaimedHTTP` already centralizes acknowledged claim→send | Reuse it with narrow fixed pair/session hooks; do not add a second claim or retry owner |
| Existing financial tables enforce replay/synthetic-only policy | Add migration 009's separate empty tables; reuse SQL through fixed trusted table-name routing, never change replay constraints/data |
| No live authority/configuration model | Strict immutable proposal binds exact identity, endpoints, model/tier, assets, dates, four ceilings and explicit count-charge evidence classification |
| SQL claim survives restart but transient send authorization must not | Bind one logical run durably; mint one-shot body/endpoint proof only after acknowledged claim, never from recovered rows |
| Assembly could otherwise become a general live executor | Fixed synthetic read-only profile plus `SingleProbe`; no CLI, HTTP route, sampler, candidate publication or write tool |
| Provider source hashes change accepted offline provenance | Add current snapshot; preserve both historical score files and assert identical 150 case/summary results |

No new dependency, SDK, service, queue, worker, cache, planner, production graph,
background recovery or financial policy. Main application remains fake-only.

## Files changed

| File | Purpose |
| --- | --- |
| `migrations/009_probe_authority.sql` | Eight empty separate control tables, relational/state/unique constraints; no seed/funding rows |
| `src/future_training/providers/authority.py` | Strict proposal/count-bound types, frozen asset binding and fixed synthetic input |
| `src/future_training/persistence/authority.py` | Separate accounting repository, ordered issuance/revocation/recovery, exact limits, single-run binding, ephemeral one-shot send proofs |
| `src/future_training/persistence/spending.py` | Extract existing project-row lock into one overridable fixed hook; preserve replay SQL behavior |
| `src/future_training/providers/probe.py` | Fixed unpublished assembly, scoped counted session/HTTP wrapper and proof consumption |
| `src/future_training/providers/sender.py` | Explicit bound account/project headers, proof check, narrow pair/send-scope hooks; hard denials unchanged |
| `src/future_training/providers/responses.py` | Narrow existing HTTP/pair factory hooks; request session inherits parent evidence kind |
| `src/future_training/providers/counted.py` | Use parent pair factory; existing admission/accounting sequence unchanged |
| `src/future_training/agent/protocol.py` | Internal truthful `live` provider-kind type; no application configuration expansion |
| `src/future_training/agent/orchestration.py` | Exact provider type checks, unpublished probe composition, existing session lifecycle and explicit evidence labels |
| `src/future_training/observability.py` | Fixed allowlisted authority-fixture/future-live source/model/token labels; no financial IDs/content |
| `tests/authority_doubles.py` | Fixed synthetic authority/window/nonmonetary ceilings |
| `tests/test_probe_authority.py` | 22 routine typing/binding/gate/privacy/composition/regression cases |
| `tests/test_authority_postgres.py` | 33 actual PostgreSQL authority/limits/fault/proof/TLS/assembly cases |
| `tests/test_migrations.py`, `tests/test_profile_postgres.py` | Add eight-table migration inventory to existing fixtures |
| `src/future_training/experiments/model_eval_assets.py` | Current source-reference filename only |
| `data/evaluation/model-v1/offline-scores-f3-04c.json` | Additive current-source synthetic provenance, identical case results |
| `data/evaluation/model-v1/README.md` | Explain preserved A/B/current C snapshots |
| `web/scripts/browser-smoke.mjs` | F3-04C screenshot namespace only |
| `docs/implementation/evidence/f3-04c-desktop.png`, `f3-04c-mobile.png`, `f3-04c-mobile-error.png` | Actual browser regression images, synthetic application workflow |
| `contracts/provider-safety.md` | Separate authority/proof/recovery contract; no spending or inference policy amendment |
| `docs/planning/19-f3-03c-pre-live-readiness.md` | Completed engineering vs external prerequisites, source/owner gates and blocked operator procedure |
| `README.md`, `docs/development.md` | Current status, migration and offline usage |
| `docs/implementation/f3-04c-handoff.md` | This report |

Existing 001–008 migrations, replay/counting SQL algorithm, rates, live hard-gate
bodies, domain/catalog/validator, public schemas/generated contracts, approval
and completion transactions, frozen 40-case corpus, F3 evaluation inputs/outputs/
expectations/scorer/rubrics, A/B score snapshots, dependencies/locks, graph
environment and historical handoffs are unchanged. No frontend application
behavior changes. Source hooks and labels above are the explicit limited changes.

## Authority, migration and lifecycle

Migration 009 creates `probe_authorities` and separately prefixed projects,
grants, sessions, attempts, pairs, operations and observations. This is a logical
table namespace in the existing database, not another service/database authority.
The schema retains the counted algorithm's foreign keys, one-operation-per-kind,
run/kind/ordinal uniqueness, monotonic wire claims and discrepancy metadata.
Original `spend_*` rows cannot supply these foreign keys or fund the probe.

`AuthoritySpec` requires account/project/operator/authority/grant/session binding,
`gpt-6.1-sol`, `default` tier, exactly both approved endpoint URLs, approved rate
version, current normalized prompt/tool/output/config/catalog/validator/input
digest, explicit zero-offset UTC timestamps with a positive window <=2 hours,
and four strict positive integer **proposed** microdollar limits. Unknown count
pricing carries neither a number nor evidence reference and rejects admission.
Live use additionally requires `provider_reviewed` plus a positive maximum and
bounded private reference. That classification is a trusted operator attestation,
not automatic verification of support/account terms. Actual proof remains absent.

`prepare()` creates only a zero-limit sentinel project and inactive proposal;
no grant/session. `simulate()` creates explicitly nonmonetary fixture accounting
and requires a synthetic evidence classification. Every simulation used isolated
test schemas and synthetic IDs; all were dropped. `activate()` checks the exact
live gate and independent financial hard denial before SQL. Its positive issuance
branch is unreachable, including direct internal active issuance while the
financial denial remains. No active branch was tested by bypassing both guards.

The accepted counted repository is reused with a fixed whitelist of trusted SQL
table identifiers. Parameter values never undergo replacement. A single project
advisory transaction lock precedes the project and authority row locks in every
issuance/reservation/claim/revoke/reconciliation path, including initial creation.
Identical issuance is idempotent; immutable fingerprint/specification changes
conflict. Exact database ceilings/mode/expiry must match the bound specification.
Each of project, UTC day, grant and session includes both operation types.

The first successful reservation binds one logical run durably. New keys/run IDs,
repository initialization or day/session rollover cannot reset the request.
All inherited token/attempt, ticket, settlement, discrepancy and unknown-liability
rules apply. SQL errors fence reuse until an explicit authoritative ordered read.
Loading the original private binding allows recovery after configuration changes;
new admission still rejects stale assets. Reconciliation never creates a count
ticket, send proof, refund or authorization to resume a logical request.

Applied locally with the existing checksum migrator:
`{'applied': ['009_probe_authority.sql']}`. Repeated migration: `{'applied': []}`.
Final native audit: **all nine checksums match**, **all 15 public financial/control
tables have zero rows**, **zero active authorities**, **zero remaining isolated
test schemas**. Existing replay grants remain replay-only; none were repurposed.

## Final assembly and safety

`SingleProbe` uses the fixed synthetic revision-1 adult strength/bodyweight/
beginner, two-day, 20-minute, no-exclusion profile and empty text. It invokes the
accepted Agent through `ResponsesProbe`, with no candidate store. A second call
on that object fails, and persistent single-run binding prevents a fresh object
from sending a new logical request. A candidate store is explicitly rejected at
composition. The result is independently validated and **unpublished**.

The same native counted session freezes payloads, validates exact count projection,
retains bounded request-local continuation, enforces usage and dispatches checked
tools. After a committed, acknowledged one-shot claim, an ephemeral proof binds
exact endpoint/kind/body. The connector consumes it once in the request context.
Missing/mismatched/reused proofs and restart cannot send. No payload digest is
stored or logged. Pure request construction uses explicit reviewed account/project
headers and discards untrusted caller auth/routing headers.

`OpenAIHTTPS` and active issuance still encounter the two independent unconditional
live/financial denials. Credentials/environment, hypothetical descriptors and
simulation/replay records cannot activate it. Making only the live gate permissive
in a unit fault still hits the financial denial; no real pool/socket/SQL grant is
created. No live executor command, CLI or application endpoint is added.

The owned HTTP boundary retains exact POST HTTPS/443 host/path allowlisting,
verified TLS/hostname, no redirects/proxies/environment CA settings/implicit
retries, identity-only encoding and bounded count/stream/body/frame sizes. Tests
use literal-loopback TLS with ephemeral synthetic certificates or exact mock
transports. Actual provider TLS/authentication remains unverified.

All original limits hold: **3 count /3 generation /6 combined**, **16,000 input /
4,000 output** inference, 2,000 output per attempt, 30 seconds, four read dispatches,
one semantic repair, one shared retry, one generation/principal and two globally.
Counted continuation and repair are fresh attempts; cancellation/unknown usage
never imply a free request. Only proven-unsent work can release a reservation.

Emergency shutdown durably revokes/disables and then cancels/awaits owned work;
uncertain SQL still fences locally and cleanup still clears proofs/tickets/native
state. Already claimed operations can charge after socket cancellation. This
repository deliberately cannot settle a count from its number-only response.
No automatic replay, count-billing reconciliation or background recovery exists.

## Observed fault, concurrency and protocol evidence

These are native PostgreSQL and controlled local TLS tests, not a reference
model or real-provider evidence. Fixture amounts below are invented nonmonetary
units labeled microdollars to exercise the exact arithmetic.

| Scenario | Observed result |
| --- | --- |
| Concurrent identical prepared issuance | Both return prepared; exactly one authority row |
| Concurrent changed operator/specification | One prepared, one `authority_conflict`; no overwrite |
| Prepared vs simulation/replay isolation | Prepared limits0/no grant; explicit simulation transition; original replay project count0; active authority count0 |
| Unknown/zero/missing/bool count ceiling | Strict rejection, no SQL/transport; synthetic quote cannot activate live authority |
| Wrong model/tier/endpoints/UTC/header-injection values | Strict schema rejection before authority use |
| Each of four exact financial ceilings exhausted | Subsequent pair rejected with both operation kinds included; no ceiling bypass |
| Actual SQL ceiling drift | Project/day modification cannot enlarge scope; `authority_mismatch` |
| Not-started/expired/revoked/wrong-account/assets | Claim/reservation fails; original matching repository can abandon proven-unsent rows |
| Lost issuance COMMIT ACK | Repository fenced; explicit reconciliation sees committed prepared row; retry idempotent |
| Uncertain rollback ACK / failed insert | Fence; ordered read confirms absent authority/grants; retry only after reconciliation |
| Repeated cancellation after issuance commit barrier | Owned transaction drained before cancellation propagates; fresh load finds one simulation grant/session, zero active authorities |
| Lost count claim ACK | Fresh repository sees count `sent`1,000; duplicate claim fails; abandonment does not release hold |
| Restart/new logical run | New repository cannot reset run; actual new interpreter reads retained sent1,000 row. Original writer process need not terminate for this assertion |
| One-shot send proof | Changed body/endpoint, second consumption, new repository and expiry reject; sent count remains1,000 |
| Input discrepancy after generation claim | Durable project freeze/one numerical observation; generation retains `sent`22,500; load/reconciliation still works after asset drift |
| Two-generation tool/continuation over real loopback TLS | Valid unpublished plan; 2 counts/2 generations/4 requests, one checked read, no second invocation |
| Same sequence with invalid output and repair over TLS | Validator rejects intermediate unknown exercise; final valid unpublished plan; 3/3/6 and one repair |
| Exact payload binding at TLS receiver | Every count body equals its paired generation's nine common fields, including native continuation |
| Fixture settlement | Every generation settles2,770; each successful count stays `responded_held`1,000 with unknown actual charge |
| Whole-request budgets | Provider-loop scenario stops at3/3/6; input scenario at16,000/one generation; output scenario at4,000/two generations; no extra send |
| Controlled deadline during stalled count + repeated stop | At clock30s returns budget error; child cleanup observed; supervisor empty; count `sent`, generation `not_sent`; repeat shutdown safe |
| Privacy with credential/project/operator canaries and live environment flags | Local fixture remains local; safe console/ring contain no private bindings, credentials, native state or workout fields; explicit authority-fixture source retained |

The existing native suites also pass unchanged for same/different-key approval
races, profile Save ordering, candidate expiry/publication, immutable readback,
completion submissions, day rollover, mixed budget liabilities, discrepancy
duplicates/uncertain transactions, claimed TLS cancellation, shutdown and retained
unknown charges. Those inherited tests are evidence for the shared algorithm;
the 33 new tests specifically establish its separate namespace/assembly behavior.
No claim of actual monetary issuance, provider billing or multi-worker correctness.

## Financial arithmetic and unresolved provider terms

The existing dated Sol Standard rate card remains unchanged. Worst-case generation
hold is `ceil(2.5*input + 10*output)` microdollars per attempt. Across the original
16,000 input /4,000 output and at most three attempts, the accepted conservative
run bound remains **80,002 microdollars = USD0.080002**, including rounding.
Proposed complete bound remains **80,002 +3*Cµ** for at most three counts.

No independently verified Cµ exists, so this report proposes **no concrete positive
live ceiling**. Current project/grant/day/session monetary authority is USD0.
The test Cµ=1,000 and test ceilings are synthetic and cannot support a live grant.
Even successful count replies retain maximum cost. Local accounting does not
establish invoices, provider-enforced limits, refunds, taxes/FX or surcharges.

Provider-dependent blockers remain counting tariff/maximum and endpoint-specific
retention; dedicated account/project/model/tier access; exact schema/stream/native
continuation compatibility; count-to-actual equality; cache TTL usage and pricing;
alias stability and end-to-end latency. The owner-reported external count18 is
not evidence for these and authorizes no request.

OpenAI Docs skill was used for read-only official documentation. Reviewed on
**2026-10-25**: [API authentication and explicit organization/project headers](https://developers.openai.com/api/reference/overview).
This supports the prepared routing headers; it does not verify access to the
proposed account/model or counting contractual terms. Existing dated pricing/
retention reviews remain in F3-03C/D and planning17–19; no new tariff is inferred.

## Commands and exact validation results

Environment: Windows11; Python **3.14.9**, Node **24.22.1**, npm **11.19.1**, Ruff
**0.17.2**, HTTPX **0.28.1**, PostgreSQL **18.6** and installed Chrome
**155.0.8059.85**. Existing dependencies reused; nothing installed/downloaded.
Docker used the cached existing image and local persistent volume.

```powershell
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
.venv/Scripts/ruff.exe check src scripts tests --no-cache
.venv/Scripts/ruff.exe format src/future_training/persistence/authority.py --no-cache
.venv/Scripts/python.exe scripts/evaluate_models.py --record-offline --output .cache/f3-04c
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-04c'
.venv/Scripts/python.exe scripts/check.py --integration --browser

# Existing isolated experiments/langgraph environment, from that directory:
.venv/Scripts/python.exe -m pytest -q --basetemp=../../.cache/pytest-f304c-graph-r2 --junitxml=../../.cache/f304c-graph-r2.xml

# Workspace root; ignored read-only audit helper saved during this work:
$env:PYTHONPATH='.'
.venv/Scripts/python.exe .cache/f304c-final-audit.py
git diff --check
git check-ignore AGENTS.md
```

Full shared checker: **22 child commands, all exit0**, summed command elapsed
**177.414s**. Exact expanded checks and results:

| Command | Observed result |
| --- | --- |
| Python/Node/npm/Ruff `--version`; `npm.cmd --prefix web ls --depth=0` | Versions above; installed locked tree resolves |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` |125 files already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Public contract drift0 |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Existing assets match; live disabled |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Historical F3-03A artifact unchanged; its old-policy labels are historical |
| `.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check` | Frozen50 inputs/expectations match |
| `.venv/Scripts/python.exe scripts/evaluate_models.py --check` | Current source/provenance matches; all150 case results unchanged |
| `npm.cmd --prefix web run check` | Strict TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | Generated TS/runtime/OpenAPI match |
| `npm.cmd --prefix web run test` | **85/85 passed**, zero skips/cancellations; Node test duration4.898s |
| `npm.cmd --prefix web run build` | Passed; command0.732s |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **964 passed,254 deselected**, zero errors/skips;27.26s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200/readiness200/invalid422; correlated safe console; owned child stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **254 passed,964 deselected**, zero errors/skips;118.07s |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 development +16/16 legacy held-out**, zero failures |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Five correct trials/mode, three mocked40ms reads/trial; peaks1/3, no retries; medians139.170/46.206ms sequential/concurrent |
| Isolated graph command above | **47 passed**, zero errors/skips;16.52s |
| Ignored final audit helper above |9 migration checksums match;15 control tables empty; active authority/test schemas0;150 results equal |

Root selections are disjoint: **1,218 Python tests**, including **55 new cases**
(22 routine +33 native). Frontend85 and isolated graph47 are separate checks.
Baseline40 and evaluation150 are software/fixture observations, not model trials.
Hosted CI was not triggered. Local CI-equivalent results/expanded command timings
are in `.cache/f107/check-results.json`; JUnit files are under `.cache/f107/` and
`.cache/f304c-graph-r2.xml`. `.cache/f304c-final-audit.json` records the empty-table,
migration and equality audit. These ignored artifacts contain synthetic metadata.

Targeted development runs also included:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_probe_authority.py tests/test_prepared_sender.py tests/test_counted_responses.py tests/test_agent_flow.py --basetemp=.cache/pytest-f304c-unit-r2 --junitxml=.cache/f304c-unit-r2.xml
# 207 passed,6.18s, before the two final mutated-provider regression cases
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_authority_postgres.py --basetemp=.cache/pytest-f304c-native-r3 --junitxml=.cache/f304c-native-r3.xml
# 32 passed,18.35s, before the final private-binding canary case
```

Initial non-elevated pytest temporary-directory access hit Windows WinError5;
the authorized local checks used subprocess/temp/pipe permissions. Initial lint
issues were fixed. First isolated graph run: **46 passed,1 failed** because a
deliberately mutated fake `kind=live` entered native session setup. Correction:
select native setup by exact concrete provider type and reject mutated labels;
two root regression cases added. Graph rerun47/47 and final root checks passed.
An intermediate rerun stopped on a102-character line; formatting fixed it before
the final all-green run. These are recorded failures, not provider behavior.

## Evaluation, privacy and browser preservation

The current source snapshot is
`974eaf22124e4ee4879cd1f4bc99a0da7a2829762fde7bcdc7057e72fd9dba86`.
Working base HEAD: `d1552e31c53e35e7f2cf782e022525b638a3a099`; no new commit.
Latest authored synthetic evidence directory:
`.cache/f3-04c/20261025T192542764030Z/`. Template/fake/replay expected handling
remains50/50 each; hard passes template50, fake44, replay44. The same six deliberate
hard failures per fake/replay path cannot obtain passing quality scores. Quality,
human and judge scores stay null. Both historical snapshots are unchanged and
all150 current case/summary results equal both. No evaluation feature was added.

Two configured ordinary sinks remain safe console and local trace ring; no hosted
or debug SDK sink. New account/project/operator/credential canaries plus existing
prompt/profile/plan/native/exception canaries pass. Private authority metadata
lives only in dedicated control records; raw body, payload hashes, credential and
opaque reasoning never enter ordinary telemetry or exported evidence. Native
state and send proofs are request-local and cleared on exit. No provider receipt
or real billing identity was used.

Actual Chrome repeated Save→Generate→Revise→lost approval response→same-key retry
→durable readback→profile change→immutable history→completion retry→owner switch.
Runtime errors0, external page requests0, horizontal overflowfalse; mobile Save
failure/recovery passes. Evidence: [desktop](evidence/f3-04c-desktop.png),
[mobile](evidence/f3-04c-mobile.png),
[mobile error](evidence/f3-04c-mobile-error.png). Mobile snapshot was visually
inspected: durable revision-1 snapshot remains after profile revision2, completion
records remain distinct and approval disabled for history. This is existing fake
application evidence, not a live-provider UI or published probe plan.

Main lock hashes remain `uv.lock`:
`a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a`, and
`web/package-lock.json`:
`cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf`.
No protected corpus/domain/contracts/prior-migration/historical evidence changes.
`AGENTS.md` remains ignored; nothing staged. Browser/API test children are stopped.
Local PostgreSQL is stopped with its volume preserved after the final audit.

Shutdown/recovery commands also executed:

```powershell
docker compose stop postgres
docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}} {{.Config.StopSignal}} {{.Config.StopTimeout}}' future-adaptive-training-agent-postgres-1
docker compose up -d --pull never --wait postgres
$env:PYTHONPATH='.'
.venv/Scripts/python.exe .cache/f304c-final-audit.py
docker compose stop --timeout 30 postgres
docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}} {{.State.Running}}' future-adaptive-training-agent-postgres-1
```

First default stop returned command0 but container137/non-OOM/SIGINT. Its cause
was not established. The cached container restarted healthy with the retained
volume; repeated audit again found nine matching checksums, all15 control tables
empty and active authority/test schemas0. Explicit30-second-grace stop completed
with container **exit0/non-OOM/not-running**. No power-loss durability conclusion
is inferred from this recovery check. Documentation UTF-8, local links, fences,
whitespace and `git diff --check` passed; no test-owned Chrome process remains.

## Readiness and limitations

Offline authority/assembly preparation is ready for owner review. Live operation
remains **NO-GO**. The [updated checklist and operator procedure](../planning/19-f3-03c-pre-live-readiness.md)
requires provider counting price/maximum and retention proof, current generation/
cache terms, account access, exact private binding/numerical four-ceiling approval,
privacy approval, explicit A–C live extension, separately reviewed release of both
source denials, final regressions and explicit execution/window/operator approval.
No concrete positive count bound or monetary ceiling can be approved by this code.

The positive active issuance and real-network branches are deliberately unexecuted;
their review remains a live prerequisite. Tests establish one-process synthetic
code/SQL ordering, conservative liabilities and local verified sockets, not provider
compliance, genuine model-selected calls, billing correctness, exact live usage,
power-loss guarantees, multi-worker support, model quality, fitness effectiveness,
production authentication, scale or cloud experience. Trusted local Python/SQL
operators are outside the untrusted-model threat boundary; the operator attestation
is not cryptographic account authorization. No billing settlement override, live
sampler or automatic logical-request replay is provided.

Stop after F3-04C for review. Acceptance cannot authorize provider requests,
monetary spending, broad evaluations, judge calls or later work.
