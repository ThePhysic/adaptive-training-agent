# F4-03B-R5B proposal — state bootstrap, then gated infrastructure planning

2026-10-25. **Proposal only. R5A authorizes no resource creation, IAM change,
backend initialization, state/lock write, apply/destroy or paid-plan upgrade.**
Credits are not execution approval. No actual account ID, bucket, principal ARN,
AMI, image digest, permission window or active grant is supplied here.

## Owner authorization request, not yet granted

- Name private account/bucket/operator/authentication route and <=2h UTC window;
  leave preflight read-only. Approve only the exact expiring inline grants below.
- Permit one local-state bootstrap plan, private review, then **separate approval
  of one saved bootstrap apply** creating the protected state bucket/configuration.
- After protection checks, permit one clean deployment-backend init and exact
  lock writes under the narrower plan grant. No deployment-state PutObject grant.
- Permit one real infrastructure plan **only if** concrete AMI/tools/images and
  deployment inputs are approved; otherwise stop after backend verification.
- Proposed allowance **$0.05 gross/credit use**, **$0.02 operational stop threshold**,
  30-day retained-state review before account expiry. No paid upgrade or resource
  deployment. Approve private lock metadata, encrypted recovery copies and cleanup.
- No deployment apply, EC2/ECR publication, recovery/deletion, additional IAM/trust
  changes, credential export, model calls or telemetry follows from these approvals.

## Account and Free-plan assessment

Owner-reported evidence supersedes earlier missing/zero-device findings: us-east-1,
standard On-Demand quota **5 vCPUs**, VPC quota **5**, **one existing VPC**, registered
passkey for the preflight user, **no permissions boundary**, **no S3 buckets**,
apparently standalone, Free plan with **$100 credits**. These are owner findings,
not fresh agent API measurements. No additional AWS calls were needed in R5A.
There are four VPC slots at that observation; current standard-vCPU usage was not
supplied. A later t3.small needs two vCPUs: existing/pending relevant usage must be
at most three before launch. Registration is not execution-session MFA proof;
"appears standalone" needs final owner attestation, not an assumed SCP exemption.

| Planned service/feature | Public evidence / remaining verification |
| --- | --- |
| General-purpose S3 Standard, SSE-S3, versioning, bucket controls and lock objects | S3 is offered under the Free plan; these use normal S3 APIs, not a separate paid lock/checkpoint service. No paid-plan requirement identified for this design; effective per-account authorization/features remain untested until separately approved execution |
| EC2 t3.small and gp3 EBS | Explicitly eligible in the current post-July-2025 credit program; custom AMI eligibility, quota usage and capacity still need review |
| ECR private app/PostgreSQL mirrors | Free/Paid credit offer documented; publication is outside this R5B state/plan proposal |
| SSM Session Manager, IAM/STS and ordinary VPC networking | Public offers cover Session Manager and IAM; no NAT, ALB, endpoints, marketplace software or commitment purchases are proposed. Exact account/AMI/network/IAM behavior remains a deployment gate |

Sources reviewed 2026-10-25: [S3 offer](https://aws.amazon.com/free/storage/),
[EC2/EBS eligibility](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html),
[ECR offer](https://aws.amazon.com/free/containers/),
[SSM offer](https://aws.amazon.com/free/devops/),
[IAM offer](https://aws.amazon.com/free/security/).
The S3 offers page contains an unrelated database example in its feature text;
that text is not evidence for individual S3 API authorization. No broad service
catalog or another sign-up experience is used as proof of this account's rights.

The [Free-plan terms](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html)
limit access and end the plan at six months or exhausted credits; resources/data
can become inaccessible. Owner must record the actual expiry, credit applicability
and recovery deadline. Do not join/create Organizations, configure Control Tower
or perform other automatic-upgrade triggers. IAM denial or unsupported feature
means STOP; do not upgrade. Documented eligibility is not actual deployment proof.

## Reused backend and exact scope

Use the existing `infra/aws/state-bootstrap` local-state root and shared
`protected-bucket` module: **six managed S3 configuration resources**, no new
stack, IAM resource, DynamoDB, KMS key, service, replication or lifecycle expiry.
The deployment root keeps its S3 backend. Native `use_lockfile=true` is supported
by pinned Terraform **1.17.0**; AWS provider remains **6.70.0**.

- Private global-namespace bucket matching `fata-[a-z0-9-]{3,45}-state`, including
  an owner-chosen opaque random component. No account number, username or PII in
  the name. Availability is unverified; collision/403 is a stop, not automatic
  rename/import/adoption. [S3 naming guidance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html).
- Exact default-workspace state key `ec2-demo/terraform.tfstate`; exact lock key
  `ec2-demo/terraform.tfstate.tflock`. Workspace discovery lists only prefix
  `env:/`; no nondefault workspace state read/write permission. Do not create
  or select another workspace. Native core/source verifies this discovery prefix.
- Versioning Enabled, AES256 SSE-S3, BucketOwnerEnforced, all four public blocks,
  HTTPS-only deny policy. `prevent_destroy` and `force_destroy=false` remain.
  No automatic state expiration; review retention after **30 days**, or before
  account/credit expiry if earlier. Retain until deployment teardown, recovery
  and billing inventory are complete, then separately authorize all-version cleanup.
- Bootstrap's own local state/recovery copy stays on owner-controlled encrypted,
  ACL-restricted storage; it never moves into its own managed bucket. No secrets
  in provider/backend HCL, CLI values, Terraform state or app containers.

## Separate permission proposals

The authoritative proposals are `bootstrap_operator_policy`, `plan_operator_policy`
and `state_operator_policy` in the bootstrap root. Outputs are sensitive and predictable
from private inputs before resource creation. **They create/attach no policy.**
Existing `future-f4-preflight` stays read-only; both write-principal variables
reject its exact user name, including a user path. An account owner must select
a different existing tightly scoped operator user/role and its authentication
route. R3 proves the preflight principal, not a newly selected operator.
No profile, assumption, credential_process or role trust is created automatically.

Every proposed statement requires exact principal ARN/account, us-east-1, TLS,
UTC start-inclusive/end-exclusive time, with a positive window **at most two
hours**. These conditions bound this Allow, not other policies; they are **not
an attached IAM permissions boundary** and do not constrain an otherwise privileged
owner. Review effective permissions/trust/session MFA privately before execution.

| Purpose | Proposed scope/actions |
| --- | --- |
| Bucket setup | Exact bucket ARN only: CreateBucket, TagResource (required for tag-on-create), PutBucketTagging (legacy fallback), PutBucketPublicAccessBlock, PutBucketOwnershipControls, PutBucketVersioning, PutEncryptionConfiguration, PutBucketPolicy (all `s3:`) |
| Bootstrap refresh/verification | Exact bucket ARN only: ListBucket, GetBucketLocation, GetBucketTagging, GetBucketPublicAccessBlock, GetBucketOwnershipControls, GetEncryptionConfiguration, GetBucketPolicy, GetBucketAcl, GetBucketCORS, GetBucketWebsite, GetBucketVersioning, GetAccelerateConfiguration, GetBucketRequestPayment, GetBucketLogging, GetLifecycleConfiguration, GetReplicationConfiguration, GetBucketObjectLockConfiguration |
| R5B backend/first plan | ListBucket only for `env:/`; GetObject only exact state key; GetObject/PutObject/DeleteObject only exact lock key. No state write/deletion/version access, bucket administration, object wildcard or ListAllMyBuckets |
| Later state writer, not part of the proposed R5B plan grant | Same binding plus PutObject only exact state key, from state_operator_policy. Requires separate authorization before deployment apply/state persistence |
| IAM grant setup/removal | Owner-managed separate approval: if an existing operator user is selected, exact-user iam:PutUserPolicy/DeleteUserPolicy; if a role, exact-role iam:PutRolePolicy/DeleteRolePolicy. Policy names/bodies, owner identity and expiry must be reviewed. These permissions are not granted to the operator/preflight by Terraform. Creating a role/user or editing trust/PassRole is outside this proposal |
| Later provider plan | Existing read rights plus the state operator grant; normal provider identity validation retained. No EC2/ECR/IAM create actions or PassRole merely to plan. If actual state exists, enumerate exact resource-refresh reads first; stop instead of broadening on denial |

Ancillary reads are required by the
[pinned bucket resource](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.70.0/internal/service/s3/bucket.go),
even for unset legacy features. See [S3 API/action mapping](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-policy-actions.html).
The pinned provider first creates with tags, requiring
[TagResource permission](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-create-tag.html).
It can internally retry CreateBucket without tags and then use PutBucketTagging
on documented compatibility/permission errors. These are seven distinct possible
API write types, eight IAM actions; normal tag-on-create may need six API writes.
Do not describe SDK max_retries=1 as suppressing this resource-level fallback.
Unexpected denials/errors must halt the operator; the reviewed pinned fallback
can occur inside one command and remains confined to the approved bucket/actions.

Future destination proposal: HTTPS/443 regional STS
`sts.us-east-1.amazonaws.com` (POST /, GetCallerIdentity) and only the privately
approved `<bucket>.s3.us-east-1.amazonaws.com`. Bucket PUT/GET/HEAD with the
reviewed configuration query set covers setup/refresh; backend permits GET
workspace discovery/state and PUT/GET/DELETE exact `.tflock` only. No state PUT
in the first-plan grant. Review pinned SDK regional endpoint behavior before
launch; do not silently permit global S3, s3-control, redirects, another bucket,
proxy, custom CA or Sign-In refresh. Normal TLS verification is mandatory.
An opaque CONNECT guard proves destination/bytes, not HTTPS methods/API counts;
the latter restriction also relies on exact IAM and pinned reviewed source.
No TLS interception/new proxy service is proposed.
No bucket/feature Delete action, object access or wildcard service action belongs
to bootstrap setup. Grant expiry must still permit owned lock release; stop
launching work with less than five minutes of approved time remaining. If expiry
or interruption strands a lock, preserve it for a separately approved recovery
identity; do not extend the grant or force-unlock automatically.

## Proposed execution checkpoints — not run in R5A

1. **Owner approval before any grant/write:** privately name account, separate
   operator, exact bucket, source/locks, permission start/end, authenticated MFA
   evidence, Free-plan expiry, privacy/retention and numerical gross/credit-use
   budget. Keep preflight untouched. An already authorized owner performs only
   the specifically approved inline-policy attachment/removal, if needed. No
   administrator shortcut, new profile, credential export or automatic refresh.
2. **Prepare private inputs:** write the six reviewed fields (account_id,
   bucket_name, bootstrap_principal_arn, state_principal_arn,
   permission_starts_at, permission_expires_at) into ignored `.cache/` JSON.
   `python infra/aws/state_bundle.py --spec <PRIVATE_CACHE_JSON> --name <OPAQUE_LABEL>`
   only creates a private local input bundle. It cannot run AWS/Terraform. Require
   READY plus exact files; identical repeat is a no-op; changed/partial bundles
   fail without overwrite. Review Windows ACLs and encryption explicitly; POSIX
   file modes are not a Windows ACL guarantee. No real values prepared in R5A.
3. **Bootstrap plan, local state only:** in a private clean copy of the existing
   root/module, use cached locked plugins, local-backend init and one bounded
   `plan -input=false -no-color -detailed-exitcode -lock-timeout=0s -var-file=<PRIVATE_TFVARS> -out=<PRIVATE_BOOTSTRAP_PLAN>`.
   Provider account reads require separate authorization. No S3 backend is involved
   here. Expected initial change: exactly six protected S3 resources, seven distinct
   write operations on apply including tagging. Sensitive policies/backend outputs
   remain private. Stop for unexpected existing bucket/state or any deletion.
4. **Independent approval of that exact saved plan:** verify source/input/plan
   binding privately and authorize **one** apply of the reviewed binary artifact.
   Proposed command shape `apply -input=false <PRIVATE_BOOTSTRAP_PLAN>`; never
   auto-approve a fresh unsaved plan. R5B scope must explicitly include this
   creation and its request/credit costs. It must not include deployment-root apply.
   Capture Terraform stdout/stderr only in bounded private process memory; publish
   classified exits/counts only, never raw CLI logs, plan/state or identifiers.
   Source-review the actual operator capture/timeout/owned-cleanup procedure before
   execution; the identity-only collector is not an apply/plan launcher.
5. **Verify before backend use:** exact bucket owner/region, all public blocks,
   enforced ownership, encryption, versioning and TLS-only policy via approved
   reads. Retain encrypted local bootstrap state plus a recovery copy. Partial
   apply/error/timeout is not absence: retain state, reconcile only reviewed reads,
   and obtain a fresh reviewed plan before any retry. Never import/adopt another
   bucket or recreate over an ambiguous outcome. The provider can internally poll
   or repeat consistency reads/writes; SDK max_retries=1 does not remove these
   higher-level waits. Set a 120-second owned-command deadline, no outer replay.
6. **Separately approved backend init:** switch explicitly to the approved state
   operator route (possibly the same separate operator, different grant). Use
   plan_operator_policy, not the broader later state-writer proposal. Approve
   exact STS and bucket S3 HTTPS destinations, selected methods/paths, core retries
   and captured-output handling. Run at most one clean deployment-root
   `init -input=false -lockfile=readonly -backend-config=<PRIVATE_TFBACKEND>`.
   No migration/force-copy/reconfigure/alternate workspace. Pinned clean init
   against both existing and absent synthetic state performed only identity/list/
   object reads; the following fixture plan wrote/deleted its lock but did not
   persist state. **Locking is write-capable and potentially billable.** The first
   plan grant deliberately denies state PutObject: if any real init/plan needs it,
   STOP for review rather than activating the broader writer. General init modes
   or state migrations are not covered by the observed clean-init result. Preserve
   default locking; no -lock=false. Future send/refresh destinations need review;
   do not widen R3's STS-only tunnel or silently reuse it as a cloud operator.
7. **Infrastructure plan gate:** if concrete AMI/tools, AZ, both image digests,
   deployment inputs and window remain unapproved, stop after backend verification.
   Otherwise separately approve one bounded locked deployment plan with the same
   flags as step 3, protecting the saved plan. Exit 2 means proposed changes, 0
   no changes, 1 failure. Verify expected inventory and unchanged guards; no
   EC2/EBS/ECR/IAM/SSM/backup-resource creation, publication, apply or deployment.
   Later apply requires a freshly valid window and separately approved actual plan.
8. **Finish:** await owned work/lock cleanup, remove only the separately approved
   inline grants, retain private evidence/recovery state and report sanitized
   results. Do not automatically delete the state bucket, versions or local recovery
   files. Record retained storage liability and a dated owner review.

Native local evidence shows core init/repeat/empty fixture plan each make two
synthetic identity reads; this is consumer authentication, not a repeat of R3's
identity-only probe. Real request counts can differ. Missing/malformed credentials,
wrong identity, any unexpected destination or raw diagnostic leakage means STOP;
never fall back to another identity. Credential renewal, effective AWS IAM and
actual S3 behavior remain unverified. No active cloud launcher is shipped by R5A.
Native lock metadata can include operator username/hostname, local path, timestamp
and lock ID. Owner must explicitly approve those private operational fields in S3
and retained lock versions, separately from synthetic business data. Do not publish
lock bodies, state, backend cache, raw output or credentials in logs/archives.

## Proposed R5B financial envelope and stop conditions

**Requested, not granted:** USD **$0.05 gross service/credit consumption** for the
state/plan exercise plus retained state within its 30-day review period; no EC2,
image-build/publication, backup data or paid upgrade. Operational stop threshold
**$0.02 forecast/observed gross**, or any unexpected service/feature/volume.
Do not wait for delayed billing data before stopping an error/retry loop.

Planning allowance: 1,000 S3 requests conservatively priced at $0.005/1,000,
64 MiB total current/noncurrent objects at $0.023/GB-month for one month, and
32 MiB gross egress conservatively at $0.09/GB: approximately **$0.0096** before
credits/tax, leaving margin. These are workload assumptions, not enforced request
or billing caps. No KMS key, DynamoDB, replication, server access logs or analytics
is added. Requote before execution; [S3 pricing](https://aws.amazon.com/s3/pricing/)
and [AWS's published Standard-rate example](https://docs.aws.amazon.com/solutions/latest/automated-security-response-on-aws/cost.html)
support the request/storage assumptions. Existing deployment cost proposal 22 is
separate and still not a grant. Credit use, retention growth, charges after any
future plan change, taxes/FX and other account activity require owner monitoring.

Stop for: missing approval/MFA/source binding; expired window or near-expiry grant;
Free-plan expiry/upgrade prompt; bucket collision/403/unknown owner; unexpected
IAM/API/endpoint; missing protection; partial/ambiguous apply or state/lock outcome;
permission denial; unsupported feature; unexpected state contents; missing AMI or
digests; sensitive output; budget/envelope drift. Preserve recovery evidence and
request the exact next authorization; do not automatically retry or broaden IAM.

## Recovery and eventual deletion — separate approvals

State has indefinite version retention until explicitly deleted. For rollback,
freeze all writers, prove lock owner is inactive, privately select/verify an exact
version/lineage/serial and preserve current state. Recovery needs separately
scoped ListBucketVersions on the bucket plus GetObjectVersion only the state key;
restoring a reviewed prior version to the current key needs PutObject on that key.
Review the next plan for drift; never treat an old state version as resource rollback.
No routine writer can read/delete prior versions or delete state.

Final cleanup follows deployment teardown and an approved version inventory:
ListBucketVersions, GetObjectVersion/DeleteObjectVersion on exact state/lock keys
as approved; DeleteObject for exact remaining current keys/markers; AbortMultipartUpload
only approved uploads if any; named configuration removal and DeleteBucket only
the exact bucket. Source-review temporary lifecycle-guard changes and the resulting
teardown plan. This is **not** the bootstrap/state grant. Do not use force_destroy,
recursive s3 rm, state rm or force-unlock. Retain an encrypted final bootstrap and
deployment-state recovery copy for the owner-approved period; final local deletion
is also explicit. Bucket names may be reclaimed after deletion; never send to an
old backend after cleanup. Revoke grants and verify retained inventory/credits.
