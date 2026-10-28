import pytest
from pydantic import ValidationError

from future_training.completion_contracts import SessionRecord, SessionSubmission


def body(**updates):
    return {
        "expected_revision": 0,
        "plan_revision": 1,
        "plan_content_hash": "a" * 64,
        "idempotency_key": "submit-key",
        "status": "completed",
        **updates,
    }


@pytest.mark.parametrize("status", ["completed", "partial", "skipped"])
def test_bounded_status_and_optional_feedback(status):
    value = SessionSubmission(**body(status=status))
    assert value.rating is None and value.effort is None
    assert SessionSubmission.model_validate_json(value.model_dump_json()) == value


@pytest.mark.parametrize(
    "updates",
    [
        {"expected_revision": True},
        {"expected_revision": 0.0},
        {"expected_revision": 1},
        {"plan_revision": True},
        {"plan_revision": 3},
        {"rating": True},
        {"rating": 3.0},
        {"rating": 0},
        {"rating": 6},
        {"effort": "pain"},
        {"notes": "synthetic-canary"},
        {"owner_id": "synthetic-b"},
        {"status": "unknown"},
        {"plan_content_hash": "invalid"},
        {"idempotency_key": "x" * 129},
        {"idempotency_key": "with spaces"},
        {"status": "skipped", "effort": "easy"},
        {"status": "skipped", "rating": 1},
    ],
)
def test_invalid_and_excess_data_rejected(updates):
    with pytest.raises(ValidationError):
        SessionSubmission(**body(**updates))


@pytest.mark.parametrize("rating", [1, 5])
def test_feedback_boundaries_and_record_shape(rating):
    submission = SessionSubmission(**body(rating=rating, effort="moderate"))
    record = SessionRecord(
        record_id="record",
        plan_id="plan",
        day_index=4,
        **submission.model_dump(exclude={"idempotency_key", "expected_revision"}),
    )
    assert record.revision == 1
    assert "idempotency_key" not in record.model_dump()
    with pytest.raises(ValidationError):
        SessionRecord.model_validate({**record.model_dump(), "revision": True})
