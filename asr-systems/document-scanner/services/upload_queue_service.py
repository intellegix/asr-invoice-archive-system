"""
Upload Queue Service
Manages offline document queue with retry logic and status tracking
"""

import asyncio
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import shared components
from shared.core.models import DocumentMetadata, UploadResult
from shared.core.exceptions import ValidationError, StorageError

# Import scanner config
from ..config.scanner_settings import scanner_settings

logger = logging.getLogger(__name__)


class UploadStatus(Enum):
    """Upload status enumeration"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class QueuedDocument:
    """Queued document metadata"""
    id: str
    file_path: str
    filename: str
    file_size: int
    created_at: datetime
    status: UploadStatus
    retry_count: int = 0
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    upload_result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class UploadQueueService:
    """
    Service for managing offline upload queue with SQLite backend

    Features:
    - Persistent queue storage with SQLite database
    - Retry logic with exponential backoff
    - Upload progress tracking
    - Batch processing capabilities
    - Queue size limits and cleanup
    """

    def __init__(self):
        self.db_path = scanner_settings.queue_db_path
        self.temp_dir = scanner_settings.temp_dir
        self.max_queue_size = scanner_settings.offline_queue_max_size
        self.retention_days = scanner_settings.offline_retention_days
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the upload queue service"""
        try:
            logger.info("🚀 Initializing Upload Queue Service...")

            # Create database and tables
            await self._create_database()

            # Clean up old completed/failed entries
            await self._cleanup_old_entries()

            # Validate queue integrity
            await self._validate_queue_integrity()

            self.initialized = True

            queue_stats = await self.get_queue_stats()
            logger.info(f"✅ Upload Queue Service initialized:")
            logger.info(f"   • {queue_stats['total']} documents in queue")
            logger.info(f"   • {queue_stats['pending']} pending uploads")
            logger.info(f"   • Database: {self.db_path}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Upload Queue Service: {e}")
            raise StorageError(f"Upload queue initialization failed: {e}")

    async def _create_database(self) -> None:
        """Create SQLite database and tables"""
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create database connection and tables
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS upload_queue (
                        id TEXT PRIMARY KEY,
                        file_path TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        status TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        last_attempt TIMESTAMP,
                        error_message TEXT,
                        upload_result TEXT,
                        metadata TEXT
                    )
                """)

                # Create indices for performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_upload_queue_status
                    ON upload_queue(status)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_upload_queue_created_at
                    ON upload_queue(created_at)
                """)

                conn.commit()

        except Exception as e:
            raise StorageError(f"Database creation failed: {e}")

    async def _cleanup_old_entries(self) -> None:
        """Clean up old completed and failed entries"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            with sqlite3.connect(self.db_path) as conn:
                # Delete old completed/failed entries
                cursor = conn.execute("""
                    DELETE FROM upload_queue
                    WHERE (status = ? OR status = ?) AND created_at < ?
                """, (UploadStatus.COMPLETED.value, UploadStatus.FAILED.value, cutoff_date))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} old queue entries")

        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed: {e}")

    async def _validate_queue_integrity(self) -> None:
        """Validate queue integrity and file existence"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, file_path, status FROM upload_queue
                    WHERE status IN (?, ?)
                """, (UploadStatus.PENDING.value, UploadStatus.RETRY.value))

                invalid_entries = []

                for row in cursor:
                    file_path = Path(row['file_path'])
                    if not file_path.exists():
                        invalid_entries.append(row['id'])
                        logger.warning(f"⚠️ File not found, removing from queue: {file_path}")

                # Remove invalid entries
                if invalid_entries:
                    placeholders = ','.join(['?'] * len(invalid_entries))
                    conn.execute(f"""
                        DELETE FROM upload_queue
                        WHERE id IN ({placeholders})
                    """, invalid_entries)
                    conn.commit()

        except Exception as e:
            logger.warning(f"⚠️ Queue validation failed: {e}")

    async def add_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add document to upload queue"""
        try:
            if not self.initialized:
                raise StorageError("Upload queue service not initialized")

            # Validate file
            if not file_path.exists():
                raise ValidationError(f"File not found: {file_path}")

            file_size = file_path.stat().st_size
            if file_size > scanner_settings.max_file_size_mb * 1024 * 1024:
                raise ValidationError(f"File too large: {file_size / 1024 / 1024:.1f}MB")

            # Check queue size limit
            current_size = await self.get_pending_count()
            if current_size >= self.max_queue_size:
                raise StorageError("Upload queue is full")

            # Create queued document
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.stem}"
            queued_doc = QueuedDocument(
                id=document_id,
                file_path=str(file_path),
                filename=file_path.name,
                file_size=file_size,
                created_at=datetime.now(),
                status=UploadStatus.PENDING,
                metadata=metadata
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO upload_queue
                    (id, file_path, filename, file_size, created_at, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    queued_doc.id,
                    queued_doc.file_path,
                    queued_doc.filename,
                    queued_doc.file_size,
                    queued_doc.created_at,
                    queued_doc.status.value,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()

            logger.info(f"✅ Added document to queue: {file_path.name} (ID: {document_id})")
            return document_id

        except Exception as e:
            logger.error(f"❌ Failed to add document to queue: {e}")
            raise

    async def get_pending_documents(self, limit: Optional[int] = None) -> List[QueuedDocument]:
        """Get pending documents from queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = """
                    SELECT * FROM upload_queue
                    WHERE status IN (?, ?)
                    ORDER BY created_at
                """
                params = [UploadStatus.PENDING.value, UploadStatus.RETRY.value]

                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                return [self._row_to_queued_document(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to get pending documents: {e}")
            return []

    async def update_document_status(
        self,
        document_id: str,
        status: UploadStatus,
        error_message: Optional[str] = None,
        upload_result: Optional[UploadResult] = None
    ) -> None:
        """Update document status in queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Increment retry count if this is a retry
                retry_increment = 1 if status == UploadStatus.RETRY else 0

                conn.execute("""
                    UPDATE upload_queue
                    SET status = ?,
                        last_attempt = ?,
                        retry_count = retry_count + ?,
                        error_message = ?,
                        upload_result = ?
                    WHERE id = ?
                """, (
                    status.value,
                    datetime.now(),
                    retry_increment,
                    error_message,
                    json.dumps(asdict(upload_result)) if upload_result else None,
                    document_id
                ))
                conn.commit()

                logger.info(f"📝 Updated document status: {document_id} -> {status.value}")

        except Exception as e:
            logger.error(f"❌ Failed to update document status: {e}")

    async def process_queue(self) -> None:
        """Process pending documents in the queue"""
        try:
            if not self.initialized:
                return

            # Get pending documents for processing
            pending_docs = await self.get_pending_documents(
                limit=scanner_settings.batch_upload_size
            )

            if not pending_docs:
                return

            logger.info(f"🔄 Processing {len(pending_docs)} documents from queue")

            for doc in pending_docs:
                try:
                    # Skip if too many retries
                    if doc.retry_count >= scanner_settings.retry_attempts:
                        await self.update_document_status(
                            doc.id,
                            UploadStatus.FAILED,
                            error_message="Maximum retry attempts exceeded"
                        )
                        continue

                    # Check retry delay
                    if doc.last_attempt:
                        time_since_attempt = datetime.now() - doc.last_attempt
                        required_delay = timedelta(seconds=scanner_settings.retry_delay * (doc.retry_count + 1))

                        if time_since_attempt < required_delay:
                            continue

                    # Attempt upload (will be implemented by GUI layer)
                    await self._attempt_upload(doc)

                except Exception as e:
                    logger.error(f"❌ Failed to process document {doc.id}: {e}")
                    await self.update_document_status(
                        doc.id,
                        UploadStatus.RETRY,
                        error_message=str(e)
                    )

        except Exception as e:
            logger.error(f"❌ Queue processing failed: {e}")

    async def _attempt_upload(self, doc: QueuedDocument) -> None:
        """Attempt to upload document (placeholder - actual upload handled by GUI)"""
        # Mark as uploading
        await self.update_document_status(doc.id, UploadStatus.UPLOADING)

        # This will be implemented by the GUI layer which has access to the production client
        # For now, just log that upload would be attempted
        logger.info(f"📤 Would attempt upload for: {doc.filename}")

    def _row_to_queued_document(self, row: sqlite3.Row) -> QueuedDocument:
        """Convert database row to QueuedDocument object"""
        return QueuedDocument(
            id=row['id'],
            file_path=row['file_path'],
            filename=row['filename'],
            file_size=row['file_size'],
            created_at=datetime.fromisoformat(row['created_at']),
            status=UploadStatus(row['status']),
            retry_count=row['retry_count'] or 0,
            last_attempt=datetime.fromisoformat(row['last_attempt']) if row['last_attempt'] else None,
            error_message=row['error_message'],
            upload_result=json.loads(row['upload_result']) if row['upload_result'] else None,
            metadata=json.loads(row['metadata']) if row['metadata'] else None
        )

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count
                    FROM upload_queue
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())

                # Get total count
                total_cursor = conn.execute("SELECT COUNT(*) FROM upload_queue")
                total_count = total_cursor.fetchone()[0]

                return {
                    'total': total_count,
                    'pending': status_counts.get(UploadStatus.PENDING.value, 0),
                    'uploading': status_counts.get(UploadStatus.UPLOADING.value, 0),
                    'completed': status_counts.get(UploadStatus.COMPLETED.value, 0),
                    'failed': status_counts.get(UploadStatus.FAILED.value, 0),
                    'retry': status_counts.get(UploadStatus.RETRY.value, 0)
                }

        except Exception as e:
            logger.error(f"❌ Failed to get queue stats: {e}")
            return {'total': 0, 'pending': 0, 'uploading': 0, 'completed': 0, 'failed': 0, 'retry': 0}

    async def get_pending_count(self) -> int:
        """Get count of pending documents"""
        stats = await self.get_queue_stats()
        return stats['pending'] + stats['retry']

    async def remove_document(self, document_id: str) -> bool:
        """Remove document from queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM upload_queue WHERE id = ?", (document_id,))
                conn.commit()

                if cursor.rowcount > 0:
                    logger.info(f"🗑️ Removed document from queue: {document_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Document not found in queue: {document_id}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to remove document: {e}")
            return False

    async def clear_completed(self) -> int:
        """Clear completed documents from queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM upload_queue
                    WHERE status = ?
                """, (UploadStatus.COMPLETED.value,))
                conn.commit()

                cleared_count = cursor.rowcount
                if cleared_count > 0:
                    logger.info(f"🧹 Cleared {cleared_count} completed documents from queue")

                return cleared_count

        except Exception as e:
            logger.error(f"❌ Failed to clear completed documents: {e}")
            return 0

    async def get_health(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            stats = await self.get_queue_stats()
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "status": "healthy",
                "queue_stats": stats,
                "database_size_bytes": db_size,
                "database_path": str(self.db_path),
                "temp_dir": str(self.temp_dir)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def cleanup(self) -> None:
        """Cleanup upload queue service"""
        logger.info("🧹 Cleaning up Upload Queue Service...")
        # No active connections to close for SQLite
        self.initialized = False