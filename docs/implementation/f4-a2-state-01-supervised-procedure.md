# F4-A2-state-01 — Proposed supervised attachment-metadata read

2026-10-26. **Offline preparation only. No AWS invocation is authorized.** Review
sections separately; do not paste/run the entire document. No automated launcher or
live switch is added. Existing `execute_live()`/`execute_account()` remain disabled.
The new helper contains only local preparation, fixed command and response validation.

## Preconditions and scope

- Existing caller profile: `future-f4-human-admin`. Target IAM username only:
  `future-f4-state-operator`. Region us-east-1, global IAM HTTPS endpoint
  `https://iam.amazonaws.com`. Service permission `iam:ListAttachedUserPolicies`
  on the privately verified exact target ARN/path. No grant, STS probe, login or setup.
- Privately verified caller/target Account, Arn including exact path and UserId
  come from owner-attested A1a/A1b records. Same account, different IAM users. Codex
  must not open those records or token/cache contents. A list response contains no
  caller/target identity proof; binding relies on the selected native login source
  and frozen command. No claim of fresh independent caller verification is made.
- Use private Windows PowerShell 5.1 `-NoProfile`, repository root, no OS elevation,
  transcript, debug/verbose logging, screen sharing or telemetry. `.cache` storage
  must be owner-controlled/encrypted with reviewed owner/SYSTEM ACLs. Do not publish
  private paths, identifiers, policy names, responses or raw exceptions.
- Pin reviewed CLI bytes and source hashes from the **independently reviewed ZIP's
  public SHA-256 manifest**, copied locally under protected `.cache`. The earlier
  CLI hash below is an attestation baseline; a changed/missing binary stops for
  review, never a PATH fallback, download or version/identity probe.
- Owner privately approves a policy-name/ARN allowlist (zero to twelve entries).
  It describes permitted observations, not assumed current attachments or grants.
  Empty is valid: only an empty returned list will pass. Do not guess new ARN/path
  values or enlarge the allowlist automatically when a surprising entry is found.
- **Fresh written A2-state-01 approval must separately accept or reject native
  credential refresh/authentication traffic and lack of OS-enforced Windows egress
  containment.** A1a/A1b exceptions do not transfer. If unacceptable, stop. Environment
  isolation is not a firewall; existing native CLI/caches remain trusted components.
  TLS verification stays enabled. CLI flags cannot prove one HTTP request or MFA use.

## A. Local-only preparation — no AWS process

This block only accepts masked private metadata, creates selected-only human login
configuration/empty credential files and pins sources. It does not inspect the real
AWS config or read/copy login tokens. The explicit existing login-cache location
will be used only by a separately authorized future CLI. Provenance labels are
owner attestations, not automatic authentication. All file writes are private.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. .\infra\aws\private_state.ps1 -Mode Functions
try {
    $A2Caller = @{
        Account = (Read-FataPrivateValue 'Verified human account (private)')
        Arn = (Read-FataPrivateValue 'Verified human ARN including path (private)')
        UserId = (Read-FataPrivateValue 'Verified human UserId (private)')
    }
    $A2Target = @{
        Account = (Read-FataPrivateValue 'Verified state account (private)')
        Arn = (Read-FataPrivateValue 'Verified state ARN including path (private)')
        UserId = (Read-FataPrivateValue 'Verified state UserId (private)')
    }
    # Private JSON array of exact {PolicyName,PolicyArn} entries, or []. No grant.
    $A2Allowed = @((Read-FataPrivateValue 'Owner-approved policy allowlist JSON (private)') | ConvertFrom-Json)
    $A2Dir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a2-state-01\' + [Guid]::NewGuid().ToString('N')))
    $A2Spec = @{
        caller = $A2Caller; target = $A2Target; approved_policies = $A2Allowed
        caller_provenance = 'owner_attested_A1a'; target_provenance = 'owner_attested_A1b'
        cli_path = (Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe')
        cli_sha256 = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
        login_cache_directory = (Join-Path $env:USERPROFILE '.aws\login\cache')
        window_start = (Read-Host 'UTC start YYYY-MM-DDTHH:mm:ssZ')
        window_end = (Read-Host 'UTC end YYYY-MM-DDTHH:mm:ssZ, <=30 minutes')
    }
    [IO.File]::WriteAllText((Join-Path $A2Dir 'input.json'), ($A2Spec | ConvertTo-Json -Depth 8))
    Assert-FataPrivateAccess (Join-Path $A2Dir 'input.json')
    $env:FATA_A2_DIRECTORY = $A2Dir
    $env:FATA_A2_REVIEW_MANIFEST = Read-Host 'Protected local path to reviewed public source-manifest.json'
} catch { throw 'a2_local_preparation_stopped_private_review' }
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import attached_policies as a
try:
    root = Path(os.environ['FATA_A2_DIRECTORY'])
    with a.local.private(Path(os.environ['FATA_A2_REVIEW_MANIFEST'])).open('rb') as stream:
        raw = stream.read(2097153)
    if len(raw) > 2097152:
        raise ValueError('review_manifest_limit')
    manifest = a.local.runner.strict_json(raw)
    if manifest['format'] != 'working-tree-review-v1':
        raise ValueError('review_manifest_format')
    spec = a.local.runner.strict_json(a.read_private(root / 'input.json'))
    spec['source_sha256'] = {name: manifest['files'][name] for name in a.SOURCES}
    a.prepare(spec, root, now=datetime.now(UTC))
except BaseException:
    print('a2_offline_preparation_stopped_private_review')
    raise SystemExit(1) from None
print('a2_offline_prepared_no_execution_authorized')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a2_preparation_stop_no_retry' }
Remove-Variable A2Caller,A2Target,A2Allowed,A2Spec -ErrorAction SilentlyContinue
```

Prepare during the proposed window (<=30 minutes; at least five minutes remaining).
Expired preparation cannot authorize a later run; new metadata/window needs review.
Hash/source/config mismatch stops. Selected-only config binds the human login ARN;
empty shared/legacy credential files, disabled IMDS and an allowlisted environment
drop inherited AWS/TF/proxy/Python/PATH/CA/credential-process settings. Native login
refresh can still occur. No automatic interactive login or credential export.

**STOP HERE for independent review and explicit future owner authorization.**
Private preparation, source hashes and acknowledgement text are not permits.
Privately review the exact preparation and its `preparation.sha256` receipt, including
both identity triples, allowlist and window. Retain that approved digest separately
for masked entry in B; never derive the expected digest from the current file at
launch. It binds all private metadata to that review, not just its schema. Neither
the digest nor its receipt is authorization or tamper-proof storage against the owner.

## B. One future owner-supervised read — not authorized now

Approve only this fixed invocation and the private bindings, not a generic IAM runner:

`<reviewed aws.exe> iam list-attached-user-policies --user-name future-f4-state-operator --profile future-f4-human-admin --region us-east-1 --endpoint-url https://iam.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15`

```powershell
if ((Read-Host 'Only after written A2-state-01 approval and risk acceptance, type A2-STATE-01-ONCE-APPROVED') -cne 'A2-STATE-01-ONCE-APPROVED') {
    throw 'a2_not_authorized'
}
$env:FATA_A2_PREPARATION_DIGEST = Read-FataPrivateValue 'Separately approved private preparation SHA-256 (private)'
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import attached_policies as a
capture = None
try:
    root = Path(os.environ['FATA_A2_DIRECTORY'])
    spec = a.claim(root, now=datetime.now(UTC), reviewed_sha256=os.environ['FATA_A2_PREPARATION_DIGEST'])
    capture = a.local.runner.capture_owned(
        a.command(spec['cli_path']), cwd=a.local.ROOT,
        env=a.environment(root, spec, os.environ), timeout=120,
        stdout_limit=65536, stderr_limit=4096,
    )
    result = a.verify_capture(capture, spec, output=root)
    a.write_private(root / 'result.json', (json.dumps(result) + '\n').encode())
except BaseException:
    print('{"checkpoint":"F4-A2-state-01","result":"stopped","outcome_uncertain":true}')
    raise SystemExit(1) from None
finally:
    if capture is not None:
        capture.clear()
print(json.dumps(result))
'@ | & .\.venv\Scripts\python.exe -I -
Remove-Item Env:FATA_A2_PREPARATION_DIGEST -ErrorAction SilentlyContinue
if ($LASTEXITCODE -ne 0) { throw 'a2_stop_private_review_no_retry' }
```

The exclusive durable claim is written **before any process release**. Partial
write/fsync error, cancellation, crash or unknown delivery retains the claim; no
automatic second invocation, marker reset or new directory as retry. The reviewed
Windows Job Object primitive owns descendants before release: <=120s execution,
<=10s cleanup (5s process wait + 5s reader join), 64KiB stdout and 4KiB stderr caps.
Failure/timeout/overflow/Ctrl+C stops and closes the owned job; hard crash retains
the claim. Confirm owned processes have stopped; never kill unrelated processes.
No claim of exact server delivery, HTTP count, socket containment or secure RAM erase.
`AWS_MAX_ATTEMPTS=1` suppresses native service retries, not all authentication traffic.

## C. Private validation, evidence and reporting

Acceptance requires clean completed capture/exit 0/no stderr, bounded strict JSON,
exact top-level **AttachedPolicies + IsTruncated**, and boolean **false** truncation.
Any Marker/NextToken/extra field (even empty), missing/wrong-type/truncated flag stops.
No `--query`, path filter, CLI paginator sizing/token flags or follow-up is supported.

Each entry must contain exactly PolicyName/PolicyArn; <=12 entries; names 1–128
ASCII IAM-name characters; ARN <=2048, aws partition/iam service/no region, policy
resource, namespace `aws` or the exact private account. Supported slash-path segments
use IAM's conservative ASCII name characters; path <=512; basename must match name.
Other partitions, foreign accounts, unsupported paths, duplicate names or ARNs stop.
Some service-valid unusual paths may be deliberately rejected pending source review.
An AWS-managed ARN never grants permission merely by matching syntax/allowlist.

Well-formed complete metadata is saved only to protected `observed-policies.json`
**before allowlist comparison**; surprising valid identifiers stay available for
private owner review without replay. This file is observation, not approval evidence.
Malformed/truncated/duplicate/unsupported results are not saved as a valid page.
There is no raw response/stderr log. Unexpected entries stop and produce no success
record. Do not edit the allowlist and rerun; retain the claim and seek fresh review.
No policy body, group traversal, effective-permissions assertion or extra API read.

Allowlisted policies may be absent; an empty valid page can pass and means only no
direct managed attachments in that response. Policy order is irrelevant. Only after
private observation and success-record persistence succeed, publish this finite shape:

```json
{"checkpoint":"F4-A2-state-01","result":"metadata_page_verified","policy_count":0,"mfa_verified":false,"http_request_count_verified":false}
```

The count is illustrative, not an actual AWS result. All current evidence is synthetic.
Do not publish identifiers, paths, policy names/ARNs, raw `$Error`/exceptions or file
contents. Retain private records/claims after uncertainty; decide deletion/retention
with the owner, no automatic cleanup. Local files are not immutable AWS snapshots or
tamper-proof authority. Close the private session after review.

## Exact future authorization request

> After independent review, authorize A2-state-01 only: one supervised initial-page
> IAM ListAttachedUserPolicies invocation, caller future-f4-human-admin, target only
> future-f4-state-operator, us-east-1, https://iam.amazonaws.com. Bind private exact
> caller/target Account/Arn/path/UserId, reviewed CLI/source hashes and policy allowlist,
> the separately approved private preparation digest,
> <=30-minute attended UTC window, 64KiB/4KiB output caps, 120s execution/10s cleanup,
> durable one-shot claim and private observation/reporting. Explicitly decide whether
> to accept native refresh/authentication traffic and no OS-enforced egress containment
> for this unit. No retry, pagination, login, additional IAM read, permission grant,
> S3/Terraform, spending or automated live-executor activation. Stop on uncertainty.

The one claim consumes this unit's one scheduled invocation even on ambiguous failure;
it counts against the runbook's proposed 40 A2/A3-call ceiling. Owner confirms remaining
allowance privately; no durable multi-unit inventory ledger is introduced here.
No positive financial authority or automatic mutation follows a successful read.

Official public sources checked 2026-10-26: [CLI options/pagination](https://docs.aws.amazon.com/cli/latest/reference/iam/list-attached-user-policies.html),
[response/continuation semantics](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAttachedUserPolicies.html),
[policy field constraints](https://docs.aws.amazon.com/IAM/latest/APIReference/API_AttachedPolicy.html).
The service marks some entry fields optional; this safety protocol requires both.
Public docs and synthetic fixtures are not proof of actual native/account compatibility.
