# F4-01 — Local release engineering and AWS deployment design

Date: 2026-10-25. Scope: **F4-01 only, submitted for owner review**. F1/F2 and
F3-05A's offline scope were already accepted. Local Docker builds, synthetic
operations and public pricing research were performed. No AWS resources, Terraform
apply, hosted CI run, provider/count request, monetary authority, telemetry export,
external deployment, real-user data, commit or push was performed.

## Result and architectural decisions

The application has a locked multi-stage local release containing FastAPI, the
built React frontend and the existing PostgreSQL service. It serves through the
existing loopback-only identity boundary. Backend runtime is non-root/read-only,
one process, fake-only and exporter-free. Database health precedes checksum-checked
migrations; readiness precedes use. The real Docker/HTTP/PostgreSQL drill restored
immutable plans, idempotency bindings and completion records into a fresh volume,
recovered from dependency/process faults and switched compatible images.

The runtime audit found a concrete packaging defect: fake generation imported
HTTPX-only replay/probe implementations even though HTTPX is a development
dependency. Native-provider imports are now conditional; exact native type checks
are retained. A fresh subprocess denies HTTPX import and still generates a valid
fake plan. The final thin image also exercises that path through real HTTP.
No provider gate, SDK, authority or production business schema changed.

Host networking is deliberate: bridge/proxy forwarding must not turn remote
requests into apparently local synthetic principals. Docker Desktop initially
had no reachable host-network listener; the owner enabled the setting, after
which Windows HTTP returned 200 and the listener was **127.0.0.1:8000**. A wildcard
bind, live provider, multiple workers and unacknowledged image startup fail closed.
Host networking is not appropriate public authentication or an OS egress sandbox.

The AWS recommendation is a short-lived t3.small host, local app/database and SSM
port forwarding. A separately priced Fargate/RDS/ALB alternative requires explicit
future network/identity changes. Neither is implemented or authorized to provision.
See the [cost/design proposal](../planning/22-f4-deployment-and-cost-plan.md).

## Changed files

| Paths | Change |
| --- | --- |
| `Dockerfile`, `.dockerignore` | Digest-pinned build stages, frozen Python/npm dependencies, minimal allowlisted context, 16-distribution runtime and non-root app |
| `compose.release.yaml` | Separate bounded local release services/volume, healthy DB dependency, loopback host network, read-only app, shutdown/log/resource bounds |
| `scripts/release.py` | Explicit release acknowledgment, safe startup/migrations/readiness, loopback Python connection guard and public source/package manifest |
| `scripts/release_probe.py` | Fixed synthetic HTTP seed/readback, approval/completion retries and bounded fake-generation measurement |
| `scripts/check_release.py` | Opt-in isolated Docker fault, restart, binary backup/restore and compatible rollback drill; keeps scoped volumes for review |
| `scripts/serve.py` | Bounded 35-second graceful shutdown inside 40-second container grace |
| `src/future_training/agent/orchestration.py`, `tests/test_release.py` | Conditional native transport imports; five thin-runtime/unsafe-startup regressions |
| `src/future_training/experiments/model_eval_assets.py`, `data/evaluation/model-v1/offline-scores-f4-01.json`, suite `README.md` | New current-source fingerprint reference; all 150 case/summary results equal historical snapshots |
| `web/scripts/browser-smoke.mjs` | Separate F4-01 evidence names; no UI/product change |
| `.github/workflows/offline.yml` | Build two release labels and run isolated release drill after stopping development DB |
| `docs/local-release.md`, `docs/runbook.md`, `docs/development.md`, root `README.md` | Local release/recovery instructions and current status |
| `docs/planning/22-f4-deployment-and-cost-plan.md`, this report | AWS comparison, IAM/state/HTTPS/teardown proposal, evidence and approval boundaries |
| `docs/implementation/evidence/f4-01-{builds,release,checks,cache-comparison,aws-costs}.json` | Bounded reproducibility, fault/restore/load, CI-equivalent, cache comparison and proposal arithmetic |
| `docs/implementation/evidence/f4-01-{desktop,mobile,mobile-error}.png` | Installed Chrome workflow regression evidence |

**No migrations:** existing 001–009 are unchanged. Root and experimental dependency
locks are unchanged. Historical review/acceptance, score snapshots and frozen
40-case files are unchanged. AGENTS.md remains local and ignored.

## Environment and build reproducibility

Windows 11 workstation, Docker Desktop Linux amd64 Engine **29.9.1**, Compose
**5.6.0**, buildx **0.38.0**. Host Python **3.14.9**, Node **24.22.1**, npm
**11.19.1**, Ruff **0.17.2**, installed Chrome **155.0.8059.85**. Container Python
is 3.14.9. Backend/PG limits are each one CPU/512 MiB; app pids limit 64. These
are laptop/VM measurements with ordinary desktop scheduling, not dedicated hosts.

Starting source HEAD: `02227c7871a2e707fe6f0f7fb91697669960a1ba`; implementation
remains an uncommitted diff. Root `uv.lock` SHA-256 remains
`a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a`.
Base image digests and exact build commands are in Dockerfile and below.

Two final **clean `--no-cache` builds** produced identical hashes for all **75**
application/migration/catalog/script/built-web files and identical Python plus
**16 runtime distribution versions**. Image sizes: baseline **226,200,977 bytes**,
candidate **226,200,936 bytes**. Candidate manifest/image ID tested by the final
drill is `sha256:deb14981a984fc945af2a7f3fe4d328dedd9fdca72a93fcc1e844b8b3701f4ce`;
the [build evidence](evidence/f4-01-builds.json) records both IDs and manifests.
Version labels/build metadata differ: **no bit-for-bit OCI reproducibility claim**.
No credentials or private worktree files are copied to the image. HTTPX, Langfuse,
Node and uv are absent from the final runtime.

An attempted `RUN --network=none` cache-only build failed on unavailable cached
Python wheels (Pydantic/Psycopg). That option was removed; package acquisition
requires network. This is a locked, repeatable payload build, not an air-gap build.
Initial harness issues (tmpfs option quoting and an HTTP helper/module name
collision) were corrected before successful complete drills. The first clean
builds preceded a measurement-helper correction; final evidence below is from
the final clean images and identical alternating workload. Earlier exploratory
measurements are not pooled into the final population.

## Commands and observed checks

Executed from repository root in PowerShell unless noted. Local Docker commands
required access to the Desktop engine; no cloud credentials were used.

```powershell
docker build --no-cache --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f4-01-baseline -t fata-release:f4-01-baseline .
docker build --no-cache --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f4-01 -t fata-release:f4-01 .
docker run --rm --network none --read-only fata-release:f4-01-baseline manifest
docker run --rm --network none --read-only fata-release:f4-01 manifest
docker run --rm --network none --read-only fata-release:f4-01
.venv/Scripts/python.exe scripts/check_release.py
docker compose up -d --pull never --wait postgres
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f4-01'
.venv/Scripts/python.exe scripts/check.py --integration --browser
.venv/Scripts/python.exe scripts/measure_catalog.py --compare
experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q
# From experiments/langfuse:
.venv/Scripts/python.exe -m pytest -q --junitxml=../../.cache/f4-01/langfuse.xml
# From root, after checks:
docker compose stop --timeout 30 postgres
```

| Check / exact component command | Observed result |
| --- | --- |
| Both final clean image builds | Success; identical payload/version manifests, different OCI metadata |
| Default image startup without acknowledgment | Nonzero exit before listener; explicit synthetic acknowledgment required |
| `.venv/Scripts/python.exe -m pytest tests/test_release.py -q` | Five passed (also included in full suite) |
| Root checker | **22/22 commands exit 0**, [recorded command timings](evidence/f4-01-checks.json) |
| `ruff check src scripts tests --no-cache`; `ruff format --check src scripts tests --no-cache` | Passed; 133 formatted files |
| `scripts/export_contracts.py --check` | Strict API/OpenAPI/TypeScript contracts unchanged |
| `scripts/prepare_responses.py --check`; `scripts/measure_token_admission.py --check`; `scripts/prepare_model_evaluation.py --check` | Provider fixtures/count protocol/evaluation manifests match |
| `scripts/evaluate_models.py --check` | 150/150 expected safe dispositions; template hard 50/50, fake/replay 44/50 each with six deliberate hard failures each retained; no quality rating hides a failure |
| `npm.cmd --prefix web run check`, `format:check`, `check:generated`, `test`, `build` | All passed; **85 frontend tests**, zero skipped/cancelled |
| Root pytest, `--basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **985 passed, 257 deselected**, zero skipped/failed, suite command 38.092s |
| `scripts/smoke_local.py` | Actual HTTP health/readiness and invalid request check passed |
| Integration pytest, `-q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **257 passed, 985 deselected**, zero skipped/failed, suite 140.76s |
| Frozen `scripts/evaluate_baseline.py --check` | **40/40: 24 development, 16 held-out**, no changed artifacts |
| `scripts/measure_async_reads.py` | Five sequential and five concurrent trials correct; 3 reads/trial, inflight 1 vs 3, zero retries; median 139.449 vs 48.691ms, controlled 40ms/read fake transport |
| Fresh cache prototype comparison | Exit 0; 216 eligibility/plan/validation equivalence checks each; no operation failures |
| Isolated LangGraph regression | **47 passed**, 18.49s; production still typed orchestration |
| Isolated socket-sealed Langfuse SDK regression | **16 passed**, 1.97s; six known deprecation/intentional socket-block warnings; no network export |
| Final opt-in Docker release drill | All startup/HTTP/load/fault/restore/rollback assertions passed; its source and restore containers stopped/removed, volumes retained |

Root selections are disjoint: **1,242 Python cases**, including six existing
reference-model cases rather than SQL proof. The 257 selection contains native
PostgreSQL, local TLS, ASGI/browser and operational tests; it is not 257 distinct
database transactions/scenarios. Graph 47, SDK 16, frontend 85, baseline 40 and
offline comparison 150 are separate denominators. No genuine model or human
quality evidence is inferred. Existing provider destination/TLS, canary, privacy,
ledger discrepancy/uncertainty, approval race and cancellation checks all passed
in their respective suites.

CI retains pinned actions, lock acquisition, PostgreSQL/schema isolation,
credential canaries and external-network-denied tests. It now executes the local
release drill after releasing ports. **Hosted GitHub Actions was not triggered or
verified**; local execution is CI-equivalent evidence only. Runner availability,
action execution and the 15-minute hosted job budget remain unverified.

## Real container fault and recovery evidence

Final run: `.cache/f4-01/3539bb6f/`; sanitized
[release evidence](evidence/f4-01-release.json). Actual PostgreSQL 18.6, real
loopback HTTP, fake generation; this is not an approval reference model.

| Operation | Observation |
| --- | --- |
| Startup order | Fresh DB healthy, nine migrations, app ready; no bind before migration completion |
| Full HTTP journey | Save A/B, generate, explicit revision, approve, durable readback/history, explicit completion, later profile revision; exact approved snapshot retained |
| Wrong owner/headers | B cannot read A's plan/completion; hostile Host and forwarded identity headers 403 |
| Broken database connection | Hold native profile-table lock, observe actual `pg_stat_activity` lock waiter, terminate waiting backend: request `http_error` in **0.2252s**; no successful candidate |
| SIGTERM with blocked request | Same native barrier; request safely `http_error`, stop **2.6970s**, app exit **0**; restart and original-key/readback checks pass |
| Database stop | `/health` **200**, `/ready` **503**; restart PostgreSQL, readiness and durable checks recover |
| SIGKILL/restart | Original approval/completion keys recover exact committed results; unapproved memory discarded |
| Backup | App quiesced; **79,992-byte** binary custom archive, SHA-256 in evidence; dump command **0.3576s** |
| Restore | Fresh target public table count zero; transactional `pg_restore`, **0.3834s** command; exact snapshot and keys/owner checks pass |
| Restored cardinality | **1 plan / 1 approval key / 1 audit / 1 session / 1 session key**, nine migrations; probe authorities **0** |
| Compatible image rollback | Stop current, run baseline label against unchanged restored schema, readback/retries pass; switch forward passes |
| Incompatible migration | Mounted modified 009 checksum: startup rejected before listener; no automatic mutation/reset |

Dump/restore durations exclude service startup/operator response and are **not
end-to-end RTO**. Quiesced synthetic records prove this recovery point only; there
is no WAL/PITR, off-machine backup or automated recovery claim. The image pair
contains the same business code/schema, so rollback is a same-schema procedure
test. Historical version compatibility/downmigration remains unproven.

The separate native SQL tests establish tested cancellation-safe commit
finalization, committed-key recheck after guard wait, uncertain commit quarantine,
mixed-operation reservations, unknown-charge preservation and restart outcomes.
The container SIGTERM drill does not substitute for those tests or prove arbitrary
power-loss correctness. Live grant/authority records are never created here.

## Bounded performance and resource observations

Fixed 20-record catalog, two supported synthetic principals, general strength /
bodyweight / beginner / two days: alternating B revision 1 at 20 minutes and A
revision 2 at 30 minutes in **both** modes. Four identical alternating warm-ups,
60 measured initial-generation requests per mode; batches of one or two distinct
principals avoid self-admission collisions. No artificial delay, provider request
or automatic retry. Raw per-request times/outcomes are in release evidence.

| Mode | Requests / errors | Total p50 / p95 (ms) | First SSE status p50 / p95 (ms) |
| --- | --- | --- | --- |
| Concurrency 1 | 60 / 0 | **51.481 / 98.546** | **10.915 / 49.821** |
| Concurrency 2 | 60 / 0 | **74.183 / 156.092** | **12.820 / 60.830** |

Total means request initiation through complete stream/EOF; first update means
the first progress **status**, not draft, browser paint or model token. p50 is
median; p95 nearest rank. Both modes include all attempts/errors. The first
post-start generation was 60.625ms, revision 63.219ms: single observations, not a
cold-start distribution. Concurrent latency increased in this run; do not infer
capacity/scaling or real-model latency from a two-principal localhost fake test.
Other desktop/profiling activity was not CPU-isolated.

Backend `/proc` RSS/high-water at measurement: **74,932 KiB**. A later one-point
Docker sample: app **57.05 MiB /512 MiB**, CPU **0.33%**, three PIDs; PG **42.2
MiB /512 MiB**, CPU **1.13%**, nine PIDs. These are different instruments/times,
not an allocation guarantee or sampled peak distribution. Host-network NetIO=0
is not proof of no TCP traffic. Request/response content was excluded from shared
measurements; private synthetic snapshots/keys/backups stay ignored.

The accepted F2 cache experiment was rerun unchanged: 216 cases (eight matrix
rows × three presets × three day counts × three exclusion variants), five rounds,
one/two cooperative clients, rotating uncached/cold/warm prototype modes, warm-up
one pass per case. Each operation/mode/client cell has **1,080 observations**;
4 operations ×3 modes ×2 clients = **25,920 observations**, zero failures.
Fresh [distribution summary](evidence/f4-01-cache-comparison.json) and historical
F2 raw evidence remain separate from HTTP timings. For one-client pipeline,
uncached/cold/warm service p50 **2.417 /3.072 /2.185ms**, p95
**4.319 /5.028 /3.656ms**. Prototype retention was eight entries/37,264 logical
bytes. Modest warm gains and cold penalty do not justify new production cache
state; the approved uncached decision stands. No cache was added to the app.

## UI and public cloud evidence boundaries

Installed Chrome regression against the isolated local test application passed
Save → Generate → Revise → lost approval response/same-key retry → readback →
completion retry → profile change/immutable history → owner switch/error recovery.
Screenshots: [desktop](evidence/f4-01-desktop.png),
[mobile](evidence/f4-01-mobile.png), [mobile error](evidence/f4-01-mobile-error.png).
No overflow/runtime errors/external page resource requests. This browser harness
uses its existing controlled fault server, **not the container listener**; the
release separately exercises real HTTP and byte-identical built frontend assets.
No cloud browser, production authentication or public TLS was tested.

Post-drill check: `docker compose -f compose.release.yaml -p
fata-f401-3539bb6f-restore up -d --pull never --wait` followed by a local Python
`urllib.request` fetch of `/` and both built assets verified all three HTTP bodies
against the clean-image SHA-256 manifest and local browser-tested build. Windows
`Get-NetTCPConnection -State Listen -LocalPort 8000` reported **127.0.0.1 only**.
Native SQL inspection again found zero probe authorities and zero test-schema
tables. The scoped project was then stopped with `stop --timeout 40` and `down`
without volume removal. This is release-asset serving evidence, not a second
browser workflow execution.

Official public AWS prices checked 2026-10-25 support approximately **$1.11930**
for the proposed EC2 24-hour demo/seven-day artifacts versus **$2.97668** for
Fargate/RDS/ALB assumptions. Idle baseline/retained resources and omitted costs
are explicit in document 22; estimates are not bills or caps. Only public pricing
documents/files were retrieved. No AWS CLI/SDK/account access or Terraform
implementation was used. AWS operation, IAM correctness, SSM tunnel, cloud HTTPS,
restore/RPO/RTO, teardown and actual billing remain unverified.

## Limitations and readiness for review

The [operator runbook](../local-release.md) covers installation, host networking,
startup/migrations, readiness, stopping, backup/restore, image rollback, faults and
named cleanup. Logs/ordinary traces remain metadata-only; no raw provider data,
reasoning, payload hashes or private billing IDs were added. Backups contain
synthetic business records and must not enter logging/export sinks.

No public bind/auth, multiple workers, replicas, additional service, production
LangGraph, cache or financial policy was introduced. Synthetic trust/database role,
same-host backups and host-network access limit this release to local operator
use. Provider count billing/retention and separately reviewed source/privacy/
numerical authorization still block live use; the owner-reported external manual
count of 18 is not application permission or model generation evidence. Langfuse
remains isolated and export-disabled. No F3 live quality claim is closed by F4.

F4-01 local scope is ready for review. F4-02 can be considered only after separate
authorization, with explicit topology/region/budget, secure identity/HTTPS choices,
state/secrets and teardown decisions. No cloud execution is implied by readiness.
