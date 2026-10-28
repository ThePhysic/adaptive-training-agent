# F4-A1b — Offline identity preparation handoff

2026-10-26. **Prepared for independent review only. No AWS call or live execution
authorization.** A1a remains [owner-attested evidence](f4-a1a-completion.md), not
newly reproduced Codex evidence. Historical reviews/NO-GO decisions are unchanged.

## Implementation and files

Four additions only; pre-existing working-tree changes are preserved:

| File | Purpose |
| --- | --- |
| [Supervised procedure](f4-a1b-supervised-sts-procedure.md) | Separate local preparation, written approval gate, one fixed bounded STS invocation, private comparison, sanitized reporting; conditional separate human GetUser procedure |
| `infra/aws/state_sts.py` | Local-only fixed state identity/configuration, source/binary/time checks, exclusive attempt claim and capture verification; separate fixed human reference-read vocabulary/validation. No process launcher, CLI entrypoint or live activation flag |
| `tests/test_state_sts.py` | Synthetic adversarial tests, actual documented assembly exercised with capture replaced by synthetic responses, PowerShell parse-only checks |
| This handoff | Scope, evidence, risks and next authorization request |

Reuse: existing `human_sts` local filesystem/binary/date checks, private runner's
strict JSON and bounded owned-process capture, selected-only credential binding,
and existing Windows Job Object. No dependencies, IAM scope, boundary policy,
application code, Terraform, migrations, generated contracts or evaluation changes.
Do not broaden `human_sts.py` into a generic profile launcher. Both existing live
executors still unconditionally raise.

## Procedure and security decisions

The proposed operator workflow is in the linked procedure. Its **only state-user
operation** is `sts:GetCallerIdentity`, profile `future-f4-state-operator`, region
`us-east-1`, HTTPS regional STS endpoint. No arbitrary action/profile/endpoint/extra
arguments are accepted by the fixed command builder. CLI binary bytes and the capture
dependency/document source bytes are re-attested before the one-shot claim.

Expectations are supplied privately by the owner and must come from authoritative
prior records or a separately approved human-admin `iam:GetUser` targeting only the
state user. Exact Account/Arn/**path**/UserId comparisons reject another identity.
The expected state UserId is never learned from an unverified STS result. Provenance
labels are owner attestations, not automatic independent authentication.

Fresh selected-only login configuration replaces the real multi-profile file.
The child receives empty shared/legacy credential files and an allowlisted process
environment, no inherited AWS/proxy/TF/Python/PATH/CA overrides, and disabled IMDS.
The existing login cache **location** is explicit; preparation does not read/copy
tokens. Native CLI credentials are not exported or recreated.

The reviewed *future documentation assembly* creates a durable exclusive claim
before capture can release any process, then uses the existing ownership primitive:
120s execution, at most 10s bounded cleanup, 8192-byte stdout/4096-byte stderr caps,
one command, no shell-level retry. A claim remains after failure, interruption,
partial persistence or restart. No release/delete/retry API exists. Claims are local
operator safeguards, not untamperable permits or exact HTTP-send acknowledgements.
No claim was generated with real inputs in this task.

Strict JSON requires exactly three string identity fields; duplicate keys and
malformed/oversized/failed captures fail closed. Raw stdout/stderr stays private
memory and is cleared; only finite summaries or the separately verified reference
identity are written privately. Clearing memory is not guaranteed secure erasure.

The human reference path is **separate**: human profile, global IAM HTTPS endpoint,
exact `--user-name future-f4-state-operator`, `iam:GetUser` on the privately known
exact user ARN, distinct directory/claim and fresh approval. It validates the target
UserName/Arn/Path/UserId and does not imply STS approval. An IAM GetUser response does
not establish its caller's identity; caller provenance relies on A1a plus the separately
reviewed selected human login binding. No extra human STS probe is included.

## Offline evidence

Windows PowerShell 5.1, Python 3.14.9, existing Terraform 1.17.0/AWS provider 6.70.0.
The installed AWS executable was **not invoked**, including no version/identity probe.
The CLI hash in the procedure comes from prior accepted attestation, not a fresh
native binary compatibility test. All test identities, caches and children were
synthetic. Public AWS documentation was reviewed; no account endpoints were called.

| Exact command / check | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_state_sts.py tests/test_human_sts.py tests/test_human_sts_attempt.py tests/test_state_boundary.py tests/test_identity_contract.py tests/test_sts_tunnel.py tests/test_review_source.py -q --basetemp=.cache/f4-a1b-preparation/pytest-final --tb=short` | **312 passed in 441.70s**, including 53 new A1b cases |
| `.venv/Scripts/python.exe -m pytest tests/test_private_command_runner.py tests/test_identity_profiles.py tests/test_identity_coordinator.py tests/test_browser_runner.py -q --basetemp=.cache/f4-a1b-preparation/pytest-capture --tb=short` | **130 passed in 10.25s** |
| `.venv/Scripts/python.exe scripts/check_infrastructure.py --terraform .tools/terraform/terraform.exe` | Exit 0; formatting and three roots validate; **21 mock-plan cases pass**, 5 deployment/14 bootstrap/2 module. No initialization, account-connected plan or backend access |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Exit 0, no drift |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **40/40**: 24 development/16 held-out, software regression only |
| `.venv/Scripts/python.exe scripts/review_source.py check` | **176 Python files** pass native and 3.13 grammar |
| `.venv/Scripts/ruff.exe check .` | Exit 0, all checks pass |
| `.venv/Scripts/ruff.exe format --check infra/aws/state_sts.py tests/test_state_sts.py` | Exit 0, both files formatted |
| `.venv/Scripts/ruff.exe format --check src tests scripts infra experiments` | Exit 0, **179 files** formatted |
| `.venv/Scripts/ruff.exe format --check .` | Exit 1: existing Python-code-block formatting in `docs/development.md` and historical `docs/implementation/f1-04-handoff.md`; 267 files pass. Those unrelated documents are unchanged |
| `git -c core.safecrlf=false diff --check` | Exit 0 |

Windows private-ACL/Job Object tests used normal local process access; no ACL
protections or system policies were relaxed. The exploratory command
`.venv/Scripts/python.exe -m pytest tests/test_state_sts.py -q --basetemp=.cache/f4-a1b-preparation/pytest-first --tb=short`
produced 45 passes/3 failures in 132.32s: two initial command/block-count assertions
were stale, and a source re-attestation rejected a document edited during that run.
The assertions were corrected and relevant sources/documents frozen before the final
run. That exploratory run is not claimed as passing acceptance evidence.

New coverage includes wrong account/user/ARN/path/case/UserId, root/role/federation,
malformed/duplicate/missing/extra/non-string/oversized output, failed/stderr commands,
timeout/cancellation/cleanup failure, selected-profile/credential-source mismatch,
poisoned inherited environment, source/binary/window/provenance mismatch, concurrent
claims, partial-write/interruption/restart and repeat-execution rejection. The actual
future Python capture assemblies are executed only with a synthetic capture function
installed first; no AWS binary can be released by those tests. Existing capture
tests use synthetic owned children. The PowerShell parser checks all four blocks
without execution; all four embedded Python blocks also parse with 3.13 grammar.

No full application/HTTP/PostgreSQL/frontend/browser regression rerun is claimed:
application, schema, UI and database behavior did not change. Existing baseline
artifacts remain byte-identical. Final preservation and ZIP checks are recorded in
ignored `.cache/f4-a1b-preparation/`, with no real credential or identity input.

## Source preservation and review archive

Raw-byte comparison with the starting public-source manifest confirmed **all 464
pre-existing files unchanged**. The only diff is the four additions listed above;
no historical review/baseline was rewritten and AGENTS.md remains ignored/unchanged.

Reproducible packaging commands (local only):

```text
.venv/Scripts/python.exe scripts/review_source.py snapshot --manifest .cache/f4-a1b-preparation/review/source-manifest.json
.venv/Scripts/python.exe scripts/review_source.py archive --manifest .cache/f4-a1b-preparation/review/source-manifest.json --archive .cache/f4-a1b-preparation/review/future-training-f4-a1b-review.zip
.venv/Scripts/python.exe scripts/review_source.py verify-archive --manifest .cache/f4-a1b-preparation/review/source-manifest.json --archive .cache/f4-a1b-preparation/review/future-training-f4-a1b-review.zip
```

The review ZIP contains the **468 public source/documentation files** plus its
embedded `_review/source-manifest.json`; verification requires every source member
to match working-tree bytes and SHA-256. It excludes AGENTS.md, ignored/private
`.cache` and `.aws`, real identity records/login caches, dependencies, Terraform
state/plans/private inputs and other prohibited paths. A bounded-pattern scan of
public source is an additional check, not proof that arbitrary secrets can always
be recognized. No private source was opened to generate the ZIP. Synthetic fixture
identifiers remain synthetic. Machine-local test directories/results are not bundled.
Archive hash/verification evidence is retained alongside the ZIP under ignored cache.

## Remaining risks, prerequisites and exact next authorization

- **NO-GO for live execution in this task.** Owner/reviewer must separately decide
  whether A1b may accept native credential refresh/authentication traffic and no
  OS-enforced egress containment. A1a's exception is not inherited. A prepared file,
  confirmation phrase, source hash or API read-only classification grants no access.
- Owner privately confirms the existing state profile alias and exact trusted
  Account/Arn/UserId/provenance. Codex did not inspect the IDE's private identity
  record, real config, credentials or authentication caches. No new login/setup.
- Actual native behavior with this selected-only configuration remains unverified;
  stop on auth errors/expired session, unexpected prompts, changed binary/source,
  identity mismatch, timeout, privacy loss or incomplete owned cleanup. No automatic
  login, credential export, profile fallback, repeated request or permission grant.
- Native HTTP count and OS egress containment remain unproven. `AWS_MAX_ATTEMPTS=1`
  and process deadlines cannot establish AWS delivery or MFA use. Report neither.
- The explicit cache path may contain other sessions; no token isolation claim is
  made. Selection depends on reviewed native CLI semantics and the fixed login ARN.
  No cache contents were inspected. If these assumptions are unacceptable, stop for
  an alternative isolation proposal, without weakening existing executors.
- A hard crash/timeout may leave a possibly delivered request and a claim. Retain
  evidence; confirm owned processes have stopped and obtain fresh owner review.
  Never reset markers or create another directory as automatic replay. Preserve
  private encryption/ACLs and agree retention; no automatic deletion.
- Boundary installation/effective-policy audit, human-bootstrap tooling corrections,
  deployment IAM escalation controls and real S3 prefix/missing-object compatibility
  remain later gates from the accepted readiness handoff. No state access or provider
  provisioning authority follows this work. No financial permission is created.

**Next proposed AWS operation, conditional:** if trusted private state expectations
already exist, one supervised state-profile STS invocation as written in procedure B.
Required approval names identity, fixed command, binary/source hashes, <=30-minute UTC
window, privacy/capture/retention and A1b-specific refresh/containment assumptions.
No IAM changes, S3, Terraform, spending, retry/login or follow-up is included.

If expectations are unavailable, request **only** the independent human GetUser
reference unit from R first: exact caller/target/endpoint, same bounded capture,
private target verification, separate risk/window approval and no extra operations.
The owner should confirm availability/provenance without sending identifiers to Codex.
GetUser service permission on the exact target must already exist; no grants added.

Recommended next task after independent review: finalize the private operator bindings
and explicit risk decision through owner attestation, then authorize **one named
branch only** for supervised execution. Do not rerun A1a or automatically execute
both GetUser and STS. This handoff does not authorize either branch.
