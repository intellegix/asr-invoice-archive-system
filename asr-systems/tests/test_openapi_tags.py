"""
Tests for OpenAPI tags and ENABLE_DOCS setting.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))

from production_server.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestOpenApiTags:
    """Every endpoint should carry an OpenAPI tag."""

    def test_openapi_schema_has_tags_metadata(self, client: TestClient):
        schema = app.openapi()
        tag_names = [t["name"] for t in schema.get("tags", [])]
        expected = {"Health", "Auth", "Documents", "GL Accounts", "Scanner", "System"}
        assert expected.issubset(set(tag_names))

    def test_all_paths_have_tags(self, client: TestClient):
        schema = app.openapi()
        paths = schema.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    tags = details.get("tags", [])
                    assert len(tags) > 0, f"{method.upper()} {path} is missing tags"

    def test_health_live_exists_in_schema(self, client: TestClient):
        schema = app.openapi()
        assert "/health/live" in schema.get("paths", {})

    def test_health_ready_exists_in_schema(self, client: TestClient):
        schema = app.openapi()
        assert "/health/ready" in schema.get("paths", {})
