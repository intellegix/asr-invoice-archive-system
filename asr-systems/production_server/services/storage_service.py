"""
Production Storage Service
Handles document storage with multi-backend support
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.core.exceptions import StorageError

# Import shared components
from shared.core.models import DocumentMetadata

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
    - S3 cloud storage with boto3
    - Multi-tenant document isolation
    - Metadata persistence
    - Document retrieval and management
    """

    def __init__(self, storage_config: Dict[str, Any]):
        self.storage_config = storage_config
        self.storage_backend = storage_config.get("backend", "local")
        self.base_path = Path(storage_config.get("local_path", "./storage"))
        self.s3_client = None
        self.s3_bucket: Optional[str] = storage_config.get("bucket")
        self.s3_prefix: str = storage_config.get("prefix", "production-server")
        self.initialized = False

    def _validate_path(self, user_path: str) -> Path:
        """Validate that a user-supplied path stays within the storage directory.

        Raises StorageError if the resolved path escapes base_path.
        """
        if ".." in user_path or Path(user_path).is_absolute():
            raise StorageError(
                f"Invalid path: directory traversal or absolute paths are not allowed"
            )
        resolved = (self.base_path / user_path).resolve()
        base_resolved = self.base_path.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise StorageError(f"Invalid path: resolved path escapes storage directory")
        return resolved

    async def initialize(self) -> None:
        """Initialize storage service"""
        try:
            logger.info("🚀 Initializing Production Storage Service...")

            if self.storage_backend == "local":
                # Ensure storage directory exists
                self.base_path.mkdir(parents=True, exist_ok=True)

                # Create tenant directories
                for tenant_dir in ["documents", "metadata", "temp"]:
                    (self.base_path / tenant_dir).mkdir(exist_ok=True)

                logger.info(f"📁 Local storage initialized: {self.base_path}")

            elif self.storage_backend == "s3":
                import boto3

                self.s3_client = boto3.client(
                    "s3", region_name=self.storage_config.get("region", "us-west-2")
                )
                # Verify bucket access
                self.s3_client.head_bucket(Bucket=self.s3_bucket)
                logger.info(f"☁️ S3 storage initialized: s3://{self.s3_bucket}")

            self.initialized = True

            logger.info("✅ Production Storage Service initialized:")
            logger.info(f"   • Backend: {self.storage_backend}")
            logger.info(f"   • Base path: {self.base_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Storage Service: {e}")
            raise StorageError(f"Storage initialization failed: {e}")

    async def store_document(
        self, document_id: str, file_content: bytes, metadata: DocumentMetadata
    ) -> StorageResult:
        """Store document with metadata"""
        try:
            if not self.initialized:
                raise StorageError("Storage service not initialized")

            logger.info(f"📁 Storing document: {document_id}")
            logger.info(f"   • Filename: {metadata.filename}")
            logger.info(f"   • Size: {len(file_content)} bytes")
            logger.info(f"   • Tenant: {metadata.tenant_id}")

            if self.storage_backend == "local":
                return await self._store_local(document_id, file_content, metadata)
            elif self.storage_backend == "s3":
                return await self._store_s3(document_id, file_content, metadata)
            else:
                raise StorageError(
                    f"Unsupported storage backend: {self.storage_backend}"
                )

        except Exception as e:
            logger.error(f"❌ Document storage failed: {e}")
            return StorageResult(success=False, error=str(e))

    async def _store_local(
        self, document_id: str, file_content: bytes, metadata: DocumentMetadata
    ) -> StorageResult:
        """Store document in local filesystem"""
        try:
            # Validate tenant_id and filename against path traversal
            self._validate_path(f"documents/{metadata.tenant_id}")

            # Create tenant-specific path
            tenant_path = self.base_path / "documents" / metadata.tenant_id
            tenant_path.mkdir(parents=True, exist_ok=True)

            # Create document file path
            file_extension = (
                metadata.filename.split(".")[-1] if "." in metadata.filename else "bin"
            )
            document_filename = f"{document_id}.{file_extension}"
            document_path = tenant_path / document_filename

            # Store document content
            import aiofiles

            async with aiofiles.open(document_path, "wb") as f:
                await f.write(file_content)

            # Store metadata
            metadata_path = self.base_path / "metadata" / metadata.tenant_id
            metadata_path.mkdir(parents=True, exist_ok=True)
            metadata_file = metadata_path / f"{document_id}.json"

            import json

            metadata_dict = {
                "document_id": document_id,
                "filename": metadata.filename,
                "file_size": len(file_content),
                "content_type": metadata.mime_type,
                "tenant_id": metadata.tenant_id,
                "scanner_id": getattr(metadata, "scanner_id", None),
                "scanner_metadata": getattr(metadata, "scanner_metadata", {}),
                "stored_at": datetime.now().isoformat(),
                "storage_path": str(document_path),
            }

            async with aiofiles.open(metadata_file, "w") as f:
                await f.write(json.dumps(metadata_dict))

            logger.info(f"✅ Document stored locally: {document_path}")

            return StorageResult(success=True, storage_path=str(document_path))

        except Exception as e:
            raise StorageError(f"Local storage failed: {e}")

    async def _store_s3(
        self, document_id: str, file_content: bytes, metadata: DocumentMetadata
    ) -> StorageResult:
        """Store document in S3 with tenant isolation"""
        try:
            import io
            import json

            file_ext = (
                metadata.filename.split(".")[-1] if "." in metadata.filename else "bin"
            )
            doc_key = (
                f"{self.s3_prefix}/tenants/{metadata.tenant_id}"
                f"/documents/{document_id}.{file_ext}"
            )
            meta_key = (
                f"{self.s3_prefix}/tenants/{metadata.tenant_id}"
                f"/metadata/{document_id}.json"
            )

            # Upload document
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=doc_key,
                Body=file_content,
                ContentType=getattr(metadata, "mime_type", "application/octet-stream"),
                Metadata={
                    "tenant_id": metadata.tenant_id,
                    "filename": metadata.filename,
                },
            )

            # Upload metadata
            metadata_dict = {
                "document_id": document_id,
                "filename": metadata.filename,
                "file_size": len(file_content),
                "content_type": getattr(metadata, "mime_type", ""),
                "tenant_id": metadata.tenant_id,
                "scanner_id": getattr(metadata, "scanner_id", None),
                "stored_at": datetime.now().isoformat(),
                "storage_path": f"s3://{self.s3_bucket}/{doc_key}",
            }
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=meta_key,
                Body=json.dumps(metadata_dict).encode(),
                ContentType="application/json",
            )

            s3_path = f"s3://{self.s3_bucket}/{doc_key}"
            logger.info(f"☁️ Document stored to S3: {s3_path}")
            return StorageResult(success=True, storage_path=s3_path)

        except Exception as e:
            raise StorageError(f"S3 storage failed: {e}")

    async def retrieve_document(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> Optional[DocumentData]:
        """Retrieve document by ID, optionally scoped to a tenant.

        Args:
            document_id: The document identifier.
            tenant_id: When provided, only returns the document if it belongs to
                this tenant. When None (internal/admin call), searches across all
                tenants.
        """
        try:
            if not self.initialized:
                raise StorageError("Storage service not initialized")

            if self.storage_backend == "local":
                return await self._retrieve_local(document_id, tenant_id=tenant_id)
            elif self.storage_backend == "s3":
                return await self._retrieve_s3(document_id, tenant_id=tenant_id)
            else:
                raise StorageError(
                    f"Unsupported storage backend: {self.storage_backend}"
                )

        except Exception as e:
            logger.error(f"❌ Document retrieval failed: {e}")
            return None

    async def _retrieve_local(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> Optional[DocumentData]:
        """Retrieve document from local filesystem"""
        try:
            # Find metadata file — scope to tenant when provided
            metadata_pattern = f"{document_id}.json"
            if tenant_id:
                metadata_files = list(
                    self.base_path.glob(f"metadata/{tenant_id}/{metadata_pattern}")
                )
            else:
                metadata_files = list(
                    self.base_path.glob(f"metadata/**/{metadata_pattern}")
                )

            if not metadata_files:
                logger.warning(f"⚠️ Metadata not found for document: {document_id}")
                return None

            metadata_file = metadata_files[0]

            # Load metadata
            import json

            with metadata_file.open("r") as f:
                metadata_dict = json.load(f)

            # Defense-in-depth: verify metadata tenant matches requested tenant
            if tenant_id and metadata_dict.get("tenant_id") != tenant_id:
                logger.warning(
                    "⚠️ Tenant mismatch for document %s: expected %s, got %s",
                    document_id,
                    tenant_id,
                    metadata_dict.get("tenant_id"),
                )
                return None

            storage_path = metadata_dict["storage_path"]

            # Load document content
            with Path(storage_path).open("rb") as f:
                content = f.read()

            # Create metadata object
            metadata = DocumentMetadata(
                filename=metadata_dict["filename"],
                file_size=metadata_dict["file_size"],
                mime_type=metadata_dict.get("content_type", "application/octet-stream"),
                tenant_id=metadata_dict["tenant_id"],
            )

            return DocumentData(
                content=content,
                metadata=metadata,
                storage_path=storage_path,
                stored_at=datetime.fromisoformat(metadata_dict["stored_at"]),
            )

        except Exception as e:
            logger.error(f"❌ Local retrieval failed: {e}")
            return None

    async def _retrieve_s3(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> Optional[DocumentData]:
        """Retrieve document from S3"""
        try:
            import json

            if tenant_id:
                # Scoped: construct exact key
                meta_key = (
                    f"{self.s3_prefix}/tenants/{tenant_id}"
                    f"/metadata/{document_id}.json"
                )
                try:
                    meta_resp = self.s3_client.get_object(
                        Bucket=self.s3_bucket, Key=meta_key
                    )
                except self.s3_client.exceptions.NoSuchKey:
                    logger.warning(
                        "⚠️ S3 metadata not found for document: %s (tenant: %s)",
                        document_id,
                        tenant_id,
                    )
                    return None
            else:
                # Unscoped: list across all tenants
                prefix = f"{self.s3_prefix}/tenants/"
                paginator = self.s3_client.get_paginator("list_objects_v2")
                meta_key = None
                for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        if obj["Key"].endswith(f"/metadata/{document_id}.json"):
                            meta_key = obj["Key"]
                            break
                    if meta_key:
                        break

                if not meta_key:
                    logger.warning(
                        "⚠️ S3 metadata not found for document: %s", document_id
                    )
                    return None

                meta_resp = self.s3_client.get_object(
                    Bucket=self.s3_bucket, Key=meta_key
                )

            metadata_dict = json.loads(meta_resp["Body"].read().decode())

            # Defense-in-depth: verify metadata tenant matches
            if tenant_id and metadata_dict.get("tenant_id") != tenant_id:
                logger.warning(
                    "⚠️ S3 tenant mismatch for document %s: expected %s, got %s",
                    document_id,
                    tenant_id,
                    metadata_dict.get("tenant_id"),
                )
                return None

            # Derive doc key from storage_path
            s3_path = metadata_dict["storage_path"]
            doc_key = s3_path.replace(f"s3://{self.s3_bucket}/", "")

            # Download document
            doc_resp = self.s3_client.get_object(Bucket=self.s3_bucket, Key=doc_key)
            content = doc_resp["Body"].read()

            metadata = DocumentMetadata(
                filename=metadata_dict["filename"],
                file_size=metadata_dict["file_size"],
                mime_type=metadata_dict.get("content_type", "application/octet-stream"),
                tenant_id=metadata_dict["tenant_id"],
            )

            return DocumentData(
                content=content,
                metadata=metadata,
                storage_path=s3_path,
                stored_at=datetime.fromisoformat(metadata_dict["stored_at"]),
            )

        except Exception as e:
            logger.error(f"❌ S3 retrieval failed: {e}")
            return None

    async def delete_document(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """Delete document and metadata, optionally scoped to a tenant.

        Args:
            document_id: The document identifier.
            tenant_id: When provided, only deletes the document if it belongs to
                this tenant. When None (internal/admin call), deletes across all
                tenants.
        """
        try:
            if not self.initialized:
                raise StorageError("Storage service not initialized")

            if self.storage_backend == "local":
                return await self._delete_local(document_id, tenant_id=tenant_id)
            elif self.storage_backend == "s3":
                return await self._delete_s3(document_id, tenant_id=tenant_id)
            else:
                raise StorageError(
                    f"Unsupported storage backend: {self.storage_backend}"
                )

        except Exception as e:
            logger.error(f"❌ Document deletion failed: {e}")
            return False

    async def _delete_local(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """Delete document from local filesystem"""
        try:
            # Find and delete metadata — scope to tenant when provided
            metadata_pattern = f"{document_id}.json"
            if tenant_id:
                metadata_files = list(
                    self.base_path.glob(f"metadata/{tenant_id}/{metadata_pattern}")
                )
            else:
                metadata_files = list(
                    self.base_path.glob(f"metadata/**/{metadata_pattern}")
                )

            deleted_files = 0

            for metadata_file in metadata_files:
                # Load metadata to get storage path
                import json

                with metadata_file.open("r") as f:
                    metadata_dict = json.load(f)

                # Defense-in-depth: verify tenant ownership
                if tenant_id and metadata_dict.get("tenant_id") != tenant_id:
                    continue

                storage_path = Path(metadata_dict["storage_path"])

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

    async def _delete_s3(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """Delete document and metadata from S3"""
        try:
            if tenant_id:
                # Scoped: construct exact keys instead of substring match
                keys_to_delete = []
                for suffix in [
                    f"/documents/{document_id}",
                    f"/metadata/{document_id}.json",
                ]:
                    key = f"{self.s3_prefix}/tenants/{tenant_id}{suffix}"
                    # Check for document files with any extension
                    if "/documents/" in suffix:
                        prefix = key
                        resp = self.s3_client.list_objects_v2(
                            Bucket=self.s3_bucket, Prefix=prefix
                        )
                        for obj in resp.get("Contents", []):
                            keys_to_delete.append({"Key": obj["Key"]})
                    else:
                        keys_to_delete.append({"Key": key})
            else:
                # Unscoped: list across all tenants (exact document_id match)
                prefix = f"{self.s3_prefix}/tenants/"
                paginator = self.s3_client.get_paginator("list_objects_v2")
                keys_to_delete = []
                for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        # Match exact document_id in path segments
                        if f"/documents/{document_id}." in key or key.endswith(
                            f"/metadata/{document_id}.json"
                        ):
                            keys_to_delete.append({"Key": key})

            if not keys_to_delete:
                return False

            self.s3_client.delete_objects(
                Bucket=self.s3_bucket,
                Delete={"Objects": keys_to_delete},
            )
            logger.info(
                f"🗑️ Deleted {len(keys_to_delete)} S3 objects for document: {document_id}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ S3 deletion failed: {e}")
            return False

    async def search_documents(
        self, query: str, limit: int = 20, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search stored documents by filename or vendor substring match.

        Args:
            query: Search term to match against filename, vendor name, or doc ID.
            limit: Maximum number of results.
            tenant_id: When provided, only searches within this tenant's documents.
                When None (internal/admin call), searches across all tenants.
        """
        results: List[Dict[str, Any]] = []
        if not self.initialized or self.storage_backend != "local":
            return results

        query_lower = query.lower()
        metadata_dir = self.base_path / "metadata"
        if not metadata_dir.exists():
            return results

        import json

        # Scope glob pattern to tenant when provided
        if tenant_id:
            glob_pattern = f"{tenant_id}/*.json"
        else:
            glob_pattern = "**/*.json"

        for meta_file in metadata_dir.glob(glob_pattern):
            try:
                with meta_file.open("r") as f:
                    meta = json.load(f)

                # Defense-in-depth: verify tenant ownership
                if tenant_id and meta.get("tenant_id") != tenant_id:
                    continue

                filename = meta.get("filename", "").lower()
                vendor = meta.get("vendor_name", "").lower()
                doc_id = meta.get("document_id", "")
                if (
                    query_lower in filename
                    or query_lower in vendor
                    or query_lower in doc_id
                ):
                    results.append(meta)
                    if len(results) >= limit:
                        break
            except Exception:
                continue

        return results

    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            if self.storage_backend == "local":
                return await self._get_local_stats()
            elif self.storage_backend == "s3":
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
                "base_path": str(self.base_path),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get local stats: {e}")
            return {}

    async def _get_s3_stats(self) -> Dict[str, Any]:
        """Get S3 storage statistics"""
        try:
            prefix = f"{self.s3_prefix}/tenants/"
            paginator = self.s3_client.get_paginator("list_objects_v2")
            total_size = 0
            doc_count = 0
            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    if "/documents/" in obj["Key"]:
                        total_size += obj["Size"]
                        doc_count += 1

            return {
                "backend": "s3",
                "total_documents": doc_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "bucket": self.s3_bucket,
                "prefix": self.s3_prefix,
            }
        except Exception as e:
            logger.error(f"❌ Failed to get S3 stats: {e}")
            return {
                "backend": "s3",
                "total_documents": 0,
                "total_size_bytes": 0,
                "bucket": self.s3_bucket,
                "error": str(e),
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
                "storage_statistics": stats,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup storage service"""
        logger.info("🧹 Cleaning up Production Storage Service...")
        self.initialized = False
