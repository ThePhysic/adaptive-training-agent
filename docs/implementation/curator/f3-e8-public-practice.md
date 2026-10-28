# Public authoring guide and offline rehearsal

Practice only. The actual curator run is not performed by publishing this guide.
The runner accepts no paths or other arguments; genuine case authoring remains
denied. Keep the shipped source/data unchanged so the rehearsal is reproducible.

## Understand the future input contract

The [domain contract](../../planning/12-f0-domain-contract.md), shared schemas and
catalog are authoritative. Future inputs are fictitious adult general-wellness
preferences, not real people, medical histories, injuries, biometrics or free-form
health notes. Supported profile values:

| Field | Supported values/bounds |
| --- | --- |
| adult | true; no coercion from text/integers |
| goal | general_strength / general_conditioning |
| equipment | bodyweight / dumbbells_and_bodyweight |
| experience | beginner / intermediate |
| days_per_week | integer2/3/4 |
| session_minutes | integer20/30/45 |
| excluded_ids / excluded_tags | Known catalog values; maximum12 IDs/8 tags; feasible combination required |

The ten-case quality contract has empty request_text, expected plan, and all common
hard checks. It is not the medical/abstention/control population. Future canonical
CaseContent also binds opaque ID/ordinal, supported read tools, actual coverage,
catalog/configuration/selection, origin and attestation references. The canonical
representation is strict UTF-8/no BOM, duplicate-key-safe finite JSON <=8192 bytes,
sorted keys/constraint collections and materialized defaults. No developer
expected workout should be copied into a genuine input. Do not hand-invent hashes,
origins, approval references or claim that a genuine envelope is currently usable.

## Public rehearsal sequence

1. Verify the package checksum, Python and local dependencies as in setup. No
   network, application startup, services, credentials or Git command is needed.
2. Run the fixed public runner. It copies **existing ME-D01-20 / fixture-01**;
   this is not an eleventh/new independent case. The source profile and origin are
   checked by the unchanged E4 canonicalizer.
3. Observe `valid_control:true`, `domain_valid:true`: baseline feasibility and
   independent plan validation use the actual existing functions. No generated
   model output or human judgment is involved.
4. Observe `invalid_control_rejected:true`: the same public control with adult
   false is rejected. No invalid genuine input is repaired or accepted.
5. Observe `canonicalization_stable:true`: whitespace/key encoding differences
   canonicalize identically. The original hard rules are not changed.
6. Observe `nonsecret_commitment_repeatable:true` and `tamper_detected:true`:
   existing purpose-bound HMAC uses public `bytes(range(32))` and the all-zero
   synthetic configuration context. An altered byte string does not verify.
   No random secret, real seal or approved freeze is generated.
7. Observe `public_overlap_detected:true`: the input is in the47-identity public
   exposure export, which is source-hash-bound to the existing public index.
   Known overlap is expected in practice. Historical private exposure/semantic
   novelty cannot be established by this export. Duplicate internal index entries
   are rejected; a different ID/key never makes exposed content unseen.
8. Save the sanitized JSON for **public dummy storage** practice. Do not modify the
   report to declare encryption or curator participation. In Windows, avoid
   PowerShell5 UTF-16 redirection if later comparing bytes:

   ```powershell
   $practice = & .\.venv\Scripts\python.exe scripts\curator_public_rehearsal.py
   if ($LASTEXITCODE -ne 0) { throw 'Public practice stopped' }
   if (Test-Path -LiteralPath .\public-report.json) { throw 'Existing report; stop' }
   [System.IO.File]::WriteAllText((Join-Path $PWD 'public-report.json'), ($practice + "`n"), [System.Text.UTF8Encoding]::new($false))
   Get-FileHash -Algorithm SHA256 .\public-report.json
   ```

   On macOS/Linux, after confirming no file already exists:
   `(set -C; .venv/bin/python scripts/curator_public_rehearsal.py > public-report.json)`.
   Stop on nonzero exit. The developer practice report is not a curator attestation.
9. Follow the storage guide with this public report only; compare ciphertext and
   restored plaintext checksums. Return sanitized statuses only after a separately
   approved curator rehearsal. Keep the declarations blank until a real human
   can truthfully review/sign them privately.

## What does not yet work for genuine authoring

Low-level ProfilePreferences, catalog filtering, baseline feasibility and domain
validation already work. E2 metadata coverage flags are declarations, not an
automatic proof that ten unseen cases satisfy semantic coverage/independence.
The current canonical_fixture accepts only the fixed exposed profiles; it rejects
new independent origin/content. Genuine key custody, independently authenticated
commitments/opening, complete private exposure review and arbitrary-case financial
authority are not supplied by this kit. Do not patch origin/fixture IDs to bypass
that barrier. Review a narrowly scoped future human-only authoring/validation
interface and final freeze before commissioning any genuine cases.

Future coverage: ten feasible human-authored inputs collectively cover the eight
goal/equipment/experience rows,20/30/45 minutes,2/3/4 days and feasible known ID/tag
exclusions. Curator reviews exact and semantic overlap against all public and
privately recorded prior exposure. A hash only detects exact normalized identity;
it cannot establish novelty, honest authorship or full prior exposure.
