"""
ASR Systems - Shared File Utilities
Common file handling functions for both systems
"""

import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from ..core.exceptions import FileSystemError, ValidationError


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (sha256, md5, sha1)

    Returns:
        Hexadecimal hash string

    Raises:
        FileSystemError: If file cannot be read or algorithm is invalid
    """
    try:
        hash_obj = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    except FileNotFoundError:
        raise FileSystemError(
            f"File not found: {file_path}", file_path=file_path, operation="hash"
        )
    except ValueError as e:
        raise FileSystemError(f"Invalid hash algorithm: {algorithm}", operation="hash")
    except Exception as e:
        raise FileSystemError(
            f"Error calculating hash: {e}", file_path=file_path, operation="hash"
        )


def safe_copy_file(
    source_path: str, destination_path: str, create_dirs: bool = True
) -> bool:
    """
    Safely copy a file with error handling

    Args:
        source_path: Source file path
        destination_path: Destination file path
        create_dirs: Whether to create destination directories if they don't exist

    Returns:
        True if copy was successful, False otherwise

    Raises:
        FileSystemError: If copy operation fails
    """
    try:
        source = Path(source_path)
        destination = Path(destination_path)

        # Check source exists
        if not source.exists():
            raise FileSystemError(
                f"Source file not found: {source_path}",
                file_path=source_path,
                operation="copy",
            )

        # Create destination directories if needed
        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source, destination)
        return True

    except Exception as e:
        raise FileSystemError(
            f"Failed to copy file: {e}", file_path=source_path, operation="copy"
        )


def safe_move_file(
    source_path: str, destination_path: str, create_dirs: bool = True
) -> bool:
    """
    Safely move a file with error handling

    Args:
        source_path: Source file path
        destination_path: Destination file path
        create_dirs: Whether to create destination directories if they don't exist

    Returns:
        True if move was successful, False otherwise

    Raises:
        FileSystemError: If move operation fails
    """
    try:
        source = Path(source_path)
        destination = Path(destination_path)

        # Check source exists
        if not source.exists():
            raise FileSystemError(
                f"Source file not found: {source_path}",
                file_path=source_path,
                operation="move",
            )

        # Create destination directories if needed
        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        shutil.move(str(source), str(destination))
        return True

    except Exception as e:
        raise FileSystemError(
            f"Failed to move file: {e}", file_path=source_path, operation="move"
        )


def safe_delete_file(file_path: str, missing_ok: bool = True) -> bool:
    """
    Safely delete a file

    Args:
        file_path: Path to file to delete
        missing_ok: If True, don't raise error if file doesn't exist

    Returns:
        True if file was deleted or didn't exist (with missing_ok=True)

    Raises:
        FileSystemError: If deletion fails
    """
    try:
        file_obj = Path(file_path)

        if not file_obj.exists():
            if missing_ok:
                return True
            else:
                raise FileSystemError(
                    f"File not found: {file_path}",
                    file_path=file_path,
                    operation="delete",
                )

        file_obj.unlink()
        return True

    except Exception as e:
        raise FileSystemError(
            f"Failed to delete file: {e}", file_path=file_path, operation="delete"
        )


def create_temp_file(
    suffix: str = None, prefix: str = "asr_", delete: bool = False
) -> Tuple[str, Any]:
    """
    Create a temporary file

    Args:
        suffix: File suffix (e.g., '.pdf')
        prefix: File prefix
        delete: Whether to auto-delete file when closed

    Returns:
        Tuple of (file_path, file_object)
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix, prefix=prefix, delete=delete
        )
        return temp_file.name, temp_file

    except Exception as e:
        raise FileSystemError(
            f"Failed to create temporary file: {e}", operation="temp_create"
        )


def create_temp_directory(prefix: str = "asr_temp_") -> str:
    """
    Create a temporary directory

    Args:
        prefix: Directory name prefix

    Returns:
        Path to temporary directory

    Raises:
        FileSystemError: If directory creation fails
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        return temp_dir

    except Exception as e:
        raise FileSystemError(
            f"Failed to create temporary directory: {e}", operation="temp_dir_create"
        )


def ensure_directory(directory_path: str) -> Path:
    """
    Ensure directory exists, create if necessary

    Args:
        directory_path: Path to directory

    Returns:
        Path object to the directory

    Raises:
        FileSystemError: If directory creation fails
    """
    try:
        dir_obj = Path(directory_path)
        dir_obj.mkdir(parents=True, exist_ok=True)
        return dir_obj

    except Exception as e:
        raise FileSystemError(
            f"Failed to create directory: {e}",
            file_path=directory_path,
            operation="mkdir",
        )


def cleanup_directory(
    directory_path: str, older_than_days: int = 7, pattern: str = "*"
) -> int:
    """
    Clean up files in directory older than specified days

    Args:
        directory_path: Path to directory to clean
        older_than_days: Delete files older than this many days
        pattern: File pattern to match (default: all files)

    Returns:
        Number of files deleted

    Raises:
        FileSystemError: If cleanup fails
    """
    try:
        directory = Path(directory_path)
        if not directory.exists():
            return 0

        cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in directory.glob(pattern):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1

        return deleted_count

    except Exception as e:
        raise FileSystemError(
            f"Failed to cleanup directory: {e}",
            file_path=directory_path,
            operation="cleanup",
        )


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive file information

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information

    Raises:
        FileSystemError: If file cannot be accessed
    """
    try:
        file_obj = Path(file_path)

        if not file_obj.exists():
            raise FileSystemError(
                f"File not found: {file_path}", file_path=file_path, operation="info"
            )

        stat_info = file_obj.stat()

        return {
            "name": file_obj.name,
            "stem": file_obj.stem,
            "suffix": file_obj.suffix,
            "size_bytes": stat_info.st_size,
            "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "is_file": file_obj.is_file(),
            "is_dir": file_obj.is_dir(),
            "absolute_path": str(file_obj.absolute()),
            "parent": str(file_obj.parent),
        }

    except Exception as e:
        raise FileSystemError(
            f"Failed to get file info: {e}", file_path=file_path, operation="info"
        )


def find_files(
    directory: str, pattern: str = "*", recursive: bool = True, max_depth: int = None
) -> List[str]:
    """
    Find files matching pattern in directory

    Args:
        directory: Directory to search in
        pattern: File pattern to match
        recursive: Whether to search recursively
        max_depth: Maximum depth for recursive search

    Returns:
        List of file paths

    Raises:
        FileSystemError: If directory cannot be accessed
    """
    try:
        directory_obj = Path(directory)

        if not directory_obj.exists():
            raise FileSystemError(
                f"Directory not found: {directory}",
                file_path=directory,
                operation="find",
            )

        files = []

        if recursive:
            if max_depth is not None:
                # Implement depth-limited search
                def _search_with_depth(path: Path, current_depth: int):
                    if current_depth > max_depth:
                        return

                    for item in path.glob(pattern):
                        if item.is_file():
                            files.append(str(item))

                    for subdir in path.iterdir():
                        if subdir.is_dir():
                            _search_with_depth(subdir, current_depth + 1)

                _search_with_depth(directory_obj, 0)
            else:
                # Unlimited depth
                for file_path in directory_obj.rglob(pattern):
                    if file_path.is_file():
                        files.append(str(file_path))
        else:
            # Non-recursive search
            for file_path in directory_obj.glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))

        return sorted(files)

    except Exception as e:
        raise FileSystemError(
            f"Failed to find files: {e}", file_path=directory, operation="find"
        )


def create_archive(
    files: List[str], archive_path: str, compression: bool = True
) -> str:
    """
    Create a ZIP archive from list of files

    Args:
        files: List of file paths to include
        archive_path: Path for the archive
        compression: Whether to use compression

    Returns:
        Path to created archive

    Raises:
        FileSystemError: If archive creation fails
    """
    try:
        archive_obj = Path(archive_path)
        archive_obj.parent.mkdir(parents=True, exist_ok=True)

        compression_type = zipfile.ZIP_DEFLATED if compression else zipfile.ZIP_STORED

        with zipfile.ZipFile(archive_path, "w", compression=compression_type) as zipf:
            for file_path in files:
                file_obj = Path(file_path)
                if file_obj.exists() and file_obj.is_file():
                    # Use just filename as archive name to avoid path issues
                    archive_name = file_obj.name
                    zipf.write(file_path, archive_name)

        return archive_path

    except Exception as e:
        raise FileSystemError(
            f"Failed to create archive: {e}",
            file_path=archive_path,
            operation="archive",
        )


def extract_archive(archive_path: str, extract_to: str) -> List[str]:
    """
    Extract ZIP archive to directory

    Args:
        archive_path: Path to ZIP archive
        extract_to: Directory to extract to

    Returns:
        List of extracted file paths

    Raises:
        FileSystemError: If extraction fails
    """
    try:
        archive_obj = Path(archive_path)
        extract_dir = Path(extract_to)

        if not archive_obj.exists():
            raise FileSystemError(
                f"Archive not found: {archive_path}",
                file_path=archive_path,
                operation="extract",
            )

        extract_dir.mkdir(parents=True, exist_ok=True)
        extracted_files = []

        with zipfile.ZipFile(archive_path, "r") as zipf:
            for file_info in zipf.infolist():
                # Security check: prevent directory traversal
                if ".." in file_info.filename or file_info.filename.startswith("/"):
                    continue

                extracted_path = zipf.extract(file_info, extract_to)
                extracted_files.append(extracted_path)

        return extracted_files

    except Exception as e:
        raise FileSystemError(
            f"Failed to extract archive: {e}",
            file_path=archive_path,
            operation="extract",
        )


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """
    Save data as JSON file

    Args:
        data: Data to save
        file_path: Path to save file
        indent: JSON indentation

    Returns:
        True if successful

    Raises:
        FileSystemError: If save fails
    """
    try:
        file_obj = Path(file_path)
        file_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        return True

    except Exception as e:
        raise FileSystemError(
            f"Failed to save JSON file: {e}", file_path=file_path, operation="json_save"
        )


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load data from JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded data

    Raises:
        FileSystemError: If load fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        raise FileSystemError(
            f"JSON file not found: {file_path}",
            file_path=file_path,
            operation="json_load",
        )
    except json.JSONDecodeError as e:
        raise FileSystemError(
            f"Invalid JSON format: {e}", file_path=file_path, operation="json_load"
        )
    except Exception as e:
        raise FileSystemError(
            f"Failed to load JSON file: {e}", file_path=file_path, operation="json_load"
        )


# Export all utility functions
__all__ = [
    "calculate_file_hash",
    "safe_copy_file",
    "safe_move_file",
    "safe_delete_file",
    "create_temp_file",
    "create_temp_directory",
    "ensure_directory",
    "cleanup_directory",
    "get_file_info",
    "find_files",
    "create_archive",
    "extract_archive",
    "save_json_file",
    "load_json_file",
]
