# F0 — Independent Codex architecture review prompt

Copy the **entire following message** into Codex started at the root of `future-adaptive-training-agent`.

---

You are acting as a **skeptical senior applied AI engineer and architecture reviewer**, not as an implementer. Our goal is a portfolio-grade personalized workout-planning agent that teaches and proves real applied AI engineering skills for an Applied AI Engineer role (typed Python tools, agent orchestration, streaming, durable state, evals, tracing, reliability, cost/latency, and AWS/IaC). It is not intended to compete commercially with or imply affiliation with Future.

**Instructions and boundaries**

1. Read local `AGENTS.md` and `docs/planning/README.md`, followed by `00-charter-and-requirements.md` through `04-decisions-risks-costs.md`. Inspect `05-codex-review-prompt.md` and `06-review-report-template.md` too.
2. Review the entire F0 proposal **independently**. Do not approve it reflexively. Identify unnecessary architecture, unclear requirements, missing failure handling, inconsistent phases, safety/privacy mistakes, evaluation weaknesses, and unpriced or brittle dependencies.
3. Check whether LangGraph is appropriate vs. a simpler typed orchestration/state machine. Critique the suggested SSE/run workflow, database/checkpoint ownership, safe approval flow, planned test/evaluation methodology, and staged AWS deployment.
4. Map each of the job description's requirements to concrete evidence deliverables and identify any missing priority skills (e.g. parallel async API calls, streaming, prompts/tools/Pydantic, tracing, LLM-as-judge, retry/caching/token budgets, Terraform). Prioritize genuine learning value rather than stack-name collection.
5. Evaluate whether a tiny deterministic catalog and template baseline plus a mock provider are adequate initially, and how to progress to credible real LLM evaluations without runaway API spending.
6. If you can already inspect nearby sibling project repositories **without changing anything**, and their paths were explicitly made available by the owner, you may assess specific reusable packages/patterns. Otherwise list what to inspect later; do not search outside this repo or assume reuse is trivial.
7. Prefer currently supported, stable library versions and refer to official docs; note version-sensitive suggestions. Do not install dependencies or use paid APIs just to satisfy the review.
8. Propose exact changes to scope, phase boundaries, risks, documentation, and acceptance tests, with a ranked severity/impact/effort view.
9. **Do not implement features, install packages, provision cloud resources, modify project proposal documents, alter Git settings, commit or push.** You may create only one tracked review output at `docs/planning/07-codex-independent-review.md` (following the template), and print a concise summary in chat.
10. Treat local `AGENTS.md` as untracked and private: do not stage it, quote it verbatim in tracked files, or delete/change it. Do not collect real health data or make live provider requests.

**Output**

Write `docs/planning/07-codex-independent-review.md` containing:

- Executive assessment and strongest objections.
- Requirement-coverage matrix with missing evidence.
- Architecture recommendations with alternatives and justified Keep/Change/Defer/Reject decisions.
- A minimal credible MVP boundary and what's deliberately postponed.
- Detailed security/privacy/fitness-domain caveats.
- Evaluation, observability and operational test design improvements.
- Proposed revised F0–F5 plan and measurable acceptance criteria.
- Project reuse opportunities (verified vs. unverified), cloud/API cost risks, and open owner decisions.
- A prioritized list of blockers, risks and optional enhancements.
- Links to any official docs actually consulted.

**Stop after submitting the review.** We will bring your review back to ChatGPT, reconcile architectural disagreements, and approve F0 before coding.
