"""Owner-scoped approved-plan read interface, composed with the PostgreSQL adapter."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from pydantic import TypeAdapter, ValidationError

from future_training.errors import ServiceError
from future_training.identity import Principal, owner_id
from future_training.schemas import Identifier, SavedPlan


@dataclass(frozen=True)
class PlanRow:
    owner_id: str
    plan_id: str
    snapshot: bytes


class ApprovedPlanSource(Protocol):
    """SQL adapters filter owner and keyset-page by ascending plan ID."""

    async def get_owned(self, owner: str, plan_id: str) -> PlanRow | None: ...
    async def list_owned(self, owner: str, limit: int, cursor: str | None) -> Sequence[PlanRow]: ...


class OwnedPlanReader:
    """Both the SQL query and this adapter enforce ownership."""

    def __init__(self, source: ApprovedPlanSource):
        self._source = source

    def _read(self, row: PlanRow | None, owner: str) -> SavedPlan:
        if row is None or row.owner_id != owner:
            raise ServiceError(404, "not_found")
        try:
            result = SavedPlan.model_validate_json(row.snapshot)
            if result.approval.plan_id != row.plan_id:
                raise ValueError
            return result
        except (
            ValueError,
            ValidationError,
        ):
            raise ServiceError(503, "internal_error") from None

    async def get(self, principal: Principal, plan_id: str) -> SavedPlan:
        owner = owner_id(principal)
        try:
            TypeAdapter(Identifier).validate_python(plan_id)
        except ValidationError:
            raise ServiceError(422, "invalid_request") from None
        row = await self._source.get_owned(owner, plan_id)
        result = self._read(row, owner)
        if result.approval.plan_id != plan_id:
            raise ServiceError(404, "not_found")
        return result

    async def history(self, principal: Principal, *, limit: int = 20, cursor: str | None = None):
        owner = owner_id(principal)
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ServiceError(422, "invalid_request")
        if cursor is not None:
            try:
                TypeAdapter(Identifier).validate_python(cursor)
            except ValidationError:
                raise ServiceError(422, "invalid_request") from None
        rows = await self._source.list_owned(owner, limit, cursor)
        if len(rows) > limit:
            raise ServiceError(503, "internal_error")
        ids = [row.plan_id for row in rows]
        if ids != sorted(set(ids)) or (cursor is not None and any(i <= cursor for i in ids)):
            raise ServiceError(503, "internal_error")
        return tuple(self._read(row, owner) for row in rows)
