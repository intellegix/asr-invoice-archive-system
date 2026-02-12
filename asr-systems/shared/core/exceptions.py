"""
ASR Systems - Shared Exception Classes
Common exceptions for both Production Server and Document Scanner
"""

from typing import Any, Dict, Optional


class ASRException(Exception):
    """Base exception class for ASR systems"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "ASR_GENERAL_ERROR"
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(ASRException):
    """Configuration-related errors"""

    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, "CONFIG_ERROR", **kwargs)
        self.config_key = config_key


class TenantError(ASRException):
    """Tenant-related errors"""

    def __init__(self, message: str, tenant_id: Optional[str] = None, **kwargs):
        super().__init__(message, "TENANT_ERROR", **kwargs)
        self.tenant_id = tenant_id


class DocumentError(ASRException):
    """Document processing errors"""

    def __init__(self, message: str, document_id: Optional[str] = None, **kwargs):
        super().__init__(message, "DOCUMENT_ERROR", **kwargs)
        self.document_id = document_id


class StorageError(ASRException):
    """Storage-related errors"""

    def __init__(self, message: str, storage_path: Optional[str] = None, **kwargs):
        super().__init__(message, "STORAGE_ERROR", **kwargs)
        self.storage_path = storage_path


class ClassificationError(ASRException):
    """Document classification errors"""

    def __init__(
        self, message: str, classification_type: Optional[str] = None, **kwargs
    ):
        super().__init__(message, "CLASSIFICATION_ERROR", **kwargs)
        self.classification_type = classification_type


class PaymentDetectionError(ASRException):
    """Payment detection errors"""

    def __init__(self, message: str, method: Optional[str] = None, **kwargs):
        super().__init__(message, "PAYMENT_DETECTION_ERROR", **kwargs)
        self.method = method


class RoutingError(ASRException):
    """Billing routing errors"""

    def __init__(self, message: str, destination: Optional[str] = None, **kwargs):
        super().__init__(message, "ROUTING_ERROR", **kwargs)
        self.destination = destination


class ValidationError(ASRException):
    """Data validation errors"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, "VALIDATION_ERROR", **kwargs)
        self.field = field


class AuthenticationError(ASRException):
    """Authentication errors"""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, "AUTH_ERROR", **kwargs)


class AuthorizationError(ASRException):
    """Authorization errors"""

    def __init__(
        self, message: str = "Access denied", resource: Optional[str] = None, **kwargs
    ):
        super().__init__(message, "AUTHZ_ERROR", **kwargs)
        self.resource = resource


class APIError(ASRException):
    """API communication errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, "API_ERROR", **kwargs)
        self.status_code = status_code
        self.endpoint = endpoint


class ScannerError(ASRException):
    """Document scanner errors"""

    def __init__(self, message: str, scanner_id: Optional[str] = None, **kwargs):
        super().__init__(message, "SCANNER_ERROR", **kwargs)
        self.scanner_id = scanner_id


class NetworkError(ASRException):
    """Network connectivity errors"""

    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        super().__init__(message, "NETWORK_ERROR", **kwargs)
        self.url = url


class DatabaseError(ASRException):
    """Database operation errors"""

    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, "DATABASE_ERROR", **kwargs)
        self.operation = operation


class CLAUDEAPIError(ASRException):
    """Claude AI API errors"""

    def __init__(self, message: str, api_status: Optional[int] = None, **kwargs):
        super().__init__(message, "CLAUDE_API_ERROR", **kwargs)
        self.api_status = api_status


class FileSystemError(ASRException):
    """File system operation errors"""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, "FILESYSTEM_ERROR", **kwargs)
        self.file_path = file_path
        self.operation = operation


class QuotaExceededError(ASRException):
    """Resource quota exceeded errors"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        current_usage: Optional[str] = None,
        limit: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, "QUOTA_EXCEEDED", **kwargs)
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit


class ConflictError(ASRException):
    """Resource conflict errors"""

    def __init__(self, message: str, resource_id: Optional[str] = None, **kwargs):
        super().__init__(message, "CONFLICT_ERROR", **kwargs)
        self.resource_id = resource_id


class RetryableError(ASRException):
    """Errors that should trigger retry logic"""

    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, "RETRYABLE_ERROR", **kwargs)
        self.retry_after = retry_after  # seconds


class CriticalSystemError(ASRException):
    """Critical system errors that require immediate attention"""

    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        super().__init__(message, "CRITICAL_SYSTEM_ERROR", **kwargs)
        self.component = component


# Error code constants
class ErrorCodes:
    """Standard error codes for consistent error handling"""

    # General errors
    GENERAL_ERROR = "ASR_GENERAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFIGURATION_ERROR = "CONFIG_ERROR"

    # Authentication & Authorization
    AUTH_ERROR = "AUTH_ERROR"
    AUTHZ_ERROR = "AUTHZ_ERROR"
    INVALID_API_KEY = "INVALID_API_KEY"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Document processing
    DOCUMENT_UPLOAD_FAILED = "DOCUMENT_UPLOAD_FAILED"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    CLASSIFICATION_FAILED = "CLASSIFICATION_FAILED"
    PAYMENT_DETECTION_FAILED = "PAYMENT_DETECTION_FAILED"
    ROUTING_FAILED = "ROUTING_FAILED"

    # Storage
    STORAGE_NOT_ACCESSIBLE = "STORAGE_NOT_ACCESSIBLE"
    STORAGE_QUOTA_EXCEEDED = "STORAGE_QUOTA_EXCEEDED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"

    # Scanner
    SCANNER_OFFLINE = "SCANNER_OFFLINE"
    SCANNER_AUTH_FAILED = "SCANNER_AUTH_FAILED"
    BATCH_UPLOAD_FAILED = "BATCH_UPLOAD_FAILED"

    # External services
    CLAUDE_API_ERROR = "CLAUDE_API_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"

    # Tenant management
    TENANT_NOT_FOUND = "TENANT_NOT_FOUND"
    TENANT_INACTIVE = "TENANT_INACTIVE"
    TENANT_QUOTA_EXCEEDED = "TENANT_QUOTA_EXCEEDED"


def handle_exception(exc: Exception) -> ASRException:
    """Convert generic exceptions to ASR exceptions"""
    if isinstance(exc, ASRException):
        return exc

    # Map common exceptions to ASR exceptions
    if isinstance(exc, FileNotFoundError):
        return FileSystemError(f"File not found: {exc}", operation="read")
    elif isinstance(exc, PermissionError):
        return FileSystemError(f"Permission denied: {exc}", operation="access")
    elif isinstance(exc, ConnectionError):
        return NetworkError(f"Network connection error: {exc}")
    elif isinstance(exc, ValueError):
        return ValidationError(f"Invalid value: {exc}")
    elif isinstance(exc, KeyError):
        return ConfigurationError(f"Missing configuration: {exc}")
    else:
        return ASRException(f"Unexpected error: {exc}")


# Export all exceptions and utilities
__all__ = [
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
]
