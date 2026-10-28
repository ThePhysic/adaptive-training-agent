# F4-03B-R2 — Restricted real Terraform authentication verification

2026-10-25 (America/Los_Angeles). **Attempt stopped safely; real identity
verification is inconclusive. F4-03C/backend/full-plan readiness remains NO-GO.**

Starting HEAD: `641938a22dce1ef5d40d19a6d614fa450ed89de7`.
Only the existing `future-f4-preflight` profile in us-east-1 was selected.
One restricted real-authentication attempt; no automatic retry/fallback.
No apply/destroy/import, remote backend/state/lock operation, resource/image/IAM/
quota change, new login profile, credential export, role escalation, provider
financial authority, real-model call, hosted export, commit or push. No F4-03C work.

## Observed result — not an AWS rejection

| Phase | Observed outcome |
| --- | --- |
| Private identity binding | Existing profile's region/login_session metadata exactly matches the account and IAM-user ARN from the accepted private preflight; no full identifiers published |
| Pinned local CLI | Terraform1.17.0; local cached AWS6.70.0 package selected with the unchanged signed checksum lock |
| Disposable provider-only init | Exit0,3.982s, `-backend=false`; zero outbound connections |
| Disposable validation | Exit0,6.481s; zero outbound connections |
| Identity-only plan attempt | Guard stopped it on the first non-allowlisted CONNECT destination; owned process tree terminated; operator wrapper exit1 |
| External forwarding | **Zero allowed TLS tunnels; zero AWS responses obtained** |
| Authenticated identity/postcondition | **Not obtained**, not a successful or mismatched AWS identity result |
| Local expiration inspection afterward | Standard login-cache file exists; access token was expired at inspection; only a boolean recorded |
| Cleanup | Proxy worker awaited; temporary directory removed; no saved plan/state files or leftover Terraform/provider processes observed |

[Sanitized evidence](evidence/f4-03b-r2-verification.json).
The rejected hostname was **not retained** by the original bounded observer.
That diagnostic omission cannot be repaired retroactively. Expiration makes an
AWS Sign-In refresh attempt plausible, but the precise rejected service/operation
is not proven. The observed failure is **egress_guard_stopped_probe**, not an AWS
AccessDenied, invalid-credentials response or proof of SDK incompatibility.

No approved STS connection opened, so the intended real GetCallerIdentity response
never arrived. Do not turn successful local init/validation or matching profile
metadata into authenticated-principal evidence. R1's source/native-cache finding
stands: generic incompatibility was superseded; this attempt does not reverse it.

The smallest next step is an owner-refreshed login on the same approved identity,
followed by **new explicit authorization** for one restricted identity retry.
Alternatively, separately authorize a precisely scoped Sign-In renewal before
agent-performed refresh. R2 permitted only the minimum STS identity operation;
token renewal was not silently added. No new IAM permission, key or process profile
is justified by this result. No renewal or real retry was performed here.

## Probe boundaries and credential-source evidence

- A disposable local directory contained pinned requirements, provider config,
  **one aws_caller_identity data source, no managed resources and no backend block**.
  No production root or S3 backend was initialized, read, locked or migrated.
- Explicit named-profile selection and exact region; shared config points to the
  existing owner file. Its selected section must contain only region/login_session,
  and match the previously approved IAM-user binding. Role/source-profile/process/
  endpoint substitutions fail before execution. No live profile was created/copied.
- Fresh empty shared-credentials file; inherited AWS credentials, web-identity,
  ECS/IMDS, proxy/endpoint/CA and Terraform log/argument overrides excluded.
  Metadata credentials disabled. The SDK alone consumed the existing login source.
  **Configured source is LoginSession; successful credential retrieval is not proven.**
- Provider startup credential validation/account discovery/region/metadata calls
  were disabled only in this identity fixture. The data source's private lifecycle
  postcondition checks expected account, complete IAM-user ARN and user ID. This
  narrows account operations; it does not change production validation controls.
- SDK configuration uses `max_retries=1` in the tested pinned path and
  AWS_MAX_ATTEMPTS=1. The fixture observed one total attempt. There is no wrapper
  replay; an atomic local one-shot claim is retained after failure.
- An ephemeral loopback CONNECT guard admits only the exact
  `sts.us-east-1.amazonaws.com:443` target, one tunnel,25s/1MiB bounds. Every other
  destination is refused before an upstream socket opens, aborting the plan.
  No inherited proxy or alternate destination is permitted. Normal provider-to-AWS TLS remains
  end-to-end; no CA injection, TLS termination, credential/header/body inspection
  or custom trust exception. The guard has no default sender in routine tests.
- The tunnel observes connection metadata, **not encrypted HTTP operation counts**.
  The operation restriction also relies on the isolated configuration and the
  pinned [data-source implementation](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v6.70.0/internal/service/sts/caller_identity_data_source.go),
  which invokes GetCallerIdentity. The identical offline shape made one local
  identity request. This is not packet-level independent real API-operation evidence.
- Raw Terraform stdout/stderr were captured only in memory and discarded; no
  debug/SDK trace export was enabled. Only classified/numerical results persisted.
  Private expected identifiers lived in the removed temporary HCL. No access key,
  session/refresh token or raw cache content was printed/exported/persisted.
  A later read-only local inspection parsed expiration into a boolean in memory;
  it did not extract credential fields, decode identity tokens or rewrite the cache.

These are experimental guards, not an application auth feature or a deployment
launcher. An ignored one-off operator script supplied the sender only for this
explicitly authorized attempt; routine code/tests do not activate real traffic
from credentials/environment variables alone.

## Offline preparation, faults and regression evidence

Before real execution, Docker network-none used a fully synthetic fresh cache
with the same profile name and pinned binaries. Only the STS transport URL was
substituted in that offline harness; the production-facing contract rejects
noncanonical endpoint substitution.

1. Local fake GetCallerIdentity returned the synthetic expected account/ARN/user
   ID; the exact private-postcondition shape passed with **one request**.
2. Restoring the canonical HTTPS destination with a senderless loopback guard
   produced **one refused CONNECT, zero forwarding, plan exit1**, proving the SDK
   uses the controlled route and does not retry under the final settings.

An initial `max_retries=0` setting did not disable retries in this pinned path:
the offline denied-route experiment observed9 refused attempts before timeout.
No AWS request occurred. Using1 produced one total attempt, consistent with the
pinned [AWS base library's RetryMaxAttempts handling](https://raw.githubusercontent.com/hashicorp/aws-sdk-go-base/v2.0.0-beta.76/aws_config.go).
This correction is only in the temporary identity fixture, not approved application
retry/repair/request limits. The real run began only after this control passed.

Following the failed real attempt, an additional **offline-only** test added a
known regional Sign-In hostname classification while preserving denial. This does
not identify the unrecorded destination from the earlier attempt or authorize
Sign-In. No second real probe was used to fill the diagnostic gap.

| Check | Observed result |
| --- | --- |
| Final shared offline sequence | **20/20 commands exit0;1,095 routine Python passed**,257 integration deselected; zero failures/errors/skips |
| New guard cases | **18** cases, included above; synthetic profile binding, disallowed config/env sources, route denial, no default sender/second tunnel and real loopback forwarding |
| Focused auth/storage/security/release regressions | **115 passed**,6.61s; overlaps the routine total |
| Existing Terraform format/static/validation/mock suite | Three roots valid; **8/8 mock plans passed**, no account credentials/backend access |
| Frontend/contracts |85 frontend tests; type/format/generated-contract checks and build passed |
| Frozen evaluation | **24/24 development +16/16 held-out**;150 existing model-suite dispositions unchanged |
| Formatting/integrity | Ruff check and148-file format check pass; protected app/HCL/storage/network/SSM/locks/CI/data/contracts unchanged |

Full PostgreSQL/browser/hosted-release suites were not rerun for these isolated
guards. Existing accepted evidence remains historical. No changes to application
ownership, approvals, budgets, model/telemetry gates or immutable business records.

## Exact commands and files

Executed from repository root:

```powershell
.venv/Scripts/python.exe .cache/f4-03b-r2/run_offline.py
.venv/Scripts/python.exe .cache/f4-03b-r2/run_identity.py
.venv/Scripts/python.exe .cache/f4-03b-r2/run_checks.py
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/python.exe -m pytest tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_terraform_authentication.py tests/test_infrastructure.py tests/test_host_preflight.py tests/test_release.py -q --basetemp=.cache/pytest-r2-final
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws --no-cache
git diff --check
```

The real operator script issued exactly these commands in its disposable local
directory, with raw output captured in memory:

```text
ROOT/.tools/terraform/terraform.exe version -json
ROOT/.tools/terraform/terraform.exe init -backend=false -input=false -lockfile=readonly
ROOT/.tools/terraform/terraform.exe validate -json
ROOT/.tools/terraform/terraform.exe plan -input=false -no-color
```

First three exits0; final command was guard-terminated. Its native exit code was
not retained; the operator wrapper exited1. The published record does not invent
a numeric Terraform exit status. No `-out`, lock-object, apply or remote backend
command. Init used only the existing local unpacked provider mirror and readonly
lock, with no direct-registry fallback or new dependency installation.

The offline native invocation uses the same cached Linux CLI/provider mirror and
release image/network-none/tmpfs flags from the infrastructure README, owned
container `fata-f403br2-offline`, and ignored `offline_identity.py`. It uses a
synthetic cache, no real `.aws` mount and no sender. `run_checks.py` invokes the
existing `scripts/check.py`; commands/durations are in the evidence JSON.
The ignored real operator script's SHA-256 is recorded there for local review;
its existing one-shot marker must not be removed to force an unapproved retry.

Changed tracked files: `infra/aws/fixtures/{identity_contract,sts_tunnel}.py`,
`tests/{test_identity_contract,test_sts_tunnel}.py`, infrastructure README,
checklist23, this handoff and `evidence/f4-03b-r2-verification.json`.
No production Terraform, credential/profile file, IAM policy, migration, dependency,
application/CI implementation or historical report changed. No commits/pushes.

## MFA and remaining readiness

R2 authorized STS identity only. No IAM/MFA/quota/organization read was added.
F4-03B's zero-device observation is historical; current registration/session MFA
is **unverified**, and even a successful GetCallerIdentity would not prove MFA.
Do not label a renewed/expired token, matching profile metadata or R1 fake output
as MFA evidence. Owner-reviewed device/session evidence remains a separate gate.

**NO-GO for further real authentication, S3 backend verification, infrastructure
plan or deployment without separate authorization.** Owner actions: fresh approved
source session and a newly scoped identity retry; then provider/backend/refresh
verification as explicitly authorized, MFA/effective-permission/quota evidence,
concrete AMI/digests/account/AZ/window, state/lock permissions, financial/privacy
and recovery/teardown decisions. No monetary grant or resource was created, and
no paid billing query was made. Stop after R2 for review.
