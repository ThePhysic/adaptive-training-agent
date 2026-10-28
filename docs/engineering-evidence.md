# Engineering claim-to-evidence map

Evidence types: **A** = actual local application demonstration; **B** = automated
regression; **C** = synthetic provider/dummy experiment; **D** = planned/unexecuted.
F5-D1 results are accepted historical evidence, not tests rerun for F5-D2. Fresh
F5-D2 commands/results are recorded in its [handoff](implementation/f5-d2-handoff.md).

| Claim and practical limit | Type | Specific evidence |
| --- | --- | --- |
| Actual UI/API/SQL integration, not only isolated components | A | [Browser projection](implementation/evidence/f5-d1-application.json); [desktop](implementation/evidence/f5-d1-desktop.png); `tests/test_browser_ui.py::test_real_browser_local_save_stream_review_revision_and_owner_switch` |
| Only terminal complete output is approvable; disconnect cannot silently publish | B | `tests/test_streaming.py::test_disconnect_before_terminalization_never_publishes`; `tests/test_stream_publication.py::test_publication_fault_after_draft_is_error_then_done_and_no_candidate`; browser revision/review assertions |
| Approval loss recovers the same transaction, without duplicate plan | A/B | Browser same-key interception; `tests/test_approvals_postgres.py::test_real_atomic_snapshot_retries_fingerprints_and_owner_isolation`; `test_true_process_restart_recovers_key_without_any_candidate` in the same file |
| Native concurrency and unknown-commit reconciliation, not exactly-once network delivery | B | `tests/test_approvals_postgres.py::test_real_commit_faults_reconcile_or_rollback_without_partial_rows`; `test_inflight_uncertainty_is_quarantined_until_authoritative_outcome` |
| Owner-scoped immutable state and explicit session feedback | A/B | Browser SQL counts and refresh; `tests/test_approvals_postgres.py::test_approved_state_is_immutable_in_postgres`; `tests/test_completions_postgres.py` |
| Real local dependency interruption/recovery and restart readback | A/B | [Release evidence](implementation/evidence/f5-d1-local-release.json); `tests/test_operations_postgres.py::test_actual_database_connection_interruption_recovers_without_state_loss`; readiness fault matrix in the same file |
| Recoverable database boundary and compatible image switch; not automatic schema downgrade | A | F5-D1 quiesced dump/restore and checksum-mismatch rejection; [release runbook](local-release.md) |
| Trace-driven diagnosis without prompt/plan capture | B/C | [12-span failure trace](implementation/evidence/f5-d1-failure-trace.json); `tests/test_observability.py::test_induced_failure_is_correlated_without_content`; local fake tool + invalid proposal + exhausted repair |
| Privacy and exporter failure do not grant authority or interrupt approval | B | `tests/test_observability.py::test_canaries_never_reach_configured_sinks`; `tests/test_langfuse_postgres.py::test_unavailable_telemetry_cannot_interrupt_real_approval` |
| Current-source local fake performance, not LLM latency or capacity guarantee | A | [F5-D1 measurements](implementation/f5-d1-report.md#recovery-and-measured-local-operation): four warm-ups, 120 requests, concurrency 1/2, zero errors, host contention disclosed |
| 3-count /3-generation /6-combined protocol and retained synthetic liabilities | B/C | `tests/test_counted_probe_evidence.py::test_real_counted_probe_common_score_and_read_only_liabilities`; `tests/test_synthetic_collection.py::test_cancellation_retains_count_hold_and_interrupted_result`; [fresh D1 projection](implementation/evidence/f5-d1-evaluation-walkthrough.json) |
| Intermediate rejection cannot be hidden by a valid repaired final plan | B/C | `tests/test_counted_probe_evidence.py::test_repaired_final_never_erases_malformed_intermediate`; E9 ten-case test retains one hard failure in its 3/3/6 sequence |
| Durable first result and immutable dummy review, not genuine identity/authorship proof | B/C | `tests/test_synthetic_collection.py::test_ambiguous_commits_retain_slot_and_never_replay`; `tests/test_blinded_review.py::test_full_synthetic_packet_import_report_demo`; E9/E10 fault suites |
| Fixed reproducible software baseline; no genuinely unseen model evidence | B/C | [40-case baseline](../data/evaluation/README.md); [evaluation protocol](planning/20-f3-model-evaluation-protocol.md); `scripts/evaluate_baseline.py --check` and `scripts/evaluate_models.py --check` |
| Archive bytes and code/configuration commitments can be checked | B | `scripts/review_source.py`, [F5-D2 scope/manifest assessment](implementation/f5-d2-publication-safety.md); commitments prove integrity, not human independence or publication consent |
| Real provider behavior, billing/retention, independent human quality | D | [Pre-live checklist](planning/19-f3-03c-pre-live-readiness.md), [E7 readiness](implementation/f3-e7-handoff.md); absent/NO-GO, not inferred from synthetic success |
| AWS operation, production auth/availability and external users | D | [Phase acceptance boundaries](planning/02-phases-and-acceptance.md); optional deployment design is not deployed infrastructure |

## How to read the numbers

The 40-case corpus is a frozen software baseline (24 development/16 historically
held-out). The newer 50 authored cases include 40 development and 10 exposed
comparison cases; they are not unseen. The 150 template/fake/replay dispositions
are 50 per source, with intentionally injected failures, not 150 quality successes.
Hard passes were 50/44/44 while expected handling was 50/50/50.

E9 executes ten public profiles with actual local replay and native SQL; E10 adds
template counterparts and dummy review. Neither supplies the ten future independent
cases. Genuine-human judgments remain zero and quality remains null. A high test
count does not prove usefulness, safe exercise suitability, user retention or
model reasoning quality. The original hard-rule implementation is unchanged.
