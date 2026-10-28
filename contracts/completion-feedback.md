# F2-04 — Explicit session completion and feedback contract

Scope: owner-authorized F2-04, synthetic localhost only. Defined before persistence
implementation. This extends the accepted slice without changing contracts 12–14.

## Domain and explicit action

One immutable session record per `(owner, approved_plan_id, day_index)`. Sessions
come from the actual stored approved snapshot, never a client plan or today's
profile/catalog. Approval, generation, viewing a plan and selecting form values
never record completion. Only an explicit **Submit session record** POST does so.

Status is `completed | partial | skipped`. Optional feedback is perceived effort
`easy | moderate | hard` and session rating integer 1–5 (1 lowest, 5 highest), each
independently nullable. Skipped sessions require both feedback fields null. These
are self-reported synthetic categories, not performance, safety or clinical data.
There are no notes, dates supplied by the client, measurements, reasons for
skipping, diagnoses, medical history or unrestricted text. UI defaults to no status
selection and no feedback. Do not infer completed status from approval.

## Version, identity and duplicate policy

Submission includes `expected_revision=0`, the reviewed immutable approved-plan
candidate revision (1 or 2), its canonical content hash and a bounded 1–128 character
idempotency key using existing `[A-Za-z0-9_-]` rules. The URL supplies plan/session;
the server supplies owner. No client owner, plan body or completion identity.

First accepted Submit creates revision **1**. There is no edit, replacement,
correction, deletion or repeated workout occurrence in this bounded unit. A session
means the numbered session of that particular approved weekly snapshot, not an
unbounded recurring activity. A later correction/revision policy needs separate
design; do not overwrite records silently. Expected revisions other than integer
zero fail validation. Reusing a create revision after a record exists with a new
key conflicts; it cannot update revision 1.

The durable owner/operation/key binding covers normalized complete request fields
(including explicit null defaults), plan ID and session index. Matching same-key
retries return the identical original record, including after restart or profile/
catalog changes. Same key with a different fingerprint returns 409
`idempotency_mismatch`, even across sessions/plans. Different keys targeting an
already recorded session return 409 `session_already_recorded`, including identical
bodies. Keys are not shared with approval's operation/key namespace.

## HTTP and readback

- `POST /api/v1/plans/{plan_id}/sessions/{day_index}/completion`: explicit Submit;
  200 on first acceptance or matching retry, returns the full durable record.
- `GET` at the same path: owned session record or 404 `not_found`.
- `GET /api/v1/plans/{plan_id}/completions`: owned approved plan's records sorted
  by day index, at most four. Empty means no submitted records. No pagination is
  needed for four numbered sessions.

Wrong-owner or unknown plans are indistinguishable 404; an invalid session of an
owned plan is 422 `invalid_request`. Changed plan revision/hash is 409
`plan_mismatch`. Invalid schema/extra fields, noninteger/bool ratings/revisions,
unknown categories, skipped feedback, duplicate JSON keys or nonfinite JSON fail
422. Completion body intake is capped at **4096 bytes**, including chunked input;
oversize is 413. Query parameters are forbidden. Existing localhost identity,
body-intake timeout and no-store/security headers apply. No completion write/read
tool is exposed to the model.

## PostgreSQL transaction and ordering

PostgreSQL is the sole record/idempotency authority. A Submit transaction takes an
owner/key advisory transaction lock, rechecks the committed binding, reads the
owned immutable plan, then takes the owner/plan/session transaction lock before
checking uniqueness and inserting record + binding atomically. Lock namespaces
are separate from approval. Each operation acquires one key then one session;
there is no profile lock or reverse path. Collisions may serialize unrelated work
but never establish authorization. SQL owner predicates and unique constraints do.

Constraints enforce owned approved-plan references, actual session membership,
snapshot revision/hash agreement, bounded categories/ratings, unique session,
unique owner/key and one binding per record. A deferred binding constraint prevents
a standalone record from committing without its key. Records and keys are
append-only, including TRUNCATE protection; approved-plan bytes are never updated.
Minimal audit is the database-generated submission timestamp on the record and
fixed operation on the key, with no copied profile or plan body.

Explicit writes use the accepted cancellation-safe owned-task helper, bounded
transaction time and connection cleanup. They may complete after a disconnect;
caller cancellation is propagated only after the owned work settles. No orphaned
task or memory finalization is needed. A COMMIT error/timeout may mean success:
return retryable 503 `reconciliation_pending`, never claim rollback. An explicit
same-key retry waits on the authoritative transaction key lock, then sees the
committed result or safely performs a new atomic insertion after rollback. No
background recovery, durable draft or in-memory quarantine is introduced.

## Privacy, UI and retention

Only synthetic data in this development release. Records/key bindings remain in
the local PostgreSQL volume with their approved plans until deliberate development
reset; no automatic expiry or production erasure policy is implied. Preserve keys
while the records exist. Do not reset a volume as routine test cleanup; tests use
isolated disposable schemas. Production retention/deletion, backup suppression,
real authentication and participant consent remain separately gated.

UI shows forms only against durable approved readback, labels them separately
from plan review, and reads saved records after Submit. One pending exact request/
key stays fixed during an uncertain outcome; explicit retry reuses it. There is
no automatic POST retry. Definite conflicts prompt readback rather than a new-key
overwrite. Switching principal/unmount aborts client work and clears old local
state; late responses cannot populate the new principal's view. A reload uses
owned readback; page-local retry keys are not persisted in browser storage.

Telemetry uses existing metadata-only local sinks. Add only fixed route/stage/
reason labels; do not trace status/ratings/effort, owner/plan/session IDs, keys,
fingerprints, payloads or SQL text. Canary and egress checks cover new routes.

Acceptance requires actual SQL/HTTP concurrency, rollback, response-loss, uncertain
commit, cancellation, restart, ownership and immutable-snapshot tests, plus UI and
installed-browser evidence. Model/reference tests alone do not establish SQL
correctness. F3 and external participants remain unauthorized.
