# F4-A2-group-managed-01 — Public-source failure analysis

2026-10-27. Offline public-source review and synthetic tests only. No private
historical artifact, AWS configuration, credential or login cache was inspected.
The [owner-attested stopped record](f4-a2-group-managed-01-stopped-observation.md)
remains `outcome_uncertain:true`. No live diagnosis or retry is requested.

## Evidence boundaries

| Evidence class | Established information | Does not establish |
| --- | --- | --- |
| Owner's sanitized outcome | Supervised fixed managed-policy operation returned stopped/uncertain | Native exit, response contents, HTTP delivery, cause |
| Owner's presence report | Preparation, digest and claim present; observation/result absent | Successful claim return, durable claim contents, process release, absence of attached policies |
| Public current source | Ordering and rejection/persistence paths below | Exact historical source/binary/runtime attestation or what actually happened |
| Synthetic fault injection | The tested branches retain claims, fail closed, clear buffers and produce bounded codes | Native AWS CLI, authentication, AWS authorization or live IAM behavior |
| Unavailable historical evidence | No capture exit/status/body or earlier bounded failure code supplied | Cannot reconstruct those values from filenames or a later test |

Plausible explanations include a claim write/ACL/fsync failure after file creation,
post-claim command/environment validation failure, launch/ownership failure,
interruption, timeout, overflow, unclean native completion, rejected output, or
observation persistence failure. None is a finding about the actual invocation.
Do not assign an expired-session, AccessDenied, missing-policy or zero-policy label.

Under the reviewed normal path, a complete unexpected policy page is persisted
**before** allowlist comparison. A result-write-only failure is also preceded by
observation persistence. Thus those failures alone normally leave an observation;
its reported absence fits neither simple explanation. This is conditional source
reasoning, not proof that they are impossible historically: exact executed source,
filesystem behavior and subsequent changes are not independently established.

## Failure paths and ordering

Sources: `group_policy_inventory.py`, `attached_policies.py`, `groups_for_user.py`,
`state_sts.py`, `human_sts.py`, `private_command_runner.py`, `tests/browser_runner.py`,
and the unchanged managed supervised procedure. No operational code is executed
by importing the new diagnostic module.

| Stage | Realistic failures in the reviewed source | Reliable local release statement |
| --- | --- | --- |
| Preparation review | Missing/changed digest, wrong record/unit/identity/group/allowlist, changed source/binary, UTC expiry, noncanonical config, nonempty legacy credentials, private path/ACL rejection | Before capture in the reviewed sequential procedure; no native release by this attempt yet |
| Exclusive claim | Existing claim, open/write/flush/fsync failure, private ACL verification failure, POSIX directory fsync failure | File can exist despite failure; no process release occurs until claim returns |
| Post-claim setup | Fixed-contract/executable rejection; group/config/path/environment construction error; resource exhaustion or interruption evaluating arguments | Before capture; retain claim even if no target was released |
| Capture setup | Invalid limits, oversized wrapper payload, Windows Job Object creation failure, local wrapper Popen/Job attach/reader startup failure | A returned `not_released` is local control-flow evidence; an escaping exception without metadata is conservatively unknown |
| Wrapper release | Writer startup/write/flush/close failure, interrupted release | `may_have_released` is set before writer start; partial or complete release can permit native launch; not launch acknowledgement or HTTP proof |
| Native execution | Native executable launch/configuration failure inside bootstrap, authentication failure, nonzero exit, stderr, stuck process, timeout/cancellation, unexpected exception, stdout/stderr overflow | Native launch failures inside bootstrap can look like nonzero exit/stderr; cannot be identified as authentication/authorization from status alone |
| Capture cleanup | Job close, kill/wait, reader/writer termination or pipe failure | Cleanup routine completion is local evidence, not service cancellation/refund or independent descendant attestation; escaping cleanup errors remain uncertain |
| Response context | Changed/invalid group binding or expected allowlist; wrong diagnostic unit | Captured response is not proof of caller/group identity |
| Parsing/schema | Invalid UTF-8/JSON, duplicate keys, excessive nesting/size, nonobject/extra/missing fields, missing or non-false IsTruncated, continuation fields | No verified observation is written; no continuation request |
| Policy metadata | Unsupported names/ARNs/account/path, duplicates, count/shape violations | Malformed data is not retained as verified metadata |
| Observation write | Existing observation, permission/path/ACL failure, partial write/fsync failure | Claim remains; file may be absent, partial, or fully written despite raised error |
| Allowlist comparison | Structurally valid entries outside independently approved expectations | Observation already written on this path; no successful result |
| Result write/report | Existing result, encoding/storage/fsync/ACL failure, interruption, stdout/report delivery loss | Observation precedes result; a complete file may still exist despite error; no automatic repair/replay |

The original supervisor catches `BaseException`, prints a fixed stopped result and
clears any returned capture. It does not persist the exception, stage or native
status. Current code cannot recover that missing evidence retrospectively.
Job construction and cleanup exceptions can escape capture; do not label them
definitively pre-release just because no Capture object was returned. Process
release is never equivalent to an AWS HTTP request or successful response.

## Bounded diagnostic contract

`inventory_diagnostics.py` is a local-only, opt-in value helper, not an executor.
The existing supervised procedures remain unchanged historical reviewed records;
their generic exception handler does **not** automatically adopt this helper.
There is no new runnable live procedure or activation flag in this work unit.

The two fixed group interfaces accept an optional matching diagnostic context.
Claim stages are marked before validation/write and after successful persistence.
Verification stages precede parsing, schema validation, observation write and
allowlist comparison. Existing ValueError-compatible rejection messages remain.
`Capture` gains default-unknown local `process_release` and `cleanup_state` fields;
the existing four-argument constructor, repr, byte limits, ownership and cleanup
algorithm remain. A separate cleanup flag retains wait/thread uncertainty even
if another final status such as overflow takes precedence.

A future **source-reviewed** supervisor integration would mark capture preparation
before evaluating command/environment, mark begin-capture only after that succeeds,
pass the optional context to claim/verify, then mark result persistence before the
existing exclusive result write. An escaping capture exception must retain
`may_have_released`/unknown cleanup. This describes integration ordering, not
permission to execute or reopen this attempt. New source pins include the helper;
old preparations must not be edited to accommodate changed code.

| Detailed finite private code | Broad public category | Interpretation/limits |
| --- | --- | --- |
| pre_release_validation_failed, claim_failed | pre_release_failure | Instrumented local stage only; partial claims remain |
| wrapper_launch_or_ownership_failed | process_failure | Wrapper/ownership exception, not native auth diagnosis |
| native_exit_nonzero, native_exit_unknown, stderr_present | process_failure | No raw output matching or service-error inference |
| timeout, cancelled | timeout_or_cancellation | No refund, no proof of HTTP delivery/non-delivery |
| capture_overflow, capture_failure, capture_exception_unclassified | capture_failure | Bounded capture rejected or exception unclassified |
| cleanup_uncertain | cleanup_uncertain | Known wait/thread cleanup uncertainty has precedence |
| invalid_json, response_schema, incomplete_page, invalid_policy_metadata, unexpected_policy, validation_unclassified | response_validation_failed | Public category conceals policy membership/allowlist details |
| observation_persistence_failed, result_persistence_failed | private_persistence_failed | Does not assert that a failed write left no file |
| unknown | unknown | No reliably classified evidence |

Authentication/authorization categories are deliberately absent. Approved evidence
does not independently classify them. The helper never reads/prints/matches raw
exceptions, native stdout/stderr, paths, policy identifiers, ARNs, credentials or
preparation digests. Codes and stages are from finite allowlists; no elapsed-time
series, event history or raw native exit code is exported. Public reports include
only fixed checkpoint, stopped, uncertainty, local release/cleanup categories,
coarse failure code and diagnostic-storage status. Detailed stage/status/code can
be saved exclusively in protected `failure-diagnostic.json` when explicitly used
by a later reviewed integration, never in this historical directory.

Diagnostic persistence uses the existing bounded, ACL-checked, exclusive fsynced
writer. Existing files are never overwritten. Failure yields `not_saved`; it
cannot replace the original failure with success, remove a claim, or authorize
replay. A partial diagnostic file can remain and must not be treated as complete.
Output buffers are cleared; that is not guaranteed secure erasure. Diagnostics
record bounded control-flow information, not a complete audit or transaction log.

## Unchanged safety and remaining limits

Fixed caller/group/action/endpoint, independently approved expectations, private
identity/source/binary/digest checks, <=30-minute UTC window, durable exclusive
claim before release, selected-only configuration, no fallback/login, capture
limits (120 seconds plus existing bounded cleanup; 64KiB stdout/4KiB stderr),
Windows Job ownership and strict complete initial-page validation remain.
No claim reset, new directory replay, policy traversal/body read, additional IAM
request, activation switch, generic launcher, dependency or permission is added.

Native authentication/refresh, exact HTTP count, real IAM behavior and Windows
OS egress containment remain outside this synthetic evidence. The original cause
cannot be narrowed reliably without historical evidence not supplied for this
task; accessing protected records is prohibited here. Retain unknown outcome,
preserve the claim/evidence, and stop for independent review. No automatic recovery
or immediate retry is recommended.
