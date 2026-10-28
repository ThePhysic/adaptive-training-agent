"""F3-E2 metadata only. No case loader, scorer runner, key generation or CLI.

Genuine case bytes and keys belong to an independent curator, outside this
developer workspace. APIs that hash bytes are for that future curator or clearly
synthetic tests; registration consumes opaque metadata, never case contents.
"""

import hashlib
import hmac
import importlib.util
import os
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, StrictInt, model_validator

from future_training.agent.protocol import Wire, canonical, parse_json
from future_training.experiments.model_review import DIMENSIONS, RUBRIC_VERSION
from future_training.experiments.model_scoring import SCORER
from future_training.schemas import ProfilePreferences

ROOT = Path(__file__).resolve().parents[1]
VERSION = "sealed-evaluation-v2"
LIMIT = 32768
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Ref = Annotated[str, Field(pattern=r"^(attestation-[a-f0-9]{32}|synthetic-[a-z0-9-]{1,64})$")]
COVERAGE = (
    "eight_supported_matrix_rows",
    "all_duration_presets",
    "supported_day_counts",
    "known_id_exclusions",
    "known_tag_exclusions",
    "feasible_nonmedical_profiles",
)
SPEC = "docs/implementation/f3-e2-sealed-evaluation-specification.md"
CURATOR = "docs/implementation/f3-e2-curator-procedure.md"
HUMAN = "docs/implementation/f3-e2-human-review-materials.md"
TEMPLATE = "docs/implementation/templates/f3-e2-human-review-blank.json"
CURATION_TEMPLATE = "docs/implementation/templates/f3-e2-curation-blank.json"


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def public_sources():
    spec = importlib.util.spec_from_file_location(
        "public_review_source", ROOT / "scripts/review_source.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.inventory()


def input_fingerprint(profile, text):
    """Constraint identity, independent of case ID/split/expected result/order."""
    try:
        value = ProfilePreferences.model_validate(profile).model_dump()
        if type(text) is not str or len(text.encode()) > 2048:
            raise ValueError
        for field in ("excluded_ids", "excluded_tags"):
            value[field] = sorted(value[field])
        return digest(dict(profile=value, request_text=text))
    except Exception:
        raise ValueError("evaluation_input_rejected") from None


def exposed_input_index():
    # These exact two public populations are already developer-exposed. Never
    # discover a new dataset directory or accept a caller-supplied content path.
    public = public_sources()
    fingerprints = set()
    for name in ("data/evaluation/v1/scenarios.jsonl", "data/evaluation/model-v1/scenarios.jsonl"):
        for line in public[name].read_bytes().splitlines():
            row = parse_json(line)
            try:
                fingerprints.add(input_fingerprint(row["profile"], row.get("request_text", "")))
            except ValueError:
                # Schema-invalid legacy API fixtures cannot be feasible held-out
                # quality inputs. Their original bytes remain frozen separately.
                continue
    return sorted(fingerprints)


def freeze_inputs():
    public = public_sources()
    exact = {
        "experiments/counted_probe.py",
        "experiments/sealed_evaluation.py",
        "tests/test_counted_probe_evidence.py",
        "tests/test_sealed_evaluation.py",
        "scripts/review_source.py",
        "scripts/evaluate_models.py",
        "scripts/prepare_model_evaluation.py",
        "uv.lock",
        "pyproject.toml",
        ".python-version",
        "web/package-lock.json",
        "docs/planning/12-f0-domain-contract.md",
        "docs/planning/13-f0-candidate-approval-contract.md",
        "docs/planning/14-f0-remaining-contract-clarifications.md",
        "docs/planning/19-f3-03c-pre-live-readiness.md",
        "docs/planning/20-f3-model-evaluation-protocol.md",
        "contracts/provider-safety.md",
        "contracts/approval-safety.md",
        "contracts/openapi.json",
        SPEC,
        CURATOR,
        HUMAN,
        TEMPLATE,
        CURATION_TEMPLATE,
    }
    if not exact <= set(public):
        raise ValueError("freeze_required_source_missing")
    names = exact | {
        n
        for n in public
        if (
            n.startswith("src/future_training/")
            and n.endswith(".py")
            or n.startswith("data/catalog/")
            or n.startswith("data/evaluation/v1/")
            or n
            in {
                "data/evaluation/model-v1/scenarios.jsonl",
                "data/evaluation/model-v1/manifest.json",
                "data/evaluation/model-v1/outputs.jsonl",
            }
            or n.startswith("data/experiments/f3-02/v1/")
        )
    }
    result = {}
    for name in sorted(names):
        body = public[name].read_bytes()
        if len(body) > 4194304:
            raise ValueError("freeze_source_bound")
        result[name] = hashlib.sha256(body).hexdigest()
    return result


def freeze():
    index = exposed_input_index()
    body = dict(
        version="evaluation-configuration-freeze-v1",
        status="candidate_not_owner_approved",
        files=freeze_inputs(),
        scorer=SCORER,
        rubric=RUBRIC_VERSION,
        selection=dict(
            sealed_count=10,
            split="held_out",
            feasible_only=True,
            coverage=list(COVERAGE),
            outcome="plan",
            quality_pairs=20,
            development_pairs=10,
            first_results_only=True,
            clarity="not_applicable",
        ),
        public_exposure_index_sha256=digest(index),
        public_exposure_input_count=len(index),
        live_enabled=False,
        monetary_authority=False,
    )
    return {**body, "fingerprint": digest(body)}


def check_freeze(value):
    try:
        if type(value) is not dict or canonical(value) != canonical(freeze()):
            raise ValueError
        return value
    except Exception:
        raise ValueError("configuration_freeze_mismatch") from None


class PrivateMetadata(Wire):
    model_config = ConfigDict(hide_input_in_errors=True)

    def __repr__(self):
        return "<private_evaluation_metadata>"

    def __str__(self):
        return self.__repr__()


class Entry(PrivateMetadata):
    ordinal: Annotated[StrictInt, Field(ge=1, le=10)]
    content_commitment: Digest
    input_token: Digest


class SealedManifest(PrivateMetadata):
    version: Literal["sealed-evaluation-v2"]
    kind: Literal["synthetic_test", "independently_curated"]
    population: Annotated[
        str, Field(pattern=r"^(synthetic-[a-z0-9-]{1,64}|holdout-[a-f0-9]{32})$", repr=False)
    ]
    case_count: Annotated[StrictInt, Field(ge=10, le=10)]
    split: Literal["held_out"]
    exposure: Literal["synthetic_not_unseen", "independently_sealed_unopened"]
    curator_attestation_ref: Ref
    owner_freeze_ref: Ref
    freeze_sha256: Digest
    public_exposure_index_sha256: Digest
    content_root: Digest
    key_context: Digest
    entries: Annotated[tuple[Entry, ...], Field(min_length=10, max_length=10, repr=False)]
    coverage: Annotated[tuple[str, ...], Field(min_length=6, max_length=6)]
    scorer: Literal["model-hard-scorer-v1"]
    rubric: Literal["synthetic-plan-human-rubric-v1"]
    provenance: Literal["curator_attestation_not_cryptographic_identity"]
    validation: Literal["metadata_only_not_case_validation"]

    @model_validator(mode="after")
    def consistent(self):
        synthetic = self.kind == "synthetic_test"
        if (
            self.population.startswith("synthetic-") != synthetic
            or self.exposure
            != ("synthetic_not_unseen" if synthetic else "independently_sealed_unopened")
            or any(
                ref.startswith("synthetic-") != synthetic
                for ref in (self.curator_attestation_ref, self.owner_freeze_ref)
            )
            or tuple(e.ordinal for e in self.entries) != tuple(range(1, 11))
            or len({e.content_commitment for e in self.entries}) != 10
            or len({e.input_token for e in self.entries}) != 10
            or tuple(sorted(self.coverage)) != tuple(sorted(COVERAGE))
            or self.content_root != digest([e.model_dump() for e in self.entries])
        ):
            raise ValueError("sealed_metadata_inconsistent")
        return self


class ExposureIndex(PrivateMetadata):
    version: Literal["private-exposure-index-v1"]
    freeze_sha256: Digest
    public_exposure_index_sha256: Digest
    key_context: Digest
    tokens: Annotated[tuple[Digest, ...], Field(max_length=90, repr=False)]


class ReviewedPins(PrivateMetadata):
    """Supplied independently by owner; never derived as approval by registration."""

    kind: Literal["synthetic_test", "independently_curated"]
    manifest_sha256: Digest
    exposure_sha256: Digest
    content_root: Digest
    key_context: Digest
    freeze_sha256: Digest
    curator_attestation_ref: Ref
    owner_freeze_ref: Ref


def metadata_json(raw):
    try:
        if type(raw) is not bytes or len(raw) > LIMIT:
            raise ValueError
        value = parse_json(raw)
        if type(value) is not dict:
            raise ValueError
        return value
    except Exception:
        raise ValueError("sealed_metadata_rejected") from None


def validate_manifest(raw, exposure_raw, configuration, pins):
    """Opaque metadata only; no content path, key, case loader or scorer call."""
    try:
        check_freeze(configuration)
        m = SealedManifest.model_validate_json(canonical(metadata_json(raw)))
        x = ExposureIndex.model_validate_json(canonical(metadata_json(exposure_raw)))
        pins = ReviewedPins.model_validate(pins.model_dump())
        if (
            m.kind != pins.kind
            or m.freeze_sha256 != configuration["fingerprint"]
            or x.freeze_sha256 != m.freeze_sha256
            or pins.freeze_sha256 != m.freeze_sha256
            or m.curator_attestation_ref != pins.curator_attestation_ref
            or m.owner_freeze_ref != pins.owner_freeze_ref
            or m.content_root != pins.content_root
            or m.key_context != pins.key_context
            or x.key_context != m.key_context
            or digest(m.model_dump()) != pins.manifest_sha256
            or digest(x.model_dump()) != pins.exposure_sha256
            or m.public_exposure_index_sha256 != configuration["public_exposure_index_sha256"]
            or x.public_exposure_index_sha256 != m.public_exposure_index_sha256
            or len(x.tokens) != configuration["public_exposure_input_count"]
            or len(set(x.tokens)) != len(x.tokens)
            or set(e.input_token for e in m.entries) & set(x.tokens)
        ):
            raise ValueError
        return m
    except Exception:
        raise ValueError("sealed_metadata_rejected") from None


def curator_token(key, configuration_fingerprint, value, *, purpose):
    """Future curator in-memory HMAC primitive. Never reads case/key files.

    For input tokens, value is the normalized input fingerprint. For content
    commitments, value is independently canonicalized complete case bytes.
    Current tests use explicit synthetic non-case bytes and a fake test key.
    """
    if type(key) is not bytes or len(key) != 32 or type(value) is not bytes or len(value) > 65536:
        raise ValueError("curator_commitment_bounds")
    if not re.fullmatch(r"[a-f0-9]{64}", configuration_fingerprint) or purpose not in (
        "input",
        "content",
        "key_context",
    ):
        raise ValueError("curator_commitment_bounds")
    return hmac.new(
        key,
        b"sealed-v2\0"
        + purpose.encode()
        + b"\0"
        + configuration_fingerprint.encode()
        + b"\0"
        + value,
        hashlib.sha256,
    ).hexdigest()


def local_registry(directory):
    directory = Path(directory).absolute()
    if (
        not directory.resolve().is_relative_to((ROOT / ".cache/f3-e2").resolve())
        or not directory.is_dir()
        or any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents))
    ):
        raise ValueError("private_registry_required")
    return directory


def write_exclusive(path, value):
    body = canonical(value) + b"\n"
    if len(body) > LIMIT:
        raise ValueError("registry_record_bounds")
    try:
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        raise ValueError("registry_write_stopped_record_retained") from None


def register_metadata(raw, exposure_raw, configuration, pins, *, directory):
    m = validate_manifest(raw, exposure_raw, configuration, pins)
    directory = local_registry(directory)
    if (directory / (m.population + ".invalidated.json")).exists():
        raise ValueError("population_invalidated")
    record = dict(
        version="sealed-registration-v1",
        state="registered_unopened",
        manifest=m.model_dump(),
        reviewed_pins=pins.model_dump(),
    )
    write_exclusive(directory / (m.population + ".json"), record)
    return {
        "state": "registered_unopened",
        "case_count": 10,
        "kind": m.kind,
        "validation": "metadata_only_not_case_validation",
    }


def invalidate_population(population, *, directory, reason):
    # Presence of even a partial invalidation marker blocks future verification.
    if (
        type(population) is not str
        or not re.fullmatch(r"(?:synthetic-[a-z0-9-]{1,64}|holdout-[a-f0-9]{32})", population)
        or reason
        not in (
            "accidental_exposure",
            "configuration_changed",
            "commitment_mismatch",
            "provenance_unverified",
        )
    ):
        raise ValueError("invalidation_metadata_rejected")
    directory = local_registry(directory)
    write_exclusive(directory / (population + ".invalidated.json"), dict(reason=reason))


def verify_registration(raw, exposure_raw, configuration, pins, *, directory):
    m = validate_manifest(raw, exposure_raw, configuration, pins)
    directory = local_registry(directory)
    if (directory / (m.population + ".invalidated.json")).exists():
        raise ValueError("population_invalidated")
    try:
        path = directory / (m.population + ".json")
        if path.is_symlink() or path.is_junction() or path.stat().st_size > LIMIT:
            raise ValueError
        with path.open("rb") as stream:
            saved = metadata_json(stream.read(LIMIT + 1))
        if canonical(saved) != canonical(
            dict(
                version="sealed-registration-v1",
                state="registered_unopened",
                manifest=m.model_dump(mode="json"),
                reviewed_pins=pins.model_dump(mode="json"),
            )
        ):
            raise ValueError
    except Exception:
        raise ValueError("registration_verification_stopped") from None
    return {"state": "registered_unopened", "kind": m.kind, "case_count": 10}


def open_population(*args, **kwargs):
    raise ValueError("separate_content_opening_authorization_required")


def blank_review():
    return dict(
        version="sealed-human-form-v1",
        rubric=RUBRIC_VERSION,
        evidence_type="human_pending_not_collected",
        pair_id=None,
        variant=None,
        reviewer_token=None,
        judgment_status="pending",
        judgment_reference=None,
        ratings=dict.fromkeys(DIMENSIONS),
        explanation_clarity=None,
        abstention_reason=None,
    )


def review_status_counts(planned_slots, received):
    """Status counts, NOT verified judgments, quality scores or reviewer agreement.

    Planned slot IDs are private operator assignments, not model/case labels.
    No absence is converted to a rating; all planned slots stay in denominator.
    """
    if (
        type(planned_slots) is not tuple
        or not 1 <= len(planned_slots) <= 80
        or len(set(planned_slots)) != len(planned_slots)
        or any(type(s) is not str or not re.fullmatch(r"slot-[0-9]{1,3}", s) for s in planned_slots)
        or type(received) is not dict
        or not set(received) <= set(planned_slots)
        or any(
            s not in ("pending", "missing", "abstained", "ineligible", "rated_attested")
            for s in received.values()
        )
    ):
        raise ValueError("review_status_metadata_rejected")
    result = {s: 0 for s in ("pending", "missing", "abstained", "ineligible", "rated_attested")}
    for slot in planned_slots:
        result[received.get(slot, "missing")] += 1
    return dict(
        planned=len(planned_slots),
        counts=result,
        verified_judgments=0,
        quality_scores=None,
        evidence="reported_status_only_not_verified_quality_judgments",
    )
