"""
ASR Systems - API Components
Shared API schemas and client for inter-system communication
"""

from .client import *
from .schemas import *

__all__ = [
    # Request schemas
    "DocumentUploadSchema",
    "ClassificationRequestSchema",
    "BatchProcessingRequestSchema",
    "ScannerRegistrationSchema",
    "ScannerHeartbeatSchema",
    "RoutingOverrideSchema",
    # Response schemas
    "DocumentUploadResponseSchema",
    "ClassificationResponseSchema",
    "RoutingResponseSchema",
    "BatchProcessingResponseSchema",
    "ScannerDiscoveryResponseSchema",
    "ScannerStatusResponseSchema",
    "DocumentListResponseSchema",
    "SystemHealthResponseSchema",
    "GLAccountListResponseSchema",
    "PaymentDetectionResponseSchema",
    # Error schemas
    "ErrorDetailSchema",
    "APIErrorResponseSchema",
    "ValidationErrorResponseSchema",
    # Success wrapper
    "APISuccessResponseSchema",
    # Utility schemas
    "PaginationSchema",
    "DocumentFilterSchema",
    # Clients
    "APIClient",
    "ProductionServerClient",
    "DocumentScannerClient",
]
