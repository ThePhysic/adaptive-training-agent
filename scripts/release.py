"""Local-only container entrypoint. No generic bind/DSN/command/egress options."""

import hashlib
import http.client
import importlib.metadata
import json
import os
import runpy
import socket
import sys
from ipaddress import ip_address
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def seal():
    original_dns = socket.getaddrinfo
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def allowed(address):
        if not isinstance(address, tuple) or not ip_address(address[0]).is_loopback:
            raise OSError("Release external egress denied")

    def dns(host, *args, **kwargs):
        if host not in (None, "localhost", "127.0.0.1", "::1", b"127.0.0.1", b"::1"):
            raise OSError("Release external DNS denied")
        return original_dns(host, *args, **kwargs)

    def connect(self, address):
        allowed(address)
        return original_connect(self, address)

    def connect_ex(self, address):
        allowed(address)
        return original_connect_ex(self, address)

    socket.getaddrinfo = dns
    socket.socket.connect, socket.socket.connect_ex = connect, connect_ex


def manifest():
    paths = sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "migrations").glob("*.sql"))
    paths += sorted((ROOT / "scripts").glob("*.py"))
    paths += [ROOT / "data/catalog/v1.json", *sorted((ROOT / "web/dist").rglob("*"))]
    hashes = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
        if p.is_file()
    }
    return {
        "version": "local-release-v1",
        "python": sys.version.split()[0],
        "files": hashes,
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    }


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"serve", "ready", "manifest"}:
        raise SystemExit("Unsupported release command")
    if sys.argv[1] == "manifest":
        print(json.dumps(manifest(), sort_keys=True))
        return
    from future_training.config import Settings
    from future_training.observability import configure_logging

    settings = Settings.from_env()
    if (
        os.environ.get("FATA_RELEASE_ACK") != "local-synthetic-only"
        or settings.local_development != "1"
    ):
        raise SystemExit("Explicit local synthetic release acknowledgment required")
    seal()
    configure_logging()
    if sys.argv[1] == "ready":
        c = http.client.HTTPConnection("127.0.0.1", 8000, timeout=3)
        try:
            c.request("GET", "/ready")
            response = c.getresponse()
            raise SystemExit(0 if response.status == 200 else 1)
        finally:
            c.close()
    # Compose orders PostgreSQL readiness; checksum migration failure aborts
    # before accepting traffic. Never performs a destructive downgrade/reset.
    runpy.run_path(str(ROOT / "scripts/migrate.py"), run_name="__main__")
    runpy.run_path(str(ROOT / "scripts/serve.py"), run_name="__main__")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print('{"event":"release_start_failed"}', file=sys.stderr)
        raise SystemExit(1) from None
