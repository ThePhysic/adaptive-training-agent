# F3-05A handoff — offline Langfuse evaluation and observability

Date: **2026-10-25**. Scope: **F3-05A only**, after acceptance of offline F3-04C.
Prepared for review. No live provider/count/judge calls, hosted export/service,
positive financial authority, spending, cloud resources, deployment, real-user
data, commit or push. Counting billing/retention remain unresolved despite the
owner-reported external count18 and support escalation. Live **NO-GO** remains.

## Result and architecture decisions

Implemented a metadata-only local projection and a separately locked actual
Langfuse SDK5 harness. The existing tracing/scoring systems remain authoritative.
Main application work invokes no SDK, HTTP exporter, flush, media uploader or
telemetry retry. Native PostgreSQL approvals succeed with failing/closed/full
local projection buffers. The sealed SDK process consumes sanitized snapshots
after business work and cannot be activated by credentials or environment flags.

Final evidence: **738 actual SDK-shaped observations** (726 from the shared
150-result comparison, plus12 from an induced HTTP agent failure), **300 SDK
BOOLEAN scores**, **three native OTel experiment groups /150 case roots**,
zero failed/dropped capture records and zero network requests. These are local
SDK/serialization/mocked-API observations, not hosted ingestion or real-model
quality. No synthetic plan content enters the new telemetry artifacts.

| Audit | Reuse / decision |
| --- | --- |
| Local tracing | Reuse sanitizer, ContextVar correlation, safe console, bounded ring and existing stages; opt-in local copy only |
| OTel dependencies | Existing FastAPI transitive OTel API1.45.1 has inert ProxyTracerProvider; no main SDK/exporter. Private SDK provider remains separate; no global registration |
| Provider accounting | Preserve reported/fake provenance and request aggregate input/output/cache/write/reasoning counts. Do not duplicate aggregates across generation spans or infer zero unknown cost |
| Evaluation | Reuse `evaluate/run_case/score`, fixed50 cases, exposure labels, rubric and manifests; add optional case trace links only |
| SDK defaults | Separate environment/process, socket/DNS seal, cleared environment, explicit mock HTTP, bounded in-memory exporter, no automatic integrations |
| SDK experiments | Use documented native experiment/item OTel attributes and typed `Evaluation` BOOLEAN scores; do not duplicate tasks through SDK `run_experiment` |
| Approval safety | No telemetry delivery in transactions; real SQL outage/buffer tests demonstrate unchanged atomic approval/readback/key recovery |
| Privacy | Reconstruct allowlisted metadata at each boundary; no content, private bindings, exceptions, native reasoning, payload hashes, baggage or resource detectors |

No new service, queue, application worker, cache, provider integration, planner,
judge, independent evaluation platform or production graph. SDK internal consumers
are confined to the disposable offline process, bounded by permitted inputs,
and explicitly joined at close.

## Files changed

| Path | Change |
| --- | --- |
| `src/future_training/langfuse_local.py` | Bounded thread-safe metadata observations, local-only tracer and existing-score projection |
| `src/future_training/observability.py` | Fixed `evaluation.case` / `agent.repair` stages and template evidence label |
| `src/future_training/agent/orchestration.py` | Observe attempted repair-stage entry without changing repair logic, prompt or budget |
| `src/future_training/experiments/model_evaluation.py` | Optional tracer/case-link map; existing execution/scorer unchanged |
| `src/future_training/experiments/model_eval_assets.py` | Current additive score-reference filename |
| `data/evaluation/model-v1/offline-scores-f3-05a.json` | Current source manifest; all150 case/summary outcomes equal earlier snapshots |
| `data/evaluation/model-v1/README.md` | Explain current vs historical provenance |
| `scripts/prepare_langfuse.py` | Fixed offline common-runner→sanitized metadata packet, no SDK or live options |
| `experiments/langfuse/pyproject.toml`, `uv.lock` | Isolated pinned SDK/dependency environment |
| `experiments/langfuse/offline_sdk.py` | Socket-sealed SDK wrappers, native experiment attributes, mock score API, bounded capture and owned cleanup |
| `experiments/langfuse/run.py`, `README.md` | Reproducible fixed-file SDK exercise, source/lock manifests and safe usage |
| `experiments/langfuse/tests/test_sdk.py` |16 actual SDK correlation/privacy/export/score/bounds/lifecycle cases |
| `tests/test_langfuse_local.py` |16 main-environment tracing, failure, cancellation, bounds, privacy and evaluation cases |
| `tests/test_langfuse_postgres.py` |3 actual PostgreSQL approval/telemetry-fault cases |
| `.github/workflows/offline.yml` | Separate frozen SDK environment/check/capture step; hosted CI not triggered |
| `web/scripts/browser-smoke.mjs` | F3-05A evidence namespace only |
| `docs/implementation/evidence/f3-05a-desktop.png`, `f3-05a-mobile.png`, `f3-05a-mobile-error.png` | Actual installed-browser fake-application regression evidence |
| `docs/planning/21-f3-langfuse-offline-integration.md` | Integration/version/mapping/retention limits and future hosted requirements |
| `docs/planning/19-f3-03c-pre-live-readiness.md` | Record accepted offline C and separate offline Langfuse boundary; preserve live blockers |
| `README.md`, `docs/development.md`, this report | Current status, reproduction and handoff |

**No migrations.** All001–009, provider/spending/authority code and both hard
denials, approval/completion persistence, public/generated contracts, domain/
catalog/validator, frozen40, fixed50 scenarios/outputs/expectations/scorer/rubric,
all historical score snapshots, root/graph locks, frontend application and
historical handoffs are unchanged. New source provenance is additive.

## SDK compatibility and containment

Selected maintained GA **Langfuse5.0.4**, separately resolved with **OTel SDK/API
1.45.1**, HTTPX0.28.1 and Pydantic2.14.1 on Python3.14.9. New isolated environment
contains41 installed packages; root lock is untouched. Upstream exporter/semantic
dependencies include0.66b1 components through the stable SDK dependency graph.
Install, frozen offline sync and `uv pip check` passed. SDK metadata permits
Python>=3.11,<4 and lists3.14. Main application has only the pre-existing locked
transitive OTel API from FastAPI, with no installed Langfuse/OTel SDK/exporter.

Official sources reviewed **2026-10-25**: [release metadata](https://pypi.org/pypi/langfuse/5.0.4/json),
[GA compatibility](https://langfuse.com/docs/compatibility),
[v4→v5 migration](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5),
[Python reference](https://python.reference.langfuse.com/langfuse),
[private-provider/export controls](https://langfuse.com/docs/observability/sdk/advanced-features),
[native experiment attributes](https://langfuse.com/docs/evaluation/experiments/experiments-via-opentelemetry).
Public docs/package descriptions partly lag releases. Installed v5's generated
score client uses `/api/public/scores`; the fixed mock validates that actual path.
Do not assume another path from the version-matrix Scores APIv3 label.

The SDK constructor ordinarily creates a secondary default async API client and
export/score/prompt-cache consumers. The harness explicitly installs a private
TracerProvider, resource attributes without host/user discovery, empty OTel
contexts, synthetic keys, fixed mock sync client and an async MockTransport
factory. Permanent socket/DNS denial independently blocks real/secondary exporters.
Langfuse/OTel/provider/proxy settings are cleared before SDK initialization;
SDK debug/default handlers cannot bypass safe formatting. No automatic OpenAI or
LangChain instrumentation is imported. The process accepts no destination or keys.

SDK5.0.4 `shutdown()` leaves its prompt-refresh consumer alive. The pinned harness
explicitly closes that private task manager, the provider/export worker, score
consumer, sync HTTP client and unused async mock clients. Tests verify no newly
owned thread survives cancellation/close. Private lifecycle hooks and the async
factory substitution are reasons to keep this isolated; an SDK upgrade requires
source review and all tests. This process must not be embedded in the application.

## Mapping, bounds and privacy evidence

Original128-bit trace IDs are retained. Source128-bit span IDs map to OTel64-bit
IDs with full opaque source/parent IDs retained in metadata. Zero/collision cases
reject; roots have no invented parent. Tests assert every parent, ID, status,
completion order and duration. UTC end is local append time; start is that end
minus the original measured duration, not a provider timestamp. SDK error levels
carry only allowlisted classifications, never stack/exception events.

Existing request/provider/tool/validator/publication/approval/failure spans map
to generic, agent, generation or tool observations. An explicit repair-stage span
records attempted entry, including rejection after the sole repair is consumed.
Provider-stage spans currently lack independently validated per-attempt token
detail: request totals remain labeled aggregates at agent execution. No duplicated
token totals, fabricated usage, auto-priced costs or count-is-free assumption.

Main projection:<=2,048 entries /4MiB encoded records, plus bounded identity/object
overhead, oldest-first eviction, copy isolation and retained-window dedup/conflict
checks. SDK:<=2,048 identities/captured spans,512 queued spans,150 distinct
case/source pairs ×2 scores. Default large SDK queues are inaccessible to inputs
beyond those caps; media is disabled. Failure drops diagnostics, never retries
business work. Closing buffers is idempotent and clears memory.

Canaries cover existing safe console/ring plus local projection, SDK memory,
mock-score capture and SDK-generated logs. Secret/PII/private-account markers,
workout fields and native reasoning markers are absent from sanitized capture.
Tests enable hostile tracing/media/proxy/credential/OTel exporter variables,
exercise a secondary OTLP exporter and prove it cannot connect. Global OTel
provider remains unchanged. These are cooperative code/test fences, not an OS
firewall or a defense against a malicious local Python administrator.

Native SQL tests separately inject failing, already-closed and full observation
buffers around candidate publication/approval. Each approval commits exactly
one plan/key/audit row; same-key recovery returns the same receipt. SDK export
cannot interrupt approval because no SDK delivery occurs on that execution path.

## Experiment comparison and failure investigation

The common runner generates **726** sanitized observations for150 existing
case/source results. SDK attributes bind150 roots into **three experiments**;
the fixed mocked score API accepts **300 BOOLEAN scores**. Every source retains
50 cases: expected handling template50/fake50/replay50, hard pass template50/
fake44/replay44. All12 deliberate hard failures remain visible and ineligible for
quality ratings. SDK scores reuse existing verdicts; no second scorer/task runner.
SDK `run_experiment` is deliberately avoided to prevent duplicated task execution,
default50-way concurrency and content capture.

Frozen40 remains24/16; fixed50 remains40 development/10 **developer-exposed**
comparison candidates. No unseen holdout, genuine model selection, human rating,
judge score, quality rating or fitness-effectiveness result. Clarity remains N/A.
The original manifest/scenario/source fingerprints remain in historical evidence;
new source fingerprints are named separately. Detailed packets retain the common
manifest, rubric/exposure provenance, SDK lock and bridge/driver source hashes.

Actual induced failure through HTTP: a scripted fake chooses the read-only catalog
tool, then twice returns an unknown exercise. Independent validation rejects both.
One repair is accepted; the second attempted repair raises
`semantic_repair_exhausted`. Final state is failed/error, no candidate published.
The12-span trace includes **3 provider**, **1 tool**, **2 validation**, **2 attempted
repair-stage** spans, plus execution/session/terminal/HTTP. It consumes **7,308
input /787 output simulated tokens**, **3 attempts,1 read,1 repair,0 retries**.
HTTP200 is transport status; business outcome is error. Observed HTTP duration
**15.891ms**, one local fake sample, not inference latency or an SLA.

Root cause is deliberately invalid synthetic proposals; the authoritative validator
and repair bound behaved correctly. Correction needed for investigation was extra
metadata visibility at attempted repair entry, not a relaxed rule. Regression
tests assert counters, terminal failure, correlation, privacy and cancellation.
SDK capture includes these12 failure observations in addition to726 comparison
observations: **738 total**, with zero dropped/failed captures. The independent
SDK shutdown-thread defect found during testing was corrected as described above.

Local ignored evidence: `.cache/f3-05a/packet.json`, `failure.json`,
`sdk-result.json`, `.cache/f305a-final-audit.json`. No raw plan/prompt/native state
enters these new telemetry packets. Keep detailed local artifacts14 days then
review/remove the exact directory. No automatic purge or upload exists.

## Exact commands and observed checks

Environment: Windows11, Python3.14.9, Node24.22.1, npm11.19.1, Ruff0.17.2,
HTTPX0.28.1, local PostgreSQL18.6 and installed Chrome155.0.8059.85. Only the
authorized isolated SDK environment was installed; root/graph dependencies stayed
unchanged. Docker used the cached image, no image pull or additional service.

```powershell
# From experiments/langfuse; initial authorized local dependency acquisition:
uv sync --python ../../.venv/Scripts/python.exe

# Workspace root:
docker compose up -d --pull never --wait postgres
.venv/Scripts/python.exe scripts/evaluate_models.py --record-offline --output .cache/f3-05a
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-05a'
$env:FATA_WRITE_F305A_EVIDENCE='1'
.venv/Scripts/python.exe scripts/check.py --integration --browser
.venv/Scripts/ruff.exe check src scripts tests experiments/langfuse --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests experiments/langfuse --no-cache
.venv/Scripts/python.exe scripts/prepare_langfuse.py

# From experiments/langfuse:
$env:PYTHONPATH='../../src'
.venv/Scripts/python.exe run.py
.venv/Scripts/python.exe -m pytest -q --junitxml=../../.cache/f305a-sdk-final.xml
uv sync --frozen --offline --python ../../.venv/Scripts/python.exe
uv pip check --python .venv/Scripts/python.exe

# From experiments/langgraph, unchanged isolated environment:
.venv/Scripts/python.exe -m pytest -q --basetemp=../../.cache/pytest-f305a-graph --junitxml=../../.cache/f305a-graph.xml

# Workspace root, saved ignored read-only audit helper:
$env:PYTHONPATH='.'
.venv/Scripts/python.exe .cache/f305a-final-audit.py
git diff --check
git check-ignore AGENTS.md
docker compose stop --timeout 30 postgres
```

Full shared checker: **22 child commands, all exit0**, summed command elapsed
**182.042s**. Expanded exact checks:

| Command | Observed result |
| --- | --- |
| Python/Node/npm/Ruff `--version`; `npm.cmd --prefix web ls --depth=0` | Existing versions/tree resolve |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` |129 application/check/test files formatted; expanded check including SDK132 |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | No public contract drift |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Five existing assets match; live disabled |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Historical F3-03A artifact unchanged; old labels remain historical |
| `.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check` | Fixed50 cases/assets unchanged |
| `.venv/Scripts/python.exe scripts/evaluate_models.py --check` | Current source snapshot matches; all150 outcomes unchanged |
| `npm.cmd --prefix web run check` | Strict TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | TS/runtime/OpenAPI match |
| `npm.cmd --prefix web run test` |85/85 passed, zero skipped/cancelled;4.597s test duration |
| `npm.cmd --prefix web run build` | Passed;0.685s command |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` |**980 passed,257 deselected**, zero errors/skips;25.28s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200/readiness200/invalid422; safe correlated console, owned child stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` |**257 passed,980 deselected**, zero errors/skips;125.19s |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` |24/24 development +16/16 legacy held-out; zero failures |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Five correct trials/mode, three mocked40ms reads; peaks1/3, no retries; medians139.307/46.348ms sequential/concurrent |
| Isolated SDK tests above |**16 passed**,1.76s;5 upstream deprecation warnings +1 intentional socket-guard warning |
| Isolated graph tests above |**47 passed**,15.58s, zero errors/skips |
| Frozen SDK sync / pip check |41 packages checked; all compatible; no download |
| Metadata producer / SDK run |726 comparison observations;150 roots/three groups; plus12 failure observations;300 scores; zero capture failures/drops/network requests |
| Final local audit | Nine migration checksums match, migration repeat[], all15 financial/control tables empty, no active authority/test schemas, all150 outcomes equal A/B/C/05A |

Root selections are disjoint: **1,237 Python tests**, including19 new main cases
(16 routine +3 native). SDK16 and graph47 are separate environments. Frontend85,
baseline40 and evaluation150 are separate denominators, not genuine model samples.
Hosted CI was not triggered; the new SDK step is locally exercised CI-equivalent
evidence. Timings/commands/JUnit are in `.cache/f107/` and named SDK/graph XML files.

Targeted development commands also passed:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_langfuse_local.py --basetemp=.cache/pytest-f305a-main --junitxml=.cache/f305a-main.xml
#16 passed,2.99s
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_langfuse_postgres.py --basetemp=.cache/pytest-f305a-db --junitxml=.cache/f305a-db.xml
#3 passed,2.08s
```

Initial isolated SDK run:6 passed/5 failed. Three assertions expected OSError
instead of the independent pytest socket-creation rejection; one malformed test
targeted the wrong duration field; one exposed the actual prompt-cache thread
remaining after normal SDK shutdown. Corrected those cases and the pinned cleanup;
final expanded SDK16/16 passes. Initial lint issues were formatted/fixed. SDK
Backoff deprecation remains documented; it is not silently suppressed. No live
compatibility or transport claim follows from these failures/corrections.

## Provenance, browser and readiness

Working base HEAD: `97030e72322873cef068b333a0c193a6ae9432e5`; no new commit.
Current main source digest:
`d19875a124a157a5203b3c914faef221277225a5a45f5d319376c505af2b675b`.
SDK lock digest:
`107c1320604af716a80ac135df1b707949a23c477c08622e8cca7ec4ba4eea35`.
The SDK artifact additionally records actual bridge and driver hashes. Main lock
remains `a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a`;
frontend lock remains `cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf`.
Historical A/B/C case/summary equality and protected-source/file checks passed.

Installed browser repeats Save→Generate→Revise→lost approval response→same-key
retry→durable readback→profile change→immutable history→completion retry→owner
switch, mobile failure/recovery and no horizontal overflow. Runtime errors0,
external page requests0. [Desktop](evidence/f3-05a-desktop.png),
[mobile](evidence/f3-05a-mobile.png), [mobile error](evidence/f3-05a-mobile-error.png)
are existing fake-application regression evidence, not a Langfuse dashboard.
`AGENTS.md` remains ignored; nothing staged. API/browser children are stopped and
local PostgreSQL is stopped with its volume preserved after audit.

Offline scope is ready for owner review. Hosted compatibility, UI grouping/query
behavior, real ingestion, provider usage, model quality, human preference, price,
retention enforcement/deletion and cloud/production operation remain **unverified**.
The [activation specification](../planning/21-f3-langfuse-offline-integration.md)
requires a separately reviewed hosted boundary, US tenant/path allowlist,
authentication/access review, verified deletion vs access-window terms, masking,
numerical budget/event ceilings, outbound permission, operator window/shutdown
and explicit execution approval. A credential or free tier is not authorization.

The sealed harness is intentionally not a latent hosted switch. SDK lifecycle
private hooks and generated-route differences must be reassessed for any upgrade.
Current per-attempt token details remain absent where the source lacks them;
request aggregates are labeled and no financial authority is inferred. Existing
synthetic-only, one-process, real-user authentication and live-provider release
gates remain. Stop after F3-05A; no F3-05B or later work begins.
