"""Routine tests permit loopback control sockets, never external sockets or DNS."""

import asyncio
import socket
from ipaddress import ip_address

import pytest


def pytest_asyncio_loop_factories():
    # Public pytest-asyncio hook; Psycopg async needs this on Windows too.
    return {"selector": asyncio.SelectorEventLoop}


@pytest.fixture(autouse=True)
def no_external_dns(monkeypatch):
    original = socket.getaddrinfo

    def local_only(host, *args, **kwargs):
        if host not in (None, "localhost", "127.0.0.1", "::1", b"127.0.0.1", b"::1"):
            raise OSError("External DNS disabled in tests")
        return original(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", local_only)
    allowed = {"localhost", "127.0.0.1", "::1", b"127.0.0.1", b"::1"}
    for name in ("gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        original_lookup = getattr(socket, name)

        def lookup(host, *args, _lookup=original_lookup, **kwargs):
            if host not in allowed:
                raise OSError("External DNS disabled in tests")
            return _lookup(host, *args, **kwargs)

        monkeypatch.setattr(socket, name, lookup)

    def check_address(address):
        if isinstance(address, tuple):
            try:
                if ip_address(address[0]).is_loopback:
                    return
            except ValueError:
                pass
        raise OSError("External socket I/O disabled in tests")

    original_nameinfo = socket.getnameinfo

    def nameinfo(address, flags):
        check_address(address)
        return original_nameinfo(address, flags)

    monkeypatch.setattr(socket, "getnameinfo", nameinfo)

    for name in ("connect_ex", "sendto"):
        original_io = getattr(socket.socket, name)

        def bounded_io(instance, *args, _io=original_io):
            check_address(args[-1])
            return _io(instance, *args)

        monkeypatch.setattr(socket.socket, name, bounded_io)


@pytest.fixture
def profile():
    return {
        "adult": True,
        "goal": "general_strength",
        "equipment": "bodyweight",
        "experience": "beginner",
        "days_per_week": 2,
        "session_minutes": 20,
    }


@pytest.fixture
def proposal(profile):
    return {
        "profile": profile,
        "days": [
            {
                "day_index": index,
                "planned_seconds": 1227,
                "blocks": [
                    {
                        "exercise_id": f"exercise-{number}",
                        "mode": "repetitions",
                        "sets": 3,
                        "repetitions_per_set": 9,
                        "rest_between_sets_seconds": 45,
                    }
                    for number in range(4)
                ],
            }
            for index in (1, 2)
        ],
    }
