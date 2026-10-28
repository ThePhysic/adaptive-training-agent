# F3-E10 — Synthetic blinded review handoff

2026-10-27. Stop for independent review. No genuine human/curator/case/key activity,
real trust anchor, provider/AWS/hosted request, spending, final freeze, installation,
commit or push. Existing E6/E9 authority and first-result contracts are unchanged.

## Exact additions

- `experiments/blinded_review.py`: fixed public packet builder, operator binding,
  strict dummy Submission, exclusive import journal and separated reporting.
- `tests/test_blinded_review.py`:6 routine +23 native cases.
- `docs/implementation/f3-e10-review-contract.md`: bounded synthetic-only packet,
  first-valid-import and reporting semantics.
- `docs/implementation/evidence/f3-e10-freeze-candidate.json`: new unapproved121-input
  freezev5; older candidates are preserved.
- `docs/implementation/evidence/f3-e10-dummy-report.json`: numerical projection from
  the final passing native demonstration, not a genuine evaluation result.
- `docs/implementation/f3-e10-report.md` and this handoff.

Seven additions, zero existing public files modified/deleted. All566 task-entry
files, including accepted dirty/untracked code and old evidence, remain identical.
No source/schema/rubric/hard-rule/approval/provider/financial change. AGENTS.md is
untouched and ignored. No production migration or extra service; only fresh
`experiment_e10_packet`, `experiment_e10_reviews`, `experiment_e10_events` tables
in existing disposable native test schemas.

## API and reproducible demonstration

Construct `Review` only from an exact E9 Collection. Existing trusted fixture setup
owns the replay project and public executions. `initialize()` creates experimental
tables; `issue()` pins one exact automation snapshot and deterministic packet;
`export()` returns reviewer content only; `blanks()` returns pending dummy forms;
`submit(bytes)` validates and imports explicitly marked dummy ratings/abstentions;
`report()` separates automated, dummy and absent genuine evidence. There is no
case-path loader, real reviewer registry, generic execution CLI or genuine import.

Reviewer content has preferences, human-readable plan days under A/B, opaque pair
IDs and rubric ID. Only the operator bundle contains source/case/variant/score
mapping and evidence pins. Neither automated verdicts nor expected judgments enter
the view. Two dummy labels across10 public pairs define40 practice slots; real
reviewer allocation is unknown, and the10 unopened independent pairs have no
fabricated records or content. Public data/seed prevent any claim of guaranteed
blindness against an informed reviewer. No signing key is created.

The full demonstration is the native test
`test_full_synthetic_packet_import_report_demo`: ten actual E9 runs, actual template
counterparts, deterministic issue/export, two scripted rated forms, one abstention,
an identical duplicate, conflict and invalid/provenance-escalation rejections,
then a consolidated report. The42 logical mocked provider operations do not
increase during packet/review handling. All genuine-human metrics remain absent.

To reproduce **only** that demonstration after local PostgreSQL startup, run the
same test by node ID with `-m integration` and a fresh local basetemp; the acceptance
command below ran it as part of all23 native E10 tests. It uses only existing
public fixtures/nonmonetary replay grants and never asks for credentials. Generated
numerical evidence is in ignored `.cache/f3-e10/evidence/`; runtime packets/maps are
not copied into the public source archive.

## Persistence and fault semantics

One fixed SQL packet key and exclusive file pin prevent changed packet IDs or
directories from replacing an issue. Import validates source/selection/snapshot,
packet, hidden A/B mapping, rubric and dummy schema before claiming a slot. Existing
validate_ratings is authoritative for rated values; pending/null fields do not
become scores. Snapshot/source is rechecked after waiting behind the SQL claim.

Each `(ordinal,A/B,dummy reviewer)` first valid import has an exclusive fsynced
file, acknowledged SQL claim, then owned update-once JSON commit. Exact committed
duplicates read; conflicts reject; partial/uncertain/corrupt records remain
indeterminate. Rejected invalid forms do not create an accepted judgment and may
be corrected only while no slot claim exists. No record/claim reset or replay API.
Finalization is an internal closure over validated data, not a public result writer.

Invalid/conflicting/duplicate events contain finite classifications only, bounded
by a noncycling128-event sequence. Counts describe **persisted events**, not a
guaranteed complete history when audit storage fails; an unavailable/full audit
raises and does not authorize a judgment. An indeterminate import is never resumed
by readback. SQL operations use existing5s/statement3s/lock1.5s bounds and
shield-and-await ownership. No raw submission, error input, credential or private
identity is logged by the new code.

If automated results change after issue, the snapshot check stops imports/reporting
instead of silently enlarging or changing the packet. Stop automation before issue.
Old records remain intact; no automatic new packet/study/directory workaround.

## Exact fresh validation

Windows Python3.14.9 AMD64; pytest9.1.1/Ruff0.17.2, existing pinned dependencies.
Docker Linux/PostgreSQL18.6 `Debian 18.6-1.pgdg12+2`, loopback55432. Cached image
only, no package installation or external request.

```powershell
New-Item -ItemType Directory -Path .cache/f3-e10 -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e10/before.json
docker compose up -d --pull never --wait postgres

.venv/Scripts/python.exe -m pytest tests/test_blinded_review.py -q -m integration --basetemp=.cache/f3-e10/pytest-native-final --tb=short
# 23 passed, 6 deselected; 93.20s

.venv/Scripts/python.exe -m pytest tests/test_synthetic_collection.py tests/test_counted_probe_evidence.py tests/test_authority_postgres.py tests/test_counted_spending_postgres.py tests/test_spending_postgres.py tests/test_opening_collection.py -q -m integration --basetemp=.cache/f3-e10/pytest-existing-native --tb=short
# 224 passed, 32 deselected; 268.09s

.venv/Scripts/python.exe -m pytest tests/test_blinded_review.py tests/test_synthetic_collection.py tests/test_probe_authority.py tests/test_opening_collection.py tests/test_independent_cases.py tests/test_sealed_evaluation.py tests/test_model_evaluation.py tests/test_review_source.py tests/test_curator_public_rehearsal.py -q --basetemp=.cache/f3-e10/pytest-routine-final --tb=short
# 309 passed, 94 deselected; 125.14s

.venv/Scripts/python.exe -m pytest tests/test_responses.py tests/test_counted_responses.py tests/test_probe_authority.py tests/test_provider_hardening.py tests/test_provider_tls.py tests/test_token_admission.py tests/test_langfuse_local.py -q --basetemp=.cache/f3-e10/pytest-provider --tb=short
# 253 passed; 11.61s; includes22 authority cases also in routine suite

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

All final checks passed:809 test executions /787 distinct selected tests, including
247 in native PostgreSQL suites. Deselections are not passes; this is not the full
repository/application/hosted-CI suite. SQL tests use actual migrations/connections
with controlled commit faults, not reference-model-only transactions. New packets
used MockTransport replay; existing suites re-exercised LocalTLS/provider denials.
No frontend/build/browser rerun because application/UI code did not change.

Baseline40/40 remains24 development/16 historical held-out software cases. All150
comparison dispositions match; hard50 template /44 fake /44 replay, no fabricated
quality. Contracts match.201 public Python files parse native/3.13 grammar; lint
passes;204 files formatted. Original hard-rule AST hash is unchanged.

## Observed fault evidence

| Scenario | Observed result |
| --- | --- |
| Deterministic issue/build/export | Identical packet/commitment;9 eligible pairs from19 hard-passing outputs/1 retained repair failure; no automated source/verdict metadata in content |
| Dummy import arithmetic |2 rated+1 abstention;33 missing+4 ineligible;40 slots/120 dimensions retained. Dummy mean4, genuine quality null |
| Wrong case/packet/rubric, range/type/fields, genuine relabel | Rejected with finite error; no accepted slot. Invalid attempts counted separately |
| Same/conflicting/concurrent import | Accepted once; exact duplicate recognized; conflict/in-flight contender cannot replace it |
| Claim/result lost_after, rollback_uncertain, open_uncertain | Six native fault cases preserve committed result or indeterminate claim/fence. No resubmission completes an unknown claim |
| Corrupt result/partial file/fsync failure | Indeterminate, not a rating; original state remains blocked |
| Cancellation and new-process restart | Actual SQL pending claim read by new process; no valid/genuine score invented and retry blocked |
| Source/selection/packet/snapshot drift, including during claim wait | Further import rejected; no silent packet or judgment replacement |
| Failed audit | Error surfaced; no judgment inferred/accepted; persisted-event coverage limitation retained |
| Missing automation | No pair exposed;10 actual templates and10 missing replay outputs remain distinct; no dummy/genuine judgment |
| Uncertain packet issue | Lost commit acknowledgment reads existing issue; absent/uncertain issue plus retained fence cannot create another namespace |
| Live/financial/genuine denials | Existing E6/E9/provider regressions pass, source unchanged; explicit genuine review import denies |

Initial two-case smoke passed. Initial full native run had22 passes/1 failure:
the fresh readback child exceeded its20s test bound. A separate no-SQL cold check
measured imports1469ms, Collection source check2020ms, Review check2170ms and
repeated check4372ms, total10387ms. This establishes source-discovery overhead,
not a recovered diagnosis of every scheduling/storage event behind the timeout.
The child now independently enumerates validated public paths once, like existing
test fixtures; every freeze still rehashes actual bytes. No parent hashes, results
or authorization are trusted in place of child checks.20s child bound, inference
deadline, SQL limits and runtime importer remain unchanged. The corrected full
native suite passed; earlier failed/development runs are not extra acceptance tests.

## Integrity, package and remaining gates

Freezev5 fingerprint:
`f0cb43f9f2792cecdb63593e3e86607b01753a205fc025e99a835fbcfcb0ca13`.
Two generations match121 current source inputs. This includes the review contract,
new test and existing rubric/scorer dependencies. Historical E2/E4/E6/E9 candidates
remain identical; their earlier current-source fingerprints are intentionally stale.
The demonstration matches the new candidate, which is not approved for a study.

Ignored logs, timing, numerical evidence and integrity/ZIP verification are under
`.cache/f3-e10/`. PostgreSQL was stopped and its volume retained. Fresh fixture
schemas were dropped by existing teardown; synthetic fences remain retained.
No historical private record, identity, credential, login cache or claim was read.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e10/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e10/review/source-manifest.json --archive .cache/f3-e10/review/future-training-f3-e10-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e10/review/source-manifest.json --archive .cache/f3-e10/review/future-training-f3-e10-review.zip
```

Source members/manifest match working-tree bytes; an additional ZIP/hashlib pass
checks exclusions and121 candidate hashes. Runtime packets, maps and raw ratings
are excluded, as are credentials/caches, AGENTS.md, state/plans and reserved genuine
evaluation/reviewer/key paths. Mechanical verification is not independent review.

This completes the bounded public synthetic review increment without weakening an
existing ownership contract. It does not establish real reviewer identity, honesty,
independence, OS custody/containment, production/multi-worker behavior or power-loss
recovery. Public data/seed permit reidentification; actual real-study blinding and
genuine authentication need separate review. No dummy-only signing label can grant
that authority. Windows async SQL uses the tested selector loop in the restart child.

The next useful implementation can be a separately authorized local demonstration/
release polish. Before genuine evaluation, resolve dormant novel-case and genuine
review provenance interfaces/source decisions, final freeze, human custody and
creation/collection gates. Provider counting/account/privacy/money clearance stays
NO-GO. Curator participation remains deferred. Optional AWS/hosted/judge/new-service
work is not required for this path. Stop now; no subsequent work is authorized.
