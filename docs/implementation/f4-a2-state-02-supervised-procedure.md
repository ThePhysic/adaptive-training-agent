# F4-A2-state-02 — Proposed supervised ListUserPolicies procedure

2026-10-26. **Offline preparation only. No AWS call is authorized.** Run sections
separately only after their gates; do not paste/run the whole document. The new
`inline_policies.py` helper has no launcher, CLI entrypoint or live switch. Existing
executors and state-01 command/preparation semantics are unchanged.

## Preconditions

- Caller profile only `future-f4-human-admin`; target username only
  `future-f4-state-operator`; us-east-1; `https://iam.amazonaws.com` (global IAM,
  HTTPS/443). Service permission `iam:ListUserPolicies` on the exact private target
  user ARN including path. No new grant, setup, STS probe, login or account discovery.
- Owner privately supplies the already verified A1a/A1b caller/target Account, Arn
  including path and UserId. Same account, distinct users; no expectations inferred
  from this response. Codex must not inspect records, config, credentials or caches.
  ListUserPolicies cannot itself prove the caller/target identity; binding relies
  on the reviewed selected-only login configuration and fixed command.
- Private Windows PowerShell 5.1 `-NoProfile` at repository root, no OS elevation,
  transcription, debug/verbose recording, screen sharing or telemetry export.
  Protected `.cache` storage needs owner-controlled encryption and owner/SYSTEM ACLs.
- Reviewed CLI/source hashes, a new <=30-minute UTC window with >=5 minutes remaining,
  a **new state-02** preparation directory/receipt/claim, and a separately approved
  private preparation digest. Do not reuse/repurpose state-01 private artifacts.
  A changed CLI pin stops for review, never PATH lookup, installation or automatic update.
- Privately approve an allowlist of zero to **40 inline policy names**, each 1–128
  supported ASCII IAM-name characters. This is a per-response safety bound, not a
  service quota, identity grant or permission to read bodies. Empty accepts only an
  empty result. Allowed names may be absent; unexpected names stop for private review.
- **Fresh state-02 written approval must decide native CLI credential refresh/
  authentication traffic and lack of Windows OS-enforced network containment.**
  State-01/A1 risk exceptions do not transfer. If unacceptable, stop. Environment
  sanitization is not a firewall; no hard HTTP-count or MFA-use proof is claimed.

## A. Local-only preparation

No AWS process is started. The helper reads only the newly supplied private metadata
and reviewed public manifest. Real AWS config and token/cache contents are not read
or copied. The explicit existing login-cache location is for a future authorized CLI.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. .\infra\aws\private_state.ps1 -Mode Functions
try {
    $Caller = @{
        Account = (Read-FataPrivateValue 'Verified human account (private)')
        Arn = (Read-FataPrivateValue 'Verified human ARN including path (private)')
        UserId = (Read-FataPrivateValue 'Verified human UserId (private)')
    }
    $Target = @{
        Account = (Read-FataPrivateValue 'Verified state account (private)')
        Arn = (Read-FataPrivateValue 'Verified state ARN including path (private)')
        UserId = (Read-FataPrivateValue 'Verified state UserId (private)')
    }
    # Keep JSON as text: PS 5.1 array wrappers do not reliably round-trip here.
    $NamesJson = Read-FataPrivateValue 'Owner-approved policy names JSON array (private), or []'
    $Dir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a2-state-02\' + [Guid]::NewGuid().ToString('N')))
    $Spec = @{
        caller = $Caller; target = $Target; approved_policy_names_json = $NamesJson
        caller_provenance = 'owner_attested_A1a'; target_provenance = 'owner_attested_A1b'
        cli_path = (Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe')
        cli_sha256 = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
        login_cache_directory = (Join-Path $env:USERPROFILE '.aws\login\cache')
        window_start = (Read-Host 'UTC start YYYY-MM-DDTHH:mm:ssZ')
        window_end = (Read-Host 'UTC end YYYY-MM-DDTHH:mm:ssZ, <=30 minutes')
    }
    [IO.File]::WriteAllText((Join-Path $Dir 'input.json'), ($Spec | ConvertTo-Json -Depth 8))
    Assert-FataPrivateAccess (Join-Path $Dir 'input.json')
    $env:FATA_A202_DIRECTORY = $Dir
    $env:FATA_A202_REVIEW_MANIFEST = Read-Host 'Protected local path to independently reviewed public source-manifest.json'
} catch { throw 'a202_local_preparation_stopped_private_review' }
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import inline_policies as a
try:
    root = Path(os.environ['FATA_A202_DIRECTORY'])
    with a.local.private(Path(os.environ['FATA_A202_REVIEW_MANIFEST'])).open('rb') as stream:
        raw = stream.read(2097153)
    if len(raw) > 2097152:
        raise ValueError('review_manifest_limit')
    manifest = a.local.runner.strict_json(raw)
    if manifest['format'] != 'working-tree-review-v1':
        raise ValueError('review_manifest_format')
    spec = a.local.runner.strict_json(a.base.read_private(root / 'input.json'))
    spec['approved_policy_names'] = a.local.runner.strict_json(spec.pop('approved_policy_names_json').encode('utf-8'))
    spec['source_sha256'] = {n: manifest['files'][n] for n in a.SOURCES}
    a.prepare(spec, root, now=datetime.now(UTC))
except BaseException:
    print('a202_offline_preparation_stopped_private_review')
    raise SystemExit(1) from None
print('a202_offline_prepared_no_execution_authorized')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a202_preparation_stop_no_retry' }
Remove-Variable Caller,Target,NamesJson,Spec -ErrorAction SilentlyContinue
```

Source hashes come from the independently reviewed public ZIP manifest, not a fresh
source computation accepted as its own expectation. Privately review the complete
preparation and `preparation.sha256`; retain the approved digest separately for B.
It binds identity triples, names, window, CLI and source pins. The receipt is not
authorization or protection against a malicious machine owner. No private digest
belongs in public reports. Preparation during a window grants no execution permission.

Selected-only human login config, empty shared/legacy credential files, disabled
IMDS and allowlisted child environment remove inherited AWS/TF/proxy/Python/PATH/CA/
credential-process overrides. Native cache selection/refresh remains a trust and
owner-risk decision. No credential export, fallback identity or interactive login.

**STOP for independent review and explicit owner authorization.**

## B. One future supervised invocation — not authorized now

Exact command, no arbitrary arguments:

`<reviewed aws.exe> iam list-user-policies --user-name future-f4-state-operator --profile future-f4-human-admin --region us-east-1 --endpoint-url https://iam.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15`

```powershell
if ((Read-Host 'Only after written state-02 approval and risk acceptance, type A2-STATE-02-ONCE-APPROVED') -cne 'A2-STATE-02-ONCE-APPROVED') {
    throw 'a202_not_authorized'
}
$env:FATA_A202_PREPARATION_DIGEST = Read-FataPrivateValue 'Separately approved private preparation SHA-256 (private)'
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import inline_policies as a
capture = None
try:
    root = Path(os.environ['FATA_A202_DIRECTORY'])
    spec = a.claim(root, now=datetime.now(UTC), reviewed_sha256=os.environ['FATA_A202_PREPARATION_DIGEST'])
    capture = a.local.runner.capture_owned(
        a.command(spec['cli_path']), cwd=a.local.ROOT,
        env=a.environment(root, spec, os.environ), timeout=120,
        stdout_limit=65536, stderr_limit=4096,
    )
    result = a.verify_capture(capture, spec, output=root)
    a.base.write_private(root / 'result.json', (json.dumps(result) + '\n').encode())
except BaseException:
    print('{"checkpoint":"F4-A2-state-02","result":"stopped","outcome_uncertain":true}')
    raise SystemExit(1) from None
finally:
    if capture is not None:
        capture.clear()
print(json.dumps(result))
'@ | & .\.venv\Scripts\python.exe -I -
$A202Exit = $LASTEXITCODE
Remove-Item Env:FATA_A202_PREPARATION_DIGEST -ErrorAction SilentlyContinue
if ($A202Exit -ne 0) { throw 'a202_stop_private_review_no_retry' }
```

The exclusive durable claim precedes any process release. Prior claims (including
partial/corrupt/failed fsync) block retry across restart. No marker deletion or fresh
directory as automatic retry. The existing Windows Job Object owns descendants
before release; <=120s process execution + <=10s cleanup (5s wait + 5s reader join),
64KiB stdout/4KiB stderr, no shell retry or extra calls. `AWS_MAX_ATTEMPTS=1` does not
audit authentication/HTTP count. No TLS-verification weakening or custom endpoint.
On Ctrl+C/crash/timeout retain the claim; ensure owned processes stopped, never kill
unrelated processes. Unknown delivery requires fresh review, not replay. These are
local operator safeguards, not tamper-proof permits or server delivery proof.

## C. Private validation and reporting

Require completed capture, exit 0, no stderr; <=64KiB strict duplicate-key-safe JSON;
**exact** top-level PolicyNames and IsTruncated; **boolean false** truncation; <=40
distinct names, each 1–128 characters matching `[A-Za-z0-9+=,.@_-]`. No strings in
place of arrays, null/objects/numbers, whitespace/control/Unicode/path names, duplicate
names or extra fields/tokens. Any Marker/NextToken (even empty), missing flag or
truncated response stops. No silent paginator, `--query`, sizing/token flags or
next-page request. The ASCII rule is deliberately conservative, not a claim about
every service-valid Unicode name. Names are compared case-sensitively, order-free.

Well-formed complete metadata is written privately to `observed-policy-names.json`
before allowlist comparison. Unexpected valid names stay available for private
review but stop with **no success record**. Malformed/truncated/duplicate/unsupported
data and raw stderr are not retained as verified observations. Observation is not
approval or permission. Do not edit an allowlist/receipt and retry without review.

Only after private observation/summary persistence succeed, report this finite shape:

```json
{"checkpoint":"F4-A2-state-02","result":"metadata_page_verified","policy_count":0,"mfa_verified":false,"http_request_count_verified":false}
```

The zero is illustrative, not a measured AWS finding. No raw names, identifiers,
paths, hashes of private preparation, exceptions, `$Error`, config/cache contents
or responses belong in public logs/reviews. Raw buffers are cleared, not guaranteed
secure RAM erasure. Close the private session after review; agree retention/deletion
with the owner, no automatic evidence cleanup. **No GetUserPolicy or other body read**
is included, even for expected names. An empty inline list does not establish no
effective permissions; group policies, boundaries and resource grants remain unknown.

## Exact future authorization — separate from state-01

> After independent review, authorize state-02 only: one supervised initial-page
> IAM ListUserPolicies request, caller future-f4-human-admin, target only
> future-f4-state-operator, us-east-1, https://iam.amazonaws.com. Bind exact private
> caller/target identity triples/path, reviewed binary/source hashes, name allowlist
> and separately approved private preparation digest; <=30-minute UTC window,
> 64KiB/4KiB capture, 120s execution/10s cleanup, one durable claim. Explicitly decide
> state-02 native refresh/authentication and Windows no-egress-containment assumptions.
> Permit private observation/validation and sanitized reporting only. No retry,
> pagination, login, body read, additional IAM operation/grant, S3/Terraform, spending
> or automated live-executor activation. Uncertainty stops for fresh owner review.

Owner privately confirms remaining A2/A3 capacity under the proposed 40-invocation
ceiling. This unit consumes one scheduled invocation even on uncertainty; no global
ledger/automatic traversal is added. The <=40-name page bound does not guarantee that
later body closure fits remaining capacity. No permission or spending follows success.

Official public sources checked 2026-10-26: [ListUserPolicies command/options](https://docs.aws.amazon.com/cli/latest/reference/iam/list-user-policies.html),
[response, names and pagination](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListUserPolicies.html).
Public docs, synthetic tests and owner-attested past results are distinct evidence.
