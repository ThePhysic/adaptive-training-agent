# Codex independent review — report template

Create `07-codex-independent-review.md` rather than modifying this template.

1. **Executive judgment:** top three strengths and top three concerns.
2. **Requirement mapping:** requirement → evidence → missing item → recommendation.
3. **Decisions:** D01–D12 with Keep / Change / Defer / Reject, rationale and minimal alternative.
4. **Architecture analysis:** data ownership, sync/async, SSE contracts, LangGraph usage, concurrency, auth, idempotency, durable state.
5. **Safety/privacy:** boundaries, leakage risks, injection and write safety, external user requirements.
6. **Evaluation and quality:** dataset, rubrics, deterministic tests, human/judge calibration and gates.
7. **Cost and operations:** mock tests, real provider opt-in, tracing costs, minimal AWS option, teardown, risk ranking.
8. **Revised phase plan:** F0–F5 outcome, non-goals, proof required at each gate.
9. **Reuse:** verified reuse opportunities and paths; unverified conjectures labeled separately.
10. **Actionable changes and owner decisions:** blockers first, then optional enhancements; cite actual documents or official references.
