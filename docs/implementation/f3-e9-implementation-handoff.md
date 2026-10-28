# F3-E9 — Bounded replay implementation handoff

2026-10-27. Stop for independent review. No account/provider/AWS request, money,
genuine case/key/custody activity, final freeze approval, installation, commit or
push. Ratification applies only to the synthetic contract in the current task;
the historical proposed/stopped E9 documents are preserved.

## Changed files and integration

| File | Change |
| --- | --- |
| `experiments/counted_probe.py` | Factor pure Observations, accounting_rows and validate_observations; original Rehearsal still performs exact fixed-probe checks |
| `experiments/synthetic_collection.py` | New ten-public-case binding/receipt, fixed replay scope, SQL schedule/claims/results, owned execution, consistency checks and summary |
| `tests/test_synthetic_collection.py` |6 routine +37 native cases |
| `docs/implementation/f3-e9-replay-collection-contract.md` | Implemented ratified offline semantics, trust/durability/privacy limits |
| `docs/implementation/evidence/f3-e9-freeze-candidate.json` | New unapproved118-input freezev4 |
| `docs/implementation/evidence/f3-e9-synthetic-summary.json` | Numerical projection from the passing native ten-case fixture |
| `docs/implementation/f3-e9-implementation-report.md` and this handoff | Outcome, validation, limitations and remaining gates |

One existing public experiment file changed; seven files added. All other558
task-entry public files remain byte-identical, including accepted dirty/untracked
work, all production source, original hard rules, migrations, frozen evaluation
artifacts, historical candidates/reports and claims. AGENTS.md remains ignored and
unchanged. No production schema migration: only two experimental tables inside
fresh disposable integration schemas.

The shared E1 `offline`, `_session`, `run`, `packet` and `persist` ASTs are identical
to the preceding public review snapshot. Observation assembly/SQL numerical
projection/consistency validation are reused; E1's validator selects the checked
manifest case rather than trusting the score's claimed case ID. E6's own code,
fixed receipt/slot, SingleProbe, AuthoritySpec, ProbeSession and both source denials
are unchanged. Native E1/E6 regressions pass. The shared hard-rule AST SHA remains
`0e0cc2ad111b41cc780c90cace86a88844a938ad16276ef942db372cc55bfbd9`.

## Operational offline boundary

Only ten canonical public controls and replay variant are accepted. Constructor
requires exact CountedSpendingLedger and synthetic Issuer; transport is exactly
MockTransport or LocalTLS. Fixed replay project/grant/session must be created by
trusted fixture setup, never automatically by the collector. No arbitrary input,
case path, account routing, credential, live connector or output-directory API.

An exclusive schedule file and fixed SQL header pin one configuration. Each
ordinal has an exclusive fsynced file plus primary-key SQL claim before release.
The SQL claim must acknowledge COMMIT, then source/receipt/deadline are rechecked.
Stable run identity is assigned before reservation. Request-local one-use write
capability prevents unowned internal execution/finalization on new handles.
Counted replay owns paired reservation, claims, limits and uncertainty as before.

The exact Agent generates unpublished results only. Shared observation captures
native proposal/tool/continuation facts, not inferred arguments or expected
success. Read-only native SQL snapshots preserve charged/held/unknown amounts.
Scores are recomputed on readback; invalid stored evidence remains indeterminate.
No recovery writer, reset, retry, queue or worker exists. Same-case duplicates
with the exact current receipt return existing results; another receipt conflicts.
After issuer-memory/window expiry, summary/SQL readback still recovers evidence;
this is not permission to recreate authentication or execute again.

Whole30s includes preflight/claim work. Existing session deadlines are shortened
to that expiry;3/3/6,16k/4k cumulative,2k per attempt,4 reads and admission caps
stand. SQL/evidence cleanup uses5s bounds,3s statement/1.5s lock limits and existing
shield-and-await. Cancellation may drain finalization after the request window;
it cannot send again. A cancellation after an already validated terminal result
may leave a committed completed record, not permission to replay a lost response.

## Exact fresh validation

Windows Python3.14.9 AMD64; pytest9.1.1, Ruff0.17.2, Pydantic2.14.1,
psycopg3.3.6, httpx0.28.1. Docker Linux/PostgreSQL18.6
`Debian 18.6-1.pgdg12+2`, loopback55432. Only cached images; no dependency fetch.

```powershell
New-Item -ItemType Directory -Path .cache/f3-e9-implementation -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e9-implementation/before.json
docker compose up -d --pull never --wait postgres

.venv/Scripts/python.exe -m pytest tests/test_synthetic_collection.py -q -m integration --basetemp=.cache/f3-e9-implementation/pytest-native-verified --tb=short
# 37 passed, 6 deselected; 77.39s

.venv/Scripts/python.exe -m pytest tests/test_counted_probe_evidence.py tests/test_authority_postgres.py tests/test_counted_spending_postgres.py tests/test_spending_postgres.py tests/test_opening_collection.py -q -m integration --basetemp=.cache/f3-e9-implementation/pytest-existing-native --tb=short
# 187 passed, 26 deselected; 240.23s

.venv/Scripts/python.exe -m pytest tests/test_probe_authority.py tests/test_opening_collection.py tests/test_independent_cases.py tests/test_sealed_evaluation.py tests/test_model_evaluation.py tests/test_review_source.py tests/test_curator_public_rehearsal.py tests/test_synthetic_collection.py -q --basetemp=.cache/f3-e9-implementation/pytest-routine --tb=short
# 303 passed, 71 deselected; 188.14s

.venv/Scripts/python.exe -m pytest tests/test_responses.py tests/test_counted_responses.py tests/test_probe_authority.py tests/test_provider_hardening.py tests/test_provider_tls.py tests/test_token_admission.py tests/test_langfuse_local.py -q --basetemp=.cache/f3-e9-implementation/pytest-provider --tb=short
# 253 passed; 13.88s, including the22 authority cases also run above

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

All final commands passed. These are758 distinct selected tests /780 executions,
not the full repository suite. Native224 tests above use real PostgreSQL with
controlled connection/commit faults, not reference-only SQL models. Deselected
cases are not passes. New ten-case execution used MockTransport; existing native
E1/E6 and provider tests re-exercised LocalTLS. Every new case was not separately
executed over TLS. No frontend/build/browser/hosted CI or real provider rerun:
application/UI and production provider source are unchanged.

Frozen baseline40/40 retains24 development/16 historical held-out software cases.
All150 expected comparison dispositions match, with hard50 template /44 fake /44
replay. No snapshot regenerated. Contracts match. Grammar checks cover199 public
Python files natively and under3.13; lint passes and202 files are formatted.

## Observed fault evidence and corrections

| Scenario | Observed outcome |
| --- | --- |
| Ten-profile native acceptance |9 complete/1 intentional repair failure;21/21/42 operations;10 observed/scored; no human scores or business/live writes |
| Concurrent duplicate/new handles | One execution; competing unfinished claim stops; exact completed duplicate reads stored result without transport |
| New receipt window / CWD / wrong config | Cannot replace first result; source/header/receipt mismatch rejects |
| Claim COMMIT lost_after / rollback_uncertain / open_uncertain | Zero sends; retained SQL/file claim or file-only fence; indeterminate, no replay |
| Result COMMIT same three modes | Four operations already occurred; lost_after result readable, rollback/open cases indeterminate; no replacement |
| Restart after acknowledged claim | New OS process reads native summary:1 indeterminate +9 not_started, actual total null; fresh collector cannot execute that case |
| Partial fence / fsync failure / failed result write | Slot stays blocked; no implicit success or retry; missing result remains indeterminate |
| Cancellation / timeout / shutdown | Owned count drains; one local count observed,1000 hold retained; interrupted evidence, no retry |
| Close failure | Explicit cleanup_uncertain, indeterminate;2000 count holds retained |
| Write/owner/invalid tools, refusal, bad model/missing usage | No hard-passing completion; original tool/usage evidence and unresolved costs retained |
| Corrupt score, bool-int substitution, missing flags, false costs, partial JSON, live relabel | Readback summarizes indeterminate with unknown snapshot; never overwrites corrupt original |
| Unowned internal execute/finalize | Rejects before execution or result write; no new claim |

Successful two-generation rows have5540 known simulated charge +2000 holds;
three-generation8310 +3000. Aggregate58,170 +21,000, actual total null. These
are observed native **replay accounting**, not provider billing. Unknown snapshot
slots and known unresolved count holds are distinct; subtotals are explicitly
partial. Body content and private selectors remain absent from the public summary.

Development runs:19 native cases initially passed. An expanded run had34 passes
and2 failures: Windows child-process Proactor loop was incompatible with psycopg;
the close-failure observer lacked a specific cleanup marker. Child readback now
uses asyncio.Runner with SelectorEventLoop, and the actual session close is wrapped
only to record its error before rethrowing. A36-case rerun passed; final37-case
suite adds the owned-capability regression. Development runs are not additional
unique acceptance tests. No timeout, inference limit or original gate was weakened.

## Source, candidate and review package

Freezev4 fingerprint:
`465cc097674593403350750b3af63031c25808a9a9e5fdf2cebc8ff00475b082`.
Two generations match all118 inputs, including ratified proposal, implemented
contract and new test. Historical E2/E4/E6 candidates are byte-identical; the old
current-source fingerprints are stale after the intentional shared-code addition.
No final freeze is ratified. Public summary matches the final tested fingerprint.

Logs, temporary fixtures, fences and second ZIP checks remain ignored under
`.cache/f3-e9-implementation/`. Only fresh disposable schemas were created/dropped;
local fences remain retained. PostgreSQL was stopped, volume retained. Existing
private/historical claims were never inspected or altered.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e9-implementation/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e9-implementation/review/source-manifest.json --archive .cache/f3-e9-implementation/review/future-training-f3-e9-implementation-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e9-implementation/review/source-manifest.json --archive .cache/f3-e9-implementation/review/future-training-f3-e9-implementation-review.zip
```

Archive source members match working-tree bytes and embedded SHA-256 manifest;
private records/credentials/caches, AGENTS.md, state/plans, sealed/reviewer/key
directories are excluded. A separate zipfile/hashlib pass checks all members and
candidate inputs. This is mechanical verification, not independent human approval.

## Remaining gates and limits

No material expansion beyond the ratified synthetic contract was needed. The new
increment is operational offline; it is not a genuine20-pair or model-quality
result. Python-issued nonsecret HMAC receipts and filesystem/DB integrity do not
prove independent custody or resist a malicious process/administrator replacing
storage. Durability evidence covers process restart, not complete power-loss
or adversarial database/workspace replacement. Windows native async SQL requires
a compatible selector loop, as demonstrated by the restart test.

Before genuine study work: settle dormant novel-case validation/authenticated
receipt/custody and per-case live authority, human packet/import source decisions,
then complete source review/final freeze. Provider account/model/count pricing/
maximum/retention/privacy remain external blockers; live money and execution stay
NO-GO. The curator is needed only after stable approved freeze and separate human
appointment/custody/creation authorization. Human judgments remain absent. Local
demo/release work can be separately authorized without AWS, hosted export or a
real model. Stop now for review; no subsequent milestone is authorized.
