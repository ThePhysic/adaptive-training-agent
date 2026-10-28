# F4-A1a — Native CLI containment and execution safety

2026-10-26. **Offline review and local fence implementation. Live STS: NO-GO.**

## Outcome and scope

Preserved the accepted preparation mechanism and both disabled live executors.
Added a preparation-bound, exclusive local attempt fence and synthetic tests,
including process termination/restart. Identified the installed Windows CLI and
ran **only its non-service `--version` command** with isolated empty configuration.

**The two live blockers are not resolved.** No enforced Windows egress boundary was
established within the current authorization. Native credential/protocol workloads
were therefore not executed. This is a deliberate stop at the requested security
boundary, not a passing native compatibility result. No proxy-only approximation
or alternative authentication mechanism was activated.

No real AWS request, login, token inspection/export, IAM/state/infrastructure
operation, dependency installation, machine security/network change, financial
authority, provider call, telemetry export, commit or push occurred.

## Initial inspection and files

Read AGENTS.md, runbook26, accepted A1a handoff, human_sts.py, private_command_runner.py,
identity contracts/coordinator, sts_tunnel.py, process ownership/ACL helpers and
related tests. Preserved the initial dirty worktree. Historical documents are
unchanged; no account setup was repeated.

Files changed in this milestone:

- `infra/aws/human_sts.py`: add only `claim_offline_attempt()`; preserve preparation,
  fixture scoring, fixed command, environment rules and unconditional live denial.
- `tests/test_human_sts_attempt.py`: 17 new synthetic/local process cases.
- This handoff.

Milestone delta is one changed preexisting untracked file plus two new files;
ordinary Git diff does not display these untracked files. The existing
generic runner, tunnel, Terraform, application, credentials and dependency locks
are unchanged. No review archive is generated or prior manifest overwritten.

## Installed CLI and measured metadata

Observed installation: `<LOCALAPPDATA>/Programs/Amazon/AWSCLIV2/aws.exe`, not on this
tool shell's PATH. The standard Program Files candidate and WindowsSandbox.exe
were absent. No real AWS config/profile/login-cache path was opened.

| Measurement | Observed result |
| --- | --- |
| Native command | Pinned absolute `aws.exe --version`, no service/action arguments |
| Result | Completed, native exit 0; AWS CLI **2.38.5**, bundled Python **3.14.8** |
| Binary size | 9,480,712 bytes |
| SHA-256 before/after | `a7396ba231e73fa9f3126486154301d15a1128780bc8cf27a7823658279a5b8d`, unchanged |
| Environment | Dedicated ignored HOME/config/empty credentials/cache/temp; OS basics only; no configured login_session; metrics off; no inherited credentials/proxies/CA settings |
| Ownership/bounds | Existing Job Object capture, 20s timeout, 8KiB stdout/4KiB stderr, owned cleanup |
| Privacy | Public report keeps only version, classification and public software hash; raw captured output cleared |

The command was executed once successfully, not an identity probe. An earlier
attempt failed while creating a protected local directory, **before** launching
the CLI. Retried with normal user process access, not administrator elevation.
No protocol test was attempted as a fallback.

Metadata artifacts: `.cache/f4-a1a-native/native-version.json` and
`installed-assets.json`. The latter hashes seven installed public software assets:
aws.exe, python314.dll, _awscrt.pyd, STS/Sign-In service models and endpoint rules.
For example STS service-model SHA-256 is
`d97a08aa49223dee070009624c1d70f5b6af6ccc43220cc30ff566d5f02f3c0b`.
These are installation-asset hashes, not extracted Python-source hashes or proof
that the bundle matches an independently built upstream release.

### Reproducing the metadata-only command

The installed path came from the fixed local Programs candidate, not a profile.
The executed native argv was exactly `[absolute_cli_path, '--version']`. It used
`human_sts.environment(OS_basics, private_root, 'http://127.0.0.1:9')`, with fresh
empty home/login-cache/tmp directories, empty-credentials, and selected-config
containing only the human profile header and region. Captured through:

```python
capture = human_sts.runner.capture_owned(
    [str(cli), "--version"],
    cwd=root,
    env=env,
    timeout=20,
    stdout_limit=8192,
    stderr_limit=4096,
)
```

The local audit checked a bounded version-string pattern, hashed the binary again,
persisted only finite metadata and cleared the capture. The deny-proxy setting is
defense in depth for this non-service command, **not containment evidence**.
AWS's [global-option reference](https://docs.aws.amazon.com/cli/latest/reference/)
defines --version; [version-tagged driver source](https://github.com/aws/aws-cli/blob/2.38.5/awscli/clidriver.py)
shows version handling before service invocation. No packet-level audit or native
credential-provider invocation was performed.

## Credential and refresh investigation

Official sources checked on 2026-10-26. These findings are **version-tagged source review
and documentation**, not observed native credential behavior. The bundled Python
code was not extracted or proven byte-identical to upstream.

[AWS CLI 2.38.5 credential resolver](https://github.com/aws/aws-cli/blob/2.38.5/awscli/botocore/credentials.py)
shows explicit profile selection affects environment-provider handling; profile
providers still include shared files, login and process providers, with legacy,
container and instance-metadata providers later in the chain. Login cache errors
raise rather than proving safe fallback behavior for every configuration.

Its LoginProvider constructs refreshable credentials. The fetcher can reload cached
data and invoke Sign-In CreateOAuth2Token. A five-minute internal threshold and separate
advisory/mandatory refresh handling mean an expiry timestamp is not a no-refresh
switch. Key loading also precedes part of the freshness handling. Invalid fake
keys could mask network refresh in a naive experiment. None was submitted here.

[AWS login documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)
documents automatic renewal. [Retry configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html)
documents total attempt accounting. Neither supplies a documented no-login-refresh
control. `AWS_MAX_ATTEMPTS=1` is not a prohibition on credential renewal or evidence
of exactly one HTTP operation. Preserve the selected-only config, empty shared and
legacy files, isolated cache, no credential_process/role/SSO fallback and IMDS-off
rules; do not substitute exported credentials or static keys.

The accepted seven-minute freshness metadata check remains unchanged. It is an attestation,
not native proof; clock error, preparation delay and refresh thresholds still need
controlled testing. Unknown/expired authentication must stop. Existing MFA setup
is accepted; GetCallerIdentity does not prove request MFA context.

## Windows containment assessment and explicit stop

| Mechanism | Assessment within this authorization |
| --- | --- |
| Proxy/environment and fixed CLI argv | Useful configuration checks; direct Winsock/CRT calls, DNS, IPv6, children or alternate transports are not OS-blocked merely by these settings. Insufficient |
| Existing Windows Job Object | Owns/terminates descendants; not a network policy. Existing tests prove cleanup, not egress denial |
| Restricted token/low integrity alone | Do not treat filesystem/integrity restrictions as an outbound socket allowlist |
| AppContainer | Genuine capability isolation candidate, but no-network capabilities also constrain needed local networking; packaged loopback is blocked by default. Profile/ACL/capability/broker compatibility needs review and testing; none was registered or exempted here |
| WFP or Windows Firewall | Could support scoped network enforcement, but involves host security objects/access rights. No filters, rules, privileges or ACL delegation were requested or changed |
| Windows Sandbox, Networking=Disable | Preferred next **offline native-test environment** if owner approves enabling the missing feature. Local fake services would run inside the guest; host credentials must never be mapped. This is not a ready live route |
| Existing Docker Desktop Linux, --network none | Enforced external-network isolation for the Linux regression population. It cannot run/prove the installed Windows binary's behavior. No Linux AWS CLI installation was authorized/performed |

Microsoft references: [AppContainer isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation),
[profile creation and its per-user folders/registry](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile),
[loopback restrictions](https://learn.microsoft.com/en-us/windows/uwp/communication/interprocess-communication),
[WFP access rights](https://learn.microsoft.com/en-us/windows/win32/fwp/access-control),
[Sandbox networking configuration](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file),
[Sandbox installation prerequisites](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install).

**No safe Windows network boundary was established here.** This is not a claim
that every unprivileged Windows isolation design is impossible. The investigated
options require additional software/feature availability, persistent configuration
or an unimplemented reviewed capability/broker boundary. Stop rather than launching
credential/protocol tests on the host under proxy-only protection.

If chosen separately, the owner would enable supported Windows Sandbox/virtualization
and accept possible reboot/resource requirements. A later offline unit would review
a network-disabled configuration, clipboard/audio/printer sharing disabled, only
synthetic/read-only mappings, local fake TLS with a scoped test CA, and owned guest
cleanup/results. No feature-enable command is executed or implied by this proposal.
Do not enroll Insider builds, install drivers, use an admin prompt, change global
firewall rules or add loopback exemptions automatically.

## Native protocol evidence and proposed experiment

| Required observation | This milestone's evidence |
| --- | --- |
| Installed executable/version | Native --version and binary/asset hashes only |
| Credential selection, profiles, environment precedence, cache lookup, missing/expired sessions, Sign-In refresh, shared/process/container/IMDS fallback | Source review and prior synthetic guard tests; **native tests not run** |
| Native endpoint override, proxy/bypass, redirects, retries, multiple HTTP requests, TLS failures, signing, response handling and CLI cancellation | **Not measured**; blocked pending containment |
| Exact identity/schema/output bounds | Existing 112 synthetic A1a cases; not native CLI/service evidence |
| Direct DNS/IPv4/IPv6/link-local/child egress rejection | Not established for Windows CLI. Linux namespace regression results do not substitute |
| TLS/client security regression | Existing loopback TLS tests use the application's test transport, not AWS CLI; never described as native STS proof |
| Local attempt fence, concurrency, partial writes, cancellation and restart | New 17 synthetic/local-process cases |

A later authorized **offline** native experiment should use the existing binary
bundle read-only in an enforced network-disabled Windows guest. Start local STS,
Sign-In, metadata/container and deny-proxy fixtures inside that guest, use synthetic
cache keys/tokens only and scoped test certificates; never --no-verify-ssl or a
machine trust-store change. Use loopback endpoint overrides only in the test harness,
never in the future live command constructor. Test the 15 requested native behavior
categories and all negative cases from the request; label every actual observation.
Do not treat a malformed synthetic DPoP key failure as proof refresh was blocked.
That test harness/guest is not installed or implemented by this task.

Protocol stages require distinct evidence: connector claim = permission reserved,
TCP success = connected, TLS success = authenticated channel, fake server inspection
= signed Action/Version observed, response parsing = strict output observed.
None alone proves an actual AWS request. A blind CONNECT tunnel sees neither action
nor HTTP count inside TLS. A second request can reuse one connection; a TLS failure
does not prove a request was sent; cancellation does not prove it was not.

Before live approval, decide whether an attested, immutable native command plus
measured no-retry behavior is an accepted trust boundary for action/count enforcement.
Do not relabel that as packet-level enforcement. If stronger inspection is required,
request separate architecture review: TLS termination exposes signed headers/session
tokens and needs explicit trust/privacy changes; an in-client gate changes the
attested CLI runtime. Neither nor a custom signer is introduced here. The STS tunnel
limit is not a one-HTTP-request guarantee.

## Local single-attempt component

`claim_offline_attempt(output, now, abort)` first verifies the accepted private
preparation: identity/profile/endpoint/UTC window, binary, source hashes, command,
config and empty runtime directories. Then exclusively creates attempt.claim.json
with fsync through the existing private writer; POSIX also fsyncs its parent directory.
It binds the preparation hash, fixed profile/operation and conservative possibly_started
state. No identity values or raw results enter the claim; the hash remains private.

Only successful return permits a **test** to release its owned synthetic child.
No process-release callback or live CLI entry point is added. Concurrent, duplicated,
partial/corrupt-existing and post-restart attempts fail closed. File/final-flush
errors never remove the record. Cancellation before a claim creates no record;
cancellation after a claim keeps it. Even completed synthetic work retains the
fence. Generic/live execution still rejects it unconditionally.

This is not financial authority or AWS idempotency. Protection is per approved
directory; an owner creating a different directory is not prevented globally. A
future executor must bind an independently authorized attempt identifier, protect
its directory from concurrency/manual replacement, recheck time/identity immediately
before release and reject all ambiguous holds. No CLI flag consumes this offline
record as live authority.

Observed restart evidence includes a child that fsyncs the claim and uses
`os._exit(23)`, followed by a newly launched process that cannot reclaim it. That
proves local **process-crash/restart** behavior, not sudden power-loss, disk-controller
durability, hostile-owner resistance or network delivery. Those limits are explicit.

## Tests, commands and results

Project Python 3.14.9/Ruff 0.17.2; cached Terraform 1.17.0/AWS 6.70.0. No installation.

Initial full routine command:
`.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/f4-a1a-native/pytest-routine --junitxml=.cache/f4-a1a-native/routine.xml --tb=short`
returned **1,506 passed/257 integration deselected in 217.66s**. It preceded the added
abrupt-process-exit test. Final results are recorded below after that addition.

| Final command | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/f4-a1a-native/pytest-final --junitxml=.cache/f4-a1a-native/routine-final.xml --tb=short` | **1,507 passed, 257 integration deselected in 231.84s**, no warnings; includes 17 new fence tests and all 112 accepted A1a tests |
| `.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe` | fmt passes; three roots validate; **21 mocked plan cases passed** (5 deployment/14 bootstrap/2 module); no init/account-connected plan |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **174 Python files** parse with native and 3.13 grammar |
| `.venv/Scripts/ruff.exe check src scripts tests infra experiments --no-cache` | Pass |
| `.venv/Scripts/ruff.exe format --check src scripts tests infra experiments --no-cache` | Pass; 177 files already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Pass; no generated-contract drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, original 24 development/16 held-out; software regression only |
| `git -c core.safecrlf=false diff --check` | Pass |
| `.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a1a-native/tested-source-final.json` followed by `verify --manifest .cache/f4-a1a-native/tested-source-final.json` with the same script | Pass; 460 public files/174 Python files, snapshot unchanged. A complete manifest is refreshed after final documentation edits |

Linux command, with the cached image, no pulls, no credential mounts, read-only
source, network disabled and disposable cache:

```powershell
docker run --rm --pull never --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -m pytest tests/test_human_sts.py tests/test_human_sts_attempt.py tests/test_private_command_runner.py tests/test_identity_contract.py tests/test_identity_coordinator.py tests/test_sts_tunnel.py tests/test_terraform_authentication.py tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_infrastructure.py tests/test_host_preflight.py tests/test_review_source.py tests/test_provider_tls.py -q --basetemp=.cache/pytest-a1a-native-final-linux --tb=short
```

**508 passed in 37.02s**, no skips/warnings. The initial selection passed 507 cases
before the abrupt-process-exit case was added. These Linux tests do not contain
the installed Windows CLI or establish Windows egress enforcement.

Tests used normal user process/Docker access because sandbox ACL restrictions
prevented private-directory creation. No elevation to Windows administrator or
machine-security change occurred. No native credential test was attempted/retried.

The process/socket/TLS/ACL/claim cases are the applicable local integration checks.
The 257 opt-in database/browser integration cases were not run: no database, web,
application or migration changes. No hosted CI result or PostgreSQL regression
result is claimed by this unit. No new native Windows protocol suite is marked
passing or silently skipped; it remains unexecuted and blocks live readiness.

Initial inventory: `.cache/f4-a1a-native/before.json`. The incremental patch is
`human_sts.incremental.patch` in the same ignored directory: **34 added lines,
zero deleted lines** in human_sts.py. Removing exactly that new function reproduces
the original file SHA-256, confirming no incidental edit to accepted behavior.
Final preservation and whole-source manifests are retained there; no ZIP is made.
Raw-byte comparison passed: of 458 preexisting public files, only human_sts.py
changed; the other **457 are byte-identical**. Exactly the two new files listed
above were added. No existing user changes were reverted, reformatted or staged.

## Future owner decisions and GO/NO-GO

**NO-GO for the first STS request.** Native refresh/fallback, enforced Windows egress
and exact HTTP action/count guarantees are unverified. The next recommended owner
decision is the isolated **offline** Windows test environment, not AWS access.
No new IAM identity, permission or login is required in this task.

After that separately approved work, a future live proposal must name the one
fixed GetCallerIdentity command/profile/regional endpoint, private Account/Arn/UserId,
fresh source/binary/config hashes, supported authentication, containment attestation,
one-shot identifier, attended UTC window, 120s execution plus bounded cleanup,
output/retention rules, no refresh/retry/follow-ups and stop conditions. Owner must
review/authorize both the new narrow executor source and the one actual request.
Current execute_live() and generic execute_account() must not be toggled on.

On unknown authentication, rejected route, unexpected operation/HTTP count, TLS
failure, output mismatch, timeout, cancellation or interrupted/ambiguous delivery:
stop and await owned tasks, retain private claim/evidence, discard transient buffers,
report only finite classifications and require a new owner decision. Do not clear
a claim, refresh credentials, widen endpoints, retry or issue reconciliation calls
automatically. No real invocation or account-changing operation follows this report.
