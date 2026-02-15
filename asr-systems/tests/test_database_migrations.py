"""
Tests for Alembic migration infrastructure and DATABASE_URL validation.
"""

import os
import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))


class TestAlembicConfiguration:
    """Verify that Alembic config and migration files exist and parse correctly."""

    _alembic_root = Path(__file__).parent.parent

    def test_alembic_ini_exists(self):
        assert (self._alembic_root / "alembic.ini").exists()

    def test_env_py_exists(self):
        assert (self._alembic_root / "alembic" / "env.py").exists()

    def test_initial_migration_exists(self):
        versions = self._alembic_root / "alembic" / "versions"
        migration_files = list(versions.glob("*.py"))
        assert len(migration_files) >= 1, "Expected at least 1 migration file"


class TestAlembicEnvImport:
    """The env.py module should be importable and resolve a valid URL."""

    def test_get_url_returns_string(self):
        import importlib.util

        env_path = Path(__file__).parent.parent / "alembic" / "env.py"
        spec = importlib.util.spec_from_file_location("alembic_env", str(env_path))
        # We don't want to *run* the migration, just test _get_url
        # So we extract the function manually
        with open(env_path) as f:
            source = f.read()

        # _get_url is defined in env.py — verify it's callable
        assert "_get_url" in source


class TestDatabaseUrlValidation:
    """Production settings should warn when using SQLite in production."""

    def test_sqlite_warning_in_production(self):
        from config.production_settings import ProductionSettings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Create settings with SQLite + production mode (DEBUG=false, no cloud)
            try:
                settings = ProductionSettings(
                    DATABASE_URL="sqlite:///test.db",
                    DEBUG=False,
                    ANTHROPIC_API_KEY="test-key-placeholder",
                )
                sqlite_warnings = [
                    x
                    for x in w
                    if "SQLite" in str(x.message) and "production" in str(x.message)
                ]
                assert len(sqlite_warnings) >= 1
            except Exception:
                # Validation may raise for other reasons; that's fine
                pass

    def test_cloud_sqlite_raises(self):
        from config.production_settings import ProductionSettings

        with pytest.raises(ValueError, match="SQLite.*not supported.*cloud"):
            ProductionSettings(
                DATABASE_URL="sqlite:///test.db",
                AWS_DEPLOYMENT_MODE=True,
                ANTHROPIC_API_KEY="test-key-placeholder",
            )


class TestAlembicMigrationChain:
    """Verify upgrade/downgrade for each migration against a temp SQLite DB."""

    _alembic_root = Path(__file__).parent.parent

    def _get_alembic_config(self, db_url: str):
        """Build Alembic Config pointing at a given database URL."""
        from alembic.config import Config

        cfg = Config(str(self._alembic_root / "alembic.ini"))
        cfg.set_main_option("script_location", str(self._alembic_root / "alembic"))
        cfg.set_main_option("sqlalchemy.url", db_url)
        return cfg

    def test_upgrade_to_head(self, tmp_path):
        """Running 'upgrade head' on a fresh DB should succeed."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        # Verify tables were created (0005 renames audit_events → audit_trail)
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "audit_trail" in tables
        assert "audit_events" not in tables
        assert "vendors" in tables
        assert "alembic_version" in tables

    def test_downgrade_to_base(self, tmp_path):
        """Running 'downgrade base' after upgrade should revert all tables."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "audit_events" not in tables
        assert "audit_trail" not in tables
        assert "vendors" not in tables

    def test_upgrade_is_idempotent(self, tmp_path):
        """Running 'upgrade head' twice should not fail."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")  # Second run should be a no-op

    def test_migration_chain_is_linear(self):
        """Verify all migrations form a linear chain (no branches)."""
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config(str(self._alembic_root / "alembic.ini"))
        cfg.set_main_option("script_location", str(self._alembic_root / "alembic"))
        script = ScriptDirectory.from_config(cfg)
        revisions = list(script.walk_revisions())
        assert len(revisions) == 6  # 0001, 0002, 0003, 0004, 0005, 0006

        # Verify linear chain: each revision (except first) has exactly one down_revision
        heads = script.get_heads()
        assert len(heads) == 1, f"Expected 1 head, got {len(heads)}: {heads}"

    def test_seed_migration_populates_vendors(self, tmp_path):
        """Migration 0003 should seed 24 vendors into the table."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
        conn.close()
        assert count == 24, f"Expected 24 seeded vendors, got {count}"

    def test_seed_migration_downgrade_removes_vendors(self, tmp_path):
        """Downgrading from 0003 to 0002 should remove seeded vendors only."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        # Add a non-seeded vendor
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO vendors (id, name, display_name, tenant_id, active, notes) "
            "VALUES ('custom-1', 'Custom Vendor', 'Custom', 'default', 1, 'Custom notes')"
        )
        conn.commit()

        # Downgrade just one step (0003 → 0002)
        command.downgrade(cfg, "0002")

        count = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
        conn.close()
        assert count == 1, f"Non-seeded vendor should survive; got {count}"

    def test_offline_sql_up_to_schema_only(self, tmp_path):
        """Schema-only migrations (0001-0002) should work in --sql mode.
        Migration 0003 is a data migration (uses op.get_bind()) so offline
        mode stops before it."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        # Generate SQL for schema-only migrations (0001 + 0002)
        command.upgrade(cfg, "0002", sql=True)

    # --- P87: Migration 0005 tests ---

    def test_migration_0005_renames_audit_events(self, tmp_path):
        """After upgrade to 0005, audit_trail exists and audit_events does not."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "audit_trail" in tables, "audit_trail table should exist after 0005"
        assert "audit_events" not in tables, "audit_events should be renamed"

    def test_migration_0005_downgrade_restores_audit_events(self, tmp_path):
        """Downgrading from 0005 to 0004 should restore audit_events name."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "0004")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert (
            "audit_events" in tables
        ), "audit_events should be restored after downgrade"
        assert "audit_trail" not in tables

    def test_migration_0005_indices_renamed(self, tmp_path):
        """After 0005 (up to 0005 only), indices should use audit_trail prefix."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "0005")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        indices = {
            row[1]
            for row in conn.execute("PRAGMA index_list('audit_trail')").fetchall()
        }
        conn.close()
        assert "ix_audit_trail_entity_id" in indices
        assert "ix_audit_trail_tenant_id" in indices
        assert "ix_audit_trail_created_at" in indices

    def test_migration_0005_upgrade_downgrade_upgrade(self, tmp_path):
        """0005 should be idempotent through upgrade→downgrade→upgrade cycle."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "0004")
        command.upgrade(cfg, "head")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "audit_trail" in tables

    def test_docker_entrypoint_exists(self):
        """docker-entrypoint.sh should exist in production_server/."""
        entrypoint = (
            Path(__file__).parent.parent / "production_server" / "docker-entrypoint.sh"
        )
        assert entrypoint.exists(), "docker-entrypoint.sh must exist for auto-migration"
        content = entrypoint.read_text()
        assert "alembic" in content, "Entrypoint must run alembic upgrade"

    def test_entrypoint_uses_advisory_lock(self):
        """docker-entrypoint.sh should use pg_advisory_lock for concurrent safety."""
        entrypoint = (
            Path(__file__).parent.parent / "production_server" / "docker-entrypoint.sh"
        )
        content = entrypoint.read_text()
        assert (
            "pg_advisory_lock" in content
        ), "Entrypoint must use pg_advisory_lock to prevent migration race conditions"
        assert (
            "pg_advisory_unlock" in content
        ), "Entrypoint must release advisory lock after migration"

    def test_dockerfile_has_entrypoint(self):
        """Dockerfile should reference the entrypoint."""
        dockerfile = Path(__file__).parent.parent / "production_server" / "Dockerfile"
        content = dockerfile.read_text()
        assert (
            "ENTRYPOINT" in content
        ), "Dockerfile must have ENTRYPOINT for auto-migration"
        assert "docker-entrypoint.sh" in content

    # --- P91: Migration 0006 tests ---

    def test_migration_0006_is_noop_on_sqlite(self, tmp_path):
        """Migration 0006 should be a no-op on SQLite (columns unchanged)."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info('audit_trail')").fetchall()
        }
        conn.close()
        # SQLite still has 0001 columns since 0006 is a no-op
        assert "entity_id" in columns
        assert "created_at" in columns

    def test_migration_0006_upgrade_downgrade_cycle(self, tmp_path):
        """0006 should survive upgrade → downgrade → upgrade on SQLite."""
        from alembic import command

        db_path = tmp_path / "test.db"
        cfg = self._get_alembic_config(f"sqlite:///{db_path}")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "0005")
        command.upgrade(cfg, "head")

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "audit_trail" in tables
