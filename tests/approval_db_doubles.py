"""Real PostgreSQL connections with explicit fault/barrier injection, not fake SQL."""

import asyncio

import psycopg


class Controls:
    def __init__(self, dsn):
        self.dsn = dsn
        self.mode = "normal"
        self.point = None
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.reconcile_unavailable = False
        self.retained = []
        self.commit_calls = 0
        self.before_execute = None
        self.after_execute = None
        self.pids = []

    async def connect(self):
        connection = await psycopg.AsyncConnection.connect(self.dsn)
        self.pids.append(connection.info.backend_pid)
        return Proxy(connection, self)

    async def settle_retained(self, *, commit):
        for connection in self.retained:
            if commit:
                await connection.commit()
            else:
                await connection.rollback()
            await connection.close()
        self.retained.clear()


class Proxy:
    def __init__(self, connection, controls):
        self.connection, self.controls = connection, controls
        self.retain = False

    @property
    def autocommit(self):
        return self.connection.autocommit

    async def __aenter__(self):
        await self.connection.__aenter__()
        return self

    async def __aexit__(self, *args):
        return await self.connection.__aexit__(*args)

    async def execute(self, query, params=None):
        ctl = self.controls
        if ctl.reconcile_unavailable and "pg_try_advisory_xact_lock" in query:
            raise psycopg.OperationalError("Synthetic reconciliation outage")
        if ctl.before_execute:
            await ctl.before_execute(query, self.connection)
        if ctl.mode == "fail_audit" and "INSERT INTO approval_audit" in query:
            raise psycopg.OperationalError("Synthetic write failure before COMMIT")
        result = await self.connection.execute(query, params)
        if ctl.after_execute:
            await ctl.after_execute(query, self.connection)
        return result

    async def commit(self):
        ctl = self.controls
        ctl.commit_calls += 1
        ctl.commit_pid = self.connection.info.backend_pid
        if ctl.point == "during":
            ctl.entered.set()
        if ctl.point == "before":
            ctl.entered.set()
            await ctl.release.wait()
        if ctl.mode == "open_uncertain":
            # Real uncommitted rows and a real advisory lock remain. The test
            # later finishes the original transaction, representing an in-flight
            # COMMIT whose outcome the adapter cannot yet establish.
            self.retain = True
            ctl.retained.append(self.connection)
            raise psycopg.OperationalError("Synthetic unknown in-flight COMMIT")
        if ctl.mode == "rollback_uncertain":
            await self.connection.rollback()
            raise psycopg.OperationalError("Synthetic lost rollback acknowledgement")
        await self.connection.commit()
        if ctl.point == "after":
            ctl.entered.set()
            await ctl.release.wait()
        if ctl.mode == "lost_after":
            raise psycopg.OperationalError("Synthetic lost COMMIT response")
        if ctl.mode == "cancel_after":
            raise asyncio.CancelledError

    async def close(self):
        if not self.retain:
            await self.connection.close()
