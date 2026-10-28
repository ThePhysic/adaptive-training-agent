# F5-D1 implementation/review handoff

2026-10-27. Offline synthetic engineering only. Stop for independent review.
No AWS/provider account operation, genuine case/curator/judgment, monetary
authority, hosted export, final freeze approval, installation, commit or push.

## Deliverables and exact changes

Use the [demonstration runbook](../local-demonstration.md) and
[readiness assessment](f5-d1-report.md). The task-entry snapshot contained 573
public files, including accepted dirty/untracked work. Only these existing files
changed during F5-D1:

- `README.md`: current demonstration/evidence links, preserving older status text.
- `docs/runbook.md`: correct aggregate test-runner allowances; historical handoffs
  are untouched.
- `scripts/check_release.py`: existing Compose image override plus separate
  comparison-image override; original defaults and all port/retention safeguards
  remain. No new command interface, resource type or transport.
- `scripts/check.py`: finite aggregate routine/native allowances 2400/900 seconds;
  ordinary checks stay 180 seconds. Application/request/SQL/browser budgets stay
  unchanged. Existing nonzero fail-fast behavior is preserved.
- `tests/test_release.py`: one new regression for explicit local image selection,
  including propagation of `--pull never`.
- `tests/test_browser_ui.py`: owned-schema readiness/migration history, positive
  health/readiness assertions, bounded structural database outcome report.
- `web/scripts/browser-smoke.mjs`: finite `f5-d1` screenshot prefix and actual full
  page reload/history/session readback assertions; approval remains disabled.
- `web/scripts/browser-support.mjs`: two finite refresh diagnostic stage names.

Additions are the new `tests/test_check_runner.py` (two mocked process-failure
regressions), `docs/local-demonstration.md`, the F5-D1 report/handoff, three F5-D1
screenshots, and these five public JSON artifacts under implementation/evidence:

- `f5-d1-application.json`: bounded projection of two observed installed-Chrome
  process reports. It is not an independently human-reviewed result.
- `f5-d1-local-release.json`: current-source Docker/SQL/fault/restore/performance
  projection. Backup hashes, private state, project/container names are omitted.
- `f5-d1-evaluation-walkthrough.json`: fresh E9/E10 numerical summaries, not copied
  historical outcomes promoted to newly executed evidence.
- `f5-d1-failure-trace.json`: fresh content-free induced failure from the existing
  `test_induced_failure_is_correlated_without_content` assertion.
- `f5-d1-validation.json`: final fresh check denominators and limitations.

No existing application source, migration, lockfile, evaluator, hard-rule body,
financial/provider gate, first-result contract, genuine opener or historical
record changed. AGENTS.md remains ignored and untouched. A task-only source diff
against the previously verified E10 ZIP is retained at
`.cache/f5-d1/task-source.diff`; ordinary Git diff also includes earlier accepted
unrelated work and must not be attributed wholly to F5-D1.

## Fresh validation commands

PowerShell, repository root. No acquisition commands or credentials were used.
Python 3.14.9, Node 24.22.1, Chrome 156.0.8078.48, Ruff 0.17.2; Windows AMD64
with Docker Linux engine 29.9.1 and pinned PostgreSQL 18.6.

```powershell
docker compose up -d --pull never --wait postgres
npm.cmd --prefix web run check
npm.cmd --prefix web run check:generated
npm.cmd --prefix web run format:check
npm.cmd --prefix web test
npm.cmd --prefix web run build

.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/f5-d1/unit --junitxml=.cache/f5-d1/unit.xml
.venv/Scripts/python.exe -m pytest -q -m integration --ignore=tests/test_browser_ui.py --basetemp=.cache/f5-d1/integration --junitxml=.cache/f5-d1/integration.xml
.venv/Scripts/python.exe -m pytest tests/test_release.py -q --basetemp=.cache/f5-d1/release-unit --junitxml=.cache/f5-d1/release-unit.xml
.venv/Scripts/python.exe -m pytest tests/test_check_runner.py -q --basetemp=.cache/f5-d1/check-runner --junitxml=.cache/f5-d1/check-runner.xml

$env:FATA_BROWSER_EXECUTABLE = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE = 'f5-d1'
.venv/Scripts/python.exe -m pytest tests/test_browser_ui.py -q -s -m integration --basetemp=.cache/f5-d1/browser-final --junitxml=.cache/f5-d1/browser-final.xml
# After the release drill, fresh Chrome and disposable SQL schema:
.venv/Scripts/python.exe -m pytest tests/test_browser_ui.py -q -s -m integration --basetemp=.cache/f5-d1/browser-repeat --junitxml=.cache/f5-d1/browser-repeat.xml -o junit_logging=all

.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/prepare_responses.py --check
.venv/Scripts/python.exe scripts/measure_token_admission.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
```

| Final invocation | Passed | Deselected | Runtime |
| --- | --- | --- | --- |
| Full routine population collected at task start |2193 |402 |1321.56s |
| All non-browser integrations |401 |2193 |411.59s |
| Release unit file (includes one new case) |11 |0 |3.98s |
| New aggregate-runner failure tests |2 |0 |0.22s |
| Expanded installed-Chrome workflow |1 |0 |4.34s |
| Second fresh Chrome/disposable-schema run |1 |0 |4.65s |

That is **2598 distinct selected Python tests /2609 passing executions**, with no
selected skip/error/failure in the final runs. Eleven executions overlap (ten old
release tests and the repeated browser case). Three new routine cases were added
after the original routine collection and run separately above. Two browser/argument
development failures are reported below, not counted as final passes. Frontend
131/131 is separate from the Python denominator.

Final exact results are recorded in [validation evidence](evidence/f5-d1-validation.json).
The full integration
selection freshly exercised accepted E9/E10 suites, local TLS, SQL accounting,
approval reconciliation, persistence, completion, source/provenance and live denial
tests. No selected skip is counted as a pass. The original common hard-rule AST
body hash remains
`0e0cc2ad111b41cc780c90cace86a88844a938ad16276ef942db372cc55bfbd9`.
The E10 candidate still reproduces exactly; it remains unapproved. Baseline 40/40
means 24 development/16 historical held-out **software** cases; all 150 comparison
handling dispositions match, with hard passes 50 template /44 fake /44 replay.
No snapshots were regenerated. The old admission-script output describes the
historical F3-03A experiment, not today's ratified 3/3/6 protocol.

Frontend: 131/131, no skipped/cancelled tests, repeated after final harness-stage
changes. Strict TypeScript, generated contracts/validators, formatting and built
assets passed. Build output was approximately 372.3 KiB JS /5.9 KiB CSS (esbuild
display units), not a fresh package acquisition. Full Linux Python/Chrome and
hosted GitHub Actions were not run. Existing CI was inspected, not triggered.

## Actual release drill

Old cached F4 images differed from 16 current source files, so they were not used
as current-source evidence. Both newly tagged images were checked in read-only,
network-disabled containers against all 75 runtime source/migration/catalog/assets
files. The same-schema image pair deliberately differs only in release labeling.

```powershell
docker build --network none --pull=false --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f5-d1 -t fata-release:f5-d1 .
docker build --network none --pull=false --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f5-d1-baseline -t fata-release:f5-d1-baseline .
docker compose stop --timeout 30 postgres
$env:FATA_RELEASE_IMAGE = 'fata-release:f5-d1'
$env:FATA_RELEASE_BASELINE_IMAGE = 'fata-release:f5-d1-baseline'
.venv/Scripts/python.exe scripts/check_release.py
```

All exited zero. BuildKit performed public registry metadata/authentication
resolution; RUN steps used cached locked dependencies with networking disabled.
Do not claim a fully air-gapped rebuild. There was no provider/AWS/telemetry call
or new dependency installation. Original F4 image tags were preserved.

The drill's private synthetic output is `.cache/f4-01/14f345ac/evidence.json`; its
backup/private-state/changed-migration fixture stay ignored. Only the bounded
numerical projection is public. Existing test PostgreSQL was stopped before the
drill; the source/restore projects were stopped and removed by the drill, retaining
both volumes. PostgreSQL was briefly restarted for the second browser exercise,
then stopped again. Its original volume remains. No global prune, volume deletion,
user-data cleanup or default-database migration was performed.

New current image IDs are
`sha256:43afb3417a132b25fd0b905c184881d4e25d46aa73b9407acde6aa0f7aaa46fa`
and comparison
`sha256:28aa80243679e7815f4094cf4cdcf91b55fb847828ca8e2ad56158b29aa4299e`.
The restore/fault/readiness/measurement results and caveats are in the report.
No current-image rollback is claimed to reverse database schema changes.

## Fault and privacy assessment

| Evidence | Observed outcome |
| --- | --- |
| Browser response loss | Exact approval/session-key retry; one committed approval and no duplicated session record |
| Full page refresh / profile change | Durable old snapshot/records recovered; approval stays disabled; no implicit write |
| Interrupted generation / cancelled revision | Existing controlled streaming tests remove incomplete eligibility and drain owned work; no automatic generation replay |
| Concurrent approval / uncertain commit | Existing real SQL tests preserve unique keys/immutable snapshots or quarantine uncertainty; no fresh-key workaround |
| Dependency interruption / process death | Actual owned backend termination, app stop/crash and DB outage fail safely and recover durable readback |
| Replay repair / cancellation | Earlier rejection remains hard failure; 21,000-unit holds and unknown totals retained. Cancelled count retains 1,000-unit liability |
| Dummy reviews | Immutable first-valid import; duplicate/conflict/partial/source drift tests; no dummy contribution to genuine metrics |
| Induced trace failure | Twelve parent-correlated spans; three fake provider calls, one search tool, one repair; final error and no captured content |
| Source/privacy | Existing sink canaries and live/financial/genuine denials freshly exercised; only public synthetic screenshots/numerical evidence exported |

No test demonstrates actual human independence, real account pricing/retention,
provider-selected tools, verified billing, OS-level egress containment or production
authentication. Local loopback/socket/Chrome interception controls are not an OS
sandbox. Public synthetic traces carry only random correlation IDs and approved
bounded metadata. No raw private captures, reasoning, prompts, credentials or real
identifiers were inspected or included.

## Development failures and reconciliation

The first frontend invocation hit sandbox `spawn EPERM` for installed esbuild;
the authorized local process rerun passed. Initial Docker pipe access was similarly
sandbox-blocked, then local Docker inspection/testing succeeded. No OS security
setting or host networking feature was changed.

The first expanded browser iteration completed its UI assertions but was rejected
by the harness because a new proof field was outside its finite report protocol.
That unnecessary field was removed; existing sanitized report shape was preserved,
and two final runs passed. No allowlist or assertion was bypassed. A repeat command
using unsupported `--junit-logging=all` stopped at argument parsing before execution;
the supported `-o junit_logging=all` invocation passed. Since `-s` leaves no captured
JUnit stdout, the public application artifact is explicitly a bounded projection
of observed tool output, not an invented automatically parsed JUnit report.

The induced trace was freshly generated by invoking the existing public failure
test with its synthetic profile and configured in-memory logging sink, without
the historical write-evidence flag. Assertions/canaries passed before exclusive
write of the new F5 file. E9/E10 projections came only from new schema-named
evidence files created after the task-entry snapshot. No historical output or
uncertain AWS attempt was modified or retried.

## Review package and remaining boundary

Create and verify the sanitized working-tree snapshot with the existing
`scripts/review_source.py` snapshot/archive/verify-archive actions. The ZIP lives
at `.cache/f5-d1/review/future-training-f5-d1-review.zip`, contains an embedded
`_review/source-manifest.json`, and is checked again using independent zipfile /
hashlib byte comparison. Reserved private paths, caches, AGENTS.md, credential
files, state/plans and genuine evaluation/reviewer material are excluded before
reading. Only public synthetic evidence is included. The adjacent SHA-256 and
verification JSON bind the actual archive; task-local source diff is separate.

Final inventory: eight existing files modified, twelve additions, 565 task-entry
files unchanged; 585 public source/evidence files, 202 Python files parsing native
and 3.13 grammar, and 205 files in the formatter's configured paths. Source-only
assertions use the public manifest, not the formatter's traversal denominator.

There is no observed blocking production-code defect in the supported offline
journey. Remaining portfolio polish, broader browser/manual usability checks and
fresh hosted CI are not claimed done. Genuine source/trust interfaces, final
configuration/study approval, family-curator custody/human-only cases, real reviewer
allocation/collection, provider support/privacy/count tariff and exact monetary
approval remain separate blockers. Optional AWS/hosted/judge work is off the
critical path. No follow-up milestone or live operation is authorized.

The existing CI native-integration step has its own five-minute limit. This
Windows-to-Docker run measured 412s; that does not establish Ubuntu runner timing.
The expanded population needs a separately authorized hosted verification and,
if measured necessary, a bounded CI aggregate allowance review. This task did not
trigger CI or silently claim the host-side runner change updates that job limit.
