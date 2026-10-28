# Remaining F2 work-unit outline

Status: proposed sequencing only, 2026-10-24. F1 is owner-accepted and closed.
Only F2-01 is currently authorized. Each later unit requires separate owner
authorization. This outline does not change ratified domain/lifecycle/budget rules.

| Unit | Proposed work | Evidence gate before review |
| --- | --- | --- |
| F2-02 — Bounded caching and performance | First measure a specific repeated catalog-read cost. Compare uncached/cached identical workloads; cache only immutable, version-keyed catalog data with explicit bounds/invalidation. Do not cache owner profiles, approved-history reads, candidates, admission decisions or approvals. Do not introduce Redis or a service. | Exact keys/version/limit policy; cold/warm/uncached counts and times; catalog-change/invalidation/size tests; equivalent validator outputs and unchanged privacy/ownership/request limits. Reject caching if the measured value does not justify it. |
| F2-03 — Contained LangGraph comparison | A separately isolated synthetic workflow spike comparing the current typed flow against a graph/checkpoint/resume path. Explicitly design checkpoint content/retention before adding the dependency. Keep graph state outside authoritative approval, identity and candidate publication. | Same cases and failure workload; one real local checkpoint/restart/resumption demonstration; count dependencies, state, cleanup and complexity; evidence-based keep/reject recommendation. No main-path adoption implied. |
| F2-04 — Explicit completion/feedback and F2 closure | Design bounded typed owner-scoped Submit contracts and migrations for completion/feedback against actual approved plans; define revision/idempotency/duplicate policy and synthetic retention rules first. Add narrow UI only after those contracts are reviewed. Consolidate operational/fault evidence. | Explicit action only, cross-owner/forged/duplicate/concurrent/failure/restart tests, real SQL evidence, no model writes, no silent mutation of approved snapshots; complete F2 gate report and runbook. |

## Decisions carried forward from F2-01

- Keep direct in-process services in the application: manufacturing loopback HTTP
  requests to local catalog/profile data would add overhead without a measured
  integration need. The HTTP-read experiment uses controlled local transports;
  it is reusable evidence, not a new source of authoritative application state.
- Independent raw reads can overlap. Profile-dependent filtering/validation waits
  for the required profile/catalog. Separate HTTP reads do not establish an atomic
  cross-resource snapshot; publication/approval must still perform their ratified
  freshness/version checks.
- One caller-owned deadline and budget; one provider retry owner. Adapters do not
  acquire extra generation capacity or hide retries. Optional availability failure
  is explicit; authorization/integrity failure is fatal.
- Prefer structured child-task lifetimes over unowned `gather`/background tasks.
  Do not change the already accepted shielded approval critical section into
  cancellable read-task behavior.
- Preserve the frozen F1 corpus/catalog/source/lock provenance. Any future
  dependency experiment needing a different lock requires an explicit provenance
  strategy; do not silently overwrite the historical baseline report.

No caching, graph/checkpoint, completion/feedback schema, endpoint, UI or durable
workflow is implemented by this outline. Live models, hosted telemetry, AWS and
external participants remain separately gated regardless of unit authorization.
