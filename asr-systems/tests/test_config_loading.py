"""
Tests for YAML configuration loading (GL accounts and routing rules).
Covers: valid parse, missing file fallback, schema validation errors,
and Pydantic v2 deprecation-free settings.
"""

import warnings
from pathlib import Path

import pytest
import yaml

# --- Billing Router (routing rules) --------------------------------------
from production_server.services.billing_router_service import BillingRouterService

# --- GL Accounts ---------------------------------------------------------
from production_server.services.gl_account_service import (
    GLAccountService,
    load_gl_accounts_from_yaml,
)

# Resolve the repo-level config dir
CONFIG_DIR = Path(__file__).parent.parent / "config"
GL_YAML = CONFIG_DIR / "gl_accounts.yaml"
ROUTING_YAML = CONFIG_DIR / "routing_rules.yaml"


# =========================================================================
# GL accounts YAML tests
# =========================================================================


class TestGLAccountsYAML:
    """Tests for GL accounts YAML loading."""

    def test_load_gl_accounts_from_yaml_valid(self) -> None:
        """The shipped gl_accounts.yaml parses and returns 79 accounts."""
        assert GL_YAML.exists(), f"Missing {GL_YAML}"
        accounts = load_gl_accounts_from_yaml(str(GL_YAML))
        assert len(accounts) == 79

    def test_load_gl_accounts_yaml_has_required_fields(self) -> None:
        """Every entry has name, category, and keywords."""
        accounts = load_gl_accounts_from_yaml(str(GL_YAML))
        for code, entry in accounts.items():
            assert "name" in entry, f"Account {code} missing 'name'"
            assert "category" in entry, f"Account {code} missing 'category'"
            assert "keywords" in entry, f"Account {code} missing 'keywords'"
            assert isinstance(entry["keywords"], list)

    def test_load_gl_accounts_missing_file_raises(self) -> None:
        """FileNotFoundError when YAML path does not exist."""
        with pytest.raises(FileNotFoundError):
            load_gl_accounts_from_yaml("/nonexistent/path/gl.yaml")

    def test_load_gl_accounts_invalid_schema_raises(self, tmp_path: Path) -> None:
        """ValueError when YAML lacks 'accounts' key."""
        bad_file = tmp_path / "bad_schema.yaml"
        bad_file.write_text(yaml.dump({"not_accounts": {}}), encoding="utf-8")
        with pytest.raises(ValueError, match="top-level 'accounts' key"):
            load_gl_accounts_from_yaml(str(bad_file))

    def test_load_gl_accounts_missing_field_raises(self, tmp_path: Path) -> None:
        """ValueError when an account entry is missing a required field."""
        bad_data = {"accounts": {"9999": {"name": "Test"}}}
        bad_file = tmp_path / "missing_field.yaml"
        bad_file.write_text(yaml.dump(bad_data), encoding="utf-8")
        with pytest.raises(ValueError, match="missing required field"):
            load_gl_accounts_from_yaml(str(bad_file))

    @pytest.mark.asyncio
    async def test_gl_service_loads_from_yaml(self) -> None:
        """GLAccountService loads 79 accounts from the shipped YAML."""
        svc = GLAccountService(config_path=str(GL_YAML))
        await svc.initialize()
        assert len(svc.get_all_accounts()) == 79

    @pytest.mark.asyncio
    async def test_gl_service_fallback_on_missing_yaml(self) -> None:
        """GLAccountService falls back to built-in constants when YAML missing."""
        svc = GLAccountService(config_path="/does/not/exist.yaml")
        await svc.initialize()
        # Should still load 79 accounts from constants
        assert len(svc.get_all_accounts()) == 79


# =========================================================================
# Routing rules YAML tests
# =========================================================================


class TestRoutingRulesYAML:
    """Tests for routing rules YAML loading."""

    def test_routing_yaml_exists(self) -> None:
        """The shipped routing_rules.yaml file exists."""
        assert ROUTING_YAML.exists(), f"Missing {ROUTING_YAML}"

    def test_routing_yaml_has_four_destinations(self) -> None:
        """Routing YAML defines exactly 4 destinations."""
        data = yaml.safe_load(ROUTING_YAML.read_text(encoding="utf-8"))
        assert "destinations" in data
        assert len(data["destinations"]) == 4

    @pytest.mark.asyncio
    async def test_billing_router_loads_from_yaml(self) -> None:
        """BillingRouterService loads rules from YAML and initializes."""
        svc = BillingRouterService(
            enabled_destinations=[
                "open_payable",
                "closed_payable",
                "open_receivable",
                "closed_receivable",
            ],
            confidence_threshold=0.75,
            config_path=str(ROUTING_YAML),
        )
        await svc.initialize()
        assert len(svc.get_available_destinations()) == 4

    @pytest.mark.asyncio
    async def test_billing_router_fallback_on_missing_yaml(self) -> None:
        """BillingRouterService falls back to defaults when YAML missing."""
        svc = BillingRouterService(
            enabled_destinations=[
                "open_payable",
                "closed_payable",
                "open_receivable",
                "closed_receivable",
            ],
            confidence_threshold=0.75,
            config_path="/does/not/exist.yaml",
        )
        await svc.initialize()
        assert len(svc.get_available_destinations()) == 4


# =========================================================================
# Pydantic v2 settings deprecation tests
# =========================================================================


class TestPydanticV2Settings:
    """Ensure ProductionSettings emits zero Pydantic deprecation warnings."""

    def test_no_pydantic_deprecation_warnings(self) -> None:
        """Instantiating ProductionSettings triggers no DeprecationWarning."""
        from production_server.config.production_settings import ProductionSettings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ProductionSettings(
                ANTHROPIC_API_KEY="test-key",
                DEBUG=True,
            )
        pydantic_deprecations = [
            w
            for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "pydantic" in str(w.message).lower()
        ]
        assert (
            pydantic_deprecations == []
        ), f"Pydantic deprecation warnings: {[str(w.message) for w in pydantic_deprecations]}"

    def test_cors_comma_separated_parsing(self) -> None:
        """cors_origins_list property parses comma-separated string."""
        from production_server.config.production_settings import ProductionSettings

        settings = ProductionSettings(
            ANTHROPIC_API_KEY="test-key",
            DEBUG=True,
            CORS_ALLOWED_ORIGINS="http://localhost:3000,http://example.com , https://app.example.com",
        )
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://example.com",
            "https://app.example.com",
        ]

    def test_cors_env_var_string(self) -> None:
        """CORS_ALLOWED_ORIGINS env var works as comma-separated string."""
        import os

        from production_server.config.production_settings import ProductionSettings

        env_patch = {
            "ANTHROPIC_API_KEY": "test-key",
            "DEBUG": "true",
            "CORS_ALLOWED_ORIGINS": "http://a.com,http://b.com",
        }
        orig = {k: os.environ.get(k) for k in env_patch}
        try:
            os.environ.update(env_patch)
            settings = ProductionSettings()
            assert settings.cors_origins_list == [
                "http://a.com",
                "http://b.com",
            ]
        finally:
            for k, v in orig.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_render_alias_resolves(self) -> None:
        """RENDER env var maps to RENDER_DEPLOYMENT_MODE field."""
        import os

        from production_server.config.production_settings import ProductionSettings

        env_patch = {
            "ANTHROPIC_API_KEY": "test-key",
            "DEBUG": "true",
            "RENDER": "true",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
        }
        orig = {k: os.environ.get(k) for k in env_patch}
        try:
            os.environ.update(env_patch)
            settings = ProductionSettings()
            assert settings.RENDER_DEPLOYMENT_MODE is True
        finally:
            for k, v in orig.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
