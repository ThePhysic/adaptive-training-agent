import importlib.util
from pathlib import Path

import psycopg
import pytest


@pytest.mark.integration
def test_local_postgres_migration_is_repeatable():
    spec = importlib.util.spec_from_file_location("bootstrap_migration", "scripts/migrate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate()
    assert module.migrate() == []
    with psycopg.connect(module.LOCAL_DSN) as connection:
        assert connection.execute(
            "SELECT value FROM foundation_metadata WHERE key='stage'"
        ).fetchone() == ("F1-01",)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            )
        }
        assert tables == {
            "schema_migrations",
            "foundation_metadata",
            "profiles",
            "approved_plans",
            "approval_idempotency",
            "approval_audit",
            "session_records",
            "session_idempotency",
            "spend_projects",
            "spend_grants",
            "spend_sessions",
            "spend_attempts",
            "spend_pairs",
            "spend_operations",
            "spend_observations",
            "probe_spend_projects",
            "probe_spend_grants",
            "probe_spend_sessions",
            "probe_spend_attempts",
            "probe_spend_pairs",
            "probe_spend_operations",
            "probe_spend_observations",
            "probe_authorities",
        }


def test_migration_has_no_premature_application_tables():
    sql = Path("migrations/001_foundation.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE foundation_metadata" in sql
    assert "CREATE TABLE approved_plans" not in sql


@pytest.mark.integration
def test_applied_checksum_change_is_rejected(tmp_path):
    spec = importlib.util.spec_from_file_location("checksum_migration", "scripts/migrate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate()
    directory = tmp_path / "migrations"
    directory.mkdir()
    (directory / "001_foundation.sql").write_text("SELECT 1;", encoding="utf-8")
    module.ROOT = tmp_path
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        module.migrate()


@pytest.mark.integration
def test_failed_migration_rolls_back_sql_and_history(tmp_path):
    spec = importlib.util.spec_from_file_location("rollback_migration", "scripts/migrate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.migrate()
    directory = tmp_path / "migrations"
    directory.mkdir()
    (directory / "002_fault.sql").write_text(
        "INSERT INTO foundation_metadata VALUES ('must_rollback', 'synthetic'); "
        "SELECT * FROM deliberately_missing_f101_table;",
        encoding="utf-8",
    )
    module.ROOT = tmp_path
    with pytest.raises(psycopg.errors.UndefinedTable):
        module.migrate()
    with psycopg.connect(module.LOCAL_DSN) as connection:
        assert (
            connection.execute(
                "SELECT value FROM foundation_metadata WHERE key='must_rollback'"
            ).fetchone()
            is None
        )
        assert (
            connection.execute(
                "SELECT name FROM schema_migrations WHERE name='002_fault.sql'"
            ).fetchone()
            is None
        )
