# F5-D6 MIT licensing and empty private GitHub handoff

Completed the authorized preparation and the one authorized GitHub resource
creation. No license/source commit, remote configuration, source upload, push,
hosted CI, publication or provider/AWS operation occurred.

## Current state

| Area | Verified result |
| --- | --- |
| Curated local repository | Owner-approved directory basename future-training-portfolio-rc-f5-d3-source, separate from development |
| HEAD / branch / history | a4306aa47fd0535c5d2ead7b7bc3e0fab78a011a / main / exactly two commits |
| Start state | Clean, no remote, all 605 file hashes matched the accepted D5 inventory |
| Final source state | README licensing paragraph modified, eight new license/notice/review files; all uncommitted and unstaged |
| Root license | Complete OSI MIT permission/warranty body, with exact Copyright (c) 2026 ThePhysic |
| New GitHub repository | [ThePhysic/adaptive-training-agent](https://github.com/ThePhysic/adaptive-training-agent), private and empty |
| Creation evidence | One POST /user/repos, HTTP 201; subsequent repository GET 200 verifies name/owner/private/admin; commit GET 409 confirms empty repository |
| Remote contents | No initial commit, README, license, .gitignore, starter template, source or history |
| Original repository | ThePhysic/future-adaptive-training-agent and its local development tree were not modified or repurposed |

Creation used the existing authenticated gh 2.103.0 account ThePhysic; its private
repository scope was observed without exposing a token. Exact-name availability
was 404 immediately before creation. The POST payload was only:

```json
{"name":"adaptive-training-agent","private":true,"auto_init":false}
```

No --source, clone, import or remote option was used. API results were reduced to
approved identity/privacy/empty-state fields, never raw account or credential
responses. No token was requested, copied, exported, printed or persisted outside
the configured gh authentication flow. No write request targeted the original repo.

## Files prepared, not committed

- README.md: replace the outdated undecided-license paragraph with the selected
  MIT status, third-party scope and continuing source-upload prohibition.
- LICENSE: complete MIT text with owner-selected notice, UTF-8, no extra conditions.
- THIRD_PARTY_NOTICES.md: separate project license, actual upstream notices and
  source-only/built-distribution boundaries.
- third_party/licenses/react-family-MIT.txt: verbatim, common pinned React/React DOM/
  Scheduler license, preserving Meta's notice.
- third_party/licenses/ajv-MIT.txt: verbatim pinned Ajv license, preserving its notice.
- _release/F5-D6-LICENSING-DECISIONS.md: specific redistribution register and gates.
- _release/F5-D6-FIRST-PUSH-PLAN.md: future-only staged authorization and exact-ref plan.
- _release/F5-D6-HANDOFF.md: this structured report.
- _release/f5-d6-review-evidence.json: bounded, sanitized observations and checks.

Eight files are new; README is the only modified committed file. No executable,
lockfile, data, screenshot, historical report or previous manifest was rewritten.
There is no new commit ID: the licensing bytes are not part of accepted HEAD yet.
The proposed working source scope has 613 files; the existing HEAD still has 605.
Its exact path/hash/Git-state inventory is the generated D6 review source manifest,
not an assertion that all working bytes are committed.

## License/notice assessment

[Third-party notices](../THIRD_PARTY_NOTICES.md) and the
[decision register](F5-D6-LICENSING-DECISIONS.md) distinguish observed files from
legal/ownership assumptions. D6 enumerated 29 installed Python distributions and
32 license-related files, plus 109 npm lock entries, 84 installed packages and
82 notice/license files. These hashes and declarations are discovery evidence,
not comprehensive clearance. Other-platform packages were not downloaded.

A concrete finding: the fresh React/Scheduler bundle has copyright comments but
not the full MIT grant. Complete actual React-family and Ajv license files are
prepared in source; the build/image pipeline does not yet copy these notice files
into delivered dist/images. That requires later reviewed packaging work before
built-artifact distribution. No executable/build changes were made here.

Psycopg LGPL/GPL, wheel-bundled libpq/OpenSSL, certifi MPL, Python/PSF history,
TypeScript NOTICE and Debian/final-image obligations remain artifact-specific
review gates. Project MIT does not replace them. The current source-only package
excludes installed code, bundles, wheels and image layers, with the two declared
legal-text copies preserved. Root ownership, all asset/screenshot rights and final
public scope still need owner clearance. No external legal representation is made.
These known built/publication gates did not require uploading source or blocking
the separately authorized empty private repository creation.

The independent curator's future materials are absent. Root licensing does not
license unknown future human cases or substitute for custody/author approvals.
Prior undecided-license and NO-GO records retain their historical meaning.

## Fresh validation versus earlier results

Fresh D6 execution, exact argv/exit codes/timings in
[evidence](f5-d6-review-evidence.json):

```powershell
python -B scripts/review_source.py check
python -B scripts/export_contracts.py --check
python -B scripts/prepare_model_evaluation.py --check
python -B scripts/evaluate_models.py --check
python -B scripts/evaluate_baseline.py --check
git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check
```

The five Python commands passed: 202 public Python files parse native/3.13 grammar,
contracts remain current, all 150 expected comparison dispositions and frozen 40/40
software cases remain intact. Current freeze generation reproduces identically
against the unapproved D5 candidate: 121 inputs, fingerprint
1e5c64c50596443e7235779039612fa8cac1615c80a8b3fbc793edf938e6331a.
Neither live/monetary flags nor final freeze approval changed.

Additional local checks verify complete MIT text against the authoritative OSI body
(modulo line wrapping), exact copyright, unchanged upstream notice bytes, Markdown
links, public/source privacy inventory, no excluded files, and unchanged original
public files/status/HEAD. The initial license-read encoding failure occurred before
writes and was corrected by explicit UTF-8, without accepting altered license text.

The full 2,601 Python, 138 frontend, 130 cold-checkout, browser/build/recovery numbers
are accepted D5 history, not rerun in D6. No application code changed, so no full-suite,
new frontend build, database, Docker, Terraform, SDK, AWS or provider test run was
necessary or performed. D6 does not claim hosted CI or genuine evaluation evidence.

## Review archive and integrity

The local D6 ZIP contains 613 current working public-source files plus an embedded
SHA-256 manifest identifying base HEAD, each path and its committed/modified/new
status. All payload bytes are verified against the working tree; unchanged committed
files additionally match accepted Git blobs. The source manifest and ZIP SHA-256
sidecar are in the sibling D6 review directory. This is an uncommitted working-source
review snapshot, not a committed release or public-distribution approval.

No .git internals, dependency caches, node_modules, dist, credentials, AWS caches,
state, private records, AGENTS.md or nine excluded historical files are included.
The two third-party text files are deliberately included notices, not dependency
binaries or fabricated licenses. Fresh screenshot bytes and historical artifacts
were not generated or changed. Privacy pattern/metadata checks cannot establish
exhaustive secret, visible-pixel or legal clearance.

## Exact next approval boundary

[First-push plan](F5-D6-FIRST-PUSH-PLAN.md): first independently review this exact
working manifest and approve one licensing/documentation commit if desired.
No commit is currently authorized by D6. The owner's exact separate local path
remains the target; never use the original development repository.
Then separately approve the intended origin URL, resulting new source revision,
private source push and the one automatic push-triggered workflow, including
account-specific Actions allowance/cost and dependency/image acquisition.
Do not dispatch a second run automatically. Private visibility and empty state
must be reconfirmed immediately before any future upload; a preexisting ref is a
stop condition, not permission to overwrite or merge it.

Public visibility, binary/image distribution, live providers, money, genuine cases,
human evaluation and final freeze remain separately gated. No approval is made on
the owner's behalf. Stop here for independent review.
