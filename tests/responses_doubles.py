"""Synthetic wire fixtures: no capture, provider key, socket or live quality evidence."""

import copy
import json

import httpx

from future_training.agent.protocol import canonical
from future_training.providers.responses import ASSETS


def fixture(name="plan"):
    return json.loads((ASSETS / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))


def frames(response, *, prefix=None):
    events = prefix or []
    events = copy.deepcopy(events)
    events.extend(
        {"type": "response.output_item.done", "output_index": i, "item": item}
        for i, item in enumerate(response.get("output", []))
    )
    events.append({"type": "response." + response["status"], "response": response})
    return b"".join(
        b"event: "
        + e["type"].encode()
        + b"\ndata: "
        + canonical({**e, "sequence_number": i})
        + b"\n\n"
        for i, e in enumerate(events)
    )


class Chunks(httpx.AsyncByteStream):
    def __init__(self, content, size=29):
        self.content, self.size, self.closed = content, size, False

    async def __aiter__(self):
        for index in range(0, len(self.content), self.size):
            yield self.content[index : index + self.size]

    async def aclose(self):
        self.closed = True


def response(body, *, size=29):
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        stream=Chunks(body, size),
    )


class Script:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.streams = []

    async def __call__(self, request):
        self.requests.append(json.loads(request.content))
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert request.method == "POST" and "authorization" not in request.headers
        assert request.headers["content-type"] == "application/json"
        value = self.responses[len(self.requests) - 1]
        if callable(value):
            value = await value(request)
        if isinstance(value, httpx.Response):
            return value
        result = response(value if isinstance(value, bytes) else frames(value))
        self.streams.append(result.stream)
        return result
