# F5-D9 ? Hosted browser-preflight diagnosis

## Outcome

**The specific F5-D8 Chrome failure remains unknown.** Public source and synthetic
reproduction confirm a diagnostic defect: timeout, capture overflow, nonzero exit,
empty stdout and rejected output all collapse to `browser_version_unavailable`.
This milestone corrects that information loss only. There is no evidence-supported
Chrome selection, version grammar or timeout correction yet. Hosted acceptance
remains NO-GO; the original failed run remains unchanged.

Base revision: `7f873f2aea5383e423f4f0083b104731db42bc0d`, main, three commits.
The curated repository started with clean index/worktree and approved origin.
Read-only GitHub checks confirmed exact private destination, approved remote main
and only [run 40757298712](https://github.com/ThePhysic/adaptive-training-agent/actions/runs/40757298712),
push event, attempt 1, completed/failure. No commit, push, dispatch or rerun occurred.

## Confirmed execution boundary

The workflow uses Ubuntu 24.04, resolves `google-chrome` with `command -v`, then
exports the result as `FATA_BROWSER_EXECUTABLE`. `scripts/check_browser.py` requires
that selection to be a file and runs exactly one installed-browser test. It does
not select a fallback browser or install one. `tests/test_browser_ui.py` supplies
the inherited environment, disposable PostgreSQL fixtures and a live loopback
server to `run_browser`. It does not filter or print inherited environment values.

On Linux, `chrome_version` runs exactly `[executable, "--version"]` through
`owned_process`, using web as cwd and a five-second communicate bound. Popen has
no shell and starts a new POSIX session. Completion, timeout and interruption flow
through owned group termination and a bounded five-second wait. Output reads are
capped at 16 KiB per stream; temporary files are not a streaming disk quota. Only
successful exit plus a full version-pattern match permits the Node/UI workflow.
The version probe has no application navigation or provider operation.

In the approved source, the observed Linux failure label is emitted after
`owned_process` returns, when exit is nonzero OR stdout fails matching. This supports
an inference that Popen and the normal cleanup-return path were reached. It does
not establish successful execution of Chrome behind a wrapper, disclose its exit,
or establish any HTTP delivery. A thrown launch/cleanup exception would normally
have produced `browser_owner_failed` instead. This is source reasoning, not newly
retained native runtime evidence.

D8 observed one failed browser test in 5.77 seconds; FastAPI health/readiness were
200/200. The full Node/UI journey had not started. Existing logs contain no native
exit, stdout, stderr or timeout discriminator. Read-only reinspection of that same
run added no such evidence; no raw logs are exported in this package.

## Failure assessment

| Mode | Classification | Evidence / limits |
| --- | --- | --- |
| Diagnostic ambiguity | Confirmed; reproduced locally | Five synthetic outcomes against the unchanged HEAD implementation produce the same failure label. |
| Version-command timeout | Supported but unconfirmed | Five-second limit and 5.77-second test are consistent; fixture/server overhead prevents timing from proving timeout. |
| Native nonzero exit or signal | Reproduced locally as a route; historical cause unknown | Same label in historical-source simulation; no native code retained. |
| Empty, malformed or oversized output | Reproduced locally as routes; historical cause unknown | Synthetic checks exercise each route, not hosted Chrome. |
| Missing executable at initial selection | Ruled out as the direct recorded boundary | Gate would emit `required_browser_not_installed`; removal/race after that check remains unknown. |
| Launch/permission/cleanup exception | Ruled out as the ordinary route to this label | Source would report another category. POSIX permission rejection and launch failures reproduced with synthetic files. |
| `Google Chrome for Testing` prefix by itself | Ruled out as a grammar defect | Already supported by the original pattern, as are Google Chrome and Chromium with trailing whitespace. |
| Distribution suffix, altered format, numeric bound excess | Supported but unconfirmed | Strict pattern rejects these synthetically; actual hosted stdout unknown. No relaxation justified. |
| Environment, wrapper, scheduling or resource contention | Unknown | Environment was inherited; no identifying values inspected or printed. No measurement establishes one of these as cause. |
| Application/DevTools failure | Ruled out as this failure boundary | Version preflight failed before Node/DevTools/UI; healthy server alone does not prove the full application passed. |

The cached Linux project test image has Python 3.14.9/pytest 9.1.1 but no Chrome or
Node. Its tests use network=none, read-only candidate mount and disposable tmpfs.
They verify synthetic process behavior, not Ubuntu-hosted installed Chrome.
Windows installed Chrome's existing fixed PE-resource path returned version
156.0.8078.48 in 0.0029 seconds without launching Chrome. This is not Linux evidence
or an Authenticode-signature verification.

## Minimal uncommitted implementation

Only executable changes:

- `tests/browser_runner.py`: typed, sanitized Popen-launch failure; owner-generated
  capture reason attached to CompletedProcess; separate command-version helper;
  finite version-preflight reason emitted under unchanged top-level failure label.
- `tests/test_browser_runner.py`: 36 additional parameterized test instances,
  including real owned Python children/descendants and synthetic version outputs.

Reports added: `_release/F5-D9-REPORT.md` and `_release/F5-D9-HANDOFF.md`.
No workflow, browser selection, application, database, scorer, dependency, frozen
artifact or historical report changed. Windows PE branch is byte-identical.

Example failure shape (illustrative; not recovered D8 evidence):

```json
{"failure":"browser_version_unavailable","versionPreflight":{"reason":"timeout"}}
```

Allowed reasons: `executable_not_found`, `launch_failed`, `timeout`, `nonzero_exit`,
`empty_stdout`, `unexpected_stdout_format`, `unsupported_version`,
`capture_overflow`, `ownership_failed`, `process_failed`.

`unsupported_version` means the existing numeric representation bounds were
exceeded; no minimum Chrome compatibility policy has been invented. An inaccessible
stat or unknown exit is not called a missing executable. Cleanup/other failures
remain `process_failed`, with cleanup certainty unestablished. Failed preflight
always returns failure and never releases Node. Native stderr cannot forge an
owner-generated timeout category merely by printing the owner's JSON marker.
No raw path, output, environment, exit error text, credential or identifying host
metadata enters the new diagnostics. Original capture/timeout behavior and cleanup
remain in force. No retry, download, sandbox relaxation or mocked success is added.

## Fresh validation and limitations

- Final Windows browser runner/harness selection: **57 passed, 1 POSIX-only skip**
  (58 collected), 6.14 seconds. Earlier development runs: 53/53; then 56 passes/one
  POSIX skip. These are repeat populations, not additive distinct test totals.
- Final cached Linux synthetic selection: **36 passed, 17 deselected**, 2.78 seconds.
  Earlier revision: 35 passed/17 deselected. Node-dependent existing checks were
  not run in this image. POSIX permission and descendant/group cleanup ran here.
- Broader selected regressions: **324 passed, 1 failed** out of 325, 99.90 seconds.
  The failure was test_review_source's subprocess lookup of Ruff, absent from PATH
  with no candidate .venv. With the already installed pinned Ruff directory on the
  child PATH, **that one test passed**, 0.16 seconds. No source correction/download
  was used, and the initial failure is retained. Do not call this a single clean
  325-test run.
- Ruff check passed; format check passed, **170 files**; contract/schema export,
  Responses fixtures and model assets checks passed; source inspection parsed
  **202 project Python files**, native 3.14 and Python 3.13 grammar.
- Frozen baseline **40/40** and comparison dispositions **150/150** passed afresh.
  Deliberate hard failures and historical exposure labels remain unchanged.
- Selected foundation, prepared-sender, provider-hardening, sealed and independent
  case tests retain live-provider, monetary and genuine-opening denials. No genuine
  cases, actual credentials or protected records were accessed.
- `git diff --check` passed. Final package checks compare all untouched committed
  bytes with preflight and verify every archive member against the worktree.

The full backend/frontend, database, browser application and release-image suites
were not rerun: these changes affect the test preflight only. D8's frontend 138,
routine 2,191 and earlier D5 totals remain historical, not fresh D9 measurements.
No Linux installed-Chrome or hosted acceptance claim is made.

## Next boundary

Review may authorize one diagnostic-only commit and one push-triggered CI run.
Its purpose would be to identify the real version failure or verify transient
recovery, not to claim an already diagnosed Chrome fix. Exact proposed procedure
and prerequisites are in the handoff. No such commit/run is authorized here.
Financial reconciliation of D8 is still pending; no billing APIs, budget changes
or paid usage were needed for D9. Final study freeze, provider/spending authority,
genuine evaluation, AWS and public publication remain denied.
