"""
Unit Tests for Shared Exception Classes
Covers exception constructors, to_dict(), and handle_exception()
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production_server"))

from shared.core.exceptions import (
    APIError,
    ASRException,
    AuthenticationError,
    AuthorizationError,
    ClassificationError,
    CLAUDEAPIError,
    ConfigurationError,
    ConflictError,
    CriticalSystemError,
    DatabaseError,
    DocumentError,
    ErrorCodes,
    FileSystemError,
    NetworkError,
    PaymentDetectionError,
    QuotaExceededError,
    RetryableError,
    RoutingError,
    ScannerError,
    StorageError,
    TenantError,
    ValidationError,
    handle_exception,
)


class TestASRException:
    """Tests for base ASRException."""

    def test_default_error_code(self):
        exc = ASRException("test error")
        assert exc.message == "test error"
        assert exc.error_code == "ASR_GENERAL_ERROR"
        assert exc.details == {}

    def test_custom_error_code(self):
        exc = ASRException("test", error_code="CUSTOM")
        assert exc.error_code == "CUSTOM"

    def test_with_details(self):
        exc = ASRException("test", details={"key": "value"})
        assert exc.details == {"key": "value"}

    def test_to_dict(self):
        exc = ASRException("test error", error_code="TEST", details={"a": 1})
        d = exc.to_dict()
        assert d["error_type"] == "ASRException"
        assert d["error_code"] == "TEST"
        assert d["message"] == "test error"
        assert d["details"] == {"a": 1}

    def test_str_representation(self):
        exc = ASRException("test error")
        assert str(exc) == "test error"


class TestSpecializedExceptions:
    """Tests for all specialized exception subclasses."""

    def test_configuration_error(self):
        exc = ConfigurationError("bad config", config_key="API_KEY")
        assert exc.error_code == "CONFIG_ERROR"
        assert exc.config_key == "API_KEY"

    def test_tenant_error(self):
        exc = TenantError("tenant missing", tenant_id="t-123")
        assert exc.error_code == "TENANT_ERROR"
        assert exc.tenant_id == "t-123"

    def test_document_error(self):
        exc = DocumentError("parse failed", document_id="doc-1")
        assert exc.error_code == "DOCUMENT_ERROR"
        assert exc.document_id == "doc-1"

    def test_storage_error(self):
        exc = StorageError("write failed", storage_path="/tmp/file")
        assert exc.error_code == "STORAGE_ERROR"
        assert exc.storage_path == "/tmp/file"

    def test_classification_error(self):
        exc = ClassificationError("low confidence", classification_type="gl")
        assert exc.error_code == "CLASSIFICATION_ERROR"
        assert exc.classification_type == "gl"

    def test_payment_detection_error(self):
        exc = PaymentDetectionError("no consensus", method="regex")
        assert exc.error_code == "PAYMENT_DETECTION_ERROR"
        assert exc.method == "regex"

    def test_routing_error(self):
        exc = RoutingError("invalid route", destination="open_payable")
        assert exc.error_code == "ROUTING_ERROR"
        assert exc.destination == "open_payable"

    def test_validation_error(self):
        exc = ValidationError("invalid field", field="email")
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.field == "email"

    def test_authentication_error_default_msg(self):
        exc = AuthenticationError()
        assert exc.message == "Authentication failed"
        assert exc.error_code == "AUTH_ERROR"

    def test_authentication_error_custom_msg(self):
        exc = AuthenticationError("bad token")
        assert exc.message == "bad token"

    def test_authorization_error(self):
        exc = AuthorizationError(resource="/admin")
        assert exc.error_code == "AUTHZ_ERROR"
        assert exc.resource == "/admin"

    def test_api_error(self):
        exc = APIError("server error", status_code=500, endpoint="/api/v1/docs")
        assert exc.error_code == "API_ERROR"
        assert exc.status_code == 500
        assert exc.endpoint == "/api/v1/docs"

    def test_scanner_error(self):
        exc = ScannerError("offline", scanner_id="sc-001")
        assert exc.error_code == "SCANNER_ERROR"
        assert exc.scanner_id == "sc-001"

    def test_network_error(self):
        exc = NetworkError("timeout", url="http://localhost")
        assert exc.error_code == "NETWORK_ERROR"
        assert exc.url == "http://localhost"

    def test_database_error(self):
        exc = DatabaseError("connection failed", operation="query")
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.operation == "query"

    def test_claude_api_error(self):
        exc = CLAUDEAPIError("rate limited", api_status=429)
        assert exc.error_code == "CLAUDE_API_ERROR"
        assert exc.api_status == 429

    def test_filesystem_error(self):
        exc = FileSystemError("disk full", file_path="/data", operation="write")
        assert exc.error_code == "FILESYSTEM_ERROR"
        assert exc.file_path == "/data"
        assert exc.operation == "write"

    def test_quota_exceeded_error(self):
        exc = QuotaExceededError(
            "too many docs",
            resource_type="documents",
            current_usage="100",
            limit="50",
        )
        assert exc.error_code == "QUOTA_EXCEEDED"
        assert exc.resource_type == "documents"
        assert exc.current_usage == "100"
        assert exc.limit == "50"

    def test_conflict_error(self):
        exc = ConflictError("duplicate", resource_id="doc-123")
        assert exc.error_code == "CONFLICT_ERROR"
        assert exc.resource_id == "doc-123"

    def test_retryable_error(self):
        exc = RetryableError("rate limited", retry_after=60)
        assert exc.error_code == "RETRYABLE_ERROR"
        assert exc.retry_after == 60

    def test_critical_system_error(self):
        exc = CriticalSystemError("disk failure", component="storage")
        assert exc.error_code == "CRITICAL_SYSTEM_ERROR"
        assert exc.component == "storage"


class TestErrorCodes:
    """Tests for ErrorCodes constants."""

    def test_general_error(self):
        assert ErrorCodes.GENERAL_ERROR == "ASR_GENERAL_ERROR"

    def test_auth_error(self):
        assert ErrorCodes.AUTH_ERROR == "AUTH_ERROR"

    def test_classification_failed(self):
        assert ErrorCodes.CLASSIFICATION_FAILED == "CLASSIFICATION_FAILED"

    def test_file_not_found(self):
        assert ErrorCodes.FILE_NOT_FOUND == "FILE_NOT_FOUND"


class TestHandleException:
    """Tests for handle_exception() mapper."""

    def test_asr_exception_passthrough(self):
        orig = APIError("test")
        result = handle_exception(orig)
        assert result is orig

    def test_file_not_found(self):
        result = handle_exception(FileNotFoundError("missing.txt"))
        assert isinstance(result, FileSystemError)

    def test_permission_error(self):
        result = handle_exception(PermissionError("denied"))
        assert isinstance(result, FileSystemError)

    def test_connection_error(self):
        result = handle_exception(ConnectionError("refused"))
        assert isinstance(result, NetworkError)

    def test_value_error(self):
        result = handle_exception(ValueError("bad input"))
        assert isinstance(result, ValidationError)

    def test_key_error(self):
        result = handle_exception(KeyError("missing_key"))
        assert isinstance(result, ConfigurationError)

    def test_generic_exception(self):
        result = handle_exception(RuntimeError("unknown"))
        assert isinstance(result, ASRException)
        assert "Unexpected error" in result.message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
