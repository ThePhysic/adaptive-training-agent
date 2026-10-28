"""Two synthetic local principals. This is not real-user authentication."""

import asyncio
import time
from enum import StrEnum
from ipaddress import ip_address
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import Security
from fastapi.security import APIKeyHeader
from starlette.requests import Request
from starlette.responses import JSONResponse

from future_training.config import Settings
from future_training.errors import ServiceError
from future_training.observability import annotate


class Principal(StrEnum):
    A = "synthetic-a"
    B = "synthetic-b"


def owner_id(principal: Principal) -> str:
    if not isinstance(principal, Principal):
        raise ServiceError(401, "unauthorized")
    return principal.value


def _loopback(address: str) -> bool:
    try:
        return ip_address(address).is_loopback
    except ValueError:
        return False


class LocalBoundary:
    def __init__(self, app, settings: Settings, body_timeout=5, now=time.monotonic):
        self.app = app
        self.settings = settings
        self.body_timeout = body_timeout
        self.now = now

    async def __call__(self, scope, receive, send):
        web = scope.get("path") == "/" or scope.get("path", "").startswith("/assets/")
        if scope["type"] != "http" or not (scope["path"].startswith("/api/") or web):
            return await self.app(scope, receive, send)
        request = Request(scope)
        session_route = scope["path"].startswith("/api/v1/plans/") and scope["path"].endswith(
            ("/completion", "/completions")
        )
        if session_route:
            downstream_send = send

            async def private_send(message):
                if message["type"] == "http.response.start":
                    message = {
                        **message,
                        "headers": [
                            *message.get("headers", []),
                            (b"cache-control", b"no-store"),
                            (b"referrer-policy", b"no-referrer"),
                            (b"x-content-type-options", b"nosniff"),
                        ],
                    }
                await downstream_send(message)

            send = private_send
        denied = self.settings.local_development != "1"
        denied |= not scope.get("client") or not _loopback(scope["client"][0])
        denied |= not scope.get("server") or not _loopback(scope["server"][0])
        host = request.headers.get("host", "")
        try:
            target = urlsplit("http://" + host)
            denied |= (
                target.hostname not in ("127.0.0.1", "localhost") or target.username is not None
            )
            if "origin" in request.headers:
                origin = urlsplit(request.headers["origin"])
                denied |= origin.scheme != "http" or origin.netloc != host
        except ValueError:
            denied = True
        denied |= len(request.headers.getlist("host")) != 1
        denied |= any(
            name.lower().startswith("x-forwarded-") or name.lower() in ("forwarded", "x-real-ip")
            for name in request.headers
        )
        if denied:
            return await JSONResponse({"code": "unauthorized", "retryable": False}, 403)(
                scope, receive, send
            )
        if web:

            async def secured_send(message):
                if message["type"] == "http.response.start":
                    message = {
                        **message,
                        "headers": [
                            *message.get("headers", []),
                            (
                                b"content-security-policy",
                                b"default-src 'none'; script-src 'self'; "
                                b"style-src 'self'; connect-src 'self'; img-src 'self'; "
                                b"base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
                            ),
                            (b"referrer-policy", b"no-referrer"),
                            (b"x-content-type-options", b"nosniff"),
                        ],
                    }
                await send(message)

            return await self.app(scope, receive, secured_send)
        values = request.headers.getlist("x-synthetic-principal")
        try:
            if len(values) != 1:
                raise ValueError
            principal = Principal(values[0])
        except ValueError:
            return await JSONResponse({"code": "unauthorized", "retryable": False}, 401)(
                scope, receive, send
            )
        # Bounded body buffering before JSON parsing; chunked bodies are counted too.
        scope.setdefault("state", {})["generation_started_at"] = self.now()
        data = bytearray()
        completion = request.url.path.startswith("/api/v1/plans/") and request.url.path.endswith(
            "/completion"
        )
        body_limit = 4096 if completion else 16384
        try:
            async with asyncio.timeout(self.body_timeout):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(data) + len(chunk) > body_limit:
                        return await JSONResponse(
                            {"code": "invalid_request", "retryable": False}, 413
                        )(scope, receive, send)
                    data.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            annotate(outcome="error", reason="budget_exceeded")
            return await JSONResponse({"code": "budget_exceeded", "retryable": False}, 503)(
                scope, receive, send
            )
        if completion and data:
            from future_training.agent.protocol import parse_json

            try:
                parse_json(bytes(data))
            except (
                ValueError,
                UnicodeError,
                RecursionError,
            ):
                return await JSONResponse({"code": "invalid_request", "retryable": False}, 422)(
                    scope, receive, send
                )
        scope.setdefault("state", {})["principal"] = principal
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            return await receive()

        return await self.app(scope, bounded_receive, send)


_header = APIKeyHeader(
    name="X-Synthetic-Principal", scheme_name="SyntheticPrincipal", auto_error=False
)


def current_principal(
    request: Request, header: Annotated[str | None, Security(_header)]
) -> Principal:
    principal = getattr(request.state, "principal", None)
    owner_id(principal)
    return principal
