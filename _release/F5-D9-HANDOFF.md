# F5-D9 ? Independent-review handoff

## State and scope

Started: approved main at `7f873f2aea5383e423f4f0083b104731db42bc0d`, exactly three
commits, clean worktree/index, only approved origin. End: same HEAD/history/origin,
index clean, two modified test-infrastructure files and two new untracked reports.
No staging/commit/remote mutation/push/run was performed. The private GitHub main
and original failed run are unchanged. The protected original development public
source bytes, Git status and HEAD are verified against preflight; no private
records were read and no writes targeted that repository. Existing installed
Python/Ruff were reused read-only, with bytecode writes disabled.

Complete change list:

1. `tests/browser_runner.py`: finite preflight diagnostics; retains strict version
   grammar, exact command, five-second bound, capture limits and owned cleanup.
2. `tests/test_browser_runner.py`: 36 additional synthetic/process regression cases.
3. `_release/F5-D9-REPORT.md`: evidence, failure-mode table and remaining uncertainty.
4. `_release/F5-D9-HANDOFF.md`: this review record and proposed future boundary.

The report's diagnostic code resolves confirmed information loss, not an established
Chrome runtime root cause. No timeout increase or browser/workflow substitution is
proposed. All 611 other pre-existing source files must match the starting manifest.
Historical D8 artifacts and all one-shot claims remain untouched.

## Exact validation commands

All commands ran with the curated repository as cwd. `$Python` denotes the already
installed Python **3.14.9**, `$Ruff` the already installed **0.17.2** executable.
Executable locations are retained only in ignored local command records to avoid
publishing personal home paths. No dependency installation was performed. The
failed lookup test's rerun alone used the existing tools directory prepended to
the child process PATH; no persistent environment configuration changed.

Final focused Windows command:

```powershell
& $Python -B -m pytest tests/test_browser_runner.py tests/test_browser_harness.py -q --basetemp=.cache/f5-d9-pytest-browser-reviewed --junitxml=.cache/f5-d9-review/browser-reviewed.xml
```

Result: **57 passed, 1 POSIX-only skip**, 6.14 seconds. Real Job Object/descendant,
launch-error, timeout, overflow and interrupt cleanup checks passed. Earlier test
iterations (retained locally): 53 passed; then 56 passed/1 skip. No test failure in
these selections was concealed by those development reruns.

Final Linux command (`$Candidate` is the resolved authorized source directory):

```powershell
docker run --pull=never --rm --network=none --read-only --tmpfs /tmp --mount "type=bind,src=$Candidate,dst=/workspace,readonly" --workdir /workspace --entrypoint /opt/testenv/bin/python fata-f403a-ci-tests:latest -B -m pytest tests/test_browser_runner.py -q -k 'command_version or version_failure or unrecognized_version or real_owner_launch or native_python or non_executable or stat_denial' --basetemp=/tmp/f5-d9-pytest-reviewed -o pythonpath=src
```

Result: **36 passed, 17 deselected**, 2.78 seconds. Earlier selection, before stat
ambiguity coverage: 35 passed/17 deselected, 2.84 seconds, basetemp=/tmp/f5-d9-pytest.
No Chrome/Node exists in this cached image; those deselections are not passes.
The container was disposable and did not access original DBs, volumes or networks.

Broader regression command:

```powershell
& $Python -B -m pytest tests/test_foundation.py tests/test_prepared_sender.py tests/test_provider_hardening.py tests/test_sealed_evaluation.py tests/test_independent_cases.py tests/test_review_source.py tests/test_check_runner.py tests/test_model_evaluation.py -q --basetemp=.cache/f5-d9-pytest-regression --junitxml=.cache/f5-d9-review/regression.xml
```

Result: **324 passed, 1 failed**, 99.90 seconds. The failed source-review formatter
test looked up nonexistent `ruff` because no candidate .venv/PATH tool was available.
No browser assertion or production defect caused this failure. After supplying the
already installed Ruff through the child PATH, only that failed test was rerun:

```powershell
& $Python -B -m pytest tests/test_review_source.py::test_native_314_syntax_explains_old_parser_failure_and_formatter_retains_fix -q --basetemp=.cache/f5-d9-pytest-ruff-ready --junitxml=.cache/f5-d9-review/ruff-ready.xml
```

Result: **1 passed**, 0.16 seconds. Initial failure and both XMLs remain local.

Other executed commands, all exit 0:

```powershell
& $Ruff check src scripts tests --no-cache
& $Ruff format --check src scripts tests --no-cache
& $Python -B scripts/export_contracts.py --check
& $Python -B scripts/prepare_responses.py --check
& $Python -B scripts/prepare_model_evaluation.py --check
& $Python -B scripts/evaluate_models.py --check
& $Python -B scripts/evaluate_baseline.py --check
& $Python -B scripts/review_source.py check
git diff --check
```

Ruff format: 170 files; source native/3.13 grammar: 202 Python files; frozen40/40;
comparison150/150. Historical manifests were neither regenerated nor reclassified.
Read-only Windows `chrome_version` read the installed PE fixed version resource:
156.0.8078.48, 0.0029 seconds. No Windows browser was launched for that probe.
Historical-source simulation demonstrated five distinct outcomes collapsing to
one label. Synthetic output is not a native hosted reproduction.

## Adversarial review

- Successful-looking stdout plus nonzero/unknown exit cannot pass.
- A failure cannot release Node, retry, alter approval assertions or skip the gate.
- Missing file and stat access denial are distinguished without path disclosure.
- Only the owner can attach capture reason metadata; child stderr resembling a
  timeout marker is classified by its actual exit rather than trusted as metadata.
- Malformed, prefixed/suffixed, non-ASCII, oversized and out-of-bound version output
  stays rejected. Valid supported prefixes/trailing whitespace remain accepted.
- Raw stderr on an otherwise successful version command remains ignored, preserving
  existing behavior; there is no new logging channel for it.
- Popen failure is distinguished at the launch site. Cleanup/unknown failure is not
  mislabeled as launch or authentication failure. Existing ownership and final wait
  execute on timeout and KeyboardInterrupt; descendants terminate in actual Windows
  and synthetic Linux tests. No stronger protection against arbitrary hostile
  breakaway processes is claimed.
- Windows PE implementation is byte-identical to approved HEAD. Linux process-group
  and Windows Job Object tests remain mandatory where runnable.

## Package and verification

The review ZIP contains the current public working-tree snapshot: original 613
source paths plus these two reports, with an embedded `_review/source-manifest.json`.
The two executable files are uncommitted modifications. This package must not be
mistaken for uploaded/committed source or a successful CI artifact.

Standard review-source snapshot/archive/verify-archive checks bind all 615 source
files to raw SHA-256 bytes and parse all 202 Python files. A separate verification
checks ZIP member bytes, source scope against the preflight manifest, unchanged
original source/status/HEAD, unchanged historical reports/screenshots, unchanged
Windows branch and clean index. ZIP checksum is supplied as an external sidecar.
No .git internals, credentials, private identities, caches, dependency trees,
builds, raw logs, state, genuine cases, curator materials or AGENTS enter the ZIP.
Pattern checks are not a comprehensive semantic secret or legal clearance.

## Proposed next decision ? not executed or authorized

If independent review accepts this diagnostic-only change, owner may separately
approve the following bounded sequence:

1. Resolve D8 delayed billing privately; confirm available included Actions use,
   unchanged zero-paid-overage controls and exact private destination.
2. Revalidate base HEAD, four-path diff and this archive's tested bytes. Stage only
   these four paths; create **one** local commit, suggested message
   `test: classify browser version preflight failures`. Record its new exact SHA.
   No extra code/timeout/browser-selection change is part of this proposal.
3. Authorize **one** push of that reviewed exact new SHA to private refs/heads/main,
   and its **one** automatically triggered existing offline workflow. No force,
   tags, other refs, manual dispatch, rerun, second push or paid usage.
4. Observe the entire mandatory workflow. A browser failure must retain its new
   finite reason; success of preflight alone is not complete CI acceptance. If the
   workflow fails/blocks, stop without correction or retry. Any Chrome/workflow fix
   remains a subsequent separately reviewed change based on actual evidence.
5. Reconcile private main, run count, cleanliness and delayed billing. Public
   visibility, release/image publication and other live activity stay excluded.

No owner authorization is requested or inferred during this milestone. Hosted
acceptance, definitive hosted root cause and D8 financial reconciliation remain
unresolved. No further milestone is automatically authorized.
