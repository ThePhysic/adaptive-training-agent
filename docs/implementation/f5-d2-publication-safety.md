# F5-D2 publication-safety assessment

2026-10-27. **Public publication is blocked pending owner decisions.** This is a
bounded audit of Git-visible working-tree source and metadata, not an approval to
publish Git history, a complete secret-detection guarantee or a legal license review.
Protected credentials, identities, login caches, raw captures and genuine evaluation
content were not opened. No historical/private evidence was edited or deleted.

## Scope and findings

The task-entry public inventory contained 585 files. The existing source-review
filter excludes ignored/private/dependency paths before reading content. Git's
staged diff was empty; no forbidden path was found among currently tracked file
names. Many accepted implementation files remain untracked: a push of the current
HEAD alone would not represent this reviewed application. No files were staged.

| Check | Finding and interpretation |
| --- | --- |
| Access-key / private-key patterns | Zero AWS access-key-shaped tokens or PEM private-key blocks in the public source scan. This is a limited pattern check, not proof no secret exists |
| Home-directory references | 34 Windows-pattern and 35 Unix-pattern matches, largely overlapping because a Windows path also matches a Unix substring. Nine files conservatively excluded from this review ZIP; the paths can reveal a host username. No private path value is reproduced here |
| IAM ARN account numbers | 75 matches in public fixtures; the scanned values were documented synthetic example accounts. No real account identifier was inferred from a private record |
| Email-shaped strings | Six matches: four reserved test-domain canaries; two are userinfo/endpoint-rejection URL fixtures misidentified as email. No human email inferred from them |
| Screenshots / PNG metadata | 58 public PNGs had only IHDR/IDAT/IEND chunks; no embedded text/EXIF chunks. F5-D1's desktop/mobile/error examples are public synthetic UI states. This does not replace visual review of every historical image before publication |
| Profile/plan/replay content | Public synthetic catalog, planner fixtures, authored prompt templates and replay outputs are intentional test material, not genuine unseen cases or actual provider captures. Do not mistake “no prompt telemetry” for “no prompt source code” |
| Custody / secrets / financial state | Reserved sealed/private-review paths, caches, `.aws`, `.env`, state/plans, dumps, database volumes, credentials and AGENTS.md excluded by boundary. No genuine population or custody record was accessed |
| Git history / authors / remote metadata | Complete historical blob, commit-author and remote-destination publication clearance was not performed. Current-tree sanitization cannot establish full-history safety |
| License / redistribution | No root LICENSE was found. Catalog README says its metadata was authored for this synthetic experiment and grants no broader repository license. Owner must choose rights/license/notice treatment; no license is supplied on their behalf |

The token check covers recognizable AWS keys/private-key blocks; it cannot detect
arbitrary tokens, encoded secrets, names inside images, unauthorized copied content
or semantic disclosure. Lockfiles refer to public package distributions; this
audit does not replace dependency-license review before source/image redistribution.
Public synthetic signing/commitment constants are test keys, not independent custody.

## Files withheld from the review archive

These existing records remain byte-identical in the repository. Only their export
is withheld. Paths/line numbers, not raw values, identify what the owner must review:

| File | Initial flagged lines |
| --- | --- |
| `docs/implementation/f1-03-handoff.md` |214,216 |
| `docs/implementation/f1-04-handoff.md` |217,229 |
| `docs/implementation/f1-05-handoff.md` |214,215 |
| `docs/implementation/f1-06-handoff.md` |242 |
| `docs/implementation/f4-03a-ci-follow-up.md` |92 |
| `docs/implementation/f4-03b-r5a-ci-devtools-follow-up.md` |146–152 |
| `docs/implementation/f4-03b-r5a-ci-startup-stabilization.md` |217–230 |
| `docs/implementation/f4-a1a-windows-home-isolation-assessment.md` |127; conservative Unix-pattern match |
| `infra/aws/README.md` |76,101 |

This is a **scoped source-review ZIP**, not a full repository or a publication-ready
release. Its embedded manifest lists exact included raw-byte hashes and these nine
exclusions. All included files match the working tree, and none of the existing
source is silently redacted or rewritten. Existing history links to excluded
documents will not resolve inside the ZIP; consult the owner's retained repository
for those records. The primary README/architecture/demo/evidence navigation is
included. No excluded historical file is represented as included or security-cleared.

The established full-inventory `scripts/review_source.py` snapshot remains useful
for internal preservation, but its default archive would still carry the flagged
historical paths. Therefore this package uses the same public inventory/raw-byte
hash boundary with an explicit nine-file omission, a separate `scoped-source-review-v1`
manifest and independent ZIP/working-tree verification. It must not be passed off
as a successful default full-inventory `verify-archive` result.

## Required owner decisions

1. Decide whether publication should use a reviewed curated export/new history or
   the existing repository history. Default recommendation: retain internal history
   unchanged and review a curated public scope. No history rewrite or new remote is
   authorized now.
2. Decide whether personal-path disclosures may be published, excluded, or replaced
   in a separately approved public copy with an explicit redaction record. Do not
   overwrite original handoffs. The current archive exclusion is not that approval.
3. Clear source ownership/license, dependency notices and any image redistribution
   requirements. No third-party rights or catalog expertise is inferred from tests.
4. Review the exact file manifest/staged diff, all intended screenshots and any
   recording, and any repository-author/remote metadata before publication.
5. Separately authorize any commit, push, hosted CI, repository visibility or upload.
   CI minutes, access and ephemeral artifacts must be approved. No broad staging or
   secret/custody export is permitted by a “review ZIP” request.

No immediate credential rotation or account operation is proposed: the current
scan did not establish an actual exposed credential. If later review finds one,
stop publication and obtain a separately authorized incident response rather than
printing or testing it. All provider, spending and genuine-evaluation gates stay closed.
