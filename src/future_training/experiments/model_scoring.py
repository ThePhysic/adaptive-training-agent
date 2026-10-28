"""One hard scorer for template, fake, replay and future imported live evidence.

This module neither calls providers nor assigns human/model quality ratings.
"""

from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, ValidationError

from future_training.agent.protocol import RESULT_ADAPTER, Wire, canonical, parse_json
from future_training.agent.tools import ProfileArguments, SearchArguments
from future_training.domain.catalog import Catalog
from future_training.domain.validator import validate_plan
from future_training.schemas import Identifier, ProfilePreferences

SCORER = "model-hard-scorer-v1"
Evidence = Literal["template", "fake", "replay", "live"]


class Case(Wire):
    case_id: Identifier
    split: Literal["development", "comparison_candidate"]
    profile: ProfilePreferences
    request_text: Annotated[str, Field(max_length=2048)]
    fixture: Literal[
        "normal",
        "medical",
        "refusal",
        "malformed",
        "unknown_tool",
        "invalid_arguments",
        "owner_argument",
        "constraint_violation",
        "incomplete",
        "duplicate_call",
        "transport",
    ]
    expected: dict[Evidence, Literal["plan", "clarify", "abstain", "error"]]
    required_tools: Annotated[
        list[Literal["search_exercises", "get_user_preferences"]], Field(max_length=2)
    ]
    provenance: Literal["developer_authored_synthetic_2026-10-25"]
    exposure: Literal["developer_exposed_not_blind"]
    eligibility: Literal["saved_profile_agent", "controlled_provider_fixture"]


class ToolEvidence(Wire):
    name: Literal["search_exercises", "get_user_preferences", "unknown"]
    arguments_valid: StrictBool
    authorized: StrictBool
    result_valid: StrictBool
    status: Literal["ok", "error"]


class Observation(Wire):
    # Accepting a label is not proof of origin. Only the offline runner creates
    # observations now; a future live importer needs its own approved provenance.
    source: Evidence
    output_json: Annotated[str, Field(max_length=16384)] = Field(repr=False)
    terminal_state: Literal["ready_unpublished", "failed", "cancelled"]
    tools: Annotated[list[ToolEvidence], Field(max_length=4)] = Field(default_factory=list)
    proposal_schema_valid: StrictBool = True
    proposals_domain_valid: StrictBool = True
    counts: dict[str, Annotated[StrictInt, Field(ge=0, le=10**9)]]
    no_publication: StrictBool = True


def check_call(call, profile: ProfilePreferences, catalog: Catalog):
    """Reuse dispatcher argument schemas; retain verdicts, never raw arguments."""
    name = call.name if call.name in ("search_exercises", "get_user_preferences") else "unknown"
    authorized = name != "unknown"
    try:
        data = parse_json(call.arguments_json)
        # No identity, file, URL or write fields are capabilities, even in an
        # otherwise recognized tool. Strict schemas reject all additional fields.
        authorized &= isinstance(data, dict) and not set(data).difference(
            SearchArguments.model_fields if name == "search_exercises" else ()
        )
        model = SearchArguments if name == "search_exercises" else ProfileArguments
        args = model.model_validate(data)
        valid = name != "unknown"
        if isinstance(args, SearchArguments):
            valid &= (
                args.goal in (None, profile.goal)
                and args.experience in (None, profile.experience)
                and not (args.equipment == "dumbbells" and profile.equipment == "bodyweight")
                and (args.tag is None or args.tag in catalog.known_tags)
            )
    except (
        ValidationError,
        ValueError,
        TypeError,
        RecursionError,
    ):
        valid = False
    return name, bool(valid), bool(authorized)


def proposal_checks(output, profile, catalog):
    """Inspect proposed output independently, including proposals later repaired."""
    try:
        parsed = RESULT_ADAPTER.validate_python(output)
    except (
        ValidationError,
        ValueError,
        TypeError,
        RecursionError,
    ):
        return False, False
    return True, parsed.outcome != "plan" or validate_plan(parsed.plan, profile, catalog).valid


def score(case: Case, observed: Observation, catalog: Catalog) -> dict:
    # Re-validate forged/mutated models and disallow any extra transcript fields.
    observed = Observation.model_validate_json(observed.model_dump_json())
    case = Case.model_validate_json(case.model_dump_json())
    return _score(case, observed, catalog)


class ScoringFacts(Wire):
    """Validated scoring inputs, without a claim about case/evidence origin.

    Origin/authorization belongs to the separately gated experiment boundary.
    This API performs no execution, opening, provenance upgrade or billing claim.
    The v1 Case and its wrapper remain unchanged.
    """

    case_id: Identifier
    split: Literal["synthetic_fixture", "independent_opened"]
    profile: ProfilePreferences
    request_text: Annotated[str, Field(max_length=2048)]
    expected: dict[Evidence, Literal["plan", "clarify", "abstain", "error"]]
    required_tools: Annotated[
        list[Literal["search_exercises", "get_user_preferences"]], Field(max_length=2)
    ]
    fixture: Literal["normal"]


def score_facts(case: ScoringFacts, observed: Observation, catalog: Catalog) -> dict:
    """Same hard rules as v1; facts are not authenticated case provenance."""
    case = ScoringFacts.model_validate_json(case.model_dump_json())
    if case.split != "synthetic_fixture":
        raise ValueError("independent_opening_not_authorized")
    observed = Observation.model_validate_json(observed.model_dump_json())
    return _score(case, observed, catalog)


def _score(case, observed, catalog):
    checks = {}
    issues = []
    try:
        if len(observed.output_json.encode("utf-8")) > 16384:
            raise ValueError("Oversized terminal output")
        output = RESULT_ADAPTER.validate_python(parse_json(observed.output_json))
        checks["schema"] = True
    except (
        ValidationError,
        ValueError,
        TypeError,
        RecursionError,
    ):
        output = None
        checks["schema"] = False
    actual = output.outcome if output else "invalid"
    checks["outcome"] = actual == case.expected.get(observed.source)
    checks["domain"] = True
    if output and actual == "plan":
        report = validate_plan(output.plan, case.profile, catalog)
        checks["domain"] = report.valid and not case.request_text
        issues = sorted({i.code for i in report.issues})
    elif output and actual == "clarify":
        checks["clarification"] = bool(
            set(output.fields) <= (set(ProfilePreferences.model_fields) | {"preferences_text"})
        ) and (not case.request_text or "preferences_text" in output.fields)
    elif output and actual == "abstain":
        checks["abstention"] = output.next_step == (
            "seek_qualified_professional"
            if output.reason == "medical_context"
            else "change_supported_preferences"
        )
    checks["terminal"] = (
        output is not None
        and observed.terminal_state == ("failed" if actual == "error" else "ready_unpublished")
        and observed.no_publication
    )
    limits = {
        "provider_requests": 3,
        "count_requests": 3,
        "wire_requests": 6,
        "tool_dispatches": 4,
        "semantic_repairs": 1,
        "transport_retries": 1,
        "input_tokens": 16000,
        "output_tokens": 4000,
    }
    checks["budgets"] = (
        set(observed.counts) == set(limits)
        and all(observed.counts.get(key, maximum + 1) <= maximum for key, maximum in limits.items())
        and observed.counts.get("tool_dispatches") == len(observed.tools)
        and observed.counts.get("wire_requests")
        == observed.counts.get("provider_requests", 0) + observed.counts.get("count_requests", 0)
    )
    checks["tool_arguments"] = all(t.arguments_valid and t.result_valid for t in observed.tools)
    checks["authorization"] = all(t.authorized for t in observed.tools)
    # Template has no provider tool capability; compare outcomes without
    # pretending its nonexistent dispatch was model-selected.
    checks["required_tools"] = (
        observed.source == "template"
        or actual == "error"
        or all(
            any(t.name == name and t.status == "ok" for t in observed.tools)
            for name in case.required_tools
        )
    )
    checks["proposal_schema"] = observed.proposal_schema_valid
    checks["proposal_domain"] = observed.proposals_domain_valid
    hard = all(checks.values())
    handling = all(
        checks.get(k, True)
        for k in (
            "schema",
            "outcome",
            "domain",
            "clarification",
            "abstention",
            "terminal",
            "budgets",
        )
    )
    return {
        "case_id": case.case_id,
        "split": case.split,
        "source": observed.source,
        "expected": case.expected.get(observed.source),
        "actual": actual,
        "checks": checks,
        "handling_passed": handling,
        "hard_passed": hard,
        "failures": sorted(k for k, value in checks.items() if not value),
        "domain_issues": issues,
        "quality_eligible": hard and actual == "plan" and case.fixture == "normal",
        "quality_scores": None,
        "explanation_clarity": "not_applicable_no_explanation_field",
        "output": parse_json(canonical(output.model_dump())) if output else None,
        "tools": [t.model_dump() for t in observed.tools],
        "counts": observed.counts,
        "terminal_scope": "internal_unpublished_not_HTTP_SSE",
    }
