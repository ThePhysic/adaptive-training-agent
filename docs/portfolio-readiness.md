# Portfolio and engineering release readiness

F5-D2 prepares an offline source presentation, not a publication or deployment.
Read the [evidence map](engineering-evidence.md) and
[publication-safety assessment](implementation/f5-d2-publication-safety.md).

| State | Capability / decision | Evidence or required next action |
| --- | --- | --- |
| Ready locally | Explicit Save, fake generation/stream, review, revision, approval, immutable history and session submission | F5-D1 installed-Chrome/SQL exercise, reproduced twice |
| Ready locally | Cancellation, idempotency/reconciliation, dependency recovery, local release and restore | Controlled regressions plus actual current-source container drill; single process only |
| Ready locally | Synthetic counted execution, retained failure/holds, shared scoring and dummy review | E9/E10 artifacts and native tests; no genuine quality claim |
| Prepared for review | Concise README, Mermaid architecture, four-minute storyboard and evidence navigation | F5-D2 documents; no video or manual usability study claimed |
| Blocking publication | Historical documents contain host-user paths; full Git history has not been cleared for publication | Owner chooses retention/exclusion/redaction policy separately; no historical rewrite here |
| Blocking publication | Root license, source ownership/distribution and dependency-notice decisions | Owner selects license and approves redistribution scope; no license invented |
| Blocking release verification | Current hosted CI remains unverified; accepted work includes untracked files | Owner reviews exact source manifest, selects/stages changes deliberately, and separately authorizes a branch push/run and any GitHub minutes |
| Before final presentation | Narrated capture and final visual/privacy review | Use public synthetic examples; review recording before upload |
| Deferred real-model | Account/model/parameter compatibility, count tariff/max charge, retention/privacy and numerical permits | Support Case 18223129 unresolved; source review and one separately approved bounded compatibility probe before any study |
| Deferred independent study | Genuine source/opening/authentication/custody, exact configuration and freeze, human-only creation and review collection | Separate human decisions and independent evidence; no genuine cases or keys handled here |
| Optional | AWS, hosted telemetry, judge calls, extra orchestration/queues | Not required to publish an honestly labelled offline engineering case study |

## Bounded CI correction

The old job limit was 15 minutes and native integration step five minutes. F5-D1
measured 22m02s routine and 6m52s non-browser integration on Windows/Docker; those
are not Ubuntu measurements, but the old aggregate envelope could not contain the
observed supported environment. The shared runner already allows routine 40m and
native 15m. F5-D2 gives the routine step 45m (40m suite plus checks/build allowance),
native 15m, preserves the mandatory isolated browser's 3m, and bounds the job at
75m: those phases plus a 12m acquisition/SDK/build/cleanup reserve. The reserve is
a policy bound, not measured hosted performance or a guarantee all phases finish.

All suites, fail-fast behavior, read-only repository permission, pinned actions,
fake/no-export configuration, isolated browser, native zero-skip checks, frozen
artifact guard and retained-volume cleanup remain. No parallel matrix or test
selection reduction was introduced: shared ports/database make that a new concern.
No result is retried or marked continue-on-error. Fresh offline YAML/structural
tests validate configuration, not GitHub scheduling, runner images or runtime.
If a future run reaches the bound, retain diagnostics and investigate; do not keep
raising limits or omit cases. Public/private GitHub runner-minute costs require
owner confirmation before a trigger; no hosted resources were used here.

## Exact next hosted verification boundary

No command below is executed in F5-D2. First resolve the publication/privacy scope,
license and clean reviewed source selection. A new private validation branch is
an option only after owner review of its destination and access; it is not an
automatic way to upload the current dirty tree. The owner must explicitly approve:

1. Exact repository/destination, visibility, reviewed source/branch/commit and
   staged diff. Do not use `git add .`; accepted untracked work needs review.
2. Whether a push or one workflow dispatch is authorized; existing push/PR triggers
   mean **do not dispatch again** if the approved push already starts the run.
3. GitHub Actions availability/minutes, dependency/image acquisition and synthetic
   ephemeral runner evidence. No provider/AWS secrets, deployment or hosted exports.
4. The single workflow run and acceptance evidence: all mandatory phases succeed,
   zero native/browser skips, actual Linux durations, frozen artifact guard and
   release/restore results. Do not infer success from a parsed YAML or local run.

The future operator may use `git push <approved-remote> <reviewed-branch>` **only**
under that separate authorization, or dispatch this workflow against an already
reviewed ref if no push-triggered run is in progress. Remote details are deliberately
not resolved here. CI currently regenerates local evidence in its ephemeral checkout;
those outputs must be labelled by run/source and must not be committed over accepted
historical evidence automatically. No public artifact upload step is added.

## Reproduction limits

The environment is locked, but a clean installation needs public dependency/image
downloads. F5-D1 rebuilt current source with cached dependencies and observed
BuildKit registry metadata traffic; it was not an air-gapped/fresh-install proof.
F5-D2 does not need another 22-minute routine suite or native restore because no
application, dependency, schema or scorer source changed. It freshly validates the
changed workflow, docs, source integrity and targeted safety regressions. Reuse the
[local demonstration](local-demonstration.md) and [release runbook](local-release.md)
without deleting volumes or replacing uncertain first results.
