# F4-03B-R1 — Authentication and account-evidence proposal

2026-10-25 (America/Los_Angeles). **Offline proposal; not an active profile,
policy, credential exporter or cloud-execution permission. F4-03C remains NO-GO.**
F4-03B read-only evidence is accepted; R1 makes no new account requests.

## Authentication proposal

Official sources reviewed on the date above:
[AWS login provider support](https://docs.aws.amazon.com/sdkref/latest/guide/feature-login-credentials.html),
[process provider contract](https://docs.aws.amazon.com/sdkref/latest/guide/feature-process-credentials.html),
[CLI login bridge](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html),
[export-credentials](https://docs.aws.amazon.com/cli/latest/reference/configure/export-credentials.html),
[locked provider dependencies](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.70.0/go.mod).
AWS's generic matrix lists login-session support as absent and process support
as present for Go SDK v2. **R1 corrects the inference drawn from that matrix:**
the pinned config1.33.9 source has an explicit
[LoginSession credential-resolution branch](https://raw.githubusercontent.com/aws/aws-sdk-go-v2/config/v1.33.9/config/resolve_credentials.go),
and credentials1.20.9 includes a
[login provider](https://raw.githubusercontent.com/aws/aws-sdk-go-v2/credentials/v1.20.9/credentials/logincreds/provider.go)
and [cache format](https://raw.githubusercontent.com/aws/aws-sdk-go-v2/credentials/v1.20.9/credentials/logincreds/token.go).
Do not describe all Go v2/provider login authentication as unsupported. Missing
cache and unsupported capability are different findings. A CLI STS result alone
still proves neither actual provider nor Terraform-core S3-backend authentication.
Offline build-info inspection found core1.17.0 embeds config1.32.12/credentials1.19.12,
while provider6.70.0 embeds config1.33.9/credentials1.20.9. The core's pinned
[config1.32.12 resolver also has LoginSession and process branches](https://raw.githubusercontent.com/aws/aws-sdk-go-v2/config/v1.32.12/config/resolve_credentials.go).
This is source/build-metadata evidence, not a backend-init test. No backend was
initialized to turn that inference into an unapproved account operation.

The smallest prospective path is first to verify direct use of the existing
source profile in **both** actual consumers, including refresh, under separate
authorization. Native fresh-cache support does not establish every consumer or
refresh operation. If a bridge is needed, prefer AWS's documented mechanism to a
new exporter service or long-lived keys. Retain `future-f4-preflight` unchanged
as the source of its existing short-lived IAM-user session. A future, explicitly
approved **consumer selector** would refer to that source; this does not assume
a role, create a user or add IAM permissions. Its example below is documentation
only; R1 creates no live selector/profile or real credential output:

```ini
[profile future-f4-terraform-proposed]
region = us-east-1
credential_process = "C:/OWNER-APPROVED-ABSOLUTE-PATH/aws.exe" configure export-credentials --profile future-f4-preflight --format process
```

The executable path is a placeholder, not PATH lookup. Do not put this callback
inside its own source profile: that can recurse. Do not switch to a differently
privileged identity. Additional-selector approval is required even though the IAM
identity stays the same. No long-lived key, env-format export, redirection, shell
evaluation, transcript, credential file or app-container credential delivery.

Future configuration must include both the original login-session profile and
the consumer in an owner-protected reviewed config; a consumer-only AWS_CONFIG_FILE
would also hide the source from its child CLI. Preserve the intended login-cache
location for the child only; do not copy/inspect its credential values. The CLI
would pipe temporary process JSON directly into the SDK's private stdin/stdout
relationship; this real export/possible token refresh is **not authorized now**.
The process must supply Version1, access/secret/session token and expiration;
optional documented AccountId must be independently compared if present. Missing
expiration must not be accepted as a deliberate long-lived-credential workaround.

Required later launch controls, not a new live launcher in R1:

- Explicit approved consumer selection for **both** provider and backend; pin the
  sole source identity/account and check it privately before planning. Keep
  provider/backend `allowed_account_ids` and us-east-1. Consumer name alone is not
  identity proof, and a process bridge adds no deployment permissions.
- Remove inherited static/session credentials, default-profile, web-identity/role,
  ECS/IMDS, endpoint/proxy/CA and Terraform CLI/log overrides. Use pinned reviewed
  config paths, an empty shared-credentials file and disabled IMDS. Reject role,
  source_profile, SSO, arbitrary process and endpoint substitutions. No default
  profile recovery after missing/failed process. Guard config and executable ACLs.
- Allow only expected process schema, finite lifetime and the approved source;
  bound runtime/output, cancel and await owned children, classify errors without
  raw stderr. Expiration/refresh failure stops the operation; never reuse expired
  values, retry with another identity or print SDK/provider debug traces.
- `credential_process` follows other providers in some chains: sanitizing the
  parent is necessary, not a guarantee supplied by the mere presence of the INI
  setting. The test-only environment helper is not a production launcher.
- Real Windows command quoting and actual CLI process JSON remain to be verified
  under separately authorized local credential use. No shell env export is needed.

The contained native experiment uses only a synthetic process, poisoned synthetic
default credentials, fixed consumer, pinned provider, loopback STS and network-none.
Its precise outcomes/limitations are in the R1 handoff. S3 backend authentication,
real identity, MFA and AWS credential refresh remain separately unverified.

## Evidence first; optional read grants second

No denied action is inherently required just to render an offline/mock Terraform
plan. What is required before AWS execution is **credible evidence**, which an
already authorized owner can supply without expanding this user's rights.

| Previously denied action | When needed | Least-privilege route |
| --- | --- | --- |
| `iam:GetUser` | Own-user boundary metadata before accepting effective access | Owner supplies timestamped exact-user result showing boundary ARN or explicit absence; alternatively exact-user-only read |
| `servicequotas:GetServiceQuota` | Applied regional EC2/VPC quota evidence before creating resources; useful before accepting a real plan | Owner provides the two applied values and current usage/headroom, or grant only two quota ARNs; no list-all or quota-increase authority |
| `organizations:DescribeOrganization` | Organization membership context if owner evidence is unavailable | Prefer existing account/org administrator's evidence; a standalone/management/member finding determines further SCP work; action alone never proves effective SCPs |
| `ssm:DescribeInstanceInformation` | After deployment for target registration, ping and agent-version verification | Not a prerequisite for a first empty-state plan. Prefer owner output filtered to the exact future instance, or later regional read-only grant |

The [two-action draft](proposals/f4-03b-r1-read-permissions.json) is deliberately
non-activating: placeholders, no attachment, no broad ReadOnlyAccess upgrade.
Its two statements are independent options, not a requirement to grant both.
Owner must substitute the exact account and user path, verify their authority,
review effective denies and approve attachment/expiry separately. Structural
checks cannot replace AWS policy evaluation.

Resource-scope references:
[IAM](https://docs.aws.amazon.com/service-authorization/latest/reference/list_iam.html),
[Service Quotas](https://docs.aws.amazon.com/service-authorization/latest/reference/list_service-quotas.html),
[SSM](https://docs.aws.amazon.com/service-authorization/latest/reference/list_ssm.html),
[Organizations](https://docs.aws.amazon.com/service-authorization/latest/reference/list_organizations.html).
GetUser is scoped to the exact user ARN; GetServiceQuota to exactly
`ec2/L-1216C47A` and `vpc/L-F678F1CE` in us-east-1. No `*` resource in that draft.
If later needed, SSM DescribeInstanceInformation has no resource-level ARN scope:
one-action `Resource:"*"` plus RequestedRegion=us-east-1 is the honest limit;
instance-ID filtering reduces returned data but is not IAM authorization scoping.
DescribeOrganization similarly needs `Resource:"*"`; avoid granting organization
administration or inventing unsupported organization-resource/region conditions.
Neither optional action is in the base draft.

### Minimum evidence acceptance

- **Quotas:** actual approved account/us-east-1, applied values, observation time,
  current regional usage/headroom and operator verification. One t3.small needs
  two additional standard On-Demand vCPUs; a new VPC needs one additional VPC.
  Existing untagged resources/pending usage matter. A zero project-tag inventory,
  published default quota or offered instance type does not prove headroom. No
  quota increase requested here; if insufficient, stop for a new owner decision.
- **Boundary:** exact IAM-user ARN, observed boundary or explicit absence, and,
  if present, its effective policy/version from an existing authorized reviewer.
  A boundary is an upper limit, not an access grant. Grant GetPolicy/GetPolicyVersion
  only on a known policy ARN if owner-provided evidence is insufficient; do not
  add IAM Get* or new boundary-management privileges. Attached public policy names
  alone do not resolve explicit denies, resource policies or session restrictions.
- **Organization:** owner establishes standalone/management/member status.
  For a member account, have an existing authorized organization reviewer inspect
  root→OU→account inheritance and policy contents (ListParents,
  ListPoliciesForTarget, DescribePolicy as appropriate); include relevant RCPs.
  Do not make the learner an Organizations delegated administrator for this task.
  [DescribeEffectivePolicy does not return SCPs/RCPs](https://docs.aws.amazon.com/organizations/latest/APIReference/API_DescribeEffectivePolicy.html).
  [SCPs do not grant access and do not constrain management-account identities](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html).
- **MFA:** F4-03B's last measurement returned zero user devices; R1 does not reread
  the account. Enrollment is an IAM change requiring separate owner action.
  Then obtain fresh own-user ListMFADevices/console evidence, a fresh MFA-authenticated
  source login and owner-reviewed session/audit evidence for the intended principal.
  Device registration and STS identity alone do not prove MFA for this session.
  Verify the applicable flow's authorization context before enforcing MFA policy;
  do not attach a guessed Bool/BoolIfExists rule or count a missing key as proof.
  [AWS context-key availability](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-multifactorauthpresent)
  matters; a SignInSessionArn correlates a login but is not itself an MFA assertion.
  Existing ListMFADevices read permission needs no broader IAM grant.

## Later account-connected plan — explicit separate approval

1. Approve source/consumer identity binding and authentication-only live validation
   for provider and S3 backend, including callback export/refresh and permitted STS
   requests. Approve profile/config/launcher changes separately; no live action R1.
2. Approve concrete AMI/tool manifest, account/AZ, ECR digests, owner/name, attended
   UTC window, recovery/deletion scope, privacy destinations and numerical costs.
   Existing placeholder values must not become apparent authorization.
3. Approve state bootstrap as a separate resource-creating operation if needed.
   A normal backend init assumes the reviewed bucket exists; init is not a bucket
   provisioning mechanism. No forced state migration or cross-project workspace.
4. Approve exact S3 ListBucket prefix, GetObject state access and the actual
   lock-object Get/Put/Delete permissions. Keep `use_lockfile=true`; specify the
   real key and owner-operated lock contention/recovery. State-object writes
   needed for lifecycle/backend migration require explicit approval too. Never
   request state DeleteObject for ordinary planning or bypass a lock with -lock=false.
5. Authorize the particular plan invocation and any backend initialization, lock
   requests/storage charges, state reads/writes and saved-plan retention it can
   cause. Maintain least-privilege read access; no apply permissions are implied.
   Provider and backend are separate clients and must both reject credential fallback.
6. Review the actual plan privately against expected inventory and prior state;
   a plan can contain sensitive values and is not approval to apply. Publishing
   images, provisioning, SSM sessions, backup/restore and teardown each remain
   separately scoped owner decisions. Keep real model/telemetry gates closed.

Source: [S3 backend permissions and locking](https://developer.hashicorp.com/terraform/language/backend/s3#permissions-required).
No need to implement a new auth service, role-assumption framework or secret store.
The process bridge is a proposal; all cloud-operational gates remain in checklist23.
