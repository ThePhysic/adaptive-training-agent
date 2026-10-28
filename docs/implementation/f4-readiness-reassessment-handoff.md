# F4 readiness reassessment — Read-only handoff

2026-10-27. **Stop for independent review.** Documentation and public-source review
only. No implementation authorization is requested or exercised by these files.

## Recommendation

1. Preserve accepted F0/F1/F2/local F4 evidence and the offline F3 work. Passing
   software checks is not production, real-model, human or AWS-operated evidence.
2. Defer further AWS discovery unless the owner selects the optional operated-AWS
   track. Do not remove its controls, rescope it as completed or retry the managed
   invocation. IAM is not a dependency of local AI/evaluation/product work.
3. Propose **F3-E1 — Offline Counted-Probe Evidence Rehearsal** next: close the
   demonstrated counted single-probe/common-scorer observation seam using existing
   fixtures, SQL and local TLS. Preserve both source denials and all spending
   restrictions. No new evaluator, generic executor or live activation path.
4. Resolve provider counting terms/prices privately through the owner in parallel;
   prepare independently sealed comparison cases and actual owner usability
   feedback. Real-model study/hosted integration remain separately gated.

Detailed deliverables:

- [Assessment and F0–F4 evidence/status matrix](f4-readiness-and-critical-path-assessment.md):
  original goals, evidence hierarchy, current NO-GOs, AWS dependency analysis,
  provider blockers, critical-path diagram and adversarial review.
- [Prioritized backlog and next milestone specification](f4-remaining-scope-backlog.md):
  essential/deferrable/optional tasks, estimated effort/dependencies, exact proposed
  scope/files/tests and definition of done.
- This handoff: observed checks, file preservation, unresolved decisions and review
  package. Historical/planning/README documents are not edited.

## Facts, interpretation and open decisions

F4 local acceptance is supported by actual container/PG restore, compatible image
switching and 120 fake-generation measurements in F4-01. Original phase 02 calls
AWS optional; actual deployment/recovery/teardown is necessary to claim AWS-operated
experience. Offline Terraform and STS identity do not satisfy that claim.

F3 offline engineering is implemented: count-aware binding/budgets, durable holds,
freeze/reconciliation, strict local transport, evaluation/scoring and socket-sealed
Langfuse. The old admission problem is not a reason to invent another tokenizer:
offline protocol semantics were ratified and implemented. Live equivalence,
endpoint-specific counting tariff/max liability and retention, model/account/rate
verification, positive numerical authority and both source-release approvals
remain unfulfilled. A manual count of 18 proves none of those. All live allowances
remain zero; no current terms/prices were reverified in this task.

The evaluation's 40-case frozen split and 50-case exposed suite are not genuine
held-out model evidence. Zero independent sealed cases or actual human/judge scores
are currently recorded. Explanation clarity stays N/A. The proposed observer
bridge is essential to credible later collection, not a claim of model quality.

The original managed result remains stopped/uncertain; preparation/digest/claim
were owner-reported present and observation/result absent. No historical artifact
was opened. State-user inherited authority and installed boundary remain unknown;
zero user-policy lists do not establish no effective permissions. Group-inline is
prepared, not executed. No new AWS operation or retry is recommended now.

Latest repository review records and owner statements take precedence over stale
proposal/status headers only for their actual scopes. The owner previously reported
R5A hosted CI success; earlier explicit hosted evidence is in readiness 23. The
exact current dirty worktree has not been freshly hosted-verified here. The prior
accepted diagnostic handoff's 512 selected tests are historical evidence, not
tests rerun or a full application denominator for this assessment.

Owner decisions still needed: whether to pursue optional AWS operation at all;
whether provider terms and hosted processing are acceptable; exact later pricing,
sample populations/reuse, numerical ceilings, curator/reviewers and execution
windows; whether eventual completion is broad live evidence or explicitly
offline-only. No permission follows from this prioritization. Proposed next
implementation requires its own authorization but no external access/spending.

## Inspection and exact fresh checks

Starting public snapshot: **499 files, 187 Python files**. Current Git revision:
`212cef8`, with existing accepted tracked/untracked modifications; this is not a
clean commit or deployment claim. The source manifest captures exact dirty bytes.
AGENTS.md was read, remains ignored, and was not modified or added to Git.

Reviewed original charter/phases/evaluation/decision/F1 contracts and F2 outline;
F1/F2 acceptance reports; F3 planning 17–21/provider safety and relevant handoffs;
F4 cost/deployment/readiness/runbook/identity/boundary/inventory/diagnostic reports;
current provider/probe/scorer/recorder/CLI/CI and Terraform source. These are public
repository sources. No private directories or real credential/configuration data
were inspected. Referenced historical logs were not re-read from ignored private
artifacts; bounded checked-in evidence and owner reports remain labelled.

Commands executed from the repository root (existing environment; no installation):

```powershell
git status --short
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-readiness-reassessment/before.json
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
git rev-parse --short HEAD
```

| Fresh validation | Observed result |
| --- | --- |
| Generated OpenAPI/TS contract check | Exit 0, no drift |
| Frozen template evaluation | 24/24 development +16/16 legacy held-out; 40/40, no failed cases |
| Model-evaluation asset check | 50 authored cases; 40 development/10 exposed comparison candidates; no drift |
| Common offline evaluation | 150/150 handling dispositions match; hard passes template 50/50, fake 44/50, replay 44/50; six intentional hard failures per fake/replay retained |
| Quality evidence from these checks | None: no actual model/human/judge rating; 34 quality-eligible normal cases per variant, automatic quality remains null |
| Public source grammar | 187 Python files pass native and Python 3.13 parsing |
| Ruff lint/format | All checks pass; 190 files already formatted |
| Git whitespace | Exit 0 |

Checks used existing no-write `--check` branches after public source inspection.
Template/fake/replay evaluation uses the existing controlled transport; no AWS,
provider, hosted or authentication traffic. No full pytest, PostgreSQL integration,
browser, frontend build, release drill or Terraform operation was executed in this
read-only assessment. Those historical test results are not promoted to fresh
verification. No code/test fixes or snapshot regeneration occurred.

## Files changed and integrity

Only three new documentation files:

1. `docs/implementation/f4-readiness-and-critical-path-assessment.md`
2. `docs/implementation/f4-remaining-scope-backlog.md`
3. `docs/implementation/f4-readiness-reassessment-handoff.md`

Before/after public SHA-256 inventory comparison requires **zero changed or deleted
initial public files** and exactly those additions. This preserves existing code,
tests, historical/planning/acceptance records, source fingerprints, frozen data,
policies and unrelated worktree edits. Git's aggregate pending diff predates this
unit and is not an implementation diff for the reassessment. Nothing was staged.
The local preservation/link audit observed zero changed/deleted initial files,
exactly the three expected additions, and **53 valid local Markdown links** across
the new documents. UTF-8/replacement-character and balanced-fence checks passed.
This audit read public files and the task's own public-hash manifest only.

## Sanitized review package

The existing reviewed packager includes the current public-source working-tree
snapshot, not just HEAD, plus `_review/source-manifest.json`. It excludes AGENTS.md,
credentials/private identities/AWS caches, ignored directories, state/plans,
dependencies and other ZIPs. It verifies every member byte-for-byte against the
current source and performs native/3.13 grammar checks. Additional common credential/
private-key pattern checks inspect public ZIP members only; pattern checks are
not a guarantee about every possible secret encoding.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-readiness-reassessment/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-readiness-reassessment/review/source-manifest.json --archive .cache/f4-readiness-reassessment/review/future-training-f4-readiness-reassessment-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-readiness-reassessment/review/source-manifest.json --archive .cache/f4-readiness-reassessment/review/future-training-f4-readiness-reassessment-review.zip
```

Package and verification metadata are retained only in the ignored task review
directory. Expected final public inventory: 502 files/187 Python files plus the
embedded manifest. The archive SHA-256 is recorded beside it, avoiding a recursive
self-hash in source documents.

**Next action: independent review of this assessment.** If accepted, owner may
separately authorize F3-E1 with its defined offline scope. No next AWS command,
live probe, hosted export, monetary permit, claim reset or infrastructure operation
is authorized or requested. Stop here.
