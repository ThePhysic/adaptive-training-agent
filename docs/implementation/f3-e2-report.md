# F3-E2 — Independent sealed evaluation preparation

2026-10-27. Owner-authorized offline implementation only. Submit for independent
review. No final sealed case, curator attestation, owner freeze approval, human
judgment, real model result or genuine population registration has been created.

The additive [metadata module](../../experiments/sealed_evaluation.py) freezes
relevant working-tree bytes and evaluation rules, validates an opaque versioned
population envelope, checks declared exposure overlap and independently supplied
pins, and exclusively registers unopened metadata. It has no case loader, provider
entrypoint or quality scorer. Its opening function always denies.

The original v1 Case schema explicitly means developer-authored/exposed. It must
not be reused to mislabel unseen cases. All original IDs, 24/16 and 40/10 splits,
50 authored cases, source fingerprints, frozen snapshots and common scorer remain
unchanged. A later authorized opening needs a truthful independent-case envelope
over that same scorer, with F3-E1's intermediate-failure and missing-evidence gates.

Prepared materials:

- [Freeze and sealed v2 specification](f3-e2-sealed-evaluation-specification.md).
- [Independent curator procedure](f3-e2-curator-procedure.md), with a blank checklist.
- [Human-review procedure](f3-e2-human-review-materials.md), blank versioned form,
  full declared denominators and no invented judgments.
- [Candidate public freeze](evidence/f3-e2-freeze-candidate.json); reproducible, **not ratified**.
- Synthetic adversarial tests and archive path exclusions before content reads.

Independent custody, secret commitments and separately retained owner pins are
necessary. Metadata alone cannot verify a person's independence, hidden coverage,
semantic novelty or token-to-content correspondence. Windows access enforcement
has not been established. Future content stays outside developer/Codex/Git storage;
the reserved archive-path exclusions are defense in depth, not an OS sandbox.

No accepted source gate, spending authority, infrastructure, application behavior,
historical claim or AGENTS.md was changed. See the [handoff](f3-e2-handoff.md) for
exact observed validation, source preservation and package details. Completion
prepares independent action; it does not authorize curation by Codex, opening,
live execution, human collection or the next milestone.

Fresh selected checks: **566 Python tests passed**, including54 new metadata tests
and153 native SQL/loopback TLS/accounting tests. Frozen40/40 and150/150 expected
comparison dispositions match; contract, grammar, lint and formatting checks pass.
The freeze binds99 public files;519 public source members are packaged with a
byte-verified SHA-256 manifest. These are synthetic/software results, with zero
genuine sealed cases, human judgments or model-quality measurements.
