"""F3-E4 synthetic-only contract rehearsal. No case paths, opener or executor.

Every accepted fixture copies a named, already public development input. The
fixed nonsecret key and repeated verification cannot establish genuine origin.
Independent states are specified but unreachable through this module's APIs.
"""

import hashlib
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, model_validator

from experiments import sealed_evaluation as sealed
from future_training.agent.protocol import ToolCall, canonical
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.experiments.model_evaluation import load_suite
from future_training.experiments.model_scoring import (
    Observation,
    ScoringFacts,
    check_call,
    score_facts,
)
from future_training.schemas import Identifier, ProfilePreferences

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/evaluation/study-v1"
SPEC = "docs/implementation/f3-e4-contract.md"
TEST_KEY = bytes(range(32))  # Public, predictable NONSECRET. Never a genuine commitment key.
IDS = (
    "ME-D01-20",
    "ME-D02-30",
    "ME-D03-45",
    "ME-D04-20",
    "ME-D05-30",
    "ME-D06-45",
    "ME-D07-20",
    "ME-D08-30",
    "ME-D01-45",
    "ME-D08-20",
)
Digest = sealed.Digest
Private = sealed.PrivateMetadata


class Study(Private):
    version: Literal["independent-study-selection-v1"]
    status: Literal["proposal_not_owner_approved"]
    development_ids: Annotated[tuple[Identifier, ...], Field(min_length=10, max_length=10)]
    selection_basis: Literal[
        "eight_rows_rotating_duration_then_two_end_row_extensions_no_output_selection"
    ]
    independent_ordinals: Annotated[tuple[StrictInt, ...], Field(min_length=10, max_length=10)]
    comparison_variants: tuple[Literal["template"], Literal["model"]]
    offline_rehearsal_variants: tuple[Literal["template"], Literal["fake"], Literal["replay"]]
    pairing: Literal["same_case_same_constraints_no_cross_case_pairing"]
    run_order: Literal[
        "development_list_then_independent_ordinals_odd_template_first_even_model_first"
    ]
    first_result: Literal[
        "one_result_per_case_variant_keep_failure_missing_uncertainty_no_replacement"
    ]
    hard_denominator: Literal[40]
    quality_pairs: Literal[20]
    quality_outputs: Literal[40]
    human_denominator: Literal["predeclared_reviewer_case_variant_dimension_slots"]
    missingness: Literal["keep_missing_abstained_ineligible_separate_no_imputation"]
    clarity: Literal["not_applicable"]
    reviewers: Literal["unappointed_two_preferred_at_least_ten_shared_pairs"]
    coverage: Literal[
        "aggregate_eight_rows_all_three_durations_all_day_counts_feasible_id_and_tag_exclusions"
    ]
    targets: Literal[
        "independent_9_of_10_legacy_9_of_9_separate_all_returned_plans_valid_zero_critical_failures"
    ]
    live_enabled: Literal[False]


def json_object(raw, limit=32768):
    try:
        if type(raw) is not bytes or len(raw) > limit or raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError
        raw.decode("utf-8", errors="strict")  # Do not accept JSON's UTF16/autodetect extensions.
        return sealed.metadata_json(raw)
    except Exception:
        raise ValueError("independent_fixture_rejected") from None


def study():
    try:
        data = json_object((DIRECTORY / "selection.json").read_bytes())
        value = Study.model_validate_json(canonical(data))
        if value.development_ids != IDS or value.independent_ordinals != tuple(range(1, 11)):
            raise ValueError
        if any(
            type(data[k]) is not int
            for k in ("hard_denominator", "quality_pairs", "quality_outputs")
        ):
            raise ValueError
        if type(data["live_enabled"]) is not bool:
            raise ValueError
        cases = {c.case_id: c for c in load_suite()[1]}
        selected = [cases[i] for i in IDS]
        if (
            any(c.split != "development" or c.fixture != "normal" for c in selected)
            or len({(c.profile.goal, c.profile.equipment, c.profile.experience) for c in selected})
            != 8
            or {c.profile.session_minutes for c in selected} != {20, 30, 45}
            or {c.profile.days_per_week for c in selected} != {2, 3, 4}
        ):
            raise ValueError
        return value.model_dump(mode="json")
    except Exception:
        raise ValueError("study_selection_rejected") from None


def freeze_inputs():
    public = sealed.public_sources()
    files = sealed.freeze_inputs()
    names = {SPEC, "tests/test_independent_cases.py"}
    names |= {n for n in public if n.startswith("experiments/") and n.endswith(".py")}
    names |= {n for n in public if n.startswith("data/evaluation/study-v1/")}
    if not names <= public.keys():
        raise ValueError("independent_freeze_source_missing")
    for name in sorted(names):
        raw = public[name].read_bytes()
        if len(raw) > 4194304:
            raise ValueError("independent_freeze_bounds")
        files[name] = hashlib.sha256(raw).hexdigest()
    return dict(sorted(files.items()))


def freeze():
    # New version. E2 candidate remains an immutable historical input, not rewritten.
    prior = ROOT / "docs/implementation/evidence/f3-e2-freeze-candidate.json"
    body = dict(
        version="evaluation-configuration-freeze-v2",
        status="candidate_not_owner_approved",
        files=freeze_inputs(),
        scorer=sealed.SCORER,
        scorer_interface="common-scoring-facts-v1",
        rubric=sealed.RUBRIC_VERSION,
        selection_sha256=sealed.digest(study()),
        historical_e2_candidate_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
        public_exposure_index_sha256=sealed.digest(sealed.exposed_input_index()),
        public_exposure_input_count=len(sealed.exposed_input_index()),
        live_enabled=False,
        monetary_authority=False,
    )
    return {**body, "fingerprint": sealed.digest(body)}


def check_freeze(value):
    try:
        if type(value) is not dict or canonical(value) != canonical(freeze()):
            raise ValueError
    except Exception:
        raise ValueError("independent_freeze_mismatch") from None


class Origin(Private):
    kind: Literal["developer_fixture", "independent_curator"]
    state: Literal["synthetic_fixture", "sealed_unopened", "opened_separate_authorization"]
    public_fixture_id: Identifier | None
    attestation_ref: sealed.Ref | None
    opening_ref: sealed.Ref | None

    @model_validator(mode="after")
    def consistent(self):
        if self.kind == "developer_fixture":
            if (
                self.state != "synthetic_fixture"
                or self.public_fixture_id is None
                or self.attestation_ref
                or self.opening_ref
            ):
                raise ValueError("case_origin_inconsistent")
        elif (
            self.public_fixture_id is not None
            or self.attestation_ref is None
            or (self.state not in ("sealed_unopened", "opened_separate_authorization"))
            or ((self.opening_ref is not None) != (self.state == "opened_separate_authorization"))
        ):
            raise ValueError("case_origin_inconsistent")
        return self


class CaseContent(Private):
    version: Literal["independent-case-v1"]
    case_id: Annotated[str, Field(pattern=r"^(fixture-[0-9]{2}|sealed-[a-f0-9]{32})$")]
    ordinal: Annotated[StrictInt, Field(ge=1, le=10)]
    profile: ProfilePreferences
    request_text: Literal[""]
    expected_outcome: Literal["plan"]
    required_tools: Annotated[
        tuple[Literal["search_exercises", "get_user_preferences"], ...],
        Field(min_length=1, max_length=2),
    ]
    coverage: Annotated[
        tuple[Literal["matrix", "duration", "schedule", "id_exclusion", "tag_exclusion"], ...],
        Field(min_length=3, max_length=5),
    ]
    checks: Literal["all_common_hard_checks_v1"]
    catalog_sha256: Digest
    freeze_sha256: Digest
    selection_sha256: Digest
    origin: Origin


def canonical_fixture(raw):
    """Only already-exposed, named public controls can be canonicalized here."""
    try:
        c = CaseContent.model_validate_json(canonical(json_object(raw, 8192)))
        if c.origin.kind != "developer_fixture" or c.origin.state != "synthetic_fixture":
            raise ValueError
        if (
            c.case_id != f"fixture-{c.ordinal:02}"
            or c.origin.public_fixture_id != IDS[c.ordinal - 1]
        ):
            raise ValueError
        source = next(x for x in load_suite()[1] if x.case_id == c.origin.public_fixture_id)
        p = c.profile.model_dump(mode="json")
        for name in ("excluded_ids", "excluded_tags"):
            p[name] = sorted(p[name])
        tags = {"matrix", "duration", "schedule"}
        tags |= {"id_exclusion"} if p["excluded_ids"] else set()
        tags |= {"tag_exclusion"} if p["excluded_tags"] else set()
        catalog = load_catalog()
        if (
            p != source.profile.model_dump(mode="json")
            or set(c.required_tools) != set(source.required_tools)
            or len(set(c.required_tools)) != len(c.required_tools)
            or set(c.coverage) != tags
            or len(tags) != len(c.coverage)
            or c.catalog_sha256 != catalog.fingerprint()
            or plan_week(c.profile, catalog).outcome != "plan"
        ):
            raise ValueError
        return canonical(
            {
                **c.model_dump(mode="json"),
                "profile": p,
                "required_tools": sorted(c.required_tools),
                "coverage": sorted(c.coverage),
            }
        )
    except Exception:
        raise ValueError("independent_fixture_rejected") from None


def verify_fixture_population(cases, raw, exposure_raw, configuration, pins):
    """Reuses E2 shapes/HMACs, binds them to v2 freeze, never registers/opens."""
    try:
        check_freeze(configuration)
        if type(cases) is not tuple or len(cases) != 10:
            raise ValueError
        m = sealed.SealedManifest.model_validate_json(canonical(json_object(raw)))
        x = sealed.ExposureIndex.model_validate_json(canonical(json_object(exposure_raw)))
        p = sealed.ReviewedPins.model_validate(pins.model_dump())
        fp = configuration["fingerprint"]
        context = sealed.curator_token(TEST_KEY, fp, b"SYNTHETIC", purpose="key_context")
        if (
            m.kind != "synthetic_test"
            or p.kind != "synthetic_test"
            or m.freeze_sha256 != fp
            or x.freeze_sha256 != fp
            or p.freeze_sha256 != fp
            or m.key_context != context
            or x.key_context != context
            or p.key_context != context
            or m.curator_attestation_ref != p.curator_attestation_ref
            or m.owner_freeze_ref != p.owner_freeze_ref
            or m.content_root != p.content_root
            or sealed.digest(m.model_dump()) != p.manifest_sha256
            or sealed.digest(x.model_dump()) != p.exposure_sha256
            or m.public_exposure_index_sha256 != configuration["public_exposure_index_sha256"]
            or x.public_exposure_index_sha256 != m.public_exposure_index_sha256
        ):
            raise ValueError
        expected_exposure = tuple(
            sealed.curator_token(TEST_KEY, fp, d.encode(), purpose="input")
            for d in sealed.exposed_input_index()
        )
        if x.tokens != expected_exposure:
            raise ValueError
        normalized = tuple(canonical_fixture(c) for c in cases)
        input_tokens = []
        for ordinal, (body, entry) in enumerate(zip(normalized, m.entries, strict=True), 1):
            c = CaseContent.model_validate_json(body)
            token = sealed.curator_token(
                TEST_KEY,
                fp,
                sealed.input_fingerprint(c.profile.model_dump(), c.request_text).encode(),
                purpose="input",
            )
            if (
                c.ordinal != ordinal
                or c.freeze_sha256 != fp
                or c.selection_sha256 != configuration["selection_sha256"]
                or entry.input_token != token
                or entry.content_commitment
                != sealed.curator_token(TEST_KEY, fp, body, purpose="content")
            ):
                raise ValueError
            input_tokens.append(token)
        if len(set(input_tokens)) != 10:
            raise ValueError
        # Deliberate exposed overlap is REQUIRED in this fixture-only rehearsal.
        if not set(input_tokens) <= set(x.tokens):
            raise ValueError
        return dict(
            state="synthetic_integrity_verified_not_independent",
            case_count=10,
            exposure="public_controls_already_exposed",
            human_scores=None,
        )
    except Exception:
        raise ValueError("independent_fixture_verification_stopped") from None


class Proposal(Private):
    response_ordinal: Annotated[StrictInt, Field(ge=0, le=3)]
    schema_valid: StrictBool
    domain_valid: StrictBool


class ToolAttempt(Private):
    name: Annotated[str, Field(max_length=64)]
    arguments_json: Annotated[str, Field(max_length=8192)] = Field(repr=False)


class FixtureEvidence(Private):
    version: Literal["independent-fixture-evidence-v1"]
    variant: Literal["template", "fake", "replay"]
    public_fixture_id: Identifier
    complete: StrictBool
    observation: Observation | None
    responses: Annotated[tuple[Literal["tools", "proposal", "failed"], ...], Field(max_length=3)]
    proposals: Annotated[tuple[Proposal, ...], Field(max_length=3)]
    tool_attempts: Annotated[tuple[ToolAttempt, ...], Field(max_length=4)]
    accounting_status: Literal["not_applicable_template", "synthetic_known", "synthetic_unknown"]
    charged_micro: Annotated[StrictInt, Field(ge=0, le=10**12)] | None
    held_micro: Annotated[StrictInt, Field(ge=0, le=10**12)] | None
    uncertainty: Annotated[
        tuple[Literal["missing", "transport", "cancelled", "cleanup", "unknown_usage"], ...],
        Field(max_length=5),
    ]


def score_fixture(cases, raw, exposure_raw, configuration, pins, ordinal, evidence_raw):
    """Pure synthetic evidence scoring; no callbacks, path discovery or execution."""
    try:
        verify_fixture_population(cases, raw, exposure_raw, configuration, pins)
        if type(ordinal) is not int or not 1 <= ordinal <= 10:
            raise ValueError
        data = json_object(evidence_raw)
        evidence = FixtureEvidence.model_validate_json(canonical(data))
        c = CaseContent.model_validate_json(canonical_fixture(cases[ordinal - 1]))
        if evidence.public_fixture_id != c.origin.public_fixture_id:
            raise ValueError
        observed = evidence.observation
        if observed is not None and (
            observed.source != evidence.variant
            or set(data["observation"]) != set(Observation.model_fields)
        ):
            raise ValueError  # No inherited default-true proposal/publication flags.
        accounting = dict(
            status=evidence.accounting_status,
            charged_micro=evidence.charged_micro,
            held_micro=evidence.held_micro,
            actual_total_micro=None,
        )
        metadata = dict(
            case_id=c.case_id,
            variant=evidence.variant,
            freeze_sha256=configuration["fingerprint"],
            selection_sha256=configuration["selection_sha256"],
            provenance="synthetic_not_model_or_human_evidence",
            counts=observed.counts if observed else None,
            proposals=[p.model_dump() for p in evidence.proposals],
            uncertainty=list(evidence.uncertainty),
        )
        complete = (
            evidence.complete
            and observed is not None
            and bool(evidence.proposals)
            and not evidence.uncertainty
        )
        complete &= evidence.accounting_status != "synthetic_unknown"
        complete &= evidence.variant == "template" or (
            evidence.charged_micro is not None and evidence.held_micro is not None
        )
        if observed is not None:
            expected_proposals = [i for i, v in enumerate(evidence.responses, 1) if v == "proposal"]
            if evidence.variant == "template":
                complete &= (
                    not evidence.responses
                    and evidence.accounting_status == "not_applicable_template"
                )
                complete &= observed.counts.get("provider_requests") == 0
                expected_proposals = [0]
            else:
                complete &= evidence.accounting_status == "synthetic_known"
                complete &= len(evidence.responses) == observed.counts.get("provider_requests")
                complete &= "failed" not in evidence.responses
            complete &= [p.response_ordinal for p in evidence.proposals] == expected_proposals
            complete &= len(evidence.tool_attempts) == len(observed.tools)
            for attempt, verdict in zip(evidence.tool_attempts, observed.tools, strict=False):
                name, valid, authorized = check_call(
                    ToolCall(
                        call_id="synthetic",
                        name=attempt.name,
                        arguments_json=attempt.arguments_json,
                    ),
                    c.profile,
                    load_catalog(),
                )
                if (verdict.name, verdict.arguments_valid, verdict.authorized) != (
                    name,
                    valid,
                    authorized,
                ):
                    raise ValueError
        if not complete:
            return dict(
                version="independent-fixture-result-v1",
                state="incomplete",
                score=None,
                accounting=accounting,
                **metadata,
            )
        observed = observed.model_copy(
            update={
                "proposal_schema_valid": observed.proposal_schema_valid
                and all(p.schema_valid for p in evidence.proposals),
                "proposals_domain_valid": observed.proposals_domain_valid
                and all(p.domain_valid for p in evidence.proposals),
            }
        )
        facts = ScoringFacts(
            case_id=c.case_id,
            split="synthetic_fixture",
            profile=c.profile,
            request_text=c.request_text,
            expected={evidence.variant: c.expected_outcome},
            required_tools=list(c.required_tools),
            fixture="normal",
        )
        scored = score_facts(facts, observed, load_catalog())
        return dict(
            version="independent-fixture-result-v1",
            state="scored_synthetic_fixture",
            score=scored,
            accounting=accounting,
            **metadata,
        )
    except Exception:
        raise ValueError("independent_fixture_scoring_stopped") from None


def retain_first(directory, ordinal, variant, result):
    """Exclusive synthetic result retention; partial/failed writes block reuse."""
    if (
        type(ordinal) is not int
        or not 1 <= ordinal <= 10
        or variant not in ("template", "fake", "replay")
    ):
        raise ValueError("synthetic_retention_rejected")
    if (
        type(result) is not dict
        or set(result)
        != {
            "version",
            "state",
            "score",
            "accounting",
            "case_id",
            "variant",
            "freeze_sha256",
            "selection_sha256",
            "provenance",
            "counts",
            "proposals",
            "uncertainty",
        }
        or result.get("version") != "independent-fixture-result-v1"
        or result.get("provenance") != "synthetic_not_model_or_human_evidence"
        or result.get("case_id") != f"fixture-{ordinal:02}"
        or result.get("variant") != variant
        or result.get("state") not in ("incomplete", "scored_synthetic_fixture")
    ):
        raise ValueError("synthetic_retention_rejected")
    if any(
        type(result[k]) is not str
        or len(result[k]) != 64
        or not set(result[k]) <= set("0123456789abcdef")
        for k in ("freeze_sha256", "selection_sha256")
    ):
        raise ValueError("synthetic_retention_rejected")
    scored = result.get("score")
    if (result["state"] == "incomplete" and scored is not None) or (
        result["state"] == "scored_synthetic_fixture"
        and (
            type(scored) is not dict
            or scored.get("case_id") != result["case_id"]
            or scored.get("split") != "synthetic_fixture"
            or scored.get("source") != variant
            or scored.get("quality_scores") is not None
        )
    ):
        raise ValueError("synthetic_retention_rejected")
    directory = Path(directory).absolute()
    if (
        not directory.resolve().is_relative_to((ROOT / ".cache/f3-e4").resolve())
        or not directory.is_dir()
        or any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents))
        or type(ordinal) is not int
        or not 1 <= ordinal <= 10
        or variant not in ("template", "fake", "replay")
    ):
        raise ValueError("synthetic_retention_rejected")
    sealed.write_exclusive(directory / f"first-{ordinal:02}-{variant}.json", result)


def open_independent(*args, **kwargs):
    raise ValueError("genuine_opening_requires_separate_authorization_and_source_review")
