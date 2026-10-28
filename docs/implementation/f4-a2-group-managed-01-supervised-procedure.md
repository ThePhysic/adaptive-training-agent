# F4-A2-group-managed-01 — Proposed supervised group-policy metadata read

2026-10-27 diagnostic integration revision. **Offline preparation only; this is
not live execution authorization.** This updated source cannot reopen the stopped
managed invocation. Retain its original preparation, digest, claim and evidence
unchanged; no new directory may be used as its replay. No diagnostic is backfilled.
Historical postmortem records describe the earlier generic-stop procedure.


2026-10-26. **Offline preparation only; no live authorization requested or granted.**
Review sections separately; do not run this entire document. This procedure has one
fixed interface, Managed, and never invokes the other group-policy operation.

## Scope and prerequisites

Caller `future-f4-human-admin`, target **FutureStateOperators**, us-east-1,
`https://iam.amazonaws.com` (global IAM, verified HTTPS/443). Exactly ListAttachedGroupPolicies,
service permission `iam:ListAttachedGroupPolicies` on the exact privately approved group ARN/path.
No new grant, login, identity probe, pagination, GetGroup, body read or traversal.

Before any future execution, require:

- Privately verified A1a caller Account/Arn/path/UserId and new **prospective** group
  approval containing exact GroupName, Arn, Path, GroupId in that same account.
  GroupName is fixed. No guessed ARN/path/ID or inference of identity from this
  policy response. The response proves neither caller nor target identity. Native
  selected-login/fixed-command binding remains trusted, not fresh identity proof.
- Owner recognition/setup recollection is not policy classification. The reported
  name SignInLocalDevelopmentAccess is **not** assumed managed or inline; no ARN,
  permissions or attachment is fabricated. Independently approve exact managed policy names/ARNs.
  Nonempty expectations require owner_independently_reviewed provenance. Empty
  owner_explicit_deny_all is an explicit deny-all observation choice, not a guess
  of zero policies; nonempty observations then stop. No missing allowlist default.
- If authoritative group fields or policy expectations are unavailable, **stop**.
  The [handoff's owner-only local resolution steps](f4-a2-group-policy-handoff.md)
  do not authorize Codex to read private files, issue another AWS request or use
  returned policies as their own preapproved expectations. No old claim/result
  is changed, deleted, copied as a permit or retroactively validated.
- Private Windows PowerShell 5.1 `-NoProfile` in repo root, no OS elevation, debug,
  transcript, screen sharing/export. Owner-controlled encrypted `.cache`, reviewed
  owner/SYSTEM ACLs. Exact reviewed CLI/source hashes from the public review ZIP,
  new <=30-minute UTC window (>=5 minutes remaining), new dedicated preparation,
  separately approved private digest, exclusive durable one-shot claim.
- **Fresh separate F4-A2-group-managed-01 owner authorization** must explicitly decide native
  CLI refresh/authentication traffic and lack of verified Windows OS-level egress
  containment. State-03 and the other operation authorize nothing here. No hard
  single-HTTP-request/MFA assertion from flags or output. Native cache contents
  remain uninspected; expired/changed authentication stops, no automatic login.

## A. Local-only preparation

This creates only new private metadata/configuration. It does not read real AWS
configuration, credentials, login-cache contents or old state-03 artifacts. JSON is
held as masked text until strict Python decoding (PowerShell 5.1 array safeguard).

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. .\infra\aws\private_state.ps1 -Mode Functions
try {
    $Caller = @{
        Account = (Read-FataPrivateValue 'Previously verified human account (private)')
        Arn = (Read-FataPrivateValue 'Previously verified human ARN/path (private)')
        UserId = (Read-FataPrivateValue 'Previously verified human UserId (private)')
    }
    $Group = @{
        GroupName = 'FutureStateOperators'
        Arn = (Read-FataPrivateValue 'Prospectively approved exact group ARN (private)')
        Path = (Read-FataPrivateValue 'Prospectively approved exact group path (private)')
        GroupId = (Read-FataPrivateValue 'Prospectively approved exact group GroupId (private)')
    }
    $AllowJson = Read-FataPrivateValue 'Independently approved managed {PolicyName,PolicyArn} JSON array (private), or explicit []'
    $Provenance = Read-Host 'owner_independently_reviewed or owner_explicit_deny_all'
    $Dir = New-FataPrivateDirectory (Join-Path (Get-Location).Path ('.cache\a2-group-managed-01\' + [Guid]::NewGuid().ToString('N')))
    $Spec = @{
        caller = $Caller; group = $Group; policy_allowlist_json = $AllowJson
        caller_provenance = 'owner_attested_A1a'
        group_provenance = 'owner_prospectively_reviewed_group'
        policy_expectations_provenance = $Provenance
        cli_path = (Join-Path $env:LOCALAPPDATA 'Programs\Amazon\AWSCLIV2\aws.exe')
        cli_sha256 = 'a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d'
        login_cache_directory = (Join-Path $env:USERPROFILE '.aws\login\cache')
        window_start = (Read-Host 'UTC start YYYY-MM-DDTHH:mm:ssZ')
        window_end = (Read-Host 'UTC end YYYY-MM-DDTHH:mm:ssZ, <=30 minutes')
    }
    [IO.File]::WriteAllText((Join-Path $Dir 'input.json'), ($Spec | ConvertTo-Json -Depth 8))
    Assert-FataPrivateAccess (Join-Path $Dir 'input.json')
    $env:FATA_GP_MANAGED_DIRECTORY = $Dir
    $env:FATA_GP_MANAGED_MANIFEST = Read-Host 'Protected local path to independently reviewed public source-manifest.json'
} catch { throw 'group_inventory_local_preparation_stopped' }
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import group_policy_inventory as p
a = p.Managed
try:
    root = Path(os.environ['FATA_GP_MANAGED_DIRECTORY'])
    with p.local.private(Path(os.environ['FATA_GP_MANAGED_MANIFEST'])).open('rb') as stream:
        raw = stream.read(2097153)
    if len(raw) > 2097152:
        raise ValueError('review_manifest_limit')
    manifest = p.local.runner.strict_json(raw)
    if manifest['format'] != 'working-tree-review-v1':
        raise ValueError('review_manifest_format')
    spec = p.local.runner.strict_json(p.base.read_private(root / 'input.json'))
    spec['approved_managed_policies'] = p.local.runner.strict_json(spec.pop('policy_allowlist_json').encode('utf-8'))
    spec['source_sha256'] = {n: manifest['files'][n] for n in p.SOURCES}
    a.prepare(spec, root, now=datetime.now(UTC))
except BaseException:
    print('group_inventory_offline_preparation_stopped')
    raise SystemExit(1) from None
print('group_inventory_offline_prepared_no_execution_authorized')
'@ | & .\.venv\Scripts\python.exe -I -
if ($LASTEXITCODE -ne 0) { throw 'group_inventory_stop_no_retry' }
Remove-Variable Caller,Group,AllowJson,Spec -ErrorAction SilentlyContinue
```

Privately review the complete preparation and preparation.sha256. Retain the approved
digest separately for later masked entry, not recomputed from current data as its own
expectation. It binds caller/group identity, policy expectations/provenance, window
and CLI/source pins. Receipt/acknowledgement are not authorization or tamper-proof
storage. Source pins cover both independent interfaces and their reviewed dependencies.
Do not alter source/config/identities concurrently. A changed binary stops; no PATH
fallback, update, new keys/profile, credential export or role escalation.

**STOP for independent review. No live authorization is requested by this task.**

## B. Future separately authorized operation only

Exact command:

`<reviewed aws.exe> iam list-attached-group-policies --group-name FutureStateOperators --profile future-f4-human-admin --region us-east-1 --endpoint-url https://iam.amazonaws.com --output json --no-cli-pager --no-cli-auto-prompt --no-paginate --cli-connect-timeout 5 --cli-read-timeout 15`

```powershell
if ((Read-Host 'Only after separate written F4-A2-group-managed-01 approval, type GROUP-MANAGED-01-ONCE-APPROVED') -cne 'GROUP-MANAGED-01-ONCE-APPROVED') {
    throw 'group_inventory_not_authorized'
}
$env:FATA_GP_MANAGED_DIGEST = Read-FataPrivateValue 'Separately approved private preparation SHA-256 (private)'
@'
import json, os, sys
from datetime import UTC, datetime
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'infra/aws'))
import group_policy_inventory as p
a = p.Managed
trace = p.diagnostic.FailureDiagnostics(a.UNIT)
capture = None
root = None
claimed = False
failure = None
try:
    trace.mark('pre_release_review')
    root = Path(os.environ['FATA_GP_MANAGED_DIRECTORY'])
    spec = a.claim(root, now=datetime.now(UTC),
                   reviewed_sha256=os.environ['FATA_GP_MANAGED_DIGEST'], diagnostics=trace)
    claimed = True
    trace.mark('capture_preparation')
    argv = a.command(spec['cli_path'])
    env = a.environment(root, spec, os.environ)
    trace.begin_capture()
    capture = p.local.runner.capture_owned(
        argv, cwd=p.local.ROOT, env=env, timeout=120,
        stdout_limit=65536, stderr_limit=4096,
    )
    result = a.verify_capture(capture, spec, output=root, diagnostics=trace)
except BaseException as error:
    failure = error
finally:
    if capture is not None:
        try:
            p.diagnostic.clear_capture(capture, trace)
        except BaseException as error:
            if failure is None:
                failure = error
if failure is None:
    try:
        trace.mark('result_persistence')
        p.base.write_private(root / 'result.json', (json.dumps(result) + '\n').encode())
        trace.mark('finished')
    except BaseException as error:
        failure = error
if failure is not None:
    try:
        report = trace.failure_report(failure, output=root if claimed else None)
    except BaseException:
        report = {'checkpoint': 'F4-A2-group-managed-01', 'result': 'stopped',
                  'outcome_uncertain': True, 'failure_code': 'unknown',
                  'process_release': 'unknown', 'cleanup': 'uncertain',
                  'diagnostic_record': 'not_saved'}
    print(json.dumps(report))
    raise SystemExit(1) from None
print(json.dumps(result))
'@ | & .\.venv\Scripts\python.exe -I -
$GroupExit = $LASTEXITCODE
Remove-Item Env:FATA_GP_MANAGED_DIGEST -ErrorAction SilentlyContinue
if ($GroupExit -ne 0) { throw 'group_inventory_stop_private_review_no_retry' }
```


The diagnostic context is scoped to this literal interface only. Claim/review,
capture setup, possible process release, response validation and result persistence
are tracked separately. Failure before successful claim return publishes only a
sanitized report; it does not write a diagnostic into the preparation directory.
This includes a failed/partial claim and a concurrent caller blocked by an existing
claim. After successful claim return, a bounded `failure-diagnostic.json` may be
written exclusively using the existing private writer. It is never overwritten;
partial writes remain retained and failed diagnostic writes do not change the
execution failure or permit retry. No raw output, exception text, identities,
policy metadata, paths or private digest enters that diagnostic or public report.

Buffer cleanup occurs before success persistence; cleanup failures latch uncertainty
and stop success. Diagnostic-storage interruptions are contained; the final fixed
fallback remains stopped/uncertain if failure reporting itself fails. The outer
PowerShell stop is unchanged. Hard process termination or failed stdout delivery
can still prevent any report; the claim is authoritative for blocking reuse, not
proof of process launch or HTTP delivery. A fully written result followed by a
persistence/report failure is not automatically repaired, replayed or overwritten.
Native authentication/authorization is never inferred from an exit/stderr category.

One fixed command, no action selector. Dedicated record kind/digest/directory/claim
cannot be reused by the other interface or state-03. An exclusive fsynced claim is
created before any process release. Failed/partial claims, cancellation/restart or
unknown delivery never release it. No reset, retry, automatic next call or fresh
directory as replay. Reviewed Job Object owns descendants before release: 120s
execution + <=10s cleanup, 64KiB stdout/4KiB stderr. Confirm owned cleanup; never
kill unrelated processes. On uncertainty retain private evidence and stop.

Child environment is allowlisted: selected-only human login config, empty shared/
legacy credentials, disabled IMDS, no inherited AWS/TF/proxy/Python/PATH/CA/process
overrides. No TLS weakening or alternate endpoint. Native AWS_MAX_ATTEMPTS=1 is not
HTTP-count proof and does not prevent authentication traffic. OS egress containment
is not established. Raw buffers are cleared, not guaranteed securely erased.

## C. Exact response validation and private reporting

Exact top-level AttachedPolicies and IsTruncated. At most 12 distinct entries, each exactly PolicyName/PolicyArn. Reuse reviewed ASCII IAM-name (1–128) and supported path validation, ARN <=2048 with matching basename, aws/iam/no-region policy resource. AWS-managed namespace aws is permitted; customer policies must match the private account. Duplicate names or ARNs stop. No ARN is inferred from a policy name.

Require completed capture/exit 0/no stderr and strict duplicate-key-safe JSON <=64KiB,
exact response fields and explicit boolean IsTruncated:false. Reject all Marker/
NextToken/extra fields (even empty), truncation/missing flags, duplicates, malformed/
oversized/unsupported data. No automatic pagination, filtering, body read, other
metadata request or operation. Allowlisted entries may be absent; no result is assumed.

Complete well-formed unexpected observations are saved to protected observed-policies.json
before allowlist rejection; no success record. Malformed/truncated/duplicate data is
not promoted as verified metadata. Owner reviews privately without replay; never use
that same observation as the prior expectation. Only after observation and summary
persistence succeed, publish checkpoint/result/policy_count plus unverified MFA/HTTP
flags. Example shape (count illustrative, not a measured result):

```json
{"checkpoint":"F4-A2-group-managed-01","result":"metadata_page_verified","policy_count":0,"mfa_verified":false,"http_request_count_verified":false}
```

No raw policy/group/account identifiers, private digests, raw exceptions/$Error,
responses, cache/config or credentials in public logs/reviews. Agree local retention
privately; no automatic evidence deletion. A metadata pass proves neither permissions
nor boundary attachment. Group may provide inherited authority; current classification
and actual contents remain unknown. No policy removal/creation/attachment/replacement
or boundary installation. Success/failure does not authorize the other operation.

## Future boundary, not a live authorization request

Any later invocation requires **its own** owner approval of this exact operation,
caller/group identity/path/ID, independently reviewed expectations, binary/source
hashes, private digest, new UTC window, capture/privacy/retention and native-refresh/
Windows-egress risk decision. Denial/unknown delivery/source mismatch/expiry/privacy
loss stops; no login, retry, grant or scope expansion. Owner counts every failed/
uncertain scheduled invocation against the existing proposed 40-call A2/A3 ceiling.
Owner supplies the complete approved global A2/A3 managed-policy allowlist (<=12 distinct ARNs), including prior approvals; do not drop previous entries to evade the limit. This helper does not independently audit an unprovided global ledger.
No financial authority or automatic recovery/traversal is introduced.

Official public sources reviewed 2026-10-26: [API](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListAttachedGroupPolicies.html),
[CLI](https://docs.aws.amazon.com/cli/latest/reference/iam/list-attached-group-policies.html).
Public docs/synthetic tests/owner-attested evidence remain distinct. No current
native/account compatibility is proven. Stop for independent review only.
