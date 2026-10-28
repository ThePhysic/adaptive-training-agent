# F5-D6 third-party licensing and notice decision register

Owner decision: MIT; copyright (c) 2026 ThePhysic. The exact OSI permission and
warranty body is preserved in the uncommitted root LICENSE. Earlier undecided-license
reports remain historical; they are not rewritten. No license commit or public
release is authorized. This assessment concerns the curated source candidate only.

## Evidence and scope

D3's inventory covered eight installed Python declarations and 109 npm lock entries.
D6 additionally enumerated 29 installed Python distributions / 32 license-related
files and the same 109 locked npm dependencies: 84 are installed on this Windows
platform, with 82 license/notice files found. The 25 other-platform entries were
not downloaded. Only public installed package metadata, license files, known
builder/generated-source code and the existing fresh bundle trailer were read.
No private records, credentials or curator files were accessed. File names, versions
and SHA-256 hashes are retained in [D6 evidence](f5-d6-review-evidence.json).

Enumeration and SPDX declarations are discovery evidence, not a complete reading,
rights opinion or redistribution approval. Separate LangGraph/Langfuse experiment
locks and final Linux images are not fully enumerated by this Windows environment.
No third-party code ownership was transferred to ThePhysic by selecting MIT.

## Artifact / obligation decisions

| ID | Artifact and verified finding | Required action / responsible approval | Gate |
| --- | --- | --- | --- |
| L1 | Project-owned source: owner selected MIT with exact copyright fields | Root LICENSE prepared; owner/reviewer reviews scope before a separately authorized commit. Keep complete MIT text with copies/substantial portions | Local preparation complete; commit not authorized |
| L2 | React 19.3.1, React DOM 19.3.1, Scheduler 0.28.0 share a byte-identical Meta MIT LICENSE | Verbatim common notice copied to third_party/licenses/react-family-MIT.txt. Future bundles must accompany original copyright and full permission/warranty text | Notice ready; built-artifact packaging remains open |
| L3 | Ajv 8.20.0: actual MIT LICENSE; generated validators refer to its runtime helper | Verbatim Ajv notice copied separately. Preserve it when redistributing copied/generated helper material; do not assume all generator output is exempt | Source notice prepared; exact final-bundle contents still need inventory |
| L4 | FastAPI, Pydantic/core, AnyIO, h11 and other installed MIT dependencies; Starlette/Uvicorn/httpx/httpcore/idna BSD dependencies | Source-only imports/locks do not ship these installed packages. If redistributing their code, wheels or environments, carry the actual copyright, conditions and disclaimers; preserve BSD no-endorsement terms where present | Required before dependency payload distribution |
| L5 | Psycopg and psycopg-binary 3.3.6 metadata and actual license files identify LGPL-3.0-only | Preserve actual LGPL and applicable GPL v3 text and notices, including extra permissions. For a conveyed combined work, assess section 4 notices, reverse-engineering/debugging rights, replacement/relinking and corresponding-source/application-code route; installation information where applicable | Exact wheel/container compliance and owner review required before binary/image redistribution |
| L6 | Installed Windows binary wheel tag cp314-cp314-win_amd64 contains libpq, libssl-3 and libcrypto-3 DLLs plus extension modules | Determine exact library versions, copyright/source provenance and notice obligations for these precise artifacts. PostgreSQL and OpenSSL are separate components; do not treat all native libraries as Psycopg LGPL or project MIT. No matching Linux wheel audit is claimed | Unresolved for binary releases; does not block an empty repo |
| L7 | certifi 2026.10.23 declares MPL-2.0, beyond D3's eight-package subset | If included in a distribution, preserve its actual notice/license and meet covered-file source-availability requirements. Do not infer this relicenses the entire application | Payload-specific gate; no certifi code is shipped in the source archive |
| L8 | Apache-2.0 components include TypeScript 5.9.3, xml-name-validator, yaml-ast-parser, Python OpenTelemetry API/pytest-asyncio/tzdata | When included, retain applicable license/copyright/attribution and supplied NOTICE material; identify modifications. TypeScript supplies ThirdPartyNoticeText.txt, which must be assessed for included code | Runtime/build-tool payload inventory needed; no generic fabricated NOTICE supplied |
| L9 | BSD-2/3, ISC, Python-2.0, PSF-2.0 and BlueOak-1.0.0 appear in installed/locked packages | Carry their actual license/copyright/conditions/disclaimers where required, including Python historical license chains and derivative-change summaries where applicable. Preserve no-endorsement/trademark limitations | Exact-payload review required; no license chosen merely from a short identifier |
| L10 | MIT-0, CC0-1.0 and dual (MIT OR CC0-1.0) npm entries exist | Keep provenance and actual texts; distinguish MIT-0/CC0 from MIT's notice condition. Do not silently choose or alter dual-license terms | Review selected distribution's actual files/branch |
| L11 | Dockerfile pins Node, uv and Python/Debian images; final image copies Python env, app files and frontend dist | Audit the exact final layers and native packages, /usr/share/doc copyright records, corresponding source/offer requirements and upstream notices. Build-stage presence alone does not prove final redistribution | Images/base layers not redistributed or audited fully in D6 |
| L12 | Catalog README describes project-authored synthetic metadata; public evaluation inputs/replay fixtures are developer-exposed synthetic material | Owner confirms rights/provenance for project-authored data under the root grant. Preserve catalog provenance and historical exposure labels; no professional/clinical validation or genuine unseen quality claimed | Final ownership/source-scope sign-off before publication |
| L13 | Existing screenshots/documentation are public synthetic app evidence; D5 checked 58 PNGs for metadata | Keep image bytes/historical evidence intact. Owner reviews all visible content, contributor/asset rights, trademarks and disclosure before public release | Full visible-content/rights clearance remains open |
| L14 | Full source import audit found no newly identified foreign source header in reviewed non-generated application/tests; generated material has separate treatment | This is a bounded scan, not proof of sole ownership or a complete copying-history audit. Owner must resolve any outside contributions or copied assets discovered later | Publication gate, no external legal representation |

## Built frontend finding

The current app.js trailer lists React and Scheduler copyright/license comments,
not the complete MIT grant. The default build generates only app.js, app.css and
index.html; it does not emit the new third_party license files. These verified
upstream files are ready in source, but publication of standalone dist or an image
requires a later reviewed packaging change (or an explicitly verified accompanying
notice delivery). No build, approval, financial or freeze code was changed here.

## Psycopg / native boundary

The existing Windows wheel's two license files were hashed; that is not complete
native-library clearance. The binary payload includes libpq and OpenSSL-family DLLs.
Do not equate the installed Windows payload with the Linux wheel and Debian packages
in a final image. Before binary release, assemble the exact bill of materials,
license texts, version-matched source availability and workable replacement/relinking
instructions. Determine applicable LGPL installation-information duties rather than
assuming either automatic applicability or automatic exemption. This remains owner
review work; no source download, image mutation or distribution occurred.

## Primary references and limitations

- [OSI MIT](https://opensource.org/license/mit): exact root permission/warranty body.
- [OSI BSD-3-Clause](https://opensource.org/license/bsd-3-clause): source/binary notice and endorsement conditions.
- [Apache 2.0, section 4](https://www.apache.org/licenses/LICENSE-2.0): license, modification and NOTICE treatment.
- [Mozilla MPL 2.0, section 3](https://www.mozilla.org/en-US/MPL/2.0/): covered source/executable forms and notices.
- [Psycopg project's LGPL text, section 4](https://raw.githubusercontent.com/psycopg/psycopg/master/LICENSE.txt): combined-work requirements; installed pinned license bytes remain the artifact-specific evidence.
- [Psycopg 3 installation](https://www.psycopg.org/psycopg3/docs/basic/install.html): binary installation includes client libraries. Current docs are not proof of the exact 3.3.6 wheel contents.
- [PostgreSQL license](https://www.postgresql.org/about/licence/): separate copyright and notice terms for PostgreSQL/libpq material.

GNU's direct LGPL HTML/text retrieval timed out; the actual installed license and
Psycopg upstream text were used instead. A psycopg2 documentation page was encountered
but is not used to characterize the project's pinned Psycopg 3 license. Public
reference retrieval did not access an AWS/provider account or GitHub source upload.
No source-only/notice finding establishes complete legal clearance for binaries,
containers, all platform variants or public publication. The empty private GitHub
repository is not a license/publication or paid-CI approval.
