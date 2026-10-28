# F4-A2-state-01 — Offline capture and validation handoff

2026-10-26. **Prepared for independent review. No AWS request, real identity/cache
inspection, permission grant or live-executor activation. Stop after this unit.**

## Result and files

Implemented a single-purpose offline preparation/response boundary for one future
human-admin ListAttachedUserPolicies read of the state operator. The actual future
supervised capture assembly is a reviewed documentation block, not an executable
entrypoint or environment-controlled live switch. Existing STS/reference executors,
generic live denial, policy generators, application and historical evidence remain
unchanged. No new service, dependency, SDK, credential mechanism or IAM capability.

Four additions only:

| File | Purpose |
| --- | --- |
| `infra/aws/attached_policies.py` | Fixed command, private preparation/source/binary/window/identity checks, separately reviewed private-digest binding, one-shot claim and strict complete-page validation. No process launcher |
| `tests/test_attached_policies.py` | Synthetic positive/adversarial cases, claims/concurrency/restart/persistence faults, actual procedure assembly exercised with a synthetic capture replacement and syntax-only PowerShell parsing |
| [Supervised procedure](f4-a2-state-01-supervised-procedure.md) | Exact local preparation, independent approval checkpoint, one future fixed bounded invocation, private observation and finite sanitized reporting |
| This handoff | Decisions, checks, limitations, review package and next authorization |

## Security and validation contract

- Fixed vocabulary: `iam list-attached-user-policies --user-name future-f4-state-operator`,
  profile `future-f4-human-admin`, us-east-1, `https://iam.amazonaws.com`. No action,
  target, profile, pagination, endpoint, filter or extra-argument API. Executable
  path is separately pinned and re-attested; no PATH or alternative identity fallback.
- Exact private caller and target Account/Arn/path/UserId shapes, same account,
  distinct IAM users and explicit owner-attested A1a/A1b provenance are required.
  The approved preparation digest binds the **entire** metadata set, including
  UserIds, paths, allowlist, window and source map. Owner supplies that digest from
  separate private review, not a fresh computation used as its own expectation.
  Provenance labels/digests are not independently authenticated permits.
- Reuse existing human/state local validators, private ACL/path checks, binary
  re-attestation and selected-only configuration/environment construction. Source
  hashes are supplied from the independently reviewed public ZIP manifest, not
  silently accepted from the current source at launch. <=30-minute UTC window with
  >=5 minutes remaining; source/binary/config/private digest rechecked before claim.
- Private preparation/observation reads and exclusive writes are <=64KiB with fsync,
  no overwrite or retry. Login-cache **location** is explicit; no token/cache contents
  read or copied by preparation. Human-only selected config, empty legacy/shared
  credentials, disabled IMDS and allowlisted environment drop inherited AWS/proxy/
  TF/Python/PATH/CA/credential-process settings. Native refresh remains a risk decision.
- A new durable exclusive claim precedes process release. Partial/failed fsync,
  cancellation, restart and uncertain delivery never release/reuse it. Future capture
  reuses reviewed Windows Job Object ownership, 120s execution + <=10s cleanup,
  64KiB stdout/4KiB stderr, one command, native `AWS_MAX_ATTEMPTS=1`, no shell retry.
  Claims are local operator safeguards, not immutable authority or HTTP-send proof.
- Strict JSON (including duplicate-key rejection); exact two-field top level;
  `AttachedPolicies` array <=12; explicit boolean `IsTruncated:false`; exact two-field
  policy entries; documented bounded ASCII names and supported paths, matching ARN
  basename, aws/iam/no-region policy ARN, AWS-managed `aws` namespace or exact private
  customer account. Duplicate name **or** ARN rejects, including same-name policies
  from different namespaces. This deliberate ambiguity rule is stricter than service
  validity. Unsupported unusual paths/partitions stop; no silent schema relaxation.
- Any pagination token/extra field, malformed/truncated/oversized/failed response,
  unexpected policy or output persistence failure stops. No subsequent page/body/
  group/policy/user lookup. Allowlisted entries may be absent; empty does not prove
  no effective permissions. Membership/inline/boundary/body closure remains later.
- Well-formed complete observations are saved privately before allowlist comparison
  so unexpected valid entries can be reviewed without replay. They are **unapproved
  observations**, not success or policy authority. Malformed/truncated/unsupported
  observations and stderr are not saved as valid metadata. Only a finite success
  summary escapes after private persistence; all raw capture buffers are cleared.
  Clearing buffers is not secure-memory-erasure proof. No policy/account identifiers,
  raw exceptions or private preparation digest enters public summaries/logs.

## Verification

All evidence below is **offline/synthetic**. Windows PowerShell 5.1 and Python 3.14.9;
no installation or native AWS executable invocation. Real selected-cache compatibility,
AWS response/permission behavior, MFA and HTTP counts were not measured. Public
official documentation was reviewed; no account API endpoint was invoked.

| Exact command / check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_attached_policies.py -q --basetemp=.cache/f4-a2-state-01/pytest-first --tb=short` | **54 passed in 120.09s** before five further integrity/boundary cases were added |
| `.venv/Scripts/python.exe -m pytest tests/test_attached_policies.py -q --basetemp=.cache/f4-a2-state-01/pytest-final --tb=short` | **59 passed in 149.71s** |
| `.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-a2-state-01/pytest-regressions-final --tb=short` | **260 passed in 12.69s**, isolated unchanged-suite rerun |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**, original 24 development/16 held-out; software regression only |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **178 Python files**, native and 3.13 grammar pass |
| `.venv/Scripts/ruff.exe check .` | Exit 0, all checks pass |
| `.venv/Scripts/ruff.exe format --check src tests scripts infra experiments` | Exit 0, **181 files** formatted |
| `git -c core.safecrlf=false diff --check` | Exit 0 |

The new suite tests correct empty/mixed AWS/customer pages, 12-entry and 64KiB
boundaries, foreign accounts/partitions/services, malformed/duplicate/missing/extra
fields, bad policy names/paths/basenames/lengths, truncation/tokens, unexpected policies,
private identity/source/binary/window/provenance mismatch, post-review private UserId/
ARN/allowlist changes, poisoned config/environment, failed/stderr commands, cancellation,
interruption, result-write failure, partial markers, failed fsync, concurrent claims,
restart and duplicate execution. Documented future capture is replaced **before**
executing its Python block in tests; no AWS command is released. Both PowerShell
blocks parse without execution and embedded Python parses under 3.13 grammar.

Tests requiring native private ACL/Job Object checks used normal local process access;
no ACL or machine security setting was weakened. Initial lint/format findings in new
files were corrected before acceptance runs. One earlier existing regression run
(`pytest-regressions`, same file list) produced **259 passed/1 failed in 12.25s**:
`test_owned_descendants_terminated_after_barrier_and_unrelated_sibling_survives[cancelled]`
read an empty `spawned.json`. Source inspection shows cancellation gates on path
existence while the child uses non-atomic `write_text`, allowing termination between
creation and JSON completion. This is an existing test-marker race, not evidence of
unauthorized traffic or failed policy validation. It remains unchanged; the isolated
260/260 rerun passed. Do not claim the fixture race is fixed or all attempts passed.

No full application/PostgreSQL/frontend/installed-browser suite is claimed rerun:
application code and runtime contracts are unchanged. No S3/Terraform operation was
performed, including no Terraform offline test invocation in this milestone.

## Limitations and owner prerequisites

1. **Live execution remains unauthorized.** Independent source/procedure review and
   fresh explicit owner approval are required. No credentials, flags, claim or receipt
   can enable an automated live executor; the new module has no launcher or main CLI.
2. Privately supply authoritative A1a caller/A1b target bindings and a reviewed policy
   allowlist; Codex must not inspect them. Existing owner records are attestation,
   not real-time proof. The list response itself proves neither caller nor target
   identity; trust rests on reviewed native login selection and fixed arguments.
3. Fresh A2-specific acceptance/rejection of native credential refresh/authentication
   traffic and Windows no-OS-egress-containment limitations is mandatory. A1 exceptions
   do not transfer. No hard HTTP-count or MFA proof; service retry suppression is not
   authentication/network containment. Cached session contents remain uninspected.
4. Owner-controlled encrypted storage, private ACLs, reviewed source/CLI, no concurrent
   source/config/identity changes, no transcription/export and a bounded attended
   window are prerequisites. Hash checks are not protection against an actively
   malicious local owner/administrator or all filesystem TOCTOU attacks.
5. Raw stderr and malformed output are intentionally not exported or retained as
   valid observations. Further diagnosis after a denial/unsupported real shape may
   require a separately reviewed private diagnostic procedure and fresh authorization;
   never relax validators, add IAM grants or automatically repeat the request.
6. One claim consumes this unit's scheduled invocation even on uncertainty; owner
   maintains the proposed overall 40 A2/A3-call ledger. No multi-unit authority/ledger
   or automatic next-step traversal is implemented. Twelve allowed policies is the
   existing global ceiling, not permission to ignore previously observed usage.
7. The existing synthetic descendant test has a documented marker-read race. Its
   source was preserved; later test-hardening review can address it separately.
8. Later A2/A3 inventory/closure, real boundary validation/installation, bootstrap
   tooling principal separation, provider IAM escalation, actual S3 compatibility
   and spending approvals remain unfulfilled gates. No new authority follows a pass.

On failure, retain preparation, claim and private observations; ensure owned process
cleanup, report stopped/uncertain, and obtain a fresh decision. Do not reset a claim,
make a fresh directory as automatic retry, login, mutate IAM, or delete user evidence.
Agree retention/deletion privately; no automatic cleanup or boundary rollback.

## Exact next proposed authorization — not granted here

> Authorize one owner-supervised A2-state-01 initial-page ListAttachedUserPolicies
> invocation only, caller future-f4-human-admin, target only future-f4-state-operator,
> us-east-1, https://iam.amazonaws.com. Bind exact private caller/target identity
> triples, reviewed CLI/source hashes, allowlist and separately approved private
> preparation digest, <=30-minute UTC window, 64KiB/4KiB output caps, 120s execution/
> <=10s cleanup and durable one-shot claim. Explicitly decide native refresh and
> Windows no-egress-containment assumptions for this unit. Permit private observations,
> validation and finite sanitized reporting only. No retry, pagination, extra read,
> login, permission grant, S3/Terraform, spending or generic/live-executor activation.
> Any failure, uncertainty or changed binding stops for fresh owner review.

Exact service permission is `iam:ListAttachedUserPolicies` on the privately approved
state-user ARN including path. No new grant is proposed or installed. Operator
procedure and official source references are in the linked procedure. Next task is
independent review; only then may the owner separately authorize that named request.

## Source preservation and sanitized review package

Starting public inventory: **471 files**. All remain byte-identical; the four additions
above produce **475 public files**. Historical records, all unrelated working-tree
changes, existing executors, policy/boundary code and frozen baseline are preserved.
AGENTS.md remains ignored and unchanged.

Local-only packaging commands:

```text
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a2-state-01/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-a2-state-01/review/source-manifest.json --archive .cache/f4-a2-state-01/review/future-training-f4-a2-state-01-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-a2-state-01/review/source-manifest.json --archive .cache/f4-a2-state-01/review/future-training-f4-a2-state-01-review.zip
```

The archive contains the public snapshot and embedded raw-byte SHA-256 manifest;
every source member must match the final working tree. Excludes credentials, private
identity records/login caches, ignored `.aws`/`.cache`, AGENTS.md, dependencies,
Terraform state/plans/private inputs and other prohibited paths. Public-source
credential-pattern checks supplement inventory exclusions; they are not universal
secret detection. Hash/verification evidence remains beside the ZIP in ignored cache.
No private artifact is opened to generate it. No commit or push.
