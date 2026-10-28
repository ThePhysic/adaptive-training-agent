# F4-03B — Read-only AWS account preflight and Terraform plan readiness

2026-10-25 (America/Los_Angeles). **Read-only preflight complete with gaps;
account-connected Terraform planning and deployment remain NO-GO.**

Only `future-f4-preflight`, region `us-east-1`, was used for AWS inspection.
Starting HEAD: `af70cf867bd30efc1a9b5f7470be9bdc0d53cfb3`.
No IAM/account/resource changes, remote state/lock operations, real Terraform
plan, apply/destroy, image publication, credential export, live model/counting
requests, telemetry export, spending authority, commit or push. No F4-03C work.

The latest user instruction narrows F4-03B to read-only inspection. Older
documents' prospective use of that label for deployment grants no additional
authority. Pending execution decisions are now in the
[F4-03C checklist](../planning/23-f4-03-cloud-execution-readiness.md).

## Account evidence

**23 explicit metadata command invocations:18 succeeded,5 AccessDenied.**
These are CLI-command counts, not authentication/HTTP handshake counts. Native
AWS responses are kept only in ignored `.cache/f4-03b/private/`; credentials were
never printed or exported. Shared [evidence](evidence/f4-03b-read-only-preflight.json)
contains redacted commands, numerical findings and classifications, not account
IDs, caller ARNs/user IDs, device serials, resource IDs or raw errors.

| Inspection | Observed result | Interpretation |
| --- | --- | --- |
| Profile/STS | AWS CLI2.38.5; profile contains region and `login_session`; returned IAM-user ARN exactly matches that session identity | Named-profile identity verified privately; not deployment approval |
| IAM group/policies | Exactly one group, `FutureReadOnly`; precisely `ViewOnlyAccess` and `SignInLocalDevelopmentAccess`; no group inline, direct-user or user-inline policies; no truncated results | Confirms the supplied setup; not a complete effective-permissions evaluation |
| MFA | Zero registered caller MFA devices, nontruncated | Current-session MFA not established; owner must address the future MFA gate separately |
| Zones/type | Six available AZs; t3.small offered in1a/1b/1c/1d/1f, not returned for1e;2vCPU,2048MiB, x86_64/Nitro/EBS | Final AZ unapproved; offerings do not prove spare launch capacity or quota headroom |
| VPC | One default VPC; associated IPv4 CIDRs do not overlap proposed10.77.0.0/24 | No networking change; VPC quota and actual proposed subnet/routing remain unverified |
| Scoped EC2/EBS | Zero instances/volumes with `Project=fata-*` | Not an account-wide or global inventory; untagged/other-project resources were not audited |
| AMI/ECR/SSM documents | Zero self-owned available x86_64 images, zero ECR repositories, zero self-owned SSM documents in this region | No reviewed custom host image, published artifact digests or deployed custom documents established |
| EBS default | Account encryption-by-default is false | Not changed. Existing Terraform explicitly encrypts both volumes; actual resources must later be verified |
| Quotas/SSM/organization | Reads denied as listed below | Capacity, managed-node visibility, organization membership and effective SCPs remain unknown |

AWS describes [ViewOnlyAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/ViewOnlyAccess.html)
as resource/basic-metadata viewing; its current public default is v46. The
attached [SignInLocalDevelopmentAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html)
supports sign-in authorization/token exchange, not infrastructure deployment;
public default v3. Sources reviewed2026-10-25. Attached names were confirmed by
account API; managed-policy bodies/versions were reviewed publicly, not retrieved
with IAM GetPolicyVersion. Effective boundaries/SCPs were not inferred from names.

## Missing permissions — no changes made

| Observed denied action | Purpose / minimum scope to review with owner |
| --- | --- |
| `iam:GetUser` | Inspect only the current user's permissions-boundary metadata; STS identity itself already verified |
| `ssm:DescribeInstanceInformation` | Regional managed-node status/agent/platform inventory; needed for later host/SSM verification |
| `servicequotas:GetServiceQuota` (two requests) | EC2 standard On-Demand vCPU quota `L-1216C47A` and VPC quota `L-F678F1CE`, in us-east-1; current usage/headroom also needs evidence |
| `organizations:DescribeOrganization` | Determine organization membership before owner review of SCP applicability; this action alone cannot inspect inherited SCPs |

Five failed calls correspond to four distinct actions. No retry with another
profile/identity and no IAM changes were attempted. The owner can provide the
missing evidence privately or separately approve narrowly scoped read access;
this report does not request an automatic policy attachment. Complete policy-body
review may additionally need `iam:GetPolicy`/`iam:GetPolicyVersion`, and inherited
SCP review needs appropriate Organizations evidence. Those extra reads were
**not attempted** and are not additional observed denials. Do not substitute
AdministratorAccess or broaden this read-only identity for deployment.

## Terraform readiness and explicit stop boundary

**No account-connected Terraform command was run.** The real target still lacks
owner-approved AMI/tool attestation, ECR digests, exact AZ, deployment name/owner,
UTC window, backend bucket/state binding, scoped operational identities, recovery
decisions and numerical spending/retention limits. Example fake values were not
replaced or treated as approvals. No state bucket was created or queried.

There is also a documented authentication compatibility concern. This profile
uses AWS CLI console-login credentials, not static credentials. AWS's
[login-provider support matrix](https://docs.aws.amazon.com/sdkref/latest/guide/feature-login-credentials.html)
currently lists Go SDK v2 support as **No**; the locked provider's
[v6.70.0 source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.70.0/go.mod)
uses Go v2/config1.33.9. **Inference:** successful CLI STS does not establish that
the provider or S3 backend can consume the same profile. Actual Terraform
authentication was not attempted, so this is a readiness blocker, not an observed
Configure failure. Verify both credential consumers before a real plan.

AWS documents a process-credential workaround in its
[CLI login guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).
Its additional-profile example is not authorized by this task. No profile was
edited/created, cache credentials inspected, export-credentials invoked, bridge
implemented or credential values passed to Terraform. Any future solution must
be separately reviewed, bind to the approved identity and fail closed rather
than falling back to environment/default/instance/root/admin credentials.

Before running any operation that can initialize/migrate a remote backend,
write state, acquire/release a remote lock, alter resources or create charges,
**stop for separate owner authorization naming the exact operation and scope**.
[HashiCorp's S3 backend requirements](https://developer.hashicorp.com/terraform/language/backend/s3#permissions-required)
include ListBucket and Get/PutObject for state, and Get/Put/DeleteObject on the
specific `.tflock` when locking is used. No state-object DeleteObject is needed.
Those writes and potentially billable storage requests are outside this grant.
Do not remove locking or use another backend as an unreviewed workaround.
Plan approval would still not authorize apply, state bootstrap or teardown.

## Exact execution and checks

The installed executable was outside the current process PATH; it was invoked
directly at `%USERPROFILE%/AppData/Local/Programs/Amazon/AWSCLIV2/aws.exe`, without
changing PATH or installing anything. Every AWS command used this common prefix:

```text
aws.exe --profile future-f4-preflight --region us-east-1 --output json --no-cli-pager --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15 <service> <operation> <arguments>
```

All23 operation/argument lists and exit codes are in the evidence JSON; only
`--user-name` values are redacted. Calls were sequential and bounded. The ignored
operator scripts stripped inherited `AWS_*` settings and proxy variables, then
set the sole profile/region explicitly, `AWS_EC2_METADATA_DISABLED=true`,
`AWS_MAX_ATTEMPTS=1`, `AWS_RETRY_MODE=standard`, `AWS_PAGER=''`,
`AWS_CLI_AUTO_PROMPT=off`, `AWS_IGNORE_CONFIGURED_ENDPOINT_URLS=true`.
Profile chaining, credential_process, role, endpoint and CA overrides were absent
and rejected by the local guard. Normal TLS verification remained enabled.
The CLI may maintain its existing login cache; no login/logout/config command or
credential-value export was performed. No S3 data-plane, paid billing/Cost Explorer,
image pull, instance launch (including dry-run) or session-start operation occurred.

| Executed local check | Result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_infrastructure.py tests/test_host_preflight.py tests/test_release.py -q --basetemp=.cache/pytest-f403b-preflight` | **71 passed**,5.91s; command/filesystem simulations and strict port checks, no AWS |
| `.tools/terraform/terraform.exe fmt -check -recursive infra/aws` | Exit0 |
| Existing `infra/aws/offline_container.py`, using README's cached Linux CLI/provider mirror invocation; container name `fata-f403b-offline` | **Three roots valid,8/8 mock-only plans passed**; Docker network-none, read-only source, no credentials mounted, backend=false local initialization in disposable tmpfs only |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 +16/16**, zero failed cases |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit0, no contract drift |
| `git diff --quiet` on application/infra/scripts/tests/contracts/data/migrations/web/locks; `git diff --check` | Protected implementation unchanged; documentation-only diff |

Terraform1.17.0/AWS6.70.0 locks unchanged. These native mock plans are not real AWS
plans and cannot establish effective IAM, state permissions or provisioning success.
Full Python/frontend/PostgreSQL/browser suites were not rerun for documentation
changes; their latest hosted evidence below is distinct from local checks.

## Hosted evidence, costs and handoff

Read-only `gh run list`/`gh run view --json conclusion,headSha,jobs,url` verified
[run40251401740](https://github.com/ThePhysic/future-adaptive-training-agent/actions/runs/40251401740)
at the starting implementation revision. It **succeeded**, including the actual
offline/browser, scoped PostgreSQL cleanup and local container release/restore
steps. The earlier port correction is therefore now **hosted-verified for that
revision**. No run was triggered here. This does not demonstrate AWS operation.

Changed files: this handoff, `docs/planning/23-f4-03-cloud-execution-readiness.md`
and `docs/implementation/evidence/f4-03b-read-only-preflight.json`. Runtime,
Terraform/IAM, dependencies, historical reports and frozen artifacts are untouched.
No new service, storage allocation or infrastructure design change. Existing
**$1.55866** proposal remains a dated estimate; **$0 new cloud spend authorized**.
No paid billing queries or actual account-bill verification, cost cap or global
resource-inventory claim. Existing account charges, if any, were not assessed.

F4-03C needs owner review of the denied reads, MFA, Terraform login compatibility,
quota/headroom, masked/patched AMI, image provenance, state/lock/write authority,
exact run/window/budget, SSM ownership/recovery, processor/retention consent and
teardown inventory. None is silently approved. **Stop after F4-03B for review.**
