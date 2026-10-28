# F4-A1a — Proposed supervised STS procedure

2026-10-26. **Preparation only; execution awaits independent review and fresh owner
authorization. No AWS command was run.** Run the blocks separately, in order, only
when their prerequisites are satisfied. Do not paste/run the entire document.

The latest owner decision permits a separate manually supervised A1a workflow with
documented native authentication refresh and no OS-enforced egress claim. This
exception applies to A1a only. It does not approve IAM/S3/Terraform activity or
change human_sts.py, its attempt fence, either disabled executor, runner safeguards,
permissions boundaries or tests. It is not the previously proposed isolated executor.

## Operator prerequisites

- Use a private Windows PowerShell **5.1, -NoProfile** session at the repository
  root; no Windows administrator elevation is needed. The AWS IAM administrator
  identity is distinct from an elevated Windows process.
- No active/mandatory transcription, debug/verbose capture, screen sharing or
  unapproved logging/export. If privacy cannot be assured, stop; do not change
  machine policies. The ignored `.cache` location must be on owner-controlled
  encrypted storage with the existing private ACL helper available.
- Existing profile is exactly `future-f4-human-admin`, using its previously approved
  browser-login identity. Owner privately confirms its selected config is direct
  login_session for the expected IAM user in us-east-1, with no role, SSO,
  credential_process, static credentials, inherited defaults, plugins or custom
  endpoint/CA settings. Do not print config, read tokens, copy caches or recreate setup.
- Have the accepted **exact Account, Arn and UserId** privately available. No values
  are supplied by this document. Do not infer them from the profile name or accept
  a new returned identity as the expectation.
- The accepted installation was CLI 2.38.5 at the local Programs path below, with
  the recorded software hash. A changed/missing binary means stop for review, not
  installation/update or a PATH fallback. No native version command is necessary.

## A. Local preparation — no networking

Expected values are masked input and memory-only. Process environment changes below
do not modify the user's AWS profiles, login cache, persistent environment or system
settings. Empty shared/legacy credential files and disabled IMDS remove fallback
sources; explicit profile selection and private response checks remain essential.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. .\infra\aws\private_state.ps1 -Mode Functions
$A1Cli = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
$A1Hash = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
if (-not (Test-Path -LiteralPath $A1Cli -PathType Leaf)) { throw 'a1a_cli_missing' }
if ((Get-FileHash -LiteralPath $A1Cli -Algorithm SHA256).Hash.ToLowerInvariant() -cne $A1Hash) {
    throw 'a1a_cli_changed'
}
$A1Expected = @{
    Account = (Read-FataPrivateValue 'Expected account (private)')
    Arn = (Read-FataPrivateValue 'Expected IAM user ARN (private)')
    UserId = (Read-FataPrivateValue 'Expected UserId (private)')
}
if ($A1Expected.Account -cnotmatch '^[0-9]{12}$' -or
    $A1Expected.Arn -cnotmatch ('^arn:aws:iam::' + $A1Expected.Account + ':user/(?:[A-Za-z0-9+=,.@_-]+/)*future-f4-human-admin$') -or
    $A1Expected.UserId -cnotmatch '^[A-Za-z0-9]{16,128}$') { throw 'a1a_expectation_invalid' }
$A1Dir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a1a-supervised\' + [Guid]::NewGuid().ToString('N')))
$A1Empty = Join-Path $A1Dir 'empty-credentials'
[IO.File]::WriteAllText($A1Empty, '')
Assert-FataPrivateAccess $A1Empty
$A1Err = Join-Path $A1Dir 'stderr.txt'
# Remove process-only overrides by name; never print their values.
@([Environment]::GetEnvironmentVariables('Process').Keys) | Where-Object {
    $_ -match '^(AWS_|BOTO)' -or $_ -match 'PROXY'
} | ForEach-Object { [Environment]::SetEnvironmentVariable($_, $null, 'Process') }
$env:AWS_CONFIG_FILE = Join-Path $env:USERPROFILE '.aws\config'
$env:AWS_LOGIN_CACHE_DIRECTORY = Join-Path $env:USERPROFILE '.aws\login\cache'
$env:AWS_SHARED_CREDENTIALS_FILE = $A1Empty
$env:AWS_CREDENTIAL_FILE = $A1Empty
$env:BOTO_CONFIG = $A1Empty
$env:AWS_MAX_ATTEMPTS = '1'
$env:AWS_RETRY_MODE = 'standard'
$env:AWS_EC2_METADATA_DISABLED = 'true'
$env:AWS_CSM_ENABLED = 'false'
$env:AWS_IGNORE_CONFIGURED_ENDPOINT_URLS = 'true'
$env:AWS_REGION = 'us-east-1'
$env:AWS_DEFAULT_REGION = 'us-east-1'
$A1Raw = $null
$A1Exit = $null
$A1Verified = $false
```

**STOP HERE.** No execution approval is currently granted. Do not invoke AWS,
including a preliminary identity/configure/login/version command.

## B. Exact owner-authorized operation — future approval required

Owner/reviewer must approve this procedure and then the one invocation in an
attended UTC window no longer than 30 minutes, naming the private expected identity
and binary hash. The confirmation phrase is only an operator acknowledgement of
that written authorization; typing it does not grant authorization.

```powershell
if ((Read-Host 'Only after written owner approval, type A1A-ONCE-APPROVED') -cne 'A1A-ONCE-APPROVED') {
    throw 'a1a_not_authorized'
}
$A1Verified = $false
try {
    # Local manual-workflow marker before launch; never reuse/delete it to retry.
    # This is not the automated offline fence or permission to enable an executor.
    $A1Claim = [IO.File]::Open((Join-Path $A1Dir 'attempt.claim'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $A1Claim.WriteByte(1); $A1Claim.Flush($true) } finally { $A1Claim.Dispose() }
    $A1Raw = & $A1Cli sts get-caller-identity --profile future-f4-human-admin --region us-east-1 --endpoint-url https://sts.us-east-1.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15 2> $A1Err
    $A1Exit = $LASTEXITCODE
} catch { throw 'a1a_stopped_private_review_required_no_retry' }
if ($A1Exit -ne 0 -or (Get-Item -LiteralPath $A1Err).Length -ne 0) {
    throw 'a1a_stopped_private_review_required_no_retry'
}
```

Exactly one shell invocation, no loop, job, detached work, automatic retry or
follow-up. Stdout is captured in `$A1Raw`, not displayed or saved; stderr is confined
to the private directory. PowerShell native-stderr/error handling may stop early;
that is a stop, not a reason to rerun with looser error handling. Never print `$Error`,
`$_`, raw output or stderr. Use the generic stop classification below.

Monitor elapsed time. **Proposed supervised stop: 120 seconds**, then Ctrl+C and confirm
the owned foreground CLI has exited before ending the session. Do not kill unrelated
processes. This manual procedure does **not** guarantee an automated whole-process
deadline, hard output-size limit or descendant cleanup. The command's 5s/15s options
are socket timeouts. These differences are explicit review points, not changes to
the automated runner's stronger limits. If those stronger bounds are required for
this manual checkpoint, reject this procedure rather than silently claiming them.

## C. Private identity verification — no additional AWS calls

```powershell
try {
    $A1Verified = $false
    if ($null -eq $A1Exit -or $A1Exit -ne 0 -or (Get-Item -LiteralPath $A1Err).Length -ne 0) {
        throw 'execution_not_completed_cleanly'
    }
    $A1Identity = ($A1Raw -join "`n") | ConvertFrom-Json -ErrorAction Stop
    $A1Fields = (@($A1Identity.PSObject.Properties.Name | Sort-Object -CaseSensitive) -join ',')
    if ($A1Fields -cne 'Account,Arn,UserId') { throw 'invalid_shape' }
    foreach ($A1Field in @('Account','Arn','UserId')) {
        if ($A1Identity.$A1Field -isnot [string] -or
            -not [string]::Equals($A1Identity.$A1Field, $A1Expected[$A1Field], [StringComparison]::Ordinal)) {
            throw 'identity_mismatch'
        }
    }
    $A1Verified = $true
} catch { throw 'a1a_identity_not_verified_stop_no_retry' }
```

Success requires native exit 0, no stderr, valid JSON with exactly those three string
properties and all three exact private matches. This rejects root, assumed-role,
federated, wrong-account/user or wrong-UserId results through the expected-identity
binding. Do not display either object or change expectations to make a mismatch pass.
The native CLI formatter is trusted here; this manual JSON check is not the strict
duplicate-key parser of the isolated preparation utilities.

## D. Sanitized reporting and stop policy

Only after C succeeds:

```powershell
if (-not $A1Verified) { throw 'a1a_not_verified_no_success_report' }
Remove-Variable A1Raw,A1Identity,A1Expected,A1Verified -ErrorAction SilentlyContinue
'{"checkpoint":"F4-A1a","result":"identity_matched","mfa_verified":false,"http_request_count_verified":false}'
```

On any error, report only `F4-A1a: stopped; private review required; no retry`.
Do not publish account/ARN/UserId, raw JSON/stderr, paths, cache contents or tokens.
Retain the marker and private evidence, including an uncertain/failed attempt;
do not create a fresh directory to repeat without fresh owner approval. Removing
variables is not secure memory erasure. Close the private session after review;
set private evidence retention/deletion with the owner, with no automatic cleanup.

Authentication failure/expiry, unexpected prompt, changed binary, identity mismatch,
privacy loss or an unresolved interruption means stop. An interactive `aws login`
requires its own owner decision; no automatic login, credential export, access-key
creation, endpoint/profile substitution or follow-up AWS command is included.

## Accepted limitations and current evidence

For **this A1a operator workflow only**, native cached-credential refresh and related
authentication traffic are accepted risk assumptions. This is not the former
STS-only/no-refresh transport design. Local flags/markers do not establish OS egress
containment or a hard single-HTTP-request guarantee. MFA registration or a matching
STS response does not prove MFA use for that request. The human administrator is
not authorized as the routine Terraform deployment identity.

Official references checked on 2026-10-26: [GetCallerIdentity options/TLS defaults](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html),
[native login refresh](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html),
[CLI retry configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html).
Public documentation review is not live-account evidence.

Validation in this task is local syntax/structure/source preservation only. No block
was executed, no profile/credential/cache was inspected and no AWS executable ran.
Only this document is added; existing source, tests, policies and historical records
are preserved. This task grants no IAM/S3/billing/Terraform change or later unit.

Observed checks: Windows PowerShell parser accepted all **four blocks with zero
errors**; AST inspection found exactly **one** fixed native STS invocation and
verified its literal service/action/profile/region/endpoint/options. Project
`scripts/review_source.py check` parsed **174 Python files** with native/3.13 grammar;
`git diff --check` passed. No application tests are claimed as rerun for this
documentation-only change. Source-preservation evidence is kept under ignored
`.cache/f4-a1a-supervised/`.

## Exact future authorization request — not granted here

> Authorize one manually supervised invocation of the fixed GetCallerIdentity
> command in section B, using future-f4-human-admin, us-east-1 and
> https://sts.us-east-1.amazonaws.com, the reviewed binary hash and privately
> approved Account/Arn/UserId, during [owner-specified UTC start/end, <=30minutes].
> Accept documented native authentication-refresh traffic, no OS egress containment,
> no hard single-HTTP-request claim and the disclosed manual time/output/cleanup
> limitations. Permit only local private verification and sanitized reporting.
> No shell-level retry, interactive login, additional AWS CLI command, IAM/S3/billing
> mutation, Terraform use or generic-executor activation is authorized. Any failure
> or uncertainty stops for a fresh owner decision.

Independent reviewer and owner must approve/reject this exact proposal separately.
