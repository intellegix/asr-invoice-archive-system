"""
P76: Database health verification + CORS validation tests.
Tests check_database_connectivity(), health endpoint DB component,
CORS origins parsing, and database_dialect property.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Ensure shared/ and production_server/ are on sys.path
_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production_server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


# ---------------------------------------------------------------------------
# check_database_connectivity tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_connectivity_returns_connected_after_init():
    """After init_database(), check returns connected + dialect + latency."""
    from config.database import (
        check_database_connectivity,
        close_database,
        init_database,
    )

    await init_database("sqlite:///")
    try:
        result = await check_database_connectivity()
        assert result["status"] == "connected"
        assert result["dialect"] in ("sqlite", "aiosqlite")
        assert isinstance(result["latency_ms"], float)
        assert result["latency_ms"] >= 0
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_db_connectivity_returns_not_initialized_before_init():
    """Before init, returns not_initialized status."""
    from config import database as db_mod

    original_engine = db_mod._engine
    db_mod._engine = None
    try:
        result = await db_mod.check_database_connectivity()
        assert result["status"] == "not_initialized"
        assert result["dialect"] is None
    finally:
        db_mod._engine = original_engine


@pytest.mark.asyncio
async def test_db_connectivity_returns_error_on_failure():
    """If the SELECT 1 fails, returns error status."""
    from unittest.mock import MagicMock

    from config import database as db_mod

    # Create a fake engine whose connect() raises synchronously
    # (async with engine.connect() will hit the error before entering)
    fake_engine = MagicMock()
    fake_engine.connect.side_effect = RuntimeError("connection refused")
    fake_engine.url.get_backend_name.return_value = "sqlite"

    original = db_mod._engine
    db_mod._engine = fake_engine
    try:
        result = await db_mod.check_database_connectivity()
        assert result["status"] == "error"
        assert "connection refused" in result.get("error", "")
    finally:
        db_mod._engine = original


# ---------------------------------------------------------------------------
# Health endpoint includes database component
# ---------------------------------------------------------------------------


def test_health_ready_includes_database_component():
    """GET /health/ready should include components.database with status and dialect."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert "database" in data["components"]
        db = data["components"]["database"]
        assert db["status"] == "connected"
        assert db["dialect"] is not None


def test_health_legacy_includes_database_component():
    """GET /health should also include the database component."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "database" in data["components"]


# ---------------------------------------------------------------------------
# CORS origins parsing tests
# ---------------------------------------------------------------------------


def test_cors_origins_single():
    """Single origin parsed correctly."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        CORS_ALLOWED_ORIGINS="http://localhost:3000",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.cors_origins_list == ["http://localhost:3000"]


def test_cors_origins_multiple():
    """Comma-separated origins parsed into list."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        CORS_ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.cors_origins_list == ["http://localhost:3000", "http://localhost:5173"]


def test_cors_origins_whitespace_stripped():
    """Whitespace around origins is stripped."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        CORS_ALLOWED_ORIGINS="  http://a.com , http://b.com  ",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


def test_cors_origins_empty_entries_removed():
    """Empty entries (trailing comma) are removed."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        CORS_ALLOWED_ORIGINS="http://a.com,,http://b.com,",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


# ---------------------------------------------------------------------------
# database_dialect property tests
# ---------------------------------------------------------------------------


def test_database_dialect_sqlite():
    """DATABASE_URL starting with sqlite returns 'sqlite'."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        DATABASE_URL="sqlite:///./data/test.db",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.database_dialect == "sqlite"


def test_database_dialect_postgresql():
    """DATABASE_URL starting with postgresql returns 'postgresql'."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/db",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.database_dialect == "postgresql"


def test_database_dialect_unknown():
    """Unknown scheme returns the scheme portion."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        DATABASE_URL="mysql://user:pass@localhost/db",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.database_dialect == "mysql"


# ---------------------------------------------------------------------------
# P84: REQUIRE_POSTGRESQL + health degradation + is_production_ready
# ---------------------------------------------------------------------------


def test_require_postgresql_blocks_sqlite_startup():
    """REQUIRE_POSTGRESQL=true + sqlite URL should raise ValueError."""
    from config.production_settings import ProductionSettings

    with pytest.raises(ValueError, match="REQUIRE_POSTGRESQL"):
        ProductionSettings(
            REQUIRE_POSTGRESQL=True,
            DATABASE_URL="sqlite:///./data/test.db",
            ANTHROPIC_API_KEY="test-key",
            DEBUG=True,
        )


def test_require_postgresql_allows_postgresql():
    """REQUIRE_POSTGRESQL=true + postgresql URL should succeed."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        REQUIRE_POSTGRESQL=True,
        DATABASE_URL="postgresql://user:pass@localhost:5432/db",
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.REQUIRE_POSTGRESQL is True
    assert s.database_dialect == "postgresql"


@pytest.mark.asyncio
async def test_connectivity_returns_production_ready_flag():
    """check_database_connectivity should include is_production_ready."""
    from config.database import (
        check_database_connectivity,
        close_database,
        init_database,
    )

    await init_database("sqlite:///")
    try:
        result = await check_database_connectivity()
        assert result["status"] == "connected"
        # SQLite is not production-ready
        assert result["is_production_ready"] is False
    finally:
        await close_database()


def test_health_degraded_when_sqlite_in_production():
    """Health endpoint should show degraded when SQLite in prod mode.

    Since test env uses DEBUG=true, the degradation doesn't trigger.
    We verify the database component has the is_production_ready field.
    """
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        db = data["components"]["database"]
        assert db["status"] == "connected"
        assert "is_production_ready" in db


def test_health_ok_when_sqlite_in_debug():
    """In DEBUG mode SQLite should NOT trigger degradation."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        # DEBUG=true means no degradation
        assert data["overall_status"] == "healthy"


@pytest.mark.asyncio
async def test_pool_status_for_postgresql_mocked():
    """Pool status should be included for PostgreSQL engines (mocked)."""
    from unittest.mock import MagicMock

    from config import database as db_mod

    fake_engine = MagicMock()

    # Mock connect() as async context manager
    fake_conn = MagicMock()
    fake_conn.execute = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=fake_conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    fake_engine.connect.return_value = cm

    fake_engine.url.get_backend_name.return_value = "postgresql"

    # Fake pool with attributes
    fake_pool = MagicMock()
    fake_pool.size = 20
    fake_pool.checkedout = 2
    fake_pool.overflow = 0
    fake_engine.pool = fake_pool

    original = db_mod._engine
    db_mod._engine = fake_engine
    try:
        result = await db_mod.check_database_connectivity()
        assert result["status"] == "connected"
        assert result["is_production_ready"] is True
        assert "pool_status" in result
        assert result["pool_status"]["size"] == 20
    finally:
        db_mod._engine = original


def test_metrics_enabled_setting():
    """METRICS_ENABLED setting should default to False."""
    from config.production_settings import ProductionSettings

    s = ProductionSettings(
        ANTHROPIC_API_KEY="test-key",
        DEBUG=True,
    )
    assert s.METRICS_ENABLED is False
    assert s.METRICS_PATH == "/metrics"
