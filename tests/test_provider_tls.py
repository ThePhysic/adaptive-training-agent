"""Real loopback TCP/TLS evidence; logical provider addresses are never dialled."""

import asyncio
import gzip
import ssl

import pytest
from local_tls_doubles import certificates, server, trusted

from future_training.agent.budget import AgentFault
from future_training.providers.gates import ENDPOINT
from future_training.providers.http import LocalTLS, OfflineHTTP


@pytest.fixture(scope="module")
def certs(tmp_path_factory):
    return certificates(tmp_path_factory.mktemp("synthetic-tls"))


@pytest.mark.parametrize("kind", ["valid", "wrong", "expired", "untrusted"])
async def test_actual_certificate_and_hostname_verification(certs, kind):
    material = certs["valid" if kind == "untrusted" else kind]
    context = ssl.create_default_context() if kind == "untrusted" else trusted(material[0])
    async with server(material) as (port, entered, closed, requests):
        wire = OfflineHTTP(LocalTLS(port, context))
        try:

            async def read():
                async with wire.stream(
                    ENDPOINT, b"{}", accept="application/json", maximum=100
                ) as r:
                    return await r.aread()

            if kind == "valid":
                assert await read() == b"{}"
                assert requests == [b"POST /v1/responses HTTP/1.1"]
            else:
                with pytest.raises(AgentFault, match="provider_transport_failure"):
                    await read()
                assert requests == []
        finally:
            await wire.aclose()


@pytest.mark.parametrize("mode", ["redirect", "interrupt", "gzip", "oversize"])
async def test_actual_socket_failures_and_bounded_bodies(certs, mode):
    body = (
        b"x" * 101
        if mode == "oversize"
        else gzip.compress(b"x" * 100000)
        if mode == "gzip"
        else b"{}"
    )
    headers = (
        {"Content-Encoding": "gzip"}
        if mode == "gzip"
        else {"Location": "https://evil.invalid"}
        if mode == "redirect"
        else None
    )
    async with server(certs["valid"], mode=mode, body=body, headers=headers) as (
        port,
        entered,
        closed,
        requests,
    ):
        wire = OfflineHTTP(LocalTLS(port, trusted(certs["valid"][0])))
        try:
            with pytest.raises(AgentFault):
                async with wire.stream(
                    ENDPOINT, b"{}", accept="application/json", maximum=100
                ) as r:
                    await r.aread()
            assert len(requests) == 1
        finally:
            await wire.aclose()


async def test_actual_stalled_socket_cancellation_is_awaited(certs):
    async with server(certs["valid"], mode="stall") as (port, entered, closed, requests):
        wire = OfflineHTTP(LocalTLS(port, trusted(certs["valid"][0])))

        async def read():
            try:
                async with wire.stream(
                    ENDPOINT, b"{}", accept="application/json", maximum=100
                ) as r:
                    await r.aread()
            finally:
                await wire.aclose()

        task = asyncio.create_task(read())
        await entered.wait()
        task.cancel()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await closed.wait()
        assert len(requests) == 1 and wire.closed


async def test_socket_ignores_proxy_and_ca_environment(certs, monkeypatch):
    context = trusted(certs["valid"][0])
    for name in ("HTTPS_PROXY", "ALL_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR"):
        monkeypatch.setenv(name, "synthetic-invalid-private-value")
    async with server(certs["valid"]) as (port, entered, closed, requests):
        wire = OfflineHTTP(LocalTLS(port, context))
        try:
            async with wire.stream(ENDPOINT, b"{}", accept="application/json", maximum=100) as r:
                assert await r.aread() == b"{}"
            assert len(requests) == 1
        finally:
            await wire.aclose()


def test_insecure_tls_configuration_cannot_construct_connector():
    context = ssl._create_unverified_context()
    with pytest.raises(ValueError):
        LocalTLS(443, context)


async def test_mutating_tls_context_cannot_disable_verification(certs):
    context = trusted(certs["valid"][0])
    connector = LocalTLS(443, context)
    context.check_hostname = False
    wire = OfflineHTTP(connector)
    try:
        with pytest.raises(AgentFault, match="provider_tls_verification_required"):
            async with wire.stream(ENDPOINT, b"{}", accept="application/json", maximum=100):
                pass
    finally:
        await wire.aclose()
