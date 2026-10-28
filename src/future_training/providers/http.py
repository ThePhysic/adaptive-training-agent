"""Owned provider-shaped HTTP, restricted to mocks or literal-loopback TLS only.

Only local connectors are accepted here; sender.py's dormant provider connector
is never accepted. LocalTLS rewrites an allowlisted logical URL to 127.0.0.1 only.
"""

import asyncio
import ssl
from contextlib import asynccontextmanager

import httpx

from future_training.agent.budget import AgentFault

PATHS = (b"/v1/responses", b"/v1/responses/input_tokens")


def verified_transport(context=None):
    """One TLS configuration for dormant provider and loopback connectors."""
    if context is not None and (
        type(context) is not ssl.SSLContext
        or not context.check_hostname
        or context.verify_mode != ssl.CERT_REQUIRED
    ):
        raise AgentFault("provider_tls_verification_required")
    return httpx.AsyncHTTPTransport(
        verify=True if context is None else context, retries=0, trust_env=False
    )


class LimitedStream(httpx.AsyncByteStream):
    def __init__(self, stream, maximum):
        self.stream, self.maximum = stream, maximum

    async def __aiter__(self):
        total = 0
        async for chunk in self.stream:
            total += len(chunk)
            if total > self.maximum:
                raise AgentFault("provider_response_too_large_or_invalid")
            yield chunk

    async def aclose(self):
        await self.stream.aclose()


def destination(method, url):
    value = httpx.URL(url)
    if (
        method != "POST"
        or value.scheme != "https"
        or value.host != "api.openai.com"
        or value.port not in (None, 443)
        or value.raw_path not in PATHS
        or value.query
        or value.fragment
        or value.userinfo
    ):
        raise AgentFault("provider_destination_denied")
    return value


class LocalTLS(httpx.AsyncBaseTransport):
    """Test connector: no hostname/base URL parameter and no external socket path."""

    def __init__(self, port, context):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Invalid local port")
        if (
            type(context) is not ssl.SSLContext
            or not context.check_hostname
            or context.verify_mode != ssl.CERT_REQUIRED
        ):
            raise ValueError("Verified local TLS context required")
        self.port = port
        self._context = context
        self.transport = verified_transport(context)

    async def handle_async_request(self, request):
        if not self._context.check_hostname or self._context.verify_mode != ssl.CERT_REQUIRED:
            raise AgentFault("provider_tls_verification_required")
        logical = destination(request.method, request.url)
        target = httpx.URL(f"https://127.0.0.1:{self.port}").copy_with(raw_path=logical.raw_path)
        local = httpx.Request(
            "POST",
            target,
            headers={
                "content-type": "application/json",
                "accept": request.headers["accept"],
                "host": f"127.0.0.1:{self.port}",
                "content-length": request.headers["content-length"],
            },
            stream=request.stream,
            extensions=request.extensions,
        )
        return await self.transport.handle_async_request(local)

    async def aclose(self):
        await self.transport.aclose()


class OfflineHTTP:
    def __init__(self, transport):
        if type(transport) not in (httpx.MockTransport, LocalTLS):
            raise ValueError("Only local test transports are supported")
        self._transport = transport
        self._client = None
        self.closed = False

    async def client(self):
        if self.closed:
            raise AgentFault("provider_transport_closed")
        if self._client is None:
            self._client = httpx.AsyncClient(
                transport=self._transport,
                trust_env=False,
                follow_redirects=False,
                timeout=30,
                headers={"Content-Type": "application/json", "Accept-Encoding": "identity"},
            )
        return self._client

    @asynccontextmanager
    async def stream(self, url, payload, *, accept, maximum, check=lambda: None):
        url = destination("POST", url)
        ceiling = 1024 if url.raw_path == PATHS[1] else 65536
        if type(maximum) is not int or not 1 <= maximum <= ceiling:
            raise ValueError("Invalid response bound")
        if not isinstance(payload, bytes) or len(payload) > 65536:
            raise AgentFault("provider_input_too_large")
        if accept not in ("application/json", "text/event-stream"):
            raise ValueError("Unsupported response format")
        client = await self.client()
        check()  # Last synchronous check immediately before the transport await.
        try:
            async with client.stream(
                "POST", url, content=payload, headers={"Accept": accept}
            ) as response:
                if response.is_redirect or response.status_code != 200:
                    raise AgentFault("provider_http_failure")
                if response.headers.get("content-type", "").split(";")[0] != accept:
                    raise AgentFault("malformed_provider_response")
                # No compressed body is accepted. This prevents decompression bombs
                # before HTTPX's decoder can allocate a potentially huge output.
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise AgentFault("provider_encoding_denied")
                length = response.headers.get("content-length")
                if length is not None and (
                    len(length) > 20
                    or not length.isascii()
                    or not length.isdigit()
                    or int(length) > maximum
                ):
                    raise AgentFault("provider_response_too_large_or_invalid")
                if response.is_stream_consumed:
                    if len(response.content) > maximum:
                        raise AgentFault("provider_response_too_large_or_invalid")
                else:
                    response.stream = LimitedStream(response.stream, maximum)
                yield response
        except httpx.HTTPError:
            raise AgentFault("provider_transport_failure") from None

    async def aclose(self):
        self.closed = True
        if self._client is not None:
            task = asyncio.create_task(self._client.aclose())
            cancelled = False
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    cancelled = True
            task.result()
            if cancelled:
                raise asyncio.CancelledError
