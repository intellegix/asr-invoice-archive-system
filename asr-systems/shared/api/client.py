"""
ASR Systems - Shared API Client
HTTP client for communication between Production Server and Document Scanner
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from pydantic import ValidationError

from ..core.constants import EXTERNAL_TIMEOUTS, MAX_RETRY_ATTEMPTS
from ..core.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    RetryableError,
)
from ..core.exceptions import ValidationError as ASRValidationError
from ..core.exceptions import (
    handle_exception,
)
from .schemas import (
    APIErrorResponseSchema,
    APISuccessResponseSchema,
    ClassificationRequestSchema,
    ClassificationResponseSchema,
    DocumentUploadResponseSchema,
    DocumentUploadSchema,
)

logger = logging.getLogger(__name__)


class APIClient:
    """
    Shared HTTP client for ASR system communication
    Handles authentication, retries, and error handling
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        tenant_id: str,
        timeout: int = EXTERNAL_TIMEOUTS.get("SCANNER_HEARTBEAT", 30),
        max_retries: int = MAX_RETRY_ATTEMPTS,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.timeout = timeout
        self.max_retries = max_retries

        # Create HTTP client with default headers
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-Tenant-ID": tenant_id,
                "User-Agent": "ASR-Systems-Client/2.0.0",
            },
        )

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def _get_request_id(self) -> str:
        """Generate unique request ID for tracking"""
        return f"req_{int(time.time()*1000)}"

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        request_id = self._get_request_id()

        # Merge custom headers with defaults
        request_headers = {}
        if headers:
            request_headers.update(headers)
        request_headers["X-Request-ID"] = request_id

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Making {method} request to {url} (attempt {attempt + 1})"
                )

                # Prepare request kwargs
                kwargs = {"headers": request_headers, "params": params}

                if files:
                    # For file uploads, don't set content-type (httpx will set multipart/form-data)
                    kwargs.pop("Content-Type", None)
                    kwargs["files"] = files
                    if data:
                        kwargs["data"] = data
                else:
                    # For JSON requests
                    if data:
                        kwargs["json"] = data

                response = await self.client.request(method, url, **kwargs)  # type: ignore[arg-type]

                # Check if we should retry based on status code
                if response.status_code >= 500 or response.status_code == 429:
                    if attempt < self.max_retries:
                        wait_time = 2**attempt  # Exponential backoff
                        logger.warning(
                            f"Request failed with status {response.status_code}, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                return response

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise NetworkError(
                        f"Network error after {self.max_retries} attempts: {e}", url=url
                    )

            except Exception as e:
                logger.error(f"Unexpected error on request attempt {attempt + 1}: {e}")
                if attempt < self.max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise handle_exception(e)

        # Should never reach here, but just in case
        raise APIError("Maximum retry attempts exceeded")

    def _handle_response_errors(self, response: httpx.Response) -> None:
        """Handle HTTP response errors"""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key or authentication failed")
        elif response.status_code == 403:
            raise AuthenticationError("Access forbidden - check tenant permissions")
        elif response.status_code == 404:
            raise APIError(f"Resource not found: {response.url}")
        elif response.status_code == 422:
            try:
                error_data = response.json()
                raise ASRValidationError(f"Validation error: {error_data}")
            except json.JSONDecodeError:
                raise ASRValidationError("Validation error occurred")
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RetryableError(f"Rate limit exceeded", retry_after=retry_after)
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get(
                    "message", f"HTTP {response.status_code} error"
                )
            except json.JSONDecodeError:
                message = f"HTTP {response.status_code} error"
            raise APIError(message, status_code=response.status_code)

    async def _parse_response(
        self, response: httpx.Response, expected_schema=None
    ) -> Any:
        """Parse response and handle errors"""
        self._handle_response_errors(response)

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {e}")

        # If we have an expected schema, validate the response
        if expected_schema:
            try:
                return expected_schema.parse_obj(data)
            except ValidationError as e:
                logger.error(f"Response validation failed: {e}")
                # Return raw data if validation fails (for debugging)
                return data

        return data

    # Health check methods

    async def check_health(self) -> Dict[str, Any]:
        """Check system health"""
        response = await self._make_request("GET", "/health")
        return await self._parse_response(response)  # type: ignore[no-any-return]

    # Document operations

    async def upload_document(
        self,
        file_path: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentUploadResponseSchema:
        """Upload a document file"""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = filename or file_path_obj.name
        file_size = file_path_obj.stat().st_size

        # Prepare upload request
        upload_request = DocumentUploadSchema(
            filename=filename,
            content_type="application/octet-stream",  # Will be detected by server
            file_size=file_size,
            tenant_id=self.tenant_id,
            scanner_id=None,
            metadata=metadata or {},
        )

        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            data = upload_request.dict()

            response = await self._make_request(
                "POST", "/api/v1/documents/upload", data=data, files=files
            )

        return await self._parse_response(response, DocumentUploadResponseSchema)  # type: ignore[no-any-return]

    async def upload_document_bytes(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentUploadResponseSchema:
        """Upload document from bytes"""
        upload_request = DocumentUploadSchema(
            filename=filename,
            content_type=content_type,
            file_size=len(file_data),
            tenant_id=self.tenant_id,
            scanner_id=None,
            metadata=metadata or {},
        )

        files = {"file": (filename, file_data, content_type)}
        data = upload_request.dict()

        response = await self._make_request(
            "POST", "/api/v1/documents/upload", data=data, files=files
        )

        return await self._parse_response(response, DocumentUploadResponseSchema)  # type: ignore[no-any-return]

    async def classify_document(
        self,
        document_id: str,
        force_reclassification: bool = False,
        preferred_gl_accounts: Optional[List[str]] = None,
    ) -> ClassificationResponseSchema:
        """Request document classification"""
        request_data = ClassificationRequestSchema(
            document_id=document_id,
            tenant_id=self.tenant_id,
            force_reclassification=force_reclassification,
            preferred_gl_accounts=preferred_gl_accounts,
            payment_detection_methods=None,
        )

        response = await self._make_request(
            "POST",
            f"/api/v1/documents/{document_id}/classify",
            data=request_data.dict(),
        )

        return await self._parse_response(response, ClassificationResponseSchema)  # type: ignore[no-any-return]

    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get document processing status"""
        response = await self._make_request(
            "GET", f"/api/v1/documents/{document_id}/status"
        )
        return await self._parse_response(response)  # type: ignore[no-any-return]

    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get document metadata"""
        response = await self._make_request("GET", f"/api/v1/documents/{document_id}")
        return await self._parse_response(response)  # type: ignore[no-any-return]

    # Scanner operations

    async def register_scanner(
        self, scanner_name: str, capabilities: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register scanner with production server"""
        data = {
            "scanner_name": scanner_name,
            "tenant_id": self.tenant_id,
            "api_key": self.api_key,
            "capabilities": capabilities or {},
        }

        response = await self._make_request(
            "POST", "/api/v1/scanner/register", data=data
        )
        return await self._parse_response(response)  # type: ignore[no-any-return]

    async def send_heartbeat(
        self,
        scanner_id: str,
        status: str,
        queued_documents: int = 0,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send scanner heartbeat"""
        data = {
            "scanner_id": scanner_id,
            "status": status,
            "queued_documents": queued_documents,
            "last_upload": datetime.utcnow().isoformat(),
            "metrics": metrics or {},
        }

        response = await self._make_request(
            "POST", "/api/v1/scanner/heartbeat", data=data
        )
        return await self._parse_response(response)  # type: ignore[no-any-return]

    async def discover_servers(self) -> List[Dict[str, Any]]:
        """Discover available production servers"""
        response = await self._make_request("GET", "/api/v1/scanner/discovery")
        data = await self._parse_response(response)
        return data.get("servers", [])  # type: ignore[no-any-return]

    # Batch operations

    async def batch_upload(
        self, file_paths: List[str], metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentUploadResponseSchema]:
        """Upload multiple documents"""
        results = []

        for file_path in file_paths:
            try:
                result = await self.upload_document(file_path, metadata=metadata)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
                # Continue with other files
                continue

        return results

    # GL Account operations

    async def get_gl_accounts(self) -> Dict[str, Any]:
        """Get available GL accounts for tenant"""
        response = await self._make_request("GET", "/api/v1/gl-accounts")
        return await self._parse_response(response)  # type: ignore[no-any-return]

    # System information

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information and capabilities"""
        response = await self._make_request("GET", "/api/v1/system/info")
        return await self._parse_response(response)  # type: ignore[no-any-return]


class ProductionServerClient(APIClient):
    """
    Client for Document Scanner to communicate with Production Server
    """

    def __init__(
        self, server_url: str, api_key: str, tenant_id: str, scanner_id: str, **kwargs
    ):
        super().__init__(server_url, api_key, tenant_id, **kwargs)
        self.scanner_id = scanner_id

    async def upload_from_scanner(
        self,
        file_path: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentUploadResponseSchema:
        """Upload document from scanner with scanner ID"""
        scanner_metadata = {"scanner_id": self.scanner_id}
        if metadata:
            scanner_metadata.update(metadata)

        return await self.upload_document(file_path, filename, scanner_metadata)


class DocumentScannerClient(APIClient):
    """
    Client for Production Server to communicate with Document Scanner
    """

    async def get_scanner_status(self) -> Dict[str, Any]:
        """Get scanner status"""
        response = await self._make_request("GET", "/status")
        return await self._parse_response(response)  # type: ignore[no-any-return]

    async def get_scanner_queue(self) -> Dict[str, Any]:
        """Get scanner queue status"""
        response = await self._make_request("GET", "/queue")
        return await self._parse_response(response)  # type: ignore[no-any-return]

    async def trigger_scanner_upload(self) -> Dict[str, Any]:
        """Trigger scanner to process its queue"""
        response = await self._make_request("POST", "/upload")
        return await self._parse_response(response)  # type: ignore[no-any-return]


# Export classes
__all__ = ["APIClient", "ProductionServerClient", "DocumentScannerClient"]
