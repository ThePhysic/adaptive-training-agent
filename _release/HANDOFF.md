# F5-D3 preparation handoff

2026-10-27. Stop for independent review. Candidate status: **BLOCKED**.
The original development repository, history, index and 593-file public snapshot
are unchanged. This directory was resolved as a fresh sibling of the original,
checked for non-overlap, links/junctions and collisions, then created exclusively.
No existing directory was overwritten; no file moved, deleted, reset or staged.

## Included scope

- All runtime backend/frontend source, contracts, migrations, pinned locks,
  Docker/Compose definitions, scripts, tests and their public fixtures.
- Accepted current README/architecture/evidence/storyboard and safe historical
  evidence needed to avoid undocumented fixture/freeze pruning.
- Isolated LangGraph/Langfuse and offline AWS definitions remain source only.
  They are not activated services or cloud operation authority.
- New candidate-only review documents and metadata under `_release/`, plus the
  root RELEASE-CANDIDATE entrypoint. No existing exported file was changed.

`scope.json` names the nine omitted historical documents. The default public-source
filter additionally excluded all ignored/private/dependency paths, Git metadata,
AGENTS.md, state/plans/caches/logs/backups and private evaluation/custody material.
`origin-public-manifest.json` contains public source hashes/names only, not excluded
file contents. The final source manifest binds every included release file; its
own bytes are bound by an adjacent SHA-256 to avoid a self-hash cycle.

## Fresh candidate commands and results

Commands ran with this directory as cwd, using an existing installed Python 3.14.9
interpreter and packages. No original application source was added to imports.
Absolute host paths are intentionally not reproduced here. Interpret `python` and
`ruff` below as those existing installed executables, not a shipped candidate venv.

```powershell
python scripts/export_contracts.py --check
# PASS
python scripts/evaluate_baseline.py --check
# PASS 40/40: 24 development, 16 historical held-out software cases
python scripts/evaluate_models.py --check
# FAIL: git rev-parse HEAD; 150 dispositions not verified in this candidate
python scripts/review_source.py check
# FAIL: Git source inventory unavailable
python -c "import sys;sys.path.insert(0,'src');from experiments.blinded_review import freeze;freeze()"
# FAIL: Git source inventory unavailable
npm.cmd --prefix web run build
# FAIL: missing installed esbuild; no node_modules copied or installed
python -m pytest tests/test_identity_profiles.py tests/test_streaming.py tests/test_observability.py tests/test_provider_hardening.py tests/test_domain.py -q --basetemp=.cache/f5-d3/backend --junitxml=.cache/f5-d3/backend.xml
# PASS 207, no failures/skips, 4.85s
ruff check src tests scripts infra experiments
# PASS
ruff format --check src tests scripts infra experiments
# PASS 204 files in this traversal
```

An independent AST walk parsed all 202 source Python files using native and 3.13
grammar. The application module resolved inside the candidate. Existing LiveGate,
require_live_financial_authority and genuine-review import were each invoked without
credentials or a transport and denied as expected. An initial inspection used a
nonexistent module name; the corrected exact sender function was then verified.
No substitute denial function or implementation change was made.

No native PostgreSQL, Chrome, frontend test/build success, E9/E10 completion,
container exercise, complete routine suite or hosted run is claimed here. Contracts
and targeted ASGI/domain/stream/privacy behavior are fresh candidate evidence.
Earlier F5-D1/F5-D2 full results remain historical. Installed Python packages were
borrowed for validation only; a self-contained fresh environment was not created.
No real accounts, credentials, protected records or provider endpoints were touched.

## Confirmed self-containment blockers

1. `scripts/review_source.py:inventory` invokes `git ls-files`. E2/E4/E6/E9/E10
   freeze/evidence code imports that boundary. Separately,
   `model_evaluation.manifest` invokes `git rev-parse HEAD` with check=True.
   A Git-less export cannot satisfy both. Git init alone would still lack HEAD.
2. Candidate dependency payloads are absent by design. Frontend build needs the
   locked packages; no fallback to original node_modules or silent download is used.
3. Six retained Markdown links point to omitted `infra/aws/README.md` or the
   historical Windows isolation assessment. Findings are retained locally. No
   unsafe excluded original was recopied to make the links green.
4. Licensing/ownership/distribution notices are unresolved. No root license added.

No executable/test/evidence patch was made to conceal these failures. They require
an explicit next decision; this candidate is not promoted to a working release.

## Safety and preservation

The fresh candidate audit checks raw key/home-path patterns, source identities,
reserved private paths, synthetic account fixtures and PNG metadata. Results are
in safety.json. Pattern absence is not complete secret/pixel/rights clearance.
Only already-public synthetic fixtures are included; synthetic token/ARN/key
canaries remain labelled test material. No genuine unseen case or human judgment
was created, opened, imported or inspected. All copied source remains byte-identical.

Validation outputs under `.cache/f5-d3/` are generated local scratch and excluded
from the source manifest/archive. They are not copied historical/private captures.
No original persistent database or volume was used. No Git directory, repository,
remote, commit, push, hosted CI or cloud operation was created.

## Future GitHub/CI handoff ? not executed

1. Owner reviews the exact candidate manifest, blockers and license/source scope.
2. Separately approve candidate-only documentation remedies and choose between
   a reviewed no-Git provenance implementation or local fresh Git init + first
   commit. Prefer the existing Git contract if a first local commit is approved;
   it avoids changing accepted integrity code. Do not use original Git history.
3. Separately approve pinned dependency setup, then rerun candidate 150 dispositions,
   source/freeze/denial checks, frontend tests/build and required native/browser
   tests in new disposable infrastructure before declaring acceptance.
4. Only after source/notice/screenshot review, authorize any exact first commit and
   private remote. Proposed later commands are `git init -b main`, explicit reviewed
   path staging, `git diff --cached --check`, `git diff --cached --stat`, and
   `git commit -m "Initial curated offline application"`. None ran here. Do not
   stage .cache, credentials, AGENTS.md or private material; no blanket git add.
5. Owner creates a **private**, empty GitHub repository only under separate approval;
   do not pre-create a README/license remotely. Specify destination/visibility and
   credentials without placing them in files. Do not configure a remote now.
6. A later explicitly approved private push triggers the existing workflow. Do not
   also dispatch another run. Preserve fake/no-export settings, read-only contents
   permission, mandatory Chrome/native no-skip/frozen guards, and retained volumes.
   Its 75m job /45m routine /15m native /3m browser bounds are configuration, not
   hosted timing proof. Owner must approve GitHub minutes/acquisition separately.
7. Public visibility/upload remains a later decision after license, source, notices,
   pixels/video, privacy and actual hosted CI evidence. Private does not mean
   account secrets or genuine cases may be uploaded.

No new milestone is authorized by this checklist.
