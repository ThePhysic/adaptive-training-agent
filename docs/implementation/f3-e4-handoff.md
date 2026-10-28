# F3-E4 — Structured independent-review handoff

2026-10-27. Authorized **offline F3-E4 only**. Stop for independent review.
No AWS/CLI/account/provider/hosted request, genuine case/commitment secret,
curator appointment, attestation, real opening/registration, human rating,
positive monetary authority, executor activation, installation, commit or push.
Private credentials/identity/case/capture records were not inspected. AGENTS.md,
historical NO-GOs and uncertain AWS attempts remain unchanged.

## Audit and architecture

Reviewed E3A assessment/procedure/handoff, E2 specification/curator/handoff/module,
E1 handoff/recorder, protocol20/provider-safety, existing scorer/evaluator/review,
scripts, public manifests, fixtures and tests. The existing Case/score boundary
required developer-authored/exposed literals. Reusing it under fake independent
labels would be untruthful; duplicating its checks would create a second scorer.

Added validated provenance-free ScoringFacts/score_facts and moved the existing
hard-rule body verbatim to shared `_score`. Both wrappers call it. The v1 Case
and its revalidation are unchanged. AST comparison against the prior sanitized
public source archive, verified against the task-start raw hash, established an
identical body. A regression pins its AST SHA-256:
`0e0cc2ad111b41cc780c90cace86a88844a938ad16276ef942db372cc55bfbd9`.

The experiment contract represents synthetic, independent-unopened and separately
authorized-opened states without treating strings as authority. All current case
verification APIs accept only fixed public development controls; every call
rechecks full/input HMACs, exact metadata/root/pins/ordinal/config and study binding.
The nonsecret key is fixed bytes(range(32)); no real secret parameter/generator.
The core facts entrypoint additionally denies independent_opened. Neither genuine
opener is activated. No v1 provenance projection, provider runner, arbitrary case
path, new transport/framework or domain/persistence rule exists.

Fixture evidence requires explicit proposal/publication flags and response,
proposal-ordinal and tool coverage. Existing check_call independently checks raw
synthetic tool arguments/capabilities; result validity is explicitly a declared
synthetic verdict. Aggregate all intermediate failures before common scoring.
Unknown accounting, missing/cancelled/uncertain evidence yields incomplete/no score
or finite rejection; charged/held/null values and counters are preserved. Actual
cost total stays null, never inferred zero from a failed request. Native E1 SQL
evidence remains separate; the new fixture bundle is not a billing collector.

Exclusive first-result writes prevent replacement after a failure, partial write
or fsync error, including concurrent writes. This pure scorer does not own provider
execution. Optional local retention cannot prove no earlier run occurred; future
actual collection must bind durable run/attempt ownership and first-result identity.
Same-user filesystem or Python-object tampering is not an OS security boundary.

## Changed files

Four initial public files modified; nine additions; no initial files deleted.

| File | Change |
| --- | --- |
| `src/future_training/experiments/model_scoring.py` | New validated facts boundary, closed genuine branch, shared unchanged hard-rule body; old Case unchanged |
| `src/future_training/experiments/model_eval_assets.py` | Exact additive compatible-reference reader, no historical output changes |
| `scripts/evaluate_models.py` | Existing offline --check binds new source manifest plus original150 results; no new execution mode |
| `tests/test_model_evaluation.py` | Same full-report/case/summary assertions using additive exact reference |
| `experiments/independent_cases.py` | New case/selection/freezev2/fixture verification/scoring/retention; no opener/executor |
| `tests/test_independent_cases.py` | 77 synthetic/canonical/provenance/integrity/hard-failure regressions |
| `data/evaluation/study-v1/selection.json` | Exact public development selection and20-pair denominator/run-order proposal |
| `data/evaluation/study-v1/legacy-compatibility.json` | Original raw score-file/manifest hashes and current exact manifest; only three permitted source-file differences |
| `docs/implementation/f3-e4-contract.md` | Normative versioned case, commitment, study and additive freeze specification |
| `docs/implementation/evidence/f3-e4-freeze-candidate.json` | New unapproved freezev2 candidate |
| `docs/implementation/evidence/f3-e4-synthetic-evidence.json` | Three bounded metadata-only unit examples, no plans/actual execution/billing claims |
| `docs/implementation/f3-e4-report.md` and this handoff | Report, validation, limitations and owner decisions |

Start522 public files/191 Python; final531/193. Raw-byte comparison requires exactly
the four changes above and nine additions. Earlier dirty changes, including the
already-selected offline-scores-python-syntax reference and parenthesized exception
handlers, are preserved; they are not new E4 changes. No Git staging occurred.

## Historical compatibility and freeze

No dataset, existing manifest/result/score snapshot, exposure label or E1/E2 report
was regenerated. `legacy-compatibility.json` is new: it stores no replacement150
rows, only the old raw file/manifest bindings and current provenance manifest.
The reader permits differences only in source_files/source_sha256 for exactly
the scorer, assets helper and CLI. Dataset/config/model/price/usage/rubric/selection
fields and the entire150 rows/summaries must remain identical to the old reference.
Unlisted/added source, altered manifest/hash or historical-file tampering fails.
Current --check does not claim old and current source bytes are identical.

The first development compatibility file was retained under ignored
`.cache/f3-e4/development-compatibility.json`; this new, unapproved artifact was
refreshed once after final genuine-source denial and raw historical-hash checks.
No historical snapshot was replaced to make tests pass.

The E2 candidate remains byte-identical, raw SHA-256
`ecaeb2db0cb4a309b9b20d3a7c63f203e09351b49848ef9677cb379e49530dfa`.
Its old current-source validator now correctly rejects the authorized source change;
it remains a truthful historical unapproved snapshot. E2 metadata tests compute
current synthetic configurations, not retroactive approval of that candidate.

Additive freezev2 captures111 files, including all experiment Python recursively,
the E4 interface/test/spec, study selection and compatibility record, current
common scorer/dependencies and original E2 inputs. Final candidate fingerprint:
`efbbe0dc28781ff952e60c7368e02c31b773858e78383c5b413015b31f434234`.
Selection SHA-256:
`dab3769466d499d6d27803b4af6758ea5687e7db2ec3413fdd734ec7298a1779`.
Two canonical generations/check_freeze agree; status candidate_not_owner_approved,
live/money false. No registry call or owner approval is implied. Generated candidate,
reports and unit-result projections are excluded from their own configuration hash.
The initial unapproved E4 candidate and unit projection were retained under ignored
`.cache/f3-e4/development-freeze-candidate.json` and
`development-synthetic-evidence.json`, then refreshed once after the final
case/variant/provenance/fingerprint retention checks. No accepted historical
candidate/result was overwritten. The final unit projection identifies the final
configuration/selection hashes and still contains only declared synthetic findings.

## Exact fresh validation

Windows, Python3.14.9, Ruff0.17.2; existing pinned PostgreSQL18.6
(Debian18.6-1.pgdg12+2), cached image and loopback55432, isolated synthetic schemas.
Existing MockTransport/LocalTLS and no-external-DNS/socket fixtures; no installation,
image pull, genuine credentials or real services. Normal local access was needed
for Windows pytest temp files and Docker, with no OS security-setting changes.

```powershell
New-Item -ItemType Directory -Path .cache/f3-e4 -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e4/before.json
docker info --format '{{.OSType}}'
docker compose up -d --pull never --wait postgres
.venv/Scripts/python.exe -m pytest tests/test_independent_cases.py tests/test_model_evaluation.py tests/test_sealed_evaluation.py tests/test_review_source.py -q --basetemp=.cache/f3-e4/pytest-release --tb=short > .cache/f3-e4/release-tests.txt 2>&1
.venv/Scripts/python.exe -m pytest tests/test_counted_probe_evidence.py tests/test_authority_postgres.py tests/test_counted_spending_postgres.py tests/test_spending_postgres.py -q -m integration --basetemp=.cache/f3-e4/pytest-native-final --tb=short > .cache/f3-e4/native-final.txt 2>&1
.venv/Scripts/python.exe -m pytest tests/test_responses.py tests/test_counted_responses.py tests/test_probe_authority.py tests/test_provider_hardening.py tests/test_provider_tls.py tests/test_token_admission.py tests/test_langfuse_local.py -q --basetemp=.cache/f3-e4/pytest-provider-final --tb=short > .cache/f3-e4/provider-final.txt 2>&1
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
docker compose exec -T postgres postgres --version
docker compose stop --timeout 30 postgres
```

| Population/check | Final observed result |
| --- | --- |
| New+legacy scorer/sealed/archive | **237 passed,95.78s**, no skips/errors:77 new+88 common evaluation+54 E2+18 archive |
| E1/native authority/mixed-spending/spending | **153 passed,108.86s**, no skips/errors:51 counted-probe+102 existing native SQL |
| Provider/transport/privacy/live denials/telemetry | **253 passed,9.72s**, no skips/errors |
| Nonduplicated selected denominator | **643 =237+153+253**; repeats not added |
| Frozen baseline | **40/40**,24 development/16 historical held-out; no failures |
| Public model suite | **50 unchanged**,40 development/10 exposed comparison; **150/150 expected handling dispositions**, template hard50, fake/replay hard44 each;12 intended failures preserved |
| Contracts | API/TS check passes; no drift |
| AST/grammar and core preservation | 193 public Python files parse native and3.13; original hard-body AST identical and pinned by test |
| Ruff/whitespace | Lint passes,196 files formatted; diff whitespace check passes |
| Source/candidate/package | Four expected initial-file changes only, nine additions, no deletions; historical candidate and live/financial gates unchanged |

Development runs used basetemps `pytest-first`, `pytest-native`, `pytest-provider`:
224/153/253 passed before the extra adversarial cases and new-facts-only closed
branch. All three batches were rerun after final src/helper/CLI changes; the
affected batch was `pytest-final` (231 passed,124.33s) at that revision. Subsequent
E4-only retention hardening ran `pytest-retention-final` (234 passed,102.14s),
then the final237-test batch above.
The native/provider batches do not import the new experiment and their exact
src/provider/recording dependencies remained unchanged through those last guards.
Repeated populations are not pooled. Initial lint found two unused imports and
missing explicit zip strictness; corrected before acceptance. No frozen fixture
was changed to obtain a pass.

No frontend/build/browser/full-application/hosted run is claimed: these changes
affect offline experiments, not routes/UI/domain/approval. Native SQL/TLS tests
are actual new local reruns, while E4 fixture observations are deliberately
declared unit data. E1's packet omits raw tool arguments by design; E4 does not
reconstruct missing arguments or falsely claim to import an actual native packet.
Actual case-driven execution collection remains a future explicitly scoped task.
The task-started PostgreSQL service was stopped, its volume retained, engine left
running. No user data, deployed resources or historical claims were touched.

## Adversarial review

| Attack or omission | Result / residual boundary |
| --- | --- |
| Rename exposed fixture independent | Origin coupling, exact public input/ordinal mapping and synthetic-only verifier reject; opened facts directly denied too |
| Replace commitments/context/key/index | Full-case/input HMAC, root, fixed nonsecret context, pins and exact current freeze checks reject. This is not human/cryptographic origin attestation |
| Change relevant source without fingerprint update | Recompute raw map and canonical freeze; new experiment modules/study artifacts included. Trusted reviewer must still assess future dependency scope/runtime source custody |
| Forge tool authorization or omit arguments | Existing check_call recomputes capability/argument verdicts; disagreement rejects; truthful denied calls remain common hard failures |
| Valid repair conceals earlier invalid proposal | Response ordinals/proposal coverage required; all verdicts retained and ANDed into unchanged core; repaired plan handling can pass while hard/quality eligibility fails |
| Missing flags/responses/accounting | No inherited true defaults; missing coverage/uncertain or unknown billing yields finite rejection or incomplete/no score, with null totals retained |
| Repeated result replaces unfavorable first | Exclusive fsynced files, concurrent one winner and partial-write blocking tested. Pure scoring can be called repeatedly; no execution authority follows. Actual collection needs durable first-run ownership, not filesystem trust alone |
| Retention substitutes case/variant/provenance | Final audit found the original generic writer lacked identity binding. Result headers now include configuration/selection and case/variant; exact shape/types/synthetic provenance checked before writing, with six new adversarial rejection cases |
| Prune human/missing denominator | Study fixes40 outputs/20 pairs and predeclared reviewer slots; strict version/types reject altered counts. No ratings/importer is implemented and no absence becomes a score |
| Malformed content leaks | Strict bounds/UTF8/no BOM/duplicates/extra-field checks, finite outer errors, opaque repr and canary tests; no new logging/export. Malicious developer/debugger remains outside OS guarantees |
| Synthetic counts promoted real | All receipts/results explicitly synthetic, public control overlap required, no real key/genuine API or live variant accepted. Core source label alone remains data, never execution proof |

Examples in the public projection show a hard pass, preserved intermediate-domain
hard failure after a valid final plan, and incomplete unknown accounting. They are
three distinct unit fixtures, not repeated real attempts or success-rate samples.
No clinical effectiveness, real-model quality, human usefulness or verified billing
claim follows from the tests or numbers.

## Remaining owner decisions and future genuine opening

Owner must review/approve the new contract, exact development selection and its
pairing/denominator policy, then choose actual stable model/configuration and
independent curator/custody/attestation arrangements. Final study freeze remains
unapproved. The final independent ten-case coverage must be checked privately;
the public controls do not fulfill or replace the final ID/tag-exclusion study.

Before any genuine opening, separately review a real unopened-to-opened capability
and authorized collector, human attestation/pin authenticity, exposure history,
canonical case/key verification, independent custody and immutable first-run evidence.
Current source denials are intentional; changing them or the actual study path
changes the configuration and requires a new candidate **before** genuine curation.
Do not silently rebind an old population or use ref strings as permits.

Provider pricing/counting ceiling/retention, monetary/source/privacy/outbound
authorization, human reviewers and any hosted integration remain separate gates.
This milestone does not resolve provider-dependent assumptions or authorize any
next work unit. No live execution, final case creation/opening, human rating or
actual authority can follow merely from acceptance of this handoff.

## Sanitized independent-review package

```powershell
New-Item -ItemType Directory -Path .cache/f3-e4/review -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e4/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e4/review/source-manifest.json --archive .cache/f3-e4/review/future-training-f3-e4-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e4/review/source-manifest.json --archive .cache/f3-e4/review/future-training-f3-e4-review.zip
```

531 public source members plus embedded SHA-256 manifest;193 Python files. All
members verified byte-identical to current working tree; separate zipfile/hashlib
audit checks the embedded map,111 freeze inputs, historical candidate, expected
four changed initial files and nine additions. Verification JSON and ZIP SHA stay
beside the ignored archive. Machine byte verification is not independent human approval.
Exclude credentials/identities/login caches, private cases/keys/reviewers, state/plans,
dependencies, all ignored registries/captures and AGENTS.md. Public-only pattern
scan classifies the unchanged clearly synthetic authentication fixture; no private
directory is scanned. No genuine case, human rating or attestation is packaged.
