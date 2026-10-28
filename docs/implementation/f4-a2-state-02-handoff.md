# F4-A2-state-01 closure and state-02 offline preparation handoff

2026-10-26. **Offline only. No AWS request, private IAM/credential/cache inspection,
grant, S3/Terraform operation or live-executor activation. Stop for independent review.**

## Result, provenance and changes

[State-01 completion](f4-a2-state-01-completion.md) records this owner-attested live
result, not independently reproduced Codex execution:

```json
{"checkpoint":"F4-A2-state-01","result":"metadata_page_verified","policy_count":0,"mfa_verified":false,"http_request_count_verified":false}
```

It establishes only the reported complete page with zero directly attached managed
policies. Inline/group policies, boundaries and resource grants remain unverified.
Neither no effective permissions nor MFA/session/HTTP-count proof is inferred.
Historical preparation/NO-GO evidence remains unchanged; no past authorization transfers.

| File | Change |
| --- | --- |
| `docs/implementation/f4-a2-state-01-completion.md` | New sanitized owner-attestation record and limitations |
| `infra/aws/inline_policies.py` | New offline-only fixed ListUserPolicies command, private preparation/digest/claim and strict names-page validation |
| `tests/test_inline_policies.py` | New adversarial synthetic tests, actual local-preparation/capture blocks with synthetic inputs, native PowerShell JSON-text check and syntax-only parsing |
| [State-02 procedure](f4-a2-state-02-supervised-procedure.md) | New local-only preparation, independent approval gate, exact future invocation, private observation and sanitized reporting |
| This handoff | New decisions, evidence, limits and next authorization |
| `docs/planning/26-f4-aws-validation-and-deployment-runbook.md` | New status addendum only; existing text retained |

## Design and safety

The new helper has no process launcher/main/live flag and accepts no arbitrary action,
profile, target or endpoint. Its only command is ListUserPolicies for the fixed human
caller/state target/us-east-1/global IAM endpoint. Reuses reviewed state-01 private
I/O (<=64KiB), identity/binary/window/source checks and human-only environment, plus
the existing owned capture/Job Object in the future procedure. No shared package,
generic IAM executor, dependency or modification to the accepted executors is added.

State-02 uses a distinct record kind, source manifest, metadata field, environment
names and private directory/receipt/claim. It cannot adopt state-01 preparations.
Reuse of common metadata validation deliberately supplies an empty managed-policy
list to that validator; inline names use their own **40-name** bound, not the twelve
managed-policy limit. Both limits come from the approved inventory plan; neither is
an inferred AWS quota or approval for policy bodies.

Require exact private caller/target Account/Arn/path/UserId, same account/distinct
users, owner-attested A1a/A1b provenance, independently reviewed source/CLI hashes,
<=30-minute UTC window with >=5 minutes remaining, and a separately reviewed private
preparation digest binding all metadata. New exclusive durable claim before release;
partial/fsync/cancellation/restart/unknown delivery retains it. No retry/reset API.
Ownership is established before releasing the fixed command, bounded to 120s + <=10s
cleanup with 64KiB stdout/4KiB stderr. No new live process was released in this task.

Accept only strict JSON with **exact PolicyNames/IsTruncated fields**, explicit boolean
false, an array of <=40 distinct case-sensitive 1–128-character supported ASCII names
and the privately approved allowlist. Reject extra fields/tokens (even empty), missing
flags, truncation, wrong types, managed-policy response shapes, malformed/oversized
data and failed/stderr captures. No query/filter/paginator/continuation or body read.
Complete well-formed observations are private before allowlist checking; unexpected
valid names remain reviewable privately but stop without a success record. Malformed
data/stderr is not promoted to valid observation. Summaries expose only checkpoint,
result, count and unverified-MFA/HTTP flags. Empty is a limited inline-list finding.

## Native PowerShell preparation correction

Read-only local synthetic testing of the proposed array pipeline under Windows
PowerShell 5.1 found `@($text | ConvertFrom-Json)` could serialize back as wrapped
`value`/`Count` objects rather than the expected plain array. The state-02 procedure
therefore retains masked JSON **text** in the temporary private input and decodes it
with the existing strict Python parser before typed validation. It does not parse
arrays through PowerShell. Empty, single-name and multiple-name preparation paths
are tested, including the actual local-preparation Python block.

This observation concerns a local conversion expression, not an audit/disproof of
the owner's state-01 live result. Historical state-01 source/procedure is preserved;
it is not reused or silently patched for state-02. Source records do not show which
local terminal details were used by the owner. Do not infer or repeat AWS operations.

## Offline checks and observed results

Windows PowerShell 5.1/Python 3.14.9; no installation or AWS executable invocation.
All test identities, names, caches and captures are synthetic. Official public API
documentation review is distinct from signed account traffic or provider evidence.

| Exact command / check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_inline_policies.py tests/test_attached_policies.py -q --basetemp=.cache/f4-a2-state-02/pytest-focused --tb=short` | **112 passed in 312.48s**, before the four additional JSON-text preparation cases |
| `.venv/Scripts/python.exe -m pytest tests/test_inline_policies.py -q --basetemp=.cache/f4-a2-state-02/pytest-final --tb=short` | **57 passed in 179.82s**, including corrected local preparation/PowerShell serialization |
| `.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-a2-state-02/pytest-regressions --tb=short` | **260 passed in 12.40s**, run in isolation |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, original 24 development/16 held-out; software regression only |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **180 public Python files**, native and 3.13 grammar pass |
| `.venv/Scripts/ruff.exe check .` | Exit 0, all checks pass |
| `.venv/Scripts/ruff.exe format --check src tests scripts infra experiments` | Exit 0, **183 files** formatted |
| `git -c core.safecrlf=false diff --check` | Exit 0 |

Adversarial coverage: malformed/duplicate/missing/extra JSON, false flag type,
truncation/tokens, name type/length/ASCII/path/count/byte bounds, duplicate/unexpected
names, failed/cancelled/interrupted captures, source/binary/identity/provenance/window
mismatch, post-review identity/name tampering, config/credential/environment poisoning,
concurrent/restarted/partial/fsync-failed claims, cross-unit record rejection, persistence
failure and second-invocation prevention. Future capture blocks are run only after
capture is replaced with a synthetic function. PowerShell parses two blocks without
executing them; both embedded Python blocks parse with 3.13 grammar. Existing live
functions remain unconditional raises.
Local consistency checks verified the exact owner JSON and all **11 local links**
in changed documents/runbook. The raw-byte preservation check reconstructed the
original runbook by removing only the new addendum; no other original file changed.

Tests use normal local process access for the reviewed ACL/Job Object fixtures;
no protection or system policy was relaxed. Initial new-file formatting was normalized
before test evidence. A preliminary nested-shell JSON probe failed quoting before
execution; the explicit local `.cache/f4-a2-state-02/check-json.ps1` reproduced the
conversion behavior, and the regression suite tests the corrected JSON-text route.
No full application/PostgreSQL/frontend/browser rerun is claimed: no runtime/app/schema
change. No S3 or Terraform operation was run, including offline Terraform commands.

## Remaining blockers and next authorization

- **No state-02 live authorization.** Owner/reviewer must approve this exact source,
  procedure, caller/target private triples/path, binary/source pins, allowlist,
  separately retained private preparation digest, attended UTC window and retention.
  Prior successful identity/metadata reads and local receipts grant no new access.
- Fresh state-02 decision on native refresh/authentication traffic and Windows lack
  of OS-enforced egress containment is mandatory. No one-HTTP-request, fresh native
  identity or MFA proof is claimed. The list response does not identify caller/target;
  reviewed login source/fixed command remain trust assumptions. Cache contents were
  never inspected. A changed/expired session stops; no automatic login or fallback.
- Native CLI/schema/account compatibility with this new read remains unverified.
  Unsupported output, denial, privacy loss, changed pins, unexpected names, ambiguous
  delivery or cleanup failure stops. Do not relax validation, fetch a body, grant IAM,
  alter an allowlist/receipt and rerun, reset a marker or repeat using a fresh directory.
- Local owner-controlled encryption/ACLs and no concurrent source/config/identity
  changes are prerequisites. Hash/claim checks are not hostile-owner/OS protection
  or complete filesystem TOCTOU prevention. Buffer clearing is not secure RAM erasure.
- Count uncertain/failed claims as scheduled invocations against the proposed 40-call
  A2/A3 budget; owner tracks remaining capacity. No durable global inventory ledger or
  automatic closure is added. Forty returned names need not fit later body-read capacity.
- Group/boundary/resource grants and effective permissions remain unknown. A3 policy
  bodies, boundary validation/creation/attachment, bootstrap/provider identity separation,
  S3 compatibility, operational recovery and spending remain later separate gates.

Exact next proposal, only after independent review:

> Authorize state-02 only: one supervised initial-page IAM ListUserPolicies invocation
> by future-f4-human-admin targeting future-f4-state-operator, us-east-1,
> https://iam.amazonaws.com. Bind exact private identities/path, reviewed binary/source
> hashes, name allowlist and separately approved preparation digest, <=30-minute UTC
> window, 64KiB/4KiB capture, 120s execution/10s cleanup and one durable claim. Explicitly
> accept/reject state-02 native refresh and no-Windows-egress-containment assumptions.
> Permit private observation/validation and sanitized reporting only. No retry, paging,
> login, body read, extra IAM operation/grant, S3/Terraform, spending or live automation.
> Uncertainty stops for fresh owner review.

Required service permission is `iam:ListUserPolicies` on the exact privately approved
state-user ARN/path, using already established human authority. No grant is installed.
Next task is independent review, not execution or preparation of a later operation.
On interruption retain claims/private evidence, verify owned cleanup and request a
fresh decision; no IAM rollback or automatic deletion is warranted for this read.

## Preservation and review ZIP

Starting inventory: **475 public files**. Only the runbook addendum changes an existing
file; its earlier body is preserved and the other **474** originals remain byte-identical.
Five additions make **480 public files**. Application, accepted helper/executor/policy
code, baseline, historical reports and unrelated worktree changes remain intact.
AGENTS.md remains ignored/unchanged; no commit or push.

```text
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a2-state-02/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-a2-state-02/review/source-manifest.json --archive .cache/f4-a2-state-02/review/future-training-f4-a2-state-02-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-a2-state-02/review/source-manifest.json --archive .cache/f4-a2-state-02/review/future-training-f4-a2-state-02-review.zip
```

The ZIP contains only the final public snapshot and embedded raw-byte SHA-256 manifest.
Every source member must match working-tree bytes. Credentials, private IAM/identity
records, login caches, `.aws`/ignored `.cache`, AGENTS.md, dependencies, Terraform state/
plans/private inputs are excluded. Public-source credential-pattern scanning supplements
path exclusions; it is not universal secret detection. No private artifact is opened
for packaging; sanitized verification/hash evidence stays beside the ZIP in cache.
