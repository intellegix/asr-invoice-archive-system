"""
ASR Invoice Archive System - Storage Service
Abstraction layer for file storage backends (local, Render disk, cloud)
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    async def upload_file(self, file_path: str, content: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Upload file content to storage"""
        pass

    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download file content from storage"""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in storage with optional prefix filter"""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage"""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""

    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file_path: str, content: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Upload file to local storage"""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(content)

        return str(full_path)

    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage"""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(full_path, 'rb') as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        full_path = self.base_path / file_path

        if full_path.exists():
            full_path.unlink()
            return True

        return False

    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in local storage"""
        files = []
        search_path = self.base_path / prefix if prefix else self.base_path

        if search_path.is_file():
            return [str(search_path.relative_to(self.base_path))]

        if search_path.exists():
            for file_path in search_path.rglob('*'):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(self.base_path)))

        return files

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage"""
        full_path = self.base_path / file_path
        return full_path.exists()


class RenderDiskBackend(StorageBackend):
    """Render persistent disk storage backend"""

    def __init__(self, mount_path: str = "/data", create_structure: bool = True):
        self.mount_path = Path(mount_path)

        if create_structure:
            # Create standard directory structure
            directories = [
                "scan_inbox",
                "manual_review",
                "processed",
                "billing/open",
                "billing/closed",
                "logs"
            ]

            for directory in directories:
                (self.mount_path / directory).mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file_path: str, content: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Upload file to Render disk"""
        full_path = self.mount_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write operation
        temp_path = full_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'wb') as f:
                f.write(content)
            temp_path.rename(full_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return str(full_path)

    async def download_file(self, file_path: str) -> bytes:
        """Download file from Render disk"""
        full_path = self.mount_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(full_path, 'rb') as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Render disk"""
        full_path = self.mount_path / file_path

        if full_path.exists():
            full_path.unlink()
            return True

        return False

    async def list_files(self, prefix: str = "") -> List[str]:
        """List files on Render disk"""
        files = []
        search_path = self.mount_path / prefix if prefix else self.mount_path

        if search_path.is_file():
            return [str(search_path.relative_to(self.mount_path))]

        if search_path.exists():
            for file_path in search_path.rglob('*'):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(self.mount_path)))

        return files

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists on Render disk"""
        full_path = self.mount_path / file_path
        return full_path.exists()


def get_storage_backend() -> StorageBackend:
    """Factory function to get appropriate storage backend"""
    backend_type = os.getenv("STORAGE_BACKEND", "local")

    if backend_type == "render_disk":
        mount_path = os.getenv("RENDER_DISK_MOUNT", "/data")
        return RenderDiskBackend(mount_path=mount_path)
    else:
        # Default to local storage
        data_dir = os.getenv("DATA_DIR", "./data")
        return LocalStorageBackend(base_path=data_dir)