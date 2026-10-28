# Approval implementation obligations — F1-01 contract supplement

Authority: ratified planning contract 13 and the owner's F1-01 instruction.
No approval service, candidate store, database transaction or reconciliation worker
is implemented in F1-01. `tests/specification` is an executable **reference model**,
not evidence that the future PostgreSQL implementation is crash/cancellation safe.

The F1-03/F1-06 implementation must preserve this order:

1. Authenticate owner and parse bounded request; fingerprint candidate ID, revision
   and hash canonically. Path/body identity must match. Owner is never request data.
2. Read committed owner/operation/key binding **before candidate access**. Return
   matching result or `409 idempotency_mismatch` without needing a live candidate.
3. Resolve and acquire the lineage guard. **Re-read committed idempotency after the
   wait, before candidate-state, expiry or hash rejection.** Another request may
   have committed while this request waited. Matching retries still return the
   same result; do not incorrectly return `candidate_already_approved`.
4. A lineage with an unresolved commit is closed to new approval, revision
   publication and eviction. Reconcile its durable approval identity first, then
   recheck the requested key. Expiry time for a first approval is the guard
   acquisition instant, subject to all subsequent validity checks in contract 13.
5. Validate the server-owned snapshot; freeze catalog/validator versions; lock and
   compare the profile row; atomically commit plan/key/identity/audit with DB unique
   constraints. Across different lineages, DB key collisions also require reading
   the winner's committed binding (or rolling back safely), not a partial write.
6. Treat commit and in-memory finalization as one guarded critical section.
   Client cancellation must not release the guard while commit/finalization is
   still running: shield an owned task and **await its completion**, including
   repeated cancellation, within bounded database/reconciliation timeouts.
7. A commit transport error or cancellation is **not proof of rollback**. Reconnect
   and query authoritative approval identity plus key binding. Committed → mark
   approved and return/recover the durable result; known rolled back → allow a
   subsequent valid attempt. If unresolved, quarantine the lineage and return a
   sanitized `503 reconciliation_pending`; refuse new approval/revision until
   reconciliation succeeds. Never reset it to ready on an arbitrary exception.
8. After a process restart no candidate survives; only owner-scoped durable retry
   remains. This does not introduce durable drafts, a queue or background workflow.

Mandatory later tests: same-key initial misses followed by guard wait/recheck;
different payload on the same key; cancellation before/during/after commit;
repeated cancellation; committed and rolled-back reconciliation outcomes;
unavailable reconciliation blocking both approval and revision; DB uniqueness,
profile row races and true process restart. F1-01 reference tests cover the two
ordering obligations only. PostgreSQL proof remains F1-06 acceptance work.
