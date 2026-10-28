"""Bounded offline HTTP reads using the existing development HTTPX dependency.

No socket transport, arbitrary URLs, retry loop, writes or generation entry point.
The caller owns the Deadline scope and Budget. Production still uses direct services.
"""

import asyncio
import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal

import httpx
from pydantic import Field, TypeAdapter, ValidationError

from future_training.agent.budget import Budget, Deadline
from future_training.agent.protocol import parse_json
from future_training.candidates import encode_snapshot
from future_training.domain.catalog import Catalog
from future_training.identity import Principal, owner_id
from future_training.observability import annotate, span, traced
from future_training.schemas import CatalogRecord, SavedPlan, SavedProfile

ReadName = Literal["profile", "catalog", "history"]
_PATHS = {
    "profile": "/api/v1/profile",
    "catalog": "/api/v1/exercises?limit=20",
    "history": "/api/v1/plans?limit=5",
}
_CAPS = {"profile": 16384, "catalog": 32768, "history": 5 * 69632}
_CATALOG = TypeAdapter(Annotated[list[CatalogRecord], Field(max_length=20)])
_HISTORY = TypeAdapter(Annotated[list[SavedPlan], Field(max_length=5)])


class ReadFailure(StrEnum):
    AUTHORIZATION = "read_unauthorized"
    INVALID = "read_invalid_result"
    OVERSIZE = "read_response_too_large"
    TIMEOUT = "read_timeout"
    TRANSPORT = "read_transport"
    HTTP = "read_http"
    UNAVAILABLE = "read_unavailable"
    INTERNAL = "read_internal"


class ReadFault(Exception):
    def __init__(self, kind: ReadFailure):
        self.kind = kind
        self.reason = kind.value
        super().__init__(kind.value)


@dataclass(frozen=True)
class HistoryRead:
    plans: tuple[SavedPlan, ...] = ()
    unavailable: ReadFailure | None = None


@dataclass(frozen=True)
class ReadContext:
    profile: SavedProfile
    catalog: tuple[CatalogRecord, ...]
    history: HistoryRead
    eligible_ids: tuple[str, ...]


class LocalReads:
    def __init__(
        self,
        transport: httpx.MockTransport | httpx.ASGITransport,
        principal: Principal,
        catalog: Catalog,
    ):
        owner_id(principal)
        if type(transport) not in (httpx.MockTransport, httpx.ASGITransport):
            raise ValueError("Explicit offline MockTransport or ASGITransport required")
        self._principal, self._catalog = principal, catalog
        self._client = httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1:8000",
            trust_env=False,
            follow_redirects=False,
            timeout=None,
        )

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args):
        return await self._client.__aexit__(*args)

    async def _get(self, name: ReadName, deadline: Deadline):
        with span("async.http", read=name):
            deadline.check()
            try:
                # Phase timeout is additional to, never a reset of, caller's deadline.
                async with (
                    asyncio.timeout(2),
                    self._client.stream(
                        "GET",
                        _PATHS[name],
                        headers={"X-Synthetic-Principal": self._principal.value},
                    ) as response,
                ):
                    annotate(http_status=response.status_code)
                    if response.status_code in (401, 403):
                        raise ReadFault(ReadFailure.AUTHORIZATION)
                    if response.status_code in (408, 429) or 500 <= response.status_code < 600:
                        raise ReadFault(ReadFailure.UNAVAILABLE)
                    if response.status_code != 200:
                        raise ReadFault(ReadFailure.HTTP)
                    if (
                        response.headers.get("content-type", "").split(";", 1)[0]
                        != "application/json"
                        or response.headers.get("content-encoding", "identity") != "identity"
                    ):
                        raise ReadFault(ReadFailure.INVALID)
                    data = bytearray()
                    # Non-identity encoding is rejected above, before body decoding.
                    async for chunk in response.aiter_bytes():
                        if len(data) + len(chunk) > _CAPS[name]:
                            raise ReadFault(ReadFailure.OVERSIZE)
                        data.extend(chunk)
                        deadline.check()
                    annotate(response_bytes=len(data))
                deadline.check()
                return parse_json(data.decode("utf-8", errors="strict"))
            except (
                httpx.TimeoutException,
                TimeoutError,
            ):
                raise ReadFault(ReadFailure.TIMEOUT) from None
            except (
                httpx.TransportError,
                OSError,
            ):
                raise ReadFault(ReadFailure.TRANSPORT) from None
            except (
                UnicodeError,
                ValueError,
                RecursionError,
            ):
                raise ReadFault(ReadFailure.INVALID) from None
            except ReadFault:
                raise
            except Exception:
                raise ReadFault(ReadFailure.INTERNAL) from None

    @traced("async.read")
    async def profile(self, deadline: Deadline) -> SavedProfile:
        annotate(read="profile")
        try:
            value = SavedProfile.model_validate(await self._get("profile", deadline))
            if self._catalog.unknown_exclusions(value.preferences):
                raise ReadFault(ReadFailure.INVALID)
            return value
        except ValidationError:
            raise ReadFault(ReadFailure.INVALID) from None

    @traced("async.read")
    async def catalog(self, deadline: Deadline) -> tuple[CatalogRecord, ...]:
        annotate(read="catalog")
        try:
            value = _CATALOG.validate_python(await self._get("catalog", deadline))
            # Current frozen seed fits one bounded page. No silent truncation,
            # invented IDs or changed metadata/provenance enter the experiment.
            if value != self._catalog.records():
                raise ReadFault(ReadFailure.INVALID)
            return tuple(value)
        except ValidationError:
            raise ReadFault(ReadFailure.INVALID) from None

    @traced("async.read")
    async def history(self, deadline: Deadline) -> HistoryRead:
        annotate(read="history")
        try:
            values = _HISTORY.validate_python(await self._get("history", deadline))
            ids = [value.approval.plan_id for value in values]
            if ids != sorted(set(ids)):
                raise ReadFault(ReadFailure.INVALID)
            for value in values:
                digest = hashlib.sha256(encode_snapshot(value.plan)).hexdigest()
                if digest != value.approval.candidate.content_hash:
                    raise ReadFault(ReadFailure.INVALID)
            return HistoryRead(tuple(values))
        except ValidationError:
            raise ReadFault(ReadFailure.INVALID) from None
        except ReadFault as error:
            if error.kind not in (
                ReadFailure.TRANSPORT,
                ReadFailure.TIMEOUT,
                ReadFailure.UNAVAILABLE,
            ):
                raise
            annotate(outcome="error", reason=error.reason)
            # Availability failure is explicit, not a fabricated successful empty history.
            return HistoryRead(unavailable=error.kind)


async def read_context(reads: LocalReads, deadline: Deadline, budget: Budget, *, concurrent=True):
    """Three independent fixed reads; required results must all succeed before filtering."""
    with span("async.batch", execution="concurrent" if concurrent else "sequential"):
        deadline.check()
        # Reserve every dispatch before creating children. Exhaustion starts no HTTP work.
        for _ in range(3):
            budget.dispatch()
        if concurrent:
            owner = asyncio.current_task()
            cancellations = owner.cancelling()
            try:
                async with asyncio.TaskGroup() as tasks:
                    profile_task = tasks.create_task(reads.profile(deadline))
                    catalog_task = tasks.create_task(reads.catalog(deadline))
                    history_task = tasks.create_task(reads.history(deadline))
            except* ReadFault as errors:
                if owner.cancelling() > cancellations:
                    raise asyncio.CancelledError from None
                # Deterministic classification when several reads fail together.
                priority = list(ReadFailure)
                fault = min(errors.exceptions, key=lambda error: priority.index(error.kind))
                raise ReadFault(fault.kind) from None
            profile, catalog, history = (
                profile_task.result(),
                catalog_task.result(),
                history_task.result(),
            )
        else:
            profile = await reads.profile(deadline)
            catalog = await reads.catalog(deadline)
            history = await reads.history(deadline)
        deadline.check()
        # Do not overlap this dependent step or invent another eligibility algorithm.
        eligible = tuple(
            record.exercise_id for record in reads._catalog.eligible(profile.preferences)
        )
        annotate(
            profile_revision=profile.revision,
            catalog_revision=reads._catalog.revision,
            read_requests=3,
        )
        return ReadContext(profile, catalog, history, eligible)
