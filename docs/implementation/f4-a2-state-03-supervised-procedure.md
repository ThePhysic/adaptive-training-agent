# F4-A2-state-03 — Proposed supervised ListGroupsForUser procedure

2026-10-26. **Offline only. No AWS request is authorized or requested in this task.**
The blocks are for independent review, not instructions to execute now. No launcher,
general IAM interface or live switch is added. Previous executors remain disabled.

## Scope and private prerequisites

- Exactly `iam:ListGroupsForUser`, caller `future-f4-human-admin`, target
  `future-f4-state-operator`, us-east-1, `https://iam.amazonaws.com` (HTTPS/443,
  global IAM). Service permission on the exact privately approved target-user ARN
  including path. No grant, login, STS/identity repeat, pagination or traversal.
- Privately verified A1a/A1b caller/target Account/Arn/path/UserId, same account and
  distinct users. No expected identity is learned from a list response. A list does
  not itself prove its caller/target; native selected-login/fixed-command binding is
  a reviewed trust assumption. Codex must not inspect any private records/cache.
- Private Windows PowerShell 5.1 `-NoProfile`, repository root, no OS elevation,
  debug/transcription/screen sharing or external logging. Owner-controlled encrypted
  `.cache` storage and reviewed owner/SYSTEM ACLs. No account/group identifiers or
  private preparation hashes in public logs, review artifacts or telemetry.
- Pin CLI bytes/source hashes from the independently reviewed public ZIP manifest.
  Changed/missing binary or source stops, no PATH fallback, installation or update.
  New <=30-minute UTC window, >=5 minutes remaining, **new state-03** directory,
  distinct kind/receipt/claim and separately reviewed private preparation digest.
- Owner approves **at most four distinct group identities**, with exact GroupName,
  Path, Arn and GroupId. `approved_groups` must be the owner's complete globally
  approved A2/A3 group set, including prior approved groups, not a fresh replacement
  that hides accumulated usage. Owner retains the overall ledger; no global ledger
  is implemented here. Actual returned membership may be a subset, never expanded
  automatically. Empty allowlist is deny-all for nonempty results, **not a prediction
  of zero groups**. Missing authoritative GroupIds blocks a passing nonempty result;
  do not guess, accept IDs from that same response as expectations or issue GetGroup.
- Fresh, separate owner decision on **state-03** native refresh/authentication
  traffic and no verified Windows OS-level egress containment remains mandatory
  before any future execution. State-01/02/A1 decisions do not transfer. Local flags
  and process ownership do not prove single HTTP count, MFA use or network containment.

## A. Local preparation only

No AWS process is started. This prepares only private metadata, selected-only human
login configuration and empty credential files. It never reads real config or tokens.
The cache **location** is explicit for a future separately authorized CLI. JSON stays
masked text until strict Python decoding, avoiding the reviewed PowerShell 5.1 array
wrapping problem. Caller/target provenance is owner attestation, not fresh audit.

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
    $GroupsJson = Read-FataPrivateValue 'Complete approved A2/A3 group identity JSON array (private), <=4, or []'
    $Dir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a2-state-03\' + [Guid]::NewGuid().ToString('N')))
    $Spec = @{
        caller = $Caller; target = $Target; approved_groups_json = $GroupsJson
        caller_provenance = 'owner_attested_A1a'; target_provenance = 'owner_attested_A1b'
        cli_path = (Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe')
        cli_sha256 = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
        login_cache_directory = (Join-Path $env:USERPROFILE '.aws\login\cache')
        window_start = (Read-Host 'UTC start YYYY-MM-DDTHH:mm:ssZ')
        window_end = (Read-Host 'UTC end YYYY-MM-DDTHH:mm:ssZ, <=30 minutes')
    }
    [IO.File]::WriteAllText((Join-Path $Dir 'input.json'), ($Spec | ConvertTo-Json -Depth 8))
    Assert-FataPrivateAccess (Join-Path $Dir 'input.json')
    $env:FATA_A203_DIRECTORY = $Dir
    $env:FATA_A203_REVIEW_MANIFEST = Read-Host 'Protected local path to independently reviewed public source-manifest.json'
} catch { throw 'a203_local_preparation_stopped_private_review' }
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import groups_for_user as a
try:
    root = Path(os.environ['FATA_A203_DIRECTORY'])
    with a.local.private(Path(os.environ['FATA_A203_REVIEW_MANIFEST'])).open('rb') as stream:
        raw = stream.read(2097153)
    if len(raw) > 2097152:
        raise ValueError('review_manifest_limit')
    manifest = a.local.runner.strict_json(raw)
    if manifest['format'] != 'working-tree-review-v1':
        raise ValueError('review_manifest_format')
    spec = a.local.runner.strict_json(a.base.read_private(root / 'input.json'))
    spec['approved_groups'] = a.local.runner.strict_json(spec.pop('approved_groups_json').encode('utf-8'))
    spec['source_sha256'] = {n: manifest['files'][n] for n in a.SOURCES}
    a.prepare(spec, root, now=datetime.now(UTC))
except BaseException:
    print('a203_offline_preparation_stopped_private_review')
    raise SystemExit(1) from None
print('a203_offline_prepared_no_execution_authorized')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'a203_preparation_stop_no_retry' }
Remove-Variable Caller,Target,GroupsJson,Spec -ErrorAction SilentlyContinue
```

Privately review `preparation.json` and its `preparation.sha256` receipt, retain the
approved digest separately, and supply that reviewed value later. Never compute a
fresh digest of current data and use it as its own expectation. It binds identities,
groups, window and CLI/source pins; neither a receipt nor typing acknowledgement is
authorization or tamper-proof local storage. Source pins cover all reused helpers.
Selected-only human config, empty shared/legacy credentials, disabled IMDS and an
allowlisted environment drop inherited AWS/TF/proxy/Python/PATH/CA/process overrides.
Native cache/refresh behavior remains trusted and unverified. No interactive login,
credential export, alternate profile, static-key fallback or automatic refresh opt-in.

**STOP. Independent review is the next action. No live approval is requested here.**

## B. Future supervised read — cannot run under this task's authorization

Exact fixed command:

`<reviewed aws.exe> iam list-groups-for-user --user-name future-f4-state-operator --profile future-f4-human-admin --region us-east-1 --endpoint-url https://iam.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15`

```powershell
if ((Read-Host 'Only after separate written state-03 approval and risk acceptance, type A2-STATE-03-ONCE-APPROVED') -cne 'A2-STATE-03-ONCE-APPROVED') {
    throw 'a203_not_authorized'
}
$env:FATA_A203_PREPARATION_DIGEST = Read-FataPrivateValue 'Separately approved private preparation SHA-256 (private)'
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import groups_for_user as a
capture = None
try:
    root = Path(os.environ['FATA_A203_DIRECTORY'])
    spec = a.claim(root, now=datetime.now(UTC), reviewed_sha256=os.environ['FATA_A203_PREPARATION_DIGEST'])
    capture = a.local.runner.capture_owned(
        a.command(spec['cli_path']), cwd=a.local.ROOT,
        env=a.environment(root, spec, os.environ), timeout=120,
        stdout_limit=65536, stderr_limit=4096,
    )
    result = a.verify_capture(capture, spec, output=root)
    a.base.write_private(root / 'result.json', (json.dumps(result) + '\n').encode())
except BaseException:
    print('{"checkpoint":"F4-A2-state-03","result":"stopped","outcome_uncertain":true}')
    raise SystemExit(1) from None
finally:
    if capture is not None:
        capture.clear()
print(json.dumps(result))
'@ | & .\.venv\Scripts\python.exe -I -
$A203Exit = $LASTEXITCODE
Remove-Item Env:FATA_A203_PREPARATION_DIGEST -ErrorAction SilentlyContinue
if ($A203Exit -ne 0) { throw 'a203_stop_private_review_no_retry' }
```

Exclusive durable claim **before process release**; prior/partial/failed-fsync claims
block replay across restart. Reviewed Windows Job Object ownership before release,
120s execution + <=10s cleanup (5s process wait + 5s reader join), 64KiB stdout/4KiB
stderr. No retry, automatic call, paging, poll or group-policy traversal. Native
`AWS_MAX_ATTEMPTS=1` is not an audit of authentication/HTTP count. TLS verification
remains on; no alternate endpoint/CA/proxy. On timeout/Ctrl+C/crash retain the claim,
confirm owned cleanup; do not kill unrelated processes or create a new directory as
automatic retry. No exact-delivery or enforced-socket-containment claim is made.

## C. Exact group response and private evidence

Require clean completed capture/exit 0/no stderr and bounded duplicate-key-safe JSON.
Top-level keys **exactly Groups and IsTruncated**, explicit boolean **false**, <=4
group objects. Tokens/Marker/extra fields (even empty), missing flags or truncation
stop, never fetch the next page. Each object has exactly:

| Field | Supported contract |
| --- | --- |
| GroupName | 1–128 ASCII IAM-name characters `[A-Za-z0-9+=,.@_-]` |
| GroupId | 16–128 ASCII word characters `[A-Za-z0-9_]`; exact private expected ID |
| Path | `/` or slash-delimited supported name-character segments ending `/`, <=512; no empty/dot/traversal segments |
| Arn | 20–2048; exactly `arn:aws:iam::<private-account>:group<Path><GroupName>`; same account, correct partition/service/no region, no `aws` namespace |
| CreateDate | Valid aware ISO-8601 string: seconds, optional 1–6 fractional digits, `Z` or numeric minute offset; calendar/time validity checked |

Approved identities have **exactly GroupName/GroupId/Path/Arn**, not CreateDate.
Timestamp is validated creation metadata, not a guessed identity expectation. Other
fields match approved identities exactly and case-sensitively. Duplicate IDs/ARNs
or duplicate names (including case-folded ambiguity) stop. No name-only trust or
silently adopted GroupId. Service-valid unusual paths/Unicode/time representations
outside this conservative protocol stop for review, not automatic relaxation.

Complete well-formed observations, including unexpected groups, are saved privately
to `observed-groups.json` **before** allowlist comparison. A changed GroupId, path or
name is unexpected even if another field matches. Unexpected observations stop with
no success record. Malformed/truncated/duplicate/oversized/unsupported pages are not
promoted to valid metadata. No raw response/stderr log. The owner can review retained
unexpected identities privately; no automated new read or allowlist update follows.

Sanitized success contains only checkpoint/result/group_count and unverified MFA/
HTTP flags. A synthetic example with **nonzero** membership:

```json
{"checkpoint":"F4-A2-state-03","result":"metadata_page_verified","group_count":1,"mfa_verified":false,"http_request_count_verified":false}
```

This is illustrative, not live group evidence. Do not expose names, IDs, ARNs,
account/path/timestamps, private digests, exceptions or `$Error`. Buffers are cleared,
not guaranteed securely erased. Private record retention/deletion needs owner review;
no automatic evidence cleanup. A complete membership page does not reveal group
policies or prove effective permissions. No GetGroup or policy-body read is included.

## Remaining authorization boundary — specification, not a request

Before any future execution, a **separate** owner decision must name this exact
command/caller/target/endpoint, private identity bindings, full <=4-group allowlist,
reviewed binary/source hashes and private preparation digest, attended <=30-minute
UTC window, capture/privacy/retention bounds and fresh state-03 native refresh/
Windows-egress risk decision. No receipt, flag or past result grants permission.
Uncertainty stops for fresh review, never retry/login/expansion. Owner counts this
one scheduled invocation, including uncertainty, against the proposed 40-call A2/A3
ceiling. No durable global ledger or additional financial authority is introduced.
Current task stops for independent review and does not solicit live authorization.

Official public sources checked 2026-10-26: [command/options](https://docs.aws.amazon.com/cli/latest/reference/iam/list-groups-for-user.html),
[response/pagination](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListGroupsForUser.html),
[Group fields](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Group.html).
The API Group type requires CreateDate; some examples omit it. This protocol requires
it and fails closed on missing data; actual CLI compatibility remains unverified.
