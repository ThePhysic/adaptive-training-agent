"""Cooperative streamed HTTPX fakes; no sockets, hidden retries or timing sleeps."""

import asyncio
import json

import httpx

from future_training.domain.catalog import load_catalog
from future_training.schemas import SavedProfile


class ControlledReads:
    def __init__(self, profile):
        self.payloads = {
            "profile": SavedProfile(revision=1, preferences=profile).model_dump(),
            "catalog": [record.model_dump() for record in load_catalog().records()],
            "history": [],
        }
        self.started = {name: asyncio.Event() for name in self.payloads}
        self.closed = {name: asyncio.Event() for name in self.payloads}
        self.header_gates = {}
        self.body_gates = {}
        self.close_gates = {}
        self.faults = {}
        self.body_faults = {}
        self.statuses = {}
        self.headers = {}
        self.raw = {}
        self.requests = []
        self.tasks = []
        self.active = self.maximum = 0
        self.all_started = asyncio.Event()
        self.closing = asyncio.Event()

    def done(self, name):
        if not self.closed[name].is_set():
            self.active -= 1
            self.closed[name].set()

    async def handle(self, request):
        name = {
            "/api/v1/profile": "profile",
            "/api/v1/exercises": "catalog",
            "/api/v1/plans": "history",
        }[request.url.path]
        assert request.method == "GET"
        assert request.headers["X-Synthetic-Principal"] in ("synthetic-a", "synthetic-b")
        self.requests.append(name)
        self.tasks.append(asyncio.current_task())
        self.active += 1
        self.maximum = max(self.maximum, self.active)
        self.started[name].set()
        if len(self.requests) == 3:
            self.all_started.set()
        try:
            if name in self.header_gates:
                await self.header_gates[name].wait()
            if name in self.faults:
                raise self.faults[name]
            return httpx.Response(
                self.statuses.get(name, 200),
                stream=Body(self, name),
                headers={"content-type": "application/json", **self.headers.get(name, {})},
            )
        except BaseException:
            self.done(name)
            raise

    def transport(self):
        return httpx.MockTransport(self.handle)


class Body(httpx.AsyncByteStream):
    def __init__(self, parent, name):
        self.parent, self.name = parent, name

    async def __aiter__(self):
        parent, name = self.parent, self.name
        if name in parent.body_gates:
            await parent.body_gates[name].wait()
        data = parent.raw.get(name, json.dumps(parent.payloads[name]).encode())
        yield data[:1]
        if name in parent.body_faults:
            raise parent.body_faults[name]
        yield data[1:]

    async def aclose(self):
        self.parent.closing.set()
        try:
            if self.name in self.parent.close_gates:
                await self.parent.close_gates[self.name].wait()
        finally:
            self.parent.done(self.name)
