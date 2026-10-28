# F4-A1b — Supervised state-operator identity procedure

2026-10-26. **Offline preparation only. No live operation is currently authorized.**
These blocks are a proposed operator procedure, not a runnable automation entrypoint.
Run sections separately only after their gates have been reviewed. Do not paste/run
the entire document. No IAM/S3/Terraform permission follows from an identity match.

## Prerequisites and separate risk decision

- Use private Windows PowerShell 5.1 `-NoProfile`, at the repository root, without
  OS elevation, transcription, debug/verbose recording, screen sharing or exports.
  Private `.cache` storage needs owner-controlled encryption and verified ACLs.
- Owner confirms the existing alias is exactly `future-f4-state-operator`, with
  browser-login authentication for the intended IAM user. No IAM/profile creation.
- Obtain authoritative Account, exact Arn **including path**, and AWS-generated
  UserId from previously verified private owner records or the separately approved
  reference read below. Never use an unverified STS response as its own expectation.
  Codex must not inspect the owner's identity file, profile or token/cache contents.
- Freeze/review this document, its helper and the existing capture dependencies.
  The previously attested CLI hash is below; a changed binary stops for review.
  No PATH fallback, installation, version probe or login is part of this procedure.
- **Fresh A1b-specific owner approval must accept or reject native credential
  refresh/authentication traffic and lack of OS egress containment.** A1a's risk
  exception does not apply. If refresh is unacceptable, do not run this workflow.
  Environment isolation does not prevent a CLI binary from opening arbitrary sockets.
- Profile name is not identity proof. Neither matching STS nor MFA registration proves
  MFA use. One CLI invocation and `AWS_MAX_ATTEMPTS=1` do not prove one HTTP request.
  TLS verification remains enabled; no custom CA, proxy, role or credential process.

## A. Local-only preparation

This creates only protected local metadata/configuration. It does not execute AWS,
read the real AWS config, or read/copy the login cache. The selected-only profile is
constructed from the privately approved ARN. Login cache **location** is explicit;
only a future authorized CLI would read it. No unrelated profile is included.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. .\infra\aws\private_state.ps1 -Mode Functions
$A1bCli = Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe'
$A1bHash = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
$A1bExpected = @{
    Account = (Read-FataPrivateValue 'Previously verified state account (private)')
    Arn = (Read-FataPrivateValue 'Previously verified state user ARN, including path (private)')
    UserId = (Read-FataPrivateValue 'Previously verified state UserId (private)')
}
$A1bProvenance = Read-Host 'owner_confirmed_existing or separately_authorized_get_user'
$A1bSpec = @{
    expected = $A1bExpected; provenance = $A1bProvenance
    cli_path = $A1bCli; cli_sha256 = $A1bHash
    login_cache_directory = (Join-Path $env:USERPROFILE '.aws\login\cache')
    window_start = (Read-Host 'Proposed UTC start YYYY-MM-DDTHH:mm:ssZ')
    window_end = (Read-Host 'Proposed UTC end YYYY-MM-DDTHH:mm:ssZ, at most 30 minutes')
}
# Retain this directory/claim across interruptions. New directory is not retry approval.
$A1bDir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a1b-supervised\' + [Guid]::NewGuid().ToString('N')))
[IO.File]::WriteAllText((Join-Path $A1bDir 'spec.json'), ($A1bSpec | ConvertTo-Json -Depth 6))
Assert-FataPrivateAccess (Join-Path $A1bDir 'spec.json')
$env:FATA_A1B_DIRECTORY = $A1bDir
@'
import sys
from datetime import UTC, datetime
from pathlib import Path
import os
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import state_sts as s
try:
    root = Path(os.environ['FATA_A1B_DIRECTORY'])
    spec = s.local.runner.strict_json(s.local.read_private(root / 'spec.json'))
    s.prepare(spec, root, now=datetime.now(UTC))
except BaseException:
    print('a1b_preparation_stopped_private_review_required')
    raise SystemExit(1) from None
print('a1b_offline_prepared_no_execution_authorized')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a1b_stop_no_retry' }
Remove-Variable A1bSpec,A1bExpected -ErrorAction SilentlyContinue
```

Preparation validates the exact fixed state identity, expectation provenance label,
CLI hash, selected configuration and UTC window (<=30 minutes, >=5 minutes remaining).
Provenance is an **owner attestation**, not automatically authenticated evidence.
The child environment will be rebuilt from OS essentials, dropping inherited AWS,
TF, BOTO, proxy, PATH, Python, CA and credential-process overrides. Shared/legacy
credential files are empty; IMDS is disabled. Existing login cache tokens stay in
place and must not be printed/exported. Expired sessions stop; no automatic login.

**STOP. Review preparation before any section B execution.** Preparation/JSON/claims
are not permits. Keep the original `.cache` directory; never delete/recreate a claim
to retry. No native CLI command, including IAM reference reads, has been approved.

## B. Explicit authorization checkpoint and one future invocation

Owner must approve the exact private identity, reviewed source/binary, this capture
assembly, attended UTC window and A1b-specific risk decision in writing. The phrase
below is acknowledgement, **not an authorization switch**. Its presence does not
enable either disabled live executor. This block is documentation for later review;
there is no new live CLI entrypoint in `state_sts.py`.

The only future AWS command is:

`<reviewed aws.exe> sts get-caller-identity --profile future-f4-state-operator --region us-east-1 --endpoint-url https://sts.us-east-1.amazonaws.com --output json --no-cli-pager --cli-connect-timeout 5 --cli-read-timeout 15 --no-cli-auto-prompt --no-paginate`

```powershell
if ((Read-Host 'Only after written A1b approval and risk acceptance, type A1B-ONCE-APPROVED') -cne 'A1B-ONCE-APPROVED') {
    throw 'a1b_not_authorized'
}
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import state_sts as s
capture = None
try:
    root = Path(os.environ['FATA_A1B_DIRECTORY'])
    spec = s.claim(root, now=datetime.now(UTC))
    # Claim retained before any process release, including failed/uncertain launches.
    capture = s.local.runner.capture_owned(
        s.command(spec['cli_path']), cwd=s.local.ROOT,
        env=s.environment(root, spec, os.environ), timeout=120,
        stdout_limit=8192, stderr_limit=4096,
    )
    result = s.verify_capture(capture, spec['expected'])
    s.local.write_private(root / 'result.json', (json.dumps(result) + '\n').encode())
except BaseException:
    print('{"checkpoint":"F4-A1b","result":"stopped","outcome_uncertain":true}')
    raise SystemExit(1) from None
finally:
    if capture is not None:
        capture.clear()
print(json.dumps(result))
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a1b_stop_private_review_no_retry' }
```

The existing ownership primitive releases one fixed command after Windows Job Object
ownership, bounds private capture to 8192 stdout/4096 stderr bytes, enforces a 120s
execution deadline, and allows up to 10s bounded cleanup (5s process wait + 5s reader
join). Overflow, timeout, Ctrl+C, stderr, nonzero exit or uncertain cleanup stops.
The wrapper bounds the process, not an AWS server's operation or HTTP count; cancellation
does not prove no request reached AWS. No retries/automatic follow-up. On interruption
retain the directory/claim, confirm owned CLI descendants have exited; do not kill
unrelated processes. Job closure handles owned descendants. An OS/Python hard crash
retains the claim; use private review and a fresh explicit decision before any repeat.
This is not an anti-tampering security boundary against the machine owner.

## C. Private verification and sanitized reporting

Verification inside B uses strict JSON (duplicate keys rejected), exactly three string
fields, fixed IAM-user shape and exact case-sensitive Account/Arn/UserId equality.
Root, roles, federation, wrong path/user/account/UserId and malformed results fail.
No raw stdout/stderr is displayed or saved. Capture buffers are cleared on all paths;
this is not a claim of secure memory erasure. Expected private metadata remains under
ACL-protected `.cache`; choose retention/deletion with the owner, never automatic.

Only after all checks and private result persistence succeed:

```json
{"checkpoint":"F4-A1b","result":"identity_matched","mfa_verified":false,"http_request_count_verified":false}
```

Any other result is stopped/uncertain, never success. Do not paste raw exceptions,
`$Error`, identity objects, paths, token/cache/config contents or stderr into reviews.
Close the private session after review. No automatic second STS, IAM read, login,
profile fallback, boundary change, S3/Terraform or spending follows success/failure.

## Conditional reference read — separately approved human administrator only

If existing authoritative state expectations are unavailable, **do not run A/B**.
Prepare only this independent reference-read unit. It is not part of A1b STS approval.

Proposed exact command:

`<reviewed aws.exe> iam get-user --user-name future-f4-state-operator --profile future-f4-human-admin --region us-east-1 --endpoint-url https://iam.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15`

Human service permission is `iam:GetUser` on the **exact privately approved state-user
ARN including path**. No grant installation is included; AccessDenied means stop.
The IAM endpoint is global, with us-east-1 configuration/signing context. No new
human identity probe, `--query`, implicit current-user target or extra IAM read.

Before execution, separately approve:

1. Human-admin caller/profile and the already verified private human Account/Arn/UserId
   from A1a; target state's known Account/Arn/path/username (UserId is the unknown).
2. The exact command above, reviewed binary, <=30-minute attended UTC window,
   human-specific refresh/no-egress risk decision, bounded capture/ownership and
   private output/retention. A1a completion is not permission for this IAM read.
3. A **distinct** private directory, selected-only human login configuration and durable
   one-shot reference claim before release, <=120s/8192 stdout/4096 stderr capture,
   with the same stop/cleanup/no-retry behavior as B. Do not reuse the state preparation
   or change its fixed command/profile to run IAM. Review the reference assembly
   below independently before invoking it; no executable reference entrypoint is added.
4. Check the response with `state_sts.reference_identity` against privately trusted
   Account/Arn. Require exact UserName, Arn, Path and bounded AWS UserId; GetUser does
   not return a top-level Account field. Store only the verified three-field identity
   privately with provenance `separately_authorized_get_user`. Do not print the return
   value. User creation/MFA/boundary metadata is private and is not further evaluated
   or promoted to authorization evidence in this narrow unit.

Stop on shape, target, path, identity, authentication, privacy, delivery or cleanup
uncertainty; no automatic retries/login/permission expansion. Reference-read approval
does not approve the later state STS invocation. If existing records suffice, omit
this unit entirely.

### R-local: reference metadata only, no networking

Use a separate private `-NoProfile` session and independently reviewed human
authentication/risk decision. Supply the known target Account/Arn/path and already
verified human expectations, never the private human record to Codex. Exact UserId
for the **target** is deliberately not requested here.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. .\infra\aws\private_state.ps1 -Mode Functions
$RefDir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a1b-reference\' + [Guid]::NewGuid().ToString('N')))
$RefHuman = @{
    Account = (Read-FataPrivateValue 'Previously verified human account (private)')
    Arn = (Read-FataPrivateValue 'Previously verified human ARN (private)')
    UserId = (Read-FataPrivateValue 'Previously verified human UserId (private)')
}
$RefSpec = @{
    human = $RefHuman
    target_account = (Read-FataPrivateValue 'Known state account (private)')
    target_arn = (Read-FataPrivateValue 'Known state ARN including path (private)')
    cli_path = (Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe')
    cli_sha256 = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
    login_cache_directory = (Join-Path $env:USERPROFILE '.aws\login\cache')
    window_start = (Read-Host 'Reference UTC start YYYY-MM-DDTHH:mm:ssZ')
    window_end = (Read-Host 'Reference UTC end YYYY-MM-DDTHH:mm:ssZ, <=30 minutes')
}
[IO.File]::WriteAllText((Join-Path $RefDir 'input.json'), ($RefSpec | ConvertTo-Json -Depth 6))
Assert-FataPrivateAccess (Join-Path $RefDir 'input.json')
$env:FATA_A1B_REFERENCE_DIRECTORY = $RefDir
@'
import hashlib, json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import state_sts as s
try:
    root = Path(os.environ['FATA_A1B_REFERENCE_DIRECTORY'])
    spec = s.local.runner.strict_json(s.local.read_private(root / 'input.json'))
    spec['sources'] = {n: hashlib.sha256((s.local.ROOT / n).read_bytes()).hexdigest() for n in s.SOURCES}
    s.validate_reference(spec, now=datetime.now(UTC))
    config = '[profile future-f4-human-admin]\nregion = us-east-1\nlogin_session = ' + spec['human']['Arn'] + '\n'
    s.local.selected_configuration(config, spec['human'])
    s.local.write_private(root / 'reference.json', (json.dumps(spec) + '\n').encode())
    s.local.write_private(root / 'human-config', config.encode())
    s.local.write_private(root / 'empty-credentials', b'')
    for name in ('home', 'tmp'):
        (root / name).mkdir(mode=0o700)
        s.local.private(root / name)
except BaseException:
    print('a1b_reference_preparation_stopped')
    raise SystemExit(1) from None
print('a1b_reference_offline_prepared_no_execution_authorized')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a1b_reference_stop_no_retry' }
Remove-Variable RefHuman,RefSpec -ErrorAction SilentlyContinue
```

**STOP for separate reference-read authorization.** A1b STS approval is insufficient.

### R-authorized: one future human GetUser reference invocation

```powershell
if ((Read-Host 'Only after separate written reference approval, type A1B-REFERENCE-ONCE-APPROVED') -cne 'A1B-REFERENCE-ONCE-APPROVED') {
    throw 'a1b_reference_not_authorized'
}
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import state_sts as s
capture = None
try:
    root = Path(os.environ['FATA_A1B_REFERENCE_DIRECTORY'])
    spec = s.local.runner.strict_json(s.local.read_private(root / 'reference.json'))
    s.validate_reference(spec, now=datetime.now(UTC))
    if s.local.read_private(root / 'empty-credentials'):
        raise ValueError('reference_empty_credentials_required')
    for name in ('home', 'tmp'):
        if any(s.local.private(root / name).iterdir()):
            raise ValueError('reference_directory_changed')
    env = s.reference_environment(root, spec['human'], spec['login_cache_directory'], spec['target_account'], os.environ)
    # Exclusive durable claim before release. Never remove it to retry.
    s.local.write_private(root / 'reference.claim', b'possibly_started\n')
    capture = s.local.runner.capture_owned(
        s.reference_command(spec['cli_path']), cwd=s.local.ROOT, env=env,
        timeout=120, stdout_limit=8192, stderr_limit=4096,
    )
    expected = s.reference_identity(capture, spec['target_account'], spec['target_arn'])
    s.local.write_private(root / 'expected-state.json', (json.dumps(expected) + '\n').encode())
except BaseException:
    print('{"checkpoint":"F4-A1b-reference","result":"stopped","outcome_uncertain":true}')
    raise SystemExit(1) from None
finally:
    if capture is not None:
        capture.clear()
print('{"checkpoint":"F4-A1b-reference","result":"reference_verified","state_sts_authorized":false}')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a1b_reference_stop_private_review_no_retry' }
```

This is a separate named, reviewed assembly, not permission to call the generic
runner with arbitrary AWS arguments. The only persisted returned data is the
privately verified target Account/Arn/UserId; no raw response is retained. R success
is a trusted reference under the approved human authentication assumptions, not an
STS identity match, MFA proof, permissions audit or permission for A1b execution.

## Exact future authorization request

> After independent review, authorize one supervised F4-A1b STS invocation using
> the exact state profile/command above, privately approved Account/Arn/UserId and
> provenance, reviewed binary/source hashes, during [UTC start/end, <=30 minutes].
> Explicitly accept or reject native credential refresh/authentication traffic and
> lack of OS-enforced egress containment for A1b. Permit only private bounded capture,
> exact verification and sanitized reporting. No automatic retry/login/follow-up,
> IAM/S3/Terraform change, spending or live-executor activation. Interruption or
> uncertainty requires a fresh owner decision. If expectations are missing, approve
> only the separately reviewed human reference read first, not this invocation.

Official public documentation checked 2026-10-26: [STS options and socket timeouts](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html),
[GetUser target/response](https://docs.aws.amazon.com/cli/latest/reference/iam/get-user.html),
[native login refresh](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).
Public documentation review and synthetic tests are not live AWS verification.
