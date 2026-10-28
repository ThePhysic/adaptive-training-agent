# F3-E2 — Structured offline handoff

2026-10-27. **F3-E2 only**. No AWS/CLI/account/provider/hosted request, credential
inspection, final sealed content, attestation, genuine registration, human scoring,
positive financial authority, executor activation, installation, commit or push.
Historical IAM stopped/uncertain attempts and NO-GO records are untouched.

## Audit and smallest integration

Reviewed the accepted readiness assessment/backlog/handoff, F3-E1 report/handoff,
protocol20/readiness19/provider-safety, common evaluation/scoring/review, preparation
scripts, counted-probe experiment, test fixtures and public source packager.

The v1 Case's provenance is developer-authored/exposed; its ten comparison cases
and the old legacy held-out cases have already been inspected. The model manifest
fingerprints all src files. Therefore this work is an additive repository experiment,
not a change to those literals, scorer, historical meaning or src fingerprints.
No parallel evaluator, case loader, SDK, service, dependency or live runner was added.

`freeze()` hashes exact raw public source bytes, including accepted dirty changes,
and canonical selection/exposure bindings. It covers application validation/tools/
schema/prompts/config, catalog, dependency/runtime locks, frozen/public datasets,
provider assets, normative contracts and the E1/E2 adapters, tests and procedures.
It has no timestamps or self-reference. Relevant source additions, changed bytes,
prompts, selection or scorer invalidate it. Reports/generated freeze are excluded
to avoid circular hashes. The public generated candidate is not owner approval.

`validate_manifest` consumes only bounded duplicate-key-safe opaque JSON and owner
pins, never a case/key pathname. V2 binds ten entries, declaration of split/coverage,
content root, private keyed input commitments/index, key context, freeze, rubric/
scorer and references. Synthetic-test and independently-curated namespaces cannot
be mixed. Tests use predictable fake keys and **non-case sentinel bytes**, not
new workout inputs or genuine attestations. Positive test records are synthetic.

`register_metadata` uses exclusive create/flush/fsync; partial records prevent
replacement. `verify_registration` rechecks exact saved metadata and current freeze,
with a bounded read even during growth. An exclusive invalidation marker blocks
verification/re-registration even if partial. No reset/delete/overwrite or opening
API exists. Storage is restricted to `.cache/f3-e2` in an owner-controlled checkout.

`review_status_counts` keeps every declared slot, including missing/abstained/
ineligible; it returns zero **verified** judgments and null quality. Supplied status
labels are not authenticated ratings. Future real-rating import must independently
verify common-scored eligibility and reuse the existing rubric/validate_ratings/
agreement helpers. This work implements neither an importer nor fake human scores.

## Files and preservation

| File | Change |
| --- | --- |
| `experiments/sealed_evaluation.py` | New metadata/freeze/registration and blank-status helpers |
| `tests/test_sealed_evaluation.py` | New synthetic metadata, tampering, exposure, archive and compatibility regressions |
| `scripts/review_source.py` | Existing public untracked file: add four reserved private path components, filtered before content reads |
| `docs/implementation/f3-e2-sealed-evaluation-specification.md` | New normative freeze/manifest specification |
| `docs/implementation/f3-e2-curator-procedure.md` | Independent custody, curation, commitments, incidents and opening handoff |
| `docs/implementation/f3-e2-human-review-materials.md` | Blank blinded review/denominator/disagreement procedure |
| `docs/implementation/templates/f3-e2-curation-blank.json` | Null checklist, not an attestation or valid manifest |
| `docs/implementation/templates/f3-e2-human-review-blank.json` | Null/pending form; no reviewer, ratings or hidden labels |
| `docs/implementation/evidence/f3-e2-freeze-candidate.json` | Reproducible public configuration candidate only |
| `docs/implementation/f3-e2-report.md` and this file | New report and handoff |

The task-start public manifest recorded 509 files/189 Python files. Raw-byte comparison
shows only the packager's path-exclusion change among initial files, ten additions
and no deletions: final519 files/191 Python files. Existing tracked Git diffs belong to earlier accepted work; this
task neither stages nor normalizes them. AGENTS.md remains ignored and unmodified.

## Validation and environment

Windows host; existing locked Python 3.14.9 and Ruff0.17.2. Cached pinned PostgreSQL
18.6 on loopback55432; isolated schemas and existing synthetic MockTransport/LocalTLS
fixtures. No downloads or new dependencies. Routine test socket/DNS guards remain.

Initial sandboxed test runs used `pytest-first-rerun` and `pytest-provider` below
`.cache/f3-e2`. Windows denied pytest temporary-directory access, including session
cleanup, so those exits are **failed**, not acceptance evidence. Logs are retained.
Reran with normal local workspace access, without changing test isolation or grants.

The first normal-access metadata run exposed two test-harness defects: a >32KiB
parameter rendered into `PYTEST_CURRENT_TEST` exceeded Windows' environment-variable
limit, and `tmp_path` was itself under the allowed registry root. It recorded
155 passed, one failed and two errors (including setup/teardown). Fixed finite
parameter IDs and a genuinely outside directory. Removed ineffective Pydantic
alias repr metadata (50 warnings), retaining opaque repr and hidden error input.
The final full selected batch below passed without warnings. These development
failures are retained in ignored logs and not counted as passing acceptance.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e2/before.json
docker compose up -d --pull never --wait postgres
.venv/Scripts/python.exe -m pytest tests/test_counted_probe_evidence.py tests/test_authority_postgres.py tests/test_counted_spending_postgres.py tests/test_spending_postgres.py -q -m integration --basetemp=.cache/f3-e2/pytest-native --tb=short
.venv/Scripts/python.exe -m pytest tests/test_responses.py tests/test_counted_responses.py tests/test_probe_authority.py tests/test_provider_hardening.py tests/test_provider_tls.py tests/test_token_admission.py tests/test_langfuse_local.py -q --basetemp=.cache/f3-e2/pytest-provider-final --tb=short
.venv/Scripts/python.exe -m pytest tests/test_sealed_evaluation.py tests/test_review_source.py tests/test_model_evaluation.py -q --basetemp=.cache/f3-e2/pytest-sealed-canonical --tb=short
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
.venv/Scripts/python.exe scripts/review_source.py check
git -c core.safecrlf=false diff --check
docker compose exec -T postgres postgres --version
docker compose stop --timeout 30 postgres
```

For the three acceptance pytest commands, stdout/stderr were redirected respectively
to `.cache/f3-e2/native-tests.txt`, `provider-final.txt`, `sealed-canonical.txt`.
Normal local workspace access was needed for Windows temp files and Docker; no
elevated OS configuration or account permission was changed.

| Check | Observed result |
| --- | --- |
| New sealed tests + existing packager/common scorer | **160 passed,109.37s**, no skips/errors/warnings:54 new+18 existing archive+88 existing evaluation |
| Existing provider/count/transport/privacy/independent-denial regressions | **253 passed,12.51s**, no skips/errors |
| Existing F3-E1 native SQL/MockTransport/LocalTLS + accounting batches | **153 passed,130.99s**, no skips/errors:51 E1+102 authority/mixed-spending/spending |
| Nonduplicated selected Python denominator | **566 =160+253+153**. No full routine/application-suite claim |
| Frozen baseline | **40/40**,24 development/16 historical held-out; all expected outcomes preserved |
| Model assets / offline comparisons | **50 unchanged** (40 development/10 exposed); **150/150 expected handling dispositions**. Template hard50, fake/replay hard44 each;12 intended hard failures retained |
| API/TS contract check | Exit0, no drift |
| Ruff lint/format | Passed;194 files already formatted |
| AST/source grammar | **191 public Python files**, native and3.13 parse successfully |
| Whitespace/source preservation | Passed; only the one expected initial-file change, ten additions, zero deletions; all initial src/data/locks/contracts/gates bytes unchanged |
| Documentation | Five new reports/procedures checked as UTF8 with balanced fences; ten relative links resolve; both blank JSON forms parse |
| Local database/version/cleanup | PostgreSQL18.6 (Debian18.6-1.pgdg12+2); task-started service stopped, volume retained, engine left running |

Freeze generation/validation was run twice in memory with byte-identical canonical
results, then `check_freeze` succeeded and the JSON was exclusively written:

```powershell
@'
import sys, json
from pathlib import Path
sys.path.insert(0, 'src')
from experiments import sealed_evaluation as e
f = e.freeze()
assert e.canonical(f) == e.canonical(e.freeze())
e.check_freeze(f)
with Path('docs/implementation/evidence/f3-e2-freeze-candidate.json').open('x', encoding='utf-8', newline='\n') as out:
    out.write(json.dumps(f, sort_keys=True, indent=2) + '\n')
'@ | .venv/Scripts/python.exe -
```

The candidate binds **99 files**, **47 distinct normalized exposed inputs** from
the90 known authored rows (not47 independent cases), and the ten-case/20-pair rules.
Fingerprint: `59c62dba4099cbfcb24e84b213e3dc05d34fca4b3d75d62a3608a4cda025cea4`.
All live/money flags are false. No genuine population commitment or approved
reference is generated. Candidate file is intentionally outside its own freeze.
The initial development candidate was retained in ignored
`.cache/f3-e2/development-freeze-candidate.json` and the new public candidate
refreshed once after the final type-sensitive comparison change. No owner-approved
freeze, final commitment or historical snapshot was replaced.

Before that final refinement, `pytest-sealed-release` passed157 tests in102.27s.
Adversarial review then found Python dictionary equality conflates false/0 and
integer/float values. Freeze and saved-record verification now compare canonical
JSON bytes; three regression cases reject these changes. The complete affected
batch was rerun to the160-test outcome above. Counts are not pooled across repeats.

New tests cover source/policy drift, manifest/version/provenance mismatch, missing
attestors, duplicate ordinal/input/content, overlap, changed commitments/pins,
JSON duplicates/nonfinite/oversize/UTF8/schema errors, exclusive/concurrent writes,
boolean/numeric type substitution despite Python equality,
fsync interruption/partial files, invalidation, stale registration, path bounds,
oversized saved records, finite private errors, blank/missing human slots, preserved
hard-failure gates, historical labels and reserved archive paths before reads.
No real OS custody or curator-content validation is claimed by these tests.

No fresh frontend/build/browser, full application, Terraform or AWS run is claimed:
application, runtime dependencies, routes, UI and infrastructure are unchanged.
Native SQL/loopback TLS and all selected software tests were freshly run here;
historical F1/F2 acceptance is not substituted for these new denominators.

## Adversarial review and limits

| Question | Control and residual limit |
| --- | --- |
| Can development tune against hidden cases? | No content loader/path discovery; independent device/account custody required. Same-user OS secrecy is not demonstrated. No final content accessed. |
| Can exposed cases be renamed unseen? | Historical labels unchanged. Normalize schema defaults/exclusion order independent of ID/split/answers; reject token/index intersection and internal duplicates. Curator witnesses token construction and semantic novelty. |
| Can stale prompts/config slip through? | Exact current freeze required at validation and saved-record verification; mutable owner selection cannot silently rebind pins. |
| Can commitments change after results? | External pins bind the complete manifest/root/context; exclusive registration, partial-record blocking and retained invalidation. A malicious owner editing files/pins is outside cryptographic origin guarantees. |
| Can errors or archives disclose content? | Fixed finite errors, opaque model repr, bounded documents, no logging/tracing/export. Reserved private paths are excluded before reads. Caller must not print raw models or put secrets under renamed public paths. |
| Can synthetic evidence become real? | Synthetic namespaces/pins/exposure paired strictly; candidate flags live/money false. No output collector or human importer. Reference strings are not authenticated identities; owner must verify independent attestations separately. |
| Can missing judgments improve denominators? | Predeclare every slot, keep missing/abstained/ineligible distinct; no quality calculation from statuses. Actual collected judgments remain zero. |
| Can repair conceal a hard failure? | Scorer/E1 unchanged; compatibility tests reject incomplete/live-labelled packets and hard-failed quality. Native E1 regression rerun. |
| Can invalidation/partial writes enable reuse? | Existing/partial files and invalidation markers block supported registration/verification, including concurrent registration. No retry/overwrite or opener; keep first observations. |

Opaque metadata cannot prove case contents, coverage, secret-key consistency,
curator identity/independence or all previous exposure. The fixed index covers
only the two known public populations. Later curation needs a privately retained
audit of prior opened/exposed/invalidated cases too; different keys are not comparable.
Unavailable custody/history means stop, not regenerate IDs or relabel cases.

The future scorer bridge remains deliberately unimplemented: current v1 Case
cannot represent independent provenance honestly. Separately approved opening must
verify full/input commitments and supply a reviewed truthful envelope to the same
scorer, preserving incomplete/intermediate failure evidence. E2 metadata registration
is not scored evidence or proof that final cases are valid.

## Owner/curator boundary and readiness

Ready for independent review of **offline infrastructure only**. Genuine population
count0, accepted curator attestations0, human judgments0, live evaluations0. Owner
must settle actual model/source/terms first, independently approve a final freeze,
nominate a human curator and establish private custody/retention. Source release or
model configuration changes invalidate the current candidate for that study.
Curator then supplies genuine cases, commitments, truthful exposure audit and
attestation privately; owner independently pins/approves metadata. Neither action
is performed by this task. A later content-opening implementation/evaluation and
any model/spending/privacy/export/participant approval are separate decisions.

No AWS or provider authorization is requested. The historical live NO-GO, unknown
counting pricing/retention, source-denial barriers and all USD0 allowances remain.

## Sanitized review package

Only Git-visible public source plus embedded raw-byte SHA-256 manifest. Exclude
AGENTS.md, caches/credentials/identities, state/plans, dependencies, future sealed
cases, real reviewer material and hidden keys. Full synthetic test code and blank
forms are public; ignored synthetic test registries and prior private packets are
not included. Exact archive commands and separate byte audit are recorded below
after final validation. A machine audit is not independent human acceptance.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e2/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e2/review/source-manifest.json --archive .cache/f3-e2/review/future-training-f3-e2-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e2/review/source-manifest.json --archive .cache/f3-e2/review/future-training-f3-e2-review.zip
```

The packager verifies519 source members against the working tree and the embedded
manifest. A separate `zipfile`/`hashlib` audit (without importing the packager)
checks exact member names, every raw-byte hash and equality to working-tree bytes,
reserved private path exclusions, public-only secret patterns and all99 freeze
inputs. Verification JSON and ZIP SHA-256 are saved beside the ignored archive.
No private directory/capture is scanned to perform this verification.
