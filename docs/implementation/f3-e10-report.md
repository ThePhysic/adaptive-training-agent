# F3-E10 — Synthetic blinded review integration report

2026-10-27. Offline implementation ready for independent review. No human
participants/judgments, curator activity, genuine case/key/custody, account request,
provider call, money, AWS operation or final freeze approval occurred.

## Implemented path and reuse

[blinded_review.py](../../experiments/blinded_review.py) connects the exact E9
public replay Collection to a deterministic packet, strict dummy import and
consolidated report. It reuses the current study/canonical/source bindings,
actual deterministic `run_case(template)`, existing hard scorer and
`model_review.validate_ratings`/rubric. No old scorer, packet helper, E9 table,
execution authority, production source or dependency changed.

The experiment uses the existing local PostgreSQL connection and disposable test
schemas. Three new experimental tables hold one packet,40 fixed dummy judgment
slots and bounded classified events. There is no production migration, service,
general evaluation CLI, real reviewer authentication or genuine importer.

## Blinding and first-result handling

The operator bundle pins exact source/review/execution configuration, selection,
E9 first-evidence snapshot, case/variant mapping, outputs and rubric. Reviewer
content contains opaque pair IDs, supported preferences and uniform A/B plan views
with exercise titles. It excludes actual case IDs, source/model labels, automated
scores/verdicts, eligibility flags, expected judgments, native reasoning and billing.
Practice/schema notices remain outside that content. The public seed/source can
permit reidentification; this is metadata-blinding practice, not genuine blindness.

Only pairs with two complete, hard-passing quality-eligible plans are issued. A
failed/missing counterpart is not shown as a biased A/B placeholder; all planned
slots remain in operator denominators. Template latency is excluded from packet
identity, making reproduction deterministic. Old exposed cases are never unseen.

Dummy forms bind through packet ID and private A/B mapping to exact configuration,
selection, case, variant and rubric. Ratings reuse the existing three integer1–5
dimensions; explanation clarity is null. Abstentions require a categorical reason
and null ratings. Pending/invalid forms do not become judgments. Genuine labels,
unsupported fields, wrong bindings and unknown pairs reject.

Each first valid import creates an exclusive file fence, acknowledged SQL claim
and owned update-once result. Natural slot keys exclude request/packet/path IDs
as replacement identities. Invalid attempts only append classified events; they
cannot replace an accepted record. Exact accepted duplicates read without counting
twice; conflicts, partial files, pending commits and corrupt records stop or remain
indeterminate. No reset/recovery writer completes an interrupted import.

## Reproducible actual synthetic demonstration

The native fixture `test_full_synthetic_packet_import_report_demo` executes all
ten E9 public profiles and actual templates. Replay uses synthetic protocol
responses; the intentional third-case repair remains a hard failure.

| Observed demonstration result | Value |
| --- | --- |
| Actual public automated outputs |20:10 deterministic template +10 counted replay |
| Common hard results |19 pass /1 intentional retained repair failure |
| Reviewer packet |One deterministic packet containing9 eligible A/B pairs |
| Practice schedule |40 dummy-review slots /120 dimension slots; not a genuine allocation |
| Issued / ineligible pair slots |36 /4 |
| Accepted dummy submissions |2 rated +1 abstention |
| Remaining records |33 missing;0 indeterminate in the successful demonstration |
| Persisted events |1 duplicate,1 conflict,2 invalid attempts |
| Dummy-only arithmetic |2 ratings per dimension; mean4 from scripted3/5 values |
| Genuine-human evidence |0 judgments; reviewer allocation unknown; quality null |
| Native provider operations |42 logical mocked operations, unchanged by packet/import/report |

The [numerical dummy report](evidence/f3-e10-dummy-report.json) is a projection
from that passing native test, not invented human observations. The dummy means
demonstrate import arithmetic only, not model quality, agreement or fitness
effectiveness. Ten future independent cases are absent/unopened;20-pair primary
study execution and broader protocol acceptance are not claimed.

## Validation and boundaries

Final selected checks passed **787 distinct tests /809 executions**, including
247 tests in native PostgreSQL suites. Frozen baseline40/40,150 comparison
dispositions, old hard rules and all live/financial/genuine denials remain intact.
The [handoff](f3-e10-handoff.md) records exact commands, faults, failed development
run and remaining limits. No frontend/browser or hosted CI run is claimed.

The additive121-input [freezev5 candidate](evidence/f3-e10-freeze-candidate.json)
reproduces and binds the demonstration; it remains unapproved. All566 task-entry
public files and historical candidates/claims are byte-identical. Runtime packets,
blinding maps and submissions stay in disposable SQL/ignored storage, not the
public review archive. This establishes local synthetic engineering behavior,
not independent custody, genuine judgments, production identity or provider terms.

## Smallest remaining work

| Goal | Required next work / boundary |
| --- | --- |
| A — offline engineering completion | The public synthetic execution→review→report slice is now implemented. Before calling the genuine-study source complete, settle and review the dormant novel-case authoring/commitment/opening/authenticated receipt and genuine review-provenance boundaries; do not convert dummy labels into real identity |
| B — local demonstration | Separately authorize one bounded local release/application journey plus this test demonstration, with a failure/recovery and metadata-only trace. Existing UI/runbook suffice; no new platform is needed |
| C — portfolio release | A concise reproducible evidence map, architecture diagram, short demonstration and limitations; verify existing CI/release artifacts for the selected source. Distinguish software/replay evidence from real-model, human, cloud and production claims |
| D — genuine independent evaluation | Stable reviewed study/model/configuration and final freeze, then separately appointed family curator/conflict/custody/exposure review and human-only ten-case creation; genuine commitment/registration/opening and actual reviewer allocation/collection approvals |
| E — real-model evaluation | Provider/account/model/settings/count tariff and maximum/retention/privacy evidence, exact source release, numerical limits, then separately authorized one compatibility logical request before any study tranche |

Provider support remains unresolved; no account inspection was performed. AWS,
hosted telemetry, judge calls, new orchestration/services and extra infrastructure
remain optional. No planning-only successor is needed for the public slice: the
next useful authorized increment can be a local demonstration/release polish.
Any genuine trust/source decision above is a concrete separate review boundary,
not an automatic follow-up or permission to enroll people now.
