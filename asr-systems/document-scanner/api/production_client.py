"""
Production Server Client
API client for communicating with ASR Production Server
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiohttp
import aiofiles

# Import shared components
from shared.core.models import DocumentMetadata, UploadResult, GLClassificationResult, PaymentConsensusResult
from shared.core.exceptions import NetworkError, ValidationError
from shared.api.schemas import DocumentUploadSchema, ClassificationResponseSchema

# Import scanner config
from ..config.scanner_settings import scanner_settings

logger = logging.getLogger(__name__)


class ProductionServerClient:
    """
    Client for communicating with ASR Production Server

    Features:
    - Document upload with progress tracking
    - Classification and routing requests
    - Server health monitoring
    - Authentication management
    - Retry logic with exponential backoff
    - Heartbeat and connectivity monitoring
    """

    def __init__(self):
        self.server_url: Optional[str] = None
        self.api_key: Optional[str] = None
        self.connected = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_heartbeat: Optional[datetime] = None
        self.server_info: Dict[str, Any] = {}

    async def connect(self, server_url: str, api_key: Optional[str] = None) -> bool:
        """Connect to production server"""
        try:
            logger.info(f"🔌 Connecting to production server: {server_url}")

            self.server_url = server_url.rstrip('/')
            self.api_key = api_key or scanner_settings.api_key

            # Create HTTP session
            timeout = aiohttp.ClientTimeout(
                total=scanner_settings.connection_timeout,
                sock_read=scanner_settings.read_timeout
            )

            headers = {
                'User-Agent': 'ASR-Document-Scanner/2.0.0',
                'Accept': 'application/json',
            }

            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=scanner_settings.max_connections)
            )

            # Test connection and get server info
            server_info = await self._get_server_info()

            if server_info:
                self.server_info = server_info
                self.connected = True
                self.last_heartbeat = datetime.now()

                logger.info(f"✅ Connected to production server:")
                logger.info(f"   • Name: {server_info.get('name', 'Unknown')}")
                logger.info(f"   • Version: {server_info.get('version', 'Unknown')}")
                logger.info(f"   • Capabilities: {', '.join(server_info.get('capabilities', []))}")

                return True
            else:
                logger.error("❌ Failed to get server information")
                await self.disconnect()
                return False

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            await self.disconnect()
            return False

    async def disconnect(self) -> None:
        """Disconnect from production server"""
        try:
            if self.session:
                await self.session.close()
                self.session = None

            self.connected = False
            self.server_url = None
            self.server_info = {}
            self.last_heartbeat = None

            logger.info("🔌 Disconnected from production server")

        except Exception as e:
            logger.warning(f"⚠️ Disconnect error: {e}")

    async def _get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information and capabilities"""
        try:
            if not self.session:
                return None

            # Check health endpoint
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status != 200:
                    return None

                health_data = await response.json()

            # Get API info
            async with self.session.get(f"{self.server_url}/api/info") as response:
                if response.status == 200:
                    api_info = await response.json()
                else:
                    api_info = {}

            # Check scanner endpoints specifically
            scanner_capabilities = await self._check_scanner_endpoints()

            return {
                "name": api_info.get("name", "ASR Production Server"),
                "version": api_info.get("version", "unknown"),
                "health_status": health_data.get("status", "unknown"),
                "capabilities": api_info.get("capabilities", []) + scanner_capabilities,
                "gl_accounts_count": api_info.get("gl_accounts_count", 0),
                "supported_formats": api_info.get("supported_formats", []),
                "max_file_size_mb": api_info.get("max_file_size_mb", 50)
            }

        except Exception as e:
            logger.warning(f"⚠️ Failed to get server info: {e}")
            return None

    async def _check_scanner_endpoints(self) -> List[str]:
        """Check availability of scanner-specific endpoints"""
        capabilities = []

        try:
            if not self.session:
                return capabilities

            # Check scanner registration endpoint
            async with self.session.get(f"{self.server_url}/api/scanner/discovery") as response:
                if response.status == 200:
                    capabilities.append("scanner_discovery")

            # Check upload endpoint
            async with self.session.get(f"{self.server_url}/api/scanner/upload", allow_redirects=False) as response:
                if response.status in [200, 405, 501]:  # Endpoint exists
                    capabilities.append("scanner_upload")

            # Check batch endpoint
            async with self.session.get(f"{self.server_url}/api/scanner/batch", allow_redirects=False) as response:
                if response.status in [200, 405, 501]:  # Endpoint exists
                    capabilities.append("batch_upload")

        except Exception:
            pass

        return capabilities

    async def upload_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> UploadResult:
        """Upload document to production server"""
        try:
            if not self.connected or not self.session:
                raise NetworkError("Not connected to production server")

            if not file_path.exists():
                raise ValidationError(f"File not found: {file_path}")

            logger.info(f"📤 Uploading document: {file_path.name}")

            # Prepare upload data
            upload_data = aiohttp.FormData()

            # Add file
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
                upload_data.add_field('file',
                                     file_content,
                                     filename=file_path.name,
                                     content_type='application/octet-stream')

            # Add metadata if provided
            if metadata:
                upload_data.add_field('metadata', json.dumps(metadata))

            # Add scanner identification
            scanner_info = {
                'scanner_id': 'asr_scanner_client',
                'scanner_version': '2.0.0',
                'upload_timestamp': datetime.now().isoformat()
            }
            upload_data.add_field('scanner_info', json.dumps(scanner_info))

            # Perform upload with retry logic
            result = await self._upload_with_retry(upload_data, file_path.name)

            if result.success:
                logger.info(f"✅ Upload successful: {file_path.name}")
                logger.info(f"   • Document ID: {result.document_id}")
                logger.info(f"   • Processing Status: {result.processing_status}")
            else:
                logger.error(f"❌ Upload failed: {result.error_message}")

            return result

        except Exception as e:
            logger.error(f"❌ Document upload failed: {e}")
            return UploadResult(
                success=False,
                error_message=str(e),
                document_id=None
            )

    async def _upload_with_retry(self, upload_data: aiohttp.FormData, filename: str) -> UploadResult:
        """Upload with retry logic"""
        max_retries = scanner_settings.retry_attempts
        retry_delay = scanner_settings.retry_delay

        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(
                    f"{self.server_url}/api/scanner/upload",
                    data=upload_data
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        return UploadResult(
                            success=True,
                            document_id=result_data.get('document_id'),
                            processing_status=result_data.get('status', 'uploaded'),
                            classification_result=result_data.get('classification'),
                            processing_time_ms=result_data.get('processing_time_ms', 0)
                        )
                    elif response.status == 413:
                        return UploadResult(
                            success=False,
                            error_message="File too large",
                            document_id=None
                        )
                    elif response.status == 400:
                        error_data = await response.json()
                        return UploadResult(
                            success=False,
                            error_message=error_data.get('message', 'Invalid request'),
                            document_id=None
                        )
                    else:
                        # Server error - retry
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        else:
                            return UploadResult(
                                success=False,
                                error_message=f"Server error: {response.status}",
                                document_id=None
                            )

            except aiohttp.ClientError as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️ Upload attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return UploadResult(
                        success=False,
                        error_message=f"Connection error: {e}",
                        document_id=None
                    )

        return UploadResult(
            success=False,
            error_message="Maximum retry attempts exceeded",
            document_id=None
        )

    async def get_document_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status of uploaded document"""
        try:
            if not self.connected or not self.session:
                return None

            async with self.session.get(f"{self.server_url}/api/scanner/status/{document_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"⚠️ Failed to get document status: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return None

    async def get_processing_result(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get full processing result for document"""
        try:
            if not self.connected or not self.session:
                return None

            async with self.session.get(f"{self.server_url}/api/documents/{document_id}/result") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to get processing result: {e}")
            return None

    async def batch_upload(self, file_paths: List[Path], metadata: Optional[Dict[str, Any]] = None) -> List[UploadResult]:
        """Upload multiple documents in batch"""
        try:
            if not self.connected or not self.session:
                raise NetworkError("Not connected to production server")

            logger.info(f"📤 Starting batch upload: {len(file_paths)} files")

            results = []

            # Process files in batches
            batch_size = scanner_settings.batch_upload_size
            for i in range(0, len(file_paths), batch_size):
                batch_files = file_paths[i:i + batch_size]

                # Upload files concurrently within batch
                batch_tasks = [
                    self.upload_document(file_path, metadata)
                    for file_path in batch_files
                ]

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Process batch results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        results.append(UploadResult(
                            success=False,
                            error_message=str(result),
                            document_id=None
                        ))
                    else:
                        results.append(result)

                # Brief pause between batches
                if i + batch_size < len(file_paths):
                    await asyncio.sleep(1)

            successful_uploads = len([r for r in results if r.success])
            logger.info(f"✅ Batch upload complete: {successful_uploads}/{len(file_paths)} successful")

            return results

        except Exception as e:
            logger.error(f"❌ Batch upload failed: {e}")
            return [UploadResult(
                success=False,
                error_message=str(e),
                document_id=None
            ) for _ in file_paths]

    async def heartbeat(self) -> bool:
        """Send heartbeat to maintain connection"""
        try:
            if not self.connected or not self.session:
                return False

            # Only send heartbeat if enough time has passed
            if self.last_heartbeat:
                time_since_heartbeat = datetime.now() - self.last_heartbeat
                if time_since_heartbeat.total_seconds() < scanner_settings.heartbeat_interval:
                    return True

            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    self.last_heartbeat = datetime.now()
                    return True
                else:
                    logger.warning(f"⚠️ Heartbeat failed: {response.status}")
                    return False

        except Exception as e:
            logger.warning(f"⚠️ Heartbeat error: {e}")
            return False

    async def register_scanner(self) -> bool:
        """Register this scanner with the production server"""
        try:
            if not self.connected or not self.session:
                return False

            registration_data = {
                'scanner_id': 'asr_scanner_client',
                'scanner_name': 'ASR Document Scanner',
                'version': '2.0.0',
                'capabilities': ['document_upload', 'batch_upload', 'offline_queue'],
                'registered_at': datetime.now().isoformat()
            }

            async with self.session.post(
                f"{self.server_url}/api/scanner/register",
                json=registration_data
            ) as response:
                if response.status == 200:
                    logger.info("✅ Scanner registered with production server")
                    return True
                else:
                    logger.warning(f"⚠️ Scanner registration failed: {response.status}")
                    return False

        except Exception as e:
            logger.warning(f"⚠️ Scanner registration error: {e}")
            return False

    async def get_server_capabilities(self) -> List[str]:
        """Get list of server capabilities"""
        return self.server_info.get('capabilities', [])

    async def get_gl_accounts(self) -> Optional[List[Dict[str, Any]]]:
        """Get available GL accounts from production server"""
        try:
            if not self.connected or not self.session:
                return None

            async with self.session.get(f"{self.server_url}/api/gl-accounts") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"❌ Failed to get GL accounts: {e}")
            return None

    async def get_health(self) -> Dict[str, Any]:
        """Get client health status"""
        try:
            return {
                "status": "healthy" if self.connected else "disconnected",
                "server_url": self.server_url,
                "connected": self.connected,
                "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                "server_info": self.server_info,
                "session_active": self.session is not None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def cleanup(self) -> None:
        """Cleanup production client"""
        logger.info("🧹 Cleaning up Production Server Client...")
        await self.disconnect()