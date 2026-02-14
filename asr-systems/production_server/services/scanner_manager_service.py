"""
Scanner Manager Service
Manages scanner client connections and communication
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from shared.core.exceptions import NetworkError, ValidationError

# Import shared components
from shared.core.models import DocumentMetadata, ScannerConfiguration, UploadResult

logger = logging.getLogger(__name__)


@dataclass
class ConnectedScanner:
    """Connected scanner client information"""

    scanner_id: str
    name: str
    version: str
    capabilities: List[str]
    ip_address: str
    connected_at: datetime
    last_heartbeat: datetime
    tenant_id: Optional[str] = None
    upload_count: int = 0
    status: str = "active"


@dataclass
class ScannerUploadRequest:
    """Scanner upload request"""

    scanner_id: str
    filename: str
    file_content: bytes
    metadata: Optional[Dict[str, Any]] = None
    scanner_info: Optional[Dict[str, Any]] = None


class ScannerManagerService:
    """
    Service for managing scanner client connections and operations

    Features:
    - Scanner registration and authentication
    - Heartbeat monitoring
    - Upload tracking and load balancing
    - Scanner capability management
    - Connection health monitoring
    """

    def __init__(self, max_clients: int = 100):
        self.max_clients = max_clients
        self.connected_scanners: Dict[str, ConnectedScanner] = {}
        self.upload_sessions: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_timeout = 300  # 5 minutes
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize scanner manager service"""
        try:
            logger.info("🚀 Initializing Scanner Manager Service...")

            # Start heartbeat monitoring task
            asyncio.create_task(self._monitor_heartbeats())

            # Start cleanup task
            asyncio.create_task(self._cleanup_stale_sessions())

            self.initialized = True

            logger.info(f"✅ Scanner Manager Service initialized:")
            logger.info(f"   • Max clients: {self.max_clients}")
            logger.info(f"   • Heartbeat timeout: {self.heartbeat_timeout}s")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Scanner Manager Service: {e}")
            raise

    async def register_scanner(
        self,
        scanner_id: str,
        name: str,
        version: str,
        capabilities: List[str],
        ip_address: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new scanner client"""
        try:
            if not self.initialized:
                raise NetworkError("Scanner manager service not initialized")

            # Check connection limits
            if len(self.connected_scanners) >= self.max_clients:
                raise NetworkError(
                    f"Maximum scanner clients exceeded ({self.max_clients})"
                )

            # Create scanner entry
            scanner = ConnectedScanner(
                scanner_id=scanner_id,
                name=name,
                version=version,
                capabilities=capabilities,
                ip_address=ip_address,
                connected_at=datetime.now(),
                last_heartbeat=datetime.now(),
                tenant_id=tenant_id,
                upload_count=0,
                status="active",
            )

            # Store in connected scanners
            self.connected_scanners[scanner_id] = scanner

            logger.info(f"✅ Scanner registered: {name} (ID: {scanner_id[:8]}...)")
            logger.info(f"   • Version: {version}")
            logger.info(f"   • IP: {ip_address}")
            logger.info(f"   • Capabilities: {', '.join(capabilities)}")
            logger.info(f"   • Connected scanners: {len(self.connected_scanners)}")

            return {
                "status": "registered",
                "scanner_id": scanner_id,
                "server_capabilities": self._get_server_capabilities(),
                "upload_endpoints": {
                    "single": "/api/scanner/upload",
                    "batch": "/api/scanner/batch",
                    "status": "/api/scanner/status",
                },
                "heartbeat_interval": 30,
                "max_file_size_mb": 50,
            }

        except Exception as e:
            logger.error(f"❌ Scanner registration failed: {e}")
            raise

    async def update_heartbeat(
        self, scanner_id: str, status_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update scanner heartbeat"""
        try:
            if scanner_id not in self.connected_scanners:
                logger.warning(f"⚠️ Heartbeat from unknown scanner: {scanner_id}")
                return False

            scanner = self.connected_scanners[scanner_id]
            scanner.last_heartbeat = datetime.now()

            # Update scanner status if provided
            if status_data:
                scanner.upload_count = status_data.get(
                    "upload_count", scanner.upload_count
                )
                scanner.status = status_data.get("status", scanner.status)

            logger.debug(f"💓 Heartbeat updated: {scanner.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Heartbeat update failed: {e}")
            return False

    async def process_scanner_upload(
        self, upload_request: ScannerUploadRequest, document_processor_service
    ) -> UploadResult:
        """Process document upload from scanner"""
        try:
            scanner_id = upload_request.scanner_id

            # Validate scanner
            if scanner_id not in self.connected_scanners:
                raise ValidationError(f"Unknown scanner: {scanner_id}")

            scanner = self.connected_scanners[scanner_id]

            # Create upload session
            session_id = str(uuid4())
            self.upload_sessions[session_id] = {
                "scanner_id": scanner_id,
                "filename": upload_request.filename,
                "started_at": datetime.now(),
                "status": "processing",
                "tenant_id": scanner.tenant_id,
            }

            logger.info(f"📤 Processing upload from scanner: {scanner.name}")
            logger.info(f"   • File: {upload_request.filename}")
            logger.info(f"   • Size: {len(upload_request.file_content)} bytes")

            try:
                # Create document metadata
                metadata = DocumentMetadata(
                    filename=upload_request.filename,
                    file_size=len(upload_request.file_content),
                    mime_type=self._detect_content_type(upload_request.filename),
                    tenant_id=scanner.tenant_id or "default",
                    scanner_id=scanner_id,
                    gl_account=None,
                    vendor_name=None,
                    amount=None,
                    invoice_date=None,
                    routing_confidence=None,
                    storage_path=None,
                )

                # Process document using document processor service
                result = await document_processor_service.process_document(
                    file_content=upload_request.file_content, metadata=metadata
                )

                # Update upload session
                self.upload_sessions[session_id].update(
                    {
                        "status": "completed" if result.success else "failed",
                        "document_id": result.document_id,
                        "completed_at": datetime.now(),
                    }
                )

                # Update scanner stats
                scanner.upload_count += 1
                scanner.last_heartbeat = datetime.now()

                if result.success:
                    logger.info(
                        f"✅ Scanner upload completed: {upload_request.filename}"
                    )
                    logger.info(f"   • Document ID: {result.document_id}")
                else:
                    logger.error(f"❌ Scanner upload failed: {result.error_message}")

                return result  # type: ignore[no-any-return]

            except Exception as e:
                # Update upload session with error
                self.upload_sessions[session_id].update(
                    {"status": "error", "error": str(e), "completed_at": datetime.now()}
                )
                raise

        except Exception as e:
            logger.error(f"❌ Scanner upload processing failed: {e}")
            return UploadResult(
                success=False,
                error_message=str(e),
                document_id=None,
                classification_result=None,
            )

    async def process_batch_upload(
        self,
        scanner_id: str,
        upload_requests: List[ScannerUploadRequest],
        document_processor_service,
    ) -> List[UploadResult]:
        """Process batch upload from scanner"""
        try:
            if scanner_id not in self.connected_scanners:
                raise ValidationError(f"Unknown scanner: {scanner_id}")

            scanner = self.connected_scanners[scanner_id]
            logger.info(f"📤 Processing batch upload from scanner: {scanner.name}")
            logger.info(f"   • Files: {len(upload_requests)}")

            # Process uploads concurrently
            tasks = []
            for upload_request in upload_requests:
                upload_request.scanner_id = scanner_id  # Ensure scanner ID is set
                task = self.process_scanner_upload(
                    upload_request, document_processor_service
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to failed results
            processed_results: List[UploadResult] = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        UploadResult(
                            success=False,
                            error_message=str(result),
                            document_id=None,
                            classification_result=None,
                        )
                    )
                else:
                    processed_results.append(result)  # type: ignore[arg-type]

            successful_uploads = len([r for r in processed_results if r.success])
            logger.info(
                f"✅ Batch upload completed: {successful_uploads}/{len(upload_requests)} successful"
            )

            return processed_results

        except Exception as e:
            logger.error(f"❌ Batch upload processing failed: {e}")
            return [
                UploadResult(
                    success=False,
                    error_message=str(e),
                    document_id=None,
                    classification_result=None,
                )
                for _ in upload_requests
            ]

    async def get_upload_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get upload session status"""
        try:
            if session_id not in self.upload_sessions:
                return None

            session = self.upload_sessions[session_id]

            # Calculate processing time
            processing_time = None
            if session.get("completed_at"):
                processing_time = (
                    session["completed_at"] - session["started_at"]
                ).total_seconds()

            return {
                "session_id": session_id,
                "scanner_id": session["scanner_id"],
                "filename": session["filename"],
                "status": session["status"],
                "started_at": session["started_at"].isoformat(),
                "completed_at": (
                    session.get("completed_at", datetime.now()).isoformat()
                    if session.get("completed_at")
                    else None
                ),
                "processing_time_seconds": processing_time,
                "document_id": session.get("document_id"),
                "error": session.get("error"),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get upload status: {e}")
            return None

    async def get_connected_scanners(self) -> List[Dict[str, Any]]:
        """Get list of connected scanners"""
        try:
            scanners = []
            for scanner in self.connected_scanners.values():
                scanners.append(
                    {
                        "scanner_id": scanner.scanner_id,
                        "name": scanner.name,
                        "version": scanner.version,
                        "capabilities": scanner.capabilities,
                        "ip_address": scanner.ip_address,
                        "connected_at": scanner.connected_at.isoformat(),
                        "last_heartbeat": scanner.last_heartbeat.isoformat(),
                        "upload_count": scanner.upload_count,
                        "status": scanner.status,
                        "tenant_id": scanner.tenant_id,
                    }
                )
            return scanners

        except Exception as e:
            logger.error(f"❌ Failed to get connected scanners: {e}")
            return []

    def disconnect_scanner(self, scanner_id: str) -> bool:
        """Disconnect a scanner"""
        try:
            if scanner_id in self.connected_scanners:
                scanner = self.connected_scanners[scanner_id]
                del self.connected_scanners[scanner_id]

                logger.info(
                    f"🔌 Scanner disconnected: {scanner.name} (ID: {scanner_id[:8]}...)"
                )
                logger.info(f"   • Connected scanners: {len(self.connected_scanners)}")
                return True
            else:
                logger.warning(
                    f"⚠️ Attempted to disconnect unknown scanner: {scanner_id}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Failed to disconnect scanner: {e}")
            return False

    def _get_server_capabilities(self) -> List[str]:
        """Get server capabilities for scanner registration"""
        return [
            "document_processing",
            "gl_account_classification",
            "payment_detection",
            "billing_routing",
            "audit_trails",
            "multi_tenant_support",
            "batch_upload",
            "real_time_status",
        ]

    def _detect_content_type(self, filename: str) -> str:
        """Detect content type from filename"""
        extension = filename.lower().split(".")[-1] if "." in filename else ""

        content_types = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "tiff": "image/tiff",
            "gif": "image/gif",
        }

        return content_types.get(extension, "application/octet-stream")

    async def _monitor_heartbeats(self) -> None:
        """Background task to monitor scanner heartbeats"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_time = datetime.now()
                stale_scanners = []

                for scanner_id, scanner in self.connected_scanners.items():
                    time_since_heartbeat = current_time - scanner.last_heartbeat

                    if time_since_heartbeat.total_seconds() > self.heartbeat_timeout:
                        stale_scanners.append(scanner_id)

                # Disconnect stale scanners
                for scanner_id in stale_scanners:
                    scanner = self.connected_scanners[scanner_id]
                    logger.warning(
                        f"⚠️ Scanner heartbeat timeout: {scanner.name} (ID: {scanner_id[:8]}...)"
                    )
                    self.disconnect_scanner(scanner_id)

            except Exception as e:
                logger.error(f"❌ Heartbeat monitoring error: {e}")

    async def _cleanup_stale_sessions(self) -> None:
        """Background task to cleanup old upload sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour

                current_time = datetime.now()
                stale_sessions = []

                for session_id, session in self.upload_sessions.items():
                    session_age = current_time - session["started_at"]

                    # Clean up sessions older than 24 hours
                    if session_age.total_seconds() > 86400:
                        stale_sessions.append(session_id)

                # Remove stale sessions
                for session_id in stale_sessions:
                    del self.upload_sessions[session_id]

                if stale_sessions:
                    logger.info(
                        f"🧹 Cleaned up {len(stale_sessions)} stale upload sessions"
                    )

            except Exception as e:
                logger.error(f"❌ Session cleanup error: {e}")

    async def get_health(self) -> Dict[str, Any]:
        """Get scanner manager health status"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            connected_count = len(self.connected_scanners)
            active_sessions = len(
                [
                    s
                    for s in self.upload_sessions.values()
                    if s["status"] == "processing"
                ]
            )

            return {
                "status": "healthy",
                "connected_scanners": connected_count,
                "max_clients": self.max_clients,
                "active_upload_sessions": active_sessions,
                "total_upload_sessions": len(self.upload_sessions),
                "heartbeat_timeout_seconds": self.heartbeat_timeout,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup scanner manager service"""
        logger.info("🧹 Cleaning up Scanner Manager Service...")

        # Disconnect all scanners
        for scanner_id in list(self.connected_scanners.keys()):
            self.disconnect_scanner(scanner_id)

        # Clear upload sessions
        self.upload_sessions.clear()

        self.initialized = False
