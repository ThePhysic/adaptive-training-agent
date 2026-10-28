# F3-E3A — Independent-review handoff

2026-10-27. **Offline readiness preparation only.** No freeze ratification,
curator appointment, genuine case/key/commitment creation, registration, opening,
model/human scoring, external request, account access, installation or source change.
No private identity/case/capture/credential/cache material inspected. No executor,
monetary authority, commit or push. Historical evidence and NO-GO decisions remain.

## Findings for owner and independent reviewer

The accepted E2 candidate matches all99 current frozen files and reproduces
exactly. Scorer/rubric versions match. This is a **technical PASS, not approval**.
Recommend **DEFER final real-study freeze/curation**, because:

1. Current `Case`/`score()` strictly means developer-authored/exposed; a truthful
   independent-case envelope and opening/canonicalization contract remain undefined.
2. Ten development IDs and exact study variant/selection settings are not bound
   in the candidate's count-only selection. A future study artifact must actually
   enter the reviewed freeze input set. New experimental files outside the current
   selected paths are not automatically covered; final dependency-scope review is
   required in addition to hash equality.
3. Fixed-input counted-probe evidence is not yet a general sealed-study collection
   interface; do not infer that E1 authorized arbitrary inputs or live study execution.
4. Known later provider/source/model configuration decisions would invalidate
   the current source fingerprint. Provider terms/live gates remain separate blockers.
5. No independent curator, custody/key recovery, genuine attestation or owner pins
   were verified. Metadata equality cannot substitute for those human responsibilities.

Ten-case coverage is internally consistent as aggregate coverage of eight rows,
all presets/schedules and feasible exclusion categories, not a24-cell cross-product.
The owner's exact coverage interpretation must precede curation. No case is selected
or created here. This does not reopen accepted E2 implementation scope.

## New documentation only

| File | Deliverables |
| --- | --- |
| [Readiness assessment](f3-e3a-freeze-readiness-assessment.md) | Public facts, compatibility/coverage gaps, sequencing, owner decision matrix and adversarial stop conditions |
| [Owner and curator procedure](f3-e3a-owner-and-curator-procedure.md) | Distinct approval gates, exact read-only public check, plain-language curator brief, two custody options, attestations and independent-verification boundaries |
| This handoff | Evidence, preservation, validation, review package and next proposed task |

No existing public file is modified/deleted. Start519 files/191 Python; end522/191.
The raw candidate SHA-256 remains
`ecaeb2db0cb4a309b9b20d3a7c63f203e09351b49848ef9677cb379e49530dfa`;
configuration fingerprint remains
`59c62dba4099cbfcb24e84b213e3dc05d34fca4b3d75d62a3608a4cda025cea4`.
All accepted E1/E2 assets/source/reports are byte-identical to task start. E3A
documents do not replace/ratify the candidate or silently change its input scope.
Existing dirty Git diffs are preserved; AGENTS.md remains ignored and untouched.

## Fresh local validation

Existing locked Windows Python3.14.9/Ruff0.17.2. No Docker/database/browser/service
startup or dependency installation. Fixed known public data only; new test artifacts
are labelled synthetic non-case metadata, not genuine population registration.

```powershell
New-Item -ItemType Directory -Path .cache/f3-e3a -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e3a/before.json
.venv/Scripts/python.exe -m pytest tests/test_sealed_evaluation.py tests/test_review_source.py tests/test_model_evaluation.py -q --basetemp=.cache/f3-e3a/pytest-readiness --tb=short > .cache/f3-e3a/readiness-tests.txt 2>&1
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
```

Normal local temp-directory access was used for pytest because the Windows sandbox
had rejected its temp directories in the accepted E2 task. No OS security or account
permission change. All listed commands exited0.

| Check | Observed result, not historical reuse |
| --- | --- |
| Selected tests | **160 passed,107.40s**, no skips/errors/warnings:54 sealed synthetic+18 archive+88 common evaluation tests |
| Candidate | `freeze()` twice, canonical equality and `check_freeze` succeeded; no candidate write, approval or registration;99 matching file hashes and47 known normalized public input identities |
| Frozen baseline | **40/40**,24 development/16 historical held_out; no failures |
| Public model suite | **50 unchanged**,40 development/10 exposed comparison; **150/150 expected handling dispositions**; template hard50, fake/replay hard44 each;12 intended hard failures retained |
| API/TS contracts | Check passed, no drift |
| Source grammar | **191 public Python files**, native and Python3.13 AST checks pass |
| Ruff | Lint passed;194 files already formatted |
| Documents / source integrity | Relative links, UTF8/JSON and fences checked; original519 public file hashes unchanged, three new Markdown files only; candidate still valid after additions |

The candidate-check result is retained in ignored `.cache/f3-e3a/freeze-check.json`;
it contains public fingerprint/status only. The exact reproducible read-only Python
check is in the [procedure](f3-e3a-owner-and-curator-procedure.md); it prints
`owner_approved_by_this_check:false`. Task check also compared candidate bytes
before/after and retained the source map/count/selection result. No genuine metadata
or secrets are generated/read by it.

E2's566 selected checks and E1's native SQL/TLS results remain **historical**; this
task freshly ran only the160-test selection above. No full routine, native PostgreSQL,
frontend/build/browser, real transport or OS custody validation is claimed. Source,
tests, dependencies, routes, persistence and UI did not change. The software results
prove neither model quality, human usefulness, provider terms nor genuine blindness.

## Next proposed owner action and Codex scope

Owner should review the decision matrix and **retain DEFER** unless the OPEN
decisions have separately been resolved. Decide whether a real study remains the
goal and whether independent human custody is available. This is not a request
to authorize AWS/provider calls or inspect/upload private material.

Suggested next separately authorized offline milestone: **independent-case contract
and common-scorer bridge readiness**. Define truthful versioned case provenance,
canonical commitment/opening requirements and exact public development-selection
artifact; test a minimal reusable scorer seam with non-final synthetic evidence.
Review any source/manifest boundary change explicitly, retain historical artifacts
and source fingerprints rather than rewriting snapshots, and keep content opening/
provider execution disabled. No implementation is authorized by this suggestion.

Final freeze then requires a stable reviewed study/model release and exact bound
inputs; curator acknowledgement/custody, actual independent curation, genuine
registration and opening each need later explicit human decisions. Model pricing/
retention, financial/source release and execution approvals remain separate; all
live allowances remain zero. No person, key, attestation or populated decision
record is supplied here.

## Sanitized review package

```powershell
New-Item -ItemType Directory -Path .cache/f3-e3a/review -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e3a/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e3a/review/source-manifest.json --archive .cache/f3-e3a/review/future-training-f3-e3a-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e3a/review/source-manifest.json --archive .cache/f3-e3a/review/future-training-f3-e3a-review.zip
```

Public source snapshot:522 source members plus embedded SHA-256 manifest,191 Python
files. Packager verifies every member against working-tree bytes; a separate
zipfile/hashlib audit verifies membership, raw hashes, all99 unchanged freeze inputs,
no changes/deletions to initial sources, and the three documentation additions.
Verification JSON/ZIP SHA-256 stay beside the ignored archive. This machine check
is not independent human approval.

Exclude AGENTS.md, credentials/identities/login caches, state/plans, dependencies,
ignored test registries, private reviewer/key/metadata paths and sealed contents.
Public synthetic source fixtures remain labelled and unchanged; any common-secret
pattern hit in an existing synthetic fixture must be classified rather than
misreported as genuine credentials. No private directory is scanned. No final
case, real key, attestation, rating or future private population is packaged.

Stop here for ChatGPT independent review. No subsequent milestone is authorized.
