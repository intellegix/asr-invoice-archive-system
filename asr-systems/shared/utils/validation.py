"""
ASR Systems - Shared Validation Utilities
Common validation functions for both Production Server and Document Scanner
"""

import mimetypes
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import magic
except ImportError:
    magic = None

from ..core.constants import (
    CONFIDENCE_THRESHOLDS,
    GL_ACCOUNTS,
    MAX_FILE_SIZE_MB,
    SUPPORTED_DOCUMENT_TYPES,
    SUPPORTED_EXTENSIONS,
)
from ..core.exceptions import ValidationError


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension against supported types

    Args:
        filename: Name of the file to validate

    Returns:
        True if extension is supported, False otherwise
    """
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    return extension in SUPPORTED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """
    Validate file size against maximum allowed size

    Args:
        file_size: Size of file in bytes

    Returns:
        True if size is within limits, False otherwise
    """
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    return 0 < file_size <= max_size_bytes


def detect_mime_type(file_path: str) -> str:
    """
    Detect MIME type of a file

    Args:
        file_path: Path to the file

    Returns:
        MIME type string

    Raises:
        ValidationError: If file cannot be read or type is unsupported
    """
    try:
        # Try using python-magic first (more accurate)
        if magic is not None:
            mime_type = magic.from_file(file_path, mime=True)
            if mime_type and mime_type in SUPPORTED_DOCUMENT_TYPES:
                return mime_type
    except Exception:
        pass

    # Fallback to mimetypes module
    mime_type, _ = mimetypes.guess_type(file_path)

    if not mime_type:
        # Try to guess from extension
        extension = Path(file_path).suffix.lower()
        for mime, extensions in SUPPORTED_DOCUMENT_TYPES.items():
            if extension in extensions:
                return mime

        raise ValidationError(f"Cannot determine MIME type for file: {file_path}")

    if mime_type not in SUPPORTED_DOCUMENT_TYPES:
        raise ValidationError(f"Unsupported MIME type: {mime_type}")

    return mime_type


def validate_file_for_upload(
    file_path: str,
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Comprehensive file validation for upload

    Args:
        file_path: Path to the file to validate

    Returns:
        Tuple of (is_valid, error_message, file_metadata)
    """
    try:
        file_path_obj = Path(file_path)

        # Check if file exists
        if not file_path_obj.exists():
            return False, f"File not found: {file_path}", {}

        # Check if it's a file (not directory)
        if not file_path_obj.is_file():
            return False, f"Path is not a file: {file_path}", {}

        # Get file metadata
        file_stats = file_path_obj.stat()
        file_size = file_stats.st_size
        filename = file_path_obj.name

        # Validate file extension
        if not validate_file_extension(filename):
            return False, f"Unsupported file extension: {file_path_obj.suffix}", {}

        # Validate file size
        if not validate_file_size(file_size):
            max_size_mb = MAX_FILE_SIZE_MB
            actual_size_mb = file_size / (1024 * 1024)
            return (
                False,
                f"File size {actual_size_mb:.1f}MB exceeds maximum {max_size_mb}MB",
                {},
            )

        # Detect MIME type
        try:
            mime_type = detect_mime_type(file_path)
        except ValidationError as e:
            return False, str(e), {}

        # Check for empty files
        if file_size == 0:
            return False, "File is empty", {}

        # Build metadata
        metadata = {
            "filename": filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "extension": file_path_obj.suffix.lower(),
            "file_stats": {
                "created": file_stats.st_ctime,
                "modified": file_stats.st_mtime,
                "accessed": file_stats.st_atime,
            },
        }

        return True, None, metadata

    except Exception as e:
        return False, f"File validation error: {str(e)}", {}


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename for safety and compatibility

    Args:
        filename: Filename to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for empty filename
    if not filename or filename.isspace():
        return False, "Filename cannot be empty"

    # Check length
    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"

    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
    for char in invalid_chars:
        if char in filename:
            return False, f"Filename contains invalid character: {char}"

    # Check for reserved names (Windows)
    reserved_names = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]

    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        return False, f"Filename uses reserved name: {name_without_ext}"

    # Check for leading/trailing dots or spaces
    if filename.startswith(".") and len(filename) == 1:
        return False, "Filename cannot be just a dot"

    if filename.startswith(".."):
        return False, "Filename cannot start with double dots"

    if filename.endswith(" ") or filename.endswith("."):
        return False, "Filename cannot end with space or dot"

    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
    sanitized = filename

    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")

    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()

    # Ensure not empty
    if not sanitized:
        sanitized = "document"

    # Limit length
    if len(sanitized) > 255:
        name = Path(sanitized).stem[:240]  # Leave room for extension
        ext = Path(sanitized).suffix
        sanitized = f"{name}{ext}"

    # Add extension if missing
    if not Path(sanitized).suffix and not sanitized.endswith(".pdf"):
        sanitized += ".pdf"

    return sanitized


def validate_gl_account(
    gl_code: str,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate GL account code

    Args:
        gl_code: GL account code to validate

    Returns:
        Tuple of (is_valid, error_message, gl_account_info)
    """
    if not gl_code:
        return False, "GL account code cannot be empty", None

    # Remove any whitespace
    gl_code = gl_code.strip()

    # Check if code exists in our GL accounts
    if gl_code not in GL_ACCOUNTS:
        return False, f"Invalid GL account code: {gl_code}", None

    gl_info = GL_ACCOUNTS[gl_code].copy()
    gl_info["code"] = gl_code

    return True, None, gl_info


def validate_confidence_score(
    score: float, threshold_type: str = "PAYMENT_DETECTION_MIN"
) -> bool:
    """
    Validate confidence score against thresholds

    Args:
        score: Confidence score to validate (0.0-1.0)
        threshold_type: Type of threshold to check against

    Returns:
        True if score meets threshold, False otherwise
    """
    if not 0.0 <= score <= 1.0:
        return False

    threshold = CONFIDENCE_THRESHOLDS.get(threshold_type, 0.5)
    return score >= threshold


def validate_tenant_id(tenant_id: str) -> bool:
    """
    Validate tenant ID format

    Args:
        tenant_id: Tenant ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not tenant_id:
        return False

    # Check format: alphanumeric, hyphens, underscores only
    pattern = r"^[a-zA-Z0-9_-]+$"
    if not re.match(pattern, tenant_id):
        return False

    # Check length
    if not 3 <= len(tenant_id) <= 50:
        return False

    return True


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format

    Args:
        api_key: API key to validate

    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False

    # Check minimum length
    if len(api_key) < 32:
        return False

    # Check format: base64-like characters
    pattern = r"^[A-Za-z0-9+/=_-]+$"
    return bool(re.match(pattern, api_key))


def validate_batch_size(batch_size: int, max_size: int = 50) -> bool:
    """
    Validate batch size for operations

    Args:
        batch_size: Number of items in batch
        max_size: Maximum allowed batch size

    Returns:
        True if valid, False otherwise
    """
    return 1 <= batch_size <= max_size


def validate_document_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate document metadata structure

    Args:
        metadata: Metadata dictionary to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check for required fields
    required_fields = ["filename", "file_size", "mime_type"]
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")

    # Validate specific fields if present
    if "filename" in metadata:
        is_valid, error = validate_filename(metadata["filename"])
        if not is_valid:
            errors.append(f"Invalid filename: {error}")

    if "file_size" in metadata:
        if not isinstance(metadata["file_size"], int) or metadata["file_size"] <= 0:
            errors.append("Invalid file_size: must be positive integer")
        elif not validate_file_size(metadata["file_size"]):
            errors.append(f"File size exceeds maximum {MAX_FILE_SIZE_MB}MB")

    if "mime_type" in metadata:
        if metadata["mime_type"] not in SUPPORTED_DOCUMENT_TYPES:
            errors.append(f"Unsupported MIME type: {metadata['mime_type']}")

    return len(errors) == 0, errors


# Input sanitization functions


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent injection attacks

    Args:
        query: Raw search query

    Returns:
        Sanitized query string
    """
    if not query:
        return ""

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", ";", "(", ")", "|", "`"]
    sanitized = query

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, " ")

    # Normalize whitespace
    sanitized = " ".join(sanitized.split())

    # Limit length
    return sanitized[:500]


def validate_sort_parameters(
    sort_by: str, sort_order: str, allowed_fields: List[str]
) -> Tuple[bool, str]:
    """
    Validate sorting parameters

    Args:
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        allowed_fields: List of allowed sort fields

    Returns:
        Tuple of (is_valid, error_message)
    """
    if sort_by and sort_by not in allowed_fields:
        return False, f"Invalid sort field: {sort_by}. Allowed: {allowed_fields}"

    if sort_order not in ["asc", "desc"]:
        return False, "Sort order must be 'asc' or 'desc'"

    return True, ""


# Export all validation functions
__all__ = [
    "validate_file_extension",
    "validate_file_size",
    "detect_mime_type",
    "validate_file_for_upload",
    "validate_filename",
    "sanitize_filename",
    "validate_gl_account",
    "validate_confidence_score",
    "validate_tenant_id",
    "validate_api_key",
    "validate_batch_size",
    "validate_document_metadata",
    "sanitize_search_query",
    "validate_sort_parameters",
]
