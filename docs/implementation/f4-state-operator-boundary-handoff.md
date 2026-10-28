# F4 — persistent state-operator boundary: offline implementation

2026-10-26. **Proposal generation and offline validation only; stop for review.**
No AWS account request, identity probe, IAM mutation, Access Analyzer call, S3
operation against AWS, remote-state init/migration, apply, resource, spending,
credential export, commit or push occurred. Public official documentation was
reviewed; all execution used synthetic fixtures and local transports.

## 1. Implementation and preserved decisions

Added a customer-managed-policy **proposal** named
`future-f4-state-operator-boundary`. Terraform remains its sole generator. It is
not an IAM resource and has not been created, attached or made effective in AWS.

Accept the owner's established human-admin, preflight, policy-administrator and
state-operator identities/setup; nothing was retried or inspected in the account.
`future-f4-human-admin` performs separately approved bucket bootstrap. The state
operator receives no bootstrap/provisioning authority. The prepared temporary
policy-administrator delegation remains unattached and must not be activated.

The initial worktree contained the user's parenthesized exception-handler repair
in `state_operator_prepare.py`. It is preserved, with a formatter-skip annotation
so formatting does not rewrite it. Regression tests compile/import the module and
exercise every caught error type with sanitized failure output.

## 2. Files changed and integration design

| File | Purpose |
| --- | --- |
| `infra/aws/state-bootstrap/boundary.tf` | Opt-in policy local/output and exact-user/size preconditions; no resource or attachment |
| `infra/aws/state-bootstrap/tests/safety.tftest.hcl` | Six additional mock-plan cases for persistent/temporal separation, exact scopes, human bootstrap, real operator path and rejected principals |
| `infra/aws/state-bootstrap/tests/fixtures/state-operator-boundary.synthetic.json` | Reviewable generated all-zero-account/dummy-bucket policy artifact |
| `infra/aws/state_boundary.py` | Independent strict output/spec validation; deliberately not a second generator or IAM simulator |
| `infra/aws/state_operator_prepare.py` | Optional `--boundary-only`, independent validation, separate readiness marker, source fingerprint for new Terraform file; existing default two-output path preserved |
| `infra/aws/fixtures/backend_probe.py` | Two additional native offline cases, bounded prefix/method evidence and differentiated missing-state 403/404 fixtures |
| `tests/test_state_boundary.py` | Positive/adversarial shape checks, limited rule illustrations, loopback errors, handler and fingerprint regressions |
| `infra/aws/README.md` and this handoff | Current human-bootstrap decision, local invocation, limitations and future approval gates |

`main.tf`, `authority.tf`, protected-bucket resources, dependency locks,
`private_command_runner.py`, application/CI code and evaluation data are unchanged.
The old bootstrap, full state-access and plan-only policy documents are byte-identical
to the accepted synthetic baseline. Their principal/account/region/TLS/start/expiry
conditions are retained; the plan-only document still omits state PutObject.
Existing administrator MFA controls and all live/provider/financial barriers remain.

Boundary generation uses the existing six-field input and serialization workflow.
The new mode permits a distinct human bootstrap principal while requiring the
exact same-account `user/[optional path/]future-f4-state-operator` as state principal.
The legacy equal-principal validator is not relaxed. Terraform's new boolean input
defaults false, so existing output behavior remains opt-in compatible.

The source manifest grows from four to five files, including `boundary.tf`. A
boundary-only readiness marker cannot be consumed as bootstrap/plan readiness.
Stale manifests fail closed: use a fresh label/review, not overwritten files or
manually replaced hashes. `--boundary-only --review-plan` is rejected. No broader
writer, temporary delegation or financial authority is emitted by the new mode.

## 3. Generated artifacts and invocation

Reviewable **synthetic**, generated fixture:

`infra/aws/state-bootstrap/tests/fixtures/state-operator-boundary.synthetic.json`

Two independently prepared private local artifacts:

```text
.cache/r5b-checkpoint-b/boundary-synthetic-a/state_operator_boundary_policy.json
.cache/r5b-checkpoint-b/boundary-synthetic-b/state_operator_boundary_policy.json
```

Both match each other and the tracked synthetic fixture byte-for-byte. Each has
14 statements, **3,300 compact JSON characters** / **5,016 artifact bytes**. The
Terraform output and independent validator enforce the managed-policy 6,144-character
limit. No real account, bucket or principal identifiers were supplied or generated.
[IAM policy limits](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html).

The future real policy uses the exact reviewed private bucket/account/user path;
do not attach the all-zero synthetic document. The artifact body contains no
PolicyName field: the separately approved CreatePolicy operation would select the
name above. Neither a local filename nor a READY marker creates an AWS policy.
Do not install this document using PutUserPolicy: it is a customer-managed boundary,
not the prior inline bootstrap/delegation grant.

Before invoking preparation, inspected its writes and isolation: new ignored,
ACL-protected bundle/review directories, copied local sources/lock, local-backend
init, `terraform console` **without `-plan`**, cached-only plugin mirror, empty
config/credentials/home and senderless deny proxy. No provider Configure/data
lookup or managed-resource planning is required to evaluate these locals. Native
preparation reported **zero proxy attempts** for each new and legacy run.

Use the existing Windows PowerShell 5.1 private-input/ACL procedure, then:

```powershell
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec $SpecPath --name $FreshLabel --boundary-only
if ($LASTEXITCODE -ne 0) { throw 'boundary_preparation_failed' }
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec $SpecPath --name $FreshLabel --boundary-only --verify-source
if ($LASTEXITCODE -ne 0) { throw 'boundary_source_review_failed' }
```

Keep real artifacts under protected ignored `.cache`, encrypted local storage and
private review. No credentials, user data or signed requests belong in the spec.
The legacy window fields remain input metadata for the reused bundle; they never
enter the persistent boundary. Its bytes remain unchanged when the temporary
window changes. Existing private command execution stays unconditionally disabled.

## 4. Exact maximum capabilities and conditions

The boundary is a ceiling, **not a grant**. Existing SignIn permissions and separately
approved identity-based state policies still supply permissions, intersected with
the ceiling and other applicable policy restrictions.

| Capability | Actions / exact scope |
| --- | --- |
| Browser CLI authentication | `signin:AuthorizeOAuth2Access`, `signin:CreateOAuth2Token`; `arn:aws:signin:*:*:oauth2/public-client/*` |
| Workspace discovery metadata | `s3:ListBucket` on only the designated bucket ARN, `StringEquals s3:prefix=["env:/"]` |
| Default-workspace state | `s3:GetObject`, `s3:PutObject` on only `<bucket ARN>/ec2-demo/terraform.tfstate` |
| Native lock | `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on only `<bucket ARN>/ec2-demo/terraform.tfstate.tflock` |

The authentication resource pattern intentionally matches the documented
SignInLocalDevelopmentAccess v3 policy, including same-/cross-device public clients.
It is the only wildcard resource Allow. Copying S3 conditions onto pre-login OAuth
could deny legitimate authentication before the context exists. No account/region,
MFA or temporal condition is added to these authentication statements. This does
not remove console MFA or authenticate a real session in this experiment.
[Managed sign-in policy](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html).

All three S3 Allows retain exact principal ARN, principal account, us-east-1 and
SecureTransport=true. They have no Date conditions. Existing temporary identity
grants retain their <=2h windows. No new MFA condition is invented for S3: the
existing state grants do not have one, and real login-session condition compatibility
has not been demonstrated. The separate administrator MFA proposal is unchanged.
No role assumption/pass-role, bucket setup/delete, object versions, IAM, EC2,
KMS/DynamoDB, workspace state paths or provider-provisioning permission is added.

## 5. Explicit denies and IAM security semantics

An implicit deny in a boundary can be bypassed by a same-account resource policy
grant directly to an IAM user ARN. An applicable explicit deny remains authoritative.
Therefore Allow-only maximums are insufficient for the prohibited paths.
[Boundary evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html),
[explicit-deny precedence](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html).

Ten reviewed Deny statements close those paths:

| SID / family | Effect |
| --- | --- |
| DenyOtherActions | `NotAction` lists only the six allowed action names; denies everything else on `*` |
| DenyOtherLoginResources | The two sign-in actions denied outside the documented public-client resource pattern |
| DenyOtherBuckets | ListBucket denied outside the exact bucket |
| DenyOtherObjectKeys | Get/Put/DeleteObject denied outside the two exact keys |
| DenyStateDeletion | DeleteObject explicitly denied on the state key |
| DenyOtherPrefixes | ListBucket denied for any other or missing prefix on the exact bucket |
| DenyWrongPrincipal / Account / Region | Three separate S3 denies ensure any one bad/missing identity/region context fails; not an incorrect combined AND |
| DenyInsecureOrMissingTransport | S3 denied for false/missing SecureTransport using BoolIfExists |

`NotAction`/`NotResource` appear only with Deny. Global `Resource="*"` is intentional
in deny guards, never a general-purpose Allow. The complementary resource denies
prevent allowed action names from becoming arbitrary-resource permissions. Separate
S3 guards preserve pre-login OAuth. No resource-policy `NotPrincipal` deny is used.
[NotAction semantics](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_notaction.html),
[NotResource semantics](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_notresource.html).

**Residual limitations:** a direct-user resource-policy grant *within* this ceiling
can still authorize the exact allowed action/key without an identity Allow, including
outside its temporary window. There is no IAM condition here proving which policy
supplied an Allow. Keep the protected bucket policy deny-only for TLS, with enforced
ownership/no ACL grants, and require trusted review of all resource-policy writers.
The tests demonstrate this remaining path rather than claiming it was eliminated.
If the requirement is absolute identity-only authorization even against a malicious
resource-policy writer, this persistent boundary alone cannot meet it; further
owner-approved policy architecture would be needed. No temporal condition was
silently added to the persistent ceiling to hide that conflict.

A trusted human/root administrator can alter/remove the boundary. The boundary
does not constrain another principal, revoke issued credentials or protect against
host compromise. State PutObject is itself trusted state-mutation authority:
downstream privileged operators must review state/plan integrity and never blindly
apply it. The policy administrator could still deny service by changing inline
policies; no delegation is activated here. The old bootstrap grant must not be
attached to the state operator; if attempted later with this boundary, its bucket
setup actions are explicitly denied.

The PrincipalAccount condition identifies the caller, not the bucket owner; S3
bucket ARNs contain no account ID. Future verification must establish the exact
bucket's expected owner/region and reject collision or adoption of another account's
bucket. No ownership proof is inferred from this offline ARN construction.

STS GetCallerIdentity has documented special behavior even under an explicit deny.
No STS permission is added, and this boundary is not advertised as preventing identity
disclosure through that operation. Local source/transport gates still prohibit
unauthorized identity requests.
[STS identity exception](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html).

## 6. Terraform 1.17.0 S3-prefix investigation

Reviewed the pinned core implementation, not merely a documentation example.
`Workspaces()` constructs `workspace_key_prefix + "/"`, therefore **`env:/`**.
The state client performs exact-key HeadObject then GetObject, not another object
list for default-state existence. Native locking uses conditional PutObject,
GetObject and DeleteObject on the exact `.tflock` key.
[Pinned workspace code](https://raw.githubusercontent.com/hashicorp/terraform/v1.17.0/internal/backend/remote-state/s3/backend_state.go),
[pinned state/lock client](https://raw.githubusercontent.com/hashicorp/terraform/v1.17.0/internal/backend/remote-state/s3/client.go).

Both Windows and network-disabled Linux native-core experiments produced:

| Synthetic workload | Native exits | Observed listing / state behavior |
| --- | --- | --- |
| Existing state: init, repeated init, read-only plan | 0 / 0 / 0 | Five env:/ lists; three HEAD+GET pairs; one conditional lock put/read/delete; no state write |
| Missing state with 404: init then plan | 0 / 0 | Three env:/ lists; two HEAD requests; lock lifecycle completes; no state write |
| Workspace discovery returns AccessDenied, state exists | 0 | Two env:/ attempts; default-workspace fallback, then HEAD+GET |
| Missing-state HEAD returns 403 | 1 | Two env:/ lists, then HEAD fails; not treated as missing state |

All ten cases on each OS retained zero real AWS requests and zero proxy attempts.
Every successful listing was exactly env:/; root/other prefixes fail in the fixture.
No HeadBucket/list-all-buckets or additional list prefix was required by the tested
core workloads. Workspace names under env:/ are metadata; exact non-default-workspace
state/lock object access remains denied. This is not support for using other workspaces.

**Decision: retain the existing prefix unchanged in grants, tests and the ceiling.**
No observed request proves it incompatible, and the documentation's default-path
listing example does not substitute for the pinned native request trace.
However, the docs require listing the state path, and AWS HeadObject/GetObject
not-found status depends on ListBucket authorization. Our fake's configured 404
does not evaluate that IAM condition; a real S3 403 could make first initialization
fail. This is an unresolved **deployment prerequisite**, especially with the new
explicit prefix deny, not a claim that empty-bucket compatibility is proven.
[Backend permissions](https://developer.hashicorp.com/terraform/language/backend/s3),
[S3 HEAD authorization](https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html).

After separate authorization, verify actual context/status for this exact key and
empty/existing state before backend activation. If evidence requires another list
prefix, propose only the exact necessary state/lock-key prefix and update both
identity grant and boundary/deny tests together. Do not assume that such an addition
fixes an internal missing-prefix authorization check; do not grant empty-prefix,
bucket-wide listing, wildcard workspace objects or catch 403 as “state absent.”
Human-initialized state is another separately reviewable option, not implemented here.

## 7. Tests and observed validation

The independent validator deliberately repeats the security assertions outside
Terraform. It validates, never generates; future unexpected Allows, wildcards,
condition changes, missing denies, auth breakage and wrong identities fail closed.
The test-only matcher supports just this policy's scalar Action/NotAction,
Resource/NotResource and condition subset. Its direct-grant/deny examples are not
complete AWS IAM simulation, account permission evidence or service-compatibility proof.

Positive cases cover exact state/lock operations, both documented login clients,
default discovery, no standalone boundary grant, independent temporal windows,
determinism and human/operator separation. Negative cases cover arbitrary buckets,
keys, workspace state, state deletion, incorrect locks, versions, IAM/EC2/STS
escalation, access-point resources, wrong/missing S3 context, inappropriate wildcard
Allow/deny exceptions, lost guards and auth constraints. Handler tests include all
five error types; fingerprint tests reject changed boundary sources and wrong modes.

| Check | Observed result |
| --- | --- |
| Shared offline sequence | **20/20 commands exit 0**; **1,360 routine Python tests passed**, 48.69s; zero failures/errors/skips, 257 integration deselected |
| Affected Windows tests | **213/213 passed**, 8.40s; subset of the routine population, including **79 new** boundary cases |
| Affected Linux tests | **213/213 passed**, 8.98s; networking disabled, source read-only and private test storage disposable |
| Terraform | fmt/static checks, all three roots validate; **21/21 mocked cases**: deployment 5, bootstrap 14, bucket module 2; no resource count increase (23 source resource blocks, six in bootstrap plan) |
| Native core protocol | **10/10 expected dispositions on each OS**, zero real AWS requests; failures are deliberately expected outcomes, not failing tests |
| Native generation | Two boundary artifacts + fixture byte-identical; legacy two policy artifacts byte-identical to accepted synthetic baseline; both new boundary and legacy manifests verify **five unchanged source files** |
| Privacy/security | Wrong identity/conditions/resources, direct-grant illustrations, canaries, corrected-handler failures and source drift fail as expected. Existing private runner/ACL/owned-process regressions pass |
| Frontend/contracts/baseline | **131 frontend tests** plus TypeScript, generated contracts, formatting and build pass; frozen **24/24 development + 16/16 held-out** baseline and all 150 template/fake/replay dispositions reproduce |
| Source checks | Ruff lint/format and Git whitespace check pass; existing user handler correction retained; protected application, policy mechanisms and data sources unchanged |
| Instructions | All three new PowerShell snippets parse without execution. Existing README `<PRIVATE...>` templates are review placeholders, not executable PowerShell; their earlier parse limitation was not changed |

Commands executed from the repository root:

```text
.tools/terraform/terraform.exe fmt -recursive infra/aws
.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/boundary-synthetic-spec.json --name boundary-synthetic-a --boundary-only
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/boundary-synthetic-spec.json --name boundary-synthetic-a --boundary-only --verify-source
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/boundary-synthetic-spec.json --name boundary-synthetic-b --boundary-only
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/boundary-synthetic-spec.json --name boundary-synthetic-b --boundary-only --verify-source
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name boundary-legacy-regression
.venv/Scripts/python.exe infra/aws/state_operator_prepare.py --spec .cache/r5b-checkpoint-b/synthetic-spec.json --name boundary-legacy-regression --verify-source
.venv/Scripts/python.exe infra/aws/fixtures/backend_probe.py --native-offline
.venv/Scripts/python.exe -m pytest tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_private_command_runner.py -q --basetemp=.cache/pytest-boundary-windows-final
.venv/Scripts/python.exe .cache/r5b-checkpoint-b/run_checks.py
.venv/Scripts/ruff.exe check infra/aws tests/test_state_boundary.py --no-cache
.venv/Scripts/ruff.exe format --check infra/aws tests/test_state_boundary.py --no-cache
git diff --check
git check-ignore AGENTS.md .cache/r5b-checkpoint-b/boundary-synthetic-a/state_operator_boundary_policy.json
```

The existing ignored `run_checks.py` launches unchanged `scripts/check.py` with
inherited AWS/TF/provider/telemetry/proxy overrides removed and captures output in
protected ignored storage; it is not a cloud runner. Native generation first
passed an AST syntax check. Synthetic-only files were created with the existing
Windows hidden-input/DACL procedure. Local byte comparisons asserted all-zero
input before comparing generated artifacts; raw policy bodies were not logged.

Exact Linux commands (PowerShell, existing local image; no pull/install):

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest infra/aws/fixtures/backend_probe.py --native-offline
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace,readonly" --tmpfs /workspace/.cache:rw,mode=700 -w /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -m pytest tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_private_command_runner.py -q --basetemp=.cache/pytest-boundary-linux
```

Reports: `.cache/f107/check-results.json`, protected `checks.log`,
`.cache/f4-02/checks.json`, and private `boundary-backend-native.json` /
`boundary-backend-linux.json` under `.cache/r5b-checkpoint-b`. Windows PowerShell
redirected the two native reports as UTF-16; their parser used that encoding.
Only operation enums/counts/known synthetic prefixes escape the native fixture;
opaque native lock contents and raw Terraform output remain private memory.

Environment: Python **3.14.9** on Windows/Linux, Windows PowerShell **5.1**,
Node **24.22.1**, Terraform **1.17.0**, locked AWS provider **6.70.0**; no dependency
or image acquisition. Native policy preparation is Windows evidence; Linux
evidence covers unit guards and the actual core's fake S3 protocol, not the Windows
ACL API or policy preparation on a different OS.

Not executed: genuine IAM/Access Analyzer, resource-policy evaluation, real login
with the boundary, actual S3 status/permission behavior, hosted CI, backend writes
or provisioning—all lack authorization. PostgreSQL and installed-browser integration
were not rerun because no application/persistence/UI code changed. Prior accepted
evidence is preserved; no new database/cloud/browser correctness is claimed.

Concise Git summary: **four tracked files modified, five new files** (including
this report and the generated synthetic fixture); no dependency, managed-resource,
application or frozen-artifact change. The initial user handler edit is included
and preserved. No staging, commit or push.

## 8. Remaining approvals and proposed next milestone

Next: independent review of this offline boundary/threat model and the unresolved
S3 not-found prerequisite; then a **separately authorized** account validation/setup
unit. No next milestone or spending is approved by this report.

Future account-side actions requiring explicit approval include:

1. Any STS/IAM read, IAM Access Analyzer ValidatePolicy/simulation or S3 probe,
   with exact identity/endpoints/output privacy and costs reviewed. None ran here.
2. Human-admin `iam:CreatePolicy` for the exact reviewed private body/name and
   managed-policy ARN; then `iam:PutUserPermissionsBoundary` on only the exact
   state-operator user. The three-action policy-administrator proposal grants
   neither action and remains inactive; do not broaden it automatically.
3. Exact GetUser/GetPolicy/GetPolicyVersion and owner-authorized effective-policy
   verification, followed by scoped login/permission compatibility checks. Keep
   preflight read-only and preserve MFA; do not assume browser registration proves
   every API's MFA condition.
4. Separately approve temporary plan-only/state identity grants and their windows.
   Boundary attachment supplies no S3 grant and does not activate a full writer.
   `plan_operator_policy` means backend state/lock access, not provider inventory
   authority. Using this user for both backend and the deployment AWS provider
   would fail under the ceiling. A real infrastructure plan needs a separately
   reviewed provider identity/credential separation; do not broaden this boundary
   or silently select another profile to accommodate the existing root.
5. Human-admin bootstrap of the reviewed six S3 configuration resources, saved-plan
   review/apply, protection/recovery checks and any genuine backend/lock operation,
   each under the existing independent execution checkpoints. No operator bootstrap.
6. Any policy version/default-version change, boundary removal/replacement or cleanup.
   Revoke/reconcile temporary grants before relaxing a boundary; never treat removal
   as a harmless rollback. Do not delete policies, state versions or resources here.

Retain the existing **$0.05 gross maximum proposal / $0.02 operational stop** as
unapproved estimates, not active authorization or an enforceable AWS cap. No
cost-bearing service/resource was added; Free-plan credits do not authorize setup.
Provider calls, hosted telemetry and financial live authority remain disabled.
