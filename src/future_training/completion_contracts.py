"""F2-04 additive schemas; preserve the frozen F1 domain/schema provenance."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field, StrictInt, field_validator, model_validator

from future_training.schemas import (
    ApiError,
    ContentHash,
    Contract,
    ErrorCode,
    IdempotencyKey,
    Identifier,
)

SessionIndex = Annotated[StrictInt, Field(ge=1, le=4)]
PlanRevision = Annotated[StrictInt, Field(ge=1, le=2)]
COMPLETION_ERRORS = frozenset({"session_already_recorded", "plan_mismatch"})


class SessionFeedback(Contract):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"status": {"const": "skipped"}}},
                    "then": {
                        "properties": {"effort": {"type": "null"}, "rating": {"type": "null"}}
                    },
                }
            ]
        },
    )
    status: Literal["completed", "partial", "skipped"]
    effort: Literal["easy", "moderate", "hard"] | None = None
    rating: Annotated[StrictInt, Field(ge=1, le=5)] | None = None

    @model_validator(mode="after")
    def skipped_has_no_feedback(self):
        if self.status == "skipped" and (self.effort is not None or self.rating is not None):
            raise ValueError("Skipped sessions cannot have feedback")
        return self


class SessionSubmission(SessionFeedback):
    expected_revision: Literal[0]
    plan_revision: PlanRevision
    plan_content_hash: ContentHash
    idempotency_key: IdempotencyKey

    @field_validator("expected_revision", mode="before")
    @classmethod
    def integer_revision(cls, value):
        if type(value) is not int:
            raise ValueError("Revision must be an integer")
        return value


class SessionRecord(SessionFeedback):
    record_id: Identifier
    plan_id: Identifier
    day_index: SessionIndex
    revision: Literal[1] = 1
    plan_revision: PlanRevision
    plan_content_hash: ContentHash

    @field_validator("revision", mode="before")
    @classmethod
    def integer_revision(cls, value):
        if type(value) is not int:
            raise ValueError("Revision must be an integer")
        return value


class SubmissionError(ApiError):
    code: ErrorCode | Literal["session_already_recorded", "plan_mismatch"]
