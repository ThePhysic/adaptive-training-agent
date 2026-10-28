# F5-D5 clean-checkout validation handoff

The scoped candidate fixes pass fresh local validation. This remains a private
review candidate, **not approved for public distribution**. Root licensing,
third-party clearance and hosted CI remain unresolved. No remote is configured.
The source directory basename is `future-training-portfolio-rc-f5-d3-source`.
The original development repository's public bytes and Git status match preflight.

## Scope and corrections

Base revision: `55fe6d0d1f251e95b7cb191f3d3f2ad879b874ed`. One additional local commit is authorized after this
report's reviewed inventory is staged. The final commit ID, complete committed-file
inventory and archive hash are post-commit metadata in the sibling D5 review area
and embedded review manifest; they cannot be self-referenced by this commit.

- E4 tests now own an exclusive UUID scratch leaf and create its missing parents.
- E1 tests use the same test-owned pattern for captured synthetic evidence.
- Production retain/persist code is unchanged. Existing exclusive-write,
  partial-write/fsync failure, cancellation, uncertain-liability, duplicate and
  first-result assertions remain active. No claim or prior artifact is reset.
- Browser screenshots always use `.cache/browser-evidence/<UUID>/` beneath the
  test root. UUID, fixed parents, real paths and links are checked; the run leaf
  and screenshot files use exclusive creation. There is no output-path argument
  or environment override. The existing finite stage selector only names files.
  The stdout protocol retains its fields and reports relative screenshot paths.
- Chrome sandbox, loopback interception, workflow assertions, lifecycle ownership
  and all startup/workflow/cleanup deadlines remain unchanged.
- New tests cover missing parents, exclusive scratch isolation, retained markers,
  duplicate evidence IDs/files, unsafe IDs, linked cache parents and preservation
  of dummy historical screenshots. Type declarations cover the helper.

Changed existing files (and no other existing files):

- `tests/test_counted_probe_evidence.py`
- `tests/test_independent_cases.py`
- `web/scripts/browser-smoke.mjs`
- `web/scripts/browser-support.d.mts`
- `web/scripts/browser-support.mjs`
- `web/tests/browser-support.test.ts`

Six additive release records: this handoff, validation JSON, unapproved current
freeze, public download receipts and the two source-manifest controls.
Historical D3/D4 reports/manifests remain historical, without rewritten outcomes.

## Fresh evidence

| Check | Result |
| --- | --- |
| Full routine Python, detached validation worktree | 2198/2198 passed; no failures/errors/skips |
| Full native PostgreSQL, candidate including installed Chrome | 403/403 passed; no failures/errors/skips |
| Second empty-checkout E4 + E1 combined | 130/130 passed; both scratch parents absent before execution |
| Frontend | 138/138 passed; TypeScript, generated types/validators, Prettier and fresh production build pass |
| Frozen software baseline | 40/40 preserved |
| Comparison dispositions | 150/150 preserved; intentional hard failures remain hard failures |
| Grammar / Ruff | 202 Python files parse natively and as 3.13; lint passes; 204 format inputs unchanged |
| Contracts / source | export, Responses, token-admission and model-evaluation --check gates pass |
| Documentation | 637 existing local Markdown links resolve; added release links checked separately |
| Images / historical evidence | 58 tracked PNGs remain byte-identical; no PNG text/EXIF chunks |
| Container recovery drill | passed from candidate; cached matching runtime images, no new image build |

The full Python populations are disjoint (2601 distinct tests).
The 130 focused tests and other repeats overlap them and are not additional unique
passes. Baseline/comparison numbers are case dispositions, not model-quality scores.
All results above were executed in D5; D1/D2/D4 results are historical context only.

Python 3.14.9, ruff 0.17.2, Node
v24.22.1, npm 11.19.1, installed Windows
Chrome 156.0.8078.48; Docker Linux PostgreSQL uses the existing
pinned 18.6 digest. Existing installed Python dependencies were reused, not freshly
installed. The main candidate and detached checkouts use their own source; no
original `node_modules`, dist or database was substituted.

The detached worktrees are under ignored `.cache/f5-d5/`. They start from the
approved initial commit with the exact six reviewed modifications overlaid; their
actual old HEAD plus dirty state is retained, not mislabelled as a new commit.
The full routine run followed focused checks in its worktree; it is not claimed as
a cache-empty full-suite run. The separate second checkout supplies that missing-parent
proof for both affected modules. It starts without `.cache`; pytest temp files go to an external retained
test area, so no manual E1/E4 directory preparation masks the defect. Both modules
pass together. No test relies on another test's artifacts; fixtures own UUID leaves.

The first focused command deliberately retained 76 passes and two pytest setup
errors: `--basetemp` itself had an absent parent. This harness issue was corrected
by using the external existing review parent, without changing app semantics.
The preliminary TypeScript check caught the missing declaration for the new helper;
that declaration was added and all final frontend checks pass. Neither initial
failure is hidden or counted as a passing run. Logs/XML stay in local review storage.

## Exact validation commands

`python` and `ruff` below denote the already installed pinned tools. The actual argv,
exit codes and timings are recorded in [validation](f5-d5-validation.json); external
paths there are represented as `<review>`/`<candidate>` to avoid host disclosure.
Raw local logs preserve original command paths but are excluded from the archive.
All test processes suppress bytecode, select fake providers/no export, remove live
credential environment inheritance, and leave FATA_WRITE_EVIDENCE unset.

```powershell
# Empty detached checkout; executed through Python subprocess argv (empty -m selects both populations).
python -B -m pytest -q -m "" tests/test_independent_cases.py tests/test_counted_probe_evidence.py --basetemp=<review>/pytest-cold-confirmation --junitxml=<review>/cold-confirmation.xml
# Full routine suite in the first detached checkout:
python -B -m pytest -q --basetemp=.cache/pytest-d5-routine --junitxml=<review>/routine.xml
# Full candidate native suite; FATA_BROWSER_EXECUTABLE selects the installed Chrome,
# FATA_BROWSER_EVIDENCE_STAGE=f5-d5; only a new disposable DB is running:
python -B -m pytest -q -s -m integration --basetemp=.cache/pytest-d5-native --junitxml=<review>/native.xml
npm.cmd --prefix web run check
npm.cmd --prefix web run check:generated
npm.cmd --prefix web run format:check
npm.cmd --prefix web test
npm.cmd --prefix web run build
ruff check src scripts tests experiments infra --no-cache
ruff format --check src scripts tests experiments infra --no-cache
python -B scripts/export_contracts.py --check
python -B scripts/prepare_responses.py --check
python -B scripts/measure_token_admission.py --check
python -B scripts/prepare_model_evaluation.py --check
python -B scripts/evaluate_models.py --check
python -B scripts/evaluate_baseline.py --check
python -B scripts/review_source.py check
python -B scripts/smoke_local.py
# After stopping only the D5 disposable DB; both cached images first compared to current runtime files:
$env:FATA_RELEASE_IMAGE='fata-release:f5-d1'
$env:FATA_RELEASE_BASELINE_IMAGE='fata-release:f5-d1-baseline'
python -B scripts/check_release.py
```

The browser exercised Save, streamed generation, revision, lost approval and
completion responses with same-key recovery, immutable owned history after refresh,
owner isolation and mobile error recovery. Health/readiness were 200/200, runtime
errors zero, external page requests zero; three new screenshots are ignored.
The separate container drill exercised restart, locked dependency recovery, binary
backup/restore, same-schema rollback/forward verification and checksum refusal.
It used cached D1 images only after all 75 runtime files (including freshly built
frontend assets) matched this candidate. This is not a new D5 image build claim.
All D5 service containers are stopped; disposable volumes/backups are retained.
No existing app database or historical volume was reused or erased.

## Dependency acquisition

Exactly 24 approved registry tarballs (6,179,845 bytes) were fetched once,
using bounded certificate-verified HTTPS, no proxy/auth inheritance and no redirects.
Every URL/version/SHA-512 SRI matched the unchanged lockfile. Download acceptance
and cache ingestion both checked integrity. The previously verified 60 cached
platform-applicable artifacts plus these 24 supported `npm ci --offline` in the
candidate and the detached checkout. Neither install allowed lifecycle scripts,
audit/fund/update requests or additional downloads. No versions or locks changed.
[Public receipts](f5-d5-download-receipts.json) enumerate every approved artifact.

```powershell
npm.cmd ci --offline --ignore-scripts --no-audit --no-fund --update-notifier=false --logs-max=0 --cache <review>/npm-cache --userconfig <review>/empty-user.npmrc --globalconfig <review>/empty-global.npmrc
```

Both fresh builds had identical 14 source/build inputs and three output assets.
No assets from a historical image were used to claim a build. Artifacts, dependency
caches, installed node_modules and generated dist are not included in source review.

## Source / freeze / publication safety

The existing source/freeze/evaluation functions pass and current freeze generation
reproduces twice. The existing 121-input v5 fingerprint changes only because
`tests/test_independent_cases.py` and `tests/test_counted_probe_evidence.py` changed.
The historical E10 candidate remains untouched and correctly does not describe
these new bytes. The [additive current candidate](f5-d5-freeze-candidate.json) has
fingerprint `1e5c64c50596443e7235779039612fa8cac1615c80a8b3fbc793edf938e6331a` and remains
`candidate_not_owner_approved`; live and monetary flags remain false.
No obsolete fingerprint or surrogate revision is used to bypass source checks.
Original hard-rule implementation, datasets, manifests, historical results,
permissions, approval/financial/genuine-case denials and locks are unchanged.

The source manifest binds raw file bytes, excluding its explicitly named two
self-referential controls. The post-commit review manifest binds every committed
source file, including those controls, plus the exact revision/tree identifiers.
Staging uses only the twelve listed existing/new paths; all staged/committed raw
bytes are compared with their Git blobs. Archives omit .git, caches, node_modules,
state, credentials, private records, AGENTS.md and all nine historical exclusions.
Every original committed file other than the six reviewed edits remains unchanged.
Pattern and PNG metadata checks found no indicated exposure; these checks do not
prove exhaustive secret, legal or visible-pixel clearance. Filesystem link checks
are local test safeguards, not OS-enforced containment against a hostile mutator.

## Remaining decisions and verification

| Area | Assessment |
| --- | --- |
| Local supported offline functionality | Fresh candidate routine/native/browser/frontend/build/recovery checks pass |
| Known candidate functional defects | No remaining blocker found in the executed supported checks |
| Clean machine reproducibility | Scratch-cold checkouts and two offline frontend installs/builds pass; Python deps reused |
| Hosted CI | Unexecuted for this curated revision; existing Ubuntu workflow remains unverified here |
| Licensing / distribution | Root license undecided; complete dependency/native/image notices, ownership and screenshot review remain owner gates |
| Real-model / human evidence | Absent; provider support, monetary/privacy authority, final freeze and genuine custody/study remain NO-GO |
| AWS / hosted observability | Optional; not accessed or activated |

No separate Langfuse SDK environment or Terraform suite was run: unaffected and
outside these frontend/test-only corrections. No new Linux full test suite or
container image build is asserted. Cached Linux runtime/recovery evidence does not
replace hosted full-source verification.

After independent review, the next infrastructure operation would require separate
owner approval: private GitHub repository creation, reviewed remote setup/push of
the two-commit curated history and one hosted workflow run. None occurred here.
The unchanged workflow budgets 45m routine, 15m native, 3m mandatory browser and
75m job total; its timing on hosted Ubuntu still needs real evidence. Keep the repo
private; public visibility additionally requires explicit rights/license/screenshot
clearance and a final publication decision. No license is selected by this handoff.
No further milestone, provider request, spending or genuine evaluation is approved.
