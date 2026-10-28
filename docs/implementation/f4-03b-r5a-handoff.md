# F4-03B-R5A — State backend bootstrap preparation and real-plan readiness

2026-10-25 (America/Los_Angeles). **Offline scope complete. R5B creation,
grants, actual backend/lock operations and real infrastructure plan are NO-GO
until separately authorized.** Starting HEAD:
`991824bdb8351234a2d9ef8b99ac01542264d1ec`.

[R5B authorization/execution proposal](../planning/25-f4-03b-r5b-state-bootstrap-and-plan-proposal.md)
and [updated readiness checklist](../planning/23-f4-03-cloud-execution-readiness.md).
No additional AWS account call was needed; account findings came from the owner.
No actual S3 initialization, state write/lock, resource creation, IAM/profile/cache
change, credential export, apply/destroy, upgrade, spending, live model/telemetry,
commit/push or later work unit. Public documentation reads are not account evidence.

## Account reconciliation

| Owner finding | Assessment |
| --- | --- |
| us-east-1; EC2 standard quota 5 vCPUs | Accepted owner evidence; current all-project standard-vCPU usage/pending allocations unknown. Need two spare vCPUs before later t3.small launch |
| VPC quota 5, one VPC | Four remaining slots at observation; sufficient for the proposed one VPC, subject to launch-time usage/CIDR check |
| Preflight registered passkey; no IAM boundary | Registration and own-user boundary gaps resolved. Future operator/session MFA and effective permissions remain separate |
| Appears standalone | Provisional owner assessment; final attestation needed. No organization creation/join or IAM expansion |
| No S3 buckets | State backend must be deliberately bootstrapped under a separately authorized writer; initialization does not create the bucket |
| Free plan, $100 credits | Accepted owner finding; no spend authorization or promise that every API/AMI is available. Expiry/credit eligibility and gross consumption need owner monitoring |
| R3 provider identity | Accepted exact private postconditions/native exit 0. Coordinator error remains separate; no real rerun performed |

Public offers support S3, eligible t3.small/gp3, ECR and SSM under Free-plan/credit
terms; no paid-plan prerequisite identified for the proposed basic backend.
Feature-level effective account permission is not proven by documentation or the
local fake. Custom AMI eligibility remains unresolved. Sources, limitations,
upgrade triggers and exact permission scopes are in proposal 25. No quota increase,
additional credit claim or Free-to-Paid upgrade is proposed as an automatic action.

## Audit and implementation decisions

The existing `state-bootstrap` root already creates the protected state bucket
through `modules/protected-bucket`; deployment already declares an S3 backend.
Recovery is an operator procedure, not a missing Terraform root. **No duplicate
stack/resource or new service was added.** The same six bootstrap resources retain
versioning, AES256 SSE-S3, BucketOwnerEnforced, all public blocks, HTTPS-only deny,
prevent_destroy, force_destroy=false and no automatic state expiry.

- Native S3 lockfiles retained; no DynamoDB/custom KMS. Exact state/lock keys
  remain `ec2-demo/terraform.tfstate[.tflock]`, default workspace only. Proposed
  ListBucket is now limited to the actually observed `env:/` discovery prefix.
- Separate non-attached bootstrap, first-plan and later state-writer policy
  outputs. Bootstrap is bucket-administration-only; first plan can read state and
  operate only its lock; later writer additionally needs exact state PutObject.
  No state/version/bucket deletion or wildcard service action in those proposals.
- Every statement is bound to exact same-account principal, region, TLS and an
  explicit start-inclusive/end-exclusive UTC window <=2h. Writers reject the
  preflight user name/path/case variants. These are Allow conditions, not an IAM
  permissions boundary or protection against another broad attached policy.
- Pinned source review found tag-on-create needs `s3:TagResource`. The proposal
  includes it and the pinned legacy PutBucketTagging fallback, plus explicit
  ancillary reads for unset legacy features. Seven possible distinct write API
  types/eight write IAM actions; not a claim of seven actual invocations. SDK
  max_retries=1 does not suppress provider resource-level compatibility retries
  or consistency waits. No tagging/read permission has actually been granted.
- Bootstrap policy/first-plan policy/full writer/backend outputs are sensitive;
  no ordinary Terraform output reveals private names. State/plan/config still
  contain private operational metadata and require encrypted storage/ACLs.
- `state_bundle.py` prepares local inputs only: bounded strict six-field JSON,
  private-cache-only paths, fixed safe label, exact-account writers, <=2h window,
  READY last. Same content is a no-op; changed, partial, oversized, unknown-field
  and public-path input fails without overwrite/deletion. It cannot execute a
  command or attach/activate permission. Windows ACL review is explicit; chmod
  is not claimed as a Windows confidentiality guarantee.
- `.aws/` and plan-JSON ignore rules supplement existing ignored state, plans,
  tfvars/backend/cache. Existing Docker context allowlist excludes all private
  artifacts. Review archives must use tracked sources, not zip the working tree;
  ignore rules do not prevent intentional force-add or arbitrary archive creation.

No active cloud launcher was shipped. Proposal 25 specifies the operator
capture/deadline/cleanup review, exact commands, saved-plan approval checkpoints,
partial apply reconciliation, immutable input/source binding, state version
recovery and separately approved deletion. The R4 identity collector is not
repurposed as a full plan/apply launcher. All actual source/authentication and
write decisions remain owner-controlled before R5B.

## Pinned Terraform-core authentication and lock experiment

`fixtures/backend_probe.py --native-offline` uses the **actual cached Terraform
1.17.0 core**, no AWS provider/plugin or application code, fixed synthetic
login-cache/profile, poisoned synthetic default credentials, fake HOME and empty
real credential chain. It invokes no AWS CLI, real cache or credential export.
Endpoints are fixed owned loopback HTTP services; a separate senderless proxy
denies any external route. No refresh/Sign-In endpoint is allowed. Temporary
files are removed and servers/processes awaited. Native output stays private in
memory and credential-canary checks cover each invocation; public results contain
only case labels, exit codes and finite operation counts.

| Native synthetic case | Exact observed disposition |
| --- | --- |
| Fresh cache / existing synthetic state | Init 0, repeat init 0, empty fixture plan 0; six local identity reads, six state reads, five workspace lists, one each lock PUT/GET/DELETE |
| Missing cache | Init 1; zero identity/S3 calls; no default fallback |
| Wrong allowed account | Init 1; two synthetic identity reads, zero S3 calls |
| S3 read denied | Init 1; two identity reads, two workspace lists, one state read. Core can treat default-prefix listing AccessDenied as a warning; the denied state read remains fatal |
| Missing selected profile | Init 1; zero identity/S3 calls; poisoned default never selected |
| Persistent S3 500 | Init 1; two identity reads, exactly one failed workspace-list attempt; no SDK transport retry with selected max_retries=1 |
| Absent synthetic state | Clean init and empty plan exit 0; no state PUT permitted; plan performs its lock lifecycle and leaves state absent |
| Already held synthetic lock | Init 0, plan 1 at lock-timeout=0s; conditional PUT fails, existing lock retained, no DELETE/unlock/replay |

**8/8 expected cases**, zero external proxy attempts/forwarding and zero real AWS
calls. The fake enforces exact prefix/key/method/credential canaries and conditional
lock creation; **it is not an AWS IAM/SigV4 cryptographic evaluator**. It uses HTTP,
not AWS TLS, and Windows proxy isolation is not a kernel network-none namespace.
Docker's Linux engine pipe was unavailable; no engine/service change was made.
Actual AWS core authentication, retention, policy effectiveness, Free-plan behavior,
future writer identity, renewal and real cancellation/recovery remain unverified.

The absent-state experiment corrected a planning assumption: in this pinned clean
fixture both init and speculative plan did **not** persist empty state; the plan
still wrote/deleted a lock. Therefore first-plan authority excludes state PutObject.
This observation does not ratify migration/other-workspace modes or guarantee a
different real infrastructure graph will need no additional operations: an
unexpected need must fail and return for review. Historical R4 reports are retained.

## Commands and checks

Windows environment: Python **3.14.9**, Node **24.22.1**, npm **11.19.1**, Ruff
**0.17.2**, cached Terraform **1.17.0**, provider **6.70.0**. Locks unchanged;
no installation or AWS credential requirement.

```powershell
.tools/terraform/terraform.exe fmt -recursive infra/aws
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe > .cache/f4-03b-r5a/terraform-final.json
.venv/Scripts/python.exe infra/aws/fixtures/backend_probe.py --native-offline > .cache/f4-03b-r5a/backend-native.json
.venv/Scripts/python.exe .cache/f4-03b-r5a/run_checks.py
.venv/Scripts/python.exe -m pytest tests/test_state_backend.py tests/test_identity_coordinator.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_terraform_authentication.py tests/test_infrastructure.py tests/test_host_preflight.py tests/test_release.py -q --basetemp=.cache/pytest-r5a-verified
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws --no-cache
git diff --check
git check-ignore AGENTS.md
```

The ignored check wrapper runs `scripts/check.py` with inherited AWS/TF/proxy
overrides removed, output redirected to ignored local checks.log. Infrastructure
checks execute only fmt, validate and explicit mock-provider plan tests; they
do not initialize any backend. The separate native experiment initializes only
its fake local backend and plans no managed resources. No account-connected plan
or repeated real identity probe is hidden in these commands.

| AWS-preparation validation before the supplemental CI correction | Observed result |
| --- | --- |
| Shared sequence | **20/20 commands exit 0**; **1,154 routine Python passed**, 37.29s; zero failures/errors/skips, 257 integration deselected |
| Focused auth/security/release/storage/private-input tests | **174 passed**, 8.35s; overlapping routine total, including **28 new cases** |
| Terraform fmt/static/validate/mock plans | Three roots valid, **14/14** pass: deployment 5, bootstrap 7, bucket module 2; zero failures/errors/skips |
| Native core loopback experiment | **8/8 expected dispositions**; finite counters above; no external forwarding or real AWS requests |
| Frontend/contracts | **85/85** frontend tests; TypeScript, formatting, contract generation/drift, Responses assets, build all pass |
| Frozen evaluations | **24/24 development + 16/16 held-out** baseline; 50-case × 3 offline variant handling dispositions unchanged, including expected hard failures; no real-model quality evidence |
| Formatting/integrity | Ruff passes; **153 files** formatted; diff check passes; AGENTS.md ignored; protected application/provider/host/release/lock/data sources unchanged |

[Sanitized commands and evidence](evidence/f4-03b-r5a-verification.json) preserve
exact relative commands, durations, denominators and native case counters. Native
entrypoints are deliberately opt-in and not run as part of routine pytest; their
actual invocation/result is recorded separately. Real-account or hosted behavior
is not inferred from mock plans, structural IAM assertions or local fake responses.

Development corrections: Git stdin text translation on Windows added CR bytes
to ignore-test paths; NUL-delimited binary input/output fixes that without changing
Git safety rules. A Terraform assertion initially compared JSON tuple/list types;
explicit list normalization fixed the test, not policy semantics. Absent-state
fake assertions initially expected state writes; measured behavior corrected that
assumption and narrowed the proposed plan grant. No actual cloud error or account
result was invented from these offline failures.

## Changed files and remaining approvals

- `.gitignore`; `infra/aws/deployment/backend.hcl.example`.
- `infra/aws/state-bootstrap/main.tf`, new `authority.tf`, existing mock test file.
- New `infra/aws/state_bundle.py`, `fixtures/backend_probe.py`,
  `tests/test_state_backend.py`.
- Infrastructure README, checklist 23, new proposal 25, this handoff and sanitized
  verification evidence under `docs/implementation/evidence/`.

Application runtime, frontend product code, migrations, locks, release/host/storage/network/SSM controls,
identity contracts/coordinator/tunnel, historical reports and frozen corpus remain
unchanged. The AWS-only checks above deselected 257 integration tests; the separately
authorized browser correction below subsequently ran the full suite on Windows/Linux.
F1/F2/F3 safeguards, provider count/financial barriers and offline Langfuse remain.

## Supplemental hosted-CI browser correction — separate from AWS preparation

The owner additionally authorized investigation of hosted run #24 (title
`docs: finalize AWS account evidence and Terraform plan readiness`): 256 integration
passes and one browser failure. This observation is owner-supplied; no hosted run
was triggered, committed or pushed during this correction.

**Confirmed stage:** original `browser-smoke.mjs:67` waits for the first nonempty
line of `DevToolsActivePort`, throwing at original line 65. No page navigation,
frontend asset load or application API workflow has started there. Uvicorn has
already reported started. The original wait swallows all file-read errors,
discards all browser stderr, and does not observe early process exit.
It therefore misreports an exited browser as a generic readiness timeout.

**Hosted launch root cause remains unconfirmed.** Original Chrome stderr cannot
be recovered retrospectively. The original source/test passed on non-root Linux,
so no file/scheduling race, sandbox failure or resource shortage is claimed as the
confirmed hosted cause. The correction repairs the confirmed observer weakness;
it cannot make a broken Chrome installation pass or prove the hosted issue closed.

The minimal behavior change is a documented Chrome ready-signal wait, with early
exit/spawn failure handling, instead of blind file polling. See
[Chrome's headless debugging guidance](https://developer.chrome.com/docs/automation-and-testing/headless)
and [nondefault profile requirement](https://developer.chrome.com/blog/remote-debugging-port),
reviewed 2026-10-25. The existing unique profile already meets the latter; it was
not replaced with a personal/default profile. The initial **15s** startup bound
is unchanged; no startup replay, arbitrary sleep increase or `--no-sandbox` flag.

Changed files in this independent correction:

- `web/scripts/browser-smoke.mjs`: consume the ready event, validate loopback CDP
  destination, label workflow stages, bound CDP operations, collect classified
  runtime/console/network/status events, and await the owned browser on cleanup.
  A 32s harness deadline reserves diagnostics/cleanup time within the existing
  40s Python subprocess limit. Production request deadlines are unchanged.
- New `web/scripts/browser-support.mjs` and `.d.mts`: <=4 KiB stderr line, <=64 KiB
  classification input, <=32 diagnostic events; finite stages/error categories,
  route classes/status/exit numbers and bounded timings only. No raw stderr,
  console arguments, page text, request/response bodies, headers, credentials,
  principal/plan IDs, URLs/query strings or CDP session identifiers in reports.
- `tests/test_browser_ui.py`: verify actual loopback `/health` before launch and
  report server-start/task/status booleans/numbers on failure. Preserve every
  original workflow, SQL cardinality, ownership, immutable snapshot, explicit
  retry and mobile/desktop assertion; original optional-browser marker unchanged.
- New `web/tests/browser-support.test.ts`: **11** deterministic cases using
  explicit events/fake timers for split readiness, early exit, spawn failure,
  missing/malformed/nonlocal/oversized signals, bounded canary-safe diagnostics,
  status-only server reads and forbidden external diagnostic destinations.
- New `tests/test_browser_harness.py`: real-process negative test launches Python
  as a deliberately exiting stand-in (not a positive browser test). It proves
  immediate `browser_exited_before_ready`, launch stage/exit 2, live local server
  status and no raw stderr/private-body leakage. No wall-clock speed assertion.
- This handoff, readiness checklist, separate sanitized
  [CI evidence](evidence/f4-03b-r5a-ci-verification.json), and new synthetic
  `f4-03b-r5a-ci-{desktop,mobile,mobile-error}.png` evidence. Historical screenshots
  and the original AWS-phase verification JSON are not overwritten.

The Save → Generate → Review → Revise → lost approval response → identical-key
retry → durable readback/history → completion retries → preference change/immutable
snapshot → owner switch/error/recovery workflow remains intact. Fetch interception
still rejects nonlocal page requests. No API/security/application/CI-workflow or
dependency-lock changes; no test skip, suppressed failure, fabricated approval or
weakened sandbox. The stand-in is used only for the negative launch test.

### Measured reproduction and final checks

| Check | Observed outcome |
| --- | --- |
| Original script/test, isolated Linux source copy | **1/1 passed**, 30.58s; original hosted failure not reproduced |
| Corrected Windows focused installed-Chrome workflow | **1/1 passed**, 5.06s |
| Corrected Linux focused repeats, direct Chrome binary | **5/5 passed** |
| Corrected Linux focused repeats, packaged Google launcher | **5/5 passed** |
| Final-source Linux workflow after diagnostic route-label correction | **1/1 passed**, 14.11s |
| Windows full integration including installed browser | **257/257 passed**, 142.66s; zero failures/errors/skips |
| Linux full integration including packaged browser | **257/257 passed**, 180.25s; zero failures/errors/skips |
| Final shared offline sequence | **20/20 commands exit 0; 1,155 routine Python passed**, 38.06s; zero failures/errors/skips; integration population selected separately above |
| Frontend and frozen artifacts | **96/96 frontend tests**, types/format/contracts/build pass; **24/24 + 16/16** baseline and 150 existing offline evaluation dispositions unchanged |
| Preserved infrastructure | Three roots validate; **14/14** native mock plans pass; Ruff/154-file format/diff checks pass |

Populations overlap: full integration includes the browser test; focused repeats
are repeated execution of the same assertions. They are not additional unique
product scenarios or model-quality evidence. All positive browser runs reported
zero runtime errors/external page requests and retained both idempotent retries.

Linux used Ubuntu WSL, kernel 6.18.54.1, UID 1000, Python 3.14.9, Node 24.22.1,
Google Chrome **156.0.8078.47**. Windows Chrome was **155.0.8059.85**. The hosted
report specifies Ubuntu/Python/Node, but not its exact Chrome version; WSL is not
the hosted Ubuntu-24.04 runner image. Both local browsers retained sandboxing.

Local setup used cached project-image Python dependencies/Node, the official
Google stable Debian package (SHA-256 in evidence), and three Ubuntu shared-library
packages extracted under ignored `.cache/`. Signed apt metadata was refreshed
only into that cache after a stale-index download 404. No system package, AppArmor,
kernel or Chrome security policy was changed. The owner started Docker's Linux
engine; the existing cached loopback PostgreSQL service/retained volume was reused.
Migrations reported `applied: []`; per-test synthetic schemas are cleaned normally.

The first Linux full-suite attempt reported **240 passed, 6 failed, 11 errors**:
restart children intentionally replace PYTHONPATH, exposing incomplete dependency
placement in the extracted interpreter, and Ubuntu's OpenSSL 3.6 rejected the
existing expired-certificate fixture's `-days -1`. Dependencies were placed into
the isolated interpreter's own site-packages; a workspace-local cached Debian
OpenSSL **3.0.22** executable/libraries/config restored the supported fixture
environment. **No application or certificate test was changed to obtain a pass.**
The corrected full run above supersedes that environment attempt without hiding it.

Exact executed validation commands (root unless noted):

```powershell
docker compose up -d --wait --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
# Windows, FATA_BROWSER_EXECUTABLE set to the installed Chrome path:
.venv/Scripts/python.exe -m pytest tests/test_browser_ui.py -q -s -m integration --basetemp=.cache/pytest-r5a-browser-windows
.venv/Scripts/python.exe -m pytest -q -m integration --basetemp=.cache/pytest-r5a-ci-integration-windows --junitxml=.cache/f4-03b-r5a-browser/windows-integration.xml
.venv/Scripts/python.exe -m pytest tests/test_browser_harness.py -q --basetemp=.cache/pytest-r5a-browser-negative
# Each Ubuntu invocation uses --cd <repository>; no real credentials mounted:
wsl.exe -d Ubuntu --cd <REPOSITORY> -- python3 .cache/f4-03b-r5a-browser/run_linux.py before
wsl.exe -d Ubuntu --cd <REPOSITORY> -- python3 .cache/f4-03b-r5a-browser/run_linux.py focused
wsl.exe -d Ubuntu --cd <REPOSITORY> -- python3 .cache/f4-03b-r5a-browser/run_linux.py launcher
wsl.exe -d Ubuntu --cd <REPOSITORY> -- python3 .cache/f4-03b-r5a-browser/run_linux.py integration
wsl.exe -d Ubuntu --cd <REPOSITORY> -- python3 .cache/f4-03b-r5a-browser/run_linux.py verified
.venv/Scripts/python.exe .cache/f4-03b-r5a/run_checks.py
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
```

The private Linux launcher invokes the extracted Python with normal site-packages,
`PYTHONPATH=src`, isolated library/PATH/XDG values, FATA_PROVIDER=fake, telemetry=none,
explicit installed-browser path and unique per-run basetemp/JUnit files. `before`
uses a source copy with HEAD's original browser script/test. Each positive run is
ordinary `python -m pytest -q -s -m integration tests/test_browser_ui.py`; integration
mode removes the file selector. Existing tools on an Ubuntu runner can execute
those commands directly after normal frozen dependency/build/database setup;
the cache-preparation scripts are local environment aids, not a new CI dependency.

**Remaining hosted-only uncertainty:** the original launch cause and this patch's
behavior on that exact hosted image remain unverified. A later owner-run Actions
execution must pass the original installed-browser test and full integration
suite. No hosted job was started or bypassed here. This correction does not
authorize AWS writes, R5B, live models, telemetry, spending, commits or pushes.

**Readiness:** GO for owner source/proposal review. Before R5B, choose/approve the
separate writer and auth route, exact bucket and source/plan, <=2h window, effective
IAM/MFA/Free-plan evidence, privacy/recovery/capture procedure and gross budget.
Proposal requests **$0.05**, stop at **$0.02** operational forecast/observation;
neither is active or an enforceable AWS billing cap. Account-owner $100 credits
do not change that. Actual backend verification follows protected bucket creation
only; a real infrastructure plan additionally needs concrete AMI/tools/AZ/image
inputs. Missing inputs stop the workflow rather than accepting placeholders.
Deployment apply, publication, teardown, paid upgrade, provider and telemetry
activation remain separate NO-GO decisions. **Stop after R5A for review.**
