# F4-A2 group inventory — Diagnostic integration handoff

2026-10-27. **Offline only. Stop for independent review. No live authorization.**

## Result and scope

The [concise report](f4-a2-group-diagnostics-integration-report.md) summarizes the
integration into the two existing supervised procedures. The original
[managed stopped observation](f4-a2-group-managed-01-stopped-observation.md),
[failure analysis](f4-a2-group-managed-01-failure-analysis.md) and
[postmortem](f4-a2-group-managed-01-postmortem-handoff.md) remain historical records,
unchanged. Their documented lack of integration describes the earlier revision;
the new procedure revision notices explicitly distinguish this update.

Original owner-attested result remains:

```json
{"checkpoint":"F4-A2-group-managed-01","result":"stopped","outcome_uncertain":true}
```

Preparation/digest/claim were reported present, observation/result absent. Cause,
native execution and HTTP delivery remain unknown. Codex did not inspect any of
those artifacts, identities, configurations, credentials, caches or raw responses.
No historical preparation/claim was modified, no attempt was replayed, and no new
real preparation was made. No AWS CLI, authentication, API, IAM/S3/Terraform,
provider, spending, telemetry, installation, commit or push operation occurred.

## Files and design

| File | Change in this unit |
| --- | --- |
| `infra/aws/inventory_diagnostics.py` | Buffer-clear helper; latched cleanup uncertainty; contain diagnostic storage BaseException, including cancellation/interruption |
| `infra/aws/group_policy_inventory.py` | Use the diagnostic-aware clear helper in verification's existing finally path |
| `docs/implementation/f4-a2-group-managed-01-supervised-procedure.md` | Integrate fixed Managed diagnostic flow and revision/privacy/one-shot notes |
| `docs/implementation/f4-a2-group-inline-01-supervised-procedure.md` | Independently integrate fixed Inline flow with its own authorization/environment/unit |
| `tests/test_group_policy_inventory.py` | Existing mocked procedure wrapper forwards the optional diagnostic context to the real claim method |
| `tests/test_group_inventory_workflows.py` | New exact-document synthetic workflow tests, including concurrency and reporting double faults |
| `docs/implementation/f4-a2-group-diagnostics-integration-report.md` | Concise implementation report |
| This handoff | Detailed validation, adversarial review, limits and review archive |

No change to private_command_runner.py, process ownership, argv, capture limits,
credentials, validators, policy scopes, application code, dependencies or execution
fences was needed. Existing fixed Managed/Inline interfaces remain separate;
neither invokes the other. There is no new executable entrypoint or live flag.

The initial public-source snapshot was 496 files/186 Python files. This unit
changes five existing public files listed above and adds three, deleting none.
The repository already has unrelated accepted tracked/untracked changes; they are
preserved, not staged. Snapshot hash comparison isolates this unit from those
changes. AGENTS.md remains ignored and unmodified. Historical records, policies,
fences, frozen artifacts and all unrelated public files retain their initial bytes.

## Integrated order and security invariants

1. The PowerShell block retains its separate literal authorization checkpoint,
   masked independently approved digest entry and fixed workflow selection. No
   approval or live operation was exercised in this task.
2. Python marks pre-release review before reading the private root/digest and
   calls the existing fixed interface's claim with the diagnostic context. Exact
   caller/group identity, source/binary hashes, selected configuration, independent
   expectations, preparation digest and <=30-minute UTC window checks remain.
3. `claimed` becomes true only after exclusive claim creation, private verification
   and durability steps return. Failed/partial claims retain their file. That
   local boolean is diagnostic-write ownership, not AWS execution authority.
4. Command/environment are constructed before `begin_capture`. Possible release
   is marked before entering the existing owned capture. Returned metadata can
   establish local not-released or possible-release status. An escaping exception
   conservatively retains possible release/unknown cleanup. No status proves an
   HTTP request, MFA, refresh behavior or account identity.
5. Existing strict response validation/persistence runs with the context. No
   relaxed schema, pagination, count/byte limit, policy identity or allowlist rule.
   Well-formed unexpected observations are still retained before rejection.
6. Verification's buffer clear and the supervisor's final clear are diagnostic-aware.
   A failed clear latches cleanup uncertainty and fails the workflow. A second
   successful clear cannot turn that failure into success or erase uncertainty.
   Native ownership/cleanup still belongs to capture_owned; buffer clearing is
   not a replacement for OS cleanup or a secure-erasure guarantee.
7. Only a failure-free generation of the sanitized result **and** completed buffer
   cleanup reaches the exclusive result write. Any result-write/flush/fsync/ACL
   exception stops. A partial or even fully written file can remain after a
   storage error; existence alone is not successful terminal evidence.
8. On failure, private diagnostic persistence is attempted only if this invocation
   acquired the claim. A blocked loser, failed review or partial claim gets only a
   finite public report. It must not write into an attempt it did not acquire.
9. Diagnostic writes use the existing <=64KiB private, exclusive fsynced writer;
   actual records contain only bounded finite fields. Storage errors, cancellation
   and interruption yield `not_saved`, preserving the original failure. Existing
   or partial diagnostic files are never overwritten. A reporter-level exception
   triggers literal stopped/uncertain/unknown fallback with conservative cleanup
   uncertainty. No raw exception, output, path, account/group/policy identifier,
   credential or preparation hash is printed.
10. Every failure exits nonzero and preserves the claim. There is no loop, replay,
    reset, new directory, login, follow-up read or second capture. Outer PowerShell
    failure propagation remains. Success or failure authorizes neither workflow.

Public codes remain broader than private codes: malformed, incomplete and
unexpected policy metadata share `response_validation_failed`. No public failure
reveals an unexpected policy name/count. Private finite code/stage/capture-status
are control-flow evidence only. Native exit/stderr are not interpreted as IAM
denial or expired credentials. Capture budgets remain 120 seconds plus existing
bounded cleanup, stdout 64KiB, stderr 4KiB; no capture/retry/ownership change.

## Adversarial review

| Attack/fault | Enforced behavior and observed synthetic evidence |
| --- | --- |
| Wrong digest/identity/source/binary/unit, expired window, poisoned config/shared credentials | Stops before capture; no claim or diagnostic write |
| Partial claim or exception after claim write | No capture; claim retained; no diagnostic-write ownership assumed; reuse blocked |
| Concurrent invocation | Winner held at a barrier; loser cannot capture or write diagnostics; winner completes with exactly one capture total |
| Wrapper/ownership failure, deadline, cancellation, interruption, escaping capture error | Finite stopped result; conservative local release/cleanup fields; claim retained |
| Nonzero/unknown exit, stderr, overflow | No observation/success; no auth inference; buffers cleared |
| Duplicate-key/invalid JSON, schema/pagination/metadata rejection | No verified observation promoted; no follow-up request |
| Unexpected well-formed policy | Observation persisted privately, allowlist rejects, public code reveals no identity |
| Observation/result write failure before/after partial/full write | Stops; retained partial/full artifacts cannot authorize another capture |
| Failed first clear, repeated clear failure, late completed cleanup metadata | No success persistence; cleanup uncertainty remains latched |
| Diagnostic failure, interruption, partial/full write followed by exception, existing diagnostic | Stops; no overwrite/retry; original failure retained where reporting operates |
| Reporter itself fails | Fixed conservative stopped fallback; no traceback/exception contents printed |
| Repeated invocation after any claimed failure or success | No second capture; file bytes unchanged, including retained claim/result/diagnostic |
| Sensitive synthetic canaries in capture/stderr/exceptions | Not present in public reports, captured stderr or log sinks; diagnostic structures contain finite values only |

The new tests execute the **exact second Python heredoc** in each Markdown procedure
with a mandatory mocked capture installed first, real exclusive temporary-file
writes and deterministic events. Their bulk fixture bypasses OS ACL attestation
only on its synthetic temporary paths to isolate workflow logic; it does not
claim ACL or native CLI proof. Existing inventory/security regressions separately
exercise normal-user Windows private ACL, Job ownership, actual local Python
children, loopback fixtures, exclusive/concurrent claims and cleanup. No test
invokes aws.exe or reads the real cache. PowerShell checks parse blocks only.

## Validation

Environment: Windows, existing Python 3.14.9 and Ruff 0.17.2. Normal local-user
fixture access only; no administrator/system security/network changes.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-group-diagnostic-integration/before.json
.venv/Scripts/python.exe -m pytest tests/test_group_inventory_workflows.py -q --basetemp=.cache/f4-group-diagnostic-integration/pytest-workflows --tb=short
.venv/Scripts/python.exe -m pytest tests/test_group_inventory_workflows.py -q --basetemp=.cache/f4-group-diagnostic-integration/pytest-workflows-final --tb=short
.venv/Scripts/python.exe -m pytest tests/test_group_policy_inventory.py tests/test_inventory_diagnostics.py -q --basetemp=.cache/f4-group-diagnostic-integration/pytest-group-regression --tb=short
.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-group-diagnostic-integration/pytest-security-regression --tb=short
.venv/Scripts/python.exe scripts/export_contracts.py --check
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
.venv/Scripts/python.exe scripts/review_source.py check
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check src tests scripts infra experiments
git -c core.safecrlf=false diff --check
```

An initial new-workflow run had 82 passing/2 failing tests because its reuse assertion expected the normal
diagnostic status even when the reporter was deliberately monkeypatched to throw.
The fixed fallback correctly reported `not_saved`; the test now expects that value
for this double-fault case. Claim retention, unchanged files, nonzero exit and
unchanged capture count assertions remain. Added cases also cover binary/unit/
shared-credential mismatch and existing diagnostic files. Final workflow suite:
**92 passed in 7.86s**. Fixed group/diagnostic regression: **160 passed in 332.11s**
(102 accepted group cases plus 58 accepted diagnostic cases). Security regression:
**260 passed in 13.43s**. Final nonduplicated selected denominator: **512 passed**,
no failures or skips reported in the final runs. The preliminary run is not added
to that denominator. Existing procedure compatibility includes Python 3.13 grammar
and parse-only Windows PowerShell syntax checks for both document blocks.

Contract export: exit 0/no drift. Frozen baseline: **40/40**, development 24/24,
held-out 16/16, no failed cases; software evidence, not real-model/fitness evidence.
Public AST check: 187 Python files pass native and Python 3.13 grammar. Ruff lint:
all checks pass; formatting: 190 files already formatted. Git whitespace: exit 0.
Full application/PostgreSQL/frontend/browser-build checks are not claimed:
application/schema/frontend code is untouched. No Terraform command was run.

## Packaging and remaining limits

The review ZIP uses the existing public-source snapshot process with an embedded
raw-byte SHA-256 manifest, not git archive (which would omit pending public source).
It excludes AGENTS.md, ignored/private paths, AWS caches/credentials/identities,
state/plans/dependencies and other ZIPs. Every member is verified byte-identical
to the tested working tree. Additional common credential/private-key pattern
checks inspect only the public ZIP, never historical private directories.

```powershell
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-group-diagnostic-integration/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-group-diagnostic-integration/review/source-manifest.json --archive .cache/f4-group-diagnostic-integration/review/future-training-f4-group-diagnostics-integration-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-group-diagnostic-integration/review/source-manifest.json --archive .cache/f4-group-diagnostic-integration/review/future-training-f4-group-diagnostics-integration-review.zip
```

No source content proves native AWS behavior, HTTP delivery/count or MFA. Windows
OS-level egress containment remains unverified; documented CLI refresh/authentication
traffic limitations still require separate risk acceptance for each future request.
No automatic login is added. Selected-only configuration is not OS containment.

Hard termination, interpreter/import/resource failure or unavailable stdout can
prevent a report. Existing capture cleanup exceptions can escape without Capture
metadata; the supervisor keeps possible release/unknown cleanup, not a false
not-sent claim. Buffer clearing is not secure erasure. The local claim fences a
directory, not a hostile operator creating another directory; fresh directories
must never be used to evade it. Global A2/A3 ledgers/allowlist provenance remain
owner-review obligations. A stored result after a failed persistence/report is not
automatically repaired, promoted or replayed. No positive live-readiness conclusion
follows from these synthetic tests.

Original managed failure remains unknown/stopped/uncertain. Its source pins must
not be updated, its claim must not be removed, and no diagnostic is backfilled.
The only next step proposed here is independent review of this offline integration;
no live authorization, immediate retry or alternative AWS diagnosis is requested.
