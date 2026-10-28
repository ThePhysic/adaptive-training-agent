# Computer setup — future public rehearsal only

Do not install/configure anything just because this document exists. Owner approves
setup and public rehearsal separately; no genuine data is present during setup.
Use the curator's separate computer and personal OS account, not the developer's
login, shared/synced folder or borrowed cloud workspace. Do not transfer developer
home directories, credentials, caches, `.env`, `.git` or real account records.

## Requirements and provenance

Python **3.14.9**, matching `.python-version` (supported branch >=3.14,<3.15), a
terminal and an archive/checksum utility. Windows11 x64, macOS Apple Silicon/Intel
or a supported Linux distribution can be used if compatible Python/wheels exist.
No OS-specific install or fresh-wheel installation was verified on the curator's
device. No extra service is required. Allow roughly1GB free disk and2GB free RAM
for Python/venv/practice; these are planning allowances, not measured minima.

The kit's [requirements](f3-e8-requirements.txt) pin18 existing `uv.lock` packages,
including transitive dependencies and all permitted wheel hashes. Core versions:
Pydantic2.14.1, httpx0.28.1, psycopg/binary3.3.6, FastAPI0.162.0. No SDK/exporter
or new package version is introduced. The lock also brings opentelemetry-api as a
library dependency; there is no configured exporter. No pytest/uv/Node is needed
for the fixed runner. Do not loosen pins if installation fails.

Before transfer, the owner supplies the source kit ZIP, a separately checked
SHA-256, Python installer/package appropriate to the OS, and an independently
approved wheelhouse for that exact CPython/platform. Wheels must match the
requirements' existing lock hashes. The kit contains **no wheels/installers**.
Acquisition/installation is a separate setup decision; do not fetch anything
during offline execution. Different OS/architecture requires compatible wheels,
not reuse of the Windows developer's installed venv. Keep executables/license
notices together; Python and dependency licenses do not license private data.

Verify the ZIP before extracting. Compare the entire checksum with the separately
reviewed value, not a value downloaded alongside a substituted ZIP:

```powershell
# Windows PowerShell; local files only
Get-FileHash -Algorithm SHA256 .\future-training-f3-e8-curator-public.zip
Expand-Archive -LiteralPath .\future-training-f3-e8-curator-public.zip -DestinationPath .\curator-public
Set-Location .\curator-public
py -3.14 --version
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --only-binary=:all: --require-hashes --find-links ..\wheelhouse -r docs\implementation\curator\f3-e8-requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\curator_public_rehearsal.py
```

Do not overwrite an existing extraction directory. `py` is the Windows Python
launcher; if absent, use the approved3.14.9 executable's full path. No activation
or PowerShell execution-policy change is necessary.

```sh
# macOS: shasum -a 256; Linux: sha256sum
shasum -a 256 future-training-f3-e8-curator-public.zip
unzip future-training-f3-e8-curator-public.zip -d curator-public
cd curator-public
python3.14 --version
python3.14 -m venv .venv
.venv/bin/python -m pip install --no-index --only-binary=:all: --require-hashes --find-links ../wheelhouse -r docs/implementation/curator/f3-e8-requirements.txt
.venv/bin/python -m pip check
.venv/bin/python scripts/curator_public_rehearsal.py
```

On Linux replace the first checksum command with `sha256sum`. Expected Python:
3.14.9; pip check: `No broken requirements found.` Runner: one JSON object with
`result:passed`, `genuine_authority:false`; encryption/backup explicitly not
exercised. This output contains no genuine case or key. Patching Python/package
versions needs review; no unsupported workaround on an older runtime.

Disconnect Wi-Fi/Ethernet using the curator's normal controls for the approved
offline rehearsal. Do not change global firewall, drivers, BIOS or security policy.
Absence of network in a public run is not process-level containment for future
provider execution. Keep telemetry/sync/AI tools closed; no credentials needed.

## Troubleshooting

| Symptom | Safe action |
| --- | --- |
| No Python/venv, wrong version | Stop; owner supplies approved runtime/setup. Do not use system Python3.12/3.13 or install globally |
| No compatible wheel / hash mismatch | Stop; check OS, CPU, Python ABI and reviewed wheelhouse. No source build, `--trusted-host`, hash bypass or online fallback |
| psycopg import error | Binary wheel must match3.3.6/runtime/platform. No database/server installation |
| `ModuleNotFoundError` | Run from kit root with its venv; preserve folder layout. Do not copy one module or add unrelated site packages |
| Runner `stopped` | No automatic retry/change to cases. Record finite status; use the public kit to troubleshoot. Never upload future private errors/content |
| Permission denied | Use curator-owned local folder; do not run as admin/root or broadly relax permissions. Record unresolved setup |
| pip tries network | Stop; exact command requires no-index. Do not provide proxy/provider credentials |

Use normal OS file properties to verify the owner and authorized viewers. macOS/
Linux may set `umask 077` before creating the private rehearsal directory and use
`chmod 700` on that directory only. Windows: inspect folder Properties → Security
and inherited access; unresolved broad access blocks future genuine custody.
Do not recursively change permissions on home/system folders. Permissions and a
SHA-256 are not encryption, proof of independent custody or protection from an
administrator. Follow the separate storage guide.
