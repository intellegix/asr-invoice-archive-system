"""
ASR Production Server - Configuration Settings
Production-ready settings for the separated production server
Inherits and extends shared configurations
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """Production Server configuration with environment variable support"""

    # Application Info
    APP_NAME: str = "ASR Production Server"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = (
        "Enterprise document processing server with sophisticated capabilities"
    )
    SYSTEM_TYPE: str = "production_server"

    # Base Directory
    BASE_DIR: Path = Path(__file__).parent.parent

    # Environment Detection
    DEBUG: bool = Field(
        default=False, env="DEBUG", description="Debug mode (false for production)"
    )

    AWS_DEPLOYMENT_MODE: bool = Field(
        default=False,
        env="AWS_DEPLOYMENT_MODE",
        description="Running in AWS ECS/Fargate environment",
    )

    RENDER_DEPLOYMENT_MODE: bool = Field(
        default=False, env="RENDER", description="Running in Render.com environment"
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./data/production_server.db",
        env="DATABASE_URL",
        description="Database connection string",
    )

    DB_POOL_SIZE: int = Field(
        default=20, env="DB_POOL_SIZE", description="Database connection pool size"
    )

    DB_POOL_OVERFLOW: int = Field(
        default=30,
        env="DB_POOL_OVERFLOW",
        description="Database pool overflow connections",
    )

    DB_POOL_RECYCLE: int = Field(
        default=3600,
        env="DB_POOL_RECYCLE",
        description="Database connection recycle time (seconds)",
    )

    # API Configuration
    API_HOST: str = Field(
        default="127.0.0.1",
        env="API_HOST",
        description="API host binding (0.0.0.0 for production)",
    )

    API_PORT: int = Field(default=8000, env="PORT", description="API port")

    API_WORKERS: int = Field(
        default=4, env="API_WORKERS", description="Number of API worker processes"
    )

    API_TIMEOUT: int = Field(
        default=60, env="API_TIMEOUT", description="API timeout in seconds"
    )

    # Claude AI Configuration
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        env="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude AI integration",
    )

    CLAUDE_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022",
        env="CLAUDE_MODEL",
        description="Claude model to use for document analysis",
    )

    CLAUDE_MAX_TOKENS: int = Field(
        default=4096,
        env="CLAUDE_MAX_TOKENS",
        description="Maximum tokens for Claude responses",
    )

    CLAUDE_TEMPERATURE: float = Field(
        default=0.1,
        env="CLAUDE_TEMPERATURE",
        description="Claude temperature for consistency",
    )

    # Storage Configuration
    STORAGE_BACKEND: str = Field(
        default="local",
        env="STORAGE_BACKEND",
        description="Storage backend type (local, s3, render_disk)",
    )

    # S3 Configuration (for AWS deployment)
    S3_BUCKET: Optional[str] = Field(
        default=None, env="S3_BUCKET", description="S3 bucket name for document storage"
    )

    S3_REGION: str = Field(
        default="us-west-2", env="S3_REGION", description="S3 region"
    )

    S3_PREFIX: str = Field(
        default="production-server",
        env="S3_PREFIX",
        description="S3 prefix for document organization",
    )

    # Render Disk Configuration
    RENDER_DISK_MOUNT: str = Field(
        default="/data",
        env="RENDER_DISK_MOUNT",
        description="Render persistent disk mount path",
    )

    # Directory Paths
    DATA_DIR: Path = BASE_DIR / "data"

    # Multi-Tenant Configuration
    MULTI_TENANT_ENABLED: bool = Field(
        default=True,
        env="MULTI_TENANT_ENABLED",
        description="Enable multi-tenant document isolation",
    )

    DEFAULT_TENANT_ID: str = Field(
        default="default",
        env="DEFAULT_TENANT_ID",
        description="Default tenant ID for single-tenant mode",
    )

    TENANT_ISOLATION_ENABLED: bool = Field(
        default=True,
        env="TENANT_ISOLATION_ENABLED",
        description="Enable strict tenant data isolation",
    )

    # Scanner API Configuration
    SCANNER_API_ENABLED: bool = Field(
        default=True,
        env="SCANNER_API_ENABLED",
        description="Enable API endpoints for document scanners",
    )

    MAX_SCANNER_CLIENTS: int = Field(
        default=100,
        env="MAX_SCANNER_CLIENTS",
        description="Maximum concurrent scanner clients",
    )

    SCANNER_AUTHENTICATION_REQUIRED: bool = Field(
        default=True,
        env="SCANNER_AUTHENTICATION_REQUIRED",
        description="Require API key authentication for scanners",
    )

    # Document Processing Configuration
    MAX_FILE_SIZE_MB: int = Field(
        default=25,
        env="MAX_FILE_SIZE_MB",
        description="Maximum file size for uploads in MB",
    )

    MAX_BATCH_SIZE: int = Field(
        default=50,
        env="MAX_BATCH_SIZE",
        description="Maximum batch size for processing",
    )

    PROCESSING_TIMEOUT: int = Field(
        default=300,
        env="PROCESSING_TIMEOUT",
        description="Document processing timeout in seconds",
    )

    # GL Account Configuration (79 QuickBooks accounts)
    GL_ACCOUNTS_ENABLED: bool = Field(
        default=True,
        env="GL_ACCOUNTS_ENABLED",
        description="Enable GL account classification",
    )

    GL_CLASSIFICATION_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        env="GL_CLASSIFICATION_CONFIDENCE_THRESHOLD",
        description="Minimum confidence for GL classification",
    )

    # Payment Detection Configuration (5-method consensus)
    PAYMENT_DETECTION_ENABLED: bool = Field(
        default=True,
        env="PAYMENT_DETECTION_ENABLED",
        description="Enable payment status detection",
    )

    PAYMENT_DETECTION_METHODS: List[str] = Field(
        default_factory=lambda: [
            "claude_vision",
            "claude_text",
            "regex_patterns",
            "keyword_matching",
            "amount_analysis",
        ],
        env="PAYMENT_DETECTION_METHODS",
        description="Enabled payment detection methods",
    )

    PAYMENT_CONSENSUS_THRESHOLD: float = Field(
        default=0.8,
        env="PAYMENT_CONSENSUS_THRESHOLD",
        description="Minimum consensus confidence for payment detection",
    )

    # Billing Router Configuration (4 destinations)
    BILLING_ROUTER_ENABLED: bool = Field(
        default=True,
        env="BILLING_ROUTER_ENABLED",
        description="Enable billing destination routing",
    )

    BILLING_DESTINATIONS: List[str] = Field(
        default_factory=lambda: [
            "open_payable",
            "closed_payable",
            "open_receivable",
            "closed_receivable",
        ],
        env="BILLING_DESTINATIONS",
        description="Enabled billing destinations",
    )

    ROUTING_CONFIDENCE_THRESHOLD: float = Field(
        default=0.75,
        env="ROUTING_CONFIDENCE_THRESHOLD",
        description="Minimum confidence for routing decisions",
    )

    MANUAL_REVIEW_THRESHOLD: float = Field(
        default=0.7,
        env="MANUAL_REVIEW_THRESHOLD",
        description="Confidence threshold below which manual review is required",
    )

    # Audit Trail Configuration
    AUDIT_TRAIL_ENABLED: bool = Field(
        default=True,
        env="AUDIT_TRAIL_ENABLED",
        description="Enable comprehensive audit trails",
    )

    AUDIT_RETENTION_DAYS: int = Field(
        default=2555,  # 7 years
        env="AUDIT_RETENTION_DAYS",
        description="Audit trail retention period in days",
    )

    # Background Processing Configuration
    BACKGROUND_PROCESSING_ENABLED: bool = Field(
        default=True,
        env="BACKGROUND_PROCESSING_ENABLED",
        description="Enable background document processing",
    )

    BACKGROUND_WORKERS: int = Field(
        default=4,
        env="BACKGROUND_WORKERS",
        description="Number of background processing workers",
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL", description="Logging level")

    LOG_TO_FILE: bool = Field(
        default=True, env="LOG_TO_FILE", description="Enable file logging"
    )

    LOG_FILE_PATH: str = Field(
        default="./logs/production_server.log",
        env="LOG_FILE_PATH",
        description="Log file path",
    )

    # Security Configuration
    API_KEYS_REQUIRED: bool = Field(
        default=True,
        env="API_KEYS_REQUIRED",
        description="Require API keys for authentication",
    )

    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"],
        env="CORS_ALLOWED_ORIGINS",
        description="CORS allowed origins (comma-separated)",
    )

    RATE_LIMIT_ENABLED: bool = Field(
        default=True, env="RATE_LIMIT_ENABLED", description="Enable API rate limiting"
    )

    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        env="RATE_LIMIT_PER_MINUTE",
        description="API requests per minute limit",
    )

    # Health Check Configuration
    HEALTH_CHECK_ENABLED: bool = Field(
        default=True,
        env="HEALTH_CHECK_ENABLED",
        description="Enable health check endpoints",
    )

    HEALTH_CHECK_INTERVAL: int = Field(
        default=60,
        env="HEALTH_CHECK_INTERVAL",
        description="Health check interval in seconds",
    )

    @property
    def get_api_host(self) -> str:
        """Get production-aware API host"""
        if self.AWS_DEPLOYMENT_MODE or self.RENDER_DEPLOYMENT_MODE:
            return "0.0.0.0"
        return self.API_HOST

    @property
    def get_data_dir(self) -> Path:
        """Get data directory based on deployment mode"""
        if self.AWS_DEPLOYMENT_MODE:
            # Use S3 or EFS in AWS
            return Path("/app/data")
        elif self.RENDER_DEPLOYMENT_MODE:
            return Path(self.RENDER_DISK_MOUNT)
        elif self.STORAGE_BACKEND == "render_disk":
            return Path(self.RENDER_DISK_MOUNT)
        return self.DATA_DIR

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.AWS_DEPLOYMENT_MODE or self.RENDER_DEPLOYMENT_MODE or not self.DEBUG

    @property
    def storage_config(self) -> Dict[str, Any]:
        """Get storage configuration based on backend"""
        config = {"backend": self.STORAGE_BACKEND, "base_path": str(self.get_data_dir)}

        if self.STORAGE_BACKEND == "s3":
            config.update(
                {
                    "bucket": self.S3_BUCKET,
                    "region": self.S3_REGION,
                    "prefix": self.S3_PREFIX,
                }
            )
        elif self.STORAGE_BACKEND == "render_disk":
            config.update({"mount_path": self.RENDER_DISK_MOUNT})

        if self.MULTI_TENANT_ENABLED:
            config["tenant_isolation"] = True

        return config

    def get_claude_config(self) -> Dict[str, Any]:
        """Get Claude AI configuration"""
        return {
            "api_key": self.ANTHROPIC_API_KEY,
            "model": self.CLAUDE_MODEL,
            "max_tokens": self.CLAUDE_MAX_TOKENS,
            "temperature": self.CLAUDE_TEMPERATURE,
            "enabled": bool(self.ANTHROPIC_API_KEY),
        }

    def get_processing_config(self) -> Dict[str, Any]:
        """Get document processing configuration"""
        return {
            "gl_accounts_enabled": self.GL_ACCOUNTS_ENABLED,
            "payment_detection_enabled": self.PAYMENT_DETECTION_ENABLED,
            "billing_router_enabled": self.BILLING_ROUTER_ENABLED,
            "audit_trail_enabled": self.AUDIT_TRAIL_ENABLED,
            "payment_methods": self.PAYMENT_DETECTION_METHODS,
            "billing_destinations": self.BILLING_DESTINATIONS,
            "confidence_thresholds": {
                "gl_classification": self.GL_CLASSIFICATION_CONFIDENCE_THRESHOLD,
                "payment_consensus": self.PAYMENT_CONSENSUS_THRESHOLD,
                "routing_decision": self.ROUTING_CONFIDENCE_THRESHOLD,
                "manual_review": self.MANUAL_REVIEW_THRESHOLD,
            },
        }

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "ProductionSettings":
        """Validate production configuration"""

        # Validate Claude AI configuration
        if self.is_production and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for production deployment")

        # Validate database configuration (only enforce PostgreSQL in cloud deployments)
        if (
            self.AWS_DEPLOYMENT_MODE or self.RENDER_DEPLOYMENT_MODE
        ) and self.DATABASE_URL.startswith("sqlite:"):
            raise ValueError(
                "SQLite database not supported in cloud deployment. Use PostgreSQL."
            )

        # Validate S3 configuration if using S3 backend
        if self.STORAGE_BACKEND == "s3" and not self.S3_BUCKET:
            raise ValueError("S3_BUCKET is required when using S3 storage backend")

        # Validate multi-tenant configuration
        if self.MULTI_TENANT_ENABLED and not self.TENANT_ISOLATION_ENABLED:
            raise ValueError(
                "TENANT_ISOLATION_ENABLED must be true when multi-tenant is enabled"
            )

        # Validate scanner API configuration
        if self.SCANNER_API_ENABLED and not self.API_KEYS_REQUIRED:
            raise ValueError(
                "API_KEYS_REQUIRED must be true when scanner API is enabled"
            )

        # Validate sophisticated processing configuration
        if len(self.PAYMENT_DETECTION_METHODS) < 3:
            raise ValueError(
                "At least 3 payment detection methods required for consensus"
            )

        if len(self.BILLING_DESTINATIONS) != 4:
            raise ValueError("All 4 billing destinations must be configured")

        # Validate confidence thresholds
        thresholds = [
            self.GL_CLASSIFICATION_CONFIDENCE_THRESHOLD,
            self.PAYMENT_CONSENSUS_THRESHOLD,
            self.ROUTING_CONFIDENCE_THRESHOLD,
            self.MANUAL_REVIEW_THRESHOLD,
        ]

        for threshold in thresholds:
            if not 0.0 <= threshold <= 1.0:
                raise ValueError(
                    "All confidence thresholds must be between 0.0 and 1.0"
                )

        return self

    def validate_required_secrets(self) -> None:
        """Validate required secrets are configured"""
        issues = []

        if self.is_production:
            if not self.ANTHROPIC_API_KEY:
                issues.append("Missing ANTHROPIC_API_KEY for Claude AI integration")

            if self.STORAGE_BACKEND == "s3" and not self.S3_BUCKET:
                issues.append("Missing S3_BUCKET for S3 storage backend")

        if issues:
            raise ValueError(f"Configuration issues: {', '.join(issues)}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = True


# Global production settings instance
try:
    production_settings = ProductionSettings()
except Exception:
    production_settings = None  # type: ignore[assignment]
