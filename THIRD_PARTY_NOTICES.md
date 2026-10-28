# Third-party notices and distribution scope

The root [MIT License](LICENSE) applies to project-owned material under the owner's
selected copyright notice, 2026 ThePhysic. Dependencies and third-party material
retain their respective copyrights and licenses. Operational review/upload gates
are instructions for this workflow, not additional restrictions on MIT's grant.

## Exact upstream notices prepared locally

| Component | Version | Original notice retained verbatim |
| --- | --- | --- |
| React / React DOM / Scheduler | 19.3.1 / 19.3.1 / 0.28.0 | [Meta Platforms MIT text](third_party/licenses/react-family-MIT.txt) |
| Ajv | 8.20.0 | [Evgeny Poberezkin MIT text](third_party/licenses/ajv-MIT.txt) |

The three installed React-family LICENSE files have identical bytes; one complete
copy preserves their common notice. The Ajv text is a separate complete copy.
They were copied from the pinned, locally installed packages, not invented or
replaced with ThePhysic's copyright. Hashes and source paths are in the
[D6 evidence](_release/f5-d6-review-evidence.json).

The source tree contains generated Ajv validators referencing its ucs2length
runtime helper. The fresh app bundle contains React/Scheduler copyright comments,
but no complete MIT permission paragraph. Preserve these upstream comments and
supply both full license files with any later bundle distribution. A root license
naming ThePhysic cannot substitute for their original notices. These files are
prepared here; the existing build and Docker packaging do not yet copy them into
dist/images. That packaging gap is a gate before distributing built artifacts.

## Source-only and built distributions

This review package contains project source, public synthetic data, documentation,
existing screenshots and the two legal-text copies. It excludes node_modules,
virtual environments, dist, wheels, container layers and database/state payloads.
Referencing a dependency in a lockfile does not include its entire implementation
in this source-only package. Copied/derived material, including generated helpers,
needs its own assessment; no blanket exemption for generated code is asserted.

Before shipping installed environments, JS bundles, wheels or images, review the
exact components actually included and preserve their actual license/NOTICE files.
Known gates include Psycopg LGPL-3.0 and corresponding GPL terms, bundled libpq and
OpenSSL notices, certifi MPL-2.0, TypeScript's ThirdPartyNoticeText, Python/PSF and
Debian/base-image components. Do not apply the project MIT label to these payloads.

See the [decision register](_release/F5-D6-LICENSING-DECISIONS.md) for artifact-specific
obligations, missing evidence and responsible next actions. This is a bounded
engineering inventory, not comprehensive legal clearance or permission to publish.
