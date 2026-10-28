# F4-A2-state-02 closure and state-03 offline handoff

2026-10-26. **Offline preparation for independent review only. No live authorization
requested or executed. No AWS API, private identity/cache inspection, IAM mutation,
S3/Terraform operation, financial authority, installation, commit or push.**

## Completion evidence and changed files

[State-02 completion](f4-a2-state-02-completion.md) records the exact owner-attested
result, not independently reproduced Codex execution:

```json
{"checkpoint":"F4-A2-state-02","result":"metadata_page_verified","policy_count":0,"mfa_verified":false,"http_request_count_verified":false}
```

Zero inline user policies and state-01's separate zero direct managed attachments
are distinct limited observations. Neither establishes no effective permissions.
Group policies, boundaries and resource grants remain unverified; MFA and HTTP count,
native authentication/refresh and Windows egress limitations remain. No private record
or raw response was read/copied, no identity/request repeated, no past authority reused.

| File | Change |
| --- | --- |
| `docs/implementation/f4-a2-state-02-completion.md` | New owner-attested completion/provenance/limitations record |
| `infra/aws/groups_for_user.py` | New closed offline state-03 command, group validation, private preparation/review/claim and sanitized capture verification |
| `tests/test_groups_for_user.py` | New synthetic boundary/adversarial/concurrency/fault/privacy tests and actual future procedure blocks with capture replaced before execution |
| [Supervised state-03 procedure](f4-a2-state-03-supervised-procedure.md) | New local preparation, independent authorization barrier, exact future request and private group review/reporting |
| This handoff | New evidence, decisions, blockers and review-package record |
| `docs/planning/26-f4-aws-validation-and-deployment-runbook.md` | New current-status addendum only; historical text retained |

## Implementation and safety decisions

Single command only: `iam list-groups-for-user`, caller profile
`future-f4-human-admin`, target `future-f4-state-operator`, us-east-1,
`https://iam.amazonaws.com`. No arbitrary IAM action/target/profile/endpoint/extra
argument API, pagination, filtering or automatic group-policy traversal.

Reuse reviewed state-01 metadata validators, selected-only human environment, strict
JSON, private <=64KiB exclusive/fsynced I/O, and owned Windows Job Object capture.
Existing helper/executor bodies are unchanged. The group helper has no process
launcher, CLI entrypoint, live flag or generic permission expansion. Separate
state-03 record kind/source manifest/spec/environment/directory/receipt/claim prevents
reusing earlier unit preparations. No new dependency, shared framework or service.

Require exact private caller/target Account/Arn/path/UserId/provenance (same account,
distinct users), reviewed CLI/source hashes, <=30-minute UTC window with >=5 minutes
remaining and a separately approved private preparation digest binding all metadata.
Source hashes come from the reviewed ZIP manifest; expected digest is independently
retained from private review, never computed from current data as its own expectation.
New exclusive durable claim precedes release; failed/partial/fsync/cancelled/restarted
attempts retain it. Process limits: 120s execution + <=10s cleanup, 64KiB stdout/4KiB
stderr, no retry. Claims/digests are operator safeguards, not immutable permits,
hostile-owner protection, HTTP-delivery proof or Windows network containment.

Group contract:

- Strict top-level **Groups/IsTruncated only**, explicit boolean false, <=4 objects.
  Reject all tokens/extra fields, missing flags, truncation and malformed/oversized
  captures. Never fetch a next page or group/policy details.
- Each observed group has exactly GroupName, GroupId, Path, Arn and CreateDate.
  Name 1–128 supported ASCII IAM-name characters; ID 16–128 ASCII word characters;
  supported slash-delimited path <=512, no empty/dot/traversal segments; ARN <=2048,
  exactly the private customer account's aws/iam/no-region group ARN matching path
  and name. No AWS-managed/foreign-account group namespace or name-only trust.
- Require a valid aware ISO-8601 creation string with bounded fractional seconds and
  valid numeric-offset components. Python's permissive offset normalization is not
  accepted as ISO validity. CreateDate is validated metadata, not an identity expectation.
- Approved identities contain exactly GroupName/GroupId/Path/Arn and match exactly;
  duplicate IDs/ARNs and case-folded duplicate names reject. The owner's complete
  approved A2/A3 group set and observed page each have <=4 identities. Owner confirms
  the global set/remaining budget privately; no durable multi-unit ledger is added.
- Complete well-formed unexpected groups are persisted privately **before** rejection,
  enabling review without replay. A changed ID/path is unexpected even if another
  field matches. Malformed/truncated/duplicate/unsupported metadata is not promoted
  to a valid observation. No success record on unexpected data/persistence failure.
- Summary contains only checkpoint/result/group_count and unverified MFA/HTTP flags.
  No names, IDs, paths, account data, creation timestamps, raw stderr/exceptions or
  private digests in ordinary outputs. Buffers are cleared, not guaranteed securely
  erased. No assumption of empty membership: positive tests use two/four groups.

Owner-approved identities cannot be learned from the very response being scored.
If GroupIds are not authoritative privately, a nonempty response remains unapproved
and stops; no guessed IDs, GetGroup or automatic trust/allowlist update. Empty
allowlist is a deny-all choice for nonempty results, not evidence or expectation of
zero groups. Group membership does not reveal group policies/effective permissions.

## Offline validation and evidence type

Windows PowerShell 5.1, Python 3.14.9, existing tools only. All identities, cache
locations, dates, groups and process outputs in tests are **synthetic**. No native
AWS executable or actual account endpoint was invoked. Official public documentation
review is distinct from account-connected validation. Native CLI/schema compatibility
and current IAM authority remain unmeasured. The Group type requires CreateDate even
though some examples omit it; this protocol fails closed if missing.

| Exact command / check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_groups_for_user.py -q --basetemp=.cache/f4-a2-state-03/pytest-focused --tb=short` | **81 passed in 174.83s**, before timezone-component hardening and three further regression cases |
| `.venv/Scripts/python.exe -m pytest tests/test_groups_for_user.py -q --basetemp=.cache/f4-a2-state-03/pytest-final --tb=short` | **84 passed in 174.07s** |
| `.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-a2-state-03/pytest-regressions --tb=short` | **260 passed in 12.43s**, run in isolation |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, frozen 24 development/16 held-out; software regression only |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **182 public Python files**, native and 3.13 grammar pass |
| `.venv/Scripts/ruff.exe check .` | Exit 0, all checks pass |
| `.venv/Scripts/ruff.exe format --check src tests scripts infra experiments` | Exit 0, **185 files** formatted |
| `git -c core.safecrlf=false diff --check` | Exit 0 |

Coverage includes nonzero/empty/four-group pages, nested/root paths, supported dates,
field/count/byte boundaries, unknown groups, changed expected IDs/paths, duplicates,
foreign accounts/partitions/services/regions, malformed or missing fields, pagination,
identity/source/binary/window/provenance mismatch, poisoned login/credentials/environment,
private-digest mutation, failed captures, cancellation/interruption/persistence failure,
exclusive concurrent claims, failed fsync/partial claims/restart/replay and cross-unit
record rejection. Actual future capture block is executed only after installing a
synthetic replacement. Local preparation block is exercised with 0/1/4 approved
identities using JSON text, preserving the reviewed PowerShell 5.1 array workaround.
Both PowerShell blocks parse without execution; embedded Python has 3.13 grammar.
Existing live executor functions remain unconditional raises.
Final consistency checks matched the exact owner JSON, resolved **13 local links**
in changed documents/runbook and verified raw-byte preservation of all original
source except the additive runbook status note; removing it restores the original.

A local standard-library probe found `datetime.fromisoformat` normalizes `+01:99`
to a 2:39 offset. Explicit offset-range validation/regression cases prevent that
malformed time from passing. No provider observation is implied. Private ACL/Job
Object fixtures use normal local process access; no ACL/security policy is weakened.
No application/PostgreSQL/frontend/installed-browser or Terraform check is claimed
rerun: application/schema/UI code is unchanged and Terraform operations are prohibited.

## Remaining limitations and approval boundary

**No live authorization request is made. Independent review is the next action.**
For any future execution, a separate owner decision must bind this single operation,
exact caller/target/private identities, full <=4-group allowlist including prior
approvals, reviewed binary/source hashes and private digest, new <=30-minute UTC
window, 120s/10s process bounds, 64KiB/4KiB capture and private retention/reporting.
It must explicitly decide state-03 native refresh/authentication traffic and lack
of verified Windows OS-level egress containment. Earlier exceptions do not transfer.
No automatic login, credential fallback, grant, body read, pagination/traversal,
retry, S3/Terraform, spending or automated live-executor activation is included.

Blockers before any live step: trusted private GroupIds/paths/bindings and complete
global allowlist attestation; source/procedure acceptance; fresh owner risk/window
decision; actual CLI/output behavior still unknown. A successful list cannot prove
caller identity, session MFA or HTTP count. Conservative paths/ASCII/timestamp
protocol may reject otherwise service-valid output; stop for review, never weaken
validators or add account calls automatically. Owner tracks the existing proposed
40-call A2/A3 budget; failures/uncertainty consume a scheduled invocation. Four-group
enforcement is against the submitted complete approved set, not an independent audit
of unprovided prior records. No global recovery/authority infrastructure is introduced.

On uncertainty retain claims/private observations, ensure owned cleanup and stop.
Do not delete markers/create directories as replay, kill unrelated processes, change
grants/boundaries or automatically delete evidence. Encryption/ACLs and no concurrent
local source/config changes are owner prerequisites; source hashes do not prevent
all filesystem TOCTOU or malicious-local-owner attacks. Raw malformed output/stderr
is intentionally not retained as verified metadata. Further diagnostics require
separate review, not an extra request under this milestone.

State-04 metadata, A3 group/policy bodies, actual boundary validation/installation,
bootstrap/provider authority separation, S3 compatibility, recovery and spending
remain separate gates. No new effective-permission or deployment-readiness claim.

## Source preservation and sanitized review package

Starting inventory: **480 public files**. Only the runbook's new status addendum
changes an original; its earlier body is preserved, all other **479 originals**
remain byte-identical. Five additions yield **485 public files**. Application,
accepted helpers/executors, policy generators, baseline and unrelated worktree changes
are preserved. AGENTS.md stays ignored/unchanged; no commit/push.

```text
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a2-state-03/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-a2-state-03/review/source-manifest.json --archive .cache/f4-a2-state-03/review/future-training-f4-a2-state-03-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-a2-state-03/review/source-manifest.json --archive .cache/f4-a2-state-03/review/future-training-f4-a2-state-03-review.zip
```

Archive source members must match final working-tree bytes and the embedded SHA-256
manifest. Private identities/IAM observations, credentials/login caches, `.aws`,
ignored `.cache`, AGENTS.md, dependencies and Terraform state/plans/private inputs
are excluded. Public-source credential-pattern scan supplements exclusions, not
universal secret detection. No private file is opened to create it. Sanitized hash/
verification evidence remains beside the ZIP. Stop for independent review only.
