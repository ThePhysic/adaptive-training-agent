"""Ephemeral self-signed test material, generated locally; never provider keys."""

import asyncio
import shutil
import ssl
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path


def certificates(directory):
    openssl = shutil.which("openssl")
    if openssl is None:
        candidate = Path("C:/Program Files/Git/usr/bin/openssl.exe")
        if candidate.is_file():
            openssl = str(candidate)
    if openssl is None:
        raise RuntimeError("Local TLS checks require installed OpenSSL")
    result = {}
    for name, san in (("valid", "IP:127.0.0.1"), ("wrong", "DNS:localhost")):
        key, cert = directory / f"{name}.key", directory / f"{name}.pem"
        subprocess.run(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-days",
                "1",
                "-subj",
                "/CN=synthetic-local-test",
                "-addext",
                f"subjectAltName={san}",
            ],
            capture_output=True,
            check=True,
            timeout=15,
        )
        result[name] = (cert, key)
    cert, key = result["valid"]
    expired = directory / "expired.pem"
    subprocess.run(
        [
            openssl,
            "x509",
            "-in",
            str(cert),
            "-signkey",
            str(key),
            "-days",
            "-1",
            "-out",
            str(expired),
        ],
        capture_output=True,
        check=True,
        timeout=15,
    )
    result["expired"] = (expired, key)
    return result


@asynccontextmanager
async def server(material, *, mode="ok", body=b"{}", headers=None, on_request=None):
    cert, key = material
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    entered, closed = asyncio.Event(), asyncio.Event()
    requests = []
    tasks = set()

    async def handle(reader, writer):
        task = asyncio.current_task()
        tasks.add(task)
        try:
            head = await reader.readuntil(b"\r\n\r\n")
            length = int(
                next(
                    (
                        v.split(b":", 1)[1]
                        for v in head.split(b"\r\n")
                        if v.lower().startswith(b"content-length:")
                    ),
                    b"0",
                )
            )
            received = await reader.readexactly(length)
            if on_request is not None:
                await on_request(head, received)
            requests.append(head.split(b"\r\n")[0])
            entered.set()
            request_mode = mode(requests[-1]) if callable(mode) else mode
            if request_mode == "stall":
                await reader.read()
            elif request_mode == "interrupt":
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                    b"Content-Length: 10\r\n\r\n{"
                )
                await writer.drain()
            else:
                extra = headers or {}
                payload = body(head.split(b"\r\n")[0]) if callable(body) else body
                if isinstance(payload, tuple):
                    payload, mime = payload
                    extra = {**extra, "Content-Type": mime}
                status = "307 Temporary Redirect" if request_mode == "redirect" else "200 OK"
                lines = {
                    "Content-Type": "application/json",
                    "Content-Length": str(len(payload)),
                    "Connection": "close",
                    **extra,
                }
                writer.write(
                    (
                        f"HTTP/1.1 {status}\r\n"
                        + "".join(f"{k}: {v}\r\n" for k, v in lines.items())
                        + "\r\n"
                    ).encode()
                    + payload
                )
                await writer.drain()
        except (
            ConnectionError,
            asyncio.IncompleteReadError,
        ):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (
                ConnectionError,
                ssl.SSLError,
            ):
                pass
            closed.set()
            tasks.discard(task)

    listener = await asyncio.start_server(handle, "127.0.0.1", 0, ssl=context)
    try:
        yield listener.sockets[0].getsockname()[1], entered, closed, requests
    finally:
        listener.close()
        await listener.wait_closed()
        for task in tuple(tasks):
            task.cancel()
        if tasks:
            await asyncio.gather(*tuple(tasks), return_exceptions=True)


def trusted(cert):
    return ssl.create_default_context(cafile=str(cert))
