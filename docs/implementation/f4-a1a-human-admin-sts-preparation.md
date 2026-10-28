# F4-A1a — Human-administrator STS preparation

2026-10-26. **Offline implementation and synthetic evidence only. Stop for review.**
No AWS CLI invocation, account request, credential/cache inspection, token export,
login/refresh, IAM modification, Terraform remote operation, spending, commit or
push occurred. The accepted runbook's approval units remain independent.

## Implementation and security decisions

Added `infra/aws/human_sts.py`, a single-purpose **preparation** CLI. Reused the
existing fixed identity-command constructor, private ACL checker, strict JSON
parser, owned-process capture and STS tunnel policy. No dependency or application,
Terraform, IAM-scope or existing-runner change was needed.

The module can prepare/re-attest protected local metadata and classify synthetic
captures. It cannot launch AWS, load credentials, construct an external sender,
refresh authentication or select another action. Its `execute_live()` always
raises. The existing generic `execute_account()` remains unchanged and disabled.
No flag, environment variable, credentials or preparation record grants execution.

Prepared controls and their evidence:

| Control | Implemented offline behavior |
| --- | --- |
| Fixed operation | Only `sts get-caller-identity`, human profile, us-east-1 and the exact regional HTTPS endpoint; no service/action/profile/endpoint/extra-argument parameters |
| Private identity | Exactly Account/Arn/UserId; matching same-account IAM user named `future-f4-human-admin`, including its privately approved path; root, role, federation and other users rejected |
| Configuration | Selected-only profile snapshot with only region/login_session; no defaults, extra profiles, static keys, credential_process, role/SSO sources, plugins or endpoint/CA overrides |
| Environment proposal | Reject inherited AWS/TF/proxy/BOTO controls; allow OS basics only; isolated HOME/config/empty credentials/login-cache/temp; IMDS disabled; legacy BOTO_CONFIG points to empty credentials; client metrics disabled |
| Routing proposal | Owned loopback guard required; empty NO_PROXY, explicit proxy settings; existing senderless STS policy rejects all external forwarding by default and permits at most one exact CONNECT only with an explicitly supplied connector |
| Retry/output bounds | CLI AWS_MAX_ATTEMPTS=1/standard, no outer retries; 120s capture ceiling, 8KiB stdout/4KiB stderr, 5s connect/15s read; owned descendants and existing wait/join cleanup budgets of up to another 10s |
| Private preparation | Inputs <=8KiB; exact fields, UTC metadata window <=30 minutes, >=5 minutes remaining; claimed session expiry >=120s+5 minutes; local absolute aws/aws.exe path and SHA-256; no links/UNC path |
| Re-attestation | Verify binary and seven source hashes, exact argv, config, empty credential file and empty private runtime directories; live=true/stale/modified preparations rejected |
| Storage | Existing ignored `.cache` boundary, owner/private ACL checks, exclusive 0600 writes/fsync; no overwrite or automatic cleanup/retry after failure |
| Reporting | Finite classifications only; buffers cleared after classification; no identifiers, stdout, stderr, tokens, URLs or raw exceptions in public summaries |

The binary hash detects changes; it does not authenticate an installer or all CLI
dependencies. No actual CLI version/package or human profile was inspected. The
30-minute window is metadata for a future proposal, **not an authorization permit**.
The session expiry is operator-supplied metadata, **not verified credential evidence**.

## Exact future command — not executable through this implementation

The generated argv is the privately pinned absolute binary plus exactly:

```powershell
# FUTURE REVIEW VECTOR ONLY. No live executor exists in this milestone.
& $A1Cli sts get-caller-identity --profile future-f4-human-admin --region us-east-1 --endpoint-url https://sts.us-east-1.amazonaws.com --output json --no-cli-pager --cli-connect-timeout 5 --cli-read-timeout 15 --no-cli-auto-prompt --no-paginate
```

No `--query`, unsigned request, custom CA, disabled certificate verification,
arbitrary arguments or automatic follow-up is supported. TLS/hostname verification
is the CLI default; a prepared command is not proof of a real TLS session.
[STS CLI contract](https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html).

The operation needs no additional IAM Allow, but still requires explicit account,
traffic/privacy and operator authorization. It proves neither MFA use nor absence
of other permissions. No IAM setup needs recreating.

## Authentication investigation and live blocker

Official sources reviewed on 2026-10-26:

- [AWS CLI login](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)
  documents browser-login caches and automatic credential refresh.
- [Login provider settings](https://docs.aws.amazon.com/sdkref/latest/guide/feature-login-credentials.html)
  documents short-lived credentials, login_session and AWS_LOGIN_CACHE_DIRECTORY.
- [Configuration precedence](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
  and [environment settings](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
  explain why selecting a profile alone does not isolate every credential source.
- [AWS CLI retries](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html)
  documents max_attempts including the initial request.
- [Botocore upstream LoginProvider/LoginCredentialFetcher](https://github.com/boto/botocore/blob/develop/botocore/credentials.py)
  shows cached refreshable credentials and Sign-In token renewal. This moving
  upstream source is **not evidence of the installed CLI's exact implementation**.

There is no documented CLI **no-login-refresh** setting in these sources.
Expiration metadata and AWS_MAX_ATTEMPTS do not disable authentication refresh.
The existing tunnel blocks known refresh destinations before its connector;
it does not authorize those destinations when credentials expire.

**Live NO-GO remains:** an environment-configured proxy is not an OS egress sandbox,
and a blind CONNECT tunnel cannot inspect HTTP actions, redirects or multiple
requests inside one TLS connection. The CLI's selected source/transport/refresh
behavior has not been natively verified here. This task does not implement a weaker
live workaround or claim these controls are already enforceable against a real CLI.

Before live execution, a separately reviewed, single-purpose execution binding must
prove the installed CLI honors the route, fails without fallback and cannot bypass
the guard, including Sign-In/IMDS/direct sockets and redirects. Use an appropriate
owned-process egress restriction and synthetic native-CLI tests, or stop and seek
an architectural decision. Do not replace login with exported/static credentials,
credential_process, a custom signer or a broader network allowance automatically.

Missing/expired/near-expiry session means stop. No automatic `aws login`, Sign-In
refresh, cache deletion, another profile or identity probe follows. Neither this
metadata preparation nor cached STS success establishes MFA authentication context.

## Private operator inputs and local setup

No user setup was performed. Future operator prerequisites:

1. Keep the existing human-admin IAM/MFA/browser-login setup. Independently confirm
   the existing profile's binding and private expected Account/Arn/UserId from
   accepted evidence; profile naming alone is not proof.
2. Use encrypted, owner-controlled local storage and Windows PowerShell 5.1 without
   transcription. Reuse `infra/aws/private_state.ps1` Functions mode and
   `New-FataPrivateDirectory` for a fresh ignored `.cache/f4-a1a/<opaque-label>`
   directory. Existing directories are checked, not silently re-ACL'd.
3. Supply a protected manifest and selected-only config snapshot; do not point the
   helper at the real AWS configuration/cache. Use masked private input, not shell
   literals, terminal output, chat attachments or shared review archives.
4. Independently attest the installed trusted CLI v2 bundle/path/version and binary
   hash. The preparation can hash the selected local binary but never executes it.
5. Supply factual session-expiry metadata only if available through an approved
   private procedure. Unknown expiry means stop; do not invent a timestamp or inspect
   token values. This milestone has no credential loader or cache-staging command.

Manifest keys, all required with no additions:

| Field | Value/validation |
| --- | --- |
| expected | Object containing exact private string Account, Arn and UserId |
| profile / region / endpoint | Fixed public constants from the command above |
| window_start / window_end | UTC `YYYY-MM-DDTHH:MM:SSZ`, positive <=30 minutes; >=5 minutes left at verification |
| session_expires_at | Same UTC form; >=7 minutes after verification time; attestation only |
| cli_path / cli_sha256 | Absolute local trusted aws/aws.exe and lowercase 64-character hex SHA-256 |

The private selected config has exactly one `[profile future-f4-human-admin]`
section and only `region = us-east-1` plus `login_session = <private expected ARN>`.
No real values belong in tracked files. Use owner-only protected writes, UTF-8
without BOM, exclusive creation, and ACL verification from the existing procedure.

Local preparation sequence, after independently protecting those files and a fresh
output directory (variables are private local paths, not actual values here):

```powershell
.venv/Scripts/python.exe infra/aws/human_sts.py --manifest $A1Manifest --selected-config $A1SelectedConfig --output $A1Output
if ($LASTEXITCODE -ne 0) { throw 'a1a_offline_preparation_failed' }
.venv/Scripts/python.exe infra/aws/human_sts.py --verify-only --output $A1Output
if ($LASTEXITCODE -ne 0) { throw 'a1a_offline_verification_failed' }
```

Output is only offline_prepared/offline_preparation_verified with live_execution=false.
Private output contains preparation.json, selected-config, empty-credentials and
empty home/login-cache/tmp directories. It contains **no staged credentials or
authorization**. There is no actual AWS execution command in this CLI.

## Synthetic outcomes and adversarial evidence

Example successful fixture summary, containing no identity:

```json
{"evidence":"offline_fixture","operation_completed":true,"identity_matched":true,"safety_failure":null,"request_sent":true}
```

Here request_sent=true refers **only to synthetic response evidence**, never AWS.
A connection claim followed by cancellation, timeout, process error, malformed
response or incomplete cleanup yields request_sent=null (uncertain). A rejected
route with no claim yields false. A strict complete response with the wrong identity
can establish synthetic completion while identity_matched remains false. No
unmatched identity is accepted. Inconsistent summaries cannot be saved.

The 112 new cases cover the requested 20 adversarial categories: correct response;
wrong account/user/UserId; root/assumed/federated identities; malformed, duplicate,
missing, extra, nested and oversized JSON; stderr/process/authentication failures;
controlled-clock timeout and event-driven cancellation; endpoint/region changes;
credential/default/profile/role/SSO/legacy-file substitutions; near/expired session
metadata; blocked refresh; proxy/process configuration; duplicate connections and
concurrent private result writes; other actions/extra arguments and unconditional
live rejection. Additional tests cover source/binary/config tampering, partial
fsync failure, native ACLs, finite public CLI errors and privacy canaries.

Owned fixture children use synthetic Python processes, not AWS CLI. Loopback socket
barriers prove cancellation/timeout cleanup; EOF/reset confirms peer termination.
Existing descendant/sibling-isolation tests remain intact. Native CLI login/token
formats, refreshed credentials, live TLS, actual API delivery and MFA remain untested.

## Commands and observed results

Windows Python 3.14.9, Ruff 0.17.2; cached Terraform 1.17.0/AWS 6.70.0. No installation.
Final source checks:

| Command | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/f4-a1a/pytest-final --junitxml=.cache/f4-a1a/routine-final.xml --tb=short` | **1,490 passed, 257 integration deselected**, 72.98s; includes 112 A1a cases, no warnings |
| `.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe` | fmt passes; three roots validate; **21 mock plans passed** (5 deployment/14 bootstrap/2 module); no account init/plan |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **173 Python files** pass native and 3.13 AST grammar |
| `.venv/Scripts/ruff.exe check src scripts tests infra experiments --no-cache` | Pass |
| `.venv/Scripts/ruff.exe format --check src scripts tests infra experiments --no-cache` | Pass; 176 files already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Pass; no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, original 24 development/16 held-out; software regression only |
| `git -c core.safecrlf=false diff --check` | Pass |

Linux command, existing cached image only, source read-only, no host credentials,
no external network, disposable tmpfs:

```powershell
docker run --rm --pull never --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -m pytest tests/test_human_sts.py tests/test_private_command_runner.py tests/test_identity_contract.py tests/test_identity_coordinator.py tests/test_sts_tunnel.py tests/test_terraform_authentication.py tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_infrastructure.py tests/test_host_preflight.py tests/test_review_source.py -q --basetemp=.cache/pytest-a1a-linux --tb=short
```

Result: **479 passed in 36.48s**, no skips or warnings. Normal local process/Docker
access was used because sandbox access cannot open protected temporary directories
or the Docker pipe; no ACL was relaxed. An initial Docker image inspection was
denied by the sandbox before the isolated run was permitted.

Intermediate evidence: initial 98-case subset passed; expanded first subset had
102 passes/1 failure because its duplicate-JSON assertion expected an internal label
instead of the existing sanitized label, plus two unhandled Windows reset warnings
in the test controller. Corrected the test expectation and treated expected socket
reset as termination, with explicit peer-close/error assertions. An intermediate
full routine run passed 1,481 cases before final re-attestation/summary tests. Final
counts above supersede those development runs; no production safeguard was relaxed.

No PostgreSQL/frontend/browser rerun: no application, schema, migration, route,
frontend or container behavior changed. Current evidence is local/offline, not
hosted-CI or real administrator verification.

## Files, integrity and review boundary

Only three new files in this milestone:

- `infra/aws/human_sts.py` — senderless preparation/re-attestation and fixture results.
- `tests/test_human_sts.py` — 112 synthetic/native-local adversarial cases.
- This handoff.

Preserve all existing tracked/untracked changes. Initial public source inventory
is `.cache/f4-a1a/before.json`. Raw-byte comparison passed: **all 455 original files
unchanged**, exactly these three added files, no missing originals. The private
preservation report and tested-source manifest are in the same ignored directory.
The three PowerShell documentation blocks also parsed with zero errors (no execution).
No prior ZIP or accepted manifest is replaced.
Git diff for this milestone is three added untracked files; source/config/permission
changes to existing files are zero. AGENTS.md remains ignored. No staging/commit/push.

## Exact future authorization boundary, failure and recovery

**This milestone cannot be activated by operator instructions.** A later unit must
source-review a new *single-purpose* executor with a real STS-only connector and
enforced egress/credential behavior. It must not enable the generic runner, introduce
arbitrary commands or turn preparation files into live permits. First external
DNS/TCP/TLS activity by that connector already crosses the live boundary.

Proposed first eventual execution, after that offline blocker is resolved:

1. Owner explicitly authorizes **one** human-admin STS request, exact private identity,
   binary/source/config hashes, regional endpoint, attended window <=30 minutes,
   <=120s process budget plus bounded cleanup, privacy retention and no follow-ups.
2. Reviewed executor rechecks sources, binary, profile, freshness, UTC window and
   egress containment; takes an exclusive durable one-shot attempt claim before
   releasing its owned CLI child. Preparation records alone cannot satisfy this.
3. Start the fixed command once with isolated sources and guarded route; no login,
   renewal, credentials export, retry or alternate identity. Expired/blocked stops.
4. Collect privately, stop/await owned child/guard tasks, verify exact identity and
   finite bounds, persist private outcome and publish only sanitized status. Peer
   closure itself grants neither success nor permission for another request.
5. On uncertainty, preserve the claim/evidence and stop; no automatic fresh attempt
   or follow-up AWS call. Owner decides subsequent reconciliation/authorization.

For offline failures, retain partial preparation/result files and investigate;
never overwrite them or clear a future claim to retry. A fresh local label is still
not AWS authorization. No cache cleanup/login is performed automatically. Unknown
session metadata, native refresh behavior and egress containment remain explicit
live blockers; no new IAM setup or broader authority is proposed. Stop for review.
