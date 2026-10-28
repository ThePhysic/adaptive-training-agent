"""Direct POST SSE: one streaming task owns generation through terminal publication.

There is no replay queue or worker. The only child task watches disconnects; all
Agent/session/progress/publication/send operations run on the ASGI owning task.
"""

import asyncio
from contextlib import asynccontextmanager, nullcontext, suppress

from pydantic import TypeAdapter
from starlette.responses import JSONResponse, Response

from future_training.agent.budget import AgentFault
from future_training.agent.orchestration import Agent, State
from future_training.agent.protocol import ModelPlan
from future_training.errors import ServiceError
from future_training.identity import Principal
from future_training.observability import correlation_id, span, terminal_outcome
from future_training.schemas import (
    ApiError,
    CandidateIdentity,
    ErrorOutcome,
    GenerateRequest,
    PlanOutcome,
    StreamEvent,
)

MAX_FRAME_BYTES = 16384
MAX_EVENTS = 64
_EVENT = TypeAdapter(StreamEvent)


class Frames:
    """Strict server ordering and bounded encoding; never send arbitrary provider prose."""

    def __init__(self, send):
        self.send = send
        self.request_id = correlation_id()
        self.sequence = 0
        self.draft = False
        self.error = None
        self.done = False

    def encode(self, event_type, payload) -> bytes:
        if self.done or self.sequence >= MAX_EVENTS:
            raise RuntimeError("Stream already terminal or too many events")
        if event_type == "draft" and (self.draft or self.error):
            raise RuntimeError("Duplicate or invalid draft")
        if event_type == "error" and self.error is not None:
            raise RuntimeError("Duplicate error")
        if event_type == "status" and (self.draft or self.error):
            raise RuntimeError("Status after preview/error")
        if event_type == "done":
            outcome = payload["outcome"]
            if outcome == "plan" and (not self.draft or self.error):
                raise RuntimeError("Plan requires a clean validated preview")
            if outcome in ("clarify", "abstain") and (self.draft or self.error):
                raise RuntimeError("Nonplan outcome after preview/error")
            if outcome == "error" and payload["error"] != self.error:
                raise RuntimeError("Error outcome needs the same prior error")
        event = _EVENT.validate_python(
            dict(
                schema_version="1",
                request_id=self.request_id,
                sequence=self.sequence,
                event_type=event_type,
                payload=payload,
            )
        )
        frame = f"event: {event_type}\ndata: {event.model_dump_json()}\n\n".encode()
        if len(frame) > MAX_FRAME_BYTES:
            raise ServiceError(503, "internal_error")
        return frame

    async def emit(self, event_type, payload):
        frame = self.encode(event_type, payload)
        self.sequence += 1
        if event_type == "draft":
            self.draft = True
        elif event_type == "error":
            self.error = payload
        elif event_type == "done":
            self.done = True
        terminal = (
            span("stream.terminal", outcome=payload["outcome"])
            if event_type == "done"
            else nullcontext()
        )
        with terminal:
            await self.send({"type": "http.response.body", "body": frame, "more_body": True})
            if event_type == "done":
                terminal_outcome(payload["outcome"])

    async def fail(self, error: ApiError):
        if self.done:
            return
        if self.error is None:
            await self.emit("error", error.model_dump())
        else:
            error = ApiError.model_validate(self.error)
        await self.emit("done", ErrorOutcome(outcome="error", error=error).model_dump())


class GenerationStream(Response):
    media_type = "text/event-stream"

    def __init__(
        self,
        agent: Agent,
        principal: Principal,
        request: GenerateRequest,
        *,
        revise: CandidateIdentity | None = None,
        started_at: float | None = None,
    ):
        super().__init__(
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
            media_type=self.media_type,
        )
        # No Content-Length for an open direct stream.
        self.raw_headers = [(k, v) for k, v in self.raw_headers if k != b"content-length"]
        self.agent, self.principal, self.request, self.revise = agent, principal, request, revise
        self.started_at = started_at

    async def __call__(self, scope, receive, send):
        owner = asyncio.current_task()
        disconnected = False
        started = False
        json_error_started = False
        frames = Frames(send)
        deadline = None

        async def watch_disconnect():
            nonlocal disconnected
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    disconnected = True
                    owner.cancel()
                    return

        async def progress(state):
            stages = {
                State.CONTEXT: "context",
                State.MODEL: "drafting",
                State.VALIDATING: "validating",
                State.REPAIRING: "repairing",
            }
            if state in stages:
                await frames.emit("status", {"stage": stages[state]})

        def check_publication():
            if disconnected:
                raise asyncio.CancelledError
            deadline.check()

        async def failure(error: ApiError, status: int, *, guarded=False):
            nonlocal json_error_started
            if disconnected or frames.done or json_error_started:
                return

            async def write():
                nonlocal json_error_started
                if not started:
                    json_error_started = True
                    await JSONResponse(error.model_dump(), status_code=status)(scope, receive, send)
                else:
                    await frames.fail(error)
                    await send({"type": "http.response.body", "body": b"", "more_body": False})

            # Retain the original expiry, including fake-clock supervision. Once
            # expired, only immediately writable error frames are attempted.
            with suppress(TimeoutError, OSError):
                if guarded:
                    await write()
                elif deadline is not None and self.agent.clock.now() < deadline.expires:
                    async with deadline.scope():
                        await write()
                else:
                    async with asyncio.timeout(0):
                        await write()

        @asynccontextmanager
        async def failure_boundary():
            # This exits BEFORE Agent.session: admission/reservation and the
            # original watchdog still cover error+done(error) backpressure.
            nonlocal disconnected
            try:
                yield
            except ServiceError as exc:
                await failure(
                    ApiError(code=exc.code, retryable=exc.retryable), exc.status, guarded=True
                )
            except AgentFault as exc:
                await failure(
                    ApiError(code=exc.code, retryable=exc.retryable),
                    429 if exc.code == "capacity_exceeded" else 503,
                    guarded=True,
                )
            except OSError:
                disconnected = True
            except Exception:
                await failure(ApiError(code="internal_error"), 503, guarded=True)

        watcher = asyncio.create_task(watch_disconnect())
        try:
            try:
                async with (
                    self.agent.session(
                        self.principal,
                        self.request,
                        revise=self.revise,
                        progress=progress,
                        started_at=self.started_at,
                    ) as run,
                    failure_boundary(),
                ):
                    deadline = run.deadline
                    # Ordinary bounded pre-header validation under the SAME deadline.
                    profile = await self.agent.profiles.get(self.principal)
                    if profile.revision != self.request.profile_revision:
                        raise ServiceError(409, "stale_profile")
                    if self.revise is not None:
                        snapshot = await self.agent.candidates.get(
                            self.principal, self.revise.candidate_id
                        )
                        if snapshot.identity() != self.revise:
                            raise ServiceError(409, "candidate_mismatch")
                    check_publication()
                    started = True
                    await send(
                        {"type": "http.response.start", "status": 200, "headers": self.raw_headers}
                    )
                    result = await run.execute()
                    output = result.output()
                    if isinstance(output, ModelPlan):
                        await frames.emit("draft", output.plan.model_dump())
                        # Give a queued disconnect/cancellation a checkpoint before
                        # entering the terminalization boundary. Never replay work.
                        await asyncio.sleep(0)
                        check_publication()
                        # Prove done framing fits BEFORE mutation. Actual opaque IDs
                        # are <=64 chars; revision <=2 and hash always 64 hex chars.
                        frames.encode(
                            "done",
                            PlanOutcome(
                                outcome="plan",
                                candidate=CandidateIdentity(
                                    candidate_id="x" * 64, revision=2, content_hash="0" * 64
                                ),
                            ).model_dump(),
                        )
                        if self.revise is None:
                            snapshot = await self.agent.candidates.publish_initial(
                                self.principal,
                                output.plan,
                                expected_profile_revision=result.profile_revision,
                                before_publish=check_publication,
                            )
                        else:
                            snapshot = await self.agent.candidates.publish_revision(
                                self.principal,
                                run.reservation,
                                output.plan,
                                before_publish=check_publication,
                            )
                        # No await between publication and handing done(plan) to ASGI.
                        # Transport loss here can leave the explicitly allowed orphan.
                        await frames.emit(
                            "done",
                            PlanOutcome(outcome="plan", candidate=snapshot.identity()).model_dump(),
                        )
                    elif isinstance(output, ErrorOutcome):
                        await frames.fail(output.error)
                    else:
                        await frames.emit("done", output.model_dump())
                    await send({"type": "http.response.body", "body": b"", "more_body": False})
            except ServiceError as exc:
                await failure(ApiError(code=exc.code, retryable=exc.retryable), exc.status)
            except AgentFault as exc:
                await failure(
                    ApiError(code=exc.code, retryable=exc.retryable),
                    429 if exc.code == "capacity_exceeded" else 503,
                )
            except TimeoutError:
                # At expiry only immediately writable failure frames are attempted.
                # Backpressure yields and is cancelled immediately: no deadline grace.
                await failure(ApiError(code="budget_exceeded"), 503)
            except (
                OSError,
                ConnectionError,
            ):
                disconnected = True
            except Exception:
                # Sanitized, best-effort error frames; no raw exceptions in output.
                await failure(ApiError(code="internal_error"), 503)
        except asyncio.CancelledError:
            if not disconnected:
                raise
        finally:
            watcher.cancel()
            # Own and drain the watcher without swallowing a new external cancel.
            cancellations = owner.cancelling()
            cancelled = False
            while not watcher.done():
                try:
                    await asyncio.shield(watcher)
                except asyncio.CancelledError:
                    cancelled |= owner.cancelling() > cancellations
            if not watcher.cancelled():
                watcher.result()
            if cancelled:
                raise asyncio.CancelledError
