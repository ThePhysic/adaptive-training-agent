# F3-E3A — Owner decisions and independent curator handoff

2026-10-27. **Procedure for later review, not authorization.** No named curator,
final cases, real secret, commitment, attestation, pins, registration or opening
is supplied. Read the [assessment](f3-e3a-freeze-readiness-assessment.md) first.
Accepted [E2 curator](f3-e2-curator-procedure.md) and
[human-review](f3-e2-human-review-materials.md) protocols remain unchanged.

## Owner-supervised gates

Each gate needs its own recorded human decision; no preceding gate authorizes
the next. Store identities, acknowledgements and future opaque population metadata
privately outside developer/chat/review artifacts. Public reports use only finite
statuses, no content, identifiers, commitment keys or reviewer material.

| Gate | Owner checks | Required evidence / stop |
| --- | --- | --- |
| T — technical validation | Reproduce fixed public candidate/current source; run existing synthetic checks; review interface/coverage/model gaps | Passing checks below prove bytes/software only. Current final-study recommendation remains DEFER |
| O — freeze approval | Decide actual study release, envelope/canonicalization, selection, model config and all freeze inputs; independently review exact fingerprint | Private dated scope/reference plus checked public candidate, not candidate self-approval. OPEN decisions or expected imminent changes block final approval |
| C — curator acknowledgement | Choose qualified independent human, review conflicts; curator acknowledges exact owner-approved fingerprint and scope **before** creating anything | Authenticated private acknowledgement, freeze/time order and explicit independent-custody responsibility; labels/UUIDs alone do not identify anyone |
| K — custody verification | Owner/witness verifies optionA orB, authorized viewers, encryption, independent plaintext environment, key backup, retention and incident plan | Non-final dummy rehearsal and signed/witnessed checklist. No OS/access assurance inferred from `.cache` or0600. Missing isolation means stop |
| R — registration authorization | After future independent curation only, verify attestation/index/root/manifest/freeze and independently recorded pins; review exclusive local storage | Explicit authorization for exact genuine metadata on owner-controlled checkout, no case/key file input. Existing/partial records stop; never reset. **Not authorized here** |
| E — opening/study/human collection | Later exact population and first-run selection, verified opener, provenance, privacy/model/budget/outbound and reviewers | Separate implementation/source and execution decisions; genuine ratings only, full denominators. Current opener always denies |

### T: exact local public-source check

In the repository PowerShell terminal, no transcript/debug mode and no AWS/provider
credentials needed. This reads only the fixed public candidate/code/known exposed
datasets and prints public configuration status. It writes nothing and does not
approve, replace or register a manifest. Stop on any error; do not auto-regenerate.

```powershell
@'
import json, sys
from pathlib import Path
sys.path.insert(0, 'src')
from experiments import sealed_evaluation as e
p = Path('docs/implementation/evidence/f3-e2-freeze-candidate.json')
before = p.read_bytes()
candidate = e.metadata_json(before)
first, second = e.freeze(), e.freeze()
assert e.canonical(first) == e.canonical(second)
e.check_freeze(candidate)
assert p.read_bytes() == before
print(json.dumps({'technical_check': 'matched',
                  'status': candidate['status'],
                  'frozen_files': len(candidate['files']),
                  'owner_approved_by_this_check': False}))
'@ | .venv/Scripts/python.exe -
```

Expected status is candidate_not_owner_approved, frozen_files99. Additional
synthetic tests write only synthetic temp/registry records; they are not genuine
registration. No genuine private file/directory or key is an argument here.

For gateO, resolve the [decision matrix](f3-e3a-freeze-readiness-assessment.md) first.
Record privately: intended study/evidence type, exact release/fingerprint, selected
public development IDs, aggregate coverage interpretation, model/variant/run
settings, preservation of first failures, closure of interface decisions, human
approver/time and stated scope. Leave approval absent until a human actually
decides. This document contains no filled approval template or invented reference.
Any new normative study artifact must actually be bound by the final freeze;
adding an arbitrary report currently does not achieve that. Review the complete
execution path: new experimental files outside the current exact-path selection
are not automatically fingerprinted, even if `check_freeze` still passes.

## Curator responsibilities in plain language

You would be responsible for making ten new synthetic test requests after the
owner has fixed the program and study rules. You must not help tune the program
against those requests, reveal them to its developer/Codex, or choose requests
because a model already did well on them. This is an evaluation role, not medical
review or a claim that the workouts are effective.

Before accepting, understand structured profiles, the supported catalog/domain
rules, feasibility checks, privacy and basic version/hash procedures. Disclose
prior authorship/tuning, access to proposed cases, personal/project interests and
any constraints on independent custody. The owner decides whether independence
is adequate; an opaque attestation reference cannot settle a conflict of interest.
If no independent person is available, report an exposed comparison instead.

You may receive the final public configuration/freeze, schema/domain contract12,
catalog and validator/baseline code, the coverage brief, scoring/rubric rules,
canonicalization instructions, and known historical **inputs** for overlap checks.
Strip model outputs and desired workouts from the historical-input brief; give
the normalized public index as well. Hashes alone cannot support semantic novelty
review. Do not receive hidden desired development answers or tune against model
outputs. Developers may know coverage/rules and opaque metadata; your final inputs,
expectations, key, private incident history and later reviewer/blinding materials
must remain hidden from them until separately approved opening.

### Future ten-case brief — no inputs selected here

- Exactly ten feasible synthetic adult/nonmedical structured inputs, expected
  plan outcome, empty request_text under the present interface. Actual input/schema
  contract must be finalized before creation.
- Cover each of the eight goal/equipment/experience rows at least once in the
  population; both goals, both equipment settings and both experience values are
  fixed by contract12, not invented. Across the same ten, include every20/30/45
  minute preset and every2/3/4-day schedule.
- Include feasible known-ID and known-tag exclusion coverage under the owner's
  approved minima. Coverage may coincide; do not infer a full24-cell cross-product
  or every catalog tag is required. Stop if the requested interpretation needs
  more cases or infeasible combinations.
- Check schema/catalog/independent validator and deterministic baseline feasibility
  in the independent environment. No provider request or selection by model success.
- Compare normalized inputs (defaults materialized, exclusions sorted, text exact)
  against both public populations and every privately retained prior exposed/
  opened/invalidated input. Ignore IDs/splits/answers when checking input overlap.
  Reject duplicates and manually review near-duplicates; different IDs/whitespace
  are not evidence of meaningful novelty.

The brief is a proposal pending owner gateO, not final case contents or an amendment
to the accepted ten-case population. Keep actual coverage checks private. Other
failure/clarification/abstention controls remain separate development evidence.

### Future integrity and attestations

Only after gatesO/C/K and explicit independent-curation permission, the curator
would generate a fresh random32-byte secret using an approved cryptographic
mechanism in the independent environment. **No key-generation command is supplied
or run now.** Never use the predictable test key. Approve the exact full-case
schema/canonical bytes first; case IDs, inputs and expected checks are committed
together. Use the reviewed HMAC domain/freeze/purpose separation for content,
normalized-input tokens and key context; same key/context for the transformed
public exposure index. Bind ordered entries into the existing canonical content root.

Keep keys and plaintext cases apart from delivered opaque metadata. Protect the
original key and one encrypted independent recovery copy; record a non-secret
custody/recovery reference. Owner/witness can rehearse recovery with dummy bytes
before any real material exists. A lost key is not permission to regenerate/recommit
after results. Compromise stops the population for independent incident disposition.

The attestation must privately identify the human and any witness, final freeze
acknowledgement/time before curation, independence/conflicts, synthetic-only sources,
coverage/feasibility and exposure-history checks, canonicalization/key context,
exact manifest/index/root digests, custody/backup/retention and any incidents.
Use an authenticated human channel and independently compare the metadata pins.
No one may invent a missing attestation, manufacture successful checks or treat
the candidate's own digest as independent owner approval.

Deliver to the owner only the bounded opaque v2 manifest/private exposure index,
attestation and witnessed digest/reference record through the approved private
handoff. Keep cases/key at the curator. Do not put genuine metadata, keys, raw
cases, reviewer records or identities in Git, VSCode agent attachments, traces,
shared manifests or a review ZIP. Owner gateR remains separate; no registration
or opening command is supplied here.

## Minimal custody options — neither established by this task

| Property | A: independent encrypted device/account | B: independently controlled encrypted storage |
| --- | --- | --- |
| Arrangement | Curator's existing separate device, independently controlled login/storage, supported encryption verified by owner/witness | Curator-held encrypted removable drive/archive plus independently controlled trusted working device/session; developer must never see it unlocked |
| Confidentiality | Stronger practical separation if developer has no administrator/key/sync access | Encrypted at rest only; custody and plaintext working environment are critical. A shared developer account/device can observe plaintext or keys |
| Independence | Human role/conflict declaration plus operational separation | Human independence still required; possession of encrypted media alone does not establish it |
| Complexity/cost | Lowest setup if curator already owns suitable equipment; availability/licensing/encryption not verified here | Low storage overhead and no hosted service; careful unlock/lock/handoff procedure. May still require another independent working device |
| Access/handoff | Owner sees metadata/attestation only; no developer-admin access, shared folders or synchronization | Physical custody documented; lock before handoff; no saved decryption key on developer machine or mounted media in IDE/session |
| Recovery | One encrypted separate backup with independent custodian; approved retention/destruction | Independent offline backup and custody log; media loss/damage has greater operational risk |
| Exposure risks | Shared accounts, automatic backup/cloud sync, screen sharing/chat/diagnostic uploads | Decrypting on developer host, temporary files/swap/previews, autosave/indexing/sync and key/password sharing |
| Verification | Witness on non-final dummy content: allowed/denied users, supported encryption, closed network/sync, backup/recovery and archive exclusions | Same dummy rehearsal plus mount/unmount and no residual plaintext on the independent working system |

RecommendA if already available. B is acceptable only with independent plaintext
execution/custody; an encrypted file placed on this developer laptop is insufficient
by itself. Neither option authorizes setup or transfers. Confirm resources/software/
permissions with the custodian later; no OS/account/encryption settings were changed.
Filesystem0600, ignored directories and archive exclusions do not prove Windows
DACLs, disk encryption, administrative isolation or the absence of copies.

Owner must choose exact allowed viewers, physical custody, incident contact,
backup recovery and retention/deletion dates before curation. Do not automatically
apply the14-day synthetic-artifact convention to the only genuine evidence/key.
Keep enough independent records to audit first results/exposure; delete only after
the explicit approved retention decision, preserving necessary audit commitments.

## Independent verification without revealing cases

| Check | Owner can verify from approved public/opaque material | Curator / independent witness must verify privately |
| --- | --- | --- |
| Freeze | Recompute current source map and candidate; compare exact externally approved fingerprint | Confirm acknowledgement preceded curation and no later changed configuration used |
| Metadata | Strict version/size/shape, ten ordered distinct entries, required refs, exact pinned digests/root/context, declared split/coverage and no synthetic namespace | Actual human identity/independence, truth of attestation, intended references |
| Overlap | Compare candidate tokens with declared transformed index, count against47 public identities; compare digests to independently approved pins | Every token corresponds to the correct normalized input, same key/context; full prior private exposure history and semantic near-duplicates |
| Full content binding | Detect change to pinned ordered commitments; no reading of cases required | Correct reviewed canonical bytes, actual feasibility/coverage/expected checks and HMAC recomputation using retained key |
| Custody | Review authenticated witness/access/backup/incident attestations and dummy rehearsal evidence | Actual encryption/key/device isolation, no leaked plaintext/copies, recovery usable |
| Registration | Under a later authorization, verify exact saved metadata/pins/current freeze and absence of invalidation | Private custody and truth of hidden checks remain human responsibilities; registration never opens content |

Hashes detect changes relative to trusted pins; they do not prove truth or human
identity. HMACs resist guessing of small input spaces without the secret, but an
owner who never receives the key cannot independently recompute hidden commitments.
Opaque refs and matching key-context strings do not authenticate the attestor or
prove all tokens used one secret. A second independent witness should recompute
coverage/overlap/commitments on the curator's system and attest only a bounded
checklist; do not transfer content to the owner-developer merely to witness it.
If no witness is available, the owner must explicitly accept and report weaker
single-curator assurance, not claim cryptographic proof of independence.

Any altered pin, mismatch, incident, lost exposure history/key or source drift
means stop. Keep original commitments/records; do not overwrite, re-key, rerun or
use a new directory/population ID to conceal a problem. Owner then separately
approves incident handling/invalidation and any genuinely new curation. Revealed
cases stay exposed even if deleted. Disappointing evaluation results remain first
results; later debugging never replaces their denominator or grants a retry.
