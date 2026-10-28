# F4-A2 — Offline IAM metadata inventory preparation

2026-10-26. **Proposal only. No AWS operation, permission grant or runner activation.**
This is the smallest next planning checkpoint after owner-attested A1a/A1b. Keep
metadata discovery (A2) separate from explicitly approved policy-body closure (A3),
as established in [runbook 26](../planning/26-f4-aws-validation-and-deployment-runbook.md).

## Scope, identities and staged authorization

Caller for every proposed read below: existing `future-f4-human-admin` profile,
privately bound to the A1a Account/Arn/UserId, us-east-1, `https://iam.amazonaws.com`
(global IAM endpoint, HTTPS/443). No new STS probe, login, IAM setup or grant.
The state operator is a **target**, not the caller; preflight remains read-only and
the old policy-administrator delegation remains unattached per last accepted evidence.
Do not use human credentials for ordinary deployment/provider operations.

Recommended first live authorization, **after a reviewed capture binding exists**:
**A2-state-01, one ListAttachedUserPolicies page for future-f4-state-operator.**
This produces new attachment metadata; it does not repeat an identity probe or grant
access. Approval is for one named read, not an inventory loop or the whole runbook.
Later state reads are distinct approvals (or an explicitly enumerated small batch).

| Subunit | Exact CLI service/action and target | Required IAM permission / scope | Successful evidence and stop criteria |
| --- | --- | --- | --- |
| A2-state-01 | `iam list-attached-user-policies --user-name future-f4-state-operator` | `iam:ListAttachedUserPolicies` on privately approved exact state-user ARN, including path | `AttachedPolicies` array; complete single page; privately review policy names/ARNs, never infer their contents |
| A2-state-02 | `iam list-user-policies --user-name future-f4-state-operator` | `iam:ListUserPolicies`, same user ARN | Complete `PolicyNames` array; names only, no inline body read |
| A2-state-03 | `iam list-groups-for-user --user-name future-f4-state-operator` | `iam:ListGroupsForUser`, same user ARN | Complete `Groups` array; verify each account/path/name privately; no automatic traversal |
| A2-state-04 | `iam get-user --user-name future-f4-state-operator` | `iam:GetUser`, same user ARN | Exact private UserName/Path/Arn/UserId; record optional PermissionsBoundary metadata. Absence of the field is only that attachment observation |
| A2-human | Same four reads, explicit `--user-name future-f4-human-admin` | Same four actions, exact human-user ARN only | Identity/boundary/attachments/groups; administrator authority is expected, state-user authority is distinct |
| A2-delegation | Same four reads, explicit `--user-name future-f4-policy-administrator` | Same four actions, exact policy-administrator ARN only | Metadata needed to check the claimed unattached old delegation. A3 bodies/group closure still needed; not a complete effective-permissions proof |
| A2-boundary-name | `iam get-policy --policy-arn $A2ProposedBoundaryArn` | `iam:GetPolicy` on the exact private proposed customer-managed boundary ARN | Expected NoSuchEntity is absence at that exact ARN only; AccessDenied is not absence. Any existing policy stops automatic adoption/creation |
| A2-MFA, separately optional | `iam list-mfa-devices --user-name future-f4-human-admin` | `iam:ListMFADevices` on exact human-user ARN | Private registered-device metadata only; does not prove session MFA. Empty/unrecognized/insufficient coverage requires review, not a fabricated conclusion |

Baseline A2 inventory: **13 first-page invocations** (three users times four, plus
one exact boundary metadata lookup), or **14** if the separate MFA read is approved.
These are proposed maximum scheduled invocations, not current authority or verified
HTTP counts. Preflight inventory would be an extra separately approved four reads.
Do not silently substitute that identity or enumerate all account users/policies.

The first GetUser reference used during A1b established identity expectations;
the owner did not report an inventory of its other metadata. A2-state-04 is proposed
for that different purpose, not for a cleaner identity result. If the owner supplies
adequate fresh metadata attestation from that reference, review reuse explicitly and
omit a redundant read; do not open the old private response to decide automatically.

## Exact future command vectors — not an executable capture procedure

No block below is run in this milestone. `$ReviewedCli` denotes the explicitly pinned
local AWS executable, not a PATH lookup. Raw command output must never go to the
ordinary terminal/transcript. A reviewed per-operation private capture/validation
assembly is a **remaining pre-execution prerequisite**, not supplied by bare vectors.
The fixed STS/reference modules are not generalized or repurposed for IAM inventory.

```powershell
# REVIEW ONLY. No AWS call is authorized by this block or document.
$A2Common = @('--profile','future-f4-human-admin','--region','us-east-1',
  '--endpoint-url','https://iam.amazonaws.com','--output','json','--no-cli-pager',
  '--no-cli-auto-prompt','--no-paginate','--cli-connect-timeout','5','--cli-read-timeout','15')
# A2-state-01 ONLY, after its separate approval and reviewed private capture:
& $ReviewedCli iam list-attached-user-policies --user-name future-f4-state-operator @A2Common
```

```powershell
# Subsequent state reads: each needs its own approval/capture, never automatic.
& $ReviewedCli iam list-user-policies --user-name future-f4-state-operator @A2Common
& $ReviewedCli iam list-groups-for-user --user-name future-f4-state-operator @A2Common
& $ReviewedCli iam get-user --user-name future-f4-state-operator @A2Common
```

```powershell
# Later human metadata subunit only, not part of state-01 approval.
& $ReviewedCli iam get-user --user-name future-f4-human-admin @A2Common
& $ReviewedCli iam list-attached-user-policies --user-name future-f4-human-admin @A2Common
& $ReviewedCli iam list-user-policies --user-name future-f4-human-admin @A2Common
& $ReviewedCli iam list-groups-for-user --user-name future-f4-human-admin @A2Common
# Later delegation metadata subunit only; never attach its old proposed grant.
& $ReviewedCli iam get-user --user-name future-f4-policy-administrator @A2Common
& $ReviewedCli iam list-attached-user-policies --user-name future-f4-policy-administrator @A2Common
& $ReviewedCli iam list-user-policies --user-name future-f4-policy-administrator @A2Common
& $ReviewedCli iam list-groups-for-user --user-name future-f4-policy-administrator @A2Common
```

```powershell
# Exact proposed private account/root-path policy ARN; no public account value.
# Owner approves this ARN/path; do not derive root paths for existing users/policies.
& $ReviewedCli iam get-policy --policy-arn $A2ProposedBoundaryArn @A2Common
# Optional, separate MFA configuration permission/approval:
& $ReviewedCli iam list-mfa-devices --user-name future-f4-human-admin @A2Common
```

Proposed boundary name remains `future-f4-state-operator-boundary`. Exact known-ARN
absence does not establish absence at another path. Do not issue ListPolicies to
resolve a collision automatically. Stop and obtain privately confirmed metadata and
new authorization. No wildcard-resource management permission or new grant is needed
for this proposal; denied existing permissions are an owner-review issue.

## Private capture, authentication and privacy contract for later implementation

Before authorizing state-01 execution, independently review a **single-purpose**
human-login capture assembly reusing existing safe primitives. No generic operation
flag/argument surface or modification of either disabled live executor is proposed.
It must establish all of the following:

1. Owner privately confirms exact caller Account/Arn/UserId, target user's known ARN
   including path and provenance, approved command, pinned binary/source hashes and
   attended UTC window <=30 minutes (>=5 minutes remaining before launch). A1 identity
   evidence is owner-attested, not a real-time caller/session assertion from this task.
   A list response does not echo/prove the target or caller; binding depends on the
   frozen command and selected native login configuration.
2. New protected `.cache` preparation/claim for the exact operation, not a reused A1
   record. Owner-controlled encrypted storage, owner/SYSTEM ACLs, no symlinks or
   unapproved logging/transcription/screen sharing. Never send private artifacts to
   Codex, telemetry or the review ZIP. No raw errors, account IDs, ARNs, policy/group
   names, UserIds, MFA serials, timestamps or pagination tokens in public summaries.
3. Selected-only human login configuration, private explicit login-cache location,
   empty shared/legacy credential files, no inherited AWS/TF/proxy/Python/PATH/CA or
   credential-process overrides; IMDS disabled; verified TLS; no profile/root/role/
   static-credential fallback, debug, custom endpoint or login. Existing credentials
   are neither exported nor copied. Preparation must not inspect tokens/cache contents.
4. **Fresh A2-specific decision** on native refresh/authentication traffic and no
   OS-enforced egress containment. A1a/A1b acceptance does not transfer. No hard
   one-HTTP-request or session-MFA claim from flags or successful IAM output.
   If these limitations are unacceptable, execution stays blocked; no weakened gate.
5. Durable exclusive claim **before release**, one fixed invocation, owned Job Object,
   <=120s execution + <=10s cleanup, <=64KiB stdout/4KiB stderr, no loop/shell retry/
   background polling. `AWS_MAX_ATTEMPTS=1` is a native retry setting, not audited
   refresh/request count. Check source/binary/window again before claiming/releasing.
6. Strict JSON/duplicate-key checks, correct action-specific response shape, zero
   stderr, exit 0, completed capture and bounded metadata arrays. No `--query` or
   filtered path prefix that could hide evidence. Unexpected fields/shapes remain
   private and require review rather than an automatic parser relaxation. Persist
   only approved bounded private inventory metadata and a sanitized finite summary;
   do not use stdout/stderr as ordinary logs. Agree local retention/deletion explicitly.

Privacy risk is broader than STS: inventory reveals account security structure,
group memberships, policy identifiers and possibly user tags/sign-in metadata.
Read-only traffic still goes to AWS and may appear in audit systems. No account
resource mutation is intended by these IAM reads, but local captures/claims are
writes and authentication cache/refresh behavior is not asserted immutable.

## Pagination, bounds and stop rules

- `--no-paginate` disables automatic following of pages; `--no-cli-pager` disables
  a different, terminal pager. Do not combine with `--max-items`/`--page-size`/
  `--starting-token`, and do not silently add a service Marker. Each proposed list
  is its initial page only. This intentionally may be an **incomplete** inventory.
- Require exact boolean `IsTruncated:false` on each list response; true/missing/
  wrong type, nonempty Marker/NextToken/nextToken or contradictory pagination state
  means incomplete and STOP. An empty array alone does not establish completeness.
  Do not infer a final page from fewer-than-default results. A next page is a new
  explicitly approved request with privately frozen continuation, not a retry loop.
- Preserve runbook caps: **40 total A2/A3 IAM invocations**, <=4 distinct approved
  groups, <=12 unique managed-policy ARNs. Proposed byte caps apply per invocation;
  aggregate retained capture <=40 x 64KiB = 2.5MiB, stderr not retained as public
  evidence. Bounds are a contract for the future assembly/operator ledger, not
  currently implemented enforcement by the STS-only tools. Count failed/uncertain
  invocations, extra approved pages, MFA and boundary lookups; never reset on restart.
- Each list also needs an owner-approved expected-entry allowlist, with a conservative
  <=40 entries per response; group/managed-policy caps above are stricter where
  applicable. Unknown/duplicate/unexpected-account/path entries stop for private
  review. AWS-managed policies use account `aws`; customer policies and group ARNs
  must match the private account. Do not treat expected authentication policy names
  as proof of their contents or absence of other effective grants.
- Caps may prevent full closure. Do not enlarge them to finish; report incomplete
  and obtain a separately scoped decision. Four groups/twelve managed policies do
  not guarantee all A3 reads fit in the 40-call allowance.
- AccessDenied, NoSuchEntity for a required user, throttling, service error, failed
  parsing, overflow, auth expiry/prompt, source/identity mismatch, privacy loss,
  expired window, unknown delivery or incomplete cleanup stops. No automatic retry,
  login, permission expansion, next read, marker deletion or alternate profile.
  A required user missing is not the same as the explicitly expected boundary-ARN
  NoSuchEntity case. Only a privately classified authoritative service error can
  establish the latter; CLI exit code alone cannot distinguish it from AccessDenied.
- On partial/interrupted execution retain the claim and private evidence; confirm
  owned descendants have stopped, classify outcome as uncertain and seek fresh review.
  Nothing in this read-only unit needs an IAM rollback. Do not "recover" by changing
  grants, deleting/attaching boundaries, creating policies or replaying automatically.

## A3 and boundary installation dependencies — outside A2 execution scope

After complete reviewed metadata, approve exact discovered names/ARNs before any A3
read. Required closure vocabulary from runbook 26:

| Future action | Approved target/resource | Evidence |
| --- | --- | --- |
| `iam:GetUserPolicy` | Exact approved user ARN + exact inline policy name | Private inline policy body |
| `iam:ListAttachedGroupPolicies`, `iam:ListGroupPolicies` | Exact discovered-and-approved group ARN/name | Complete group policy metadata; pagination stops apply |
| `iam:GetGroupPolicy` | Same group ARN + approved inline name | Private group inline body |
| `iam:GetPolicy`, `iam:GetPolicyVersion` | Exact approved managed policy ARN and observed default version, including any existing boundary | Private metadata and policy body; AWS-managed `aws` namespace is distinct |

No `GetGroup` membership enumeration is needed for this policy closure. No automatic
traversal of returned names, version history, ListUsers, ListPolicies, account-wide
authorization dump, credential report, access-key read, Organizations, S3, CloudTrail,
Access Analyzer or simulation is part of the minimum A2 proposal. Optional existing
CloudTrail context remains separate A4; registered MFA is not request MFA.

Read bodies privately, decode/parse independently, review Allows/Denies/NotAction/
NotResource/variables/conditions and transitive group/boundary grants. Validate no
unapproved state-user IAM/EC2/PassRole/AssumeRole/unrelated S3 privileges or active old
delegation. An incomplete body/group closure cannot prove least privilege. A2/A3
are sequential observations, not an atomic IAM snapshot or an audit of every
resource-policy/cross-account grant. Freeze concurrent IAM changes with the owner;
stale or inconsistent evidence requires a separately approved reconciliation read.

Only later: B1 exact real-document Access Analyzer validation and optional B2
simulation; C customer-managed boundary creation; D attachment to exact state user.
The existing boundary is still a local proposal on last recorded evidence. A1b did
not prove attachment/permissions. A2 must reconcile existing boundaries before any
replacement. Never substitute an inline policy for a permissions boundary, activate
the old delegation or treat boundary removal as a safe rollback. A ceiling grants
no permissions; account resource grants and human mutation authority need review.

Human one-time S3 bootstrap remains distinct from restricted backend access and
future nonadmin provider provisioning. Legacy human-bootstrap preparation/plan
binding corrections, host-role privilege escalation controls, actual S3 env:/ and
missing-object 403/404 behavior, backup/state custody and costs remain later gates.
No S3/Terraform command, cloud spending or deployment is authorized here.

## Exact first authorization proposal and next task

> Subject to independent review of the single-purpose capture assembly, authorize
> A2-state-01 only: one supervised initial-page IAM ListAttachedUserPolicies invocation
> via future-f4-human-admin, targeting only future-f4-state-operator in the privately
> approved account/path, us-east-1 and https://iam.amazonaws.com. Bind reviewed CLI/
> source hashes, exact private caller identity, <=30-minute UTC window, 64KiB/4KiB
> output caps, 120s execution/10s cleanup and durable one-shot claim. Decide explicitly
> whether to accept A2-native refresh/authentication traffic and no OS egress
> containment. Permit private verification and sanitized metadata-only reporting.
> No retry, pagination continuation, extra IAM read, login, permission grant, S3,
> Terraform, spending or automated live-executor activation. Any uncertainty stops.

**Next Codex task:** offline preparation/review of that fixed human capture and
action-specific page validator, reusing existing primitives and synthetic fixtures.
Do not expand the STS module's command surface or enable the generic runner.
Then obtain explicit owner approval for the named read. The command vector above
is not a substitute for that execution prerequisite and authorizes nothing now.

Official public sources reviewed 2026-10-26: [GetUser](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetUser.html),
[managed attachments](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAttachedUserPolicies.html),
[inline names](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListUserPolicies.html),
[groups](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListGroupsForUser.html),
[CLI pagination](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html),
[native login refresh](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html),
[MFA metadata](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListMFADevices.html),
[GetPolicy](https://docs.aws.amazon.com/cli/latest/reference/iam/get-policy.html).
API/command review is public-document evidence, not live-account validation. Resource
scope proposals retain the accepted runbook's exact-user/group/policy restrictions;
no new IAM permission JSON or policy attachment is generated.
