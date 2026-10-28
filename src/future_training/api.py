"""Local profiles, generation streams, atomic approval and immutable owned readback."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi import Path as PathParameter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from future_training.agent.budget import Clock, SystemClock
from future_training.agent.orchestration import Agent
from future_training.agent.protocol import ModelProvider
from future_training.approval import Approvals
from future_training.candidates import CandidateStore
from future_training.completion_contracts import (
    COMPLETION_ERRORS,
    SessionRecord,
    SessionSubmission,
    SubmissionError,
)
from future_training.config import Settings
from future_training.domain.catalog import load_catalog
from future_training.errors import ServiceError
from future_training.identity import LocalBoundary, Principal, current_principal
from future_training.observability import LocalTracer, TraceBoundary, annotate
from future_training.persistence.approvals import PostgresApprovals
from future_training.persistence.completions import PostgresCompletions
from future_training.persistence.plans import OwnedPlanReader
from future_training.persistence.profiles import PostgresProfiles, ProfileAccess
from future_training.readiness import DatabaseCheck, ReadinessStatus, check_ready
from future_training.schemas import (
    ApiError,
    ApprovalRequest,
    ApprovalResult,
    CatalogRecord,
    Equipment,
    Experience,
    GenerateRequest,
    Goal,
    Identifier,
    ProfileSaveRequest,
    ReviseRequest,
    SavedPlan,
    SavedProfile,
)
from future_training.streaming import GenerationStream


def create_app(
    *,
    settings: Settings | None = None,
    profiles: ProfileAccess | None = None,
    provider: ModelProvider | None = None,
    clock: Clock | None = None,
    approvals: PostgresApprovals | None = None,
    completions: PostgresCompletions | None = None,
    tracer: LocalTracer | None = None,
    database_check=None,
    web_dist: Path | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    catalog = load_catalog()
    web_dist = (
        web_dist if web_dist is not None else Path(__file__).resolve().parents[2] / "web" / "dist"
    )
    repository = profiles if profiles is not None else PostgresProfiles(catalog)
    clock = clock if clock is not None else SystemClock()
    app = FastAPI(
        title="Future Training local workspace", version="0.1.0", docs_url=None, redoc_url=None
    )
    app.add_middleware(LocalBoundary, settings=settings, now=clock.now)
    app.state.tracer = tracer if tracer is not None else LocalTracer()
    app.add_middleware(TraceBoundary, tracer=app.state.tracer)
    app.state.profiles = repository
    app.state.candidates = CandidateStore(repository, catalog, clock=clock.now)
    app.state.agent = Agent(
        repository, catalog, candidates=app.state.candidates, provider=provider, clock=clock
    )
    database = approvals if approvals is not None else PostgresApprovals(catalog)
    app.state.approval_database = database
    app.state.approvals = Approvals(app.state.candidates, database)
    app.state.plans = OwnedPlanReader(database)
    app.state.completions = completions if completions is not None else PostgresCompletions()

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, error: ServiceError):
        annotate(outcome="error", reason=error.code)
        model = SubmissionError if error.code in COMPLETION_ERRORS else ApiError
        return JSONResponse(
            model(code=error.code, retryable=error.retryable).model_dump(),
            status_code=error.status,
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        annotate(outcome="error", reason="invalid_request")
        return JSONResponse({"code": "invalid_request", "retryable": False}, status_code=422)

    PrincipalDependency = Annotated[Principal, Depends(current_principal)]
    errors = {status: {"model": ApiError} for status in (401, 403, 404, 409, 413, 422, 503)}

    @app.get("/api/v1/profile", response_model=SavedProfile, responses=errors)
    async def get_profile(request: Request, principal: PrincipalDependency):
        if request.query_params:
            raise ServiceError(422, "invalid_request")
        return await repository.get(principal)

    @app.put("/api/v1/profile", response_model=SavedProfile, responses=errors)
    async def save_profile(
        request: Request, body: ProfileSaveRequest, principal: PrincipalDependency
    ):
        if request.query_params:
            raise ServiceError(422, "invalid_request")
        return await repository.save(principal, body)

    @app.get("/api/v1/exercises", response_model=list[CatalogRecord], responses=errors)
    async def exercises(
        request: Request,
        principal: PrincipalDependency,
        limit: Annotated[int, Query(ge=1, le=20)] = 20,
        cursor: Identifier | None = None,
        goal: Goal | None = None,
        equipment: Equipment | None = None,
        experience: Experience | None = None,
    ):
        if set(request.query_params) - {"limit", "cursor", "goal", "equipment", "experience"}:
            raise ServiceError(422, "invalid_request")
        if cursor is not None and cursor not in catalog.ids:
            raise ServiceError(422, "invalid_request")
        return [
            record
            for record in catalog.records()
            if (cursor is None or record.exercise_id > cursor)
            and (goal is None or goal in record.goals)
            and (equipment != "bodyweight" or record.equipment == "bodyweight")
            and (experience is None or experience in record.experiences)
        ][:limit]

    stream_errors = {
        status: {"model": ApiError} for status in (401, 403, 404, 409, 410, 413, 422, 429, 503)
    }
    stream_success = {
        200: {
            "description": "Version 1 SSE; no replay or automatic reconnect",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        }
    }

    @app.post(
        "/api/v1/drafts/stream",
        status_code=200,
        response_class=GenerationStream,
        responses={**stream_errors, **stream_success},
    )
    async def generate(request: Request, body: GenerateRequest, principal: PrincipalDependency):
        if request.query_params or "last-event-id" in request.headers:
            raise ServiceError(422, "invalid_request")
        return GenerationStream(
            app.state.agent, principal, body, started_at=request.state.generation_started_at
        )

    @app.post(
        "/api/v1/drafts/{candidate_id}/revise/stream",
        status_code=200,
        response_class=GenerationStream,
        responses={**stream_errors, **stream_success},
    )
    async def revise(
        request: Request,
        candidate_id: Identifier,
        body: ReviseRequest,
        principal: PrincipalDependency,
    ):
        if (
            request.query_params
            or "last-event-id" in request.headers
            or candidate_id != body.candidate.candidate_id
        ):
            raise ServiceError(422, "invalid_request")
        return GenerationStream(
            app.state.agent,
            principal,
            GenerateRequest(
                profile_revision=body.profile_revision, preferences_text=body.preferences_text
            ),
            revise=body.candidate,
            started_at=request.state.generation_started_at,
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "alive", "stage": "F1-07"}

    approval_errors = {
        status: {"model": ApiError} for status in (401, 403, 404, 409, 410, 413, 422, 503)
    }

    @app.post(
        "/api/v1/drafts/{candidate_id}/approve",
        response_model=ApprovalResult,
        responses=approval_errors,
    )
    async def approve(
        request: Request,
        candidate_id: Identifier,
        body: ApprovalRequest,
        principal: PrincipalDependency,
    ):
        if request.query_params or candidate_id != body.candidate_id:
            raise ServiceError(422, "invalid_request")
        return await app.state.approvals.approve(principal, body)

    @app.get("/api/v1/plans/{plan_id}", response_model=SavedPlan, responses=approval_errors)
    async def read_plan(request: Request, plan_id: Identifier, principal: PrincipalDependency):
        if request.query_params:
            raise ServiceError(422, "invalid_request")
        return await app.state.plans.get(principal, plan_id)

    @app.get("/api/v1/plans", response_model=list[SavedPlan], responses=approval_errors)
    async def history(
        request: Request,
        principal: PrincipalDependency,
        limit: Annotated[int, Query(ge=1, le=20)] = 20,
        cursor: Identifier | None = None,
    ):
        if set(request.query_params) - {"limit", "cursor"}:
            raise ServiceError(422, "invalid_request")
        return await app.state.plans.history(principal, limit=limit, cursor=cursor)

    session_errors = {
        status: {"model": SubmissionError} for status in (401, 403, 404, 409, 413, 422, 503)
    }

    @app.post(
        "/api/v1/plans/{plan_id}/sessions/{day_index}/completion",
        response_model=SessionRecord,
        responses=session_errors,
    )
    async def submit_session(
        request: Request,
        plan_id: Identifier,
        day_index: Annotated[int, PathParameter(ge=1, le=4)],
        body: SessionSubmission,
        principal: PrincipalDependency,
    ):
        if request.query_params:
            raise ServiceError(422, "invalid_request")
        return await app.state.completions.submit(principal, plan_id, day_index, body)

    @app.get(
        "/api/v1/plans/{plan_id}/sessions/{day_index}/completion",
        response_model=SessionRecord,
        responses=session_errors,
    )
    async def read_session(
        request: Request,
        plan_id: Identifier,
        day_index: Annotated[int, PathParameter(ge=1, le=4)],
        principal: PrincipalDependency,
    ):
        if request.query_params:
            raise ServiceError(422, "invalid_request")
        return await app.state.completions.read(principal, plan_id, day_index)

    @app.get(
        "/api/v1/plans/{plan_id}/completions",
        response_model=list[SessionRecord],
        responses=session_errors,
    )
    async def read_sessions(request: Request, plan_id: Identifier, principal: PrincipalDependency):
        if request.query_params:
            raise ServiceError(422, "invalid_request")
        return await app.state.completions.read(principal, plan_id)

    @app.get("/ready", response_model=ReadinessStatus, responses={503: {"model": ReadinessStatus}})
    async def ready() -> JSONResponse:
        status = await check_ready(settings, catalog, database_check or DatabaseCheck(), web_dist)
        return JSONResponse(
            status_code=200 if status.status == "ready_local" else 503, content=status.model_dump()
        )

    @app.get("/", include_in_schema=False)
    async def web_index():
        if not (web_dist / "index.html").is_file():
            return JSONResponse({"code": "internal_error", "retryable": False}, 503)
        return FileResponse(web_dist / "index.html", headers={"Cache-Control": "no-store"})

    app.mount("/assets", StaticFiles(directory=web_dist / "assets", check_dir=False), name="assets")
    return app
