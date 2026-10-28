# F3-05A — offline Langfuse integration and future activation specification

Date: **2026-10-25**. F3-04C accepted for offline scope. F3-05A is prepared for
review, not hosted activation. Provider requests, provider spending and hosted
telemetry remain **zero-authorized**. No self-hosted service is introduced.
The owner-reported count18 and support escalation establish neither counting
tariff/retention nor authorization. [Checklist19](19-f3-03c-pre-live-readiness.md)
and [evaluation protocol20](20-f3-model-evaluation-protocol.md) remain authoritative.

## Reuse and boundary

Existing `LocalTracer`, safe console, ContextVar correlation, stage allowlists,
usage counters, native SQL boundaries and shared hard scorer are retained.
The locked application has no OTel SDK/exporter or Langfuse dependency. This local
environment already has the locked transitive OTel API1.45.1 distribution; its provider is
the inert `ProxyTracerProvider`, with no OTel SDK/exporter installed. The adapter
does not import it, replace it or register a global provider.
`LangfuseTracer` is an explicitly injected **local** tracer that reuses the same
sanitizer and copies completed records into bounded memory. It never invokes SDK
code, HTTP, callbacks, flushes or export retries inside application work.

The optional SDK lives in separately locked `experiments/langfuse`, not production
dependencies. Its disposable process permanently denies sockets/DNS, clears
provider/Langfuse/OTel/proxy environment configuration, uses only synthetic keys,
and substitutes a fixed in-process score API mock and in-memory span exporter.
An SDK HTTP URL cannot be selected by a flag, credential or environment variable.
The fixed `.invalid` mock host is never resolved. No cloud or local server runs.

This separation allows real SDK wrapper/OTel/score serialization experience while
making outage, cancellation and SDK lifecycle behavior irrelevant to approvals.
Native PostgreSQL tests separately prove failing/closed/full projection buffers
cannot interrupt a committed approval or its same-key recovery.

## Version and compatibility decision

Use **Langfuse5.0.4** with separately locked **OpenTelemetry1.45.1**, HTTPX0.28.1
and the application's Pydantic2.14.1 on Python3.14.9. PyPI metadata permits
Python>=3.11,<4 and includes3.14. Installation and tests, not metadata alone,
establish compatibility on this host. Main and graph locks remain unchanged.
OTel exporter dependencies include related `0.66b1` transport/semantic packages
selected by upstream constraints; these do not make the stable SDK a prerelease.
[Release metadata](https://pypi.org/pypi/langfuse/5.0.4/json),
[official compatibility](https://langfuse.com/docs/compatibility).

SDKv5 targets Langfusev4; legacy v2 `trace()/span()/generation()` APIs and older
dataset-run assumptions are unsuitable for new integration. We use public typed
span/generation/agent/tool wrappers, OTel experiment attributes and SDK `Evaluation`
with BOOLEAN scores. No previous SDK instrumentation requires migration.
Docs and package description can lag releases: the installed v5 generated score
client actually posts to `/api/public/scores`; a version-matrix label mentioning
Scores APIv3 is not proof of another wire path. Test the pinned route locally;
future hosted compatibility requires a separate approved check.
[Migration guide](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5),
[Python reference](https://python.reference.langfuse.com/langfuse).

Two pinned-SDK implementation details require containment: constructor creation
of a secondary async API client without a public custom-async-client option, and
a prompt-cache refresh consumer left alive by ordinary `client.shutdown()`.
The isolated harness seals the async factory with MockTransport, closes those
unused clients, and explicitly shuts down that pinned private prompt-cache task
manager. Tests assert no newly owned thread remains. This private lifecycle hook
is an upgrade-review obligation, not a production SDK abstraction. Backoff2.2.1
emits a Python3.14 deprecation warning for `asyncio.iscoroutinefunction`; no
runtime failure observed, Python3.16 compatibility is unverified.

## Observation mapping

| Existing stage | SDK representation / meaning |
| --- | --- |
| HTTP, profile reads/Save, publication, terminalization, approval/transaction/reconciliation/readback, completion | Named generic observations with original hierarchy/status/duration |
| Agent session/execute/repair | Agent observations; repair spans record attempted repair-stage entries, including rejection when its one allowed repair is exhausted |
| Provider generation | Generation observation; no input/output content, exception event or inferred usage/cost |
| Provider count | Named span; counting is not inference usage and no free charge is inferred |
| Read tool | Tool observation with allowlisted name, bounded counts and classified result |
| Independent validation | Named span with allowlisted invalid-plan classification |
| Evaluation case | Root observation with native experiment/item attributes, source/split/exposure and existing hard-score links |

Trace IDs remain128-bit. Source span IDs are128-bit, whereas OTel IDs are64-bit:
map their low64 bits and retain full opaque source/parent IDs in metadata.
Zero/colliding mappings reject; never fabricate a parent. Root remains root.
Completion order is retained, so children may arrive before parents. Missing
parents after bounded eviction mean a partial trace, not a complete reconstruction.

Original measured duration is preserved exactly to its existing millisecond
precision. UTC end is anchored at local projection append; SDK start is end minus
that duration. It is not a provider timestamp or precision latency measurement.
Error/cancellation levels and allowlisted reasons survive; no raw exception text.
Provider-attempt counts and final request aggregates remain distinct. Current
per-attempt spans lack validated per-attempt token breakdowns: retain request
usage/cache/write/reasoning totals on agent execution as **request aggregates**,
never copy them to every generation or infer unknown values as zero. SDK cost
details stay absent; the financial ledger remains sole spending authority.

Only original bounded enum/integer/boolean metadata and opaque correlation IDs
cross the boundary. No prompts, profiles, plans, preferences, arguments/results,
credentials, billing identities, native reasoning, response bodies, exception
strings, user IDs, content/payload hashes, events, baggage or resource detectors.
Empty explicit OTel contexts and a private provider prevent global/secondary
exporters and instrumentation from receiving these spans. No OpenAI/LangChain
automatic instrumentation is imported.

The main buffer has<=2,048 entries and<=4MiB encoded record bytes, oldest-first
eviction and counters. Its duplicate identity strings and Python objects add
bounded overhead beyond that encoded-byte limit. Deduplication/conflict detection
lasts for retained entries, not forever after eviction. SDK capture admits<=2,048
distinct identities, a512-span batch queue and2,048 captured spans. Scores are
limited to150 unique case/source pairs ×2, with duplicate no-op/conflict rejection.
SDK default100,000-item score/media queues are not exposed: media is disabled and
at most300 score items can enter through this harness. Failed span export drops
diagnostics, without automatic replay. Close is idempotent and drains owned work.

## Evaluation linkage, interpretation and artifacts

`evaluate(tracer=...)` retains the one shared case runner/scorer; optional case
roots and a separate trace-link map add correlation. No other scoring algorithm
or task executor is introduced. SDK native `langfuse.experiment.*` attributes
represent three offline experiments and150 items, using scenario IDs plus existing
split/exposure labels. Input/expected-output attributes are omitted. SDK BOOLEAN
`hard_passed` and `handling_passed` scores reuse existing verdicts. Consistency
guards reject fabricated quality ratings or a hard pass hiding failed checks.
SDK `run_experiment` is deliberately not used: its default concurrency, task
execution, content capture and remote behavior would duplicate the accepted runner.
[OTel experiment integration](https://langfuse.com/docs/evaluation/experiments/experiments-via-opentelemetry).

Frozen40 remains24 development/16 legacy held-out. Current50 remains40 development/
10 developer-exposed comparison candidates, zero genuinely unseen holdout. All
150 template/fake/replay dispositions,12 deliberate hard failures and manifest
source fingerprints are preserved in historical snapshots. An additive F3-05A
snapshot records current changed source while requiring identical case outcomes.
No human/judge/quality scores exist; clarity remains N/A. A high software handling
score is neither real-model behavior nor fitness effectiveness.

`scripts/prepare_langfuse.py` writes sanitized observations, experiment mapping,
the original reproducibility manifest and summary to ignored `.cache/f3-05a/`.
The isolated `run.py` writes SDK-shaped capture evidence there. These are local
mock artifacts, not hosted ingestion/UI proof. Preserve code/SDK-lock hashes and
evidence types. Keep local detailed artifacts14 days, then explicitly review/remove
the exact directory; no cleanup daemon. Tracked historical evidence remains.
Reproduction, fault evidence and exact results: [handoff](../implementation/f3-05a-handoff.md).

## Future hosted activation — separately authorized work only

All current hosted endpoints/credentials/budgets are inactive. This harness is
permanently offline; do not relax its socket seal or turn `.invalid` into a real
host. A separately reviewed hosted boundary must satisfy **all** of:

- Explicit owner scope, named project/operator/window and independent outbound
  permission, even for a free tier. No credential/environment-only opt-in.
- Approve the US tenant, proposed `https://us.cloud.langfuse.com:443`, after
  account/region review. Official documentation identifies this as Oregon;
  EU `cloud.langfuse.com` is a different tenant and must not be a fallback.
  [Regions](https://langfuse.com/security/data-regions).
- Approve exact paths/methods: candidate OTLP POST
  `/api/public/otel/v1/traces` with the reviewed v4 ingestion header; separately
  approve score/experiment APIs only if required and compatibility verified.
  No auth-check, model-list, prompt management, media upload or arbitrary SDK APIs.
- Review authentication/key storage, account membership, TLS/hostname, redirects,
  proxy inheritance, compression/body limits, retry ownership, bounded buffers,
  emergency disable and no-impact delivery outages. No keys in reports/sinks.
- Approve exact allowed metadata/masking, all sinks and secondary exporters,
  access/deletion/backup/support/subprocessor terms and data processing region.
- Verify a real **deletion** policy and dataset/audit exceptions; a plan's access
  window only limits visibility. Current docs distinguish default retention from
  deletion and make configurable retention plan-dependent. Do not assume a free
  tier deletes data after30 days. [Retention](https://langfuse.com/docs/administration/data-retention).
- Approve a numerical hosted budget, volume/event ceiling and account controls,
  including subscription/overage risk. Current hosted allowance is **USD0**;
  no tariff or spending authority is established here.
- Re-run canaries, failure/duplicate/cancellation/shutdown/correlation tests and
  independently inspect final redacted envelopes before any export. Verify
  ingestion/query/UI behavior and deletion in a separately approved experiment.
- Provider requests remain separately blocked by counting billing/retention,
  numerical financial authority and both source barriers. Hosted permission does
  not imply OpenAI permission, and vice versa. No real-user release or F3 closure.

No hosted experiment, provider request or subsequent milestone is authorized by
this specification. Stop after offline F3-05A for review.
