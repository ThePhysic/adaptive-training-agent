# F1-01 handoff — environment, schemas and foundational contracts

Date: 2026-10-23 (America/Los_Angeles). Scope authorized by owner: **F1-01 only**.
F0 approval and the local instruction update were read before implementation.
Historical planning documents remain unchanged. No commit or push was performed.

## Result and readiness

F1-01 is complete for review. The environment starts locally, strict structural
schemas and API design contracts are available, and the relevant checks pass.
**Ready for owner review and subsequent F1-02 authorization; F1-02 has not begun.**
The product is not yet functional: generation, actual catalog feasibility,
duration calculation, user identity/persistence and approval are later work.

## Files changed

| Area | Files | Implemented scope |
| --- | --- | --- |
| Environment | `.python-version`, `pyproject.toml`, `uv.lock`, `compose.yaml`, `.gitignore` | Workspace-local Python/venv/cache; exact Python/JS dependency locks; digest-pinned localhost PostgreSQL; local artifacts ignored while `AGENTS.md` remains ignored |
| Schemas | `src/future_training/__init__.py`, `schemas.py` | Profile and catalog/provenance types; discriminated prescriptions and static goal/experience bounds; proposal/day structures; internal candidate metadata and commit-state vocabulary; approval IDs; error/SSE outcome types; fixed budget/capacity descriptors |
| Foundation API | `src/future_training/config.py`, `api.py`, `scripts/serve.py` | Fake-only/no-exporter settings and safe launcher; `/health` 200 and deliberately `/ready` 503; no business handlers |
| API/TS contracts | `scripts/export_contracts.py`, `contracts/openapi.json`, `web/package.json`, `web/package-lock.json`, `web/tsconfig.json`, `web/src/api.generated.ts`, `web/src/contract-check.ts` | Offline-generated OpenAPI/TypeScript and compile/drift checks; all future business operations explicitly labeled specification-only |
| Approval obligations | `contracts/approval-safety.md`, `tests/specification/__init__.py`, `approval_reference.py`, `test_approval_obligations.py` | Normative ordering supplement plus reduced executable **reference model**, not production transaction code |
| Bootstrap DB | `migrations/001_foundation.sql`, `scripts/migrate.py`, `tests/test_migrations.py` | Transactional, checksum-verified metadata-only migration; repeatability, checksum rejection and rollback integration checks |
| Other tests/data | `tests/conftest.py`, `test_schemas.py`, `test_foundation.py`, `data/catalog-provenance-seed.json` | Strictness/negative tests, eight matrix rows, startup/config/egress checks; one explicitly synthetic provenance fixture |
| Documentation | `README.md`, `docs/development.md`, this handoff | Current implemented stage, install/run/check instructions, limitations and unit evidence |

The `tests/test_*.py` names in this table are relative to `tests/`; reference-model
files are under `tests/specification/`. Existing untracked planning documents were
already present before this work and were not created or edited by F1-01.

## Dependency decisions and evidence

Verified official registry release metadata, Python requirements, generator peer
requirements, non-yanked package status and dependency resolution before final
pinning. Actual Windows runtime/import/tests and TS compilation verified the
chosen combination; no Linux application-runtime test is claimed.

| Component | Selected version | Reason/evidence |
| --- | --- | --- |
| Python | 3.14.9 | Maintained 3.14 line; workspace-managed runtime, not the machine's older 3.13.0 installation |
| FastAPI / Pydantic | 0.162.0 / 2.14.1 | Official stable releases; FastAPI requires Pydantic >=2.9; strict-model and ASGI checks pass |
| Uvicorn / Psycopg binary | 0.54.0 / 3.3.6 | Compatible Python constraints/wheels; local HTTP startup and PostgreSQL connections tested |
| pytest / pytest-asyncio / pytest-socket | 9.1.1 / 1.4.0 / 0.8.1 | Compatible declared requirements and working Windows event loop/network guard |
| HTTPX / Ruff | 0.28.1 / 0.17.2 | Stable registry releases; ASGI transport and scoped lint/format commands tested |
| TypeScript / openapi-typescript | 5.9.3 / 7.13.0 | Current generator explicitly peers on TypeScript `^5.x`; latest stable 5.x selected, rather than forcing latest-major 7.0.2 through an incompatible peer constraint |
| PostgreSQL | 18.6-bookworm plus SHA-256 digest in Compose | Official supported 18 minor; real container startup, localhost publication and migration tests pass |

Installed transitive versions are in the locks; `uv pip check` reports all 29
installed Python packages compatible. The base FastAPI dependency includes the
OTel **API**, but no SDK/exporter is installed or configured; tests verify exporter
absence. No provider SDK, graph framework, ORM, frontend framework or hosted
service was added. Node 24.22.1 and npm 11.19.1 were already installed; uv 0.13.5
was used. npm install reported zero known vulnerabilities in its audit.

Official sources consulted on 2026-10-23: [Python support/downloads](https://www.python.org/downloads/),
[FastAPI registry metadata](https://pypi.org/pypi/fastapi/json),
[FastAPI release notes](https://fastapi.tiangolo.com/release-notes/),
[FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/),
[Pydantic metadata](https://pypi.org/pypi/pydantic/json) and
[strict validation](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/),
[Psycopg metadata](https://pypi.org/pypi/psycopg/json),
[Uvicorn](https://pypi.org/pypi/uvicorn/json), [pytest](https://pypi.org/pypi/pytest/json),
[pytest-asyncio](https://pypi.org/pypi/pytest-asyncio/json),
[pytest-socket](https://pypi.org/pypi/pytest-socket/json),
[HTTPX](https://pypi.org/pypi/httpx/json), [Ruff](https://pypi.org/pypi/ruff/json),
[TypeScript release metadata](https://registry.npmjs.org/typescript),
[generator peer metadata](https://registry.npmjs.org/openapi-typescript/latest),
and [PostgreSQL support policy](https://www.postgresql.org/support/versioning/).

## Commands executed and observed results

Dependency acquisition used network access; routine tests and generation do not.
The runbook gives clean setup/replay instructions. Local sandbox restrictions
required elevated tool execution for registry downloads, Docker and localhost
integration checks; this did not provision external infrastructure.

| Command | Observed result |
| --- | --- |
| `uv python install 3.14 --install-dir .tools/python --no-bin --no-registry --cache-dir .cache/uv --no-progress` | Installed workspace Python 3.14.9; exact runtime then recorded in `.python-version` |
| `uv lock --python .tools/python/cpython-3.14.9-windows-x86_64-none/python.exe` | Resolved 30 project/package records; wrote hashed transitive lock |
| `uv sync --frozen --python .tools/python/cpython-3.14.9-windows-x86_64-none/python.exe` | Installed 29 packages into `.venv` |
| `uv sync --frozen --offline --python .tools/python/cpython-3.14.9-windows-x86_64-none/python.exe` | Cached offline environment check passed |
| `uv pip check --python .venv/Scripts/python.exe --offline` | All installed packages compatible |
| `npm install --ignore-scripts --cache .cache` from `web/` | Installed compatible locked TS tooling; 34 audited package records, zero reported vulnerabilities |
| `.venv/Scripts/python.exe -m pytest -q` | **71 passed, 3 integration tests deselected**, no warnings |
| `.venv/Scripts/python.exe -m pytest -q -m contract_spec` | **6 passed, 68 deselected**; subset of the default tests, not six additional tests |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/python.exe scripts/export_contracts.py` and `--check` | OpenAPI generated and drift check passed |
| `npm --prefix web run generate`, `run check`, `run check:generated` | TS generation, strict compilation (including negative type checks), and generated-file drift check passed |
| `docker compose config --quiet` | Compose configuration valid |
| `docker compose up -d --wait postgres` | PostgreSQL healthy; published only `127.0.0.1:55432` |
| `.venv/Scripts/python.exe scripts/migrate.py` | Applied `001_foundation.sql` |
| `.venv/Scripts/python.exe -m pytest -q -m integration` | **3 passed, 68 deselected** at time of execution; repeat migration, checksum mismatch rejection and SQL/history rollback verified against real PostgreSQL |
| Inline Python subprocess smoke check of `scripts/serve.py` | Real localhost HTTP `/health` 200 with stage F1-01; `/ready` 503 `foundation_only`; own server process terminated afterward |
| `git check-ignore AGENTS.md` | Local instruction file remains ignored |

The integration run preceded the final internal-metadata test and two numeric
strictness cases; its reported deselection count therefore differs by three.
There are **74 collected cases total**: 71 default (including six reference-model
cases), plus three opt-in PostgreSQL cases. No skipped placeholder tests are used.

Initial failures and fixes: npm correctly rejected TypeScript 7 against the
generator's peer contract; the final lock uses verified compatible 5.9.3. Docker
Desktop needed startup and sandbox pipe access. An initial internal Docker network
prevented host port publication; the final configuration uses standard bridge plus
loopback-only publication, and all DB checks subsequently passed. Ruff initially
scanned local tool files; final checks explicitly scope `src scripts tests` and
disable its cache. pytest cache writing was disabled, iterator/warning handling
corrected, and the temporary failed-cache artifact removed. Final checks pass.

## Architectural and contract decisions

- F1-01 enforces structural and static matrix constraints only. It does not
  calculate duration, resolve catalog IDs/tags, or call itself a full plan
  validator. A regression test explicitly demonstrates that distinction.
- Transport limits: ASCII opaque IDs <=64 characters, tags <=32, keys <=128,
  SHA-256-shaped content hashes; request text <=2,048 characters inside the ratified
  16-KiB request ceiling. Catalog/plan list design pages are capped at 20. These are
  wire-format limits, not new workout rules. Byte-cap middleware and pagination
  execution remain later runtime work.
- The API design uses the agreed paths and typed four-outcome SSE contract.
  Only terminal `done(plan)` exposes candidate approval identity. Event ordering,
  incomplete-EOF UI and stream limits remain F1-05 enforcement, not schema claims.
- The approval supplement requires committed-key lookup before candidate access
  **and after guard wait**, before stale/expired/already-approved rejection. The
  reference tests force both initial reads to miss and explicitly observe guard
  waiting before releasing the simulated commit.
- Cancellation must retain guard ownership through an awaited, shielded finalizer.
  An uncertain commit must reconcile authoritative durable identity/key state;
  unresolved state quarantines both new approval and revision publication. The
  reference tests cover matching/mismatched retries, repeated cancellation,
  committed/rolled-back reconciliation and unavailable reconciliation.
- The actual profile row locks, durable uniqueness, restart recovery and commit
  reconciliation require F1-03/F1-06 code and PostgreSQL fault tests. Reference
  model success does not satisfy those later acceptance gates.
- PostgreSQL uses a standard Docker bridge and a loopback-only trusted synthetic
  database; this is deliberately not public/real-user infrastructure. Default
  pytest blocks external DNS and socket connections while permitting loopback.
- Readiness remains 503 until the product is implemented, avoiding a misleading
  green readiness signal. Business paths are never backed by placeholder handlers.

## Limitations and next review boundary

No unresolved F1-01 test failures remain. F1-02 still must curate actual content,
prove conditional catalog coverage for all eight rows/presets, implement exact
duration/business validation and the deterministic template baseline, and create
the versioned 40-task corpus. The provenance record here proves metadata parsing
only. Real fitness suitability, live model quality, streaming, auth, operational
costs and approval safety have not been demonstrated.

The database container is stopped after verification, preserving the disposable
project volume and image for local reuse. No live provider calls, telemetry export,
AWS resources, real-user data, commits or pushes occurred. F1-02 remains blocked on
the owner's next authorization, not on an unreported technical failure.
