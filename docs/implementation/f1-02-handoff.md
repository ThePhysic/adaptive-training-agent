# F1-02 handoff — independent domain validation and deterministic baseline

Date: 2026-10-23 (America/Los_Angeles). Authorized scope: **F1-02 only**.
F1-01 was owner-accepted before this work. No F1-03 or subsequent application
functionality was implemented, and no commit or push was performed.

## Result and readiness

F1-02 is complete for review. A bounded original metadata catalog, contract-12
duration arithmetic, independent validator, finite deterministic template planner
and reproducible 40-scenario evaluation are implemented and tested offline.
**Ready for owner review and subsequent F1-03 authorization.** No unresolved
F1-02 test failure remains. Readiness for implementation is not approval to start
the next unit or to enroll participants.

The runnable application still exposes only the accepted foundation endpoints;
`/ready` remains 503. Pure domain functions do not publish candidates, grant user
identity, persist data, call a model, stream responses, or approve plans.

## Files changed

| Area | Files | Purpose |
| --- | --- | --- |
| Catalog | `data/catalog/v1.json`, `data/catalog/README.md` | Twenty original records, provenance, explicit tags, version and content-review limits |
| Domain | `src/future_training/domain/__init__.py`, `catalog.py`, `duration.py`, `validator.py`, `baseline.py` | Read-only catalog access, exact integer arithmetic, independent checks and bounded template search |
| Evaluation | `src/future_training/evaluation.py`, `scripts/evaluate_baseline.py` | Frozen-case loader, exact outcome/issue scoring, coverage and reproducible artifact generation/checking |
| Dataset/artifact | `data/evaluation/v1/scenarios.jsonl`, `manifest.json`, `data/evaluation/results/baseline-v1.json`, `data/evaluation/README.md` | Fixed 24/16 split, checksums and complete per-case synthetic results |
| Tests | `tests/test_domain.py`, `tests/test_evaluation.py` | 155 positive, negative, boundary, mutation, feasibility and reproducibility cases |
| Documentation | `README.md`, `docs/development.md`, this handoff | Current scope, domain interfaces, commands, evidence and limitations |

Names following `domain/__init__.py` in the domain row are under that same
directory; `manifest.json` is under `data/evaluation/v1/`. The F1-01 schemas,
OpenAPI/TypeScript contracts, settings, health API, locks, migrations, approval
supplement/reference model, historical handoff and ratified planning files were
preserved. No dependencies, frameworks, services or migrations were added.
Local-only instructions remain ignored and were not modified.

## Catalog coverage and provenance

Catalog revision: `catalog-v1`. It contains eight bodyweight repetition records,
eight bodyweight timed records and four dumbbell repetition records. All carry
stable IDs, declared goal/mode/equipment/experience compatibility, exclusion tags,
revision, original-content attribution and a local source reference. No
third-party prose, images, routines, personal histories or external licensed
content were imported. No new repository-wide license grant is asserted.

Every row has at least six eligible unexcluded records. Exact feasible first-day
seconds below are observed baseline output; the full weekly plans are in the
results artifact. Weekly lengths 2/3/4 are independently tested across all rows
and presets (72 combinations).

| Goal | Equipment | Experience | Eligible records | 20 min | 30 min | 45 min |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| general_strength | bodyweight | beginner | 8 | 1200 | 1800 | 2697 |
| general_strength | bodyweight | intermediate | 8 | 1200 | 1800 | 2700 |
| general_strength | dumbbells_and_bodyweight | beginner | 12 | 1200 | 1800 | 2697 |
| general_strength | dumbbells_and_bodyweight | intermediate | 12 | 1200 | 1800 | 2700 |
| general_conditioning | bodyweight | beginner | 8 | 1200 | 1800 | 2700 |
| general_conditioning | bodyweight | intermediate | 8 | 1200 | 1800 | 2700 |
| general_conditioning | dumbbells_and_bodyweight | beginner | 8 | 1200 | 1800 | 2700 |
| general_conditioning | dumbbells_and_bodyweight | intermediate | 8 | 1200 | 1800 | 2700 |

All 24 row/preset checks pass the independent validator. The 2697-second estimate
is within the inclusive 2640–2760 interval; no rounding is used for acceptance.
Dumbbells are optional under contract 12, so conditioning may remain bodyweight.
Coverage is conditional: exclusions or missing records can make a request
infeasible. A declared supported row does not guarantee every excluded subset
has a solution.

Metadata and compatibility were inspected for software-contract consistency,
not professionally certified fitness suitability. Independent qualified human
content review remains necessary before any participant trial. The earlier
F1-01 provenance fixture remains separate and is not loaded as an exercise.

## Domain behavior and architectural decisions

- `load_catalog()` returns versioned records as fresh validated copies, with
  read-only public revision/tags and an immutable encoded-record mapping. Duplicate
  IDs, inconsistent revisions and out-of-scope catalog size are rejected.
- `session_seconds(blocks, preset)` implements contract 12 exactly: repetition
  work uses four seconds per rep; rest is counted only between sets; transition
  is 45 seconds between blocks; warm-up/cooldown are fixed per preset. Integer
  arithmetic and the inclusive ±60-second interval determine acceptance.
- `validate_plan(raw, expected_profile, catalog)` revalidates both dictionaries
  and existing mutable/preconstructed Pydantic models. The caller supplies the
  trusted profile separately. A proposal cannot remove exclusions, substitute
  equipment/experience or otherwise change its own effective constraints.
- The validator checks schema/prescription/day bounds, every exercise's existence
  and compatibility, ID/tag exclusions, each day's recomputed seconds, and every
  day's preset interval. Unknown exclusion IDs/tags fail closed. Reports contain
  bounded issue codes and numeric locations, without input text or exception
  dumps. Serialization warnings are suppressed before revalidation of malformed
  transport objects so invalid values cannot leak through those warnings.
- `plan_week(profile, catalog, choices_declined=False, request_text="")` enumerates
  only the prescription choices allowed by contract 12. A finite bitset sum table
  determines feasibility for 3–6 distinct exercises. It prefers 4/5/6 blocks for
  20/30/45 minutes, then other counts, and chooses the nearest valid estimate to
  the target (ties shorter). Three-set options are preferred before fixed
  rest/work ordering; eligible exercise IDs rotate deterministically across days.
  This is an inspectable template policy, not a fitness optimizer or progression
  rule. It can find a feasible four-exercise fallback when a preferred five-record
  template is unavailable, rather than falsely calling the request infeasible.
- The baseline uses the same catalog and `validate_plan` entry point intended for
  the future agent. Validator code does not import the planner. A validation
  disagreement returns `error`, never an invalid fallback plan.
- Unknown/missing/unsupported constraints request clarification; exhausted or
  time-infeasible requests never relax constraints. Declining changes yields
  abstention. Uninterpreted free text cannot silently become a new constraint or
  instruction: it requests structured clarification, or abstains if declined,
  with a fixed professional-referral note for clinical contexts. This is not an
  NL/medical classifier and must not be represented as one.
- `PlanningResult` has no candidate approval ID. Attaching candidate identity,
  SSE terminalization, user authorization and saving remain subsequent units.

## Evaluation outcomes and documented rejections

Dataset revision: `synthetic-v1`. Exactly 40 fixed cases, split 24 development and
16 held out, with explicit expected outcomes/codes and exact issue sets for
invalid-proposal checks. There are 24 positive row/preset cases and 16 negative
cases. The complete artifact includes every result, generated plan, clarification
choice and rejection code/location; it does not just report aggregate success.

| Split | Expected outcomes passed | Plans | Clarify | Abstain | Invalid-plan errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development | 24/24 | 16 | 6 | 0 | 2 |
| Held out | 16/16 | 8 | 4 | 2 | 2 |
| Total | 40/40 | 24 | 10 | 2 | 4 |

**24/24 generated plans** pass independent hard checks. All 16 negative cases
produce the expected non-plan outcome. The four `error` cases are supplied bad
plans rejected deliberately, not generated invalid plans or hidden task failures:

| Case | Rejection |
| --- | --- |
| `dev-invalid-id` | `unknown_exercise` |
| `dev-wrong-seconds` | `duration_mismatch` on a later day, 1228 declared vs 1227 calculated |
| `holdout-wrong-equipment` | `equipment_mismatch` |
| `holdout-excluded-id` | `excluded_exercise` |

Unexpected outcome/scorer failures: **0** (`failed_cases: []`). The 72 matrix
tests, 24 coverage checks and other unit tests do not inflate the 40-case
denominator. The held-out split is fixed and inspectable, not a claim of blind,
unseen developer data or a population reliability estimate. No quality judge,
human usefulness score, model tool choice or clinical metric was measured.

Artifact fingerprints (SHA-256):

- Dataset: `c340a3761c3b6e1732f56e36e28bf4a9e985fe11235e67c4aea75855555c7d91`.
- Canonical catalog: `9f1e38c5e5e55eec28a663c4bd9dd50b031370895702ebaf9cf6283fda4e216a`.
- Runtime source set: `1db5d07969583ad6c68ddaa1f33c42d7f80e716ea70e444860ed4efdaf12814a`.
- Accepted dependency lock: `a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a`.

Rule versions are `template-v1`, `validator-v1`, `duration-v1` and
`hard-outcome-scorer-v1`. The runner normalizes text line endings, records source
and dependency hashes, and introduces no clock, network, Git-state or randomness
dependency. Frozen data/manifest inconsistencies fail before scoring.

## Exact commands and results

Executed from the repository root using the accepted F1-01 environment. No
dependency installation or download was needed.

| Command | Final observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q` | **226 passed, 3 deselected**, no warnings |
| `.venv/Scripts/python.exe -m pytest tests/test_domain.py tests/test_evaluation.py -q` | **155 passed** |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py` | Wrote full results; 24/24 development and 16/16 held-out expected outcomes, zero unexpected failures |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | Byte-for-byte recorded artifact check passed |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | 23 files already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Accepted OpenAPI unchanged/current |
| `npm --prefix web run check` | TypeScript compilation passed |
| `npm --prefix web run check:generated` | Accepted generated types remain current |
| `git diff --check` | Passed; only existing Windows line-ending notices |
| `git check-ignore AGENTS.md` | Local instruction file remains ignored |

Fresh-process reproducibility commands also passed without writing files:

```powershell
$env:PYTHONHASHSEED = '1'
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
$env:PYTHONHASHSEED = '1979'
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
Remove-Item Env:PYTHONHASHSEED
```

The 226 default cases comprise 71 accepted F1-01 cases plus 155 new F1-02 cases;
the six F1-01 approval reference-model cases are included, not counted again.
The three deselected tests are existing PostgreSQL bootstrap integration checks.
They were not rerun because no database, migration or environment code changed;
F1-02 needs no running database. No tests are skipped as future placeholders.

All nine hand-calculated contract examples pass: conditioning totals
1137/reject, 1140/accept, 1200/accept, 1260/accept, 1263/reject, 1800/accept and
2700/accept; strength totals 1227/accept and 2709/accept. Additional tests cover
all presets' inclusive limits and outside neighbors, unknown IDs/tags, equipment,
mode, experience, altered embedded profiles, duplicate blocks, invalid bounds,
mutated models, all-day arithmetic, feasible fallback vs true infeasibility,
declined changes, untrusted text, sanitized errors and an independent set-based
arithmetic oracle for the bounded search.

During test development, a mutation fixture initially assigned a value already
selected by the planner and therefore did not alter the plan; it was corrected
to force a real change. A checksum-tamper test initially depended on an
inaccessible OS temp directory; it now uses an in-memory altered-file view while
still exercising the real checksum. Final tests have no temp-path requirement
outside the workspace and no unresolved failures.

## Known limitations and F1-03 boundary

- No independent qualified content review or evidence of personal exercise
  suitability exists; no external participants are authorized.
- The catalog intentionally covers two goals, two gear selections and two
  experience bands only. Exclusions can remove feasibility. No clinical,
  pregnancy-specific, injury, nutrition, biometric or progression support exists.
- The template is deterministic and constraint-focused. It offers no NL
  interpretation, model personalization, effectiveness claim or subjective
  preference ranking beyond explicit supported fields and exclusions.
- Validator success is neither human approval, authorization, clinical safety
  nor a durable certificate. Mutable output must be revalidated at future trust
  boundaries against server-owned constraints, versions and immutable snapshots.
- No identity service, profile/candidate store, API business route, provider/tool
  loop, stream UI or approval transaction was added. The F1-01 guard/reconciliation
  obligations remain normative and are still reference-model evidence only.
- No hosted telemetry, live LLM/provider request, AWS provisioning, real-user
  data, commit or push occurred. The existing stopped database was not started.

F1-03 can compose the existing schemas with `load_catalog`, `plan_week` and
`validate_plan` under its separately authorized identity/persistence design.
It must retain process-frozen catalog/validator versions, candidate ownership,
TTL/lineage rules, and committed-key rechecks/uncertain-commit blocking for the
later approval path. No F1-03 work has begun. Stop for owner review.
