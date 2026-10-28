# Offline provider and spending boundary — F3-04C

F3-04B is owner-accepted for its offline scope. F3-04C adds separate, inactive
financial-authority preparation and a fixed single-request provider assembly.
F3-03C's live **NO-GO** remains: no counting tariff/retention proof, live financial
authority or provider transport is activated. Local TLS dials only `127.0.0.1`.

Updated: 2026-10-25. Implements the offline portion of approved planning document
[17](../docs/planning/17-f3-experiment-and-spend-plan.md). This contract does not
authorize a provider call. The owner ratified document 18 amendments A–C for
**offline implementation/testing only**. The count-aware exception below is now
normative for that local pathway. Historical F3-01/F3-02/F3-03A reports retain
their original evidence and policy context.

## Execution and token admission

Application configuration remains `fake` only. The explicit Python-only
`ResponsesReplay` integration accepts exactly HTTPX `MockTransport`, or exactly
`LocalTLS` in explicitly counted mode with a ledger/scope and positive synthetic
quote. It never accepts arbitrary clients/default transports, credentials or a
base URL. Its source label is `replay`; local TLS is synthetic protocol replay
over loopback, not real model evidence. Legacy uncounted
input allowances are fixture reservations, **not real-input token estimates or
proof**. Counted replay instead admits its mock count as specified below.
Production HTTP routes acquire no live-provider mode. The existing
typed Agent owns admission, deadline, dispatch, repair/retry and independent
validation. No second planner or model write tool is introduced.

Unchanged: 30 seconds, four read dispatches, **three generation attempts**, one
repair, one transport retry, cumulative **16,000 inference input / 4,000 inference
output**, one run/principal and two globally. `BudgetLimits.provider_attempts`
stays three. The explicit `ResponsesReplay(counted=True, ...)` pathway additionally
enforces **three counting attempts and six combined attempts**. Initial generation,
continuation, repair and retry each need a fresh independent count. Failed,
cancelled and uncertain claims consume counters conservatively before transport;
no endpoint has a separate retry allowance. The Agent alone owns retry. Counting
errors stop without retry; only a generation failure with validated known usage
and a classified retryable terminal status may use the shared retry. Ambiguous
transport failures stop. No automatic generation replay exists.

Counts are not inference usage. Reserve the validated integer count `N` against
remaining input, and at most `min(2000, remaining output)` before generation.
Unknown generation usage retains its whole allowance. Exact terminal usage,
including reasoning within output and cached/write partitions within input, is
settled once; cumulative stream snapshots are not summed. Count/wire counters
are separate internal numeric metrics. Fake metrics remain simulated; the legacy
uncounted replay mode remains fixture-only, using its original allowances and
three calls. Neither mode can contact a provider; counted local TLS may contact
only the controlled loopback test endpoint.

Serialize and freeze one bounded generation body before counting. Copy exactly
`model,input,instructions,tools,tool_choice,parallel_tool_calls,reasoning,text,
truncation` to the count body. Normalize `truncation=disabled` once before freezing.
Generation-only storage/stream/tier/output/cache fields remain fixed and bound.
Unknown fields, provider conversations, references, personality, remote files,
hosted tools and summaries are rejected. Preserve ordered completed native items,
call IDs, checked tool results and opaque encrypted reasoning without decoding.
The count ticket binds original context, native history, attempt, allowances and
frozen generation bytes; it is single-use and memory-only. No reconstruction or
native-state change after counting is allowed. There are at most 30 input items
under existing native-output/tool/repair bounds; wire bytes remain 65,536.

Count replies must be JSON <=1,024 bytes with exactly `object=response.input_tokens`
and strict integer `1 <= input_tokens <= remaining input`. Redirect, wrong MIME,
malformed/duplicate/extra fields, missing/oversized/count-overrun responses,
cancellation and deadline fail closed without generation. After generation,
reported input must equal `N`, even downward. A model/tier/cache-price or usage
discrepancy freezes the project and retains unresolved costs. Actual reported
usage is retained without clamping; client admission cannot undo provider overrun.

**Live admission remains unverified and unconditionally blocked.** The documented
counter includes formatting/tool context, but no live model/schema/native-state
compatibility, alias stability or count-to-usage equality has been measured.
[Official token-counting guide](https://developers.openai.com/api/docs/guides/token-counting),
[count reference](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count).
Counting pricing/maximum liability and endpoint-specific retention are unverified.
A numeric count is not billing evidence. Even a hypothetical enabled permit hits
the unconditional `real_input_admission_unproven` gate. No live transport or active
monetary permit exists. The prepared connector retains independent,
unconditional live and financial deny barriers. See the
[current checklist](../docs/planning/19-f3-03c-pre-live-readiness.md).

## Wire and continuation rules

Strict provider schemas are a projection of existing Pydantic schemas. Object
envelope, required properties, closed objects, enum discriminants and disjoint
unions are checked offline. Unsupported projection keywords/unions fail. Existing
parsers and independent domain validation remain authoritative; provider grammar
alone cannot establish feasibility, durations or authorization.

No dispatch occurs from token/argument deltas. The complete bounded terminal
response supplies authoritative calls and usage. Native IDs map to local IDs;
repeated native calls across attempts, duplicated calls within a response,
unmatched/repeated tool results and name mismatches reject before another HTTP
request or dispatch. Reasoning state is never interpreted, logged or stored in
PostgreSQL. Ordered native items exist only in a request session and are cleared
on every session exit. The runtime accepts no nonempty reasoning summaries.

Limits: 65,536-byte serialized request and cumulative raw provider stream;
16,384-byte normalized response/tool result; 4,096-byte tool arguments; at most
12 terminal output items and four tool calls. Strict UTF-8/framing, event order,
terminal status and numeric usage consistency are required. Extra/duplicate
terminal events and incomplete EOF fail, with conservative unknown accounting.
No raw provider stream reaches application SSE; existing terminal publication
and explicit approval boundaries are unchanged. Replay `Agent.generate()` returns
an unpublished result, as it did for fakes.

## Durable replay spending state

Migration `005_spending.sql` creates **empty** project/grant/session/attempt
tables. Projects have a database-enforced `mode='replay'`; this is not a live
permit table. Setup methods are trusted local test/experiment infrastructure,
not HTTP or model tools. They create no default project or dollar allowance.

Use exact fractional rates and upward-rounded integer microdollars. At the
reviewed Sol Standard rate card, reserve `2.5*input_bound + 10*output_cap`
microdollars. Settled ordinary/cached/30m-write/output rates are respectively
2/0.1/2.5/10 microdollars per token. Reasoning is part of output, never added twice.
Partition checks reject inconsistent counts. Prices are from the approved dated
plan, not a provider invoice or a live price lookup.

One project row lock precedes all reads/writes to its grants/sessions/attempts.
New reservations must fit project, UTC day, grant and session ceilings including
all open and unknown liabilities. Attempt ID binds immutable request allowances;
`(run_id, attempt_number)` is also unique. Same-ID retries recheck committed state
under the lock. Per-run attempt/token allowances cannot reset with a new key.

| State | Liability / permitted transition |
| --- | --- |
| `reserved` | Full reserved amount; durable before any send claim. May release to `not_sent` only because no send claim exists. |
| `sent` | One-shot claim committed **before** transport. Full liability remains until known settlement. A crash between claim/send is intentionally indistinguishable from a charged attempt. No automatic replay or release. |
| `settled` | Known typed usage and rate-compatible cost committed atomically with settlement hash. Identical settlement returns existing amount; changed usage/model/tier conflicts. |
| `not_sent` | Zero monetary liability; retained attempt identity prevents reuse. Conservative per-run attempt/token accounting is not reset. |

Cancellation drains the owned transaction, then propagates, even if COMMIT also
fails. SQL statement/lock limits and a five-second operation timeout bound
cooperative database work. Cleanup may finish after the generation deadline;
the deadline is rechecked before HTTP and no extra generation attempt is granted.

Any database error fences that ledger object's project until explicit
`reconcile(project)` acquires the authoritative project lock and reads state.
An in-flight transaction must resolve before that lock can be acquired. Another
repository/process still observes committed liabilities and one-shot claims;
an unsettled run cannot reserve its next attempt after restart. Reconciliation
does **not** release `sent` rows or prove no provider charge. Lost settlement
acknowledgements recover by committed settlement hash. Unapproved model/tier,
12-hour cache writes or reported allowance overrun freeze the project durably
and retain the unresolved reservation; they are not priced as ordinary tokens.

At midnight, send claim revalidates/rebases the reservation against the new UTC
day. Expired sessions/grants cannot claim or add work. New sessions/days do not
release previous project/grant liabilities. Shutdown persists `disabled` under
the same lock; pending reservations cannot become send claims afterward.

Database reconciliation is implemented/tested against actual PostgreSQL. Real
provider billing reconciliation is **unverified**: no live usage, invoice API,
receipt matching or proof of provider-enforced spend limits exists. Known trusted
synthetic usage may settle a replay row; absent authoritative future evidence,
leave a sent reservation charged at its maximum indefinitely. No timer/TTL,
dashboard silence, process restart or cancellation is a refund signal.

## Durable mixed operations — offline amendment C

Additive migration `006_counted_spending.sql` creates empty `spend_pairs` and
`spend_operations`; `007_counted_rate_version.sql` adds the fixed generation-rate
version. Migration 005 is unchanged. A pair binds project/grant/session,
run, ordinal, inference ceilings, generation rate and positive versioned
**synthetic** count quote.
Each pair has distinct count/generation identities; unique run/kind ordinals 1–3
and claimed combined ordinals 1–6 prevent identity reuse. A run cannot mix legacy
and counted protocols. Project-first locking orders both paths and includes
**both tables'** liabilities in project, UTC-day, grant and session ceilings.

Before counting, reserve both `C` and `2.5*remaining_input+10*output_cap`
microdollars atomically. Offline fixtures use invented `C=1000` microdollars,
version `synthetic-count-ceiling-v1`; no default or real tariff is inferred.
Count claim is a one-shot durable transition from `reserved` to `sent` before
transport. A valid acknowledged count changes it to `responded_held`: its full
`C` persists, while the paired generation hold shrinks to `2.5*N+10*output_cap`.
Generation additionally requires a fresh ephemeral ticket minted only after a
definitely acknowledged count transaction. Durable count state alone cannot
mint a ticket after restart, lost acknowledgement or cancellation.

Known generation usage settles exactly once by usage/model/tier fingerprint.
Only explicit trusted synthetic charge evidence can settle a held count cost;
the adapter never does this from a count number. Unknown/no-response counts stay
`sent`; successful counts with unknown billing stay `responded_held`. Both retain
their maximum indefinitely. No automated provider billing reconciliation exists.
Cleanup releases only still-`reserved` operations to `not_sent`, invalidates tickets
and never releases a sent/held operation. Uncertain claim means possible charge
even if HTTP was never reached. No background task or automatic replay follows.

The existing cancellation-safe bounded `_owned` transaction applies to every
mixed transition. Database errors fence the ledger object's project until
`reconcile_mixed(project)` waits on the authoritative project lock and reads state.
It neither refunds uncertainty nor reconstructs tickets. Lost settlement ACKs
resolve through the committed settlement hash. An unresolved generation or unknown
count blocks the next pair in that run. A known-count/held-cost pair permits its
own generation and subsequent pairs only within the remaining limits.

Both send claims recheck disabled/frozen state and grant/session expiry. Midnight
rebases only the newly claimed operation; already claimed count liability stays
on its original day. New days/sessions never erase project/grant costs. A failed
generation claim consumes its ticket; retry/reconciliation does not replay it.
Emergency shutdown is serialized at the claim boundary: it prevents later claims,
but cannot retract an already committed send claim or charge. No claim is made
about production billing, multiple application workers or power-loss durability.

## F3-03D hardening guarantees

Migration `008_spending_observations.sql` adds an empty metadata table, without
changing replay mode, existing migrations, rates or grant policy. Under the same
project-first guard, a validated pricing/usage mismatch atomically freezes the
project and stores its first bounded numerical observation and classified reason.
Both legacy and counted paths retain their original outstanding maximum.
Identical observations are idempotent; changed observations conflict without
overwriting the first. A later corrected report cannot silently settle an
operation with an outstanding discrepancy. Reconciliation does not clear the
freeze or invent a refund; failed accounting does not release financial holds.

Observed numbers are strict integers 0–1,000,000,000 in an allowlisted JSON object
<=1,024 bytes, enforced again by database constraints. Model and tier are stored
only as `expected|unexpected|missing`, never their untrusted strings. Missing,
invalid or unpriced cache usage salvages only individually validated numbers and
freezes conservatively. Nonzero writes without adequate TTL detail remain
unpriced; no missing value becomes zero. Observation fingerprints cover only
this bounded financial evidence, never prompt/native/body content. Ambiguous SQL
outcomes keep the existing project fence until an authoritative ordered read.

SSE requires one completed-item event for each terminal output item, with bounded
indices/IDs/types and exact event/terminal consistency. Optional added items must
match completed identities; partial encrypted state is never used for continuation.
Unknown/missing/duplicate/inconsistent items, late deltas, unsupported content and
oversized streams fail before tool dispatch. Completed native items, including
allowed assistant phase, remain request-local and are cleared on exit. Refusal,
incomplete behavior and independent validation remain unchanged. Historical
synthetic emitters now include completed-item events; frozen outcomes/provenance
are unchanged.

`OfflineHTTP` owns one async client per replay session, closed/awaited on every
exit. It accepts only exact HTTPX MockTransport or `LocalTLS`, a fixed-loopback
test connector. Logical destinations allow only POST to the two exact HTTPS
`api.openai.com` paths on port 443, with no userinfo/query/fragment/alternate path.
`LocalTLS` always rewrites the socket destination to literal `127.0.0.1` at an
explicit test port, requiring certificate/hostname verification. F3-03D added no
production connector; F3-04B's dormant connector below cannot activate. TLS is tested
against ephemeral synthetic local certificates, not the provider hostname.

Redirects, environment proxies/CA overrides and implicit retries are disabled.
Clients request identity encoding and reject **all compressed responses before
decoding**, preventing decompression expansion. Streamed and cached decoded
body bytes are bounded (count 1,024; generation 65,536); SSE framing stays inside
the original cumulative ceiling. A last synchronous stop/deadline check precedes
transport. There is no reconnection or automatic replay.

Replay emergency stop marks the supervisor stopped, commits disable under the
project guard, then cancels and awaits owned runs; SQL disable failure still
cancels local work and retains its uncertainty fence. Repeated stop/cancellation
drains cleanup and discards native tickets. A stop initiated by an owned task
cannot wait on itself. Already claimed work can still charge; cancellation is
not a refund or server-side cancellation proof. The unconditional live gate and
fake-only application settings are preserved.

Proposed arithmetic uses conservative generation maximum **80,002 microdollars**
($0.080002), including per-attempt upward rounding, plus `3*Cµ` for three counts.
`proposed_probe_micro(Cµ)` calculates numbers only; it verifies no tariff and
creates no grant/permit. Unknown `Cµ` is rejected. The synthetic count quote still
requires positivity; even verified zero billing needs separate reviewed live
compatibility work. Live spending and outbound request authorization remain zero.

## F3-04B prepared sender and final compatibility gate

`ClaimedHTTP` reuses the single owned bounded `OfflineHTTP` client. For each
count/generation it checks captured financial scope and the immutable full
generation/count projection, awaits the existing PostgreSQL claim transaction,
then rechecks stop/deadline immediately before transport. There is no separate
claim in the caller and no second retry owner. Uncertain, cancelled or denied
claims cannot reach HTTP; claimed liability survives an unsent socket. Attempt
counters stay conservative, while outgoing-byte counters advance only after
acknowledged claim. No opaque history or payload binding enters SQL or logs.

Full typed-Agent count→tool→recount→continuation and repair sequences now run
over real **loopback TLS** with native SQL, not only direct HTTP component tests.
The source remains `replay`. `OpenAIHTTPS` is rejected by `OfflineHTTP` and
`ResponsesReplay`; caller-supplied clients or subclasses cannot bypass this rule.

`OpenAIHTTPS` prepares the real fixed-destination request/HTTPX connector but
always calls the existing unconditional `LiveGate.check` and a second independent
`require_live_financial_authority` denial before credentials, pool, DNS or socket
use. Even making the first gate permissive in a unit fault cannot enable it.
There is no environment activation switch, live application HTTP route or CLI
sender. Original SQL still enforces replay mode and the synthetic count quote.
F3-04C's separate authority preparation and unpublished assembly below do not
activate this connector. Future activation requires separately reviewed source
release and owner authorization, not merely credentials or a flag.

The shared TLS transport factory uses verification, `trust_env=false` and zero
implicit retries. Pure request construction checks exact HTTPS/443 POST paths
before using an explicit bounded redacted credential; it discards incoming auth,
cookies, Host and private headers, rejects routing/SNI/trace extensions and sets
identity encoding and bounded timeouts. The local connector strips credentials
entirely and always rewrites the socket address to literal loopback. Actual
provider TLS/authentication is unverified; it is not exercised by these tests.

Existing response/frame/encoding bounds and owned cleanup remain authoritative.
No opaque native state, credential, arbitrary exception or payload hash is logged.
F3-04B changed no migration, rate, allowance or inference policy. Current additive
F3-04C preparation is specified below. Prior evidence and remaining requirements:
[F3-04B handoff](../docs/implementation/f3-04b-handoff.md),
[authorization checklist](../docs/planning/19-f3-03c-pre-live-readiness.md).

## F3-04C separate authority and single-request assembly

Migration `009_probe_authority.sql` adds **empty**, separately prefixed control
tables: `probe_authorities` and `probe_spend_{projects,grants,sessions,attempts,
pairs,operations,observations}`. Original replay rows, constraints and migrations
are unchanged. No replay row can fund this pathway. Prepared proposals create
only a zero-limit project and bounded authority metadata; they create no grant
or session. `simulation` rows are explicitly nonmonetary synthetic fixtures in
isolated test schemas. Positive live issuance is unreachable behind both hard
denials; no active row or monetary grant is created in this milestone.

`AuthoritySpec` binds one authority/account/project/grant/session/operator, exact
`gpt-6.1-sol`/`default`, both fixed POST endpoints, the dated rate card, frozen
prompt/tool/output/config/catalog/validator/input assets, explicit UTC window
greater than zero and <=2 hours, and four exact integer microdollar ceilings.
Live counting requires a positive explicit ceiling and `provider_reviewed`
evidence reference; missing/unknown pricing rejects before SQL or transport.
That label is a trusted operator attestation, **not automatic provider evidence
verification**. Obtaining and reviewing the actual tariff/maximum and retention
terms remains an external prerequisite. A test quote is not such evidence.

The fixed trusted SQL namespace adapter reuses the accepted counted transaction
algorithm. Issuance, reservation, claim, revocation and reconciliation acquire
the same project advisory guard **before** the project/authority row locks.
Strict metadata/fingerprint, actual four ceilings/mode/expiry and scope are
rechecked; the first reservation durably binds exactly one logical run. A fresh
repository or new run ID cannot reset it. Identical issuance is idempotent;
conflicting/revoked issuance fails. UTC day rollover never erases liabilities.
Uncertain SQL fences the repository; explicit ordered reads reconcile database
state, never billing, refunds or lost tickets. Recovery can load the original
private binding after asset drift; drift prevents new admission, not cleanup.

`ResponsesProbe` uses the same counted session, native parser, tools, Agent,
budgets, validator and bounded owned client. `SingleProbe` fixes the approved
synthetic revision-1 profile and empty text, admits one invocation and returns
only an **unpublished** result. Agent composition rejects a candidate store for
this provider. Local outcomes are labeled `authority_fixture`; a future released
network path would be labeled `live`, never replay. No application route,
evaluation sampler or business write is added.

After an acknowledged durable claim, request-local one-shot proof binds the
operation kind, endpoint and exact immutable body. The sender consumes that
proof once. Wrong body/endpoint, missing or reused proof, restart, expiry,
uncertain claim and revocation prevent sending; durable rows alone cannot mint
proof after restart. Real request construction additionally binds explicit
account/project headers; no inherited caller routing/auth headers are accepted.
The real connector checks the exact live gate and financial denial independently
before consuming proof, using credentials, creating a pool or opening a socket.
Neither credentials, flags nor prepared/simulation rows can release those checks.

Emergency stop revokes/disables under the same ordered SQL guard, then cancels
and awaits owned work through the existing supervisor. Proofs/tickets/native
state clear even when revocation acknowledgment is uncertain. Sent and successful
but unpriced counting operations retain their entire maximum; this authority
repository deliberately provides no count-settlement shortcut. Socket cancellation
does not establish provider cancellation or a refund. Generation discrepancies
reuse durable freeze/numerical observation semantics in the separate tables.

Only the future **active** issuance/send branch remains deliberately unexecuted;
native SQL tests establish prepared/simulation behavior, not live monetary
correctness or provider compatibility. Both hard-denial release and any execution
require separately authorized source/financial/privacy review. Current allowances
and authorized provider requests remain **zero**. Numerical proposals still use
`80002 + 3*Cµ`; no tariff, rate or approved spending policy is changed.

Evidence: [F3-04C handoff](../docs/implementation/f3-04c-handoff.md) and the
[current authorization procedure](../docs/planning/19-f3-03c-pre-live-readiness.md).

## Privacy and retention

Ledger fields are bounded opaque local IDs, times, integer bounds/amounts,
version/hash, state and typed numeric usage. They contain no profiles, prompts,
plans, native state, provider receipt IDs, credentials or exception strings.
The separate authority metadata additionally contains private account/project/
operator bindings and reviewed configuration digests, with no payload hash or
native content. These fields are control-plane records, never ordinary logging,
tracing or exported evidence. Metadata readback is a private repository API,
not an HTTP/model tool. Local trace labels distinguish fake, replay and
authority fixtures (future live explicitly labeled); usage counters
are allowlisted. Existing safe console formatting remains mandatory. No hosted
sink, auto-instrumentation, content callback or telemetry destination is enabled.

Fixtures contain authored synthetic placeholder ciphertext and invented usage,
not real reasoning captures. No content-bearing checkpoint/durable conversation
is introduced. Accepted business snapshots remain in their existing tables.
Retention proposal: resolved billing metadata 90 days, unresolved rows retained;
cleanup is manual/reviewed, with no automatic purge or new background worker.
This milestone's development control tables remain empty; isolated test schemas
are dropped. No real-user retention or deletion guarantee is implied.
