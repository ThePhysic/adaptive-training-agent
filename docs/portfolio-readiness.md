# Source portfolio and engineering release readiness

This is the curated, source-only portfolio repository. The original development
repository, its private records and complete history are preserved separately.
The current summary incorporates accepted F5-D5/F5-D10 engineering evidence and
the reviewed F5-D11 assessment; F5-D12 is the bounded documentation update.
Earlier [publication findings](implementation/f5-d2-publication-safety.md) and
`RELEASE-CANDIDATE.md`/`_release/` records describe their dated milestones, not
unresolved current defects. Historical reports and evidence remain unchanged.

## Current source-only status

| State | Capability / decision | Evidence and remaining boundary |
| --- | --- | --- |
| Validated offline | Explicit Save, fake generation/stream, review, revision, approval, immutable history and session submission | F5-D1 actual local journey; F5-D10 mandatory installed-Chrome workflow passed |
| Validated offline | Cancellation, idempotency/reconciliation, dependency recovery, release and restore | Controlled regressions and F5-D10 actual container drill; single process, synthetic data |
| Validated synthetic experiment | Counted replay, retained failures/holds, common scorer and dummy review | E9/E10 and native tests; no genuine model/human quality or provider-billing claim |
| Clean-checkout validation passed | Test-owned scratch setup, pinned dependency installation, fresh frontend build and isolated browser evidence | Accepted F5-D5; F5-D10 independently executed a fresh hosted checkout and all mandatory phases |
| Curated source prepared and uploaded privately | Fresh curated Git history; preserved original repository; reviewed exclusions retained | F5-D11 reviewed all four commits through a74e10c41fca740770428f4fdcff9b9f83c7c5bf; no confirmed sensitive disclosure identified |
| MIT committed | Project-owned source, copyright 2026 ThePhysic | [LICENSE](../LICENSE) is committed; [third-party notices](../THIRD_PARTY_NOTICES.md) retain their own terms |
| Owner affirmation recorded | Necessary rights and reviewed nonsecret historical context | Owner affirms no known employer/collaborator/coursework/third-party restriction and accepts reviewed identity/operational/curator context and both existing Actions histories; owner-supplied, not independent legal verification |
| Hosted CI accepted at F5-D10 | Browser, native integration, frontend, frozen guard, SDK and release/restore | [Exact source/run evidence](engineering-evidence.md#accepted-f5-d10-hosted-verification); all mandatory phases passed, job 6m31s |
| Separate final decision | Public repository visibility | Owner must approve the exact final source revision and visibility action after review; no public publication occurs through this documentation change |
| Optional polish | Narrated video, repository description/topics, badge | Existing storyboard and reviewed synthetic screenshots are sufficient; any recording/upload/metadata edit needs its own scope |

The source-only review found no technical requirement to activate a provider,
complete genuine evaluation or deploy AWS before publishing an honestly labelled
offline engineering project. Owner rights/disclosure affirmation is not a blanket
third-party license grant. Maintainer execution/publication approvals do not add
conditions to MIT's software grant.

## Accepted hosted evidence and historical failure

[Run 40765462914](https://github.com/ThePhysic/adaptive-training-agent/actions/runs/40765462914)
passed at **a74e10c41fca740770428f4fdcff9b9f83c7c5bf**, push event, attempt 1,
Ubuntu 24.04. Its mandatory phases all completed: locked dependency acquisition,
database/migrations, routine backend/frontend validation, actual installed browser,
remaining PostgreSQL/HTTP/TLS/fault integration, frozen/generated artifact guard,
isolated SDK compatibility, container release and synthetic backup/restore.
The [evidence map](engineering-evidence.md#accepted-f5-d10-hosted-verification)
reports each test population separately; no overlapping local/history totals are
added. A new documentation revision's CI result must be reported separately rather
than attributed to this already accepted run.

The [F5-D8 run](https://github.com/ThePhysic/adaptive-training-agent/actions/runs/40757298712)
failed the browser-version preflight. Its cause remains unknown. F5-D9 added finite
sanitized diagnostics without changing the version command, five-second bound or
strict grammar; F5-D10's success does not retroactively diagnose or erase D8.

## CI architecture and operational authority

The workflow remains unchanged: routine step 45m, native integration 15m, isolated
browser 3m and aggregate 75m, including setup/SDK/release reserve. F5-D2 selected
these finite bounds after Windows routine 22m02s/integration 6m52s measurements;
F5-D10 supplied actual hosted evidence. Bounds are not performance or free-usage
guarantees. All suites, fail-fast behavior, read-only repository permissions,
pinned actions, fake/no-export configuration, native/browser zero-skip guards and
frozen-artifact guard remain. No retry, parallel matrix or coverage reduction.

Maintainer-operated release commits/pushes and their automatic workflows need
explicit scope and included Actions allowance. Do not dispatch an extra run after
a push. Paid overages or budget/payment changes are not implied. Billing observations
may be owner-attested or delayed when APIs are unavailable; do not infer verified
zero cost from a green run or an inaccessible endpoint. Private/public visibility
is a separate decision.

## Deferred scopes

| Scope | Required before that scope, not source-only publication |
| --- | --- |
| JS bundles, installed environments, wheels or container/base images | Exact payload notice/license review and delivery, including React/Ajv full texts and applicable Psycopg LGPL, libpq/OpenSSL and other native/component obligations; see [distribution register](../_release/F5-D6-LICENSING-DECISIONS.md) |
| Real-model/provider execution | Account/model/parameter compatibility, input-count tariff and uncertain liability, retention/privacy and numerical permits; support Case 18223129 remains unresolved; no live probe authorized |
| Genuine independent human study | Curator appointment/independence, human-only cases, custody/authentication/commitments, exact configuration/final freeze, opening, actual execution and review collection; all separately gated |
| AWS and hosted observability | Optional and outside this source release; no deployment/export authority |

The installed app remains loopback-only, fake-provider and synthetic adult examples,
not production authentication, clinical validation or a participant deployment.
No real-model, genuine sealed-case or independent-human outcome is established.

## Reproduction and presentation

Start with the [local demonstration](local-demonstration.md),
[architecture](architecture.md), [evidence map](engineering-evidence.md) and
[recording storyboard](portfolio-walkthrough.md). Fresh browser screenshots are
ignored per-run outputs, not updates to accepted historical PNGs. Dependencies and
images require first-time acquisition; no air-gapped installation is claimed.
Keep test/demo data disposable and retain existing user volumes. No additional
engineering milestone is needed without a concrete defect or separately chosen
scope. Public visibility remains the next exact owner decision after review.
