"""Apply checksum-verified local migrations for profiles and durable approved state."""

import hashlib
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DSN = "host=127.0.0.1 port=55432 dbname=training_dev user=training_dev connect_timeout=3"


def migrate() -> list[str]:
    applied = []
    with psycopg.connect(LOCAL_DSN) as connection:
        connection.execute("SET LOCAL statement_timeout = '5s'")
        connection.execute("SELECT pg_advisory_xact_lock(10101)")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name text PRIMARY KEY, checksum text NOT NULL
            )
        """)
        for path in sorted((ROOT / "migrations").glob("*.sql")):
            content = path.read_text(encoding="utf-8")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            existing = connection.execute(
                "SELECT checksum FROM schema_migrations WHERE name = %s", (path.name,)
            ).fetchone()
            if existing:
                if existing[0] != digest:
                    raise RuntimeError("Applied migration checksum mismatch")
                continue
            connection.execute(content)
            connection.execute("INSERT INTO schema_migrations VALUES (%s, %s)", (path.name, digest))
            applied.append(path.name)
    return applied


if __name__ == "__main__":
    print({"applied": migrate()})
