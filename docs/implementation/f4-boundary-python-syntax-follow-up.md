# F4 Python exception syntax and review-archive follow-up

2026-10-26. **Offline correction only. Stop for review.** No AWS account call,
infrastructure configuration change, provider request, spending, commit or push.
Pre-existing boundary implementation changes remain in the worktree.

## Finding: parser compatibility, not demonstrated source drift

Located the local `../future-f4-boundary-review.zip` (4,057 entries). Before editing,
the four reported source members were **byte-for-byte identical** to the actual
working-tree files:

| File | Original archive / working-tree bytes | Native Python 3.14.9 | Python 3.13 grammar |
| --- | --- | --- | --- |
| `infra/aws/private_command_runner.py` | 21,477 / 21,477, identical | PASS | FAIL |
| `infra/aws/state_boundary.py` | 6,088 / 6,088, identical | PASS | FAIL |
| `infra/aws/state_bundle.py` | 4,549 / 4,549, identical | PASS | FAIL |
| `infra/aws/fixtures/backend_probe.py` | 18,801 / 18,801, identical | PASS | FAIL |

The boundary handler was indeed present at line 165. It was not invented by ZIP
extraction or a different checkout. Python **3.14** permits omitted parentheses in
multi-exception handlers under PEP 758; earlier grammars reject the form. The
project's `requires-python`, lock and CI checks specify 3.14, and previous checks
ran on **3.14.9**. Native raw-source parsing succeeded for all 169 existing owned
Python files; 25 failed the 3.13 grammar because of this syntax.
[Python 3.14 language change](https://docs.python.org/3.14/whatsnew/3.14.html#pep-758-allow-except-and-except-expressions-without-brackets).

A controlled stdin experiment with pinned Ruff **0.17.2** confirmed that
`ruff format --target-version py314` converts a short parenthesized handler into
the reported form. Its py313 formatter preserves existing parentheses. The earlier
AST checks did not establish compatibility with older review-tool grammars; their
Python 3.14 pass result was valid, but that limitation was not made clear enough.

The independent reviewer's interpreter/tool version and uploaded artifact checksum
were not supplied. The local ZIP comparison proves equality for the four inspected
members, not identity with an unseen remote upload or every other original member.
The parser mismatch reproduces the discrepancy without assuming archive drift or
stale bytecode. Original ZIP/hash-only evidence is retained locally in
`.cache/python-source-review/original-archive-comparison.json`; no original archive
member was modified or broadly extracted.

## Corrections and behavior preservation

Converted **55 handlers in 25 files** to explicit multiline parenthesized tuples
with trailing commas. Ruff retains this form under the existing **py314** target.
No runtime/formatter target downgrade, new dependency or exception-type change was
needed. `pyproject.toml` and all dependency locks remain unchanged.

Syntax-only files by group:

- The four reported infrastructure modules.
- `scripts/check_browser.py`, `scripts/check_release.py`.
- `experiments/langgraph/spike.py`.
- `tests/browser_runner.py`, `tests/local_tls_doubles.py`, `tests/test_browser_harness.py`.
- Fifteen runtime modules: agent orchestration/tools; approval, candidates, identity
  and streaming; async-read, scoring and token-admission experiments; approval,
  completion, plan and profile persistence; counted and Responses providers.

A before-edit raw-byte/AST snapshot verified **all 169 existing Python ASTs were
unchanged by the syntax transformation**, excluding location attributes. Therefore
the caught classes, order, bodies and cancellation behavior were preserved.
This comparison includes the owner's existing boundary work, rather than reverting
it to HEAD. The corrected handler in `state_operator_prepare.py` remains intact.

Added `scripts/review_source.py` and `tests/test_review_source.py`:

- Parse every Git-visible, project-owned `.py` file directly from raw bytes with
  both the native parser and `feature_version=(3, 13)`, without importing it.
- Keep the grammar check in routine pytest, with a regression demonstrating the
  original mismatch and formatter retention of the corrected form.
- Snapshot raw SHA-256 for public working-tree files, then refuse packaging if
  inventory or bytes changed after validation.
- Verify every archive member against its working-tree bytes, reject duplicate/
  corrupted members and verify the embedded manifest's canonical bytes.
- Exclude ignored/private state and explicitly reject AGENTS, AWS/config/cache,
  virtual environments, downloaded tools, Terraform working/state/input files,
  dependency trees, bytecode, symlinks/junctions and path escapes. ZIP creation is
  exclusive and never overwrites a prior archive. No upload/deployment is performed.

The project runtime is still Python 3.14. Passing a 3.13 *grammar* check does not
claim runtime compatibility with 3.13: the project uses 3.14 runtime behavior,
including deferred annotations.

## Versioned offline evaluation provenance

Formatting application files changes their recorded source hashes. Existing
`offline-scores.json` and `offline-scores-f4-01.json` were **not overwritten**.
Used the established versioned-reference mechanism to add:

`data/evaluation/model-v1/offline-scores-python-syntax.json`

Updated only `SCORE_REFERENCE` in `model_eval_assets.py` to select that new record.
An automated deep comparison proves that **only** `manifest.source_files` and
`manifest.source_sha256` differ from the previous active reference. All 150 cases,
scores, handling outcomes, hard failures, rubric/catalog/data/prompt versions and
remaining metadata are identical. The frozen 24/16 corpus and prior evaluation
evidence remain unchanged; no hard failure was reclassified as a pass.

The one reference-path constant is the only subsequent non-format AST difference
in the 169 existing modules. Normalizing that documented constant back to its old
value restores exact AST equivalence for all 169. No domain, provider, approval,
persistence, scoring or authorization rule was changed. Evidence remains entirely
template/fake/replay, not real-model quality.

## Commands and observed results

| Check | Result |
| --- | --- |
| Raw-source AST | **171/171 Python files PASS** native 3.14.9 and 3.13 grammar; includes two new source/test modules |
| Semantics | 55 corrected handlers across 25 files; original 169 ASTs identical after syntax-only phase; subsequent reference-only constant separately verified |
| New archive/grammar tests | **18/18 PASS**, including CRLF preservation, source drift, corruption, duplicate ZIP entries, private exclusions and unchanged evaluation outcomes |
| Affected Windows tests | **231/231 PASS**, 10.58s; subset of routine count |
| Affected network-disabled Linux tests | **231/231 PASS**, 19.38s |
| Complete offline sequence | **20/20 commands exit 0; 1,378 routine Python tests PASS**, 52.28s in the observed initial run; zero failures/errors/skips; 257 integration deselected |
| Native synthetic Terraform backend | **10/10 expected dispositions**, zero real AWS requests; only controlled loopback S3/STS fixtures |
| Frontend/contracts/baseline | **131 frontend tests**, TypeScript, build, contract/asset generation, lint/format pass; frozen **24/24 development + 16/16 held-out** cases and all 150 comparison dispositions reproduce |

Exact principal commands from the repository root:

```text
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/python.exe -m pytest tests/test_review_source.py tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_private_command_runner.py -q --basetemp=.cache/pytest-source-review-windows
.venv/Scripts/python.exe scripts/evaluate_models.py --record-offline --output .cache/python-source-review/evaluation
.venv/Scripts/python.exe .cache/r5b-checkpoint-b/run_checks.py
.venv/Scripts/python.exe infra/aws/fixtures/backend_probe.py --native-offline
.venv/Scripts/ruff.exe check src scripts tests infra/aws experiments --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws experiments --no-cache
git diff --check
```

`run_checks.py` is the previously used ignored driver for unchanged
`scripts/check.py`, with AWS/TF/provider/telemetry/proxy overrides removed and
output captured locally. A final full run after the source snapshot writes
`.cache/f107/check-results.json` and the protected driver log; packaging requires
that snapshot still match. The initial and final runs are the same offline suite,
not additive test denominators. No source edits occur between the final snapshot,
full run, archive creation and byte verification.

Linux command, using the already installed Python 3.14.9 image with no network:

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -m pytest tests/test_review_source.py tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_private_command_runner.py -q --basetemp=.cache/pytest-source-review-linux
```

No Python/SDK installation or hosted CI was performed. PostgreSQL/browser integration
and isolated experiment execution were not rerun: the existing code changes are
AST-equivalent formatting; the full routine and affected cross-platform suites
were run instead. Native backend testing used fake local services, not AWS.

## Review archive and exact diff

Use the newly generated local ZIP, not a recompressed older checkout:

```text
.cache/python-source-review/future-f4-boundary-python-syntax-review.zip
.cache/python-source-review/future-f4-boundary-python-syntax-review.zip.sha256
.cache/python-source-review/tested-source.json
.cache/python-source-review/archive-verification.json
```

The ZIP contains Git-visible public working-tree source and assets, including
untracked authorized boundary work, plus `_review/source-manifest.json`. It does
not include `.git`, local instructions, private inputs, credentials, dependencies
or caches. The embedded manifest is byte-identical to the sidecar snapshot.
Archive verification compares **raw bytes**, so newline/encoding changes are not
silently normalized. The detached checksum avoids a self-referential archive hash.

Reproduce the snapshot → test → package → verify order:

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/python-source-review/tested-source.json
if ($LASTEXITCODE -ne 0) { throw 'review_snapshot_failed' }
.venv/Scripts/python.exe .cache/r5b-checkpoint-b/run_checks.py
if ($LASTEXITCODE -ne 0) { throw 'offline_checks_failed_do_not_package' }
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/python-source-review/tested-source.json --archive .cache/python-source-review/future-f4-boundary-python-syntax-review.zip
if ($LASTEXITCODE -ne 0) { throw 'review_packaging_failed' }
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/python-source-review/tested-source.json --archive .cache/python-source-review/future-f4-boundary-python-syntax-review.zip
if ($LASTEXITCODE -ne 0) { throw 'review_archive_not_identical' }
```

Creation is exclusive: use new paths for another review, never overwrite a tested
snapshot or ZIP. Any later source/document edit requires a new snapshot, checks and
archive. A successful manifest check proves file parity, not absence of every
possible secret in public files; known private inputs remain excluded.

Incremental change summary relative to the task's starting worktree:

- 25 Python files: exception-header formatting only.
- One existing Python module: versioned evaluation reference path only.
- Four new files: source-review utility, its tests, versioned offline reference,
  and this follow-up report.

The normal `git diff` against HEAD also includes the pre-existing boundary changes;
it must not be presented as exclusively this correction. Full tracked diff/stat and
the before/after semantic/hash reports are retained under `.cache/python-source-review`.
The review ZIP and manifest include the complete current public file inventory,
including new untracked files that ordinary `git diff` omits. No staging, commit,
push, AWS operation or infrastructure change follows from these results.
