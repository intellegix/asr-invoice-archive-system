"""
Alembic environment configuration for ASR Production Server.
Reads DATABASE_URL from the environment (same source as production_settings).
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Path setup so we can import the ORM Base
# ---------------------------------------------------------------------------
_root = Path(__file__).resolve().parent.parent  # asr-systems/
sys.path.insert(0, str(_root / "production_server"))
sys.path.insert(0, str(_root / "shared"))

from config.database import Base  # noqa: E402

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def _get_url() -> str:
    """Resolve the sync database URL."""
    # CLI override: alembic -x sqlalchemy.url=...
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    # Environment variable (same as production_settings)
    url = os.environ.get("DATABASE_URL", "sqlite:///./data/production_server.db")
    # Ensure we use sync drivers for Alembic (it doesn't do async)
    url = url.replace("sqlite+aiosqlite:", "sqlite:")
    url = url.replace("postgresql+asyncpg:", "postgresql:")
    return url


def run_migrations_offline() -> None:
    """Run migrations in --sql mode (emit SQL without connecting)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
