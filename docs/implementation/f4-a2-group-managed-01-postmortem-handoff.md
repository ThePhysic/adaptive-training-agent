# F4-A2-group-managed-01 — Offline postmortem handoff

2026-10-27. **Stop for independent review.** No AWS/API or AWS CLI execution,
private historical record/configuration/cache inspection, IAM mutation/grant,
S3/Terraform operation, installation, paid service, executor activation, commit or
push. No retry, alternative AWS diagnosis or live authorization is requested.

## Outcome and evidence

The [stopped-observation record](f4-a2-group-managed-01-stopped-observation.md)
preserves the owner's exact stopped/uncertain result and presence report. It is
owner-attested evidence, not Codex reproduction. Preparation, digest and claim were
reported present; observation and result absent. **The original cause remains
unknown and `outcome_uncertain:true` remains in force.** Neither process release
nor HTTP delivery follows from claim existence. No policy/authentication or
authorization conclusion is inferred. No historical private file was accessed,
modified, deleted, reset or reconstructed.

The [failure-path analysis](f4-a2-group-managed-01-failure-analysis.md) separates
owner evidence, public source reasoning, synthetic measurements and unavailable
historical information. An ordinary allowlist-only failure normally follows
observation persistence; missing artifacts alone still cannot diagnose this case.

## Files changed in this work unit

| Path | Change |
| --- | --- |
| `infra/aws/private_command_runner.py` | Add default-unknown local release/cleanup metadata to Capture; conservatively mark possible release before writer startup; preserve independent cleanup uncertainty when another final status takes precedence |
| `infra/aws/group_policy_inventory.py` | Optional fixed-unit diagnostic context for claim/verification stages; constant typed ValueError-compatible rejection codes; include new helper in reviewed source pins |
| `infra/aws/inventory_diagnostics.py` | New bounded failure value/helper module: finite private codes, coarse public categories, optional exclusive private diagnostic persistence; no launcher |
| `tests/test_inventory_diagnostics.py` | 58 synthetic cases, reusing existing synthetic group fixtures |
| `docs/implementation/f4-a2-group-managed-01-stopped-observation.md` | Owner-attested record, artifact-presence table and limits |
| `docs/implementation/f4-a2-group-managed-01-failure-analysis.md` | Stage/failure/evidence tables, privacy taxonomy and integration limitations |
| This handoff | Scope, actual validation, preservation, packaging and blockers |

The initial public-source snapshot contained 491 files/184 Python files. Its hashes
are retained only in the ignored task cache. Of those initial public files, this
unit changes only the two Python files listed above; it adds five public files and
deletes none. Existing worktree modifications elsewhere are preserved. AGENTS.md
remains ignored and unmodified. The old supervised managed/inline procedures,
historical handoffs, policies, execution fences, approval/application code and
frozen evaluation files retain their initial bytes.

Git context: `group_policy_inventory.py` was already untracked on arrival; the
existing worktree also contains accepted changes from earlier units. The tracked
`git diff -- infra/aws/private_command_runner.py` includes pre-existing syntax
corrections, so it is not an isolated diff for this task. Its current full tracked
diff is 51 additions/9 deletions. The snapshot comparison distinguishes this unit's
two changed existing files from unrelated pending work. No staging occurred.

## Design and safety

The two closed inventory interfaces retain fixed actions/caller/group/endpoint,
exact private identities, independently approved allowlists, source/binary hashes,
private digest, <=30-minute UTC window and durable exclusive claim before capture.
No flag enables live access. No additional AWS command, automatic pagination,
policy-body read, credential fallback, login or retry is introduced.

Capture argv, timeout/byte limits, Windows Job Object ownership, child cleanup and
private I/O protections remain unchanged. New metadata describes local control
flow only. `may_have_released` is set before writer startup; it proves neither
native launch nor HTTP delivery. A context entering capture without a returned
Capture retains conservative possible release and unknown cleanup. A completed
cleanup routine is not independent proof of every OS/service effect.

Private finite codes distinguish parsing, schema, pagination, metadata, unclean
capture, observation/result persistence and supported local stages. Public codes
hide policy-specific distinctions. No raw stdout/stderr, exception text, native
exit number, identifiers, policy values, paths or preparation hashes enter these
reports. There is intentionally no authentication/authorization classifier.
Synthetic canaries in exceptions, output, stderr and unknown statuses do not appear
in tested public/private diagnostic structures or captured console/log sinks.

Diagnostic persistence is optional, bounded, private, exclusive and fsynced.
Storage failure yields `not_saved`; an existing diagnostic is not replaced.
Partial artifacts and all claims remain retained. Diagnostic failure cannot
create success, authorize replay, remove claims or reset the attempt.

**Integration limitation:** the historical supervised procedures are unchanged and
still emit their generic stopped result. The new contexts/helpers are implemented
and exercised synthetically, not silently wired into a new live script. The
analysis specifies source-review ordering for a potential future integration;
it is not a retry procedure. No diagnostic is backfilled for the original attempt.
Changed source pins invalidate old preparations rather than rewriting them.

## Exact validation commands and observed results

Environment: Windows host; Python 3.14.9; Ruff 0.17.2; existing locked environment.
Normal local-user process execution was used for ACL/Job Object fixtures; no OS
administrator change or system/network configuration was made. All identities,
policy metadata and process output in tests are synthetic. Network fixtures in
the selected regression suite are controlled loopback fixtures only.

Commands are run from the repository root:

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-group-managed-postmortem/before.json
.venv/Scripts/python.exe -m pytest tests/test_inventory_diagnostics.py -q --basetemp=.cache/f4-group-managed-postmortem/pytest-diagnostics --tb=short
.venv/Scripts/python.exe -m pytest tests/test_group_policy_inventory.py tests/test_inventory_diagnostics.py -q --basetemp=.cache/f4-group-managed-postmortem/pytest-group-final --tb=short
.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-group-managed-postmortem/pytest-regression --tb=short
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
```

| Check | Observed result |
| --- | --- |
| Initial public snapshot | 491 files, 184 Python files; passed |
| Preliminary diagnostic suite, before three additional process-fault cases | 55 passed in 27.76s |
| Final fixed group contracts + diagnostics | 160 passed in 256.06s: 102 existing + 58 new |
| Selected private runner/identity/ownership/boundary/tunnel/source regressions | 260 passed in 12.81s |
| Final nonduplicated test denominator | 420 passed; no failures/skips reported |
| OpenAPI/TypeScript contract check | Exit 0; no drift |
| Frozen baseline | 40/40; development 24/24, held-out 16/16; no failed cases |
| Public Python AST/grammar | 186 files pass native and Python 3.13 parsing |
| Ruff lint | All checks passed |
| Ruff formatting | 189 files already formatted |
| Git whitespace | Exit 0 |

An initial local Ruff run rewrote three new exception tuples into Python 3.14-only
syntax; the grammar checker caught it. They were made multiline parenthesized
tuples and rechecked before tests. Initial new-test lint also found fixture-import
shadowing; reuse now uses explicit fixture aliases. Final checks above pass.
These development failures are not evidence about the stopped AWS invocation.

New cases cover finite-code/privacy mapping; conservative release and unknown
cleanup; cancellation/KeyboardInterrupt/timeout; actual synthetic child success,
timeout, cancellation and overflow; injected wrapper Popen failure; nonzero exit,
stderr and unknown native exit without auth guessing; duplicate-key JSON, malformed
schema, truncation, invalid/unexpected policy metadata; observation/result and
diagnostic persistence failure; partial claim failure and blocked reuse; cross-unit
context rejection and stage reversal. Existing regressions add concurrent exclusive
claim, fsync failure, owned descendant cleanup and unrelated-sibling preservation.
Synthetic Capture-state tests are distinguished from real local Python-child tests
in the test names. Neither verifies native AWS CLI or AWS service behavior.

No PostgreSQL, installed-browser UI, frontend build, account-connected test or full
application suite was run: application/frontend/schema code is unchanged. The 420
denominator is the selected suites above, not every project test. No Terraform
command was executed.

## Review archive

The existing `scripts/review_source.py` process packages the complete public
working-tree snapshot, including pending public changes. It excludes AGENTS.md,
ignored/private directories, AWS/login caches, credentials, private identities,
state/plans, dependencies and other review ZIPs. It embeds raw-byte SHA-256 hashes
in `_review/source-manifest.json` and verifies every member against the current
working tree. No historical private directory is included or scanned.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-group-managed-postmortem/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-group-managed-postmortem/review/source-manifest.json --archive .cache/f4-group-managed-postmortem/review/future-training-f4-group-managed-postmortem-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-group-managed-postmortem/review/source-manifest.json --archive .cache/f4-group-managed-postmortem/review/future-training-f4-group-managed-postmortem-review.zip
```

The public ZIP is additionally checked for prohibited member paths and common
access-key/secret-key/private-key patterns; synthetic test fixtures are public
source, not real credentials. Pattern checks are an additional bounded check, not
proof of all possible secret detection. Verification metadata and ZIP SHA-256 are
retained beside it in the ignored review directory. No source file contains its
own archive hash.

## Remaining blockers and next boundary

The historical cause cannot be resolved from the permitted evidence. No supported
finding identifies authentication, AWS denial, HTTP delivery or policy contents.
Independent review of this offline postmortem is the only proposed next task.
There is no immediate retry, fresh invocation directory, alternative AWS request,
live authorization request or IAM correction recommended in this unit. All prior
effective-permission, boundary, native refresh, MFA/HTTP-count and Windows-egress
limitations remain. Stop here.
