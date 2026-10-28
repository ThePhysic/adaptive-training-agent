# F4-A2 group-policy metadata — Offline preparation handoff

2026-10-26. **Offline only. No live authorization requested/executed. No AWS call,
private-record inspection, IAM grant/mutation, S3/Terraform operation, paid API,
executor activation, installation, commit or push. Stop for independent review.**

## State-03 evidence and security conclusions

[Stopped-observation record](f4-a2-state-03-stopped-observation.md) preserves exactly:

```json
{"checkpoint":"F4-A2-state-03","result":"stopped","outcome_uncertain":true}
```

Owner-attested local inspection reported preparation.json, preparation.sha256,
attempt.claim and observed-groups.json present, result.json absent. The retained
structurally valid observation had one group, recognized as FutureStateOperators;
empty approved-group allowlist caused the stop. **Not a state-03 allowlist pass.**
The result, claim and old allowlist are unchanged; no rerun or retrospective approval.

Owner reports the group's only member is the state operator and recalls assigning
SignInLocalDevelopmentAccess during setup. Neither membership enumeration nor its
managed/inline type, ARN, contents or actual permissions was independently verified.
This task fabricates none of those. State-01's zero direct managed user attachments
and state-02's zero inline user policies do not rule out inherited group authority.
The boundary and effective permissions remain unverified. MFA, HTTP count, native
refresh/authentication and Windows egress limitations remain; no historical NO-GO
or evidence is rewritten. Codex did not open the old private observation/identities.

## Exact changed files and architecture

| File | Change |
| --- | --- |
| `docs/implementation/f4-a2-state-03-stopped-observation.md` | New owner-attested stopped observation, artifact-presence report and limitations |
| `infra/aws/group_policy_inventory.py` | Two fixed offline interfaces, Managed and Inline; shared private mechanics with distinct units/response contracts/record kinds; no launcher or CLI selector |
| `tests/test_group_policy_inventory.py` | Parameterized independent-operation synthetic/adversarial tests, mocked future capture and local preparation, parse-only PowerShell |
| [Managed supervised procedure](f4-a2-group-managed-01-supervised-procedure.md) | New ListAttachedGroupPolicies-only preparation/approval/capture/review protocol |
| [Inline supervised procedure](f4-a2-group-inline-01-supervised-procedure.md) | New ListGroupPolicies-only preparation/approval/capture/review protocol |
| This handoff | Local-resolution procedure, sequencing, evidence and blockers |
| `docs/planning/26-f4-aws-validation-and-deployment-runbook.md` | Additive latest-status note; earlier text preserved |

There are two concrete consumers of the shared **local-only** mechanics. No abstract
multi-service platform or generic IAM launcher: each interface's command signature
accepts only the pinned executable, no action/target/profile/endpoint argument.
The future documents select literal Managed or Inline, never a user/env-driven
operation switch. Unknown subclasses or changed contract constants are rejected
before command construction. Neither triggers the other. Existing helpers/executors/policies
are unmodified; no broader live permission or new dependency/service is introduced.

Reuse: existing private ACL/path/exclusive fsynced <=64KiB I/O, selected-only human
login config/environment, binary/cache-location/UTC checks, exact group identity
validator, managed-policy ARN validator, inline-name validator and Windows owned
capture primitive. Separate preparation kinds, directories, environment names,
digests and claims prevent cross-unit/state-03 record adoption. Common source pins
include both reviewed interfaces/procedures and dependencies; editing either invalidates
existing source expectations, not authority to execute the other.

## Independent safeguards

Caller only future-f4-human-admin; group only FutureStateOperators; us-east-1/global
IAM HTTPS endpoint. Exact private caller Account/Arn/path/UserId plus group Name/Arn/
Path/GroupId in the same account, new prospective group-review provenance, reviewed
binary/source hashes, new <=30-minute UTC window with >=5 minutes remaining and
separately approved private preparation digest. Neither response proves its caller
or group; private bindings/native login are trust assumptions. Group recreation or
path/identity drift cannot be detected from these policy-list responses alone.
Owner freezes IAM/local configuration changes; uncertain/stale identity blocks the
operation. No automatic GetGroup or repeated identity request resolves it.

Policy expectations have a required independent-provenance attestation: nonempty
allowlists require owner_independently_reviewed, empty requires owner_explicit_deny_all.
Labels are owner attestations, not cryptographic verification of external provenance.
No default when expectations are absent and no name-based inference of policy type.

Each unit: dedicated durable exclusive claim before process release; partial/fsync/
failure/cancellation/restart retains it; no retry/reset. Reviewed Job Object ownership
before release, 120s execution + <=10s cleanup, 64KiB stdout/4KiB stderr; one initial
page only. Selected-only human config, empty shared/legacy credentials, IMDS disabled,
allowlisted environment, no inherited AWS/TF/proxy/Python/PATH/CA/process override.
Native retry setting AWS_MAX_ATTEMPTS=1 does not prove HTTP count or prevent auth
traffic. Neither credentials nor preparation enables a live executor.

Managed: exact AttachedPolicies/IsTruncated, <=12 unique managed ARNs, exact entry
PolicyName/PolicyArn; existing supported name/path/length, aws namespace for AWS-managed
or exact private account for customer policies, matching basename; duplicate names/ARNs
stop. Inline: exact PolicyNames/IsTruncated, <=40 distinct case-sensitive supported
ASCII names 1–128 characters. Both require boolean false, duplicate-key-safe JSON;
no extra fields/tokens even empty, missing flags, wrong response kind, malformed or
oversized output. No pagination, filter, traversal, policy-body read or automatic call.

Well-formed complete but unexpected observations are retained privately before
rejection; no success record. No raw stderr/malformed data as verified metadata.
Only finite unit/result/count/MFA-unverified/HTTP-unverified summaries escape after
private persistence. Buffer clearing is not secure-erasure proof. Claims/digests are
local operator safeguards, not hostile-owner protection, hard delivery proof or OS
egress containment. Parent global A2/A3 limits (40 scheduled invocations, four groups,
twelve managed ARNs) remain owner-attested ledgers outside these single-unit records;
submitted full managed allowlist <=12 is enforced, not an independent account audit.

## Safe owner-only local resolution — no AWS operations

These are **future owner-local review steps**, not performed by Codex in this task.
Do not upload private inputs or ask Codex to inspect old files.

1. Retain original state-03 directory/result/claim unchanged. In a private local
   terminal with no transcript/export, the owner may review their already retained
   observation and original IAM setup records. No AWS call, login/config command,
   cache/token access or membership enumeration is required/authorized by this plan.
2. Independently assess the capture provenance/caller/account and setup recognition.
   If the owner cannot attest that the **exact** group Arn/path/GroupId belongs to
   FutureStateOperators in the intended account, mark identity unresolved and stop.
   Do not construct an ARN from the name, guess a root path or substitute an ID.
   A structural observation alone is not complete trust proof. Any additional account
   verification requires a different authorization, not a hidden prerequisite here.
3. If satisfactory, the owner can prospectively approve those four exact group fields
   **only for a new future metadata-read unit**, supplying them through masked prompts
   in a new directory. Record provenance owner_prospectively_reviewed_group. Do not
   edit/copy the state-03 preparation as a permit, replace its empty allowlist, delete
   its claim, create result.json or re-label that stop as success.
4. Separately establish policy expectations from independent owner-reviewed setup/
   existing authoritative records. A recollection of SignInLocalDevelopmentAccess
   by name is insufficient to establish managed-versus-inline, exact ARN or contents.
   Do not auto-fill either allowlist from that recollection or from the response that
   will be checked. No speculative ARN or permissions document is generated.
5. Missing authoritative nonempty expectations is a **readiness blocker**. Do not
   silently treat missing as empty. An owner may instead explicitly choose/approve
   an empty deny-all expectation for a future separately authorized observation:
   any nonempty well-formed response then stays private and **stops**, not passes.
   This preserves validation and does not classify the named setup policy. It is
   neither default behavior nor an authorization request in this task.
6. An unexpected policy observed later must not be rescored against itself or an
   edited allowlist. Preserve that stopped unit and seek separate review for any
   prospective policy identity/body work. No automatic repeat of the metadata query,
   body request, policy change or permission expansion is included.

The new procedure's local preparation reads only newly supplied metadata and the
public reviewed manifest. It never opens the state-03 observation, real config or
cache contents. Use masked JSON text to avoid the reviewed PowerShell 5.1 array
wrapping problem; strict Python decodes it. No live step is necessary to test this.

## Authorization sequence and unresolved decisions

| Checkpoint | Scope / gate | Explicit exclusions |
| --- | --- | --- |
| Current milestone | Offline record, two source/procedure contracts, synthetic tests and independent review | No account requests or live authorization solicitation |
| Owner-local resolution | Private prospective exact group/expectation review as above, if independently accepted | No state-03 retroactive pass, claim deletion, replay, policy-type inference or extra IAM read |
| Future managed authorization | One ListAttachedGroupPolicies initial-page invocation only; fresh managed bindings/receipt/window/risk decision | Does not authorize inline or bodies |
| Future inline authorization | One ListGroupPolicies initial-page invocation only; fresh inline bindings/receipt/window/risk decision | Does not authorize managed or bodies |
| Later independent review | Interpret complete/private metadata and plan specifically named policy closure if separately authorized | No automatic GetPolicy/GetPolicyVersion/GetGroupPolicy, traversal or mutation |

No dependency automatically executes the other operation. Either can remain blocked
or unapproved independently. Recommend owner review after each before considering
another; pages are not an atomic IAM snapshot. Missing group authority/expectations,
source/procedure acceptance, private encryption/ACLs/retention, fresh caller/session
attestation, <=30-minute window and **per-operation** native refresh/Windows-egress
decision are unresolved prerequisites. Earlier risk exceptions do not transfer.

Any future live approval must name the exact unit/action/caller/group ARN/path/ID,
private caller identity, independently approved policy expectations, binary/source
pins, private preparation digest, time/capture/privacy/retention bounds and risk
decision. No retries, pagination, login, body reads, other unit, IAM change/grant,
S3/Terraform, spending or live automation accompanies it. This is a boundary
specification, **not a request for approval**. Stop now for independent review.

## Offline tests and measured evidence

Windows PowerShell 5.1/Python 3.14.9; no installation or AWS executable invocation.
Public official API/CLI docs were reviewed, not account traffic. All tests use fake
account IDs, GroupIds, unrelated synthetic policy names/ARNs and private fixture
directories. No fixture asserts the recalled policy's actual type or permissions.
Both official API pages and the inline CLI reference were retrieved. Direct retrieval
of the managed CLI reference timed out twice; its link is a reference, not evidence
of a successful native CLI probe. Managed semantics come from the official API;
routine CLI options reuse the reviewed CLI conventions. Native compatibility remains
unverified. No account permission or network gate was expanded to resolve that fetch.

| Exact command/check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_group_policy_inventory.py -q --basetemp=.cache/f4-a2-group-policy/pytest-focused --tb=short` | **101 passed in 261.08s**, before adding the closed-contract guard/case |
| `.venv/Scripts/python.exe -m pytest tests/test_group_policy_inventory.py -q --basetemp=.cache/f4-a2-group-policy/pytest-final --tb=short` | **102 passed in 260.33s** |
| `.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-a2-group-policy/pytest-regressions --tb=short` | **260 passed in 13.49s**, isolated run |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, frozen 24 development/16 held-out; software regression only |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **184 public Python files**, native and 3.13 grammar pass |
| `.venv/Scripts/ruff.exe check .` | Exit 0 |
| `.venv/Scripts/ruff.exe format --check src tests scripts infra experiments` | Exit 0, **187 files** formatted |
| `git -c core.safecrlf=false diff --check` | Exit 0 |

Focused coverage: fixed commands/forbidden arguments, empty/nonempty pages, expected
limits and exact byte boundary, AWS/customer managed namespace handling, inline-name
validation, malformed/duplicate/missing/extra/wrong-kind responses, flags/tokens,
unexpected retention, caller/group/source/binary/window/provenance mismatch, absent or
same-response expectations, implicit empty rejection, concurrent/restarted/partial/
failed-fsync claims, cross-unit rejection, private digest tampering, poisoned config/
environment, failed/cancelled captures, actual documented capture with synthetic
replacement installed first, persistence/interruption/replay and independent local
preparation with empty/nonempty JSON text. Both procedures parse without execution;
both embedded Python blocks per document have 3.13 grammar. Neither live executor
can be activated; existing bodies remain unconditional raises.
Final consistency checks matched the exact original stopped JSON, resolved **17 local
links**, and verified that removing only the new runbook addendum reconstructs its
original bytes; every other pre-existing public file remains unchanged.

Normal local process access is used for existing private ACL/Job Object fixtures,
no ACL/security policy relaxation. No full application/PostgreSQL/frontend/browser
or Terraform suite rerun is claimed: runtime/schema/UI/policies are unchanged and
Terraform operations are prohibited. Real IAM identity/output/permission/authentication
behavior, current boundary/effective authority and hard network/request-count/MFA
guarantees remain unverified. Conservative schema/path checks may reject provider
variations; stop for review rather than weaken them or expand IAM. Unavailable or
ambiguous native results require retained claims, owned cleanup and separate review,
never refunds/replay or automatic evidence deletion. Local hashes are not complete
filesystem TOCTOU or malicious-local-owner protection.

## Preservation and sanitized review ZIP

Starting inventory **485 public files**: only a runbook status addendum changes an
original; removing it reconstructs the old body byte-for-byte. The other **484**
originals, application/accepted helper/policy/baseline/historical records and unrelated
worktree changes remain intact. Six additions yield **491 public files**. AGENTS.md
stays ignored/unchanged; no commit or push.

```text
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a2-group-policy/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-a2-group-policy/review/source-manifest.json --archive .cache/f4-a2-group-policy/review/future-training-f4-a2-group-policy-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-a2-group-policy/review/source-manifest.json --archive .cache/f4-a2-group-policy/review/future-training-f4-a2-group-policy-review.zip
```

The ZIP contains only final public working-tree files and the embedded raw-byte
SHA-256 manifest. Every source member must match working-tree bytes. No private
IAM/identity records, credentials/login caches, `.aws`/ignored `.cache`, AGENTS.md,
dependencies or Terraform state/plans/private inputs. Credential-pattern scan of
public source supplements path exclusions, not universal secret detection. No private
artifact is opened for packaging; verification/hash evidence stays beside the ZIP.
