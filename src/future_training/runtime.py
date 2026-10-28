"""Psycopg async requires a selector loop on Windows; no policy/global mutation."""

import asyncio


def loop_factory():
    return asyncio.SelectorEventLoop()
