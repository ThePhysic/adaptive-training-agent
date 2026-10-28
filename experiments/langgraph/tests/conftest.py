import asyncio
import socket

import pytest


def pytest_asyncio_loop_factories():
    return {"selector": asyncio.SelectorEventLoop}


@pytest.fixture(autouse=True)
def deny_dns(monkeypatch):
    original = socket.getaddrinfo

    def local(host, *args, **kwargs):
        if host not in (None, "localhost", "127.0.0.1", "::1"):
            raise OSError("External DNS disabled")
        return original(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", local)
