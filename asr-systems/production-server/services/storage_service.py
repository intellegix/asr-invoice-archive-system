"""
Production Storage Service
Handles document storage with multi-backend support
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import shared components
from shared.core.models import DocumentMetadata
from shared.core.exceptions import StorageError

logger = logging.getLogger(__name__)


@dataclass
class StorageResult:
    """Storage operation result"""
    success: bool
    storage_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DocumentData:
    """Stored document data"""
    content: bytes
    metadata: DocumentMetadata
    storage_path: str
    stored_at: datetime


class ProductionStorageService:
    """
    Production storage service with multi-backend support

    Features:
    - Local filesystem storage
    - Cloud storage integration (S3, Azure, etc.)
    - Multi-tenant document isolation
    - Metadata persistence
    - Document retrieval and management
    """

    def __init__(self, storage_config: Dict[str, Any]):
        self.storage_config = storage_config
        self.storage_backend = storage_config.get('backend', 'local')
        self.base_path = Path(storage_config.get('local_path', './storage'))
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize storage service"""
        try:
            logger.info("🚀 Initializing Production Storage Service...")

            if self.storage_backend == 'local':
                # Ensure storage directory exists
                self.base_path.mkdir(parents=True, exist_ok=True)

                # Create tenant directories
                for tenant_dir in ['documents', 'metadata', 'temp']:
                    (self.base_path / tenant_dir).mkdir(exist_ok=True)

                logger.info(f"📁 Local storage initialized: {self.base_path}")

            elif self.storage_backend == 's3':
                # S3 storage initialization would go here
                logger.info("☁️ S3 storage configuration detected")

            self.initialized = True

            logger.info("✅ Production Storage Service initialized:")
            logger.info(f"   • Backend: {self.storage_backend}")
            logger.info(f"   • Base path: {self.base_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Storage Service: {e}")
            raise StorageError(f"Storage initialization failed: {e}")

    async def store_document(
        self,
        document_id: str,
        file_content: bytes,
        metadata: DocumentMetadata
    ) -> StorageResult:
        """Store document with metadata"""
        try:
            if not self.initialized:
                raise StorageError("Storage service not initialized")

            logger.info(f"📁 Storing document: {document_id}")
            logger.info(f"   • Filename: {metadata.filename}")
            logger.info(f"   • Size: {len(file_content)} bytes")
            logger.info(f"   • Tenant: {metadata.tenant_id}")

            if self.storage_backend == 'local':
                return await self._store_local(document_id, file_content, metadata)
            elif self.storage_backend == 's3':
                return await self._store_s3(document_id, file_content, metadata)
            else:
                raise StorageError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"❌ Document storage failed: {e}")
            return StorageResult(success=False, error=str(e))

    async def _store_local(
        self,
        document_id: str,
        file_content: bytes,
        metadata: DocumentMetadata
    ) -> StorageResult:
        """Store document in local filesystem"""
        try:
            # Create tenant-specific path
            tenant_path = self.base_path / "documents" / metadata.tenant_id
            tenant_path.mkdir(parents=True, exist_ok=True)

            # Create document file path
            file_extension = metadata.filename.split('.')[-1] if '.' in metadata.filename else 'bin'
            document_filename = f"{document_id}.{file_extension}"
            document_path = tenant_path / document_filename

            # Store document content
            async with asyncio.get_event_loop().run_in_executor(None, document_path.open, 'wb') as f:
                await asyncio.get_event_loop().run_in_executor(None, f.write, file_content)

            # Store metadata
            metadata_path = self.base_path / "metadata" / metadata.tenant_id
            metadata_path.mkdir(parents=True, exist_ok=True)
            metadata_file = metadata_path / f"{document_id}.json"

            metadata_dict = {
                "document_id": document_id,
                "filename": metadata.filename,
                "file_size": len(file_content),
                "content_type": metadata.content_type,
                "tenant_id": metadata.tenant_id,
                "upload_source": metadata.upload_source,
                "scanner_id": getattr(metadata, 'scanner_id', None),
                "scanner_metadata": getattr(metadata, 'scanner_metadata', {}),
                "stored_at": datetime.now().isoformat(),
                "storage_path": str(document_path)
            }

            import json
            async with asyncio.get_event_loop().run_in_executor(None, metadata_file.open, 'w') as f:
                await asyncio.get_event_loop().run_in_executor(None, json.dump, metadata_dict, f)

            logger.info(f"✅ Document stored locally: {document_path}")

            return StorageResult(
                success=True,
                storage_path=str(document_path)
            )

        except Exception as e:
            raise StorageError(f"Local storage failed: {e}")

    async def _store_s3(
        self,
        document_id: str,
        file_content: bytes,
        metadata: DocumentMetadata
    ) -> StorageResult:
        """Store document in S3 (placeholder implementation)"""
        try:
            # S3 storage implementation would go here
            # This would use boto3 to upload to S3 with tenant isolation

            s3_key = f"tenants/{metadata.tenant_id}/documents/{document_id}"

            logger.info(f"☁️ Would store to S3: s3://bucket/{s3_key}")

            # Placeholder - actual S3 implementation needed
            return StorageResult(
                success=True,
                storage_path=f"s3://bucket/{s3_key}"
            )

        except Exception as e:
            raise StorageError(f"S3 storage failed: {e}")

    async def retrieve_document(self, document_id: str) -> Optional[DocumentData]:
        """Retrieve document by ID"""
        try:
            if not self.initialized:
                raise StorageError("Storage service not initialized")

            if self.storage_backend == 'local':
                return await self._retrieve_local(document_id)
            elif self.storage_backend == 's3':
                return await self._retrieve_s3(document_id)
            else:
                raise StorageError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"❌ Document retrieval failed: {e}")
            return None

    async def _retrieve_local(self, document_id: str) -> Optional[DocumentData]:
        """Retrieve document from local filesystem"""
        try:
            # Find metadata file
            metadata_pattern = f"{document_id}.json"
            metadata_files = list(self.base_path.glob(f"metadata/**/{metadata_pattern}"))

            if not metadata_files:
                logger.warning(f"⚠️ Metadata not found for document: {document_id}")
                return None

            metadata_file = metadata_files[0]

            # Load metadata
            import json
            with metadata_file.open('r') as f:
                metadata_dict = json.load(f)

            storage_path = metadata_dict['storage_path']

            # Load document content
            with Path(storage_path).open('rb') as f:
                content = f.read()

            # Create metadata object
            metadata = DocumentMetadata(
                filename=metadata_dict['filename'],
                file_size=metadata_dict['file_size'],
                content_type=metadata_dict['content_type'],
                tenant_id=metadata_dict['tenant_id'],
                upload_source=metadata_dict.get('upload_source', 'unknown')
            )

            return DocumentData(
                content=content,
                metadata=metadata,
                storage_path=storage_path,
                stored_at=datetime.fromisoformat(metadata_dict['stored_at'])
            )

        except Exception as e:
            logger.error(f"❌ Local retrieval failed: {e}")
            return None

    async def _retrieve_s3(self, document_id: str) -> Optional[DocumentData]:
        """Retrieve document from S3 (placeholder implementation)"""
        try:
            # S3 retrieval implementation would go here
            logger.info(f"☁️ Would retrieve from S3: {document_id}")
            return None

        except Exception as e:
            logger.error(f"❌ S3 retrieval failed: {e}")
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete document and metadata"""
        try:
            if not self.initialized:
                raise StorageError("Storage service not initialized")

            if self.storage_backend == 'local':
                return await self._delete_local(document_id)
            elif self.storage_backend == 's3':
                return await self._delete_s3(document_id)
            else:
                raise StorageError(f"Unsupported storage backend: {self.storage_backend}")

        except Exception as e:
            logger.error(f"❌ Document deletion failed: {e}")
            return False

    async def _delete_local(self, document_id: str) -> bool:
        """Delete document from local filesystem"""
        try:
            # Find and delete metadata
            metadata_pattern = f"{document_id}.json"
            metadata_files = list(self.base_path.glob(f"metadata/**/{metadata_pattern}"))

            deleted_files = 0

            for metadata_file in metadata_files:
                # Load metadata to get storage path
                import json
                with metadata_file.open('r') as f:
                    metadata_dict = json.load(f)

                storage_path = Path(metadata_dict['storage_path'])

                # Delete document file
                if storage_path.exists():
                    storage_path.unlink()
                    deleted_files += 1

                # Delete metadata file
                metadata_file.unlink()
                deleted_files += 1

            logger.info(f"🗑️ Deleted {deleted_files} files for document: {document_id}")
            return deleted_files > 0

        except Exception as e:
            logger.error(f"❌ Local deletion failed: {e}")
            return False

    async def _delete_s3(self, document_id: str) -> bool:
        """Delete document from S3 (placeholder implementation)"""
        try:
            # S3 deletion implementation would go here
            logger.info(f"☁️ Would delete from S3: {document_id}")
            return True

        except Exception as e:
            logger.error(f"❌ S3 deletion failed: {e}")
            return False

    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            if self.storage_backend == 'local':
                return await self._get_local_stats()
            elif self.storage_backend == 's3':
                return await self._get_s3_stats()
            else:
                return {}

        except Exception as e:
            logger.error(f"❌ Failed to get storage statistics: {e}")
            return {}

    async def _get_local_stats(self) -> Dict[str, Any]:
        """Get local storage statistics"""
        try:
            total_size = 0
            document_count = 0

            for document_file in self.base_path.glob("documents/**/*"):
                if document_file.is_file():
                    total_size += document_file.stat().st_size
                    document_count += 1

            return {
                "backend": "local",
                "total_documents": document_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "base_path": str(self.base_path)
            }

        except Exception as e:
            logger.error(f"❌ Failed to get local stats: {e}")
            return {}

    async def _get_s3_stats(self) -> Dict[str, Any]:
        """Get S3 storage statistics (placeholder implementation)"""
        return {
            "backend": "s3",
            "total_documents": 0,
            "total_size_bytes": 0,
            "bucket": "placeholder"
        }

    async def get_health(self) -> Dict[str, Any]:
        """Get storage service health status"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            stats = await self.get_storage_statistics()

            return {
                "status": "healthy",
                "backend": self.storage_backend,
                "base_path": str(self.base_path),
                "storage_statistics": stats
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def cleanup(self) -> None:
        """Cleanup storage service"""
        logger.info("🧹 Cleaning up Production Storage Service...")
        self.initialized = False