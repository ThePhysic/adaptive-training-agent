# Local synthetic demonstration

F5-D1, 2026-10-27. This demonstrates software behavior, not real-model quality or
fitness effectiveness. No credentials, provider requests, AWS, hosted telemetry,
genuine cases or people are needed. The 20-pair independent study remains deferred.

## Prerequisites

Use the installed locked environment: Python 3.14.9, Node 24.x, the repository's
`.venv` and `web/node_modules`, Docker's Linux engine with the cached Compose
PostgreSQL image, and an installed Chrome. This milestone installed nothing.
On Windows the tested Chrome is at
`C:/Program Files/Google/Chrome/Application/chrome.exe`; select your installed path.
On Linux use `.venv/bin/python` and an installed `google-chrome`. No browser
download, `--no-sandbox`, Docker socket exposure to the app, Redis or extra frontend
server is required. The application serves built React from FastAPI.

Only localhost synthetic adult preferences are supported. Keep the one-process,
loopback Host/Origin/peer guards. Do not use a proxy, public listener, extra workers,
real profile data or an external participant. Do not set any evidence-writing
environment variable from older milestones: those can overwrite historical files.

## Reproduce the complete automated UI journey

From the repository root in PowerShell, with no development/release API using the
same ports:

```powershell
docker compose up -d --pull never --wait postgres
if ($LASTEXITCODE -ne 0) { throw 'Local PostgreSQL startup failed' }
npm.cmd --prefix web run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
$env:FATA_BROWSER_EXECUTABLE = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE = 'f5-d1'
# Confirm old write-evidence flags are absent; do not opt into historical exports.
Remove-Item Env:FATA_WRITE_EVIDENCE -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -m pytest tests/test_browser_ui.py -q -s -m integration --basetemp=.cache/f5-d1/browser-repeat
if ($LASTEXITCODE -ne 0) { throw 'Local browser demonstration failed' }
Remove-Item Env:FATA_BROWSER_EXECUTABLE,Env:FATA_BROWSER_EVIDENCE_STAGE -ErrorAction SilentlyContinue
```

This uses an actual installed headless Chrome, loopback TCP Uvicorn, built React
assets and real PostgreSQL. The fixture creates a uniquely named test schema,
executes existing migrations, records its migration checksums and binds all
repositories/readiness to that schema. It drops only that owned schema on teardown.
It does not migrate, clear or save into the development `public` schema. Uvicorn
uses an available loopback port; no existing server is reused or terminated.

The browser performs the actual controls in this order:

1. Select profile A; attest synthetic adult inputs; Save general strength,
   bodyweight, beginner, two days, 20-minute preset. No implicit Save occurs.
2. Generate preview; wait for complete SSE output. A draft alone cannot be approved.
3. Revise once; verify another revision is disabled. Review the complete result.
4. Explicitly Approve. A test-only interception loses the successful response.
   Choose **Retry approval**, preserving the exact key. Read the durable saved plan.
5. Explicitly submit session 1 as completed, moderate effort, rating 4; lose its
   response, then retry that same submission. Submit session 2 as skipped.
6. Save current preferences as 30 minutes. Open saved history: the approved
   snapshot still shows its original 20-minute profile and submitted records.
7. Reload the entire page. Only persisted history is recovered; no transient plan
   is restored or approved automatically. Open the saved plan and both records.
8. Switch to profile B. A single injected Save failure leaves generation disabled;
   explicit Save recovers. A's plan is not available to B.

Success prints zero runtime/external-page errors, same-key recovery booleans and
structural SQL counts: one plan, one approval key, one audit, two session records
and two session keys. Health/readiness are 200 against the owned schema.
The tracked `docs/implementation/evidence/f5-d1-*.png` files are historical desktop,
mobile and injected mobile Save-error evidence. Fresh runs preserve those bytes
and write three PNGs under a new ignored `.cache/browser-evidence/<UUID>/` directory.
The successful harness JSON prints their actual repository-relative paths in its
`screenshots` array; use those reported paths to inspect the new run. The evidence
stage selects the filename prefix, not an arbitrary output destination. No automatic
copy into tracked historical evidence occurs. A failing command must be investigated;
do not skip assertions, reset approval state or rerun an uncertain real operation.

## Optional hands-on application

The automated journey above is the freshly verified UI demonstration. For a
human-operated window, use a **new local release project** with a newly built image
and empty volume; do not overwrite the existing development database. See
[local release](local-release.md) for the established safeguards and recovery.
Docker Desktop host networking must already be enabled; this task changes no OS
setting. Stop the development PostgreSQL after native tests finish, retaining its
volume. Check that ports 8000 and 55432 are free; never kill another owner.

```powershell
docker compose stop --timeout 30 postgres
docker build --network none --pull=false --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f5-d1 -t fata-release:f5-d1 .
if ($LASTEXITCODE -ne 0) { throw 'Release build failed' }
$demoProject = 'fata-f5-d1-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$env:FATA_RELEASE_IMAGE = 'fata-release:f5-d1'
docker compose -f compose.release.yaml -p $demoProject up -d --pull never --wait
if ($LASTEXITCODE -ne 0) { throw 'Inspect this owned project; do not delete its volume' }
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
```

Open `http://127.0.0.1:8000/` and use steps 1–3 above, then approve once and inspect
saved history. Response-loss and Save faults are injected only by the automated
harness; do not expect them in ordinary use. Free text outside supported structured
preferences can clarify/abstain; it is not a general conversational trainer.
No interactive operator session is claimed by automated evidence.

The image is non-root, read-only, single-process and fake-only. Startup performs
checksum-verified migrations on this fresh project, then readiness. The Docker
build reused pinned cached dependencies; `--network none` restricts RUN steps, not
BuildKit's registry metadata/authentication traffic. This is not a proven
air-gapped rebuild. No provider or telemetry service is involved.

Stop only this project; keep its synthetic volume for inspection/recovery:

```powershell
docker compose -f compose.release.yaml -p $demoProject stop --timeout 40
docker compose -f compose.release.yaml -p $demoProject down
Remove-Item Env:FATA_RELEASE_IMAGE -ErrorAction SilentlyContinue
```

No `down --volumes`, pruning or deletion of existing app data is part of this
runbook. Keep the project name while it exists. A later explicitly selected
demo-only volume can be removed only after its ownership and recovery boundary
have been reviewed. Restore the development PostgreSQL only if you need it again.

## Failure and recovery walkthrough

Run these existing tests against disposable schemas/controlled transports:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_streaming.py tests/test_observability.py tests/test_async_diagnostics.py -q --basetemp=.cache/f5-d1/stream-repeat
.venv/Scripts/python.exe -m pytest tests/test_approvals_postgres.py tests/test_operations_postgres.py tests/test_stream_postgres.py -q -m integration --basetemp=.cache/f5-d1/recovery-repeat
```

These cover Stop/disconnect before publication, cancelled revision cleanup,
concurrent approval conflicts, lost/uncertain commit reconciliation, fresh-process
same-key recovery, native connection termination and readiness degradation/recovery.
They distinguish controlled ASGI/clock fault evidence from real local PostgreSQL
transactions; a browser success alone does not prove all race cases.

`test_induced_failure_is_correlated_without_content` investigates an injected
invalid final proposal, one repair and a second rejection: final `done(error)`,
three provider attempts, one tool, one repair, `semantic_repair_exhausted`.
It checks trace parentage and metadata-only console canaries. HTTP 200 is not plan
success; inspect the terminal business outcome. Local traces live in a bounded
memory ring; no exporter or trace HTTP endpoint is enabled. The existing
[runbook](runbook.md#diagnose-a-request-without-content-capture) explains filtering
supported console metadata. Do not enable payload/SQL/debug logging.

## Separate synthetic evaluation walkthrough

This is an experiment, not a user-facing application feature or genuine study.
Start the same PostgreSQL test service, then:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_synthetic_collection.py::test_all_ten_actual_counted_cases_summary_and_duplicate tests/test_synthetic_collection.py::test_cancellation_retains_count_hold_and_interrupted_result tests/test_blinded_review.py::test_full_synthetic_packet_import_report_demo -q -m integration --basetemp=.cache/f5-d1/evaluation-repeat
```

Ten distinct public cases use actual counted replay and SQL ledgers: nine 2-count /
2-generation /4-operation cases and one 3/3/6 repair case. Intermediate rejection
remains a hard failure despite its final valid plan. The summary retains 21,000
synthetic micro-unit holds and unknown actual charge; this is not real billing.
Cancellation retains an interrupted result and a 1,000-unit count hold, not zero.
The E10 test builds a deterministic blinded practice packet, imports two scripted
dummy ratings and one abstention, recognizes an exact duplicate and rejects
conflicting/provenance changes,
and reports nine eligible pairs, missing/ineligible slots and **zero genuine
judgments with null genuine quality**. Dummy arithmetic is not model quality.

Fresh bounded numerical summaries are written exclusively under ignored
`.cache/f3-e9-implementation/evidence/` and `.cache/f3-e10/evidence/`, one random
schema-named file per demonstration. SQL schemas are dropped after assertions;
runtime receipt/claim fences are retained in ignored storage. Do not delete or
reuse claims to retry, copy raw reviewer packets into shared archives, or open any
private/genuine population. The public F5-D1 evidence contains only reviewed
numerical projections. Existing E10 handoff documents packet APIs and limitations.

Stop PostgreSQL after all native tests finish with `docker compose stop --timeout
30 postgres`; preserve its volume. Never stop it underneath another test run.

## Current-source release, restore and fault drill

For the full automated container exercise, build both local tags with the same
reviewed business source and different release labels. This demonstrates compatible
image switching, not schema downgrade or rollback between historical releases.
Stop the test PostgreSQL first and ensure neither application is already running.

```powershell
docker build --network none --pull=false --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f5-d1 -t fata-release:f5-d1 .
if ($LASTEXITCODE -ne 0) { throw 'Current image build failed' }
docker build --network none --pull=false --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f5-d1-baseline -t fata-release:f5-d1-baseline .
if ($LASTEXITCODE -ne 0) { throw 'Comparison image build failed' }
docker compose stop --timeout 30 postgres
if ($LASTEXITCODE -ne 0) { throw 'Stop owned test PostgreSQL first' }
$env:FATA_RELEASE_IMAGE = 'fata-release:f5-d1'
$env:FATA_RELEASE_BASELINE_IMAGE = 'fata-release:f5-d1-baseline'
.venv/Scripts/python.exe scripts/check_release.py
if ($LASTEXITCODE -ne 0) { throw 'Inspect retained owned project and evidence; do not prune' }
Remove-Item Env:FATA_RELEASE_IMAGE,Env:FATA_RELEASE_BASELINE_IMAGE -ErrorAction SilentlyContinue
```

The existing drill waits boundedly for exclusive ports 8000/55432 without address
reuse or killing listeners. It uses uniquely named source/restore projects, fixed
local fake configuration and `--pull never`. It measures 120 synthetic generations
after warm-up, terminates only a known owned PostgreSQL backend, stops the app
while its request is blocked, tests DB readiness loss/recovery, kills/restarts its
app, backs up while quiesced, restores into a separate empty owned database and
checks immutable snapshots, same-key approval/completion recovery and owner
isolation. A modified-migration fixture must refuse startup. The entrypoint never
silently repairs a checksum mismatch.

The release scenario contains one session record; the browser scenario contains
two. Their counts must not be conflated. The existing drill prints a local report
and retains backup, synthetic private-state and evidence under
`.cache/f4-01/<run-token>/`. Only bounded numerical projections are public. Its
`finally` stops/removes its own containers; both synthetic volumes remain. On an
interrupted drill, inspect its recorded project names and stop only those projects;
do not run global cleanup or delete a volume to hide an uncertain result.
Backup restore is an application/database recovery point, not an automatic schema
rollback. Timed dump/restore excludes provisioning, startup and operator time.
