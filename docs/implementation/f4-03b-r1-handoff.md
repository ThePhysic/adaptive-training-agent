# F4-03B-R1 — Offline authentication and account-readiness resolution

2026-10-25 (America/Los_Angeles). **R1 complete for review; F4-03C remains NO-GO.**
Starting HEAD: `992b0861dbc10bfb0ae521da8aed3a6cbdd10435`.
Zero new AWS account requests, real credential exports, live profile changes,
IAM changes, account-connected plans/backend initialization, resources, cloud
spending, model calls, hosted exports, commits or pushes. Real AWS config/cache
and credentials were not read by the experiment. No live auth launcher was added.

## Main finding: correct the broad incompatibility assumption

The public AWS support matrix still says Go v2 login support is absent, but the
**pinned SDK implementations contain direct login resolution**. F4-03B reported
an inference, not an observed authentication failure; historical report unchanged.
R1's stronger source/native evidence supersedes that broad inference.

Offline ELF/PE build-info inspection found:

| Inspected binary | SDK config / credentials modules | Evidence |
| --- | --- | --- |
| Terraform1.17.0 Linux CLI |1.32.12 /1.19.12 | Embedded build metadata; pinned config source resolves LoginSession and CredentialProcess |
| AWS6.70.0 Windows provider |1.33.9 /1.20.9 | Embedded metadata agrees with tagged provider go.mod; source includes logincreds/cache support |
| AWS6.70.0 Linux provider | Runtime experiment below | Both process and fresh synthetic login-cache credentials work against local STS |

The native probe's **fresh synthetic login cache succeeded without a process**.
A missing cache failed; that failure must not be described as lack of SDK support.
No refresh, DPoP exchange, real CLI cache, real identity/MFA or S3-backend integration
was verified. The fresh-cache fixture deliberately uses a nonfunctional synthetic
refresh/DPOP value; it cannot demonstrate refresh compatibility.

**Recommendation:** verify the existing source profile directly in both actual
consumers before adding another selector. Keep the documented credential_process
bridge as a reviewed fallback, not a mandatory new abstraction. The
[concrete proposal24](../planning/24-f4-authentication-and-account-evidence-proposal.md)
contains its non-activating INI example, sole source binding, callback/ACL/expiration/
fallback rules, real-plan authorization requirements and official sources dated
2026-10-25. Both potential routes retain the approved IAM identity and short-lived
credentials; neither grants additional permissions or authorizes activation.

## Implemented offline experiment and exact outcomes

`infra/aws/fixtures/authentication_probe.py` is a contained test, not a credential
exporter. It invokes no AWS CLI. Entry requires Linux with **only lo**, fixed cached
tool/mirror mounts and disposable `/work`. It initializes only provider plugins
with `-backend=false`, creates no resources/remote backend, and runs speculative
plans against a loopback STS fake. No account-connected plan occurs.

The fake checks GetCallerIdentity, the synthetic signer key ID and session token;
it is not an independent cryptographic SigV4 verifier or AWS authorization engine.
The selected profile is exercised against poisoned synthetic default credentials.
Inherited credential/role/web-identity/container/proxy/endpoint/log overrides are
removed; HOME/config/credentials/login cache point only into the sandbox. No real
home/cache is mounted. Process replies are captured privately in memory; no key,
secret or session canary appears in captured Terraform output or shared evidence.

| Native case | Terraform exit | Process calls | Local STS requests | Result |
| --- | ---: | ---: | ---: | --- |
| Valid process, explicit provider profile |0 |1 |2 | Expected identity output true |
| Valid process, sanitized AWS_PROFILE selection |0 |1 |2 | Same result, without a provider profile override |
| Process failure |1 |1 |0 | No default/other credential fallback |
| Malformed process JSON |1 |1 |0 | Rejected before STS |
| Unsupported process Version |1 |1 |0 | Rejected before STS |
| Missing selected profile |1 |0 |0 | Poisoned default not selected |
| Login session, missing synthetic cache |1 |0 |0 | Missing material fails closed |
| Login session, fresh synthetic cache |0 |0 |2 | Direct native login-cache path works |

**8/8 expected dispositions.** [Native evidence](evidence/f4-03b-r1-authentication.json).
This demonstrates Linux provider behavior only. Normal AWS TLS/destination
behavior is not tested by this HTTP-only network-none fake. Production destination,
network, state/locking and application safeguards are unchanged. No local fixture
endpoint/skip flag is a deployment example.

All server threads are shut down/awaited, owned process groups have bounded
timeouts and are killed/awaited on timeout, and temporary profiles/cache are
removed. Unit tests cover the timeout path using a controlled fake; no real
unrelated process is killed. Native success/failure cases use real child processes.

An initial Windows test expected LF rather than CRLF; splitlines now checks the
same classified stderr on both platforms. Initial native credential_process INI
quoting returned127 even though direct fake-process execution succeeded. The
corrected synthetic command quotes executable/script paths without outer command
quotes and ends with a controlled no-space argument; native cases then passed.
This is fixture correction, not a bypass of credential validation. Diagnostic raw
error dumping was removed. Real Windows CLI INI quoting still needs separate
authorization/verification; the proposal ends with literal `--format process`.

## Permission and evidence resolution

No previously denied read is a prerequisite to **rendering an offline plan**.
Before AWS execution, the owner must establish evidence, without necessarily
granting the learner new access:

- **Boundary:** exact-user GetUser result or owner console/API evidence of the
  boundary/explicit absence; if present, exact policy/version review. The optional
  draft permits only that exact user's GetUser, not IAM Get* or boundary writes.
- **Quotas:** applied us-east-1 EC2 standard-vCPU `L-1216C47A` and VPC `L-F678F1CE`,
  plus current regional headroom. Need at least2 extra standard vCPUs and1 extra
  VPC. Owner-provided evidence avoids any grant; alternative is two exact quota
  ARNs. No quota increase, list-all grant or default-value assumption.
- **Organization:** owner establishes standalone/management/member status and,
  for a member, has an existing authorized reviewer inspect inherited SCP/RCP
  controls. DescribeOrganization alone is insufficient; DescribeEffectivePolicy
  does not apply to SCPs/RCPs. No Organizations administrator/extra role is needed
  for this agent merely to obtain an owner-reviewed evidence package.
- **SSM:** DescribeInstanceInformation is for registration/agent verification
  after deployment, not a first empty-state plan requirement. If later granted,
  it requires Resource `*` with a regional condition; exact instance filtering is
  data minimization, not IAM scoping. It is omitted from the base draft. Optional
  DescribeOrganization also has no resource-level scope and is omitted.
- **MFA:** last F4-03B measurement returned zero registered caller devices; no
  fresh account read in R1. Owner enrollment, refreshed device evidence, fresh
  MFA-authenticated source login and session-specific evidence remain outstanding.
  STS identity/device registration/sign-in-session ARN alone do not prove MFA.
  Verify context-key availability before a policy change; no guessed MFA condition
  or MFA enrollment permission is introduced by this work.

[Draft policy](../planning/proposals/f4-03b-r1-read-permissions.json): two optional
statements, placeholders, exact resources, no `*`, no write/attach/pass-role actions.
Tests are structural only, **not AWS IAM evaluation**. Owner-provided evidence is
preferred; no attachment or grant is requested automatically. Proposal24 gives
the exact scope and public AWS service-authorization references.

## Files, commands and checks

Changed files:

- `infra/aws/fixtures/authentication_probe.py`, `tests/test_terraform_authentication.py`:
  native synthetic experiment,26 routine tests for process/env/privacy/cleanup and
  proposed-policy structure; no production authentication path.
- `docs/planning/24-f4-authentication-and-account-evidence-proposal.md`, its
  `proposals/f4-03b-r1-read-permissions.json`, checklist23 and `infra/aws/README.md`:
  concrete fallback/least-privilege proposal, corrected finding and reproducible probe.
- This handoff and `evidence/f4-03b-r1-{authentication,checks}.json`.

No Terraform HCL, IAM attachment, migration, main/experimental lock, application
source, frontend, production release/SSM/storage/networking code or historical
acceptance/evaluation record changed. No dependency acquisition was required.

```powershell
.venv/Scripts/python.exe .cache/f4-03b-r1/run_checks.py
.venv/Scripts/python.exe .cache/f4-03b-r1/run_linux.py
.venv/Scripts/python.exe .cache/f4-03b-r1/run_native.py
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/python.exe -m pytest tests/test_terraform_authentication.py tests/test_infrastructure.py tests/test_host_preflight.py tests/test_release.py -q --basetemp=.cache/pytest-f403br1-final
.venv/Scripts/ruff.exe check src scripts tests infra/aws --no-cache
.venv/Scripts/ruff.exe format --check src scripts tests infra/aws --no-cache
git diff --check
```

The ignored check wrapper invokes `scripts/check.py` with stdout/stderr captured;
Linux wrapper uses the existing locked test image, copies tracked files plus new
auth/proposal fixtures into disposable tmpfs and invokes `python -m pytest -q`.
Exact native Docker flags/mounts are in the infra README; wrapper uses precisely
that invocation. Native per-case commands are `terraform init -backend=false
-input=false -lockfile=readonly` and `terraform plan -input=false -no-color` only
inside the isolated fake-provider experiment. No remote backend initialization.
Binary metadata was read using `Path.read_bytes()` and regex
`github\.com/aws/aws-sdk-go-v2/(config|credentials)\tv[^\n\x00]+`, retaining only
module/version fields, not executing credential resolution.

| Check | Observed outcome |
| --- | --- |
| Windows shared sequence |20/20 commands exit0; **1,077 routine Python passed**,257 integration deselected, zero failed/error/skipped |
| Linux routine | **1,077 passed**,257 deselected;45.27s, Docker network-none |
| Final auth/infrastructure/storage/release population | **97 passed**,7.05s; new auth population26; final auth-only repeat26 passed in1.39s |
| Native provider probe | **8/8 expected outcomes**, six local STS requests total, zero AWS/real credentials |
| Existing Terraform suite | Three roots validate, **8/8 mock plans pass**; format/static checks pass; locked1.17.0/6.70.0 unchanged |
| Frontend |85 tests, build/type/format/generated-contract checks pass |
| Frozen baseline | **24/24 development +16/16 held-out**; original model-suite150 dispositions unchanged |
| Privacy/integrity | New env/process canaries and existing privacy tests pass; credentials absent from captured native output/shared artifacts; protected implementation paths unchanged |

[Commands, durations and denominators](evidence/f4-03b-r1-checks.json).
Python3.14.9, Node24.22.1/npm11.19.1/Ruff0.17.2; unchanged cached tooling/images.
Root routine results include26 new cases; counts above overlap and must not be
summed. Full PostgreSQL/browser, hosted Actions and release/restore drills were
not repeated: no application/storage/CI behavior changed. Earlier accepted hosted
release evidence remains for its recorded revision, not proof of this new probe.

## F4-03C assessment and owner actions

**GO for review/offline preparation; NO-GO for live authentication or cloud work.**
Generic SDK incompatibility is corrected; actual profile/refresh/backend behavior
is unresolved. Before live validation, owner must approve exact identity/account,
credential use and any config/callback change. Before a real plan, also obtain
MFA/effective-permission/quota evidence and approve all concrete inputs, state
destination/initialization/lock permissions and potentially billable requests.
Keep native S3 locking; do not use -lock=false or another identity as a workaround.
State bootstrap, state migration/write, resource creation, image publication,
SSM operation, recovery and teardown require their own exact authorization.
An approved plan would not authorize apply. Existing privacy, provider-spend and
telemetry NO-GO gates remain. **Stop after F4-03B-R1 for owner review.**
