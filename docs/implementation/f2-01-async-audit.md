# F2-01 async audit before implementation

Scope: owner-authorized F2-01 only; F1 is owner-accepted and closed. Read the local
instructions, planning 01/02/09/12–14 and final F1 acceptance evidence. Historical
planning status labels do not override the owner's authorization.

## Existing capabilities to preserve

| Area | Existing behavior / evidence | Decision |
| --- | --- | --- |
| Generation deadline | One server-owned start before body intake, 30-second deadline through SSE terminalization; fake-clock tests | Reuse `Deadline`, no new generation timer/budget |
| Retry ownership | `Run._call` owns the one provider transport retry; all attempts reserve/settle conservative tokens | No HTTP adapter retry loop or nested provider retry |
| Admission | Shared one run/principal, two total, held through terminalization and cleanup | Keep unchanged; experiment is not another generation entry point |
| Read tools | Bounded strict names/arguments/results, captured owned profile; actual catalog filtering depends on profile | Keep profile dependency explicit; do not parallelize dependent filtering or add tools |
| SSE cancellation | Owned disconnect/watchdog tasks drained; incomplete preview non-approvable | Preserve accepted implementation/tests |
| Approval | Guard through DB commit/memory finalization; repeated cancellation shielded and awaited; unknown outcome quarantined and reconciled | No change to transaction, lock order, idempotency or recovery |
| SQL cleanup | Short-lived native connections, local timeouts, actual row-lock/commit/connection-interruption tests | Run accepted native regressions; no new pool or service |
| Privacy | Bounded local spans, strict attribute/value allowlists, safe console; cooperative test egress guards | Extend fixed metadata only; no content or identity tracing |

## Concrete gaps and bounded work

1. **Diagnostic correctness:** `Run.execute` calls `_result` before appending
   CANCELLED/FAILED on cancellation. Tracing therefore records the preceding
   state. The generic span exception handler also overwrites the explicit
   `deadline_exceeded` cause with `cancelled`. Reproduce these observations before
   fixing their ordering/classification; preserve cancellation propagation and
   accounting.
2. **HTTP-read integration learning:** F1 has typed browser HTTP and internal
   read tools, but no Python async HTTP read boundary demonstrating bounded
   streamed bodies, typed partial results and fail-fast sibling cleanup. Add a
   contained offline experiment using the already locked development HTTPX client
   with explicitly injected local transports. It is not a new production source,
   generation endpoint or provider integration. Keep the dependency lock and
   frozen baseline unchanged.
3. **Parallel-read evidence:** current application catalog reads are local and
   profile-dependent; parallelizing their filtering has no demonstrated value.
   Compare the same independent owned profile, raw catalog and bounded optional
   owned-history reads, then filter only after required reads finish. Use actual
   existing DTOs/catalog and strict identity-scoped routes. Do not claim atomic
   cross-request snapshots or faster real-model generation.
4. **Resource lifetime proof:** new batch reads need a structured task lifetime,
   a parent-owned deadline, no hidden retries and explicit optional-history
   degradation. A required-read failure must cancel/await every sibling; an
   optional authorization/integrity failure must not be silently degraded.

No F1 database correctness blocker was identified by this inspection. New fault
evidence will distinguish controlled transport/ASGI experiments, native SQL
regressions and reference-model tests. F2-02 caching, a contained LangGraph
comparison and completion/feedback remain outline-only work.
