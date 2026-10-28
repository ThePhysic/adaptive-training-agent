# F3-E6 — Independent-review handoff

2026-10-27. Offline implementation only. Stop for independent review; no next
milestone, genuine case handling, freeze approval, network or money authorized.
Read the [report](f3-e6-report.md) and normative
[opening/collection contract](f3-e6-opening-and-collection-contract.md).

## Exact additions and preservation

- `experiments/opening_collection.py`: fixed synthetic receipt/capability,
  immutable commitment checks, additive freezev3, bounded SQL claim/readback and
  E1 recorder/common-scorer integration. Genuine opening always denies.
- `tests/test_opening_collection.py`:26 pure and34 native integration cases.
- `docs/implementation/f3-e6-opening-and-collection-contract.md`: normative
  supported slot, trust assumptions, persistence, uncertainty and approval gates.
- `docs/implementation/f3-e6-report.md`: implementation/outcome summary.
- `docs/implementation/f3-e6-handoff.md`: this handoff.
- `docs/implementation/evidence/f3-e6-freeze-candidate.json`: new, unapproved
 114-input candidate; fingerprint
 `f938f33dfe9c0e5fc1029d005f099ad3f2f63d3d790671e4d4de209c197a90e7`.

All535 public files present at task entry are preserved byte-for-byte, including
accepted dirty/untracked source and E2/E4 candidates. AGENTS.md remains ignored
and unchanged. No original hard-rule, dataset, historical score, exposure label,
AWS claim, production source, lockfile or policy changed. No application migration.
Only the disposable test schema receives `experiment_e6_first`; existing fixture
teardown removes that schema. Synthetic local fences remain in ignored `.cache/`.

## Architecture and evidence boundaries

Preparation verifies ten canonical public-control bytes, input/content HMACs,
ordinals, population root, exposure pins, current source and selection. A separate
issued receipt authenticates exact operation/case/configuration/financial binding
and a <=30-minute UTC window without changing those bytes. Both keys are public
synthetic test constants. An unsigned reference or caller provenance string grants
nothing. Actual independent custody and human authorization are not implemented.

Execution supports only the existing fixed ordinal1/replay compatibility profile.
The fresh simulation authority, exclusive fixed-schema fence, constant SQL primary
key and acknowledged COMMIT precede Rehearsal.run. A stable logical identity is
derived from bindings, not supplied as a retry identifier. Schema checks exclude
application/public state. There is no output-directory selector or retry API.

E1 records actual native proposal/tool verdicts, continuation results, terminal
outcomes and read-only SQL liabilities. E6 retains that packet and reuses shared
ScoringFacts/score_facts. It does not invent unavailable raw arguments. The wrapper
binds exact receipt and claim metadata; readback validates both and recomputes
scores. A valid final plan cannot conceal an intermediate hard failure. Incomplete
or drifted evidence has no common score; financial unknowns never become zero.

Whole-request30s includes claim work. Existing shared deadlines are only shortened;
3-count/3-generation/6-combined, input/output/tool/repair/concurrency and native
reservations are unchanged. Owned SQL finalization is shielded and awaited with
5s bounds plus3s statement/1.5s lock limits. Exceptions do not reset a claim.

## Exact fresh validation

Windows / Python3.14.9 AMD64; pytest9.1.1; Ruff0.17.2; httpx0.28.1;
psycopg3.3.6; Pydantic2.14.1. Docker Linux engine; PostgreSQL18.6
`Debian 18.6-1.pgdg12+2` on loopback55432. No external network/test credentials.

Commands run from repository root. Native tests use unique existing test schemas,
not a reference-only transaction model. Each listed test command exited0.

```powershell
docker info --format '{{.OSType}}'
docker compose up -d --pull never --wait postgres
docker compose exec -T postgres postgres --version

.venv/Scripts/python.exe -m pytest tests/test_opening_collection.py -q -m integration --basetemp=.cache/f3-e6/pytest-native-final --tb=short
# 34 passed, 26 deselected; 105.10s

.venv/Scripts/python.exe -m pytest tests/test_independent_cases.py tests/test_model_evaluation.py tests/test_sealed_evaluation.py tests/test_review_source.py tests/test_opening_collection.py -q --basetemp=.cache/f3-e6/pytest-evaluation-final --tb=short
# 263 passed, 34 deselected; 166.38s

.venv/Scripts/python.exe -m pytest tests/test_counted_probe_evidence.py tests/test_authority_postgres.py tests/test_counted_spending_postgres.py tests/test_spending_postgres.py -q -m integration --basetemp=.cache/f3-e6/pytest-accounting-final --tb=short
# 153 passed; 124.26s

.venv/Scripts/python.exe -m pytest tests/test_responses.py tests/test_counted_responses.py tests/test_probe_authority.py tests/test_provider_hardening.py tests/test_provider_tls.py tests/test_token_admission.py tests/test_langfuse_local.py -q --basetemp=.cache/f3-e6/pytest-provider --tb=short
# 253 passed; 11.28s

.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
.venv/Scripts/python.exe scripts/review_source.py check
git -c core.safecrlf=false diff --check
```

Contracts match; baseline24/24 development +16/16 historical held-out. Historical
held-out software results are not unseen model-quality results. Preparation
retains50 authored /40 development /10 exposed comparison cases. Comparison
retains150/150 expected handling dispositions, hard passes template50/50,
fake44/50 and replay44/50; no invented quality ratings. Ruff passes;198 files
formatted;195 public Python files parse natively and under3.13 grammar. Earlier
development runs also passed26 pure and28 native cases; they are not additional
unique tests in the703 total. Frontend/browser, full application integration,
hosted CI, AWS and real-provider tests were not run: no corresponding code changed
or execution authorized. No performance/generalization claim follows from timings.

## Adversarial and fault evidence

| Tested boundary | Observed outcome |
| --- | --- |
| Original byte preservation; forged/stale receipt; wrong case/ordinal/study/selection/source/financial binding | Opening rejects or retains identical committed bytes; genuine openers still deny |
| MockTransport and LocalTLS; continuation and repair | Four positive executions:2/2/4 or3/3/6. Repair handling succeeds but earlier rejection prevents hard pass |
| Unknown tools/write/owner-bearing/invalid arguments; refusal | Actual rejected attempts retained, no quality success; no approval publication |
| Missing proposal evidence/accounting; drift after execution | Incomplete, common score null; missing liability snapshot remains unknown |
| Three native initial-COMMIT faults: lost_after, rollback_uncertain, open_uncertain | Zero transport releases; fence persists and new handle cannot replay |
| Same three result-COMMIT faults | Four operations observed; lost_after result readable, others claimed_unknown; holds preserved and replacement denied |
| Concurrent handles; new receipt; different financial identity; changed working directory | One first execution; replacement/readback mismatch rejected |
| Process restart after claimed commit | New Python process observes real SQL claimed_unknown; restarted collector cannot execute |
| Partial fence write/fsync fault; public schema | Retained partial fence prevents reuse; non-test schema rejected before experimental DDL |
| Cancellation, repeated cancellation, deadline, emergency shutdown | Count task drains; owned finalization awaited; unresolved1000 count hold or claimed_unknown retained; no automatic replay |
| Stored score/body/provenance/bool-int manipulation | Strict readback validation rejects; incomplete data cannot receive passing score |
| Existing TLS/privacy/canary/live-denial tests | Local-only transport and existing sinks remain isolated; no new logging/export sink added. New outer failures are finite and redact synthetic canaries |

Two-generation fixtures retain known simulated charge5540 and holds2000;
three-generation fixtures8310 and3000. Actual total is null because counting is
unpriced. These are independently observed native fixture rows, **not verified
provider prices or bills**. Original hard-rule AST SHA-256 remains
`0e0cc2ad111b41cc780c90cace86a88844a938ad16276ef942db372cc55bfbd9`.

## Source integrity and review package

The task-entry snapshot is ignored `.cache/f3-e6/before.json`. A new source
snapshot, archive and verification use the accepted `scripts/review_source.py`
workflow under `.cache/f3-e6/review/`. The ZIP contains current public source plus
embedded `_review/source-manifest.json`; excluded paths include AGENTS.md,
credentials/caches, state/plans, private evaluation/reviewer/key directories and
ignored artifacts. An additional zipfile/hashlib pass checks every source byte,
manifest digest, task-entry preservation and every freezev3 input. This is a second
local mechanical check, not independent human acceptance. See ignored verification
output and ZIP SHA-256 sidecar supplied with the package.

## Remaining limitations and next approval boundary

This is a fixed public-control rehearsal. Genuine receipt authentication/custody,
case-specific authority and multi-case collection remain absent, deliberately.
No claim is made about hostile same-process developers, DB/workspace-admin
tampering, OS isolation or full machine-power-loss recovery. The two storage
fences conservatively prevent supported process-restart replay; they do not prove
storage that failed before any bytes were written. Detailed synthetic packets
stay local; normal logs/traces receive no new content.

Historical candidates are preserved; E6 necessarily makes E4's old current-source
fingerprint stale. Freezev3 is reproducible but unapproved. Final model/settings,
provider compatibility, verified counting ceiling/retention and privacy evidence
remain external blockers. Synthetic charges cannot create positive money.

**Next boundary:** independently review this exact source and fixed-slot contract.
Owner must then separately decide genuine receipt authentication/custody and
case-specific authority design before authorizing any further implementation.
Final source/freeze, curator appointment, genuine creation/registration, genuine
opening, provider/privacy terms, numerical monetary limits, actual study execution
and human-review collection remain distinct approvals. No live authorization is
requested, and no execution gate is activated by this handoff.
