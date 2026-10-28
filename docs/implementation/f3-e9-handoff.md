# F3-E9 — Contract-boundary handoff

2026-10-27. **Generalized implementation stopped for contract review.** The
requested audit, offline checks and review package are complete; the proposed
multi-case counted workflow is not implemented or claimed complete.

## Disposition and files

The E9 instruction explicitly requires stopping before a meaningful established
authorization-contract change. Source review and two local synthetic checks show
that E6's fixed profile/receipt/SQL slot is such a boundary. No existing code,
tests, policy or gate was changed; no bypass or parallel execution framework added.

Three new Markdown documents only:

- [Report](f3-e9-report.md): actual restrictions, alternatives, current result
  handling and readiness/critical path.
- [Synthetic binding proposal](f3-e9-synthetic-binding-proposal.md): precise
  additive offline contract, ownership/result semantics and implementation
  acceptance criteria for owner review. It is not ratified.
- This handoff: fresh validation, preservation and exact next boundary.

Owner context is retained: primary20-pair scope with broader protocol separate;
future family-member human-only curation on a separate device after stable final
freeze; public technical AI help only; no curator involvement needed for this
engineering increment. Provider/counting terms and live money remain NO-GO;
AWS is optional and outside the current critical path.

## Technical decision and alternatives

`AuthoritySpec.input_version` is a fixed literal; frozen_assets binds that version.
ProbeSession checks exact profile/revision/text/history. E1 records only an exact
SingleProbe/AuthorityLedger authority_fixture; E6 authenticates only fixture-01 /
ordinal1/replay and claims constant SQL slot1. Changing any into a multi-case
capability requires reviewed binding/lifecycle semantics, even offline.

ResponsesReplay(counted=True) already supports other synthetic profiles and its
ledger is replay-only. It is the recommended implementation foundation, **not a
forbidden transport**. What it lacks is the reviewed case/receipt/pre-send
first-result ownership plus generalized actual E1 observations. E4's ten-case
declared FixtureEvidence is useful but cannot be relabelled as that execution.
No live or financial policy expansion is needed for the proposed replay-only
contract. This distinction avoids both an unsafe probe broadening and a needless
new provider/account infrastructure track.

Review may authorize direct implementation of the proposal; no second exploratory
assessment is recommended. Until then, result aggregation is specified but not
fabricated, and no new retry/claim namespace is operational.

## Exact fresh validation

Windows Python3.14.9, Ruff0.17.2, existing environment. Public/non-final fixtures
only. Tests use the existing socket restrictions and no genuine key/credential.

```powershell
New-Item -ItemType Directory -Path .cache/f3-e9 -ErrorAction Stop
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e9/before.json
.venv/Scripts/python.exe -m pytest tests/test_probe_authority.py tests/test_opening_collection.py tests/test_independent_cases.py tests/test_sealed_evaluation.py tests/test_model_evaluation.py tests/test_review_source.py tests/test_curator_public_rehearsal.py -q --basetemp=.cache/f3-e9/pytest-boundaries --tb=short
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
```

| Check | Fresh observed result |
| --- | --- |
| Existing selected regressions |297 passed,34 native integration cases deselected,154.00s;22 authority +26 pure opening +77 independent-case +54 sealed metadata +88 common evaluation +18 archive +12 curator practice |
| Direct contract checks | Existing ME-D02-30 passed to ProbeSession._payload rejected invalid_request; speculative synthetic-study-cases-v1 rejected by AuthoritySpec; no SQL/transport invocation |
| Frozen baseline |40/40,24 development +16 historical held-out; software evidence, not model quality |
| Comparison assets/results |50 public authored cases;150/150 expected handling dispositions; hard50 template /44 fake /44 replay retained |
| Contracts | No drift |
| Syntax/Ruff |197 public Python files parse native/3.13 grammar; lint passes;200 files formatted |
| Source/docs | All556 task-entry public files unchanged; three Markdown additions; links/UTF8/fences, original hard-rule AST and114 candidate inputs checked |

No new automated test source was needed because implementation stopped before any
code change. The direct checks instantiate only existing synthetic types and use
callbacks that fail on SQL or transport; finite conclusions are recorded in ignored
`.cache/f3-e9/boundary-check.json`. Test output is in boundary-tests.txt and exact
individual check commands/exit codes/output in check-results.json in that directory.
Normal local temporary-file access was used for pytest; no OS policy change.

Native PostgreSQL/TLS/fault tests, frontend/browser/full application, fresh installs
and actual provider behavior were **not rerun**. The34 native E6 cases above are
deselected, not passes. E6/E8 prior SQL/TLS results remain historical evidence.
No Docker service was started. Existing selected tests cover duplicate/conflicting
retention, interrupted/partial synthetic records, source/receipt/provenance mismatch,
missing observations, genuine opening and independent live-denial behavior within
their established scopes; they do not verify the unimplemented new contract.

## Preservation and review ZIP

No private credential, identity, custody, login-cache or historical capture was
read. No genuine data/key, claim, registration, result or human score created.
All historical source/results/candidates/exposure labels/claims and ignored
AGENTS.md are unchanged. Current E6 candidate still matches its114 inputs and is
unapproved; the proposal does not silently enter a ratified freeze.

The ZIP contains559 public working-tree files plus the embedded raw SHA-256
manifest; source byte comparison and a second ZIP/hashlib check validate the
archive and exclusions. This is local mechanical verification, not independent
acceptance of the proposed contract. No private records/caches, AGENTS.md,
Terraform state/plans or future sealed/reviewer/key directories are included.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f3-e9/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f3-e9/review/source-manifest.json --archive .cache/f3-e9/review/future-training-f3-e9-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f3-e9/review/source-manifest.json --archive .cache/f3-e9/review/future-training-f3-e9-review.zip
```

## Precise next owner boundary

Review and, if acceptable, explicitly ratify **only** the proposed synthetic
ten-public-case input/receipt/ownership/result contract and authorize its direct
offline implementation using existing counted replay/SQL/scorer components. Keep
the fixed compatibility authority and E6 behavior intact. Acceptance requires
actual multi-case2/2/4 and3/3/6 evidence plus native duplicate/interruption/unknown
liability tests and the ten-slot summary; no declared fixtures may substitute.

That decision does not approve genuine case handling, final freeze, provider
terms/privacy, positive money, live source release, API execution, curator work,
human ratings or AWS. If it is rejected/deferred, retain the existing working
fixed-control path and report the multi-case increment blocked. No automatic
follow-up, retry, implementation or external operation occurs after this handoff.
