# F3-E2 — Configuration freeze and sealed metadata v2

2026-10-27. Offline infrastructure only. **No genuine sealed population, curator
attestation, owner freeze approval or final case commitment is created here.**
Tests use synthetic non-case sentinel bytes/keys, not future workout cases.

## Compatibility and freeze

`experiments/sealed_evaluation.py` is additive, outside src. Existing Case's
developer-authored/exposed literals, v1 manifests, 40-case baseline, 150-case
comparison, F3-E1 and scorer are unchanged. `sealed-evaluation-v2` is a separate
population envelope. It never relabels old held-out/comparison inputs as unseen.

`freeze()` produces `evaluation-configuration-freeze-v1`, with status
`candidate_not_owner_approved`. A sorted public file SHA-256 map plus selection,
scorer/rubric and public exposure-index bindings is canonically hashed to its
fingerprint. It includes accepted dirty working-tree bytes, not only HEAD. No
timestamp or self-reference; identical sources yield identical bytes. `check_freeze`
requires exact current inventory/content/policy equality, including new source files.

Frozen inputs:

- All application Python: schema/domain/duration/validator, template, tools and
  authorization, prompt assembly, budget/protocol/native parser, scorer and rubric.
- Catalog, root Python lock/config/runtime and frontend dependency lock; reviewed
  F3-02 prompt/tool/output/model configuration and native fixtures. Rates/config
  remain assumptions, never live authority; current hard denials are captured.
- Original40 and exposed50 inputs/manifests (and model outputs); no regeneration
  of historic score artifacts. Both populations remain developer-exposed.
- Contracts12–14, provider/approval safety, OpenAPI, protocol20/readiness19,
  evaluation/source-package scripts, F3-E1/E2 adapters/tests and these normative
  curation/review procedures and both blank forms.
- Exact selection: ten new feasible held-out inputs, all eight supported matrix
  rows, all duration presets/day counts, known ID/tag exclusions; 20 future quality
  pairs (ten development/ten independent), first results only, clarity N/A.

Reports/handoffs and generated freeze JSON are excluded from freeze inputs to avoid
circular hashes. Owner must privately approve the exact candidate/reference before
curation. Current candidate is not that approval or a live model freeze. Later
model/price/source/prompt changes require a new freeze and population disposition;
do not silently test old cases under a changed relevant configuration.

## Commitments and overlap

Final contents and a fresh random32-byte secret belong only to the independent
curator, **outside developer/Codex/Git workspaces**. No key is generated or final
file opened here. `curator_token` is a bounded in-memory HMAC-SHA256 primitive for
future independent use; current tests supply clearly synthetic non-case bytes.

Domain separation binds `sealed-v2`, purpose input/content/key_context, freeze
fingerprint and bytes. Content commitment covers the independently canonicalized
full case (including ID/input/expectations). Input token covers its normalized
input fingerprint, omitting case ID, split, answer and description. Normalize via
ProfilePreferences, materialize defaults, sort exclusions and preserve exact text.
Renaming a case or reordering exclusions cannot evade overlap detection.

The public input index is derived only from the two fixed known public datasets,
including historical held-out inputs. Schema-invalid API fixtures cannot be feasible
quality inputs and are omitted from normalization; their original bytes are frozen.
The curator transforms every distinct exposed input fingerprint using the same
secret/freeze. Raw unsalted hashes of the small final profile space would permit
guessing and are **not final input tokens**. Key-context binding must match the
manifest, private index and owner pins. No actual token/root/reference is published.

Opaque metadata cannot prove correspondence to hidden bytes or human independence.
Independent attestation and later authorized full recomputation are required. A
same-key context detects mismatched metadata, not a dishonest attestor. Semantic
near-duplicates need human review beyond exact normalized identity.
The fixed public index covers these two known populations only. Future curation
also requires an independent private audit against all previously opened/exposed/
invalidated populations. Opaque tokens under different keys cannot establish that
history; missing custody/history blocks a new unseen claim.

## Ready manifest

Strict duplicate-key-safe JSON, <=32KiB/document, extra fields/coercions rejected.
Errors are fixed finite messages, models have opaque repr/str, no value logging.

| Field | Required meaning |
| --- | --- |
| version | sealed-evaluation-v2 |
| kind/population/exposure | independently_curated / opaque holdout-UUID / independently_sealed_unopened; tests use synthetic-* namespace and synthetic_not_unseen. Mixing is rejected |
| case_count/split | Exactly10 / held_out |
| curator_attestation_ref/owner_freeze_ref | Required independently reviewed opaque references; never supplied by this task; synthetic refs allowed only in test namespace |
| freeze_sha256 | Exact approved fingerprint, checked against current source/config |
| public_exposure_index_sha256 | Known public input-index binding from freeze |
| key_context | Private HMAC context shared by manifest/index/pins, not the key |
| entries | Ten ordered ordinals1–10, content commitment/input token; no duplicates |
| content_root | SHA-256 of canonical entries, binding every ordinal/commitment |
| coverage | Exactly six required category labels; actual coverage attested by curator |
| scorer/rubric | Existing model-hard-scorer-v1 / synthetic-plan-human-rubric-v1 |
| provenance/validation | curator_attestation_not_cryptographic_identity / metadata_only_not_case_validation |

`ReviewedPins` is independently owner-supplied: manifest digest, exposure-index
digest, content root, key context, freeze and references. Do not derive approval
from a candidate's own freshly recomputed digest. The private index count/digest
must bind the frozen public index; tokens are unique. Any candidate-input/index
intersection, changed root, missing attestation or mismatched pins stops.

`register_metadata` writes only a bounded exclusive fsynced local record;
`verify_registration` rechecks current freeze, both reviewed metadata inputs and
the saved record. Same population cannot register twice, including after partial
write. Registry lives under ignored `.cache/f3-e2` in an **owner-controlled checkout**;
no content/key is stored. This task registers synthetic fixtures only.

`invalidate_population` appends an exclusive finite reason marker: exposure,
configuration change, commitment mismatch or unverified provenance. Even partial
markers block verification/registration. No deletion, overwrite, re-key or reset.
Verification reads at most32KiB+1 even if the record grows after its size check.
Mode0600/path/link checks do not attest Windows DACLs or stop a malicious same-account
user; independent custody and externally retained pins are operational prerequisites.

## Opening, scoring and export

`open_population` always raises. No flag/state/pin opens content. A later owner-
authorized unit must verify full/input commitments using the privately retained
key, and implement a reviewed independent-case envelope to the **same** common
scorer. Current Case literals cannot truthfully represent sealed provenance;
do not relabel or add a second scorer. E2 has no case loader, score runner, real
collector, provider entrypoint or rating importer. F3-E1's incomplete/intermediate-
failure semantics remain required; human judgment never overrides hard failures.

Archive defense: reserved sealed-cases/private-evaluation/reviewer-materials/
blinding-keys components are excluded before content reads, alongside .cache/.aws/
credential/state exclusions. This is path-based defense, not a content scanner or
OS sandbox. Final content must remain outside any Git workspace; renaming secrets
into ordinary public paths cannot be prevented here. Only blank templates, public
freeze candidates and synthetic test code enter the review package.
