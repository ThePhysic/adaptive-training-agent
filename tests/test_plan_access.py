import pytest

from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.persistence.plans import OwnedPlanReader, PlanRow
from future_training.schemas import ApprovalResult, CandidateIdentity, ContextVersions, SavedPlan


class FakeRows:
    """Read-interface test double; these are not database-approved plans."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def get_owned(self, owner, plan_id):
        self.calls.append((owner, plan_id))
        return next((r for r in self.rows if r.owner_id == owner and r.plan_id == plan_id), None)

    async def list_owned(self, owner, limit, cursor):
        self.calls.append((owner, limit, cursor))
        return [
            r for r in self.rows if r.owner_id == owner and (cursor is None or r.plan_id > cursor)
        ][:limit]


@pytest.fixture
def rows(profile):
    plan = plan_week(profile, load_catalog()).plan
    result = []
    for principal, plan_id in [(Principal.A, "plan-a"), (Principal.B, "plan-b")]:
        snapshot = SavedPlan(
            approval=ApprovalResult(
                plan_id=plan_id,
                candidate=CandidateIdentity(
                    candidate_id="synthetic-candidate", revision=1, content_hash="a" * 64
                ),
            ),
            plan=plan,
            versions=ContextVersions(
                profile_revision=1, catalog_revision="catalog-v1", validator_revision="validator-v1"
            ),
        )
        result.append(PlanRow(principal.value, plan_id, snapshot.model_dump_json().encode()))
    return result


async def test_two_owner_read_history_cursor_and_copies(rows):
    source = FakeRows(rows)
    reader = OwnedPlanReader(source)
    result = await reader.get(Principal.A, "plan-a")
    result.plan.days.clear()
    assert len((await reader.get(Principal.A, "plan-a")).plan.days) == 2
    for plan_id in ("plan-a", "unknown"):
        with pytest.raises(ServiceError, match="not_found"):
            await reader.get(Principal.B, plan_id)
    assert [p.approval.plan_id for p in await reader.history(Principal.B)] == ["plan-b"]
    assert await reader.history(Principal.B, cursor="plan-b") == ()
    assert source.calls[-1][0] == Principal.B.value
    with pytest.raises(ServiceError, match="unauthorized"):
        await reader.get("synthetic-a", "plan-a")


async def test_backend_ownership_mistake_is_rejected_again(rows):
    source = FakeRows(rows)

    async def wrong(owner, plan_id):
        return rows[1]

    source.get_owned = wrong
    with pytest.raises(ServiceError, match="not_found"):
        await OwnedPlanReader(source).get(Principal.A, "plan-b")


@pytest.mark.parametrize("limit", [0, 21, True, "1"])
async def test_history_bounds(rows, limit):
    with pytest.raises(ServiceError, match="invalid_request"):
        await OwnedPlanReader(FakeRows(rows)).history(Principal.A, limit=limit)


async def test_history_rechecks_backend_owner_and_page_bounds(rows):
    source = FakeRows(rows)

    async def wrong_owner(owner, limit, cursor):
        return [rows[1]]

    source.list_owned = wrong_owner
    with pytest.raises(ServiceError, match="not_found"):
        await OwnedPlanReader(source).history(Principal.A)

    async def duplicate(owner, limit, cursor):
        return [rows[0], rows[0]]

    source.list_owned = duplicate
    with pytest.raises(ServiceError, match="internal_error"):
        await OwnedPlanReader(source).history(Principal.A)


async def test_corrupt_owned_readback_is_not_returned(rows):
    source = FakeRows([PlanRow(Principal.A.value, "plan-a", b'{"private":"synthetic-canary"}')])
    with pytest.raises(ServiceError) as error:
        await OwnedPlanReader(source).get(Principal.A, "plan-a")
    assert error.value.status == 503 and "synthetic-canary" not in str(error.value)
