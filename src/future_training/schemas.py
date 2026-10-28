"""Strict structural contracts derived from ratified planning documents 12–14.

Parsing a proposal does NOT establish catalog feasibility, calculated duration,
user authorization, or fitness safety. Independent domain validation is F1-02.
"""

from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
    model_validator,
)

Goal = Literal["general_strength", "general_conditioning"]
Equipment = Literal["bodyweight", "dumbbells_and_bodyweight"]
Experience = Literal["beginner", "intermediate"]
Mode = Literal["repetitions", "timed"]
Identifier = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]
Tag = Annotated[str, Field(min_length=1, max_length=32, pattern=r"^[a-z0-9_-]+$")]
Revision = Annotated[StrictInt, Field(ge=1)]
ContentHash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
IdempotencyKey = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")]
SafeText = Annotated[str, Field(min_length=1, max_length=512)]
Rest = Annotated[StrictInt, Field(ge=30, le=90, multiple_of=15)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProfilePreferences(Contract):
    adult: StrictBool
    goal: Goal
    equipment: Equipment
    experience: Experience
    days_per_week: Literal[2, 3, 4]
    session_minutes: Literal[20, 30, 45]
    excluded_ids: Annotated[list[Identifier], Field(max_length=12)] = Field(default_factory=list)
    excluded_tags: Annotated[list[Tag], Field(max_length=8)] = Field(default_factory=list)

    @field_validator("days_per_week", "session_minutes", mode="before")
    @classmethod
    def integer_presets(cls, value):
        # Literal integer matching otherwise accepts equal floats even in strict mode.
        if type(value) is not int:
            raise ValueError("schedule presets must be integers")
        return value

    @field_validator("excluded_ids", "excluded_tags", mode="before")
    @classmethod
    def deduplicate(cls, value):
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return list(dict.fromkeys(value))
        return value

    @model_validator(mode="after")
    def adults_only(self) -> Self:
        if not self.adult:
            raise ValueError("adult attestation required")
        return self


class ProfileSaveRequest(Contract):
    expected_revision: Annotated[StrictInt, Field(ge=0)]
    preferences: ProfilePreferences


class SavedProfile(Contract):
    revision: Revision
    preferences: ProfilePreferences


class Provenance(Contract):
    origin: Literal["original", "licensed"]
    attribution: SafeText
    license: SafeText
    source_reference: SafeText


class CatalogRecord(Contract):
    exercise_id: Identifier
    title: Annotated[str, Field(min_length=1, max_length=120)]
    goals: Annotated[list[Goal], Field(min_length=1, max_length=2)]
    mode: Mode
    equipment: Literal["bodyweight", "dumbbells"]
    experiences: Annotated[list[Experience], Field(min_length=1, max_length=2)]
    exclusion_tags: Annotated[list[Tag], Field(max_length=8)]
    provenance: Provenance
    catalog_revision: Identifier

    @model_validator(mode="after")
    def compatible_mode(self) -> Self:
        expected = "general_strength" if self.mode == "repetitions" else "general_conditioning"
        if set(self.goals) != {expected}:
            raise ValueError("catalog goal and mode disagree")
        return self


class RepetitionBlock(Contract):
    exercise_id: Identifier
    mode: Literal["repetitions"]
    sets: Annotated[StrictInt, Field(ge=2, le=4)]
    repetitions_per_set: Annotated[StrictInt, Field(ge=6, le=15)]
    rest_between_sets_seconds: Rest


class TimedBlock(Contract):
    exercise_id: Identifier
    mode: Literal["timed"]
    sets: Annotated[StrictInt, Field(ge=2, le=4)]
    work_seconds_per_set: Annotated[StrictInt, Field(ge=30, le=90)]
    rest_between_sets_seconds: Rest


Block = Annotated[RepetitionBlock | TimedBlock, Field(discriminator="mode")]


class DayPlan(Contract):
    day_index: Annotated[StrictInt, Field(ge=1, le=4)]
    blocks: Annotated[list[Block], Field(min_length=3, max_length=6)]
    planned_seconds: Annotated[StrictInt, Field(ge=0)]

    @model_validator(mode="after")
    def distinct_exercises(self) -> Self:
        if len({block.exercise_id for block in self.blocks}) != len(self.blocks):
            raise ValueError("duplicate exercise within day")
        return self


class PlanProposal(Contract):
    """Structural proposal only; never a domain-validation certificate."""

    profile: ProfilePreferences
    days: Annotated[list[DayPlan], Field(min_length=2, max_length=4)]

    @model_validator(mode="after")
    def matrix_bounds(self) -> Self:
        profile = self.profile
        if sorted(day.day_index for day in self.days) != list(range(1, profile.days_per_week + 1)):
            raise ValueError("day indices must be exactly 1..requested days")
        for day in self.days:
            for block in day.blocks:
                expected = "repetitions" if profile.goal == "general_strength" else "timed"
                if block.mode != expected:
                    raise ValueError("goal and prescription mode disagree")
                if profile.experience == "beginner":
                    if block.sets > 3:
                        raise ValueError("beginner sets exceed contract")
                    if isinstance(block, RepetitionBlock):
                        if block.repetitions_per_set > 12 or block.rest_between_sets_seconds < 45:
                            raise ValueError("beginner strength prescription exceeds contract")
                    elif block.work_seconds_per_set > 75:
                        raise ValueError("beginner timed prescription exceeds contract")
        return self


class CandidateIdentity(Contract):
    candidate_id: Identifier
    revision: Revision
    content_hash: ContentHash


class ContextVersions(Contract):
    profile_revision: Revision
    catalog_revision: Identifier
    validator_revision: Identifier


class ApprovalRequest(CandidateIdentity):
    idempotency_key: IdempotencyKey


class ApprovalResult(Contract):
    plan_id: Identifier
    candidate: CandidateIdentity


class SavedPlan(Contract):
    approval: ApprovalResult
    plan: PlanProposal
    versions: ContextVersions


class GenerateRequest(Contract):
    profile_revision: Revision
    preferences_text: Annotated[str, Field(max_length=2048)] = ""


class ReviseRequest(GenerateRequest):
    candidate: CandidateIdentity


ErrorCode = Literal[
    "invalid_request",
    "not_found",
    "candidate_expired",
    "candidate_superseded",
    "revision_in_progress",
    "candidate_already_approved",
    "candidate_mismatch",
    "stale_profile",
    "idempotency_mismatch",
    "budget_exceeded",
    "provider_failure",
    "internal_error",
    "reconciliation_pending",
    "capacity_exceeded",
    "unauthorized",
]


class ApiError(Contract):
    code: ErrorCode
    retryable: StrictBool = False
    # Fixed codes only: no arbitrary exception, prompt or provider error strings.


class PlanOutcome(Contract):
    outcome: Literal["plan"]
    candidate: CandidateIdentity


class ClarifyOutcome(Contract):
    outcome: Literal["clarify"]
    fields: Annotated[list[Identifier], Field(min_length=1, max_length=12)]
    choices: Annotated[list[SafeText], Field(min_length=1, max_length=12)]


class AbstainOutcome(Contract):
    outcome: Literal["abstain"]
    reason: Literal["unsupported_scope", "infeasible", "medical_context"]
    next_step: Literal["change_supported_preferences", "seek_qualified_professional"]


class ErrorOutcome(Contract):
    outcome: Literal["error"]
    error: ApiError


TerminalOutcome = Annotated[
    PlanOutcome | ClarifyOutcome | AbstainOutcome | ErrorOutcome, Field(discriminator="outcome")
]


class EventBase(Contract):
    schema_version: Literal["1"] = "1"
    request_id: Identifier
    sequence: Annotated[StrictInt, Field(ge=0)]


class StatusPayload(Contract):
    stage: Literal["context", "drafting", "validating", "repairing"]


class StatusEvent(EventBase):
    event_type: Literal["status"]
    payload: StatusPayload


class DraftEvent(EventBase):
    event_type: Literal["draft"]
    payload: PlanProposal  # No candidate identity/token here.


class ErrorEvent(EventBase):
    event_type: Literal["error"]
    payload: ApiError


class DoneEvent(EventBase):
    event_type: Literal["done"]
    payload: TerminalOutcome


StreamEvent = Annotated[
    StatusEvent | DraftEvent | ErrorEvent | DoneEvent, Field(discriminator="event_type")
]


class BudgetLimits(Contract):
    # Fixed ratified values, not runtime permissions or an enforcement engine.
    deadline_seconds: Literal[30] = 30
    read_tools: Literal[4] = 4
    provider_attempts: Literal[3] = 3
    semantic_repairs: Literal[1] = 1
    transport_retries: Literal[1] = 1
    input_tokens: Literal[16000] = 16000
    output_tokens: Literal[4000] = 4000
    per_principal_runs: Literal[1] = 1
    global_runs: Literal[2] = 2

    @model_validator(mode="before")
    @classmethod
    def integer_limits(cls, value):
        if isinstance(value, dict) and any(type(item) is not int for item in value.values()):
            raise ValueError("budget limits must be integers")
        return value


class CandidateLimits(Contract):
    ttl_seconds: Literal[1800] = 1800
    lineages: Literal[200] = 200
    store_bytes: Literal[16777216] = 16777216
    candidate_bytes: Literal[65536] = 65536
    request_bytes: Literal[16384] = 16384
    successful_revisions: Literal[1] = 1

    @model_validator(mode="before")
    @classmethod
    def integer_limits(cls, value):
        if isinstance(value, dict) and any(type(item) is not int for item in value.values()):
            raise ValueError("candidate limits must be integers")
        return value


CandidateStatus = Literal["ready", "revision_pending", "approved", "expired", "superseded"]
CommitState = Literal["idle", "committing", "reconciling", "unresolved", "committed", "rolled_back"]


class CandidateMetadata(Contract):
    """Internal shape only, not a candidate store or a client-supplied owner."""

    lineage_id: Identifier
    owner_id: Identifier
    candidate: CandidateIdentity
    versions: ContextVersions
    expires_at_monotonic: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    status: CandidateStatus
    commit_state: CommitState = "idle"
    successful_revisions: Annotated[StrictInt, Field(ge=0, le=1)] = 0
    pending_revision_token: Identifier | None = None
