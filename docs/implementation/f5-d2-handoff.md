# F5-D2 portfolio preparation and final audit handoff

2026-10-27. Prepared for independent review. No publication, account/API operation,
model request, spending, genuine evaluation/custody, installation, commit, push or
hosted CI execution occurred. Existing denials and historical outcomes are unchanged.

## Outcome and deliverables

The [README](../../README.md) now explains the product, explicit approval boundary,
stack, demonstration, tests and limitations without a milestone chronology. See:

- [Architecture](../architecture.md): native Mermaid diagram and concrete design
  decisions, with application and experiments separated.
- [Four-minute storyboard](../portfolio-walkthrough.md): a real recording guide,
  existing screenshots and capture/privacy checklist; no video fabricated.
- [Evidence map](../engineering-evidence.md): claim → actual artifact/test → evidence
  type. Historical D1 execution is explicitly distinguished from fresh D2 checks.
- [Engineering history](../engineering-history.md): an index, not rewritten history.
- [Readiness and CI](../portfolio-readiness.md): ready/blocked/deferred/optional matrix,
  measured budget correction and the exact proposed hosted authorization boundary.
- [Publication safety](f5-d2-publication-safety.md): bounded scan, nine export
  exclusions and owner decisions. Full-tree/full-history publication remains blocked.

The shortest release path is now a privacy/license/source-scope decision, selected
hosted validation and recording review—not another infrastructure milestone.
Provider support Case 18223129, monetary authority and genuine study interfaces,
freeze, human-only curation and reviewer collection remain independent deferred gates.

## Scope audit and changes

Five existing files changed: `README.md`, living `docs/development.md` and
`docs/runbook.md` navigation notices, `.github/workflows/offline.yml` and
`tests/test_browser_runner.py`. New files are the six portfolio/architecture/history/
safety documents linked above, this handoff, and
`evidence/f5-d2-validation.json`. All application, migration, dependency, scorer,
provider, ledger, E9/E10 and genuine-opening code is unchanged. No historical
implementation report, old freeze, data/evaluation snapshot or screenshot changed.
AGENTS.md is untouched/ignored. No files are staged. Other accepted dirty/untracked
changes were preserved against the 585-file task-entry source snapshot.

Presentation findings: root README was a chronology; living setup pages had old
review-status labels; the old F0 architecture is a dated proposal, not the current
runtime; legacy admission output and held-out terminology need historical context;
the CI job/step limits did not contain measured supported local runtimes. These
were addressed with navigation, current architecture and explicit evidence labels,
without reinterpreting old NO-GO decisions or changing normative contracts.

## Fresh validation

PowerShell commands actually executed from the repository root:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_browser_runner.py tests/test_check_runner.py tests/test_release.py tests/test_review_source.py tests/test_provider_hardening.py tests/test_probe_authority.py tests/test_model_evaluation.py tests/test_blinded_review.py -q --basetemp=.cache/f5-d2/focused --junitxml=.cache/f5-d2/focused.xml
# 205 passed, 23 deselected, 10.97s; includes the new YAML/budget regression
.venv/Scripts/python.exe -m pytest tests/test_approval_http.py tests/test_stream_publication.py -q --basetemp=.cache/f5-d2/approval --junitxml=.cache/f5-d2/approval.xml
# 11 passed, 10 deselected, 1.71s; terminal-publication checks, native approval HTTP deselected

npm.cmd --prefix web run check
npm.cmd --prefix web run check:generated
npm.cmd --prefix web run format:check
npm.cmd --prefix web test
# 131 passed; zero failures/skips/cancellations
npm.cmd --prefix web run build

.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/prepare_responses.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check

docker image inspect fata-release:f5-d1 fata-release:f5-d1-baseline --format '{{.RepoTags}} {{.Id}}'
```

Fresh total: **216 distinct selected Python tests**, no selected skips/failures,
plus **131 frontend tests**. Deselections are not passes. Native SQL, real installed
Chrome, restore/load measurements and full routine suite were not rerun: runtime,
schema, scoring and dependencies are unchanged. D1's 2598 distinct tests and actual
local demonstration remain historical accepted evidence. No native AWS CLI/account
or provider request was invoked. The focused ownership tests launch only synthetic
owned processes/loopback fixtures. No dependency or YAML tool was installed.

Baseline check: **40/40**, 24 development/16 historical held-out software cases.
Comparison check: **150/150 expected dispositions**, hard passes 50/44/44 for
template/fake/replay. No frozen regeneration. All source grammar checks pass native
and 3.13 for 202 public Python files; Ruff reports 205 formatted files in its
configured traversal. OpenAPI/types/validators, TypeScript and frontend build pass.

Workflow YAML was parsed by the already locked installed `js-yaml` transitively
used by frontend tooling, inside the new regression. No standalone actionlint or
Mermaid renderer was installed; action-runtime expressions/scheduling and rendered
Mermaid layout are not claimed validated by that parse. Mermaid structure was
reviewed as repository-native text. Local Markdown targets/anchors are checked
separately; current documentation and image bytes are source-manifest-bound.

## CI correction and remaining verification

The job is now bounded at 75m; routine step 45m, non-browser integration 15m and
browser still 3m. This is a derived envelope: routine suite's existing 40m bound
plus 5m checks/build, 15m native, 3m browser and 12m other work. F5-D1's Windows
measurements were 1321.56s/411.59s; they do not prove Ubuntu timings. No coverage,
failure propagation, pinned action, repository permission, artifact guard, browser
isolation or retained-volume cleanup was removed. No parallelization introduced.

The new structural regression checks parsed budgets, push/PR/dispatch triggers,
read-only contents permission, fake/no-export environment and absence of a matrix.
Existing negative tests still reject missing installation, skipped/failed browser
populations and unexpected protocol output. Actual hosted verification remains a
blocker. The next owner approval must specify source/ref, destination/visibility,
CI minutes/acquisition, one push-triggered **or** dispatched workflow (not both),
and required all-phase/no-skip/restore evidence. Do not upload the dirty tree or
private history to obtain a green badge. No CI run was triggered here.

## Image/source and privacy verification

Read-only inspection found cached current image IDs matching D1:
`sha256:43afb3417a132b25fd0b905c184881d4e25d46aa73b9407acde6aa0f7aaa46fa`
and comparison
`sha256:28aa80243679e7815f4094cf4cdcf91b55fb847828ca8e2ad56158b29aa4299e`.
Their 75-file source attestation is D1 evidence; D2 additionally verifies current
runtime/migration/asset source has not drifted. No image/container was run, built,
pulled or retagged; no service, data or volume changed. Build reproducibility is
locked/cached local evidence, not a new air-gapped/fresh-install proof.

Pattern scanning was limited to the public inventory. Zero recognizable AWS key
or private-key blocks, nine historical home-path files withheld, synthetic ARN
fixtures and test/negative-URL email matches classified; all 58 PNGs lacked text/
EXIF chunks. Pixel content across all historical images and all Git history are
not comprehensively cleared. Staged diff and forbidden tracked-path counts were
zero. No private record was opened to compare account identities. Findings are
locations/classes, not reproduced path/user/credential values.

An initial check for an installed package named `yaml` failed; available locked
`js-yaml` was used instead. Initial link checking found one wrong baseline README
target, corrected to `data/evaluation/README.md`; references to this not-yet-created
handoff were then resolved. These were preparation issues, not application defects.

## Review package

The archive is `.cache/f5-d2/review/future-training-f5-d2-review.zip`. It deliberately
omits the nine public historical files listed in the safety report, in addition
to all standard ignored/private/cache/credential/state/genuine-material exclusions.
Their repository bytes are preserved. Its embedded `_review/source-manifest.json`
uses **scoped-source-review-v1**, listing included raw SHA-256 hashes and explicit
omissions. It is not the default full-inventory archive, a full Git export or a
publication-approved tree. Some historical links to omitted records are therefore
unavailable within the ZIP; primary portfolio navigation is included.

Independent standard-library ZIP verification checks the exact member set, no
duplicates, every included byte/hash against the working tree, exclusion rules and
the absence of the identified path/key patterns in included text. Adjacent archive
SHA-256 and verification JSON record actual results. No manifest/scan proves absence
of all possible sensitive content or grants licensing/publication consent.

## Stop and next decisions

Final source scope: five existing files modified, eight added, 580 task-entry
files unchanged; 593 public files before the nine-file review omission. The ZIP
contains 584 source/evidence files plus its embedded manifest, including all 202
public Python files. Documentation checks resolved 644 relative local targets
across the public Markdown inventory and four portfolio fragment links; eight
portfolio documents have balanced code fences. These checks do not render Mermaid
or clear the excluded historical records for publication.

Release remains NO-GO for public distribution until the owner resolves historical
path/history scope, source/license/notices, final image/recording review and exact
staged source. Hosted verification needs separate commit/push/CI authorization.
No existing claim or freeze is reset to simplify release. Provider/AWS/monetary/
genuine/hosted-export barriers remain unchanged. No further infrastructure milestone
is required for the honestly labelled offline portfolio slice. Stop for review.
