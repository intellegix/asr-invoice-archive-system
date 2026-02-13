"""
P78: GL Account database migration and CRUD tests.
Validates GLAccountRecord ORM model, DB persistence, CRUD endpoints,
migration seeding, and category filtering.
"""

import os
import sys
from pathlib import Path

import pytest

_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production-server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from tests.auth_helpers import AUTH_HEADERS, CSRF_COOKIES, WRITE_HEADERS

# ---------------------------------------------------------------------------
# Direct service-level tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gl_account_create_and_read():
    """Create a GL account via service and read it back."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()

        result = await svc.create_gl_account(
            code="9999",
            name="Test Account",
            category="EXPENSES",
            keywords=["test", "debug"],
        )
        assert result["code"] == "9999"
        assert result["name"] == "Test Account"
        assert result["category"] == "EXPENSES"

        # Should now be in cache
        account = svc.get_account_by_code("9999")
        assert account is not None
        assert account.name == "Test Account"
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_gl_account_update():
    """Update a GL account and verify changes propagate."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()

        await svc.create_gl_account(code="9998", name="Original", category="ASSETS")
        updated = await svc.update_gl_account(
            "9998", {"name": "Updated Name", "keywords": ["new"]}
        )
        assert updated is not None
        assert updated["name"] == "Updated Name"

        # Cache should reflect update
        acc = svc.get_account_by_code("9998")
        assert acc.name == "Updated Name"
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_gl_account_update_nonexistent():
    """Updating a nonexistent GL account returns None."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()
        result = await svc.update_gl_account("0000", {"name": "X"})
        assert result is None
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_gl_account_delete():
    """Delete a GL account from DB and cache."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()

        await svc.create_gl_account(code="9997", name="Doomed", category="INCOME")
        assert svc.get_account_by_code("9997") is not None

        deleted = await svc.delete_gl_account("9997")
        assert deleted is True
        assert svc.get_account_by_code("9997") is None
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_gl_account_delete_nonexistent():
    """Deleting a nonexistent GL account returns False."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()
        assert await svc.delete_gl_account("0000") is False
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_gl_account_list_from_db():
    """List GL accounts from DB with optional category filter."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()

        await svc.create_gl_account(code="8001", name="A1", category="ASSETS")
        await svc.create_gl_account(code="8002", name="E1", category="EXPENSES")

        all_accounts = await svc.list_gl_accounts_from_db()
        assert len(all_accounts) >= 2

        assets_only = await svc.list_gl_accounts_from_db(category="ASSETS")
        assert all(a["category"] == "ASSETS" for a in assets_only)
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_gl_account_deactivation_removes_from_cache():
    """Setting active=False removes account from in-memory cache."""
    from config.database import close_database, init_database
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        svc = GLAccountService()
        await svc.initialize()

        await svc.create_gl_account(code="8003", name="Active", category="ASSETS")
        assert svc.get_account_by_code("8003") is not None

        await svc.update_gl_account("8003", {"active": False})
        assert svc.get_account_by_code("8003") is None
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_load_from_database_loads_accounts():
    """_load_from_database populates gl_accounts from DB rows."""
    from config.database import close_database, get_async_session, init_database
    from models.gl_account import GLAccountRecord
    from services.gl_account_service import GLAccountService

    await init_database("sqlite:///")
    try:
        # Manually insert a row
        async with get_async_session() as session:
            session.add(
                GLAccountRecord(
                    code="7777",
                    name="DB Account",
                    category="INCOME",
                    keywords=["db", "test"],
                )
            )
            await session.commit()

        svc = GLAccountService()
        loaded = await svc._load_from_database()
        assert loaded is True
        assert "7777" in svc.gl_accounts
        assert svc.gl_accounts["7777"].name == "DB Account"
    finally:
        await close_database()


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


def test_create_gl_account_endpoint():
    """POST /api/v1/gl-accounts creates a new GL account."""
    import uuid

    from fastapi.testclient import TestClient

    from api.main import app

    code = f"X{uuid.uuid4().hex[:4].upper()}"
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post(
            "/api/v1/gl-accounts",
            json={
                "code": code,
                "name": "Endpoint Test",
                "category": "EXPENSES",
                "keywords": ["ep"],
            },
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["code"] == code


def test_update_gl_account_endpoint():
    """PUT /api/v1/gl-accounts/{code} updates a GL account."""
    import uuid

    from fastapi.testclient import TestClient

    from api.main import app

    code = f"U{uuid.uuid4().hex[:4].upper()}"
    with TestClient(app, raise_server_exceptions=False) as client:
        # Create first
        client.post(
            "/api/v1/gl-accounts",
            json={"code": code, "name": "Before", "category": "ASSETS"},
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        # Update
        resp = client.put(
            f"/api/v1/gl-accounts/{code}",
            json={"name": "After"},
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "After"


def test_delete_gl_account_endpoint():
    """DELETE /api/v1/gl-accounts/{code} removes a GL account."""
    import uuid

    from fastapi.testclient import TestClient

    from api.main import app

    code = f"D{uuid.uuid4().hex[:4].upper()}"
    with TestClient(app, raise_server_exceptions=False) as client:
        # Create first
        client.post(
            "/api/v1/gl-accounts",
            json={"code": code, "name": "ToDelete", "category": "INCOME"},
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        # Delete
        resp = client.delete(
            f"/api/v1/gl-accounts/{code}",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["code"] == code


def test_delete_gl_account_not_found():
    """DELETE /api/v1/gl-accounts/{code} returns 404 for nonexistent code."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.delete(
            "/api/v1/gl-accounts/0000",
            headers=WRITE_HEADERS,
            cookies=CSRF_COOKIES,
        )
        assert resp.status_code == 404


def test_gl_record_to_dict_structure():
    """_gl_record_to_dict returns expected fields."""
    from models.gl_account import GLAccountRecord
    from services.gl_account_service import GLAccountService

    row = GLAccountRecord(
        code="1234",
        name="Test",
        category="ASSETS",
        keywords=["k"],
        active=True,
        description="desc",
        tenant_id="t1",
    )
    d = GLAccountService._gl_record_to_dict(row)
    assert d["code"] == "1234"
    assert d["name"] == "Test"
    assert d["category"] == "ASSETS"
    assert d["keywords"] == ["k"]
    assert d["description"] == "desc"
    assert d["tenant_id"] == "t1"
