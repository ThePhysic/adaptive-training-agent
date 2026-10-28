# F4-03B-R5B execution readiness — offline administrator and private runner preparation

2026-10-26. **Stop for owner/source review. No account access is authorized.**
No AWS CLI/API request, IAM/account change, real Terraform plan, S3/state/lock
operation, resource, monetary authority, spending, credential export, commit or
push occurred. Public AWS documentation was consulted without account access.
All identity, policy and process evidence below is synthetic and offline.

## Decision and remaining gates

Propose one dedicated, non-root **`future-f4-policy-administrator`** IAM user for
the trusted human who installs and removes the operator's reviewed inline grant.
This is a proposed identity, **not an existing or newly created user**. Retain
`future-f4-state-operator` and `FutureStateOperators` unchanged; preflight remains
read-only. Do not put administrative authority on either existing group/user.

A dedicated role would normally be preferable with an existing federation/trusted
human-role route. None is established here: adding a source identity, AssumeRole
permission, role trust and a different principal protocol would add scope. The
direct-login user proposal fits the accepted standalone setup without access keys.
AWS recommends federation for human access; this narrow synthetic exercise is not
a general workforce authentication design. [AWS MFA and temporary-access guidance](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_fido.html).

**`iam:PutUserPolicy` is a privilege-escalation capability.** Even on one exact
user, it can install arbitrary permissions on that user. In an account with no
restricting boundary, a malicious/mistaken administrator and operator could turn
that into broad account access. A role, MFA, two-hour expiry and our runner do not
make the policy body safe by themselves. Existing operator grants might also be
changed/deleted. The human must be trusted for this power. If the owner will not
delegate it, keep the writes with an already trusted owner-authorized non-root
administrator using separately reviewed Console operations instead.

IAM authorization here is on the user ARN, **not an inline-policy ARN**. The
published IAM keys do not provide a PolicyName/body-equality constraint for these
operations; do not invent `iam:PolicyName` or misuse `iam:PolicyARN`. Exact opaque
name, absent-before-install, body comparison and no blind overwrite are local
procedure safeguards, not AWS-enforced limits against a hostile administrator.
[PutUserPolicy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_PutUserPolicy.html),
[IAM condition keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html).

**Current GO:** review source, prepare protected local proposals, run synthetic tests.
**Current NO-GO:** account reads/writes, administrator setup, real command execution
or a Terraform plan. The supported account entrypoint always rejects execution;
there is no environment flag, credential, manifest or owner-approved boolean that
activates it. Source-reviewed activation/assembly remains a separately authorized
step. This document does not silently approve the administrator or spend proposal.

## Exact proposed administrative permissions

`infra/aws/private_command_runner.py::administrator_proposal` renders a private
identity policy with **one statement**:

| Element | Exact proposed scope |
| --- | --- |
| Actions | `iam:GetUserPolicy`, `iam:PutUserPolicy`, `iam:DeleteUserPolicy` only |
| Resource | Private exact existing operator user ARN, including its actual IAM path |
| Principal condition | `ArnEquals aws:PrincipalArn` = private exact proposed administrator user ARN |
| Account/region | `StringEquals aws:PrincipalAccount` = private approved account; `aws:RequestedRegion` = `us-east-1` |
| Transport/MFA | `Bool aws:SecureTransport=true`, `aws:MultiFactorAuthPresent=true` |
| Window | `DateGreaterThanEquals aws:CurrentTime` = approved UTC start; `DateLessThan` = approved UTC expiry; positive and <=2 hours |
| Excluded authority | No user/group/role creation, keys/password/MFA management, trust changes, AttachUserPolicy, managed-policy editing, boundary removal, group policies, S3/EC2 or wildcard-resource/action grant |

IAM uses its global HTTPS endpoint; the proposed requested-region condition does
not turn IAM into a regional service. These are conditional Allows, not a boundary
or an explicit deny of unrelated grants. Owner must review effective permissions.
The administrator's own setup and cleanup authority stays with the trusted
provisioning identity; it is not delegated to this new user.

For browser-based local login, the owner may separately approve direct assignment
of **SignInLocalDevelopmentAccess** to this proposed user, as with the operator.
Its documented v3 grants the two `signin:` OAuth actions on the managed policy's
public-client resources; it grants no S3/IAM administration. Do not call it an
exact-bucket policy or silently add it to `FutureStateOperators`.
[Managed policy](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html).

The new proposal deliberately requires MFA **present**, without IfExists. MFA
registration and STS identity are not proof of a CLI request's MFA condition.
Compatibility of this new user's `aws login` context with that IAM condition is
unverified. Missing/false context must deny IAM access; do not remove the condition,
fall back to static keys or add another session mechanism automatically.
[MFA API conditions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_configure-api-require.html).

Administrative expiry ends the Allow; it does not remove documents or revoke all
login sessions. Schedule operator-grant readback/removal **before both windows
expire**. If missed, use a separately authorized trusted cleanup identity; do not
extend either window or assume the expired administrator can still remove it.

## Owner Console setup proposal — no steps executed

Each account action below needs fresh approval; this is not a request to do it now.

1. Owner selects the trusted provisioning identity and human administrator, attests
   standalone/account identity, reviews the escalation risk and chooses direct user
   or an explicitly redesigned role. No new Organizations/Identity Center setup,
   paid-plan upgrade or AdministratorAccess assignment. If initial provisioning
   requires owner break-glass access, approve that separately; root credentials
   must never enter this runner, AWS CLI route or Terraform provider.
2. In IAM Console → Users → Create user, create only the proposed administrator,
   with console access and a separately delivered password. Do not create access
   keys, copy the operator's permissions, or add privileged groups. If self-service
   password/MFA setup needs more permissions, stop: the trusted provisioning human
   completes approved setup instead of granting broad self-management authority.
   Review the wizard's password-reset defaults: do not silently attach
   IAMUserChangePassword or leave a mandatory reset that the user cannot perform.
   Any narrowly scoped password-change allowance needs its own owner review.
3. Under the user's Security credentials → MFA → Assign MFA device, enroll a passkey
   or hardware security key with the human present. Verify an actual fresh MFA
   sign-in. Keep passwords, device names/ARNs, recovery material, QR codes, browser
   tokens and account identifiers out of repository/terminal recordings.
   [Console passkey procedure](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_fido.html).
4. After reviewing private inputs and the exact <=2h window, separately approve the
   generated three-action administrative policy on this administrator. Attach the
   local-login managed policy only if separately approved. Neither policy is a
   bootstrap S3 grant, and neither exists because it was rendered locally.
5. Under separate authentication approval, the human uses AWS CLI v2 >=2.32's
   `aws login --profile <privately-selected-admin-profile>` in us-east-1, selecting
   this exact IAM user and MFA browser session. Do not infer profile names from
   usernames, accept another active browser identity or export credentials.
   Login can refresh for up to 12 hours, longer than the permission window; the
   runner must block unapproved refresh destinations and never auto-login.
   [Official login behavior](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).
6. Owner records the expected private Account/Arn/UserId evidence, effective policies,
   MFA/session context and cleanup responsibility. Owner-authorized inspection of
   IAM/Console audit evidence is separate from runner execution; no list-all-users,
   policy enumeration or audit-service grants were added for UI convenience.
7. End-of-window cleanup separately removes the named operator grant, verifies its
   absence, then removes the administrator's temporary IAM management grant.
   Any user/login-policy deletion or session logout is another owner-approved action.

### Local private proposal preparation

Reuse Checkpoint B's Windows PowerShell 5.1 private-directory helpers, hidden input,
six-field `$SpecPath`, `$Private` and `$Label`. No real inputs were supplied here.
The disk-encryption, private terminal, no-transcription and ACL gates still apply.
Only proposed identifiers belong in the local JSON; never include credentials.

```powershell
# LOCAL ONLY, from the repository root; assumes accepted Checkpoint B variables
. ./infra/aws/private_state.ps1
$AdminIdentityPath = Join-Path $Private ($Label + '-admin-identity.json')
$AdminPolicyPath = Join-Path $Private ($Label + '-admin-proposal.json')
if ((Test-Path -LiteralPath $AdminIdentityPath) -or
    (Test-Path -LiteralPath $AdminPolicyPath)) { throw 'private_proposal_already_exists' }
$AdminIdentity = @{
  Account = Read-FataPrivateValue 'Approved private account ID'
  Arn = Read-FataPrivateValue 'Proposed exact administrator user ARN'
  UserId = Read-FataPrivateValue 'Private expected administrator UserId (after approved setup)'
}
[IO.File]::WriteAllText($AdminIdentityPath, ($AdminIdentity | ConvertTo-Json),
    (New-Object Text.UTF8Encoding($false)))
Assert-FataPrivateAccess $AdminIdentityPath
& .venv/Scripts/python.exe infra/aws/private_command_runner.py --prepare-administrator --spec $SpecPath --identity $AdminIdentityPath --output $AdminPolicyPath
if ($LASTEXITCODE -ne 0) { throw 'offline_administrator_proposal_rejected' }
Assert-FataPrivateAccess $AdminPolicyPath
```

Before user creation the owner can review the generator and permission table;
the genuine UserId will only exist after separately approved setup. A fabricated
UserId is not identity evidence. Local rendering does not check IAM existence.
The helper validates exact user/account/window, verifies private cache ownership,
creates UTF-8 with exclusive/private file creation and fsync, refuses overwrites,
and emits only a finite result plus action/user counts. No real policy body is
included in this document. Partial/failed output is retained for private review,
not automatically overwritten or attached.

## Prepared private Windows runner

Changed files in this unit:

- `infra/aws/private_command_runner.py`: offline proposal CLI, strict command/config
  preparation, memory-only process capture, finite response classifiers and local
  one-shot claims. **No active AWS launcher or remote backend executor.**
- `tests/test_private_command_runner.py`: synthetic identity/IAM, credential-source,
  source/plan, concurrency, timeout, cancellation, ownership and privacy tests.
- This handoff. Existing Checkpoint B, Terraform definitions/locks, application,
  CI/browser infrastructure, schemas, financial controls and frozen data remain intact.

The supported module command without `--prepare-administrator` exits 1 with a fixed
disabled classification. `execute_account` unconditionally rejects before looking
at credentials or spawning. `ACCOUNT_EXECUTION_ENABLED` is false and not an
activation interface. **Do not bypass this by calling generic process primitives
with real AWS commands.** There is no active monetary approval or live transport.

| Safeguard | Implemented offline behavior / future execution requirement |
| --- | --- |
| Identity | Selected-only config has exactly region + login_session, bound to private exact Account/Arn/UserId and the correct operator/admin user. Reject root, roles, preflight, default, alternate profiles and unexpected fields. STS response must match all three fields exactly; duplicate JSON keys fail |
| Sources | Reject inherited AWS_*, TF_* or proxy overrides; child inherits OS basics only. Explicit config, empty credentials file, selected login cache/home and profile/default-profile; IMDS disabled. No process/role/SSO/static-key fallback. Config snapshots omit cli_history, whose documented default is disabled; no inherited history config/file is accepted |
| Command vocabulary | AWS vectors contain only STS identity and exact-user, exact opaque `FataBootstrap-cb-<32 hex>` Get/Put/DeleteUserPolicy; only reviewed bootstrap policy filename for Put. Explicit executable, profile, us-east-1, HTTPS endpoint, no pager/debug/shell, finite CLI I/O timeout and one SDK attempt setting |
| Terraform | Preparation only: reuse verified private copy of existing bootstrap root; same operator binding, selected-only config and empty credentials; exact cached-only plugin rc, original source/input hashes, no extra override files; reject existing state and existing saved plan. Prepare only local-state plan, never deployment/apply/destroy/import/backend/lock commands |
| Output | Separate bounded in-memory stdout (1 MiB) / stderr (64 KiB). No TemporaryFile, raw CLI log, public terminal echo or exception forwarding. Private buffers excluded from repr and cleared after classification. This is best-effort buffer clearing, not a forensic memory-erasure guarantee |
| Ownership | Spawn isolated Python release wrapper, attach existing reviewed Windows kill-on-close Job Object **before releasing command arguments on stdin**; descendants inherit the job. POSIX uses a new owned process group. No arbitrary process/port killing, task accumulation or automatic retry |
| Timing | <=120s command deadline including startup/release; output drains and stdin release are separate bounded workers. Stop on cancellation, overflow, pipe failure or deadline; kill owned descendants and await parent/readers. Cleanup permits <=5s wait plus <=5s aggregate joins, so normal hard bound <=130s plus OS scheduling/termination overhead. Cleanup failure blocks further work |
| Reconciliation | Exclusive-create/fsync local attempt claim precedes any future launch. Claim survives process restart, failure or ambiguous result and is never auto-removed/reused. Any uncertain IAM write requires approved readback; exit 0 still requires readback. AccessDenied is not NoSuchEntity; wrong-body readback is a conflict |

`prepare_bootstrap_plan` returns **private in-memory** argv/environment only. It does
not attest an executable's authenticity, validate a real cache or run a provider.
Its prepared cache must be an explicitly approved protected `.cache/` directory;
no existing real login cache was read/copied. Using it later requires separately
approved direct login into that selected directory (no credential export), or a
source-reviewed metadata-only ACL procedure for an already existing external cache.
Do not silently copy credentials or relax the helper's cache boundary.

Before a real provider launch, mandatory private STS checks must verify the operator
using the **same frozen config/cache/environment context**; config and source must
be rechecked after waiting and before send. Terraform's existing account allowlist
does not itself prove the user ARN. The offline tests establish source selection,
not actual authentication of this new IAM user or resistance to a hostile local
administrator modifying its cache/client. No AWS credential material was inspected.

Remaining live binding work is explicitly gated: review executable/version/source
attestation, a per-stage approval bound to identity, private policy/source/input
fingerprints and expiry, persist one-shot claims before launch, validate private
identity proofs/readback prerequisites, and bind a separately approved owned egress
guard. Existing identity-only R3 coordinator/tunnel is **not** a generic plan/IAM
launcher: it permits only one STS tunnel. Do not broaden it or reuse its accepted
identity evidence as authorization for this new administrator/operator. The generic
capture function has no network enforcement by itself. There is no account-capable
CLI in this milestone, so these pending live bindings cannot be bypassed by flags.

Future network review must allow only the operation's necessary regional STS or
global IAM HTTPS destination; bootstrap plan may require its exact bucket's regional
S3 endpoint only under an additional read/apply authorization. Retain TLS hostname/
certificate verification, no custom endpoints/CA/proxy inheritance, no automatic
Sign-In refresh, no outer replay and approved call/byte/deadline bounds. AWS SDK or
provider higher-level retries/polls still require review; `AWS_MAX_ATTEMPTS=1` is
not a proof of one HTTP request for an entire provider operation.

Local claims are an interruption/replay fence, **not AWS IAM idempotency, exactly-once
execution, a power-loss durable ledger or a spending permit**. A failed fsync/cleanup
means stop and preserve evidence; no write replay based on process/socket failure.
Readback matches exact UserName, PolicyName and decoded PolicyDocument. Binary plan
exit 2 means only “review needed”; the existing six-resource guard/source review
must still pass. Never log raw stderr to diagnose a failed private command.
[CLI history and data protection](https://docs.aws.amazon.com/cli/latest/userguide/data-protection.html).

## Staged authorization matrix

Every row is a separate owner decision; **none is authorized by this milestone**.

| Stage | Explicit approval and private evidence | Stop / next boundary |
| --- | --- | --- |
| Administrative setup | Trusted provisioning identity, human/new user, MFA method, local-login route, exact three-action grant/window and escalation risk | No CLI root, broad group policy, access keys or unreviewed boundary changes |
| First AWS reads | One private regional STS identity request for selected new administrator; later separately approve operator identity and exact-name GetUserPolicy | Exact private identity match; no refresh/alternate endpoint; STS does not prove MFA |
| IAM condition/absence read | Exact-user GetUserPolicy by administrator within the MFA/time grant, fresh operator/admin identity and privately attested session | Require genuine NoSuchEntity for fresh name, or exact matching reviewed body for reconciliation; denial/unknown context stops |
| Temporary attachment | Exact administrator/target, fresh opaque name, exact existing bootstrap_operator_policy body/fingerprint, bucket/window, one write claim and readback permission | Put is add-or-replace: no blind retry, overwrite, group change, broader plan/state writer or automatic cleanup |
| Real bootstrap plan | Frozen operator context, pinned binaries/source, empty local state, explicit endpoints, bounded runner/egress review, proposed costs approved, one saved plan path | Expected exactly six protected S3 create-only resources; review guard, private binary hash and independent review; no apply |
| Saved-plan apply | Separate exact reviewed binary, creator identity/window, six resources, recovery/retention and gross budget | Not implemented in this runner; ambiguous apply retains local state and requires approved reconciliation |
| Protection verification | Exact bucket owner/region, public blocks, versioning, ownership, AES256 and TLS-only policy; encrypted recovery copy | No backend initialization, state write or lock authority implied |
| Revocation | Exact administrator, target/name/body, timely removal and readback; trusted cleanup route if expiry missed | Remove only reviewed grant; separately remove temporary admin grant/logout; never erase unrelated policy or recovery evidence |
| Later backend/lock | Separate plan_operator_policy approval, protected bucket, exact state/lock keys and operation/network/cost authorization | No broader state-writer activation, remote-state writes or deployment approval |

The first safe **future** account-connected operation is one bounded
`sts:GetCallerIdentity` via the exact selected administrator profile and
`https://sts.us-east-1.amazonaws.com`, privately compared to all expected identity
fields. It requires completed owner setup, reviewed live binding/egress and fresh
read authorization first. No need to repeat accepted preflight R3 evidence. Do not
take the next IAM read/write merely because the identity check succeeds.

Retain Checkpoint B/proposal 25's **$0.05 gross maximum proposal** and **$0.02
operational stop threshold**. Neither is active authorization or an enforceable
AWS cap. Credits/Free plan do not authorize spending/upgrading. No new resource or
cost-bearing service is proposed here. Stop at forecast/observed operational
threshold, unexpected request/service, permission/Free-plan denial, expired window,
privacy breach, unverified identity/MFA, source mismatch, ambiguous result or
incomplete cleanup. Do not wait for delayed billing to stop. Keep private artifacts
encrypted/ignored and retain the original manual recovery/30-day-or-earlier review.

## Offline verification and limitations

Validation used Windows PowerShell 5.1, Windows Python 3.14.9 and the existing Linux
test image (Python 3.14.9). No dependencies were added, real login profiles/caches
read, or AWS CLI process executed. Linux runs use `--network none`, read-only
repository source and disposable `.cache` tmpfs; no host credentials are mounted.
Private-path positive/negative Windows DACL checks from Checkpoint B remain intact.

| Check | Observed result |
| --- | --- |
| Shared offline check sequence | **20/20 commands exit 0**; **1,281 routine Python tests passed**, 52.76s; zero failures/errors/skips, 257 integration deselected |
| Focused Windows preparation/identity regressions | **159/159 passed**, 8.33s; subset of routine tests, not an additional denominator |
| Focused network-disabled Linux regressions | **159/159 passed**, 5.55s; same subset on Python 3.14.9, including positive and negative POSIX file-access cases |
| Final pipe-cleanup follow-up | All **79/79 new runner tests passed** on Windows (6.07s) and network-disabled Linux (3.36s); Ruff check/format also pass; no source change after these focused checks |
| Terraform | Cached Terraform **1.17.0**, AWS provider **6.70.0**; fmt/static checks and all three roots validate; **15/15 mock cases** (deployment 5, bootstrap 8, bucket module 2) |
| Frontend/contracts | **131/131 frontend tests**; TypeScript, formatting, generated contracts and build pass through the shared sequence |
| Frozen evidence | Baseline **24/24 development + 16/16 held-out**; all 150 offline template/fake/replay dispositions reproduce. Software/fake/replay evidence only |
| Private/process security | Windows native Job Object and ACL tests pass; Linux owned-group cleanup passes. Early exit, ownership failure, cancellation, controlled deadline, stdout/stderr floods, unrelated sibling survival and private canaries verified |
| Operator instructions | Both PowerShell blocks parse with the native parser; neither was executed |

Commands actually executed from the repository root:

```text
.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_identity_contract.py tests/test_identity_coordinator.py -q --basetemp=.cache/pytest-readiness-windows-completion
.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py -q --basetemp=.cache/pytest-readiness-pipes-final
.venv/Scripts/python.exe .cache/r5b-checkpoint-b/run_checks.py
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/ruff.exe check infra/aws tests/test_private_command_runner.py --no-cache
.venv/Scripts/ruff.exe format --check infra/aws tests/test_private_command_runner.py --no-cache
git diff --check
git check-ignore AGENTS.md .cache/r5b-checkpoint-b/checks.log
```

The existing ignored `run_checks.py` launches unchanged `scripts/check.py` after
removing inherited AWS/TF/provider/telemetry/proxy overrides, with stdout/stderr
in ignored protected storage. It is an offline regression driver, not a cloud
runner. Results are summarized from `.cache/f107/check-results.json` and the
private log; infrastructure results from `.cache/f4-02/checks.json`.

The exact final Linux command (PowerShell, existing local image; no pull/build):

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -m pytest tests/test_private_command_runner.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_identity_contract.py tests/test_identity_coordinator.py -q --basetemp=.cache/pytest-readiness-linux-completion
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -m pytest tests/test_private_command_runner.py -q --basetemp=.cache/pytest-runner-linux-pipes
```

The earlier Linux focused populations also passed (145/145, then 158/158 before
the last ownership case). Native inspection of the prior synthetic prepared root
confirmed **zero root state files**; the plan guard's empty-state requirement is
compatible with actual offline console preparation. No real account input was
used. Early development failures were test expectation/dependency-fixture setup
errors; the corrected tests retain failed-identity rejection and source checks.

Only synthetic responses/processes establish behavior; no genuine IAM authorization,
new-user/provider authentication, hosted CI, power-loss durability or financial
enforcement is inferred from these tests. PostgreSQL/browser integration is not
rerun for these operator-only changes; application source and prior accepted
durability/browser evidence remain unchanged.

Official documentation reviewed 2026-10-26 is linked beside the relevant claims.
No source or policy decision here changes provider NO-GO, immutable business state,
request budgets, frozen evaluation artifacts or the separate AWS deployment gates.
