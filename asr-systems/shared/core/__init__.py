"""
ASR Systems - Core Components
Essential shared models, exceptions, and constants
"""

from .constants import *
from .exceptions import *
from .models import *

__all__ = [
    # Models
    "SystemType",
    "ProcessingStatus",
    "PaymentStatus",
    "BillingDestination",
    "GLAccount",
    "PaymentDetectionMethod",
    "PaymentConsensusResult",
    "DocumentMetadata",
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "ClassificationRequest",
    "ClassificationResult",
    "RoutingDecision",
    "AuditTrailEntry",
    "TenantConfiguration",
    "ScannerConfiguration",
    "SystemHealth",
    "APIResponse",
    # Exceptions
    "ASRException",
    "ConfigurationError",
    "TenantError",
    "DocumentError",
    "StorageError",
    "ClassificationError",
    "PaymentDetectionError",
    "RoutingError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "APIError",
    "ScannerError",
    "NetworkError",
    "DatabaseError",
    "CLAUDEAPIError",
    "FileSystemError",
    "QuotaExceededError",
    "ConflictError",
    "RetryableError",
    "CriticalSystemError",
    "ErrorCodes",
    "handle_exception",
    # Constants
    "VERSION",
    "API_VERSION",
    "MAX_FILE_SIZE_MB",
    "MAX_BATCH_SIZE",
    "SUPPORTED_DOCUMENT_TYPES",
    "SUPPORTED_EXTENSIONS",
    "GL_ACCOUNT_CATEGORIES",
    "GL_ACCOUNTS",
    "PAYMENT_INDICATORS",
    "BILLING_DESTINATION_RULES",
    "CONFIDENCE_THRESHOLDS",
    "SCANNER_DEFAULTS",
    "API_ENDPOINTS",
    "HEALTH_CHECK_INTERVALS",
    "STORAGE_CONFIG",
    "DATABASE_CONFIG",
    "EXTERNAL_TIMEOUTS",
    "LOGGING_CONFIG",
    "SECURITY_CONFIG",
]
