# Local container release and recovery

For separately prepared AWS definitions see [offline infrastructure](portfolio-readiness.md) (curated release-readiness substitute; original infrastructure reference omitted)
and the [execution checklist](planning/23-f4-03-cloud-execution-readiness.md).
Those files do not authorize deployment or change the local release boundary.

F4-01 provides an opt-in, synthetic-only release. There is one FastAPI process
serving the built React application and one PostgreSQL instance. It has no public
authentication, live model, telemetry exporter or monetary authority. Do not expose
it through a reverse proxy, wildcard bind, published bridge port or public host.

## Acquire and build

Use Linux Docker Engine, or Docker Desktop with the Linux engine and **Enable
host networking** applied (Desktop 4.34+). Host networking preserves the existing
loopback peer/Host/Origin boundary. Docker Desktop can require a restart. See the
[Docker host networking documentation](https://docs.docker.com/engine/network/drivers/host/).
Windows and macOS containers are not supported. Registry, PyPI and npm access is
needed to acquire images/dependencies; an air-gapped build is not promised.

From the repository root:

```powershell
docker build --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f4-01-baseline -t fata-release:f4-01-baseline .
docker build --provenance=false --sbom=false --build-arg FATA_RELEASE_VERSION=f4-01 -t fata-release:f4-01 .
```

The bases are digest-pinned, Python uses `uv.lock --frozen --no-dev`, and Node uses
`npm ci` with lifecycle scripts disabled. The final image has no Node, uv, HTTPX
or Langfuse SDK. The context allowlist excludes local credentials, `.env`, Git,
AGENTS.md, checkpoints, backups and evaluation artifacts. Build dependencies
can access package registries; runtime provider/export paths remain disabled.
Use an immutable image digest for a reviewed release rather than trusting a
mutable tag. The two example tags have identical business code/schema and
different version labels; they are not two historical application releases.

## Start, check and stop

Stop the development API and development PostgreSQL first: they use the same
ports. Keep its volume. Never run development and release instances together.

```powershell
docker compose stop --timeout 30 postgres
docker compose -f compose.release.yaml config
docker compose -f compose.release.yaml up -d --pull never --wait
curl.exe --fail http://127.0.0.1:8000/health
curl.exe --fail http://127.0.0.1:8000/ready
docker compose -f compose.release.yaml ps
```

Open `http://127.0.0.1:8000/` on this machine. Explicitly Save synthetic adult
preferences, Generate, Review, optionally Revise once, Approve, read History and
explicitly Submit structured session completion. Approval never means completion.
Other machines must not be able to connect. On Windows inspect the listener with
`Get-NetTCPConnection -State Listen -LocalPort 8000`; it must be 127.0.0.1.

The image defaults to local mode disabled. Compose explicitly acknowledges
`local-synthetic-only`. Settings reject public binds, multiple workers, live
providers and exporters. A Python loopback socket/DNS guard supplements those
controls; it is not an OS firewall or a sandbox against a hostile local operator.
Native libpq uses the fixed loopback database address. Host networking is an
intentional local constraint, not a cloud deployment recipe.

PostgreSQL must become healthy before the app starts. The entrypoint verifies
all migration checksums and applies missing migrations under the existing
transaction/advisory lock before accepting HTTP. Migration failure exits without
binding. `/health` means process liveness; `/ready` checks the dependency/schema
and can return 503 while liveness remains 200. It does not certify production
readiness. Compose marks an unhealthy container; it does not restart it for you.

The app runs as UID/GID 10001, read-only, with no Linux capabilities, bounded
tmpfs/logs and 512 MiB/one CPU limits. The stock PostgreSQL entrypoint initializes
its volume then runs PostgreSQL as its database user. The synthetic local database
uses trust authentication and one development role; this is not a production
credential/least-privilege design.

```powershell
docker compose -f compose.release.yaml stop --timeout 40 app
docker compose -f compose.release.yaml stop --timeout 30 postgres
# Remove stopped containers/network metadata, retaining the database volume:
docker compose -f compose.release.yaml down
```

SIGTERM permits bounded request cleanup (Uvicorn 35 seconds, Compose 40 seconds).
The original 30-second generation budget remains. Stop the app before PostgreSQL.
Do not use `down --volumes`, global pruning or recursive cleanup as a routine stop.
The default release database volume belongs to project `fata-release`, separate
from the development volume. Restart with `up ... --wait`; durable profiles,
approvals, keys and completions survive, while unapproved candidates disappear.
Retry an uncertain approval/completion with the original key and fingerprint.
Do not regenerate a plan to recover a committed approval.

## Reproducible recovery and fault exercise

Acquire the root test environment using the [development runbook](runbook.md).
Ensure both ports 8000 and 55432 are free, then run:

```powershell
.venv/Scripts/python.exe scripts/check_release.py
```

The drill waits at most75 seconds for strict, non-reusable binds on both ports.
Linux TCP `TIME_WAIT` can retain55432 after a stopped development PostgreSQL;
waiting does not share that address or stop its owner. A persistent conflict
fails with the exact port. Inspect `ss -H -tanp '( sport = :8000 or sport = :55432 )'`
on Linux and the relevant Compose project's status. Stop only a known owned
service; never kill an unknown listener or delete its volume. Hosted CI stops
and removes its own stopped integration-test PostgreSQL container without volume
deletion, then uses this same bounded preflight.

This opt-in script uses fresh uniquely named source and restore projects. It
executes the real HTTP synthetic journey, 120 measured fake generations, native
database lock barriers/connection termination, in-flight SIGTERM, database loss,
SIGKILL/restart, binary backup/restore, same-key durable readback and same-schema
image rollback. It aborts on a failed invariant and always stops its containers.
It retains its volumes and `.cache/f4-01/<run>/` for review. The private synthetic
state and backup stay ignored; only bounded metadata is suitable for shared
evidence. Do not print private-state.json or upload the archive to telemetry.

The executable backup/restore reference is `scripts/check_release.py`: stop the
app, keep PostgreSQL healthy, run `pg_dump -Fc` via a binary subprocess stdout
file, verify its SHA-256, stop the source database, start a fresh isolated database
with **zero public tables**, and pipe the trusted archive as binary stdin to
`pg_restore --exit-on-error --single-transaction --no-owner --no-privileges`.
Never use Windows PowerShell text redirection for a binary archive. Restore with
the same PostgreSQL major version and reviewed image/migration set. Do not restore
into an existing data-bearing schema. For real incident recovery, retain the
source unchanged and require an explicit restore target/data-loss decision.

The harness proves exact approved snapshot equality after profile revision,
approval/completion key replay after process loss, owner isolation and one row
each for plan, approval key, audit, session and completion key. Nine checksum
migrations and zero probe authorities are verified. Financial records, including
unknown liabilities, are included by the full database dump; this drill creates
no live authority or real financial records and cannot demonstrate provider-side
reconciliation. Native ledger fault tests provide the separate synthetic SQL
evidence. Unapproved candidates and native request-local state are not backed up.

Quiesced dump is a point-in-time recovery boundary: later writes would be lost.
There is no continuous/WAL backup or automated scheduler. Backups on the same
laptop are not disaster recovery. Retain synthetic drill files only for review;
after review remove only the explicitly verified run's cache directory and named
source/restore volumes. Verify project/volume names before any deletion; this
document intentionally gives no blanket destructive cleanup command.

## Release and rollback

Record image digest, source revision plus dirty diff, lock hashes, nine migration
checksums, configuration and a verified backup before an image change. Stop the
old process before starting the new one: no overlapping workers or replicas.
Start the database, migrate/check, start the selected digest and require readiness
and owned readback. Do not deploy if checksums/schema compatibility fail.

For a compatible image change, stop the app, set `FATA_RELEASE_IMAGE` to the
previous reviewed digest, then `up -d --pull never --wait app`. Retain the database.
Clear the environment override after the operation. The automated drill switches
the two same-schema labels and switches forward again. It also proves a changed
009 checksum blocks startup. This tests the release procedure, not compatibility
with an unimplemented historical release.

An application image rollback does **not** undo a migration. There are no downgrade
migrations. Future schema changes require an explicit old/new reader/writer
compatibility matrix, expand/contract sequencing where warranted and tests. The
current exact-schema readiness check can reject an older app against a newer
schema. Prefer a compatible forward fix; otherwise stop and restore a reviewed
backup into a separate fresh database with an explicitly accepted recovery point.

## Diagnose and recover

Use `compose ps`, `/health`, `/ready` and bounded `compose logs --tail 100 app`.
Ordinary application logs remain allowlisted metadata only. Never enable SQL
statement logging, raw exception dumps, provider payload logging or public access
to debug an issue. Stock PostgreSQL operational logs are local and bounded, with
error-statement logging suppressed; they are not an approved hosted exporter.

- No listener: inspect engine/host-network opt-in, occupied ports, acknowledgment,
  migration checksums and entrypoint's classified `release_start_failed`.
- Health 200, readiness 503: restore PostgreSQL availability; wait for health then
  probe readiness. Existing bounded failed requests stay failed; clients must
  explicitly choose any new generation. No automatic generation replay.
- Connection interruption: a generation fails safely; immutable approvals remain
  in PostgreSQL. Restart PostgreSQL if needed and perform same-key readback.
- Interrupted approval: preserve holds/reconciliation state and original key.
  Database authority wins; do not clear a hold to make readiness green.
- Graceful stop exceeds 40 seconds or forced crash: transient work is lost;
  restart and use durable key lookup/readback. Native regression tests cover
  uncertain commit reconciliation separately from the container stop drill.

No live OpenAI/counting request, Langfuse export or AWS deployment is activated by
these commands. See the [F4 handoff](implementation/f4-01-handoff.md) and
[AWS proposal](planning/22-f4-deployment-and-cost-plan.md) for evidence and gates.
