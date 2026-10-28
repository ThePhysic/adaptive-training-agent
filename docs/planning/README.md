# Future Adaptive Training Agent — reconciled F0 planning package

**Status:** RECONCILED PROPOSAL — owner approval required before F1 implementation.  
**Date:** 2026-10-23  
**Project:** `future-adaptive-training-agent`  
**Scope:** educational applied-AI engineering portfolio project, not affiliated with Future.

## Decision and review trail

- `00-charter-and-requirements.md` — revised goals, scope and honest evidence targets.
- `01-architecture-proposal.md` — revised request-scoped design, data ownership, approval transaction and streaming contract.
- `02-phases-and-acceptance.md` — revised F0–F5 milestones and testable gates.
- `03-evaluation-safety-privacy.md` — offline baseline, synthetic fixtures, approved live evidence and privacy rules.
- `04-decisions-risks-costs.md` — D01–D12 decisions and separately gated spending.
- `05-codex-review-prompt.md` — **historical**, initial independent-review request; not the next prompt.
- `06-review-report-template.md` — **historical** template.
- `07-codex-independent-review.md` — independent F0 report, retained unchanged in the user's repository.
- `08-reconciled-decisions.md` — changes accepted, adjusted and deferred; pending owner sign-off.
- `09-f1-work-package.md` — implementation-ready scope and acceptance contract, **not authorization**.
- `10-final-consistency-review-prompt.md` — instructions for a short final Codex consistency check.

Keep `AGENTS.md` local only; the root `.gitignore` excludes it. The reconciliation archive includes a proposed local revision to that file but must **not** add it to Git. Root README and `.gitignore` are intentionally absent from this patch so existing files remain intact.

## Project philosophy

Use established frameworks and reusable methods where they solve actual problems. Learn and demonstrate typed tool calls, async APIs, evaluation, operational reliability, and evidence-based decisions. Never claim fake tests establish real LLM behavior, or local deployment establishes operated AWS experience.

### Authorization boundary

**Nothing in this archive authorizes application implementation, dependency installation, external network/provider usage, cloud provisioning, commits or pushes.** First reconcile F0, run the final consistency check, and obtain explicit owner approval. Then update local `AGENTS.md` for the approved F1 work only.

## Final F0 amendment following review 11

- `11-final-consistency-review.md` — historical independent second review; preserve unchanged.
- `12-f0-domain-contract.md` — **proposed owner-ratified** supported matrix, exercise prescription bounds, exact duration arithmetic and examples (C1).
- `13-f0-candidate-approval-contract.md` — **proposed owner-ratified** transient candidate lifecycle, concurrent revision/approval/expiry, DB version checks and committed-key-first idempotency (C2/C5).
- `14-f0-remaining-contract-clarifications.md` — four terminal SSE outcomes, incomplete EOF and whole-request attempt/budget definitions (C3/C4).
- `15-f0-closure-and-review-instructions.md` — blocker resolution index, owner sign-offs and **read-only** targeted verifier.

**Authorization:** This amendment is not F1 approval. The repo owner must ratify contracts and explicitly authorize the chosen next work unit. Keep `AGENTS.md` ignored and local; update it only after approval.
