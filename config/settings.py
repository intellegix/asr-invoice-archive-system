"""
ASR Invoice Archive System - Configuration Settings
Production-ready settings with environment variable support
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with environment variable support"""

    # Application Info
    APP_NAME: str = "ASR Invoice Archive System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Enterprise document processing and archiving system"

    # Base Directory
    BASE_DIR: Path = Path(__file__).parent.parent

    # Environment Detection
    DEBUG: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode (false for production)"
    )

    IS_PRODUCTION: bool = Field(
        default=False,
        env="RENDER",
        description="Render production environment detection"
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./data/invoice_archive.db",
        env="DATABASE_URL",
        description="Database connection string"
    )

    DB_POOL_SIZE: int = Field(
        default=20,
        env="DB_POOL_SIZE",
        description="Database connection pool size"
    )

    DB_POOL_OVERFLOW: int = Field(
        default=0,
        env="DB_POOL_OVERFLOW",
        description="Database pool overflow connections"
    )

    DB_POOL_RECYCLE: int = Field(
        default=3600,
        env="DB_POOL_RECYCLE",
        description="Database connection recycle time (seconds)"
    )

    # API Configuration
    API_HOST: str = Field(
        default="127.0.0.1",
        env="API_HOST",
        description="API host binding (0.0.0.0 for production)"
    )

    API_PORT: int = Field(
        default=8000,
        env="PORT",
        description="API port (from Render $PORT variable)"
    )

    # Claude AI Configuration
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        env="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude AI integration"
    )

    # Storage Configuration
    STORAGE_BACKEND: str = Field(
        default="local",
        env="STORAGE_BACKEND",
        description="Storage backend type (local, render_disk)"
    )

    RENDER_DISK_MOUNT: str = Field(
        default="/data",
        env="RENDER_DISK_MOUNT",
        description="Render persistent disk mount path"
    )

    # Directory Paths
    DATA_DIR: Path = BASE_DIR / "data"

    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )

    @property
    def get_api_host(self) -> str:
        """Get production-aware API host"""
        return "0.0.0.0" if self.IS_PRODUCTION else self.API_HOST

    @property
    def get_data_dir(self) -> Path:
        """Get data directory based on storage backend"""
        if self.STORAGE_BACKEND == "render_disk":
            return Path(self.RENDER_DISK_MOUNT)
        return self.DATA_DIR

    @model_validator(mode='after')
    def validate_required_secrets(self) -> 'Settings':
        """Validate required environment variables for production"""
        if self.IS_PRODUCTION:
            if not self.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required for production")
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields for backwards compatibility


# Global settings instance
settings = Settings()