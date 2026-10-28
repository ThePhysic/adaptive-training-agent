"""Actual ASGI chunk/disconnect harness; no buffered HTTPX stream timing claims."""

import asyncio
import json

from agent_doubles import ManualClock
from profile_doubles import MemoryProfiles

from future_training.api import create_app
from future_training.config import Settings
from future_training.identity import Principal
from future_training.schemas import ProfileSaveRequest


async def stream_app(profile, *, provider=None, clock=None):
    profiles = MemoryProfiles()
    for principal in Principal:
        await profiles.save(principal, ProfileSaveRequest(expected_revision=0, preferences=profile))
    return create_app(
        settings=Settings(local_development="1"),
        profiles=profiles,
        provider=provider,
        clock=clock or ManualClock(),
    )


class Exchange:
    def __init__(
        self,
        app,
        *,
        path="/api/v1/drafts/stream",
        body=None,
        principal="synthetic-a",
        hook=None,
        spec="2.4",
        extra_headers=(),
        query=b"",
    ):
        self.app, self.hook = app, hook
        self.scope = dict(
            type="http",
            asgi={"version": "3.0", "spec_version": spec},
            http_version="1.1",
            method="POST",
            scheme="http",
            path=path,
            raw_path=path.encode(),
            query_string=query,
            root_path="",
            client=("127.0.0.1", 12345),
            server=("127.0.0.1", 8000),
            headers=[
                (b"host", b"127.0.0.1:8000"),
                (b"x-synthetic-principal", principal.encode()),
                (b"content-type", b"application/json"),
                *extra_headers,
            ],
        )
        self.incoming = asyncio.Queue()
        self.incoming.put_nowait(
            {
                "type": "http.request",
                "body": json.dumps(body if body is not None else {"profile_revision": 1}).encode(),
                "more_body": False,
            }
        )
        self.messages = []
        self.events = []
        self.seen = {key: asyncio.Event() for key in ("status", "draft", "error", "done")}

    async def send(self, message):
        event = None
        if message["type"] == "http.response.body" and message.get("body", b"").startswith(
            b"event:"
        ):
            event = json.loads(message["body"].split(b"\ndata: ", 1)[1])
        if self.hook is not None:
            await self.hook(message, event)
        self.messages.append(message)
        if event:
            self.events.append(event)
            self.seen[event["event_type"]].set()

    def start(self):
        self.task = asyncio.create_task(self.app(self.scope, self.incoming.get, self.send))
        return self

    async def finish(self):
        await asyncio.wait_for(self.task, 3)
        return self

    def disconnect(self):
        self.incoming.put_nowait({"type": "http.disconnect"})

    @property
    def status(self):
        return next(m["status"] for m in self.messages if m["type"] == "http.response.start")

    @property
    def body(self):
        return b"".join(m.get("body", b"") for m in self.messages)
