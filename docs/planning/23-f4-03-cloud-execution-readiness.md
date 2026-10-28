# F4-03C cloud-execution readiness — separate authorization required

Date: 2026-10-25 (America/Los_Angeles). F4-01/F4-02 are owner-accepted for their
authorized scopes; F4-03A and its CI correction have recorded evidence.
F4-03B was accepted for **read-only account preflight only**, using
`future-f4-preflight` in us-east-1. F4-03B-R1 through R3 are owner-accepted.
R3 completed with native Terraform exit 0 and mandatory private account/ARN/user-ID
postconditions satisfied; the coordinator separately reported a transport/shutdown
error. R4 is accepted. **F4-03B-R5A permits offline bootstrap/plan preparation and
narrowly scoped read-only verification only.** R5A used owner-supplied findings
and made no additional AWS calls. No identity retry, actual backend initialization
or real infrastructure plan ran in R4/R5A. No credentials were exported. Accepted provider identity evidence
is retained without repeating the probe for a cleaner coordinator outcome.
The older use of F4-03B for prospective
deployment does not expand that scope. Pending cloud-execution decisions are
now listed under F4-03C, which requires separate authorization.
**Cloud execution NO-GO: $0 cloud spend authorized.** This checklist grants no
backend initialization, remote state/lock write, account-connected infrastructure plan,
apply/destroy, image publication, provider request, telemetry or external-user access.

The source implementation is [infra/aws](../portfolio-readiness.md) (curated release-readiness substitute; original infrastructure reference omitted). It targets
the single-host option in [proposal 22](22-f4-deployment-and-cost-plan.md), not ECS.
The [F4-02 handoff](../implementation/f4-02-handoff.md) separates offline evidence
from untested cloud behavior. The limited account inventory below is read-only;
it is not a complete billing inventory or deployed-application evidence.

## R5A owner evidence and next execution gates

[R5A handoff](../implementation/f4-03b-r5a-handoff.md) and
[R5B proposal 25](25-f4-03b-r5b-state-bootstrap-and-plan-proposal.md).
New owner findings supersede matching historical gaps below; they are not new
agent API measurements. No actual account identifiers are published.

| Finding | Current assessment / remaining action |
| --- | --- |
| us-east-1; EC2 standard quota 5 vCPUs | Applied quota accepted from owner. Current all-project usage/pending headroom not supplied; t3.small needs two spare vCPUs |
| VPC quota 5, one existing | Four slots at observation; enough for one new VPC. Recheck count/CIDR at launch |
| Registered MFA passkey for preflight user | Registration gate met. Actual future operator/session MFA context still needs evidence |
| No IAM boundary | Own-user boundary gap resolved. Future separate operator effective policies/trust still need review |
| Appears standalone | Provisional owner assessment; obtain final attestation. Joining Organizations can trigger a paid-plan upgrade |
| No S3 buckets | No backend exists; explicit protected-bucket creation is needed before actual backend init |
| Free plan and $100 credits | Accepted owner finding, not spending permission. Confirm expiry/applicability and monitor gross credit use |
| Backend mechanism | Pinned core consumes a fresh synthetic login cache against local S3/STS. Actual S3 authentication/authorization/TLS/renewal unverified; R3 real provider identity remains accepted |

- [x] Accept owner-provided quota values, VPC count, passkey registration and no
  preflight boundary; no automatic extra read grant.
- [x] Accept R4's offline coordinator improvement. No clean real rerun claimed.
- [ ] Name a separate bootstrap/state operator and source/authentication route,
  effective permissions, execution-session MFA and <=2h UTC grant window. Keep
  preflight read-only; no new profile/trust/role/export follows automatically.
  R3 does not establish a different operator's identity.
- [ ] Approve exact private state bucket and six-resource bootstrap plan,
  protected local state/copy, seven distinct bucket-setup writes, owner-only
  grant attachment/removal if needed, and post-create verification.
- [ ] Approve one exact saved bootstrap apply separately; no deployment-root apply.
  Partial/ambiguous outcomes retain state and require reconciliation/new plan.
- [ ] Approve exact lock-key PUT/GET/DELETE and state GET for one clean backend
  init/first plan using plan_operator_policy. Full later state PutObject is not
  granted automatically. Native fake clean init/empty plan made no state writes;
  any unexpected real need for them stops for review. No migration/unlock bypass.
- [ ] Approve private lock metadata (operator user/host/path/time/ID) in S3 and
  retained versions; local state/plan/cache ACLs/encryption; retention review at
  30 days/before account expiry; recovery and final all-version cleanup.
- [ ] Review Free-plan eligibility/expiry and proposal 25's **$0.05 gross credit-use
  ceiling / $0.02 operational stop threshold**, neither active nor an enforceable
  AWS billing cap. No upgrade, extra credits or deployment spending follows.
- [ ] If also requesting an infrastructure plan, approve concrete AMI/tools,
  AZ/images/window, input/source/lock binding, endpoints/read set and bounded
  capture/cleanup. Missing inputs stop after backend verification; no fixtures,
  provisioning or ECR publication are substituted.

**GO:** offline review. **NO-GO:** real grant, bootstrap/lock/state write, init,
infrastructure plan, upgrade or cloud execution until separate R5B authorization
names those effects and owner decisions.

### Supplemental R5A browser-CI evidence

Owner-reported hosted run #24 failed waiting for Chrome's DevToolsActivePort,
before page navigation. The original browser stderr was discarded; its launch
cause is unconfirmed and the original source passed a local Linux reproduction.
The separately scoped correction observes Chrome readiness/exit events, preserves
the startup timeout/full workflow/sandbox, and adds bounded metadata-only failure
diagnostics. See the [handoff](../implementation/f4-03b-r5a-handoff.md) and
[sanitized evidence](../implementation/evidence/f4-03b-r5a-ci-verification.json).

- [x] Local corrected workflow: 11/11 focused Linux runs plus complete 257/257
  integration suites on both Windows and Linux; final 1,155 routine Python/96
  frontend tests, 14 Terraform mock plans, contracts/build/frozen baseline pass.
- [ ] Owner reviews source and later obtains a successful hosted run on the
  actual Actions image. Local Ubuntu WSL/Chrome evidence is not hosted verification;
  no commit, push or hosted job was performed. Earlier hosted release evidence
  below remains historical for its recorded revision, not proof of this correction.

## F4-03B historical account preflight

[Handoff and exact scope](../implementation/f4-03b-handoff.md).

| Check | Observed result | Remaining gate |
| --- | --- | --- |
| Sole named profile | AWS CLI 2.38.5; caller IAM-user ARN exactly matches the profile's `login_session`; us-east-1; no fallback | Actual account/user IDs remain in ignored private evidence; deployment binding still needs approval |
| IAM attachments | One `FutureReadOnly` group, precisely `ViewOnlyAccess` and `SignInLocalDevelopmentAccess`; no direct or inline policies | GetUser denied; boundary/effective permissions and organization/SCP context not verified |
| MFA | ListMFADevices returned zero registered devices for the caller | Owner must address the MFA gate separately; no current-session MFA claim |
| EC2 target | t3.small, 2 vCPU/2 GiB, x86_64/Nitro/EBS; offered in us-east-1a/b/c/d/f | Do not select us-east-1e from this result; quota, capacity and final AZ still unapproved |
| Networking | One default VPC; no associated IPv4 CIDR overlaps 10.77.0.0/24 | This is not proof of subnet/VPC quota, actual routing or host isolation |
| Scoped inventory | Zero Project=fata-* instances/volumes, zero self-owned available x86_64 AMIs, zero ECR repositories and self-owned SSM documents | Reviewed AMI/tools/digests/documents/state destinations still absent/unapproved; SSM managed-node read denied |
| Encryption | Account EBS encryption-by-default is false; not changed | Existing Terraform explicitly encrypts root/data; actual created-volume encryption remains future evidence |
| Quotas | GetServiceQuota denied for EC2 standard-vCPU and VPC quotas | Owner-supplied evidence or separately approved targeted read permission; no increase requested |
| Terraform authentication | R3 native plan exit0 satisfies exact private account/ARN/user-ID postconditions using the fresh existing profile | Provider identity verified; coordinator transport warning is separate. Renewal, MFA and Terraform-core backend authentication remain unverified |
| Hosted CI | Run 40251401740 at af70cf8 passed full offline/browser, scoped DB cleanup and the actual release/restore step | Hosted evidence now covers the earlier correction for that revision; not AWS runtime evidence |

23 explicit AWS metadata command invocations: 18 succeeded, 5 denied. No remote
Terraform backend was touched and no real account-connected plan was attempted.
Counts describe CLI commands, not authentication/HTTP handshakes. Missing read
actions and their purposes are detailed in the handoff. No IAM change, alternative
identity, resource creation, credential export, billing API or paid data-plane read.

## F4-03B-R1 offline resolution / remaining NO-GO

[Proposal24](24-f4-authentication-and-account-evidence-proposal.md) and the
[R1 handoff](../implementation/f4-03b-r1-handoff.md) distinguish the synthetic
provider experiment from unverified live authentication. The native experiment
uses the pinned Terraform/provider, mock process and loopback STS in network-none;
the actual source login/cache, IAM grants and Terraform S3 backend are untouched.
Pinned SDK source contradicts the generic documentation's unsupported label;
do not turn a missing synthetic cache into proof of missing SDK support. Prefer
verifying the existing source profile before adding a consumer selector.
Eight native cases passed: process selection through explicit/configured profile
and sanitized environment, direct fresh synthetic login cache, and five failure
dispositions with no default fallback. Source/build metadata also shows login
resolution in core's embedded SDK; actual S3-backend integration/refresh was not
executed. No live profile change is justified solely by the old support matrix.
The proposed consumer selector references the existing source and must retain
the same approved IAM identity. It is not a new role or permission grant.

Evidence may be supplied by an already authorized owner instead of widening
the read-only user's rights. The optional placeholder draft grants only exact
own-user GetUser and the two regional GetServiceQuota reads. SSM node inspection
is needed after a host exists, not to render an empty-state plan; organization
membership alone cannot establish effective SCPs. Neither optional broad-resource
read is silently bundled into the base draft. No policy has been attached.

**GO:** review the offline artifacts and gather owner-provided evidence.
**NO-GO:** real callback/export, new live consumer config/profile, additional
authentication probe, backend initialization/locking, infrastructure plan or provisioning
until separately authorized and the unresolved gates below are satisfied.

## F4-03B-R2 restricted real-authentication attempt

[R2 handoff](../implementation/f4-03b-r2-handoff.md).
Local provider-only initialization and validation passed with zero outbound
connections. One identity-only plan was attempted with the existing sole profile,
pinned versions, no resources/remote backend, and private account/ARN/user-ID
postconditions. Its TLS guard rejected one non-allowlisted destination and admitted
**zero outbound tunnels**. The attempt stopped; no retry or process-profile fallback.

**At the end of R2, authenticated AWS identity was unverified by Terraform.** Exact source
login-session metadata matched the previously approved principal, but that is not
an account response. A subsequent read-only local expiration check confirmed the
cached access token was expired. Refresh is a plausible explanation for the
blocked route; the rejected hostname was not retained, so its exact service is
not proven. It must not be described as an AWS authentication/IAM rejection.

R2 did not authorize non-STS requests or automatic token renewal. Smallest next
step: an owner-refreshed session on the same approved source identity, then a
separately authorized one-shot identity retry with improved bounded route
classification. Alternatively, explicitly scope and approve sign-in renewal
before any agent-performed refresh. No bridge, key or IAM change is justified by
this result. S3 backend authentication/locking, MFA and full-plan readiness remain
unverified. R2 performed no new IAM/MFA/quota/organization reads: prior evidence
remains historical, not refreshed by this attempted identity check.

## F4-03B-R3 restricted retry — provider verified, coordinator warning

[R3 handoff](../implementation/f4-03b-r3-handoff.md).
The owner separately refreshed the same source session and authorized one retry.
The precheck confirmed freshness; only `future-f4-preflight`/us-east-1 was selected.
Local init/validation had zero outbound connections. The sole identity-only plan
returned **native exit0**, which satisfies its unchanged hard postconditions for
the exact privately approved account, IAM-user ARN and user ID. The output boolean
was not retained because the coordinator entered its transport-abort path; this
identity conclusion uses the native exit code and hard postconditions, not an
invented raw response. An offline wrong-principal control returns exit1.

One regional STS TLS tunnel was admitted. There were **zero rejected destinations**,
no Sign-In connection and no real replay. Raw coordinator evidence still says
failed_closed: it prioritized a generic transport-error event over collecting
the completed native result. The original socket error subtype was not retained;
normal peer-close handling is a demonstrated defect in that guard, not proof of
the exact observed subtype. Offline tests now distinguish peer closure from
timeouts/byte limits and record bounded transport classes. This correction was
not revalidated by another real request. Future coordinators must preserve
provider/postcondition results separately from transport/cleanup outcome.

Diagnostics retain at most16 finite-category events and fixed public endpoint
names; arbitrary hostnames, ports, URLs, bodies, credentials and identities are
not logged. The exact STS-only authority and one-attempt limit are unchanged.
Provider identity is verified for this run; backend/state/lock access, actual
renewal, MFA/effective permissions/quota evidence and deployment remain NO-GO
pending separate authorization and review of remaining gates.

## F4-03B-R4 account evidence and first-plan approval boundary

This accepted R4 snapshot predates the owner findings and implemented R5A policy
refinements at the top of this checklist; use that newer section for current gates.

[R4 handoff](../implementation/f4-03b-r4-handoff.md) contains the precise proposed
action/resource scopes, safe MFA procedure and separately proposed backend/plan
commands. It grants no live execution or IAM changes. Public source review is not
fresh account inspection; denied/zero-device findings above remain historical.

| Before the first real infrastructure plan | Owner evidence/action still required |
| --- | --- |
| Identity/coordinator | Accept R3 identity (done); review the new offline-only result collector. Native exit/private checks remain separate from guard/deadline/cleanup warnings; no clean real rerun claimed |
| Effective access | Exact-user boundary/absence and applicable policy versions/session/resource restrictions; optional exact-user GetUser and two quota reads only if owner cannot supply evidence |
| MFA | Fresh own-user registration completeness plus actual-session authentication/provenance evidence. No tokens/device identifiers/raw audit artifacts. Registration/STS/session ARN alone do not prove MFA |
| Organization | Owner/org reviewer establishes standalone/management/member and relevant inherited SCP/RCP controls; membership read alone is insufficient |
| Capacity | Applied EC2 L-1216C47A/VPC L-F678F1CE values and all-project us-east-1 headroom, timestamped; at least two spare standard vCPUs and one VPC |
| Images/inputs | Concrete approved AZ, patched masked/tool-attested AMI, both mirror digests/provenance, account/name/owner and attended UTC window; no fixture substitutions |
| State | Existing dedicated bucket and protection/recovery evidence, or separate bootstrap provisioning authorization. Exact default-workspace state key, lock key, scoped List/Get/Put/Delete-lock and numerical request/storage allowance |
| Backend/plan execution | Separate explicit approvals for one bounded init and one locked plan, protected artifacts, precise endpoints/read actions/core and provider retries, owned lock cleanup and stop conditions. No migration, apply or deploy authority follows |

- [ ] Owner supplies the evidence above privately, or separately approves exact
  missing read actions. R4 added no permissions and made no further AWS calls.
- [ ] Owner approves the exact backend bucket/key and whether any state-object
  write is allowed. Lock Get/Put/Delete is write authority. Bucket creation is a
  separate decision; an init permission never authorizes bootstrap apply.
- [x] R5A implements the measured `env:/` discovery-prefix restriction in the
  proposed state/plan policies. Native loopback evidence supports it; effective
  AWS IAM is untested. Never widen automatically after a denial.
- [ ] Review a future bounded backend/plan launcher independently of the STS-only
  identity fixture. Its exact S3/service endpoints, credential-consumer behavior,
  deadlines, request counts/retries and lock cleanup are not established by R3.
  Do not run a real plan until these controls and account inputs are approved.
- [ ] Explicit owner authorization names the source/locks, sole profile/account,
  operations/commands, region, UTC window, endpoints, budget and private evidence
  retention. Detailed plan exit 2 means proposed changes, not identity failure;
  review the resulting plan before any separately authorized apply.

The new `identity_coordinator.py` fixture has no launcher or network sender. Tests
retain a finished native result even if a guard fires concurrently; stops and
incomplete cleanup cannot create identity successes. The old ignored R3 executor
is historical, not silently made into a new active launcher. Its source/result and
the exact identity-contract HCL are unchanged. This remains offline evidence only.

## What is implemented offline

| Boundary | Implemented preparation | Still needs AWS/operator evidence |
| --- | --- | --- |
| Network | us-east-1 VPC/subnet/IGW, one t3.small, no inbound SG rules, outbound TCP443, loopback app/PG, no SSH key/NAT/ALB | Effective account networking, DNS, SSM connectivity, no public reachability |
| Credentials | Exact instance role, SSM minimum actions, two ECR pull scopes, backup-prefix access; no app credential mounts/env | Effective IAM/SCP/boundary review; actual app-UID firewall/IMDS denial |
| Host | IMDSv2, hop one, disabled IPv6 metadata, UID10001/999 egress fences; app/PG non-root/capability-free | Reviewed AMI/kernel/tools, effective UIDs/no remap, firewall persistence/reboot |
| State | Separate bootstrap root; versioned encrypted TLS-only public-blocked bucket; exact state and lock key, delete only lock | Private state/identity creation, lock contention/recovery, effective bucket permissions |
| Persistence | Encrypted8GB root/protected32GB data, exact device/UUID/source checks, atomic bundle/config, Docker masking, restartable preparation and daemon pre-start checks | Actual Nitro/cloud-init/systemd timing, damaged-volume recovery, root-size compatibility |
| Release | Digest-only ECR app/PG mirrors; bounded compressed bootstrap; explicit Start after publication; existing migration/readiness ordering | Publish/verify images, host bootstrap, real HTTP/browser journey through SSM |
| Operations | Fixed prepare/start/stop/verify/backup document; bounded same-source recovery, no arbitrary shell | SSM schema acceptance, exact caller tags, emergency recovery identity/local tunnel listener |
| Recovery | Quiesced full binary dump, checksum/private receipt, S3 prefix, bounded size, 7-day current +7-day noncurrent expiration | Actual S3 upload/download, explicit recovery role/target, cloud restore and deletion checks |
| Expiration | <=24h UTC window; reject early/late start, OS poweroff timer/EC2 Stop, standard CPU credits | Clock/timer behavior, attended emergency stop and billed resource inventory |

The same-host database remains synthetic trust authentication with the existing
development role. No medical/real-user or production security claim. Host root
and SSM operator are trusted administrators. The firewall and IMDS metadata settings
are defenses for app/PG UIDs, not proof against host compromise.

## F4-03A findings and evidence boundary

1. **SSM exact ownership retained after review.** AWS documents the tag format
   `role-id:caller-specified-role-name` but illustrates StringLike with a trailing
   wildcard. That broader pattern also accepts prefix-colliding callers. Fourteen
   structural cases cover exact assumed-role/IAM-user tags, other roles/sessions,
   collisions, missing tags, wrong target/region/account/action. They are **not AWS
   IAM evaluation**. Only the documented exact tag shape is supported offline;
   a real transformed/suffixed tag must trigger source review, not broadening.
2. **PG metadata gap corrected.** The app-only fence did not restrict UID999.
   Both UIDs now have IPv4 loopback-only/IPv6-deny rules. Cloud PG is forced to999
   with no capabilities/no-new-privileges, including initialization. Actual isolated
   Linux tests reproduce prior PG metadata reachability and corrected denial while
   preserving SQL. They contact synthetic metadata endpoints, never EC2 IMDS.
3. **Preparation/restart gap corrected.** Docker/socket are masked before bootstrap
   writes. Atomic files and a final bundle manifest reject partial cloud-init.
   A boot-enabled240-second oneshot waits180 seconds for the exact disk, serializes
   preparation and records format intent; recognized ext4 is never reformatted.
   Repeated preparation reuses mounts. Docker pre-start and every launch/backup/
   verify recheck the actual mount. `nofail` permits host recovery but cannot allow
   Docker root-disk fallback. A still-blank interrupted format requires inspection.

Commands/denominators: [F4-03A handoff](../implementation/f4-03a-handoff.md).
No Terraform resource, price, storage allocation or networking service was added.
F4-02's estimated **$1.55866** under stated assumptions remains; it is not a cap.
Expiry/failed preparation require attended stopping. No actual cloud billing,
boot or restore evidence exists.

## Required owner decisions before F4-03C / any write-capable cloud operation

- [x] Explicitly authorize F4-03B read-only preflight with the sole named profile;
  completed within that narrower scope. This grants no write-capable operation.
- [x] Accept F4-03B-R1; authorize the narrow R2 identity-only attempt. It failed
  closed before reaching AWS and does not establish authenticated identity.
- [x] Owner-refreshed source session and separately authorized R3 identity retry;
  native exit0 verifies the intended principal under private postconditions.
  No fallback, refresh endpoint or second R3 request was enabled.
- [x] Review R3's coordinator transport/cleanup limitation independently of its
  successful provider identity result. Preserve both outcomes for future probes;
  owner accepted the distinction. Offline close-handler/collector improvements
  do not count as a clean real rerun; the new R4 collector still requires review.
- [ ] Explicitly authorize **F4-03C** with its exact
  scope. Name any permitted plan/backend/state/lock operations and costs separately
  from infrastructure creation. No apply permission follows from plan approval.
- [ ] Approve the exact AWS account privately, us-east-1/AZ, opaque owner tag,
  attended UTC start/end (<=24h), operator and emergency contact/stop responsibility.
- [ ] Review the complete source diff and pinned Terraform1.17.0/AWS6.70.0 locks;
  inspect the future real plan and expected inventory. Do not reuse fake fixture
  account/digests/2030 window or infer permission from a config flag.
- [x] Hosted offline Actions run of the implementation revision, including the
  corrected integration-database/release handoff: [40251401740](https://github.com/ThePhysic/future-adaptive-training-agent/actions/runs/40251401740)
  at `af70cf867bd30efc1a9b5f7470be9bdc0d53cfb3`, actual cleanup and release/restore
  steps succeeded. No run was triggered by F4-03B. Recheck if implementation changes.
- [x] Owner resolves preflight passkey registration, own-user boundary absence,
  EC2/VPC quota values and VPC count in R5A. Historical read denials grant no IAM changes.
- [ ] Complete final standalone/effective-policy and execution-session MFA
  evidence, and current EC2 usage/headroom before launch.
- [x] Owner confirms preflight passkey registration in R5A, superseding the old
  F4-03B zero-device finding; the agent performed no enrollment/read.
- [ ] Establish fresh execution-session MFA evidence. R1 made no fresh account read.
  R2 also made no IAM read and returned no authenticated identity result; R3
  verified provider identity but made no MFA read. R4 makes no account call.
  Then establish a fresh source login authenticated with MFA and review evidence
  linking that session to the intended principal. Device registration, STS identity
  and a sign-in-session ARN alone do not prove MFA. Verify flow-specific policy
  context before any MFA condition; do not attach an untested BoolIfExists rule.
- [ ] Recheck current regional headroom from owner evidence at launch: at least
  two spare standard vCPUs and one VPC. Quotas 5/5, one VPC and no preflight boundary
  are owner-established; a two-quota/GetUser grant is no longer required just to
  recover those values. Obtain final standalone/organization assurance as applicable.
- [x] Accept R3 provider authentication and exact private identity postconditions
  for its fresh session. No repeat solely to remove the coordinator warning.
- [ ] Establish **backend** compatibility with this profile's login credentials
  under separate init/state/lock authorization before account-connected planning.
  Future credential freshness/renewal is not proven by R3. Do not silently switch to
  another profile, static credentials, instance metadata, root or administrator
  identity. Proposal24's separate consumer selector preserves the source identity
  but still needs explicit config/profile/export authorization. No live bridge or
  export was implemented. Review CLI/config ACLs, finite expiration, parent-env
  sanitization and error suppression; validate both provider and backend clients.
  R5A proves the core mechanism offline with a fabricated cache. Actual S3 and
  any separately selected writer identity remain unverified; preflight stays read-only.
- [ ] Approve a concrete AMI ID, publisher/source/architecture/root size, OS patch
  evidence, host tool versions and `/etc/fata-host-tools.json` SHA-256. Preparation
  does not install tools or build an AMI. Require a currently patched SSM Agent,
  **at least 3.3.4851.0**, and current security review. The host helper enforces
  that floor in addition to exact version attestation.
  Verify Docker service/socket are masked in the AMI before cloud-init, no
  rootless/user-namespace remap, and expected app10001/PG999 kernel UIDs. The
  helper also rejects remapping or an unexpected daemon data-root at launch.
- [ ] Approve both linux/amd64 app and PostgreSQL18.6 mirror digests and provenance,
  image publisher role/window and ECR artifact retention. Verify registry digests
  after publication, not just local image IDs. No credentials baked into images.
- [ ] Approve private deployment identity, narrowly scoped EC2/VPC/EBS/ECR/S3/SSM
  and named IAM lifecycle actions, exact-role PassRole-to-EC2, state permissions,
  MFA/federated session duration, SCPs and permission boundaries. No administrator
  shortcut. Review the generated fixed-document operator policy separately;
  it is not attached to a role by this module. Its regional OpenDataChannel grant
  uses the message gateway's required wildcard resource; termination instead uses
  exact AWS system caller/target tags. Verify denied wrong-owner sessions/documents.
  Verify the actual federated tag shape privately. Approve an emergency recovery
  identity able to terminate the exact captured session ARN if routine termination
  fails. An unexpected tag format requires source review; no suffix/prefix
  widening is approved here.
- [ ] Approve state bootstrap identity, dedicated bucket/key, local encrypted
  bootstrap state/recovery copies, default-workspace restriction and lock recovery.
  A short-lived state writer cannot delete state; a separately reviewed recovery
  identity is needed for version restoration/final deletion.
- [ ] Approve all cloud processors/destinations: EC2/EBS and ECR in us-east-1, the
  dedicated S3 backup/state buckets, AWS SSM control/session traffic, and ordinary
  AWS control-plane records. No app prompt/plan/log exporter to CloudWatch or
  Langfuse is configured. Cloud backups contain synthetic business records;
  retention and all-version deletion need explicit approval.
- [ ] Accept loopback HTTP inside an encrypted SSM tunnel and synthetic-only
  selector semantics; verify local port binds only 127.0.0.1. This is **not** public
  TLS or real-user authentication. If literal browser HTTPS/public ingress is
  required, stop for a separately reviewed design; do not relax app guards.
- [ ] Approve the revised numerical run/retention budget, spending monitoring,
  manual stop threshold and residual-resource allowance. No number in this document
  is an active grant or enforceable billing cap.
- [ ] Approve recovery-point targets (manual quiesced daily/before-release backup,
  RPO<=24h/RTO<=1h targets), exact restore verification and a separately reviewed
  recovery SSM role/document or attended administrative procedure. The routine
  operator policy intentionally cannot run arbitrary restore shell commands.
- [ ] Approve teardown timing, explicit deletion inventory, temporary guard changes
  and retention of data volume/images/backups/state/AMI snapshots. Do not bypass
  protection using force deletion, global cleanup or state removal.
- [ ] Give explicit execution approval for the reviewed plan/window. This is
  separate from accepting Terraform files or authorizing offline validation.

SSM security sources reviewed 2026-10-25:
[minimal instance role](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html),
[session schemas](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-schema.html),
[IMDS owner firewall guidance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-metadata-limiting-access.html).
Also verify [federated caller/target session tags](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-examples.html)
and [message-gateway resource limits](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ssmmessages.html).
AWS's [SSM bulletin 2026-107](https://aws.amazon.com/security/security-bulletins/2026-107-aws/)
sets the cited fix floor for remote-host forwarding credential exposure. This
configuration grants no remote-host forwarding, but still requires the fix.

## Revised cost inventory, not spending authorization

The actual design introduces **no** extra hosted service: no NAT, ALB, RDS,
CloudWatch exporter/alarm, secret, custom KMS key or scheduled snapshot resource.
It does add a second ECR repository/mirror and separates retained data from root.
Reuses dated us-east-1 official assumptions from document22, checked again against
[EBS](https://aws.amazon.com/ebs/pricing/), [ECR](https://aws.amazon.com/ecr/pricing/),
[S3](https://aws.amazon.com/s3/pricing/) and [public IPv4](https://aws.amazon.com/vpc/pricing/)
on 2026-10-25. F4-03B's separate account metadata reads above do not verify billing;
no paid billing API was invoked and no spending authority was added.

Same proposed 24h/1,000-request/100-fake-generation/2GB-egress workload:

| Item | Gross USD allowance |
| --- | ---: |
| t3.small24h | 0.49920 |
| 8GB root24h +32GB data retained7d | 0.61019 |
| One public IPv4 for24h | 0.12000 |
| Two GB total ECR artifacts for7d | 0.04603 |
| One GB backup up to14d lifecycle window | 0.01059 |
| Reviewed AMI8GB snapshot7d allowance (not a TF resource) | 0.09205 |
| State/request allowance | 0.00060 |
| Two GB internet DTO, no free credit | 0.18000 |
| **Total proposal** | **1.55866** |

[Machine-readable arithmetic](../implementation/evidence/f4-02-costs.json).
F4-01's $1.11930 proposal assumed all40GB active only24h, one GB ECR,7d backup,
10GB EBS snapshot allowance plus proposed logs/secret/alarms. Here the retained
32GB disk materially increases storage time, mirror doubles the ECR allowance,
version cleanup lengthens potential backup retention, and unimplemented hosted
logs/secrets/alarms/scheduled snapshot are removed. The AMI allowance makes its
prerequisite cost explicit. Existing AMI artifacts might have no incremental cost;
building a new AMI or publishing more image versions needs a separate cost quote.

No-request730h baseline: about **$22.65702 running**, or **$3.18302 after instance
termination with32GB disk and stated ECR/S3/AMI artifacts retained**. Stopping
without terminating retains the additional8GB root (**+$0.64/month**). State can
remain indefinitely; backup deletion is asynchronous, ECR/data do not auto-expire.
Taxes/FX/support, new AMI build time, additional copies, requests and traffic can
increase cost. A prospective $5 ceiling needs renewed owner approval and a manual
stop threshold; AWS alarms/timers do not create a hard billing limit.

## Future execution evidence and stop conditions

Record plan inventory/digest, actual source/lock/AMI/image versions, approved window
and identity evidence privately. Verify host/bootstrap readiness, exact listeners,
IAM denial cases (including wrong document/resource and app UID→IMDS), no public
ingress, no container credentials and no exported app data. Run the existing full
regressions and real synthetic browser/API journey through the approved tunnel.
Measure actual host resources/latency separately from the F4-01 laptop fake run.

Take a quiesced S3 backup; restore only into a fresh approved target, verify exact
immutable snapshots, original key retries, ownership, all nine migration checksums
and completion/audit counts. Record actual RPO/RTO and failure/recovery outcomes.
No live monetary record may be discarded or held liability released as a shortcut.

Stop immediately for unreviewed IAM/AMI/image/endpoint changes, failed firewall or
mount verification, public bind/tunnel, expired window, data leak, migration drift,
unexpected spend, unknown inventory or failed recovery. Stop app and instance
without deleting the recovery source; owner reviews the next action. No automatic
generation replay or broad cloud retry/recovery worker.

After an explicitly approved teardown, enumerate lingering volumes, addresses,
AMI snapshots, ECR layers, backup/state versions and account costs; record zero
unapproved resources and precise retention/expiry for approved leftovers. Only
then close the cloud exercise. Offline Terraform tests cannot satisfy these gates.

Live OpenAI/counting/monetary provider authority, hosted Langfuse, participant
access and later work units remain separate **NO-GO** decisions regardless of
any future AWS approval. F4-03B completion grants none of them.
