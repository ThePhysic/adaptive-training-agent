# F4-A1b completion and F4-A2 offline preparation handoff

2026-10-26. **Documentation-only work. No AWS/CLI account request, S3 or Terraform
operation performed. No new live authority. Stop for independent review.**

## Outcome and evidence provenance

[A1b completion](f4-a1b-completion.md) records the exact owner-attested result:

```json
{"checkpoint":"F4-A1b","result":"identity_matched","mfa_verified":false,"http_request_count_verified":false}
```

The owner reported a separately authorized human GetUser reference read, private
state identity verification/storage and a separately authorized state-profile STS
match. Codex did not reproduce execution, inspect private artifacts or verify MFA,
HTTP count, native refresh/containment or capture implementation. No IAM modification,
S3/Terraform operation or deployment was reported. This does not authorize A2 or any
later read/mutation. Historical preparation and NO-GO records remain untouched.

## Changes and architectural decision

| File | Change |
| --- | --- |
| `docs/implementation/f4-a1b-completion.md` | New sanitized completion/provenance/limitations record |
| `docs/implementation/f4-a2-iam-inventory-preparation.md` | New staged metadata-read matrix, exact future vectors, privacy/bounds/pagination/authorization contract and later policy-closure gates |
| This handoff | New validation, next operation and review-package record |
| `docs/planning/26-f4-aws-validation-and-deployment-runbook.md` | New latest-status addendum only; earlier body/status/proposal retained |

The smallest next milestone is **offline A2-state-01 single-read capture preparation**,
followed by separate approval of one initial attachment-metadata page. Reuse existing
private capture and identity primitives after source review; do not generalize the
fixed STS/reference tools or enable the generic executor. No runtime, test, dependency,
policy generator, IAM grant, migration, application, baseline or frontend change is
necessary for this planning checkpoint. No duplicate evaluation/infrastructure tool.

A2 remains metadata-only. Full baseline inventory proposes three specifically named
users x four reads plus exact proposed-boundary GetPolicy = **13** invocations; the
separately optional human MFA metadata read would make **14**. This is not one blanket
authorization. A3 body/group closure starts only after exact metadata targets are
reviewed. The accepted 40-call A2/A3 / four-group / twelve-policy caps are retained;
they may force an incomplete finding rather than automatic scope expansion.

## Offline validation

Existing Windows PowerShell 5.1/Python 3.14.9 environment; no installation or native
AWS executable invocation. Public official documentation review is not account API
access. Tests below are synthetic/static/loopback evidence, not AWS IAM evaluation.

| Exact command / check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-a1b-closure-a2/pytest-normal --tb=short` | **130 passed in 4.06s**, normal local process access for existing ACL fixtures; no protection/ACL relaxation |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, 24 development/16 held-out; frozen software regression only |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **176 Python files**, native and 3.13 grammar pass |
| `powershell -NoProfile -NonInteractive -File .cache/f4-a1b-closure-a2/validate-docs.ps1` | ParseInput/AST only: **22 PowerShell blocks**, zero syntax errors; **14 proposed A2 command vectors**, fixed IAM vocabulary/common arguments; no AWS block executed |
| `git -c core.safecrlf=false diff --check` | Exit 0 |

The initial pytest command used the same file list with
`--basetemp=.cache/f4-a1b-closure-a2/pytest` and exited 1 because the sandbox could
not access pytest's protected temporary directory (WinError 5), including teardown.
It is not passing test evidence. The normal-access rerun above passed; no source or
security policy was changed to obtain it. An initial parser check piped through
PowerShell stdin emitted no result, so it was not counted as verification; the
explicit parse-only script above produced the stated counts.

Additional local consistency checks verify exact owner JSON, local document links,
unconditional raises in both disabled live executors, original-source preservation
and ZIP byte identity. No new mirrored implementation tests were added for reversible
documentation changes. No full application, PostgreSQL, frontend/browser, native AWS
or Terraform suite is claimed rerun. Terraform operations were excluded by scope.

## Remaining blockers and recovery

1. **No live A2 permission.** Owner must approve exact caller/profile, private
   Account/Arn/UserId and target ARN/path, reviewed binary/source, UTC window and
   capture/retention. Owner-attested A1 results do not prove a current session or
   permit another service action. Do not repeat either STS checkpoint automatically.
2. **Single-read capture/page validator not implemented for IAM inventory.** Fixed
   STS/reference tools must not be repurposed. The next narrowly scoped offline task
   should prepare/review that assembly and synthetic malformed/truncated/error,
   ownership/source/cancellation/duplicate-claim tests before real execution.
3. **Fresh A2 authentication/network decision required.** Native refresh, no OS
   egress containment, no hard HTTP-count proof and unverified session MFA remain.
   If unacceptable, stop for another proposal; do not add endpoints or lower TLS.
4. **Inventory and effective authority unknown.** GetUser/attachments/groups and
   proposed-policy presence have not been measured here. AccessDenied, truncation,
   unknown policy/group/path, missing required user, stale/concurrent changes or
   exhausted caps means incomplete/stop, not absence/safety. Do not traverse names
   or paginate automatically. Policy/group bodies require later named A3 approvals.
5. **Boundary installation gates remain.** Confirm real current attachments, old
   delegation state and complete approved policy closure; then separately validate
   the real boundary document, create a customer-managed policy, attach and verify.
   No inline-policy substitute or automatic boundary removal/replacement. A ceiling
   is not a grant and metadata alone cannot exclude resource-based permissions.
6. **Later bootstrap/deployment gates remain.** Human-bootstrap principal/tooling
   correction, distinct nonadmin provider identity and host-role escalation controls,
   actual S3 prefix/missing-object behavior, state custody/recovery and numerical
   spending approvals are not resolved by successful identity or metadata reads.

Read-only uncertainty needs private review/owned cleanup, not IAM rollback. Preserve
claims and private bounded evidence after interruption/unknown delivery. No retry,
automatic login, permission expansion, resource mutation or cleanup of user data.
No financial authority, paid service, account upgrade or cloud resource is introduced.

## Exact next proposed AWS authorization — future only

After the capture prerequisite is independently accepted:

> Authorize **A2-state-01 only**, one supervised initial-page
> `iam:ListAttachedUserPolicies` targeting `future-f4-state-operator`, caller profile
> `future-f4-human-admin`, us-east-1, https://iam.amazonaws.com. Bind exact private
> caller/target account and ARN/path, approved source/binary hashes and <=30-minute
> attended UTC window. Require selected-only login configuration, 120s execution/
> <=10s cleanup, <=64KiB stdout/4KiB stderr, durable one-shot claim and private
> verification/reporting. Explicitly decide A2 refresh/no-OS-containment assumptions.
> No pagination continuation, retry, login, extra IAM read, permission grant,
> S3/Terraform, deployment, spending or live-executor activation. Stop on uncertainty.

Exact command and later separately scoped vectors are in
[A2 preparation](f4-a2-iam-inventory-preparation.md). Service permission is
`iam:ListAttachedUserPolicies` on the exact privately approved state-user ARN. No
automatic grant is proposed. If existing human permissions are insufficient, report
the denial and purpose rather than modifying IAM. Approval of this read does not
approve the other three state reads, any other user or proposed-policy/MFA lookup.

**Recommended next Codex task:** offline A2-state-01 fixed human capture and strict
single-page validator preparation, using synthetic fixtures only. Independent review
and fresh owner authorization must precede any account request. No new AWS operation
is authorized by completion of this handoff.

## Preservation and sanitized review ZIP

Starting public-source inventory: **468 files**. Only the runbook's new addendum
changes an existing file; the other **467** remain byte-identical, and removing that
addendum reconstructs the original runbook exactly. Three new documents make **471
public files**. Existing worktree changes, historical policy/baseline files and all
executable source remain intact. AGENTS.md stays ignored/unchanged.

Local review commands (no account or Terraform activity):

```text
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a1b-closure-a2/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-a1b-closure-a2/review/source-manifest.json --archive .cache/f4-a1b-closure-a2/review/future-training-f4-a1b-completion-a2-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-a1b-closure-a2/review/source-manifest.json --archive .cache/f4-a1b-closure-a2/review/future-training-f4-a1b-completion-a2-review.zip
```

The ZIP includes only public working-tree files and its embedded raw-byte SHA-256
manifest. Every source member must match the final working tree. Credentials,
private identities, login caches, `.aws`, ignored `.cache` evidence, AGENTS.md,
dependencies and Terraform state/plans/private inputs are excluded. A public-source
credential-pattern scan supplements path/inventory checks; it is not a universal
secret detector. Archive hash and sanitized verification results are kept beside
the ZIP under ignored cache. No private artifact is opened to create the package.
