# F3-E8 — Independent-review handoff

2026-10-27. Offline preparation only; stop for review. No accounts, provider/AWS
requests, installations, financial authority, genuine secrets/cases/registration/
opening, human ratings, final freeze, commits or pushes. AGENTS.md is untouched.

## Files added

- `scripts/curator_public_rehearsal.py`: fixed public fixture validation/commitment
  practice with finite reporting; no arbitrary paths, genuine interface or service.
- `tests/test_curator_public_rehearsal.py`:12 synthetic regression/adversarial tests.
- `docs/implementation/curator/README.md`: role, boundaries and reading order.
- `docs/implementation/curator/f3-e8-computer-setup.md`: Windows/macOS/Linux setup,
  locked offline wheels, success outputs, permissions and troubleshooting.
- `docs/implementation/curator/f3-e8-public-practice.md`: public input/canonical
  guide and reproducible public-only steps, future coverage and known limitations.
- `docs/implementation/curator/f3-e8-storage-practice.md`: future public encryption/
  backup/restore options and their limits; no executed storage/OS change.
- `docs/implementation/curator/f3-e8-human-protocol.md`: exclusively human
  authorship, AI boundary, relationship/conflicts, sequencing and incidents.
- `docs/implementation/curator/f3-e8-declarations-blank.json`: all human fields null.
- `docs/implementation/curator/f3-e8-public-exposure.json`:47 already-public input
  fingerprints from existing exposed_input_index; five exact public source hashes.
- `docs/implementation/curator/f3-e8-requirements.txt`:18 existing lock versions,
  wheel-only hashes, no new dependency or modified lock.
- `docs/implementation/f3-e8-report.md` and this handoff.

Twelve additions; all544 task-entry public files remain byte-identical. No original
source/test, hard-rule body, rule, policy, manifest, exposure label or claim changed.
No application migration. The current114-input E6 candidate remains reproducible
and unapproved. E8's public-practice helper is not the genuine study/custody release;
future normative curator code and dependencies must be explicitly freeze-bound.

## Packaging and trust

Small kit selection: unchanged `src/future_training/*.py` recursively; the two
existing independent_cases/sealed_evaluation modules; new runner; all eight curator
guide/data/requirements files; pyproject/uv.lock/.python-version; domain contract12;
catalog-v1; public v1/model-v1 manifests/scenarios and model outputs; study selection;
four required prior protocol fixtures. Exactly84 files plus
`_curator/source-manifest.json`. Original relative paths are preserved.

Only the fixed public command is documented, not application startup or account
operations. Shared imports explain why FastAPI/psycopg/httpx are installed despite
no server, SQL or HTTP execution. No Git, IAM/Terraform, frontend, credentials,
state/claims, private cases or reviewer records are needed in the small kit.

The full source-review archive uses `scripts/review_source.py` and contains556
public files plus `_review/source-manifest.json`. Both archives have SHA-256
sidecars; all source members are verified against raw working-tree bytes. They
exclude ignored/private paths, AGENTS.md, credentials/caches and genuine evaluation
materials. Hashes detect substitution only when compared with independently
reviewed values; they do not establish human independence or actual custody.

## Fresh checks and exact commands

Windows Python3.14.9; Ruff0.17.2; existing locked developer environment only.

```powershell
New-Item -ItemType Directory -Path .cache/f3-e8 -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e8/before.json
.venv/Scripts/python.exe scripts/curator_public_rehearsal.py
.venv/Scripts/python.exe -m pytest tests/test_curator_public_rehearsal.py tests/test_independent_cases.py tests/test_sealed_evaluation.py tests/test_model_evaluation.py tests/test_review_source.py -q --basetemp=.cache/f3-e8/pytest-public --tb=short
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
```

| Check | Observed outcome |
| --- | --- |
| Selected tests |249 passed,128.89s; no skipped/failed tests |
| New failures/tampering | Unexpected CLI arguments/private-path/key/open attempts reject; malformed/duplicate/wrong-scope/source index rejects; exception canary not printed |
| Existing scoring/integrity | Intermediate hard failures, missing evidence, genuine-opening denials, historical v1 compatibility and public exposure protections retained by selected tests |
| Frozen baseline |40/40:24 development+16 historical held-out; software correctness only |
| Comparison |150 expected handling dispositions; hard50 template /44 fake /44 replay; no human-quality results |
| Contracts/grammar | No contract drift;197 public Python files parse natively and under3.13 grammar |
| Ruff | Check passes;200 files formatted |
| Extracted minimal kit | Two isolated-interpreter runs, identical public JSON, no Git or socket/DNS/child-process operations; existing venv libraries only |
| Setup/storage | Three PowerShell blocks parsed via Language.Parser.ParseInput; encryption/storage steps not run; no fresh install, macOS/Linux or curator-device verification |
| Pin/source checks | Requirements versions/wheel hashes match uv.lock; public index equals existing helper;12 new files only; all prior544 hashes and114 freeze inputs unchanged |

The first isolated-kit harness incorrectly replaced subprocess.Popen with a
function, causing Windows asyncio's subclass import to fail before practice.
The harness was corrected to a rejecting subclass, then both extracted-kit runs
passed. No application protection was weakened. This was a test-instrumentation
failure, not evidence of network traffic or a successful curator run.

Test/check logs, public developer report and standalone verification are ignored
under `.cache/f3-e8/`. Public index was generated using the unchanged
sealed_evaluation.exposed_input_index plus raw SHA-256 of its fixed five sources.
Requirements were generated by traversing the existing uv.lock dependency closure
for FastAPI/Pydantic/httpx/psycopg/binary and copying only locked wheel hashes.
No packages/wheels were fetched or installed. Freeze/preservation/doc checks use
the task-entry public inventory, current freeze() and checked-in candidate bytes.
PowerShell blocks were parsed, never evaluated.

Small ZIP construction uses the exact inventory above and raw SHA-256 entries.
It was extracted into a new ignored directory and executed twice with `python -I`,
only basic Windows environment variables, socket connect/DNS hooks rejecting and
Popen subclass rejecting. This is Python-level instrumentation, not OS isolation.
Fresh dependency installation and cross-OS binary availability remain unverified.

Full review packaging:

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e8/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e8/review/source-manifest.json --archive .cache/f3-e8/review/future-training-f3-e8-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e8/review/source-manifest.json --archive .cache/f3-e8/review/future-training-f3-e8-review.zip
```

Native SQL/TLS spending, frontend/browser, hosted CI, full application suite and
real providers were not rerun: no corresponding source changed, and the curator
rehearsal needs no such service. Earlier E6 evidence is historical, not a fresh
E8 denominator. No retrospective result or frozen snapshot was regenerated.

## Remaining custody requirements and exact next boundary

Independent review should approve/reject the **public-only** kit and proposed
human-only protocol. Owner then separately chooses curator OS/runtime/wheelhouse,
conflict acceptance, viewers, encryption/recoverable backup arrangement and may
commission public setup/rehearsal. Actual human observations and recovery checks
must be recorded by the human/witness, not inferred from developer test output.

Before genuine work, still resolve the denied novel-case canonicalization and
genuine secret/authenticated receipt/pins interface, final source/model/study
decisions and freeze, private exposure audit, curator appointment/acknowledgement,
witness/custody/recovery and separate ten-case creation authorization. Human alone
must author them. No AI content generation, rewrite, selection or improvement.
Sealing/registration/opening, provider privacy/prices, money, actual study and
human reviews remain separately gated. No next activity is automatically approved.
