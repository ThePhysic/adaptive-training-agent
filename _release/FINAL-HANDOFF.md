# F5-D3 final source-candidate handoff

Read this with [initial findings](HANDOFF.md), [clean-candidate validation](final-validation.json),
[safety](safety.json), [scope](scope.json) and [licensing/next decisions](LICENSING-AND-NEXT-DECISIONS.md).

## Delivered state

**BLOCKED: not accepted as a fully working, self-contained release.** The source-only
candidate is the directory whose basename is `future-training-portfolio-rc-f5-d3-source`.
The earlier sibling `future-training-portfolio-rc-f5-d3` is retained as a validation
workspace; it is not the release payload. Neither is the original development repo.
No original source, private record, Git index/history or persistent data was changed.

The first validation workspace acquired bytecode/Ruff caches from tests. They were
not copied from development, were not deleted, and are not exported. A fresh clean
source directory was then collision/non-overlap checked and populated exclusively
from the approved file list. Final tests used bytecode suppression, Ruff --no-cache,
and temporary/JUnit outputs routed to the retained validation area. This clean tree
contains no cache, node_modules, venv, database data, .git or inherited history.

Every one of 584 copied originals remains byte-identical to the original public
snapshot. The nine approved historical omissions remain omitted. Only additive
candidate review/manifest documents were authored; no executable/test/historical
source was edited, redacted or silently substituted. The candidate still retains
safe history/experiments/infrastructure source because their complete test/freeze
closure has not been approved for further reduction.

## Fresh final-candidate results

- 207 existing offline backend/domain/streaming/privacy/provider-hardening tests
  passed directly in this clean directory, zero failures/skips, 5.02 seconds.
- Independent import check resolved the app inside this candidate. LiveGate,
  require_live_financial_authority and genuine-review import explicitly denied.
- OpenAPI contract check and frozen 40/40 software baseline passed here.
- All 202 Python files parse native/3.13 grammar; Ruff lint and 204-file formatting
  check passed here without creating a cache.
- Source inventory and sealed configuration failed closed without Git inventory;
  the 150-disposition check failed without committed Git HEAD. No 150/150 candidate
  claim is made. The baseline does not compensate for that failed acceptance check.
- Frontend build was attempted in the earlier isolated validation workspace and
  failed because esbuild/dependencies are absent. The clean copy also contains no
  dependencies. No installs, symlinks or fallback to original node_modules occurred.
- Six retained document links still point to owner-excluded material. This was
  recorded rather than editing original evidence or copying unsafe originals back.
- No final native PostgreSQL, Chrome, container, frontend-test or hosted CI success
  is claimed. Earlier D1/D2 results are historical. Earlier workspace's 207 passes
  are a repeat population, not 414 unique tests.

Python dependencies were reused from an existing installed interpreter, not copied
or acquired. Environment reproducibility from a fresh install is not established.
The original README and CI are retained byte-for-byte; their full commands are not
certified runnable in this Git-less/dependency-less pre-commit export.

## Commands in the clean directory

`python`/`ruff` refer to the existing installed executables. `$validationArea` is
an external retained scratch directory, not inside the clean release tree.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:FATA_PROVIDER = 'fake'
$env:FATA_TELEMETRY_EXPORTER = 'none'
$env:FATA_WRITE_EVIDENCE = '0'
python -B -m pytest tests/test_identity_profiles.py tests/test_streaming.py tests/test_observability.py tests/test_provider_hardening.py tests/test_domain.py -q --basetemp=$validationArea/clean-backend --junitxml=$validationArea/clean-backend.xml
ruff check --no-cache src tests scripts infra experiments
ruff format --check --no-cache src tests scripts infra experiments
python -B scripts/export_contracts.py --check
python -B scripts/evaluate_baseline.py --check
python -B scripts/evaluate_models.py --check
python -B scripts/review_source.py check
python -B -c "import sys;sys.path.insert(0,'src');from experiments.blinded_review import freeze;freeze()"
```

The last three commands failed; their classified results and actual timing are in
final-validation.json. No failure was suppressed to create a passing release label.

## Safety and licensing

Fresh clean-tree pattern/metadata checks show no forbidden cache/account/credential/
private/custody files, no identified home-directory or key patterns, only documented
synthetic IAM ARN accounts, and no PNG text/EXIF among 58 images. One primary mobile
error view was visually inspected; all historical pixels and rights are not fully
cleared. Original private identities/caches/captures were not accessed.

License is undecided. No root LICENSE added. The source-only archive does not ship
wheels, JS bundles or container images. The inventory covers available eight direct
installed Python declarations and 109 npm lock entries; it is not complete transitive
license/notice clearance. Psycopg/binary metadata declares LGPL-3.0-only, making later
binary/image notice review particularly relevant. MIT versus Apache-2.0 are owner
options, not selected grants; official links are in the licensing note.

## Next authorization boundary

Do not repair the Git prerequisite by using the original .git, a surrogate HEAD,
a fake repository, an arbitrary file-path trust string or by skipping source checks.
Prefer a separately approved fresh local init AND reviewed initial commit if the
owner accepts that next boundary; init alone cannot satisfy rev-parse HEAD. Otherwise
an additive manifest-backed inventory/revision contract needs explicit source review
and authorization before implementation. Neither was done now.

Dependency setup, exact candidate-only link remedies, source/license review, first
commit, private GitHub creation, remote/push, one hosted workflow and final public
visibility remain separately gated. No genuine/provider/financial gate is opened by
any of them. The existing CI remains a proposal, not a verified run on this tree.

The source manifest lists all included raw SHA-256 hashes. Its self-excluded control
files are explicitly declared; a sidecar binds manifest bytes. The sibling review
ZIP contains only these candidate files and the manifest controls, never validation
workspaces/caches or original Git/private history. No publication approval is implied.
Stop for independent review and owner direction on these concrete blockers.
