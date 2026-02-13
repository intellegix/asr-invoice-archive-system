"""
Unit Tests for Shared Validation Utilities
Covers validate_*, sanitize_*, and detect_* functions in shared/utils/validation.py
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from shared.core.constants import (
    CONFIDENCE_THRESHOLDS,
    GL_ACCOUNTS,
    MAX_FILE_SIZE_MB,
    SUPPORTED_EXTENSIONS,
)
from shared.core.exceptions import ValidationError
from shared.utils.validation import (
    detect_mime_type,
    sanitize_filename,
    sanitize_search_query,
    validate_api_key,
    validate_batch_size,
    validate_confidence_score,
    validate_document_metadata,
    validate_file_extension,
    validate_file_for_upload,
    validate_file_size,
    validate_filename,
    validate_gl_account,
    validate_sort_parameters,
    validate_tenant_id,
)


class TestValidateFileExtension:
    """Tests for validate_file_extension()"""

    def test_supported_pdf(self):
        assert validate_file_extension("invoice.pdf") is True

    def test_supported_jpg(self):
        assert validate_file_extension("photo.jpg") is True

    def test_supported_jpeg(self):
        assert validate_file_extension("photo.jpeg") is True

    def test_supported_png(self):
        assert validate_file_extension("scan.png") is True

    def test_supported_tiff(self):
        assert validate_file_extension("document.tiff") is True

    def test_supported_docx(self):
        assert validate_file_extension("report.docx") is True

    def test_unsupported_exe(self):
        assert validate_file_extension("malware.exe") is False

    def test_unsupported_py(self):
        assert validate_file_extension("script.py") is False

    def test_case_insensitive(self):
        assert validate_file_extension("INVOICE.PDF") is True

    def test_no_extension(self):
        assert validate_file_extension("noextension") is False


class TestValidateFileSize:
    """Tests for validate_file_size()"""

    def test_valid_small_file(self):
        assert validate_file_size(1024) is True

    def test_valid_1mb(self):
        assert validate_file_size(1 * 1024 * 1024) is True

    def test_at_max_limit(self):
        assert validate_file_size(MAX_FILE_SIZE_MB * 1024 * 1024) is True

    def test_over_limit(self):
        assert validate_file_size((MAX_FILE_SIZE_MB + 1) * 1024 * 1024) is False

    def test_zero_size(self):
        assert validate_file_size(0) is False

    def test_negative_size(self):
        assert validate_file_size(-100) is False


class TestDetectMimeType:
    """Tests for detect_mime_type()"""

    def test_pdf_by_extension(self, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 dummy content")
        result = detect_mime_type(str(f))
        assert result == "application/pdf"

    def test_txt_by_extension(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = detect_mime_type(str(f))
        assert result == "text/plain"

    def test_unsupported_extension(self, tmp_path):
        # Use binary content that magic detects as application/octet-stream
        f = tmp_path / "test.qzqzqz"
        f.write_bytes(bytes(range(256)) * 4)
        with pytest.raises(ValidationError):
            detect_mime_type(str(f))

    def test_known_image_extension(self, tmp_path):
        f = tmp_path / "scan.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n dummy")
        result = detect_mime_type(str(f))
        assert result == "image/png"


class TestValidateFileForUpload:
    """Tests for validate_file_for_upload()"""

    def test_valid_pdf_file(self, tmp_path):
        f = tmp_path / "invoice.pdf"
        f.write_bytes(b"%PDF-1.4 dummy content for upload test")
        is_valid, error, metadata = validate_file_for_upload(str(f))
        assert is_valid is True
        assert error is None
        assert metadata["filename"] == "invoice.pdf"
        assert metadata["file_size"] > 0
        assert metadata["extension"] == ".pdf"

    def test_nonexistent_file(self):
        is_valid, error, _ = validate_file_for_upload("/nonexistent/file.pdf")
        assert is_valid is False
        assert "not found" in error.lower()

    def test_directory_instead_of_file(self, tmp_path):
        is_valid, error, _ = validate_file_for_upload(str(tmp_path))
        assert is_valid is False
        assert "not a file" in error.lower()

    def test_unsupported_extension(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b,c")
        is_valid, error, _ = validate_file_for_upload(str(f))
        assert is_valid is False
        assert "unsupported" in error.lower()

    def test_oversized_file(self, tmp_path):
        f = tmp_path / "big.pdf"
        f.write_bytes(b"%PDF-1.4 " + b"x" * ((MAX_FILE_SIZE_MB + 1) * 1024 * 1024))
        is_valid, error, _ = validate_file_for_upload(str(f))
        assert is_valid is False
        assert "exceeds" in error.lower()


class TestValidateFilename:
    """Tests for validate_filename()"""

    def test_valid_filename(self):
        is_valid, error = validate_filename("invoice_2024.pdf")
        assert is_valid is True
        assert error is None

    def test_empty_filename(self):
        is_valid, error = validate_filename("")
        assert is_valid is False

    def test_whitespace_filename(self):
        is_valid, error = validate_filename("   ")
        assert is_valid is False

    def test_too_long(self):
        is_valid, error = validate_filename("a" * 256)
        assert is_valid is False
        assert "too long" in error.lower()

    def test_invalid_char_colon(self):
        is_valid, error = validate_filename("file:name.pdf")
        assert is_valid is False
        assert "invalid character" in error.lower()

    def test_invalid_char_pipe(self):
        is_valid, error = validate_filename("file|name.pdf")
        assert is_valid is False

    def test_invalid_char_angle(self):
        is_valid, error = validate_filename("file<name>.pdf")
        assert is_valid is False

    def test_reserved_name_con(self):
        is_valid, error = validate_filename("CON.pdf")
        assert is_valid is False
        assert "reserved" in error.lower()

    def test_reserved_name_lpt1(self):
        is_valid, error = validate_filename("LPT1.txt")
        assert is_valid is False

    def test_double_dots(self):
        is_valid, error = validate_filename("..secret")
        assert is_valid is False

    def test_single_dot(self):
        is_valid, error = validate_filename(".")
        assert is_valid is False

    def test_trailing_space(self):
        is_valid, error = validate_filename("file.pdf ")
        assert is_valid is False

    def test_trailing_dot(self):
        is_valid, error = validate_filename("file.")
        assert is_valid is False


class TestSanitizeFilename:
    """Tests for sanitize_filename()"""

    def test_replaces_invalid_chars(self):
        result = sanitize_filename("file<name>:test.pdf")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert result.endswith(".pdf")

    def test_empty_becomes_document(self):
        result = sanitize_filename("")
        assert result == "document.pdf"

    def test_long_name_truncated(self):
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_adds_pdf_extension_if_missing(self):
        result = sanitize_filename("invoice")
        assert result.endswith(".pdf")

    def test_preserves_existing_extension(self):
        result = sanitize_filename("scan.png")
        assert result == "scan.png"

    def test_strips_whitespace(self):
        result = sanitize_filename("  invoice.pdf  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestValidateGlAccount:
    """Tests for validate_gl_account()"""

    def test_valid_account(self):
        code = next(iter(GL_ACCOUNTS.keys()))
        is_valid, error, info = validate_gl_account(code)
        assert is_valid is True
        assert error is None
        assert info["code"] == code

    def test_empty_code(self):
        is_valid, error, info = validate_gl_account("")
        assert is_valid is False
        assert info is None

    def test_invalid_code(self):
        is_valid, error, info = validate_gl_account("9999")
        assert is_valid is False
        assert "invalid" in error.lower()

    def test_whitespace_stripped(self):
        code = next(iter(GL_ACCOUNTS.keys()))
        is_valid, _, info = validate_gl_account(f"  {code}  ")
        assert is_valid is True
        assert info["code"] == code


class TestValidateConfidenceScore:
    """Tests for validate_confidence_score()"""

    def test_above_threshold(self):
        threshold = CONFIDENCE_THRESHOLDS["PAYMENT_DETECTION_MIN"]
        assert validate_confidence_score(threshold + 0.1) is True

    def test_at_threshold(self):
        threshold = CONFIDENCE_THRESHOLDS["PAYMENT_DETECTION_MIN"]
        assert validate_confidence_score(threshold) is True

    def test_below_threshold(self):
        assert validate_confidence_score(0.1) is False

    def test_out_of_range_high(self):
        assert validate_confidence_score(1.5) is False

    def test_out_of_range_low(self):
        assert validate_confidence_score(-0.1) is False

    def test_zero(self):
        assert validate_confidence_score(0.0) is False

    def test_perfect_score(self):
        assert validate_confidence_score(1.0) is True

    def test_custom_threshold(self):
        assert validate_confidence_score(0.8, "GL_CLASSIFICATION_HIGH") is False
        assert validate_confidence_score(0.95, "GL_CLASSIFICATION_HIGH") is True

    def test_unknown_threshold_defaults_to_half(self):
        assert validate_confidence_score(0.6, "NONEXISTENT") is True
        assert validate_confidence_score(0.4, "NONEXISTENT") is False


class TestValidateTenantId:
    """Tests for validate_tenant_id()"""

    def test_valid_alphanumeric(self):
        assert validate_tenant_id("tenant-123") is True

    def test_valid_underscores(self):
        assert validate_tenant_id("my_tenant") is True

    def test_empty_string(self):
        assert validate_tenant_id("") is False

    def test_too_short(self):
        assert validate_tenant_id("ab") is False

    def test_too_long(self):
        assert validate_tenant_id("a" * 51) is False

    def test_special_chars(self):
        assert validate_tenant_id("tenant@invalid") is False

    def test_spaces(self):
        assert validate_tenant_id("tenant 123") is False

    def test_min_length(self):
        assert validate_tenant_id("abc") is True

    def test_max_length(self):
        assert validate_tenant_id("a" * 50) is True


class TestValidateApiKey:
    """Tests for validate_api_key()"""

    def test_valid_key(self):
        assert validate_api_key("a" * 32) is True

    def test_empty_key(self):
        assert validate_api_key("") is False

    def test_too_short(self):
        assert validate_api_key("short") is False

    def test_valid_base64_chars(self):
        assert validate_api_key("ABCDEFghijk12345+/=_-" + "x" * 20) is True

    def test_invalid_chars(self):
        assert validate_api_key("a" * 31 + "!") is False


class TestValidateBatchSize:
    """Tests for validate_batch_size()"""

    def test_valid_size(self):
        assert validate_batch_size(10) is True

    def test_min_valid(self):
        assert validate_batch_size(1) is True

    def test_max_default(self):
        assert validate_batch_size(50) is True

    def test_zero(self):
        assert validate_batch_size(0) is False

    def test_over_default_max(self):
        assert validate_batch_size(51) is False

    def test_custom_max(self):
        assert validate_batch_size(100, max_size=200) is True
        assert validate_batch_size(201, max_size=200) is False

    def test_negative(self):
        assert validate_batch_size(-1) is False


class TestValidateDocumentMetadata:
    """Tests for validate_document_metadata()"""

    def test_valid_metadata(self):
        meta = {
            "filename": "invoice.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
        }
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is True
        assert errors == []

    def test_missing_filename(self):
        meta = {"file_size": 1024, "mime_type": "application/pdf"}
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False
        assert any("filename" in e for e in errors)

    def test_missing_file_size(self):
        meta = {"filename": "test.pdf", "mime_type": "application/pdf"}
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False
        assert any("file_size" in e for e in errors)

    def test_missing_mime_type(self):
        meta = {"filename": "test.pdf", "file_size": 1024}
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False
        assert any("mime_type" in e for e in errors)

    def test_invalid_file_size_zero(self):
        meta = {
            "filename": "test.pdf",
            "file_size": 0,
            "mime_type": "application/pdf",
        }
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False

    def test_invalid_file_size_string(self):
        meta = {
            "filename": "test.pdf",
            "file_size": "not a number",
            "mime_type": "application/pdf",
        }
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False

    def test_unsupported_mime_type(self):
        meta = {
            "filename": "test.pdf",
            "file_size": 1024,
            "mime_type": "application/zip",
        }
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False
        assert any("mime" in e.lower() for e in errors)

    def test_empty_dict(self):
        is_valid, errors = validate_document_metadata({})
        assert is_valid is False
        assert len(errors) == 3  # 3 required fields missing

    def test_invalid_filename_in_metadata(self):
        meta = {
            "filename": "CON.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
        }
        is_valid, errors = validate_document_metadata(meta)
        assert is_valid is False
        assert any("filename" in e.lower() for e in errors)


class TestSanitizeSearchQuery:
    """Tests for sanitize_search_query()"""

    def test_clean_query(self):
        assert sanitize_search_query("invoice 2024") == "invoice 2024"

    def test_removes_angle_brackets(self):
        result = sanitize_search_query("<script>alert(1)</script>")
        assert "<" not in result
        assert ">" not in result

    def test_removes_quotes(self):
        result = sanitize_search_query("test' OR '1'='1")
        assert "'" not in result

    def test_removes_semicolon(self):
        result = sanitize_search_query("test; DROP TABLE;")
        assert ";" not in result

    def test_normalizes_whitespace(self):
        result = sanitize_search_query("  hello   world  ")
        assert result == "hello world"

    def test_empty_query(self):
        assert sanitize_search_query("") == ""

    def test_truncates_long_query(self):
        long_query = "a" * 600
        result = sanitize_search_query(long_query)
        assert len(result) <= 500


class TestValidateSortParameters:
    """Tests for validate_sort_parameters()"""

    def test_valid_asc(self):
        is_valid, error = validate_sort_parameters("name", "asc", ["name", "date"])
        assert is_valid is True
        assert error == ""

    def test_valid_desc(self):
        is_valid, error = validate_sort_parameters("date", "desc", ["name", "date"])
        assert is_valid is True

    def test_invalid_field(self):
        is_valid, error = validate_sort_parameters("invalid", "asc", ["name", "date"])
        assert is_valid is False
        assert "invalid sort field" in error.lower()

    def test_invalid_order(self):
        is_valid, error = validate_sort_parameters("name", "random", ["name", "date"])
        assert is_valid is False
        assert "asc" in error and "desc" in error

    def test_empty_sort_by_is_valid(self):
        is_valid, _ = validate_sort_parameters("", "asc", ["name"])
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
