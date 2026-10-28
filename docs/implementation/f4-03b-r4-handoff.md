# F4-03B-R4 — Account evidence and Terraform plan readiness

2026-10-25 (America/Los_Angeles). **Offline preparation complete; real backend
initialization, infrastructure planning and deployment remain NO-GO.**
Starting HEAD: `7f50b6af30f8cb1c0b57553f2c7cbf26a596d927`.

R3's native exit 0 and mandatory private account/ARN/user-ID postconditions are
accepted evidence. No real identity retry, AWS CLI operation, credential/cache
inspection, backend request or account-connected Terraform command ran in R4.
Public documentation was reviewed; that is not new account evidence.

## Account-readiness matrix

All account observations below are historical F4-03B/R3 evidence, not refreshed
by this unit. Owner-provided evidence should carry a UTC observation time, private
exact-account/principal comparison, completeness check and reviewer attestation.
Shared reports retain only classifications, counts and approval status.

| Gate | Accepted evidence / outstanding fact | Smallest next owner action |
| --- | --- | --- |
| Provider identity | **Resolved for R3's fresh session**; pinned Terraform 1.17.0 / AWS provider 6.70.0, exact private postconditions passed | Retain evidence; do not repeat just for a clean coordinator result. This does not establish future credential freshness or backend authentication |
| Coordinator | R3 peer-close correction passed offline; a different guard could still obscure already-completed output in the old ignored executor | Review the new offline-tested collector below; no clean real rerun claimed |
| IAM boundary/effective access | GetUser was denied; named group attachments alone do not resolve effective denies | Supply exact-user boundary or explicit absence; review boundary/default policy versions and session/resource restrictions privately |
| MFA registration | Last own-user ListMFADevices returned zero; current registration unknown | Owner verifies existing registration using the procedure below; any enrollment is a separately authorized IAM change |
| MFA authentication context | STS identity, device registration and login-session ARN do not establish this session's MFA | Attest the actual login/session flow and supported audit/context evidence; unknown stays unresolved |
| Organization | DescribeOrganization denied; standalone/management/member and inherited controls unknown | Existing authorized owner/org reviewer supplies membership and applicable SCP/RCP evidence; do not promote the preflight user |
| EC2 quota/headroom | Applied standard On-Demand quota L-1216C47A denied; project-only inventory cannot establish usage | Supply applied quota and current all-project regional standard-vCPU usage, including pending allocations; require at least two additional vCPUs |
| VPC quota/headroom | One default VPC observed; applied L-F678F1CE denied | Supply applied quota and complete current us-east-1 VPC count; require one additional VPC and recheck CIDR conflicts |
| AZ/AMI/tools | Historical t3.small offerings do not select an AZ or prove capacity; no approved custom AMI | Approve exact AZ and patched x86_64/Nitro/systemd AMI, private owner/source/root size and host-tools hash; masked Docker units, SSM floor and UID fences remain mandatory |
| Images | No approved published app/PostgreSQL mirror digests | Approve both linux/amd64 digests/provenance; image publication is separate write/spend authority. A prospective plan does not prove pullability |
| Backend | No state bucket/key, core authentication, lock or recovery evidence established | Name a reviewed existing dedicated bucket or separately authorize bootstrap; approve precise state/lock access and request costs before init |
| Plan execution | Inputs, current effective read access, source revision/window and backend operations not approved | Approve the bounded procedure below independently of any apply/deploy authority |

No new infrastructure, service, retention allocation or cost assumption was added.
The dated $1.55866 proposal in checklist 23 is an estimate, not a grant or cap.
**$0 new cloud spending authorized.** An S3 backend entails potentially billable
requests/storage even when the provider only reads infrastructure metadata.

## Minimal permission recommendations — proposals only

**Zero additional permissions are necessary in this unit.** Prefer evidence from
an already authorized owner. If the same preflight principal must later collect
missing evidence, the existing placeholder-only
[two-action draft](../planning/proposals/f4-03b-r1-read-permissions.json) remains
the smallest base proposal; it is not attached or modified here.

| Exact proposed action | Exact scope / condition | Purpose and approval boundary |
| --- | --- | --- |
| `iam:GetUser` | `arn:aws:iam::<APPROVED_ACCOUNT>:user/<EXACT_USER_PATH_AND_NAME>` | Own-user boundary metadata; historically denied |
| `servicequotas:GetServiceQuota` | Exactly `arn:aws:servicequotas:us-east-1:<APPROVED_ACCOUNT>:ec2/L-1216C47A` and `arn:aws:servicequotas:us-east-1:<APPROVED_ACCOUNT>:vpc/L-F678F1CE`; `aws:RequestedRegion=us-east-1` | Two applied values; historically denied. No quota increase/list-all grant |
| `iam:GetPolicy`, `iam:GetPolicyVersion` | Only the privately identified boundary/policy ARN(s), including exact publisher account/path | Conditional on an observed boundary/body-review gap; not new observed denials. Prefer owner-reviewed bodies and versions |
| `iam:ListMFADevices` | Same exact user ARN as GetUser | Already succeeded historically; no new grant proposed absent a fresh denial. Never list all virtual devices |
| `ec2:DescribeInstances`, `ec2:DescribeInstanceTypes`, `ec2:DescribeVpcs` | `Resource:"*"`, `aws:RequestedRegion=us-east-1` | Regional quota usage/type-to-vCPU evidence; use existing read rights if sufficient. These list APIs cannot honestly be restricted to project-tagged resource ARNs; returned filters are not IAM boundaries |
| `ec2:DescribeImages`, `ec2:DescribeSnapshots`, `ec2:DescribeInstanceTypeOfferings` | `Resource:"*"`, `aws:RequestedRegion=us-east-1`; requests restricted to approved image/snapshots/type/AZ | Image metadata and availability evidence, using existing reads where sufficient; metadata cannot prove patched contents/tools/digests |
| `organizations:DescribeOrganization` | `Resource:"*"`; no invented per-account ARN or regional restriction on this global service | Optional membership evidence only; historically denied. Prefer owner evidence. Does not establish inherited policy contents |
| `cloudtrail:LookupEvents` | `Resource:"*"`, requested Region restricted to the actual approved sign-in/audit Region(s) | Optional existing event-history inspection by an already authorized reviewer. Time/user filters are data minimization, not IAM scoping; no new trail/Lake/query service or automatic grant |

Exact-user/policy scoping is supported by [IAM's authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_iam.html).
The two quota resource forms are confirmed in [Service Quotas' reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_service-quotas.html).
The EC2 list scopes are documented in [EC2's reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ec2.html);
the optional broad-resource reads in [Organizations](https://docs.aws.amazon.com/service-authorization/latest/reference/list_organizations.html)
and [CloudTrail](https://docs.aws.amazon.com/service-authorization/latest/reference/list_cloudtrail.html).
All were reviewed 2026-10-25. These are structural proposals, not AWS IAM evaluation.

An existing authorized organization reviewer should inspect root→OU→account
inheritance and policy bodies using their existing `organizations:ListParents`,
`ListPoliciesForTarget`, `DescribePolicy` rights as applicable. No such grant is
proposed for this learner identity. DescribeOrganization alone is insufficient;
[DescribeEffectivePolicy excludes SCPs/RCPs](https://docs.aws.amazon.com/organizations/latest/APIReference/API_DescribeEffectivePolicy.html).
Record applicable restrictions and reviewer assurance without publishing org IDs.
SSM DescribeInstanceInformation remains a post-deployment regional visibility
requirement, not a blocker for rendering a first empty-state plan.

None of these recommendations includes administrator access, `iam:*`, PassRole,
resource creation, SSM sessions, ECR publication, static keys, credential_process
activation or a new profile. Any future denied operation stops for review.

## Proposed MFA verification — not executed

1. Owner uses existing authorized IAM console access, or separately authorizes
   exact-user `ListMFADevices` through the sole existing profile. Privately compare
   the intended user; inspect every required page and its completeness flag.
   Keep device serials/ARNs, QR seeds, recovery codes and OTPs off recordings,
   transcripts, logs and shared artifacts. Publish only UTC time, registration
   count/yes-no, completeness and exact-user-match boolean. The
   [API explicitly exposes device data and pagination](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListMFADevices.html).
2. Zero devices is an unresolved gate, not permission to enroll one. Enrollment,
   resynchronization or replacement belongs to a separate owner action.
3. For the future execution window, owner establishes a fresh login for the same
   profile/principal and records an MFA challenge attestation without its values.
   Login/refresh endpoints and requests are separately approved; R3's STS-only
   tunnel is not broadened. No `mfa-login` credential export/new profile is used.
4. An existing authorized reviewer privately correlates the actual login/session
   with available sign-in and credential-origin audit evidence. ConsoleLogin's
   MFA indicator can substantiate a console authentication, but is not by itself
   proof that a later SDK token belongs to that session. Verify provenance/time
   and the documented fields for this specific credential flow. Do not assume
   CloudTrail delivery or a particular MFA field is available for every flow.
   See [console events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-aws-console-sign-in-events.html)
   and [session identity fields](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-user-identity.html).
5. Retain only `registration_verified`, `session_binding_verified`,
   `mfa_context_verified` and `context_support=verified|unknown`, reviewer and UTC
   time in an owner-controlled record. Do not publish session IDs, access-key IDs,
   principal/device identifiers or raw audit events. Missing context stays unknown.
   IAM's [MFA context-key availability](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-multifactorauthpresent)
   varies by credential flow. No guessed BoolIfExists policy is added, no fresh
   API request is made just to manufacture evidence, and no identity retry is
   implied. If correlation cannot be demonstrated, stop for owner/security review.

## Separately proposed backend and first-plan authorization

This is an operator review procedure, **not an executable authorization**.
R3's provider success is retained; core's S3 backend is a different credential
consumer. Fresh-cache support does not prove renewal or backend compatibility.

1. **Evidence/input approval:** privately approve the sole account/IAM user,
   `future-f4-preflight`, us-east-1/AZ, source revision and locks; approve all
   concrete AMI/tools/image inputs, opaque owner/name, attended UTC window,
   privacy destinations, expected inventory and numerical request/storage budget.
   No mock account, 2030 dates, fake AMI/digests or alternate credentials.
   Use direct login. Remove inherited static/default/role/web-identity/ECS/IMDS,
   proxy/endpoint/CA and Terraform logging/CLI overrides as in the accepted guard.
   No automatic refresh destination, process bridge or identity fallback.
2. **Backend prerequisite:** owner attests a dedicated, correctly owned us-east-1
   SSE-S3 bucket, versioning, public block, TLS policy and recovery identity.
   If it does not exist, STOP: state-bootstrap plan/apply and its local protected
   state need separate resource-creation/spending authorization. Init never creates
   the bucket. No backend was queried to determine existence in R4.
3. **Explicit state/lock permission:** name exact bucket and default-workspace
   key `ec2-demo/terraform.tfstate`. Propose `s3:ListBucket` on only that bucket;
   approve the minimum tested `s3:prefix` values needed for state/workspace
   discovery (review `ec2-demo/` and core's `env:/` discovery separately; do not
   guess a prefix then widen on denial). Propose Get/PutObject only on the state
   object and Get/Put/DeleteObject only on its `.tflock`. No state DeleteObject,
   ListAllMyBuckets, DynamoDB or custom KMS key. State PutObject is write authority,
   even if unused by a successful speculative plan; if owner excludes it, prove a
   narrower supported path offline before requesting execution. Current bootstrap
   policy's ListBucket scope is bucket-wide; prefix refinement is a proposed
   future reviewed change, not implemented or presumed enforced here.
4. **Bounded initialization approval:** approve at most one init in a disposable,
   private clean checkout/data directory, pinned cached plugins/readonly lock,
   non-secret reviewed backend HCL and existing profile. Proposed command shape:
   `terraform -chdir=<PRIVATE_ROOT> init -input=false -lockfile=readonly -backend-config=<PRIVATE_HCL>`.
   Use only the default workspace; no workspace creation, old local state,
   migration, force-copy or blind reconfigure. Backend credential selection and
   allowed_account_ids must be explicit. Approve potential STS/S3 metadata,
   List/Get/Put/lock requests and storage charges, even if an observed execution
   needs fewer. Abort on backend identity/config/renewal mismatch; do not retry.
5. **One infrastructure plan approval:** separately authorize
   `terraform -chdir=<PRIVATE_ROOT> plan -input=false -no-color -detailed-exitcode -lock-timeout=0s -var-file=<PRIVATE_INPUTS> -out=<PRIVATE_PLAN>`.
   Keep locking and normal refresh; no `-lock=false`, `-target`, imports, refresh-only,
   state push/rm, apply/destroy or provisioners. A clean empty-state configuration
   may need only provider startup identity reads; do not grant create/PassRole
   just to plan. An existing state requires a separately enumerated resource-read
   set before refresh, based on its actual inventory; no blanket Get*/Describe*
   proposal. Stop on an unexpected API/destination or permission denial.
6. **Network and budget review before launch:** the identity-only tunnel remains
   STS-only and must not be reused by broadening it silently. Approve the exact
   regional STS and selected bucket's S3 HTTPS host/path/method set; if existing
   objects require service reads, review those exact endpoints/actions first.
   No Sign-In refresh endpoint follows automatically. Core and provider attempt
   settings must be reviewed independently; provider max_retries=1 is not proof
   of core behavior. Enforce a bounded owner-approved command deadline/request
   allowance; no outer retry, no unbounded lock wait. If enforcement cannot be
   established offline, execution remains blocked pending a targeted correction.
7. **Private review and stop:** detailed plan exit 2 means changes proposed, 0 no
   changes, 1 error; it is not the identity collector's exit-0 contract. Protect
   plan, local backend cache and JSON on encrypted/ACL-controlled ignored storage.
   Record only sanitized inventory/actions and source/input fingerprints. Verify
   expected single t3.small/VPC/subnet/routes/SG, encrypted root/data, two ECR
   repositories, host IAM/SSM documents and backup bucket; reject unreviewed
   changes/deletions, public ingress or weakened host/provider gates. No state
   migration/write or lock release is called read-only. Normal owned-lock cleanup
   must finish; ambiguous lock ownership/release stops for owner recovery, never
   force-unlock. Retain evidence; approve neither apply nor teardown automatically.

HashiCorp documents [S3 state/lock permissions](https://developer.hashicorp.com/terraform/language/backend/s3),
[initialization/migration](https://developer.hashicorp.com/terraform/cli/commands/init)
and [plan refresh, saved artifacts and exit codes](https://developer.hashicorp.com/terraform/cli/commands/plan).
Reviewed 2026-10-25. Provider resource reads do not modify managed infrastructure;
backend init/local metadata, state/lock I/O and storage charges are separate
effects. No future command or permission here has been executed or activated.

## Offline coordinator correction and evidence

The old ignored R3 executor is historical and was **not rerun or rewritten**.
Its peer-close handler is retained unchanged. A small no-launch/no-network helper,
`infra/aws/fixtures/identity_coordinator.py`, now collects an already-owned process:

- Native exit, completed-before-stop, fixed output marker, coordinator status and
  stop-requested are independent fields. `private_postconditions_passed` retains
  native exit-0 evidence under the unchanged identity_contract.py. The extra
  `private_identity_verified` corroboration also requires exactly one true output
  marker; marker alone cannot override a nonzero exit. An output-drain timeout
  retains native postcondition evidence while reporting missing output and
  incomplete cleanup. This does not reinterpret R3, whose output was not retained.
- A guard/deadline concurrent with completion cannot erase native evidence or
  label completed work as killed. Guard/deadline remains a separate non-success
  outcome; identity evidence is not permission to continue cloud operations.
- Pending processes are stopped only by the caller-supplied owned-tree callback
  and awaited. Stopped/unknown/unawaitable outcomes cannot become identity
  successes, even if intervention produces exit 0. Duplicate/missing markers fail
  corroboration. A stop-callback exception is awaited and propagated, not hidden
  by a return from cleanup.
- No Terraform/AWS invocation, sender, credential read, output logger or retry
  exists in the helper. Raw private output is discarded in memory. A future
  separately authorized coordinator must adopt it; no clean real wrapper rerun
  or full-plan launcher is claimed. The identity helper is not a plan-exit parser.

Tests cover completion/guard races in both collection positions, peer-close and
other transport cases through the existing tunnel tests, nonzero private-check
failure, missing/duplicate output, deadlines, owned stop/await, incomplete cleanup,
poll timeouts without retries and an actual harmless local Python child.
Private canaries never reach returned evidence/stdout/logs. These are offline
coordinator/contract tests, not new authenticated account evidence.

## Commands, results and changed files

Windows local environment: Python **3.14.9**, Node **24.22.1**, npm **11.19.1**,
Ruff **0.17.2**; pinned cached Terraform **1.17.0** / AWS provider **6.70.0**.
No dependency installation or credential-bearing command was needed.

From repository root:

```powershell
.venv/Scripts/python.exe .cache/f4-03b-r4/run_checks.py
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe > .cache/f4-03b-r4/terraform-offline.json
.venv/Scripts/python.exe -m pytest tests/test_identity_coordinator.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_terraform_authentication.py tests/test_infrastructure.py tests/test_host_preflight.py tests/test_release.py -q --basetemp=.cache/pytest-r4-verified
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws --no-cache
git diff --check
git diff --quiet -- src scripts contracts data migrations web infra/aws/deployment infra/aws/state-bootstrap infra/aws/host infra/aws/modules infra/aws/fixtures/identity_contract.py infra/aws/fixtures/sts_tunnel.py
git check-ignore AGENTS.md
```

The ignored local check wrapper invokes exactly
`.venv/Scripts/python.exe scripts/check.py`, removing inherited AWS/TF/proxy
environment overrides and redirecting local output to `.cache/f4-03b-r4/checks.log`.
It cannot launch an AWS probe; the unchanged shared script enumerates all checks.
The Terraform checker uses only existing cached roots, fmt/validate and explicit
mock-provider plan-only tests; it does not initialize a backend or install plugins.

| Final check | Observed result |
| --- | --- |
| Shared offline sequence | **20/20 commands exit 0**; **1,126 routine Python tests passed**, 38.48s; zero failures/errors/skips/warnings in the final run |
| Focused auth/coordinator/security/storage/release tests | **146 passed**, 8.38s; overlap routine total, including **16 new coordinator cases** |
| Terraform | Format pass; three roots validate; **8/8 native mock plans** pass (deployment 5, bootstrap 1, protected bucket 2); zero failures/errors/skips |
| Frontend/contracts/build | **85/85 frontend tests**; TypeScript, formatting, generated OpenAPI/TypeScript contracts and build pass |
| Frozen offline evaluations | **24/24 development + 16/16 held-out** baseline; all 50-case × 3 template/fake/replay handling dispositions unchanged, including deliberate hard failures. No real-model quality evidence |
| Lint/format | Pass; **150 files** already formatted |
| Source/integrity | Protected implementation unchanged; diff check pass; AGENTS.md ignored |

The first sandboxed targeted attempt hit WinError 5 accessing its own pytest
temporary directory. The same offline checks ran successfully with local cache
access outside that sandbox; no ACL change, live credential access or AWS operation
was used to bypass the failure. An intermediate passing sequence exposed Python's
return-in-finally warning in the new fixture; corrected with an explicit regression
that stop-callback failures remain visible. Final results supersede those attempts.

No PostgreSQL/browser/Linux-container or hosted Actions rerun was needed for the
isolated fixture/documentation changes; **257 integration tests are deselected**,
not counted as passes. Prior hosted/runtime evidence is unchanged, not newly
verified. No native real Terraform process or AWS authentication rerun was hidden
in routine tests; the only new native child prints a synthetic Python marker.

Changed files: this handoff, checklist 23, infrastructure README, the new fixture
collector and its tests. No Terraform/provider/app source, historical R3 evidence,
locks, IAM policy, migrations, data, evaluation artifacts or financial authority
changed. AGENTS.md stays local/ignored. No AWS calls, backend access, credential
exports, IAM/account changes, provisioning, spending, live model/telemetry,
commit/push or F4-03C work.

**GO:** owner review of offline artifacts and provision of missing private evidence.
**NO-GO:** real backend/plan until the specified evidence, scoped authority and
operational controls are approved. Deployment remains a further approval gate.
