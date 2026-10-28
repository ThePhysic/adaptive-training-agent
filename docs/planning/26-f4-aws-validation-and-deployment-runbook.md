# F4 AWS validation and deployment-readiness runbook

> Group-policy status, recorded on 2026-10-26: [State-03 stopped observation](../implementation/f4-a2-state-03-stopped-observation.md)
> is owner-attested, structurally retained one-group evidence, not an allowlist pass.
> The original stopped result/claim remain; no rerun or retroactive approval.
> [Independent group-policy preparation](../implementation/f4-a2-group-policy-handoff.md)
> is offline only. Policy classification, boundary and effective permissions remain
> unknown. No further AWS call, grant or live authorization request is made here.

> Current checkpoint status, recorded on 2026-10-26: [State-02 is owner-attested complete](../implementation/f4-a2-state-02-completion.md)
> for zero inline user policies in the reported complete response. State-01 separately
> reported zero direct managed attachments; effective permissions remain unverified.
> [State-03 preparation](../implementation/f4-a2-state-03-supervised-procedure.md) is
> offline only. No further AWS call or live authorization request is made here.
> Earlier status/proposal/NO-GO records remain historical; live executors stay disabled.

> Newest status addendum, recorded on 2026-10-26: [A2-state-01 is owner-attested complete](../implementation/f4-a2-state-01-completion.md)
> for one complete initial page with zero directly attached managed policies only.
> Effective permissions remain unverified. [State-02 preparation](../implementation/f4-a2-state-02-supervised-procedure.md)
> is offline; no further read, body lookup or other AWS operation is authorized.
> Codex did not reproduce the owner's request. Earlier status/proposal/NO-GO text
> remains historical; no executor or permission is activated by this addendum.

> Latest status addendum, recorded on 2026-10-26: [F4-A1b is owner-attested complete](../implementation/f4-a1b-completion.md),
> following a separately approved human GetUser reference read and state-user STS
> identity match. A1a/A1b were not independently reproduced by Codex. Do not repeat
> those identity checkpoints for cleaner evidence. [A2 metadata preparation](../implementation/f4-a2-iam-inventory-preparation.md)
> is offline only, with fresh capture/authentication/authorization gates. No A2 or
> later AWS operation is authorized. Earlier status addendum/proposal/NO-GO text
> below remains historical evidence; no live executor or IAM permission is changed.

> Current-status addendum, recorded on 2026-10-26: [F4-A1a is owner-attested complete](../implementation/f4-a1a-completion.md)
> following a separately authorized human-user GetUser reference read and supervised
> regional STS identity verification. Codex did not reproduce those operations.
> Do not rerun A1a. [A1b preparation and remaining gates](../implementation/f4-a1b-preparation-handoff.md)
> are offline proposals only; no subsequent AWS operation/permission is authorized.
> The original proposal and NO-GO reasoning below are retained as historical text;
> the A1a manual-risk exception does not activate automation or extend to A1b/later units.

2026-10-26. **Planning proposal; no AWS execution or spending authorized.** All AWS
and account-connected Terraform commands below are future review vectors, not
instructions to run in this milestone. Approval of one unit never approves another.

## Decision baseline and evidence

This runbook uses the owner-accepted boundary implementation and syntax follow-up.
The latest owner instruction supersedes proposal 25 wherever it suggested an
operator bootstrap or a shared backend/provider authority:

- Existing identities: `future-f4-human-admin`, `future-f4-preflight`,
  `future-f4-policy-administrator`, `future-f4-state-operator`.
- Human administrator performs the one-time state-bucket bootstrap. Preflight
  stays read-only. The old policy-administrator delegation remains unattached.
- State operator is an IAM **user**, constrained to the designated state/lock
  objects; its proposed persistent boundary is not yet created/attached in AWS.
- Standalone Free-plan account, us-east-1, MFA/browser login and prior identity
  verification are **owner-supplied facts**, not fresh measurements here. Do not
  repeat account setup, MFA enrollment or accepted preflight R3 merely for cleaner logs.
- Terraform **1.17.0**, AWS provider **6.70.0**, local bootstrap backend and S3
  deployment backend are verified repository facts. There is no Organizations,
  Identity Center, Redis, worker, queue, model or hosted-telemetry addition.
- Previous accepted 5-vCPU/5-VPC/one-existing-VPC findings are historical owner
  evidence. Current usage, credits/expiry, account permissions, policy attachment,
  S3 ownership/behavior and deployment AMI/images remain live-verification gates.

Verified source: `state-bootstrap/{main,authority,boundary}.tf`,
`modules/protected-bucket/main.tf`, `deployment/{versions,main,iam}.tf`,
`state_operator_prepare.py`, `state_boundary.py`, `state_bundle.py`,
`private_command_runner.py`, existing mock tests and the two accepted handoffs.
Historical plans/reviews remain unchanged. This proposal grants no source activation.

## Execution prerequisites applying to every future unit

1. Owner names the exact unit/subunit, caller/profile, private Account/Arn/UserId,
   destinations, command list, UTC window, data retention and numerical allowance.
   Confirm independently that the human caller is not root. No default/alternate
   profile, static credentials, instance/container metadata or automatic role fallback.
2. Privately attest the existing profile bindings. The exact **proposed command
   labels** below are the IAM usernames; actual profile labels have not been
   inspected in this milestone. Only `future-f4-preflight` has prior repository
   profile evidence. If another existing alias is used, revise and approve the
   private command manifest; do not create a profile or infer identity from its name.
3. Freeze reviewed sources, locks, policy bytes/hashes, private inputs and expected
   outputs. Recheck identity/window/source after waiting and immediately before a
   mutation. Use <=2h grants, stop launching with <5min left, no concurrent IAM/state
   changes by another operator and no automatic extension.
4. Use a reviewed private Windows capture/execution binding: <=120s command plus
   bounded owned cleanup; <=1MiB stdout/64KiB stderr; bounded downloaded files;
   no raw console/log export, `--debug`, shell transcription or credentials in argv.
   Local artifacts require owner-controlled encryption and verified ACLs in `.cache`.
5. Preserve verified TLS, exact per-unit HTTPS/443 destinations, no redirects/custom
   CA/proxy inheritance, CLI `AWS_MAX_ATTEMPTS=1`, no outer retries or detached work.
   Terraform's checked-in provider/backend `max_retries=1` is not proof of identical
   CLI semantics: document the pinned implementations' actual attempt limits with
   offline fault fixtures before authorizing E/F/G traffic. Explicit configuration
   may override environment settings. Provider waiters/fallbacks are separate from
   SDK retry count. Count all attempts; reconcile ambiguous writes before replay.
6. Disable CLI pagination; inspect `IsTruncated`/`Marker`/`nextToken`/`NextToken`.
   Truncation means incomplete evidence and STOP for separately reviewed pages.
   Do not combine `--no-paginate` with CLI paginator `--max-items`/`--page-size`.
   Query/output filters are presentation, never authorization boundaries.
7. Read-only is still signed account traffic with private output/audit implications.
   A login cache might need remote refresh. Do not run `aws login`, credential export,
   `configure list`, Sign-In refresh or new endpoints as an automatic prerequisite.
   Expired/unsupported credentials mean stop for a separate authentication decision.

**Current engineering blocker:** `execute_account()` always raises; the supported
runner emits offline proposals only. Its fixed AWS vocabulary does not implement
the read inventory, validation, installation or S3 units below. The old R3 tunnel
permits one STS tunnel, not generic IAM/S3. A separately reviewed offline expansion
and explicit live authorization are required before using an agent-operated runner.
The generic capture primitive or a boolean flag is not an authorized workaround.
An owner-run manual procedure likewise needs an independently reviewed capture/
egress/identity method; bare commands below do not supply one.

### Common future command vectors

These local variable definitions make profile/destination choices explicit. Values
such as `$F4Account`, `$F4HumanArn`, `$F4StateArn`, expected UserIds, bucket, paths,
policy versions/ETags and UTC times must come from the private approved manifest.
None are real values in this document. `$F4PolicyFile` is the **real**, independently
validated output, not the tracked all-zero synthetic fixture.

```powershell
# REVIEW ONLY: profile-label bindings need owner confirmation before any AWS call.
$F4AdminProfile = 'future-f4-human-admin'
$F4StateProfile = 'future-f4-state-operator'
$F4PreflightProfile = 'future-f4-preflight'
$F4Region = 'us-east-1'
$F4BoundaryName = 'future-f4-state-operator-boundary'
$F4StateKey = 'ec2-demo/terraform.tfstate'
$F4LockKey = 'ec2-demo/terraform.tfstate.tflock'
$F4Common = @('--region', $F4Region, '--output', 'json', '--no-cli-pager',
  '--no-cli-auto-prompt', '--no-paginate', '--cli-connect-timeout', '5', '--cli-read-timeout', '15')
$F4AdminSts = $F4Common + @('--profile', $F4AdminProfile, '--endpoint-url', 'https://sts.us-east-1.amazonaws.com')
$F4StateSts = $F4Common + @('--profile', $F4StateProfile, '--endpoint-url', 'https://sts.us-east-1.amazonaws.com')
$F4AdminIam = $F4Common + @('--profile', $F4AdminProfile, '--endpoint-url', 'https://iam.amazonaws.com')
$F4AdminAA = $F4Common + @('--profile', $F4AdminProfile, '--endpoint-url', 'https://access-analyzer.us-east-1.amazonaws.com')
$F4AdminS3 = $F4Common + @('--profile', $F4AdminProfile, '--endpoint-url', 'https://s3.us-east-1.amazonaws.com')
$F4StateS3 = $F4Common + @('--profile', $F4StateProfile, '--endpoint-url', 'https://s3.us-east-1.amazonaws.com')
```

All stdout/stderr below is private capture, never ordinary terminal output. Do not
paste policy bodies, identifiers, MFA serials, tokens, state, plans, lock bodies,
CloudTrail events or billing details into public reviews/LLMs. Publish only finite
classifications, counts and approved synthetic evidence. No model/provider or
Langfuse permission accompanies AWS authorization.

## Authorization order and effects

Phase letters describe subjects; the recommended chronological order is
**A → B → C → D → E → F**, then separately **G**. Here E is human S3 bootstrap
(requested Phase F), and F is genuine S3 compatibility (requested Phase C).

| Unit | Caller / effect | Independent approval and success gate | Recovery |
| --- | --- | --- | --- |
| A1a / A1b | Human / state; one STS read each | Exact private identity match; A1a alone is the first recommended account unit | Stop on mismatch/refresh; no identity fallback |
| A2 / A3 | Human; IAM metadata then separately named policy closure reads | Complete bounded inventory, approved effective permissions and MFA evidence | Incomplete/denied is not absence; approve further reads separately |
| A4 optional | Human; one bounded existing CloudTrail history read | Correlated session evidence or explicit inconclusive result | No new trail/Lake/instrumentation |
| B1 | Human; ValidatePolicy sends exact private document | Findings complete and reviewed; no policy resource changed | No automatic rewriting or paid checks |
| B2 optional | Human; explicit custom simulations | Expected matrix, no missing context/truncation; no service actions execute | Investigate disagreement; never use it as live S3 proof |
| C | Human; create one managed policy | Exact new ARN/version/body verified; no attachment | Ambiguous create: GetPolicy/GetPolicyVersion; no blind repeat/adoption |
| D1 / D2 | Human attaches boundary; separately authorized state-user login/reads | Exact attachment/body and intended authentication; no new state grant | Preserve boundary; narrowly reviewed recovery, never blanket removal |
| E-plan / E-apply / E-read | Human; local-state plan, separate six-resource apply, separate verification | Saved-plan/source/account checks; bucket protections/owner/region | Preserve local state and partial resources; new reconciliation plan |
| F-read / F-init / F-lock / F-seed | State/human as named; distinguish reads, remote init, lock writes, optional state seed | Exact keys/versions; no 403-as-absence or permission expansion | No automatic state deletion/force-unlock; separately authorized repair |
| G-design / G-plan / G-apply | New nonadmin deployer proposed; backend stays state user | Separate identity/host-role security design, dual-profile proof and new budget | Source/state-compatible rollback; no admin fallback or blanket destroy |

IAM and basic validation have no published additional service charge, but still
need explicit traffic/privacy approval. S3 requests/versions may consume credits;
E/F need numerical spending approval. G deployment has a **different** budget.

## A. Read-only account, identity, MFA and permissions

### A1: smallest independent unit

Approve **one** HumanAdmin STS GetCallerIdentity first; only after it matches, approve
the state-user equivalent. No accepted preflight identity retry is needed here.

```powershell
# A1a approval only: one invocation, no credential refresh or automatic retry.
aws sts get-caller-identity @F4AdminSts
# A1b needs its own approval; it does not follow automatically from A1a.
aws sts get-caller-identity @F4StateSts
```

Expected: exact private Account/Arn/UserId for the two intended IAM users. Reject
`:root`, assumed/federated roles, another account/user, mismatched UserId, default
profile or unapproved refresh destination. STS has no region/MFA field here:
region consistency comes from frozen config and verified regional destination;
this response does not prove MFA. Full identifiers are sensitive.
[STS behavior](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html).

### A2: metadata inventory, bounded before reading bodies

Human-admin profile executes the following **per approved public username**. Start
with human-admin/state; include policy-administrator explicitly to corroborate the
unattached-delegation finding. Preflight policy auditing is optional separate scope,
not a reason to use it for writes. Proposed cap: 40 IAM reads for A2/A3 combined,
<=4 approved groups and <=12 unique managed policies; exceed/truncation stops.

```powershell
# A2: bind one approved name at a time, not arbitrary account-wide enumeration.
$F4UserName = 'future-f4-state-operator'
aws iam get-user --user-name $F4UserName @F4AdminIam
aws iam list-attached-user-policies --user-name $F4UserName @F4AdminIam
aws iam list-user-policies --user-name $F4UserName @F4AdminIam
aws iam list-groups-for-user --user-name $F4UserName @F4AdminIam
# Separately approved A2 MFA configuration read for the administrator.
aws iam list-mfa-devices --user-name future-f4-human-admin @F4AdminIam
# Exact proposed root-path ARN derived privately from the expected account/name.
aws iam get-policy --policy-arn $F4BoundaryArn @F4AdminIam
```

| API / IAM permission | Resource scope / successful response | Failure or sensitive evidence |
| --- | --- | --- |
| sts:GetCallerIdentity | Selected caller; Account/Arn/UserId | No separate Allow required by this API; still no execution approval. Values private; identity cannot be inferred from profile name |
| iam:GetUser | Exact approved user ARN including actual path; matching User and optional PermissionsBoundary | Unknown user/account/Arn or unexpected boundary stops. Absence of field is the expected not-attached observation, not a general permission assessment |
| iam:ListAttachedUserPolicies / ListUserPolicies / ListGroupsForUser | Exact user ARN; complete policy/group metadata | Unexpected entry, truncation or denial stops expansion; names/ARNs/private structure are sensitive |
| iam:ListMFADevices | Exact human user ARN; >=1 owner-recognized registered device | Serial/device metadata is private. Empty/unrecognized stops; registration is not session MFA |
| iam:GetPolicy | Exact proposed boundary ARN; expected absent NoSuchEntity, or an unexpected existing resource to reconcile | AccessDenied != absence. Never replace/adopt on discovery; known ARN absence does not prove no name collision under another path |

Do not request ListUsers, ListPolicies, GetAccountAuthorizationDetails, a credential
report, access-key values, ListBuckets or Organizations APIs for this unit.

### A3: explicitly approved policy/group closure

From A2, owner approves the **exact** reachable group/policy ARN list before more
reads. Read each unique managed policy's default version, each named user/group
inline policy and any existing boundary's default version. Do not follow arbitrary
names from an unreviewed API result. AWS-managed policy ARNs may use account `aws`;
customer policy ARNs must match the private account. Do not assume usernames have
root IAM paths.

```powershell
# A3: each variable is one independently reviewed A2 result.
aws iam get-user-policy --user-name $F4UserName --policy-name $F4InlineName @F4AdminIam
aws iam get-policy --policy-arn $F4ManagedArn @F4AdminIam
aws iam get-policy-version --policy-arn $F4ManagedArn --version-id $F4DefaultVersion @F4AdminIam
aws iam list-attached-group-policies --group-name $F4GroupName @F4AdminIam
aws iam list-group-policies --group-name $F4GroupName @F4AdminIam
aws iam get-group-policy --group-name $F4GroupName --policy-name $F4GroupInlineName @F4AdminIam
```

Permissions: GetUserPolicy on exact users; GetPolicy/GetPolicyVersion on exact
approved policies; ListAttachedGroupPolicies/ListGroupPolicies/GetGroupPolicy on
exact discovered-and-approved group ARNs. No IAM management Allow is proposed.
Read decoded policy JSON privately; check Statements, NotAction/NotResource, policy
variables, group grants, explicit denies, boundaries and dates against an owner
allowlist. Human admin's expected account-administration authority is distinct from
state-user authority. State should have only reviewed authentication grants before
temporary state grants; reject EC2/IAM/PassRole/AssumeRole or unrelated S3 authority.
Confirm no active old delegation on policy-administrator. Findings describe the
inspected policy set, not every possible resource-based/cross-account grant.

### A4: intended authentication context, optional sensitive read

Accept existing MFA setup. Require privately attested fresh MFA console/browser
authentication, known direct-login config and unchanged cache source. Do not call
GetSessionToken, AssumeRole or re-enroll devices to “check MFA.” GetCallerIdentity
and ListMFADevices cannot prove `aws:MultiFactorAuthPresent` for an API request.

If current existing CloudTrail history is needed, separately approve one bounded
read in the attended UTC interval. `cloudtrail:LookupEvents` needs Resource `*`;
it can reveal unrelated account activity and is therefore **not in minimum A1/A2**.

```powershell
# A4 only; exact endpoint/profile, no trail or event-data-store creation.
$F4AdminTrail = $F4Common + @('--profile', $F4AdminProfile, '--endpoint-url', 'https://cloudtrail.us-east-1.amazonaws.com')
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=GetCallerIdentity --start-time $F4ReadStart --end-time $F4ReadEnd @F4AdminTrail
```

Correlate event timestamp, private caller and session evidence; parse CloudTrailEvent
privately. Missing/delayed/unmatched events or absent MFA context are **inconclusive**,
not false/true by assumption. No automatic polling, new event-context instrumentation,
trail, Lake or export. CloudTrail MFA fields and IAM condition availability are
not interchangeable; owner must accept sufficient evidence before mutations.
[IAM audit context](https://docs.aws.amazon.com/IAM/latest/UserGuide/cloudtrail-integration.html).

## B. AWS policy validation before creation

### B1: IAM Access Analyzer ValidatePolicy

Preconditions: A identity/account evidence, real private policy produced by the
accepted boundary-only generator, owner-approved bucket/user ARNs and exact source/
document hashes. Parse strict JSON locally; no duplicate fields; 14 expected
statements; exact state/lock paths; four Allows and ten reviewed denies; compact
managed-policy body <=6,144 characters. Validate actual-length output, not the
3,300-character synthetic example. ValidatePolicy also limits policy-document text
to 131,072 characters; that is not a bound on the entire HTTP request envelope.

```powershell
# B1 approval: sends the exact private policy to the AWS validation service.
aws accessanalyzer validate-policy --policy-document ('file://' + $F4PolicyFile) --policy-type IDENTITY_POLICY --locale EN @F4AdminAA
```

Permission `access-analyzer:ValidatePolicy` uses Resource `*` (no policy resource
is created). Type is **IDENTITY_POLICY**, not a fictional boundary-policy type.
Omit `--validate-policy-resource-type`; that option is for RESOURCE_POLICY. One
page only; nextToken means validation incomplete and STOP for an approved next
request. Do not silently enable automatic CLI paging.
[CLI type/options](https://docs.aws.amazon.com/cli/latest/reference/accessanalyzer/validate-policy.html).

ValidatePolicy is a published **no-additional-charge** check. It does not require
creating an analyzer and changes no IAM policy/attachment; it still discloses the
document to AWS and produces account audit/usage. No CreateAnalyzer, unused/internal
analyzer, CheckNoNewAccess/CheckAccessNotGranted/CheckNoPublicAccess or other paid
custom check is included. Free-plan availability/account authorization is not
proven by a public price page; denial stops, never upgrades the account.
[Access Analyzer pricing](https://aws.amazon.com/iam/access-analyzer/pricing/).

Review all returned findings: ERROR blocks; SECURITY_WARNING blocks pending
independent disposition; WARNING and SUGGESTION require issue-by-issue written
disposition, not blanket suppression. Check unsupported action/resource combinations,
ARN format, S3 prefix/context operators and separate single-fault denies. Review
the documented public-client auth wildcard as an intentional exception; do not add
MFA/region/time conditions that break pre-login OAuth. S3 conditions do not verify
bucket ownership. Zero findings is not a proof of effective security or live login.

### B2: optional, explicitly separate IAM simulation

Recommended before attachment if the owner approves this account API. Use
**SimulateCustomPolicy**, not automatically attached-principal simulation, to
compare the exact proposed boundary with the exact plan-only/full-state/auth
identity documents. Permission `iam:SimulateCustomPolicy` has Resource `*`;
GetContextKeysForCustomPolicy is optional separate scope, not needed for known keys.

```powershell
# B2: private reviewed API-shaped JSON, one bounded case-group per invocation.
aws iam simulate-custom-policy --cli-input-json ('file://' + $F4SimulationRequest) @F4AdminIam
```

The private request contains `PolicyInputList` (identity grants), one
`PermissionsBoundaryPolicyInputList`, `ActionNames`, `ResourceArns`, private user
`CallerArn`, and typed `ContextEntries`. Explicitly supply PrincipalArn/account,
RequestedRegion, SecureTransport, s3:prefix and CurrentTime where the grant needs
them; supplied MFA is hypothetical, not evidence of session authentication.
Do not simulate the boundary as a standalone identity grant.

Matrix: auth localhost/remote with no S3 context; state Get/Put vs state Delete;
lock Get/Put/Delete; env:/ listing vs missing/other prefixes; unrelated bucket/key,
workspace/access-point paths; IAM/EC2/PassRole/AssumeRole; wrong/missing S3 context;
expired identity grant; optional same-account direct-user resource Allow inside
and outside the ceiling. Expect plan-only state Put denied, full-state Put allowed,
and prohibited paths explicitly denied. Empty MissingContextValues and untruncated
results are required; record PermissionsBoundaryDecisionDetail where returned.

For a resource-policy case supply one applicable `ResourcePolicy`, explicit
`CallerArn` user and account `ResourceOwner`. Do not use IAM role simulations as
proof for the user/resource-policy interaction. Simulator limitations, hypothetical
context and service-specific behavior can differ from AWS. Neither it nor ValidatePolicy
proves S3 403/404 behavior, actual MFA, all resource policies or successful CLI login.
[Simulation API](https://docs.aws.amazon.com/cli/latest/reference/iam/simulate-custom-policy.html).

Persistent ceiling limitation remains: a direct-user resource grant **within** it
can bypass absent/expired identity grants. Explicit denies close prohibited paths,
not the origin of an allowed action. Keep bucket policy TLS-deny-only and resource
writers trusted; do not claim identity-window enforcement against malicious resource
administrators. No policy or boundary is attached by B.

## C. Create only the customer-managed boundary policy

Preconditions: A/B complete, reviewed findings, unchanged real body/name/account,
exact root-path managed-policy ARN approved and expected absent, IAM change freeze,
human-admin MFA evidence and explicit single CreatePolicy authorization.

```powershell
# C WRITE approval; no identity attachment. Description intentionally contains no IDs.
aws iam create-policy --policy-name $F4BoundaryName --path / --description 'F4 persistent state operator ceiling' --policy-document ('file://' + $F4PolicyFile) @F4AdminIam
# C readbacks must also be approved; use exact returned-and-expected ARN/version.
aws iam get-policy --policy-arn $F4BoundaryArn @F4AdminIam
aws iam get-policy-version --policy-arn $F4BoundaryArn --version-id $F4BoundaryVersion @F4AdminIam
```

Required: `iam:CreatePolicy`, GetPolicy/GetPolicyVersion on only the exact proposed
policy ARN. No tagging/version-management grant or inline PutUserPolicy is added.
Expected response: same-account customer policy, expected name/path/Arn, initial
default v1; canonical decoded document equals the approved bytes semantically.
Record PolicyId/version privately. CreatePolicy creates v1/default; it **does not
attach a boundary or grant state access**.
[CreatePolicy semantics](https://docs.aws.amazon.com/IAM/latest/APIReference/API_CreatePolicy.html).

EntityAlreadyExists/timeout/cancellation/unknown response means STOP. GetPolicy and
GetPolicyVersion reconcile; never create another version, change a default, rename,
adopt an existing policy or retry a write blindly. A newly created unused policy
can simply remain while review proceeds. Deletion requires separate authorization,
GetPolicy attachment/boundary-usage counts of zero and exclusive-change evidence.

## D. Attach and verify the boundary

Recheck exact state UserId/Arn, current boundary field, effective grants and the
pinned managed-policy default/body before attach. Expected authentication-only
state identity has no active bootstrap/delegation grant. Different/existing boundary
is a conflict, not permission to replace it. IAM APIs lack a compare-and-swap for
this operation: an attended no-concurrent-IAM-change window is required.

```powershell
# D1 WRITE approval: user only; the policy ARN is customer-managed, not an inline name.
aws iam put-user-permissions-boundary --user-name future-f4-state-operator --permissions-boundary $F4BoundaryArn @F4AdminIam
# D1 verification reads; no state-operator IAM-management permission is introduced.
aws iam get-user --user-name future-f4-state-operator @F4AdminIam
aws iam get-policy --policy-arn $F4BoundaryArn @F4AdminIam
aws iam get-policy-version --policy-arn $F4BoundaryArn --version-id $F4BoundaryVersion @F4AdminIam
```

Required: `iam:PutUserPermissionsBoundary` on exact state-user ARN, constrained to
the approved `iam:PermissionsBoundary` ARN if any temporary administrative policy
is designed; GetUser and exact policy reads. Never use AttachUserPolicy or the old
PutUserPolicy delegation to install a boundary. They are different permission paths.
The policy-administrator proposal grants none of this setup authority and stays inactive.

Success: GetUser reports the exact boundary ARN, policy default/body unchanged;
effective authentication grant remains intact. Treat propagation as eventual:
readback alone is not proof all services enforce a new boundary. Keep state grants
inactive until review; simulate prohibited writes rather than attempting live
CreateBucket/RunInstances/DeleteObject/IAM mutation to “test denial.” A wrongly
allowed destructive probe would itself be unauthorized.

D2 separately approves one real state-user signing read and, if needed to verify
OAuth authorization after attachment, **one explicit browser-login flow**. The owner
has already enrolled MFA; do not repeat setup. Existing cached-credential STS success
does not test AuthorizeOAuth2Access/CreateOAuth2Token under the boundary.

```powershell
# D2-read approval; does not grant another login or any S3 access.
aws sts get-caller-identity @F4StateSts
# D2-login needs separate authentication/cache/destination approval; never automatic.
aws login --profile $F4StateProfile --region $F4Region
```

Unknown IAM outcome: reconcile via human GetUser/default-version reads before
anything else. Login failure: preserve the boundary and stop. Prefer an independently
reviewed replacement that remains at least as restrictive, rather than removing it.
Any removal/replacement/default-version change needs new approval, effective-policy
inventory and revoked/expired temporary grants first. A boundary is not a grant,
so detaching it can **expand** permissions; it is not an automatically safe rollback.

## E. Human-administrator six-resource S3 bootstrap

### Verified inventory and remaining offline tooling prerequisite

Bootstrap root uses `backend "local" {}`; protected-bucket module has
`backup_retention=false` here. Exactly six create-only managed addresses:

```text
module.state.aws_s3_bucket.this
module.state.aws_s3_bucket_public_access_block.this
module.state.aws_s3_bucket_ownership_controls.this
module.state.aws_s3_bucket_versioning.this
module.state.aws_s3_bucket_server_side_encryption_configuration.this
module.state.aws_s3_bucket_policy.tls
```

Required protections: force_destroy=false and prevent_destroy; all four public
blocks; BucketOwnerEnforced; versioning Enabled; SSE-S3 AES256; deny insecure
transport on bucket/objects. No state expiry lifecycle, IAM resource, KMS key or
DynamoDB table. Six Terraform resources are **not** six API requests.

**NO-GO before a narrow offline correction is separately reviewed:** the existing
legacy helper's `operator_spec` requires both principals to be the state user.
`validate_policies`/plan review also assumes equal principals; the private runner's
plan preparation selects that operator. Boundary-only mode correctly accepts human
bootstrap/state separation but explicitly cannot review a bootstrap plan. Therefore
the current guarded workflow cannot be reused unchanged for a human bootstrap.
Do not spoof equal principals, call raw Terraform around the guard or relax scopes.

Proposed correction for separate owner review: explicit human-bootstrap preparation/
review mode binding HumanAdmin profile/Arn to bootstrap proposals and state-user
Arn to state/plan proposals; preserve six-resource checks, source hashes, windows,
account/TLS/region conditions and legacy offline compatibility. Add negative
principal-swapping/account/source tests; implement a reviewed human capture/egress
path. This runbook does not implement or authorize that change.

### E-offline then separately E-plan

Use a fresh protected copy of the **existing** bootstrap root/module/lock, local
state path and source manifest. Preserve private local state and encrypted recovery
copy outside the managed bucket forever; never self-host bootstrap state. The
private var file has human bootstrap ARN and state-user state ARN. Its real values
are not public. Installed binaries/locks and fresh direct-login source are attested.

```powershell
# E-offline: cached-only plugins, no credentials/network; clean copied LOCAL root.
& $F4Terraform "-chdir=$F4BootstrapRoot" init -input=false -lockfile=readonly -no-color
& $F4Terraform "-chdir=$F4BootstrapRoot" validate -json
# E-plan: separate account/network/privacy authorization and reviewed human runner.
# Provider context has ONLY human profile/config/cache; no operator/default fallback.
$env:AWS_PROFILE = $F4AdminProfile
$env:AWS_DEFAULT_PROFILE = $F4AdminProfile
& $F4Terraform "-chdir=$F4BootstrapRoot" plan -input=false -no-color -detailed-exitcode -lock-timeout=0s "-var-file=$F4BootstrapVars" "-out=$F4BootstrapPlan"
# LOCAL saved-plan review through private bounded capture, never public stdout.
& $F4Terraform "-chdir=$F4BootstrapRoot" show -json $F4BootstrapPlan
```

E-offline needs the existing filesystem plugin mirror/no-direct configuration and
senderless isolation. It must not inherit real credentials. Do not confuse local
init with deployment-root S3 init. E-plan is not read-only account metadata by fiat:
provider STS validation and any existing-state refresh are real API reads. An empty
initial state is required; unexpected state/bucket discovery stops for recovery.

Expected exit2 and exact six creates; no delete/update/import/adoption, IAM/new
services or protection loss. Review root/module/lock/input and exact binary-plan
hash privately, sensitive outputs, account/region and source attestation. The
future corrected guard must distinguish both principals. No stdout plan logs,
`-target`, `-replace`, `-destroy`, `-lock=false` or unsaved-plan auto-apply.

### E-apply: separate creation approval

```powershell
# E-apply approval must name this exact reviewed binary and human identity/window.
& $F4Terraform "-chdir=$F4BootstrapRoot" apply -input=false -no-color $F4BootstrapPlan
```

Human authority: the existing exact-bucket bootstrap proposal's CreateBucket,
TagResource/PutBucketTagging, PutBucketPublicAccessBlock, PutBucketOwnershipControls,
PutBucketVersioning, PutEncryptionConfiguration, PutBucketPolicy; plus its explicit
ancillary ListBucket/GetBucketLocation/Tagging/PublicAccessBlock/Ownership/Encryption/
Policy/Acl/CORS/Website/Versioning/Accelerate/RequestPayment/Logging/Lifecycle/
Replication/ObjectLock reads. Exact account/region/principal/TLS/window. Existing
human admin authority does not remove source/cost/approval restrictions; no new IAM
grant is silently required or installed. State operator receives none of these.

Review the pinned provider's tag-on-create/fallback/consistency behavior and exact
actual service destinations before launch. Regional STS and the exact regional S3
service/bucket endpoints are the proposal; unapproved global S3, s3-control,
redirect, alternate bucket or refresh blocks. Do not silently enlarge the egress
allowlist to make bootstrap succeed. Deadline expiry can leave partial resources.

### E-read: post-apply protection/ownership checks

```powershell
# E-read: human only, exact bucket plus expected-owner guard; not automatic after apply.
aws s3api head-bucket --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
aws s3api get-bucket-location --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
aws s3api get-public-access-block --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
aws s3api get-bucket-ownership-controls --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
aws s3api get-bucket-versioning --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
aws s3api get-bucket-encryption --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
aws s3api get-bucket-policy --bucket $F4Bucket --expected-bucket-owner $F4Account @F4AdminS3
```

Expected: successful expected-owner check; GetBucketLocation null/absent location
constraint for **us-east-1**, not an invented string requirement; all protections
above; only reviewed TLS-deny policy, no direct-user Allow. Bucket ARNs lack account
IDs, so PrincipalAccount alone did not prove owner. A 403/redirect is not absence
or permission to adopt another bucket. Record private region/owner evidence.

Failure/partial/ambiguous apply: stop, retain local state/plan/source and encrypted
recovery copy, authorize exact reconciliation reads and a new reviewed plan. Never
rerun apply blindly, import/adopt, delete the bucket or relax protection to clear an
error. Image rollback does not roll back state or IAM. Retention: manual 30-day or
earlier Free-plan-expiry review; no deletion until recovery/teardown inventory and
separate all-version cleanup are approved. prevent_destroy is a Terraform guard,
not an account-wide S3 deletion denial.

## F. Genuine S3 backend compatibility — after an existing protected bucket

### What can precede bootstrap

A/B and local pinned-core experiments can check identities, documents and fake
protocol behavior without a bucket. They cannot prove bucket owner/region,
conditional ListBucket evaluation, real empty-state HEAD status, versioning or
native lock semantics. Do not run fake-to-live endpoint substitutions as a probe.

### F-read: least-risk empty/current-state observations

First E-read establishes ownership/protections. Owner separately approves temporary
**plan-only** state identity access from the existing proposal; its attachment is
an independent IAM write naming exact body/user/window. Do not activate the old
policy-administrator delegation or full state writer. Human performs installation
only under that approval; source/broker support must be reviewed first.

```powershell
# Optional grant installation WRITE, separate from every compatibility read.
aws iam put-user-policy --user-name future-f4-state-operator --policy-name $F4PlanGrantName --policy-document ('file://' + $F4PlanGrantFile) @F4AdminIam
# F-read: human establishes real missing/existing state, operator observes its own response.
aws s3api head-object --bucket $F4Bucket --key $F4StateKey --expected-bucket-owner $F4Account @F4AdminS3
aws s3api head-object --bucket $F4Bucket --key $F4StateKey --expected-bucket-owner $F4Account @F4StateS3
aws s3api list-objects-v2 --bucket $F4Bucket --prefix 'env:/' --expected-bucket-owner $F4Account @F4StateS3
```

Effects: IAM installation changes identity permissions; HEAD/LIST read S3 only and
may be billable. IAM grant readback/expiry/removal also need explicit approval.
The state boundary is persistent, but identity grants remain <=2h and names/body
must be verified before any add-or-replace API; no blind PutUserPolicy replay.

| Observation | Interpretation / stop |
| --- | --- |
| Human authorized HEAD returns404; state HEAD returns404 | Missing object as observed with each caller; proceed only with exact owner/protection evidence |
| Human404; state403 | Object absence is known from human evidence, but operator authorization/not-found handling is incompatible or inconclusive. Preserve prefix; stop remote init/plan |
| Both403, wrong owner/region or redirect | No reliable absence/permission conclusion; stop |
| HEAD200 | Existing object: record ETag/VersionId/size privately; do not delete/overwrite to manufacture an empty bucket |
| env:/ list200 | Observed workspace-discovery metadata only, not state-object or other-workspace permissions |
| env:/ list403 | Failure for this policy/path; pinned default-workspace fallback existed offline, but do not call it successful list authorization |

S3 distinguishes missing-object 403/404 according to ListBucket authorization.
The boundary's explicit missing/other-prefix deny may matter to internal checks.
The retained `env:/` condition is not silently changed. CLI expected-owner checks
and local fake404 cannot prove real S3 evaluation.
[HeadObject authorization](https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html).

Existing state read: human first confirms approved content size <=1MiB and exclusive
window; operator GetObject uses observed current ETag and bounded range/file. Check
complete length and matching current version; never treat a partial download as state.

```powershell
# F-read-existing only; local output must be protected and bounded, not public logging.
aws s3api get-object --bucket $F4Bucket --key $F4StateKey --if-match $F4StateETag --range 'bytes=0-1048575' --expected-bucket-owner $F4Account $F4PrivateReadback @F4StateS3
# Separate human version metadata reads, not permissions for state operator.
aws s3api list-object-versions --bucket $F4Bucket --prefix $F4StateKey --expected-bucket-owner $F4Account @F4AdminS3
```

Human needs ListBucketVersions; state operator must not receive ListBucketVersions,
GetObjectVersion or DeleteObjectVersion. Version listing prefix may include lock/
similar names: filter exact keys privately and stop unexpected contents. Versioning
is not restore proof; an actual restore is a separately approved state mutation.

### F-init / F-lock: native core, explicit remote and lock approval

Use one disposable **backend-only** private root, pinned core, no provider/resources,
with exact default-workspace key, encrypt=true, use_lockfile=true, workspace_key_prefix
env:, explicit state profile, allowed account and approved private backend settings.
No prior `.terraform`, local state, workspace override, migration or force-copy.
Only run this configuration against absent state or an owner-reviewed empty-resource
synthetic seed. Never use empty configuration to plan destruction of real deployment state.

```hcl
terraform {
  required_version = "= 1.17.0"
  backend "s3" {}
}
```

```powershell
# F-init separately approves one REAL remote-backend init (not run in this milestone).
& $F4Terraform "-chdir=$F4CompatibilityRoot" init -input=false -no-color "-backend-config=$F4CompatibilityBackend"
# F-lock separately approves one plan's conditional lock PUT/GET/DELETE and read costs.
& $F4Terraform "-chdir=$F4CompatibilityRoot" plan -input=false -no-color -detailed-exitcode -lock-timeout=0s "-out=$F4CompatibilityPlan"
```

Expected observations: default workspace only; env:/ discovery; exact-key HEAD/GET;
one owned native lock lifecycle; exit0/no changes for empty resources; current state
version/body unchanged. Lock body contains operator/host/path/ID/time: approve its
S3 destination/retention privately. Init was read-only in tested fake cases, but no
general promise prevents a real core from requiring an initial state write. The
plan-only grant denies it: if required, stop for review, never broaden automatically.
Do not disable locking, change key/workspace, catch403 as missing, use force-unlock,
or automatically retry the generation/plan after a lost response.

Prefer native locking to hand-crafted locks. A failed/stalled plan requires owned
process cancellation/await, an exact-key readback and a separately authorized own-lock
recovery after proving no live holder and matching native lock ID. No automatic
DeleteObject or state deletion. A versioned lock delete leaves markers/noncurrent
versions; count them toward retention/cost. No concurrent plan is permitted until
uncertain lock outcome is reconciled.

### F-seed: alternative only if missing-state behavior blocks progress

Lowest-risk decision is to stop and review evidence. Two alternatives require new
approval: narrowly adjust identity **and boundary/deny tests together** only for a
demonstrably necessary exact prefix; or human initializes the exact state object.
Adding the state-key prefix is not assumed to fix a missing-prefix internal check.
No empty-prefix, all-bucket or wildcard workspace expansion is proposed.

For the seed alternative, separately review an offline-generated minimal Terraform
format4 state (1.17.0, serial0, fresh opaque lineage, empty outputs/resources), verify
it locally, and require human expected-owner HEAD404 plus exclusive change window.
Use one conditional, AES256 PutObject; **not** an operator full-writer grant.

```powershell
# F-seed WRITE approval: creates one state-object version; no overwrite on race.
aws s3api put-object --bucket $F4Bucket --key $F4StateKey --body $F4SeedState --content-type application/json --server-side-encryption AES256 --if-none-match '*' --expected-bucket-owner $F4Account @F4AdminS3
```

412/409/timeout means stop and reconcile, not retry/overwrite. Capture exact version,
read back/validate payload privately and re-run separately approved F-read/init/lock
steps. Do not delete the seed as rollback: preserve lineage and version history.
State push, migration, restore, marker/version deletion and object initialization
are mutations, not “read-only validation.” No seed is produced/uploaded by this task.

## G. Provider/backend identity architecture and deployment readiness

### Alternatives and recommendation

| Alternative | Selection / scope / lifecycle | Decision and risks |
| --- | --- | --- |
| State user for backend and provider | Existing shared AWS_PROFILE; would need provider inventory/provisioning actions | Reject: boundary intentionally denies them; do not widen it even just to get a plan |
| Human admin provider + state backend | Backend explicit profile, provider human environment | One-time **bootstrap only**, not routine application deployment; broad credentials in Terraform process |
| Preflight provider + state backend | Existing read-only profile for provider, state plan-only backend grant | Optional read-only planning alternative after exact missing reads are reviewed; no apply and no AssumeRole-to-write on preflight |
| Human-admin source_profile → new scoped deploy role | Explicit assumed role for provider; state backend independent; <=1h role session/window | Good temporary-credential pattern, but source admin cache is exposed to the provider process; a compromised client could use it directly. Role trust/MFA/source-chain compatibility adds untested work |
| **New nonadmin direct-login deployment user + state backend** | Separate existing-pattern browser login, temporary exact-project provisioning policy; no access keys/admin cache; explicit profiles | **Recommended for this bounded standalone exercise**, subject to owner review and host-role escalation correction below. One new identity; no role chain/Organizations/Identity Center |

Proposed name `future-f4-deployer` is **not established/created**. Human admin handles
its separately approved Console/MFA setup and grants; owner can choose a reviewed
role instead. Routine Terraform never receives human/preflight/policy-admin login
cache entries or broad AdministratorAccess. New identity/grants are explicit owner
decisions, not implied by this recommendation.

Use existing Terraform integration: private deployment `.tfbackend` sets
`profile="future-f4-state-operator"`; provider uses explicit
`AWS_PROFILE=AWS_DEFAULT_PROFILE=future-f4-deployer`, with selected-only config,
empty static credentials, isolated home, IMDS off and two approved login-cache
entries only. Backend and provider allow the same private account; verify each
principal separately with frozen context. No provider secrets in HCL/state.
[Backend profile option](https://developer.hashicorp.com/terraform/language/backend/s3).

No Terraform definition change is needed merely to select these two sources, but
the existing single-profile mock evidence is not proof of dual-profile precedence.
Before live planning, separately approve offline tests with both synthetic users,
poisoned defaults, wrong/missing cache, rejected refresh and identity postconditions.
Extend private backend-config validation under review; no credential_process fallback
or real profile/configuration is created here. Backend plan-only permission includes
lock writes; a later apply requires separately approved exact-state PutObject.

### Material provider IAM risk requiring review before grants

The existing deployment root manages the EC2 host role, instance profile and inline
role policy. Exact-role `iam:PutRolePolicy` plus PassRole/RunInstances can still
escalate if the deployer can put arbitrary permissions on that role and obtain its
credentials. Restricting ARN/name alone cannot restrict that JSON body. The same
principle that blocked unsafe PutUserPolicy delegation applies here.

Recommend a **separately human-created host-role permissions ceiling**, required on
CreateRole and protected from removal/replacement by deployer permissions. This
ceiling would contain only reviewed SSM/ECR/backup permissions, no IAM administration.
The deployer may manage only the exact project host role/profile and pass it only
to EC2 (`iam:PassedToService=ec2.amazonaws.com`); it cannot edit the ceiling/default
version, its own grants, state-user grants or any other roles. An alternative is
to move IAM ownership into a separately administered security bootstrap. Both are
**material, unimplemented proposals requiring owner/source review**; do not grant
current-role policy editing until one is approved and tested.

Deployment permission families for that future design: exact tagged/project VPC,
subnet/routes/SG, t3.small/approved AMI/volumes and attachments; exact ECR repos,
backup bucket, SSM documents; exact host IAM objects with the ceiling controls.
Some Describe/create APIs require Resource `*`; pair supported tag/region/type
conditions and review per action. No administrator/wildcard-service policy is
prepared here. Stop on unsupported scoping rather than guessing least privilege.

Future command skeletons, **blocked** on that policy/configuration review:

```powershell
# G-identity/account WRITE approval would be separate; no login/key/MFA setup follows.
aws iam create-user --user-name future-f4-deployer @F4AdminIam
# G-backend: independent remote init; private backend profile is the state user.
$env:AWS_PROFILE = 'future-f4-deployer'
$env:AWS_DEFAULT_PROFILE = 'future-f4-deployer'
& $F4Terraform "-chdir=$F4DeploymentRoot" init -input=false -lockfile=readonly -no-color "-backend-config=$F4DeploymentBackend"
# G-plan: provider reads + backend lock writes; one saved plan, fresh independent review.
& $F4Terraform "-chdir=$F4DeploymentRoot" plan -input=false -no-color -detailed-exitcode -lock-timeout=0s "-var-file=$F4DeploymentVars" "-out=$F4DeploymentPlan"
# G-apply: distinct creation/spending approval for this exact plan, never bundled with G-plan.
& $F4Terraform "-chdir=$F4DeploymentRoot" apply -input=false -no-color $F4DeploymentPlan
```

No actual deployment permission document, identity creation, host-ceiling source
change, grant, plan or apply is authorized here. Preconditions additionally include
approved AMI/host-tool attestation, digest-pinned images/ECR publication approval,
exact AZ/quota usage, loopback-only synthetic access, UID10001/999/IMDS fences,
SSM-only zero inbound, backup/restore and explicit retained-resource teardown.
SSM operational authority is not the state user. Retained EBS/ECR/backups and IAM
resources survive some application rollbacks; follow existing recovery spec.

## Costs, Free-plan limits and stop controls

The **$0.05 gross maximum proposal** and **$0.02 operational stop** remain unapproved
and are not AWS-enforced caps. IAM/validation being published no-charge is not
authorization. Credits are not spending approval. Owner must approve gross/credit
consumption, expiry, request inventory, window and retained-storage allowance.

| Item | Published assumption / uncertainty and controls |
| --- | --- |
| IAM/STS metadata and IAM policy resources | IAM offered at no additional charge; signed requests/audit disclosure still require approval. Existing paid audit copies/features could have ancillary costs; no account billing configuration inspected |
| ValidatePolicy | Basic policy validation no additional charge; paid custom checks/internal/unused analyzers excluded; no analyzer resource created |
| S3 Standard us-east-1 | Provisional public-guide rates: $0.023/GB-month; $0.005/1,000 PUT/COPY/POST/LIST; $0.0004/1,000 GET/other requests. Reconfirm exact regional control/tagging tariffs before E; these are not account-specific binding quotes |
| State/locks | Every version/marker can persist after overwrite/delete. No automatic state expiry; operator has no version-cleanup permissions. Bound number of operations and retained total bytes, including locks |
| Encryption/other services | SSE-S3, not a new KMS key; no DynamoDB, paid analyzer, new trail/Lake/data-event export, NAT, budget or monitoring service in A–F |
| Event history | Optional existing management-event history only; no trail delivery/data-event configuration. Billing dashboard manually reviewed; no Cost Explorer API/query or budget creation without separate permission/cost review |
| G deployment | EC2, public IPv4, EBS, ECR, backup/version storage and retention add recurring/idle costs. Existing proposal22 is an estimate, not this $0.05 envelope; reprice and obtain a distinct deployment/teardown budget before G-apply |

Illustration, **not a guaranteed maximum**: 200 billed PUT/LIST-class requests +
1,000 GET-class requests + 10MiB of all retained versions for 30 days, conservatively
treated as 0.0105GB-month, gives `0.001 + 0.0004 + 0.0105*0.023 ≈ $0.00165` before
uncertain control/tagging/account-specific charges. Failed calls, retries/waiters,
payload sizes/versions, other account usage, audit configuration and price changes
prevent treating this as a spend cap. Six resources are not a request bound.

Sources checked 2026-10-26: [IAM pricing](https://aws.amazon.com/iam/faqs/),
[Access Analyzer pricing](https://aws.amazon.com/iam/access-analyzer/pricing/),
[S3 pricing](https://aws.amazon.com/s3/pricing/),
[AWS N. Virginia cost example/rates](https://docs.aws.amazon.com/solutions/latest/automated-security-response-on-aws/cost.html).
The S3 public table is dynamic; endpoint-specific tariffs remain to be confirmed
in the current price/account context before a cost-bearing approval.

AWS's current Free-plan documentation says the plan ends after six months or credit
exhaustion, whichever first, with no charges on that plan. This is not project
permission to consume credits, a resource-availability guarantee or a recovery
strategy. Verify actual account plan/remaining credits/expiry privately; denial or
upgrade prompt stops. No upgrade, Organizations/Identity Center enrollment or
paid-only feature is proposed. Retain state recovery copies before expiry.
[Free-plan terms](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).

Monitor operation counts/version bytes and forecast retained costs before each
unit. Stop at forecast/observed $0.02 or a lower approved threshold; do not wait for
delayed billing to enforce it. Existing billing/Free Tier console views and owner
review are the monitoring proposal. No new billing budget/alarm is created; such
alerts are delayed and would not create a hard cap anyway. Uncertain writes remain
possible liabilities, including cancellation after a send claim.

## Readiness decision and first authorization request to consider

**GO:** independent review of this plan and separately authorized offline corrections.
**NO-GO:** any live unit under this milestone. Before account execution, resolve
profile/capture/egress binding; A/B account evidence; C/D creation/attachment approvals;
human bootstrap guard adaptation; real S3 behavior; and G's identity/host-IAM design.

First future operation recommended: **A1a only**, one private
`aws sts get-caller-identity @F4AdminSts`, HumanAdmin profile confirmed offline,
regional STS HTTPS/443, <=120s, one SDK attempt/no replay/refresh, exact private
Account/Arn/UserId postconditions, 30-minute attended read window and no mutation.
This is a proposed owner authorization unit, not a request executed or granted
now. Success authorizes neither A1b nor IAM/Access Analyzer/S3/Terraform operations.
