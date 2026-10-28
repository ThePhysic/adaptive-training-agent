# F4 AWS validation and deployment-readiness planning handoff

2026-10-26. **Offline planning completed; no AWS execution authorized or performed.**

## Executive summary

The independently reviewable procedure is
[planning document 26](../planning/26-f4-aws-validation-and-deployment-runbook.md).
It provides future PowerShell command vectors, caller/profile selection, permission
scopes, expected results, sensitive-output handling, mutation/cost classifications,
stop conditions and recovery. The vectors are proposals, not activated commands.

Keep the state user restricted to state/lock access; the human administrator does
the one-time bucket bootstrap. Recommend a separately approved nonadmin direct-login
deployment user for provider operations. The deployment root's host-role policy
editing needs an independently administered permissions ceiling, or separate IAM
ownership, before provisioning grants are issued. These are design proposals;
no identity, policy or infrastructure source was changed.

**GO for independent review; NO-GO for live execution under this milestone.** The
boundary remains a local proposal. The old policy-administrator delegation remains
inactive. No fresh account evidence, MFA-session proof, actual S3 compatibility or
AWS deployment correctness is claimed.

## Verified facts, supersession and unresolved implementation prerequisites

Reviewed AGENTS.md, current Git status, infrastructure README/roots/module/utilities,
planning documents 22–25, the boundary handoff and syntax follow-up. Existing working
changes were preserved. The latest owner instruction supersedes the older
operator-bootstrap procedure; historical handoffs were not rewritten.

Verified repository facts:

- Terraform 1.17.0 and AWS provider 6.70.0; bootstrap backend is local, deployment
  backend is S3, both providers restrict account and us-east-1.
- Bootstrap has exactly six protected S3 resources: bucket, public-access block,
  ownership controls, versioning, encryption and TLS-only bucket policy. No IAM
  policy resource, DynamoDB or state-expiration lifecycle is added.
- The proposed user boundary has four Allows/ten explicit Denies. It retains
  `s3:prefix=["env:/"]`, the exact state/lock keys and the reviewed login exception.
- Boundary-only generation supports human-bootstrap/state-user separation.
  Legacy operator preparation and plan review still require equal principals;
  the private runner prepares the operator identity and its live entry point is
  disabled. This is an execution prerequisite, not a reason to bypass guards.

Narrow corrections proposed for separate review, **not implemented here**:

1. Human-bootstrap preparation/review mode with independent principal bindings,
   exact six-resource/source/hash/window guards and negative swapping tests.
2. Reviewed private capture/identity/egress binding for the explicitly approved
   command vocabulary. Current generic capture primitives do not authorize AWS.
3. Dual-profile synthetic tests: explicit state-backend profile versus provider
   deployment profile, poisoned defaults, cache/refresh rejection and private
   principal postconditions. Keep administrator credentials outside that process.
4. Resolve provider host-role escalation before deployment grants: exact-role
   PutRolePolicy plus PassRole/RunInstances alone is insufficient containment.
5. Establish actual pinned Terraform retry/waiter behavior with offline faults;
   its `max_retries=1` must not be assumed equivalent to CLI `AWS_MAX_ATTEMPTS=1`.

Account plan, identities/MFA registration, accepted R3 identity evidence and quotas
are owner-supplied/historical evidence, not reverified here. Existing profile aliases,
live MFA context, policy closure, bucket ownership and authentication refresh paths
remain verification gates. No AWS profile/login cache or credential values were read.

## Proposed validation sequence and principal mapping

Exact future commands and permissions are in document 26, with separate approvals
for each subunit. Its E/F labels put bootstrap before genuine S3 testing.

| Checkpoint | Identity | Proposed scope and effects |
| --- | --- | --- |
| A1a, then A1b | Human administrator, then state user | One STS identity request each; private exact Account/Arn/UserId checks; no fallback or accepted preflight-probe rerun |
| A2/A3 | Human administrator | Exact user/group/policy metadata and then approved document closure; MFA registration; no management writes or account-wide policy enumeration |
| A4 optional | Human administrator | One sensitive existing CloudTrail history read; missing MFA context remains inconclusive |
| B1 | Human administrator | ValidatePolicy on the real private boundary as IDENTITY_POLICY; no analyzer/policy created; basic validation published no additional charge |
| B2 optional | Human administrator | SimulateCustomPolicy with exact identity and boundary documents/context; no service actions executed; not real S3/MFA proof |
| C | Human administrator | Create one customer-managed policy; private ARN/version/body readback; no attachment |
| D1/D2 | Human attaches; state signs in only as separately approved | PutUserPermissionsBoundary on the exact user, readbacks and distinct login verification; no old delegation or inline-policy substitute |
| E-plan/E-apply/E-read | Human administrator | Local-state bootstrap plan, separately approved saved-plan six-resource apply, separately approved owner/protection reads |
| F-read/F-init/F-lock/F-seed | State or human as explicitly named | Distinct read, real backend init, conditional native lock writes and optional human state seed approvals; no permission broadening |
| G-design/G-plan/G-apply | Proposed nonadmin deployment user + state backend | New identity/security review, then separate provider planning/backend locking and deployment/spending approvals |

Preflight remains read-only. Policy-administrator remains unused. No Organizations,
Identity Center, account upgrade or new role/profile is performed or implied.

## Boundary validation, S3 compatibility and bootstrap readiness

Access Analyzer receives the **real** generated policy, not the all-zero fixture.
Review strict JSON, size, exact ARN/account/user/region/TLS bindings, explicit-deny
matrix, authentication exception and every finding. No automatic pagination, paid
custom check or analyzer creation. Zero findings is not a security proof. Optional
IAM simulation is a separately approved account operation with hypothetical context.
Direct same-account user resource grants inside the ceiling can bypass an expired
identity grant; keep resource-policy administration trusted and bucket policy
TLS-deny-only. Neither the caller's PrincipalAccount nor an accountless S3 ARN proves
bucket ownership.

Real S3 compatibility remains unverified. After bootstrap/protection verification,
compare authorized human/state HEAD results and exact env:/ discovery. Human404 /
state403 means stop; never reinterpret403 as missing or broaden listing automatically.
Use a provider/resource-free compatibility root only with absent or reviewed
empty-resource state. Its native lock plan is a distinct S3-write approval. Preserve
state versions and lock liabilities; no automatic force-unlock or deletion.

If absence semantics block init, lowest-risk action is review. A separately approved
human conditional seed (`If-None-Match:*`) is an alternative to permission changes,
not an automatic workaround. Seed/lock writes and versions are retained/accounted.
An empty configuration must never plan against real deployment state.

Bootstrap is structurally ready and mock-tested, but human plan tooling/capture,
account evidence, policy validation, numerical cost approval and saved-plan review
remain prerequisites. Local bootstrap state stays protected outside the bucket;
it is never migrated into its own managed backend.

## Costs, security, recovery and limitations

Official public references were reviewed on 2026-10-26 and linked next to their
claims in document 26. IAM/basic ValidatePolicy are published no additional charge;
signed requests still need privacy/traffic authorization. S3 request/control tariffs,
versions and retained bytes require current confirmation before cost-bearing units.
An illustrative standard-rate workload totals about $0.00165 before uncertainties;
it is not a maximum, binding quote or account observation.

The $0.05 gross proposal and $0.02 operational stop remain **unapproved** and are
not AWS-enforced caps. Free-plan credits are not permission to spend. Verify remaining
credits/expiry privately; never upgrade automatically. Deployment needs its own
compute/storage/retained-resource budget. No billing budget/service was created.

Stop on unexpected identities/endpoints, refresh, truncation, changed source/policy,
unreviewed findings, denied evidence, expired window, ambiguous writes or budget
uncertainty. Keep private outputs/identifiers/state/plans in protected ignored
storage, never public review artifacts. Commands require bounded capture, TLS,
explicit destinations, no proxy/default-credential fallback and owned cleanup.

Reconcile ambiguous IAM/S3/apply outcomes with separately approved exact reads;
never replay writes blindly. Preserve partially applied resources/local state and
encrypted recovery copies. Boundary removal can expand privileges and is not a
safe automatic rollback. Revoke/expire grants before separately reviewing a
replacement; lock/state/version deletion and resource teardown each need approval.

## Offline commands and observed results

Windows PowerShell, Python 3.14.9, Ruff 0.17.2, Terraform 1.17.0 windows_amd64;
existing locked AWS provider 6.70.0. No installation, remote backend initialization,
account-connected plan, AWS CLI execution or authenticated AWS request occurred.
Public documentation browsing was unauthenticated and separate from account APIs.

| Exact command | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe` | Exit0; fmt passes; three roots validate; mock cases deployment5/bootstrap14/module2 = **21 passed**, no failures/errors/skips |
| `.venv/Scripts/python.exe scripts/review_source.py check` | Exit0; **171 project-owned Python files** parse using native and 3.13 grammar |
| `.venv/Scripts/python.exe -m pytest tests/test_state_boundary.py tests/test_state_operator_preparation.py tests/test_state_backend.py tests/test_review_source.py tests/test_private_command_runner.py -q --basetemp=.cache/f4-validation-plan/pytest-local --tb=short` | **231 passed in 11.60s**, normal local process access; synthetic fixtures only |
| `.venv/Scripts/python.exe -m pytest tests/test_infrastructure.py tests/test_host_preflight.py tests/test_terraform_authentication.py -q --basetemp=.cache/f4-validation-plan/pytest-safety --tb=short` | **87 passed in 2.88s**, normal local process access; offline security/storage/auth fixtures |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit0; no generated-contract drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | Exit0; **24/24 development +16/16 held-out =40/40** software baseline; no fitness/model-quality claim |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Exit0; five frozen assets match, live=false |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Exit0; historical F3-03A mock/reference artifact matches; its historical unratified labels do not supersede the later accepted count-aware protocol |
| `.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check` | Exit0; 50 authored cases, existing40development/10exposed comparison labels unchanged |
| `.venv/Scripts/python.exe scripts/evaluate_models.py --check` | Exit0; template50/50 hard/handling; fake and replay44/50 hard,50/50 handling each; six intentional hard failures each, no live/human quality evidence |
| `.venv/Scripts/ruff.exe check .` | Exit0; all checks pass |
| `.venv/Scripts/ruff.exe format --check src scripts tests infra experiments --no-cache` | Exit0; **174 files already formatted** |
| `git diff --check` | Exit0; only existing Git LF/CRLF notices, no whitespace errors |

Two failed environment/broad-scope attempts are recorded rather than omitted:

- The first focused pytest invocation without an override:179passed/52setup errors
  (WinError5 accessing the existing restricted `.cache/pytest`). A second invocation
  with `--basetemp=.cache/f4-validation-plan/pytest-offline --tb=short` also encountered
  denied temporary-directory access and session cleanup failure. Neither is a
  product assertion failure or pass. The exact231case rerun above passed with normal
  local access; no ACL/product/test safeguard was weakened.
- `.venv/Scripts/ruff.exe format --check .` returned1 because unchanged historical
  Markdown examples in `docs/development.md` and `docs/implementation/f1-04-handoff.md`
  would be reformatted. Left intact. The project's Python-source formatting scope
  above passed. No formatter write was used.

PowerShell syntax-only check extracted the runbook's18 fenced PowerShell blocks
and passed each to
`[System.Management.Automation.Language.Parser]::ParseInput(...)`: **18 blocks,
zero parse errors**. No command in a block was executed. This validates shell
syntax, not live AWS option/authorization/provider compatibility.

Equivalent exact local syntax-check sequence:

```powershell
$doc = Get-Content docs/planning/26-f4-aws-validation-and-deployment-runbook.md -Raw -Encoding UTF8
$blocks = [regex]::Matches($doc, '(?ms)^```powershell\r?\n(.*?)^```')
$totalErrors = 0
foreach ($block in $blocks) {
  $t = $null
  $e = $null
  [System.Management.Automation.Language.Parser]::ParseInput($block.Groups[1].Value, [ref]$t, [ref]$e) | Out-Null
  $totalErrors += $e.Count
}
if ($totalErrors) { throw 'document_powershell_parse_failed' }
```

Before/after raw-byte inventory comparison uses existing
`scripts/review_source.py:inspect()` and the initial453file manifest at
`.cache/f4-validation-plan/before.json`. The resulting preservation report is in
the same ignored directory: **PASS, all453original files byte-identical, zero
changed/missing originals, exactly the two documents below added**. No prior tested
ZIP/manifests are overwritten.

No frontend/PostgreSQL/browser/release drill rerun: this unit changes documentation
only, with no application/container/migration/contract changes. The frozen checks
and focused infrastructure regressions above are current offline evidence, not
fresh hosted-CI or account execution evidence.

## Files modified and Git diff summary

Only added in this milestone:

1. `docs/planning/26-f4-aws-validation-and-deployment-runbook.md` — phased runbook,
   current official references, exact future commands and proposed design gates.
2. `docs/implementation/f4-aws-validation-and-deployment-readiness-handoff.md` —
   findings, validation, source preservation and approval handoff.

All preexisting tracked/untracked work remains. These new docs are untracked;
ordinary `git diff` therefore does not yet display them. Compare them with
`git diff --no-index -- /dev/null <path>` for review (exit1 means differences).
Source/configuration/permission-scope changes in this milestone: **zero**. Ignored
local artifacts are test evidence and the preservation manifests, not AWS data.
AGENTS.md remains local/ignored. No staging, commit, push or review ZIP generation.

## Exact first operation proposed for later owner authorization

**A1a only:** one `aws sts get-caller-identity @F4AdminSts`, with document26's frozen
human-admin profile binding and regional STS endpoint, private Account/Arn/UserId
postconditions, no root/default/other identity, <=120s plus bounded cleanup, one
SDK attempt/no refresh or replay, and an attended30minute authorization window.
Prerequisite: reviewed private capture/egress/identity binding; the current disabled
runner is not activated by this proposal. No additional permission/mutation follows.

This operation has **not** been executed or authorized here. Its successful result
would not authorize state-user verification, IAM reads/validation, policy creation,
attachment, bucket bootstrap, remote init/locking or deployment. Stop for review.
