# F4-03B-R5B, Checkpoint B — private operator and bootstrap-plan preparation

2026-10-26 (America/Los_Angeles). **Offline preparation only. Stop for review.**
No AWS CLI/API call, IAM attachment/removal, account-connected Terraform plan,
S3/backend/lock write, apply/destroy, resource creation, spending, credential
export, commit or push occurred. Only synthetic private inputs were exercised.
R5A and its hosted CI success are accepted owner-reported closure evidence.

## Permission reconciliation

The owner-established IAM user is **`future-f4-state-operator`**, group
`FutureStateOperators`, with sign-in access, console sign-in, registered MFA and
an owner-verified CLI identity. `future-f4-preflight` remains read-only and is never
used for bootstrap, a state grant or IAM administration. No profile/configuration
or group membership was changed or inspected here.

Reuse the existing sensitive outputs from `infra/aws/state-bootstrap`:

| Output/purpose | Scope retained |
| --- | --- |
| `bootstrap_operator_policy` | One exact bucket ARN; eight setup/tagging Allow actions plus the existing explicit bucket refresh reads. No object read/write/delete, bucket deletion, IAM/EC2 authority, service-action wildcard or all-bucket listing |
| `plan_operator_policy` | **Later only**: ListBucket for exactly `env:/`, GetObject for the single state key, and GetObject/PutObject/DeleteObject for its exact `.tflock` key. No state PutObject, object wildcard or bucket administration |
| `state_operator_policy` | Broader later writer; **not exported by the preparation helper, not selected, not attached** |

Both proposed principals are the same exact existing operator **user ARN**, including
its actual IAM path if any. Every statement retains account, principal, us-east-1,
HTTPS, start-inclusive/end-exclusive UTC conditions and a positive window <=2h.
These conditional Allows are **not** an IAM permissions boundary; unrelated attached
policies can grant more. Effective user/group policies, denies and session context
must be reviewed privately before execution. Registration alone does not establish
MFA use for a particular CLI/provider session; no unverified MFA-condition amendment
was added to the approved policies.

The eight setup actions remain CreateBucket, TagResource, PutBucketTagging,
PutBucketPublicAccessBlock, PutBucketOwnershipControls, PutBucketVersioning,
PutEncryptionConfiguration and PutBucketPolicy (`s3:`). Tagging fallbacks and
provider consistency waits remain as described in proposal 25. No definition of
the bucket or policy was duplicated or broadened.

An already authorized **non-root** administrator—not this operator and not
preflight—needs `iam:GetUserPolicy`, `iam:PutUserPolicy`, `iam:DeleteUserPolicy`
on the **exact selected user ARN** for named-policy precheck, installation/readback
and separately approved removal. No such rights are granted by Terraform or this
checkpoint. PutUserPolicy can replace a document and cannot be treated as a
policy-body-constrained delegation: the administrator must review the exact file
and use a fresh opaque policy name. Existing policies are not overwritten.

## Local private preparation — permitted, no account access

Use Windows PowerShell **5.1**, the existing Python 3.14 environment and cached
Terraform **1.17.0** / AWS provider **6.70.0**. Confirm an owner-controlled encrypted
volume, private terminal and no recording/transcription/debug session before real
input. Disk encryption was **not** independently attested by this checkpoint;
do not infer it from ACL checks or enable/change encryption automatically.

`private_state.ps1` creates protected directories with a DACL at creation and
verifies ownership/access before input. Existing broad directories, links/junctions
and wrong owners fail; they are not silently re-ACL'd. New roots grant the current
Windows user and SYSTEM. Verification also recognizes OWNER RIGHTS and trusted
local Administrators, as used by Python 3.14's Windows mkdir(0700). It rejects
Everyone, ordinary Users, Authenticated Users, unknown principals and Deny entries.
Local administrators can take ownership; this is not protection against a hostile
machine administrator. Windows chmod is not used as proof of confidentiality.

Run this local-only setup from the repository root; **no real values appear in
the command text, terminal output, tracked files or shell history**:

```powershell
$ErrorActionPreference = 'Stop'
. ./infra/aws/private_state.ps1
$Private = New-FataPrivateDirectory (Join-Path $PWD '.cache/r5b-checkpoint-b')
$null = New-FataPrivateDirectory (Join-Path $PWD '.cache/state-backend')
$Label = 'cb-' + [Guid]::NewGuid().ToString('N')
$SpecPath = Join-Path $Private ($Label + '.json')
if (Test-Path -LiteralPath $SpecPath) { throw 'private_input_already_exists' }
$Account = Read-FataPrivateValue 'Approved private account ID'
$OperatorArn = Read-FataPrivateValue 'Exact approved operator user ARN'
$Start = Read-FataPrivateValue 'Approved UTC start: yyyy-MM-ddTHH:mm:ssZ'
$End = Read-FataPrivateValue 'Approved UTC expiry: yyyy-MM-ddTHH:mm:ssZ (max 2h)'
$Bucket = 'fata-' + [Guid]::NewGuid().ToString('N') + '-state'
$Spec = @{
  account_id=$Account; bucket_name=$Bucket
  bootstrap_principal_arn=$OperatorArn; state_principal_arn=$OperatorArn
  permission_starts_at=$Start; permission_expires_at=$End
}
[IO.File]::WriteAllText($SpecPath, ($Spec | ConvertTo-Json),
    (New-Object Text.UTF8Encoding($false)))
Assert-FataPrivateAccess $SpecPath
$Tf = (Resolve-Path '.tools/terraform/terraform.exe').Path
& .venv/Scripts/python.exe infra/aws/state_bundle.py --spec $SpecPath --name $Label
if ($LASTEXITCODE -ne 0) { throw 'private_bundle_rejected' }
& .venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec $SpecPath --name $Label --terraform $Tf
if ($LASTEXITCODE -ne 0) { throw 'private_preparation_rejected' }
$Bundle = Join-Path $PWD ('.cache/state-backend/' + $Label)
$Review = Join-Path $Private $Label
$Root = Join-Path $Review 'source/infra/aws/state-bootstrap'
$BootstrapPolicy = Join-Path $Review 'bootstrap_operator_policy.json'
$LaterPlanPolicy = Join-Path $Review 'plan_operator_policy.json'
& .venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec $SpecPath --name $Label --verify-source
if ($LASTEXITCODE -ne 0) { throw 'private_source_binding_failed' }
```

The generated bucket name is an opaque proposal. Review it privately; no availability
probe ran. Do not put account numbers, usernames or PII in names/labels. Reject the
all-zero synthetic account before any future account operation. Profile names are
**not inferred from IAM usernames**: privately select the existing operator login
profile and the already authorized administrator profile; do not create a new profile,
credential_process bridge, static key or role assumption as part of this procedure.

The existing `state_bundle.py` remains the six-field authority: bounded JSON,
explicit UTC, exact account, no preflight writer, READY last, identical repeat a
no-op and changed/partial bundle rejection. Its bundle stays exactly three files.
The separate review directory contains the two policy proposals, copied existing
Terraform sources/lock, local-only metadata, source manifest and a distinct READY.
An existing review directory is refused; a changed window needs a fresh label and
fresh review, never an overwritten or automatically extended grant.

The helper evaluates the **exact existing named-output value expressions**, not
Python-authored IAM policies. It uses a clean copy with the existing **local**
backend, locked cached-only plugin mirror, empty credential/config/home paths,
disabled checkpoint lookup and the existing senderless loopback proxy. Only
version, local init and console run; console **never** uses `-plan`. It rejects any
proxy attempt, source/input/policy drift and remote backend/data/provisioner source.
The source manifest covers both root files, the protected-bucket module and lock.
Public cached provider links are not private data. No account-connected executor
or IAM attachment is enabled by a READY marker.

Keep all inputs, policies, manifests, binary/JSON plans, bootstrap state and recovery
copies under verified ignored storage. Do not use `Get-Content`/`terraform output`
to print their values in shared sessions. Use UTF-8 without BOM for structured
files; Windows PowerShell 5 `>` defaults to UTF-16. Never zip the working tree or
force-add ignored files. Share reviewed source and sanitized counts only.

## Exact future operator sequence — **not authorized to run now**

The command vectors below are for owner/source review. **Every account block
requires separate written approval and a reviewed bounded private-memory capture
context**: hidden native processes, 120s deadline, bounded stdout/stderr, owned
child cleanup, no raw logging, no outer replay. That live command-capture/transport
procedure remains an execution prerequisite from proposal 25; this checkpoint
deliberately ships only offline preparation/review. Do not substitute the R3
identity coordinator, the mock fixture, public terminal output or raw log files
as an unreviewed cloud launcher. Commands are exact; no account-connected command
below was invoked here.

Before the first account command, select `$OperatorProfile` and `$AdminProfile`
privately. All AWS CLI calls must carry the explicit profile and region. Terraform
uses only `$OperatorProfile`; never the administrator or preflight. In a fresh
process, reject static credential/session-token variables, alternate config/credential
files, role/web-identity/container credentials, endpoint/custom-CA/proxy overrides,
TF_LOG, TF_CLI_ARGS*, TF_VAR_* and nondefault workspace overrides. Do not print their
values. Set AWS_PROFILE to the selected operator, region/default region to us-east-1,
and AWS_EC2_METADATA_DISABLED=true. Review the direct login-session profile privately;
do not export credentials, renew automatically, change trust or disable TLS validation.
If source login renewal needs an unapproved destination, stop.

**B1 — approval for narrowly named identity/IAM reads, not IAM writes.** Capture
these responses privately; compare Account/ARN/UserId to the owner-approved private
identity evidence. Reject `:root`, default/preflight fallback, another user/role,
unexpected account or unresolved MFA context. Do not publish the response.

```powershell
# READ-ONLY AWS ACCESS APPROVAL REQUIRED BEFORE EACH CALL
Assert-FataPermissionWindow $Spec
aws sts get-caller-identity --profile $OperatorProfile --region us-east-1 --output json --no-cli-pager
Assert-FataPermissionWindow $Spec
aws sts get-caller-identity --profile $AdminProfile --region us-east-1 --output json --no-cli-pager
$BootstrapName = 'FataBootstrap-' + $Label
Assert-FataPermissionWindow $Spec
aws iam get-user-policy --user-name future-f4-state-operator --policy-name $BootstrapName --profile $AdminProfile --region us-east-1 --output json --no-cli-pager
```

The named policy must be absent (`NoSuchEntity` after privately checking the
classified response). Any existing document, other error or denial is a stop.
Registration and the previously verified CLI identity are accepted owner evidence,
not fresh proof of Terraform authentication for this new operator.

**B2 — explicit approval of one temporary IAM installation.** Approve the exact
user ARN, generated bucket, policy file/source digest, opaque name, TLS/region/time
conditions, effective permissions and <=2h window. Confirm current UTC is in that
window, session freshness covers the work, and >=5 minutes remain before starting
any command. `file://` is one quoted native argument, so Windows paths with spaces
are preserved. Nothing is attached to the group or preflight user.

```powershell
# IAM WRITE APPROVAL REQUIRED; administrator only, never root
Assert-FataPermissionWindow $Spec
aws iam put-user-policy --user-name future-f4-state-operator --policy-name $BootstrapName --policy-document ('file://' + $BootstrapPolicy) --profile $AdminProfile --region us-east-1 --no-cli-pager
# SEPARATELY APPROVED READBACK; compare decoded JSON with the exact private file
Assert-FataPermissionWindow $Spec
aws iam get-user-policy --user-name future-f4-state-operator --policy-name $BootstrapName --profile $AdminProfile --region us-east-1 --output json --no-cli-pager
```

PutUserPolicy is an add-or-replace API, not a safe blind retry. An ambiguous outcome
means “possibly attached”: stop, obtain approved readback and reconcile. Do not
overwrite an existing policy or automatically reissue the write. The administrator's
read/write endpoint is global IAM (`iam.amazonaws.com`, HTTPS/443), separately
approved from the operator's regional STS/S3 destinations.

**B3 — local init, then separate approval for one real bootstrap plan.** Reverify
source and immutable inputs; use only the prepared **state-bootstrap** root, never
deployment. Confirm local backend metadata and absent/empty bootstrap resource state.
Unexpected existing state is a recovery gate, not permission to delete/import it.
Use the prepared cached-only `offline.rc` for local plugin initialization, not a
real credential file. Local init does not create a bucket.

```powershell
& .venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec $SpecPath --name $Label --verify-source
if ($LASTEXITCODE -ne 0) { throw 'source_or_input_changed' }
$env:TF_CLI_CONFIG_FILE = Join-Path $Review 'offline.rc'
& $Tf "-chdir=$Root" init -input=false -lockfile=readonly -no-color
if ($LASTEXITCODE -ne 0) { throw 'local_init_failed' }
# ACCOUNT-CONNECTED PLAN / NETWORK / PRIVACY / BUDGET APPROVAL REQUIRED
Assert-FataPermissionWindow $Spec
$SavedPlan = Join-Path $Review 'bootstrap.tfplan'
if (Test-Path -LiteralPath $SavedPlan) { throw 'saved_plan_already_exists' }
& $Tf "-chdir=$Root" plan -input=false -no-color -detailed-exitcode -lock-timeout=0s "-var-file=$Bundle/bootstrap.tfvars.json" "-out=$SavedPlan"
```

Exit **2** is the expected six-create proposal; 0 is unexpected for a clean initial
bootstrap and requires review; 1/timeout/denial stops. No `-target`, `-replace`,
`-destroy`, `-refresh=false`, `-lock=false`, workspace switch, backend migration or
automatic retry. Show the **explicit saved file** as JSON through approved capture;
write only the resulting structured JSON privately in UTF-8, not raw CLI logs:

```powershell
# LOCAL SAVED-PLAN READ ONLY; capture structured stdout into $PlanJson privately
& $Tf "-chdir=$Root" show -json $SavedPlan
# $PlanJson names the protected UTF-8 JSON file produced by the approved capture context
& .venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec $SpecPath --name $Label --review-plan $PlanJson
if ($LASTEXITCODE -ne 0) { throw 'bootstrap_plan_rejected' }
```

The guard checks exact input/version/source binding, six unique create-only
managed addresses, bucket identity, public blocks, ownership, AES256, versioning,
known TLS deny policy and the two policy outputs. An unknown computed TLS policy
still requires the reviewed unchanged module source. It is a structural guard,
**not AWS IAM evaluation or approval to apply**. Privately retain exact binary-plan
hash, source/input binding and operator/window evidence before independent review.

Expected resources (zero IAM/EC2/ECR/SSM/DynamoDB/KMS/lifecycle-expiry additions):

1. `module.state.aws_s3_bucket.this`
2. `module.state.aws_s3_bucket_public_access_block.this`
3. `module.state.aws_s3_bucket_ownership_controls.this`
4. `module.state.aws_s3_bucket_versioning.this`
5. `module.state.aws_s3_bucket_server_side_encryption_configuration.this`
6. `module.state.aws_s3_bucket_policy.tls`

Retain `prevent_destroy`, `force_destroy=false`, all four public blocks,
BucketOwnerEnforced, Enabled versioning, AES256 SSE-S3 and HTTPS-only deny. Source
and native mock evidence establish this proposed inventory; no real plan exists.

**B4 — independent creation checkpoint.** Stop after review of that saved plan.
Bucket creation needs a new explicit authorization of that exact binary apply,
request costs, window and recovery conditions. No apply command is part of this
checkpoint. A partial/uncertain future apply is not absence; retain local state and
seek approved reconciliation, never recreate/adopt a bucket automatically.

**B5 — separate IAM removal approval.** Await/terminate owned work first and retain
evidence. Expiry ends the conditional Allow but does **not** remove its document.
The already authorized administrator removes only the exact named inline grant:

```powershell
# IAM WRITE APPROVAL REQUIRED; no automatic finally-block deletion
aws iam delete-user-policy --user-name future-f4-state-operator --policy-name $BootstrapName --profile $AdminProfile --region us-east-1 --no-cli-pager
# SEPARATELY APPROVED verification: expect classified NoSuchEntity, not raw output
aws iam get-user-policy --user-name future-f4-state-operator --policy-name $BootstrapName --profile $AdminProfile --region us-east-1 --output json --no-cli-pager
```

On interruption, timeout or uncertain IAM result: stop new work, await owned child
cleanup, preserve the original policy name/files and any plan/state, then authorize
readback/revocation separately. Do not delete artifacts, extend grants, repeat a
generation/plan or remove unrelated policies. No detached/background cloud command.

**B6 — remote-backend and lock checkpoints, later only.** Even after bucket creation,
separately verify owner/region and every protection before considering deployment
backend init. Attaching `plan_operator_policy`, initializing that S3 backend and
every lockfile lifecycle require fresh explicit approvals. Do not install it for
this local bootstrap plan. Never select the broader writer, migrate bootstrap state
into its own bucket, force-copy, force-unlock or authorize state PutObject here.

## Account-connected read inventory — identified, not executed

| Context | Reads/authorization boundary |
| --- | --- |
| Fresh local-state, six-create bootstrap plan | Regional STS `GetCallerIdentity` for normal provider credential/account validation. Repeated consumer/configuration calls are possible; there is no promised call count. With truly empty state, no existing S3 resources are refreshed and bucket-name availability is not proved |
| Credential resolution | Existing fresh direct login cache only. Sign-In refresh is a distinct network/auth operation; no automatic endpoint expansion, alternate identity, IAM fallback or IMDS access |
| Named IAM policy procedure | Administrator GetUserPolicy on exact user/name; additional effective-policy/MFA evidence supplied privately by owner or separately approved exact-user reads. No account-wide enumeration |
| If any bootstrap state/resources already exist | STOP this initial-plan procedure. Review refresh separately: HeadBucket (ListBucket), GetBucketPolicy, GetBucketAcl, GetBucketCors, GetBucketWebsite, GetBucketVersioning, GetBucketAccelerateConfiguration, GetBucketRequestPayment, GetBucketLogging, GetBucketLifecycleConfiguration, GetBucketReplication, GetObjectLockConfiguration, GetBucketTagging and the separate GetPublicAccessBlock/GetBucketOwnershipControls/GetBucketEncryption protections; GetBucketLocation is in the existing proposal. These map to the existing exact-bucket IAM reads; no object contents or ListAllMyBuckets |
| Later deployment backend | Separately approved STS, workspace discovery `env:/`, exact state GetObject and lock GetObject. Lock PutObject/DeleteObject are **writes**, not read-only planning. Init/migration/general workspaces are not implicitly covered |

Pinned provider/base source retains credential validation, so its normal identity
path uses STS and fails on error. The IAM GetUser/ListRoles fallback path is not
enabled by this root; do not add those grants or disable credential validation to
make authentication succeed. A newly configured operator's real provider behavior
still requires separately authorized observation. Unexpected calls/redirects,
global S3/STS, another bucket, custom endpoints or account deny means stop.

## Budget, approval checklist and remaining issues

Retain proposal 25's **$0.05 gross maximum proposal** and **$0.02 operational stop
threshold**, including promotional-credit consumption and retained storage. Neither
is active authorization or an enforceable AWS cap. $100 credits and the Free plan
are accepted owner findings, not permission to spend or upgrade. No resource/service
was added; cost assumptions remain those in proposal 25 and must be reconfirmed
before execution. Stop on forecast/observed $0.02, unexpected retries/services,
quota/Free-plan denial or upgrade prompt; do not wait for delayed billing to halt.

Before any actual account operation the owner must approve:

- Actual private account/bucket/exact user ARN, existing operator profile and a
  distinct already authorized non-root administrator identity; no assumed profile
  name or default credential fallback.
- Actual <=2h UTC window, fresh session/MFA evidence, effective permissions,
  encryption/ACL/privacy and source/policy file review; no broad policy/boundary change.
- Separate identity/read operations; exact IAM installation and removal; one
  account-connected local-state bootstrap plan; its endpoints, bounded private
  command capture/owned interruption handling and explicit gross budget.
- Subsequent saved-plan apply/S3 creation **separately**; remote backend/lock
  authority **separately** after protection/recovery verification. No state-writer grant.
- Retained local bootstrap state/encrypted recovery copy, 30-day or earlier Free-plan
  expiry review, no automatic state expiration or all-version cleanup.

**GO: owner review and real private input preparation under the local-only procedure.**
**NO-GO: any AWS access/write or real plan under this checkpoint.** Actual values,
profiles/admin selection, encryption/session context, execution capture/transport
review and numerical spending approval remain owner gates. No active cloud launcher
was created. R3's accepted preflight identity evidence was not rerun or treated as
proof of this new operator; preflight stays read-only.

## Verification and changed files

Source changes: new `infra/aws/private_state.ps1`,
`infra/aws/state_operator_prepare.py`, `tests/test_state_operator_preparation.py`;
one selected-user mock test in `state-bootstrap/tests/safety.tftest.hcl`; optional
stdin support in the existing offline `fixtures/backend_probe.run` for console.
`state_bundle.py`, root/module/policy definitions, provider locks, application,
CI, browser harness, migrations, financial controls and frozen data are unchanged.

The local helper creates only the two policy proposals and verifies source/inputs;
the full writer is never exported. Tests are structural/synthetic and must not be
reported as effective AWS IAM evaluation or a genuine account plan. Native console
preparation reported **zero proxy attempts**; private ACL positive/negative checks
verified rejection of broad-read ACLs without printing SIDs. Real account fields,
generated real bucket values, IAM policy bodies, credentials/state are absent from
this document and tracked review artifacts.

| Check | Observed result |
| --- | --- |
| Shared offline sequence | **20/20 commands exit 0**; **1,202 routine Python tests passed**, 46.87s; zero failures/errors/skips; 257 integration deselected |
| Focused preparation/bundle tests | **55/55 passed**, final run 1.16s; 27 new structural/private-access cases overlap the routine denominator |
| Terraform fmt/static/validation/mock plans | Three roots valid; **15/15 passed**: deployment 5, state-bootstrap 8, bucket module 2 |
| Native mock six-resource inventory | **1/1 selected-user case passed**, exactly six unique create-only addresses and protection checks; no genuine account plan |
| Native offline policy preparation | Three fresh synthetic labels completed; correct two output names, source/input binding verified, **zero proxy attempts**; no actual account values supplied |
| Terraform-core regression after stdin support | **8/8 expected synthetic loopback cases**; report records **0 real AWS requests**, no real credentials |
| Frontend/contracts/evaluations | **131/131 frontend tests**; TypeScript, format, generated contracts, build and Responses/evaluation assets pass; **24/24 development + 16/16 held-out** baseline and all 150 offline comparison dispositions reproduce |
| Windows/local safeguards | Native ACL positive/negative checks, source/input/output bounds and local window preconditions pass; all **six** future PowerShell blocks parse without execution |
| Source/privacy integrity | Ruff and formatting pass, Git diff check passes, AGENTS.md remains ignored; no protected app/policy/lock/data source drift; private artifacts remain ignored |

Commands actually executed from the repository root (no account-connected command):

```text
.venv/Scripts/python.exe -m pytest tests/test_state_operator_preparation.py tests/test_state_backend.py -q --basetemp=.cache/pytest-r5b-final
.venv/Scripts/python.exe -m pytest tests/test_state_operator_preparation.py tests/test_state_backend.py -q --basetemp=.cache/pytest-r5b-completion
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/python.exe infra/aws/fixtures/backend_probe.py --native-offline
.venv/Scripts/python.exe .cache/r5b-checkpoint-b/run_checks.py
.venv/Scripts/python.exe .cache/r5b-checkpoint-b/native_inventory.py
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name cb-synthetic-a
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name cb-synthetic-a --verify-source
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name cb-synthetic-b
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name cb-synthetic-c
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name cb-synthetic-c --verify-source
.venv/Scripts/ruff.exe check infra/aws tests/test_state_operator_preparation.py --no-cache
.venv/Scripts/ruff.exe format --check infra/aws tests/test_state_operator_preparation.py --no-cache
.tools/terraform/terraform.exe fmt -recursive infra/aws
git diff --check
git check-ignore AGENTS.md
```

The synthetic spec uses the all-zero account, dummy bucket and 2030 timestamps;
it is not a private configuration for the real operator. Native inventory uses
one disposable mock-provider test in that protected synthetic source copy and
requires a **nonzero, exactly-one pass** summary; no managed resource was applied.
`run_checks.py` strips AWS/TF/provider/telemetry/proxy overrides, captures the
unchanged routine `scripts/check.py` sequence and keeps its log ignored. Native
backend output is synthetic metadata only. The Windows PowerShell redirected
reports were UTF-16; the tool-written infrastructure `.cache/f4-02/checks.json`
is UTF-8. Operator artifacts and structured private inputs use explicit UTF-8.

Development findings: a Windows test-file filter initially matched zero tests
despite Terraform exit 0, so final native proof checks both the run count and exact
inventory. The first console experiment disabled backend initialization and was
correctly rejected; final preparation initializes **only the clean local backend**.
The ACL negative test uses the DACL-only .NET setter to avoid unnecessary
owner/group restoration privileges. No AWS denial, account result or permission
effectiveness was inferred from these local corrections.

Validation environment: Windows PowerShell **5.1.26100.9711**, Python **3.14.9**,
Node **24.22.1**, Ruff **0.17.2**, cached Terraform **1.17.0**, AWS provider **6.70.0**.
No package/service installation was needed. PostgreSQL/browser integration was
not rerun for these filesystem/policy-preparation changes; accepted R5A CI closure
is retained, and no new database, UI or real-AWS correctness claim is made.

Official references reviewed 2026-10-26: [Terraform console/local-state behavior](https://developer.hashicorp.com/terraform/cli/commands/console),
[pinned provider configuration](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.70.0/internal/conns/config.go),
[pinned base identity path](https://raw.githubusercontent.com/hashicorp/aws-sdk-go-base/v2.0.0-beta.76/aws_config.go),
[pinned bucket refresh/create behavior](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.70.0/internal/service/s3/bucket.go),
[sign-in managed policy](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html),
[PutUserPolicy](https://docs.aws.amazon.com/cli/latest/reference/iam/put-user-policy.html),
[GetUserPolicy](https://docs.aws.amazon.com/cli/latest/reference/iam/get-user-policy.html),
[DeleteUserPolicy](https://docs.aws.amazon.com/cli/latest/reference/iam/delete-user-policy.html).
