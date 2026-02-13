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

# Ensure shared/ and production-server/ are on sys.path
_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production-server"))

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
