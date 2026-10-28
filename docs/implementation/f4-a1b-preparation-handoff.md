# F4-A1a closure and F4-A1b preparation handoff

2026-10-26. **Offline review only; no AWS operation performed or authorized here.**

## Outcome and next milestone

Recorded [A1a completion](f4-a1a-completion.md) exactly as owner-attested evidence.
Do not rerun the human-administrator identity probe to obtain independent/cleaner
evidence. [Runbook 26](../planning/26-f4-aws-validation-and-deployment-runbook.md)
places **A1b, state-operator identity verification**, next; it is not a bootstrap,
permission-grant, backend or provider-provisioning unit.

The smallest useful next milestone is **F4-A1b — State-Operator Identity
Verification**. Next Codex work should finalize the offline operator procedure
before separately approved execution. Bind only existing `future-f4-state-operator` to its
privately established Account/Arn/UserId. Prepare a narrow operator procedure,
private comparisons, sanitized result and explicit authorization request; execute
nothing. Do not generalize human_sts.py to accept arbitrary profiles or enable an
automated runner. No new identity or IAM setup is needed for preparation.

The owner must confirm that the existing CLI profile alias and authoritative
state-user identity expectations are available privately. This task did not open
any real profile, expected-identity file or authentication cache. Earlier owner
reports of state-user creation/login are retained, but availability/provenance of
its exact expected UserId is not independently established here.

## Exact next proposed AWS operation — conditional, not authorized

The runbook's A1b target is **one operator-started STS GetCallerIdentity invocation**,
with native credential/source and transport assumptions approved separately:

```powershell
# REVIEW VECTOR ONLY: not a complete executable procedure or current authorization.
# ReviewedCli and PrivateError are private operator bindings, not supplied here.
$A1bRaw = & $ReviewedCli sts get-caller-identity --profile future-f4-state-operator --region us-east-1 --endpoint-url https://sts.us-east-1.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15 2> $PrivateError
```

Required approval: exact existing state profile, private expected Account/Arn/UserId,
reviewed source/binary, regional HTTPS endpoint, attended UTC window, private capture/
comparison/retention, retry/interruption rules, and an explicit decision about native
refresh/no-containment/manual limitations for **A1b**. A1a's exception is not inherited.
No new IAM grant is proposed merely to perform the identity check. Permission to
execute remains required regardless of an API's service-permission behavior.

Success must privately match the exact IAM user `future-f4-state-operator` in the
already approved account, rejecting root/role/federation/other account/user/UserId.
Do not disclose identifiers or infer MFA, HTTP count, S3 permission or policy
correctness. No automatic retry, fallback identity, login or follow-up AWS command.

### If the expected UserId is unavailable

Stop A1b execution preparation short of an executable live procedure. Do not use
the same unverified STS response as both expectation and evidence. First propose a
**separate A1b-reference authorization**, only if needed:

```powershell
# Separate future reference-read review vector; never automatic before/after STS.
$A1bReferenceRaw = & $ReviewedCli iam get-user --user-name future-f4-state-operator --profile future-f4-human-admin --region us-east-1 --endpoint-url https://iam.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15 2> $PrivateError
```

Caller: human administrator; target: only the exact state-user ARN, including its
privately approved path. Required service permission: `iam:GetUser` scoped to that
user. This is an IAM-global endpoint with us-east-1 signing/configuration context,
not an invented regional IAM destination. It changes no IAM resource, but exposes
private user/possible-boundary metadata and is still a signed account operation.

Owner must separately authorize that single read, caller, target, authentication
assumptions, window and private handling. Check returned UserName/Arn/UserId against
known account/path/user metadata; Account comes from the approved private account
and returned ARN, not an invented GetUser Account field. Keep raw output private.
AccessDenied, missing user or mismatch means stop without permission expansion.
The earlier GetUser approval for the **human** user does not cover this target.
The state user is not asked to perform IAM reads that its proposed boundary denies.

If the owner already has adequate authoritative expectations, omit that read. The
next proposed live operation is then STS; otherwise the separately approved
reference read would precede it. Neither branch is authorized now, and approval
of the reference read would not approve the later STS invocation.

## Remaining gates for safe progression

A1b's immediate gates are private identity provenance, profile binding and its
own authorization/risk decision. Later bootstrap/deployment gaps below are not
reasons to bundle resource changes or broad IAM reads into this identity checkpoint.

These are existing decisions/gaps confirmed against current repository source,
not new AWS measurements or authority to implement corrections:

| Area | Current evidence / remaining prerequisite | Scope consequence |
| --- | --- | --- |
| Human identity | A1a owner-attested match resolves that checkpoint only; no independent MFA/session or policy audit | No repeat probe; later mutation units still require reviewed authentication/effective permissions and explicit authorization |
| State identity | Exact private source binding/profile and independently established expectations pending confirmation | Prepare A1b only; do not copy private files into public artifacts or silently select default/human credentials |
| Policy inventory | Runbook A2/A3/A4 remain separate; current groups, inline/managed policies, boundary and session context have not been freshly audited here | Exact named reads, pagination/privacy and optional MFA evidence need approval; no account-wide enumeration or IAM modifications |
| State boundary | Last accepted evidence is a local generated proposal, not creation/attachment; no new installation evidence supplied | Real-document validation B, customer-managed policy creation C and user-boundary attachment D are independent approvals. Never install it as an inline policy or activate the old policy-administrator delegation |
| Boundary semantics | Ceiling is not a grant. Existing explicit denies, principal/account/region/TLS and env:/ restriction remain. Direct-user resource grants inside the ceiling can bypass missing/expired identity grants | Keep trusted resource-policy administration; validate real documents/interactions before installation. Do not broaden permissions to get a plan working |
| Human bootstrap tooling | Terraform supports distinct bootstrap/state principals; legacy operator_spec, policy/plan validator and private-runner plan preparation still assume the state user for both | Secure human bootstrap needs a separately approved offline correction/test unit preserving independent principal bindings, source checks and six-resource guard. Do not spoof equal principals or bypass the guard with raw Terraform |
| Bucket/bootstrap | Six protected S3 resources; local bootstrap state, force_destroy=false/prevent_destroy, ownership, public block, versioning, SSE-S3 and TLS deny. No new actual bucket/protection evidence | Local recovery/state custody, reviewed inputs, account/region, exact read/write inventory and saved-plan review remain prerequisites. Plan/apply/verification each need approval; bootstrap state must not migrate into its own bucket |
| Backend vs provider | State user remains exact state/lock access only. Separate nonadmin deployment identity remains a proposal; human admin is one-time bootstrap authority, not routine deployment credentials | Preserve backend/provider separation and preflight read-only status. Review two-profile precedence/poisoned-default isolation before a provider plan; never broaden the state ceiling |
| Provider escalation | Deployment root manages host role/profile/inline policy; exact-role PutRolePolicy plus PassRole/RunInstances can still escalate | Before provisioning grants, review a protected host-role ceiling or separately administered IAM bootstrap. State-user boundary is not a substitute for host-role controls. No new deployer/grant created here |
| Financial/operations | Current credits/expiry/resource usage not inspected. $0.05 gross/$0.02 stop remain proposals, not active permits or enforceable caps | Separate cost/retention/teardown and operation-specific approvals before resources or data-plane work. No account upgrade or spending follows A1a/A1b |
| Automation | execute_live() and execute_account() still unconditionally deny. Owned capture/attempt fence unchanged; no enforced Windows egress demonstrated | Manual identity evidence does not activate an executor or establish a general safe cloud runner |

## S3 compatibility remains a later gate

Preserve `s3:prefix=["env:/"]`, `ec2-demo/terraform.tfstate` and its `.tflock` key.
Accepted native Terraform fake-S3 evidence is not real S3 authorization evidence.
An absent state object's HEAD may produce 403 rather than 404 depending on permissions;
never interpret 403 as absence or silently widen prefixes/explicit denies.

After a separately approved protected-bucket bootstrap, exact owner/region/protection
reads and authorized human/state-user HEAD/workspace comparisons can establish real
behavior. Native remote init and lock PUT/GET/DELETE are distinct approval units;
a Terraform plan with backend locking is not wholly read-only. If an initial state
write is required, stop: a conditional human seed is a separate mutation proposal,
not automatic permission to expand state access. Preserve versions/lineage and
uncertain locks; no automatic force-unlock/delete/rollback.

A1b needs no S3 permission, bucket, Terraform operation or resource provisioning.
These later gates therefore do not justify bundling them with identity verification.

## Validation and file handoff

This task added:

1. `docs/implementation/f4-a1a-completion.md`: sanitized owner-attestation record.
2. This handoff: A1b scope, conditional reference read, remaining gates/next task.
3. A dated current-status note in runbook 26; original proposal text remains intact.

Offline Windows Python 3.14.9, existing Terraform 1.17.0/AWS 6.70.0; no installation:

| Command / check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py -q --basetemp=.cache/f4-a1a-closure/pytest --tb=short` | **112 passed in 3.18s**; synthetic policy/identity and loopback-only tunnel fixtures, no credentials/account calls |
| `.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe` | fmt passes; three roots validate; **21 mock-plan cases passed** (5 deployment/14 bootstrap/2 module), no backend init/account plan |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, original 24 development/16 held-out; software regression only |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no contract drift |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **174 Python files** pass native and 3.13 grammar |

Targeted pytest used normal local process access for existing private-ACL fixtures;
no safeguards or ACLs were relaxed. These are fresh **offline** checks, not live
IAM evaluation, native AWS compatibility, S3 testing or independently reproduced A1a.
No PostgreSQL/frontend/browser/full routine rerun: no application/runtime change.
Historical baseline/evidence records remain unchanged.

Final checks: all **20 PowerShell blocks** in the runbook/handoff parsed with zero
errors, without execution; all eight local document links resolved; the completion
JSON exactly matched the owner's sanitized result. Static AST review confirmed both
live executor bodies still unconditionally raise. `git diff --check` passed.
Raw-byte preservation/source-manifest evidence is under ignored
`.cache/f4-a1a-closure/`. No real identity/config/cache material was accessed.
The starting public-source inventory contained 462 files: 461 remain byte-identical;
only the runbook status note changed, and its original body remains byte-identical.
The two new documentation files are the only additions. Existing worktree changes
were preserved; this task changed no executable source, policy or baseline artifact.

## Proposed next Codex task — not authorized by this handoff

> Prepare F4-A1b offline only: a single-purpose supervised state-operator identity
> procedure using the existing future-f4-state-operator profile. Confirm privately
> through owner attestation whether authoritative Account/Arn/UserId expectations
> already exist; do not read/copy private identity files. If unavailable, prepare
> only the separate exact-human-GetUser reference-read request first. Request an
> explicit A1b decision on authentication refresh/manual containment limitations;
> do not inherit A1a's exception. Preserve all code, boundaries, fences and disabled
> executors. Review syntax/synthetic comparisons and stop before any AWS invocation.

**GO for independent review/offline preparation only.** No current permission to
perform A1b, a reference read or any later AWS operation has been granted. Do not
begin bootstrap, IAM changes, real backend/provider plans or deployment.
