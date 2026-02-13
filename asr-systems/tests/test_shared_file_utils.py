"""
Unit Tests for Shared File Utilities
Covers calculate_file_hash, safe_copy/move/delete, temp files, archive, JSON I/O
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from shared.core.exceptions import FileSystemError
from shared.utils.file_utils import (
    calculate_file_hash,
    cleanup_directory,
    create_archive,
    create_temp_directory,
    create_temp_file,
    ensure_directory,
    extract_archive,
    find_files,
    get_file_info,
    load_json_file,
    safe_copy_file,
    safe_delete_file,
    safe_move_file,
    save_json_file,
)


class TestCalculateFileHash:
    """Tests for calculate_file_hash()"""

    def test_sha256_deterministic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h1 = calculate_file_hash(str(f), "sha256")
        h2 = calculate_file_hash(str(f), "sha256")
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex length

    def test_md5(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = calculate_file_hash(str(f), "md5")
        assert len(result) == 32  # md5 hex length

    def test_sha1(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = calculate_file_hash(str(f), "sha1")
        assert len(result) == 40  # sha1 hex length

    def test_file_not_found(self):
        with pytest.raises(FileSystemError):
            calculate_file_hash("/nonexistent/file.txt")

    def test_invalid_algorithm(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("data")
        with pytest.raises(FileSystemError):
            calculate_file_hash(str(f), "invalid_algo")

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert calculate_file_hash(str(f1)) != calculate_file_hash(str(f2))


class TestSafeCopyFile:
    """Tests for safe_copy_file()"""

    def test_basic_copy(self, tmp_path):
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("content")
        result = safe_copy_file(str(src), str(dst))
        assert result is True
        assert dst.read_text() == "content"

    def test_creates_destination_dirs(self, tmp_path):
        src = tmp_path / "source.txt"
        dst = tmp_path / "subdir" / "deep" / "dest.txt"
        src.write_text("content")
        safe_copy_file(str(src), str(dst))
        assert dst.exists()

    def test_source_not_found(self, tmp_path):
        with pytest.raises(FileSystemError):
            safe_copy_file("/nonexistent.txt", str(tmp_path / "dest.txt"))

    def test_preserves_metadata(self, tmp_path):
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("content")
        safe_copy_file(str(src), str(dst))
        assert dst.stat().st_size == src.stat().st_size


class TestSafeMoveFile:
    """Tests for safe_move_file()"""

    def test_basic_move(self, tmp_path):
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("content")
        result = safe_move_file(str(src), str(dst))
        assert result is True
        assert not src.exists()
        assert dst.read_text() == "content"

    def test_creates_destination_dirs(self, tmp_path):
        src = tmp_path / "source.txt"
        dst = tmp_path / "subdir" / "dest.txt"
        src.write_text("content")
        safe_move_file(str(src), str(dst))
        assert dst.exists()
        assert not src.exists()

    def test_source_not_found(self, tmp_path):
        with pytest.raises(FileSystemError):
            safe_move_file("/nonexistent.txt", str(tmp_path / "dest.txt"))


class TestSafeDeleteFile:
    """Tests for safe_delete_file()"""

    def test_delete_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("delete me")
        result = safe_delete_file(str(f))
        assert result is True
        assert not f.exists()

    def test_missing_ok_true(self, tmp_path):
        result = safe_delete_file(str(tmp_path / "nonexistent.txt"), missing_ok=True)
        assert result is True

    def test_missing_ok_false(self, tmp_path):
        with pytest.raises(FileSystemError):
            safe_delete_file(str(tmp_path / "nonexistent.txt"), missing_ok=False)


class TestCreateTempFile:
    """Tests for create_temp_file()"""

    def test_creates_temp_file(self):
        path, fobj = create_temp_file(suffix=".pdf", delete=False)
        try:
            assert Path(path).exists()
            assert path.endswith(".pdf")
        finally:
            fobj.close()
            Path(path).unlink(missing_ok=True)

    def test_custom_prefix(self):
        path, fobj = create_temp_file(prefix="myapp_", delete=False)
        try:
            assert "myapp_" in Path(path).name
        finally:
            fobj.close()
            Path(path).unlink(missing_ok=True)


class TestCreateTempDirectory:
    """Tests for create_temp_directory()"""

    def test_creates_directory(self):
        path = create_temp_directory()
        try:
            assert Path(path).is_dir()
        finally:
            Path(path).rmdir()

    def test_custom_prefix(self):
        path = create_temp_directory(prefix="test_dir_")
        try:
            assert "test_dir_" in Path(path).name
        finally:
            Path(path).rmdir()


class TestEnsureDirectory:
    """Tests for ensure_directory()"""

    def test_creates_new_directory(self, tmp_path):
        target = tmp_path / "new_dir" / "sub"
        result = ensure_directory(str(target))
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory_ok(self, tmp_path):
        result = ensure_directory(str(tmp_path))
        assert result.exists()

    def test_returns_path_object(self, tmp_path):
        result = ensure_directory(str(tmp_path / "test"))
        assert isinstance(result, Path)


class TestCleanupDirectory:
    """Tests for cleanup_directory()"""

    def test_nonexistent_directory_returns_zero(self):
        count = cleanup_directory("/nonexistent/path")
        assert count == 0

    def test_empty_directory(self, tmp_path):
        count = cleanup_directory(str(tmp_path))
        assert count == 0

    def test_deletes_old_files(self, tmp_path):
        import os
        import time

        f = tmp_path / "old.txt"
        f.write_text("old content")
        # Set mtime to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(str(f), (old_time, old_time))

        count = cleanup_directory(str(tmp_path), older_than_days=7)
        assert count == 1
        assert not f.exists()

    def test_preserves_recent_files(self, tmp_path):
        f = tmp_path / "new.txt"
        f.write_text("recent content")
        count = cleanup_directory(str(tmp_path), older_than_days=7)
        assert count == 0
        assert f.exists()

    def test_pattern_filter(self, tmp_path):
        import os
        import time

        txt = tmp_path / "old.txt"
        pdf = tmp_path / "old.pdf"
        txt.write_text("text")
        pdf.write_bytes(b"pdf")
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(str(txt), (old_time, old_time))
        os.utime(str(pdf), (old_time, old_time))

        count = cleanup_directory(str(tmp_path), older_than_days=7, pattern="*.txt")
        assert count == 1
        assert not txt.exists()
        assert pdf.exists()


class TestGetFileInfo:
    """Tests for get_file_info()"""

    def test_basic_info(self, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"PDF content here")
        info = get_file_info(str(f))
        assert info["name"] == "test.pdf"
        assert info["stem"] == "test"
        assert info["suffix"] == ".pdf"
        assert info["size_bytes"] > 0
        assert info["is_file"] is True
        assert info["is_dir"] is False
        assert "created" in info
        assert "modified" in info

    def test_file_not_found(self):
        with pytest.raises(FileSystemError):
            get_file_info("/nonexistent/file.txt")


class TestFindFiles:
    """Tests for find_files()"""

    def test_find_all_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / "c.pdf").write_bytes(b"c")
        files = find_files(str(tmp_path), pattern="*")
        assert len(files) == 3

    def test_find_by_pattern(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.pdf").write_bytes(b"b")
        files = find_files(str(tmp_path), pattern="*.txt")
        assert len(files) == 1
        assert files[0].endswith(".txt")

    def test_recursive_search(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "root.txt").write_text("root")
        (sub / "nested.txt").write_text("nested")
        files = find_files(str(tmp_path), pattern="*.txt", recursive=True)
        assert len(files) == 2

    def test_non_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "root.txt").write_text("root")
        (sub / "nested.txt").write_text("nested")
        files = find_files(str(tmp_path), pattern="*.txt", recursive=False)
        assert len(files) == 1

    def test_directory_not_found(self):
        with pytest.raises(FileSystemError):
            find_files("/nonexistent/directory")

    def test_sorted_output(self, tmp_path):
        (tmp_path / "c.txt").write_text("c")
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        files = find_files(str(tmp_path), pattern="*.txt")
        assert files == sorted(files)


class TestArchive:
    """Tests for create_archive() and extract_archive()"""

    def test_create_and_extract(self, tmp_path):
        # Create source files
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("alpha")
        (src / "b.txt").write_text("bravo")

        archive_path = str(tmp_path / "test.zip")
        files = [str(src / "a.txt"), str(src / "b.txt")]

        # Create archive
        result = create_archive(files, archive_path)
        assert Path(result).exists()

        # Extract archive
        extract_dir = str(tmp_path / "extracted")
        extracted = extract_archive(archive_path, extract_dir)
        assert len(extracted) == 2

    def test_create_with_no_compression(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("test content")
        archive_path = str(tmp_path / "nocomp.zip")
        result = create_archive([str(f)], archive_path, compression=False)
        assert Path(result).exists()

    def test_extract_nonexistent_archive(self, tmp_path):
        with pytest.raises(FileSystemError):
            extract_archive("/nonexistent.zip", str(tmp_path))

    def test_skips_nonexistent_files(self, tmp_path):
        archive_path = str(tmp_path / "test.zip")
        create_archive(["/nonexistent.txt"], archive_path)
        assert Path(archive_path).exists()


class TestJsonIO:
    """Tests for save_json_file() and load_json_file()"""

    def test_save_and_load(self, tmp_path):
        data = {"key": "value", "count": 42, "nested": {"a": 1}}
        path = str(tmp_path / "data.json")
        save_json_file(data, path)
        loaded = load_json_file(path)
        assert loaded == data

    def test_save_creates_dirs(self, tmp_path):
        path = str(tmp_path / "sub" / "deep" / "data.json")
        save_json_file({"test": True}, path)
        assert Path(path).exists()

    def test_load_not_found(self):
        with pytest.raises(FileSystemError):
            load_json_file("/nonexistent.json")

    def test_load_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not valid json {{{")
        with pytest.raises(FileSystemError):
            load_json_file(str(f))

    def test_save_unicode(self, tmp_path):
        data = {"name": "prix"}
        path = str(tmp_path / "unicode.json")
        save_json_file(data, path)
        loaded = load_json_file(path)
        assert loaded["name"] == "prix"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
