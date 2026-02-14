"""
ASR Systems - Shared API Schemas
Common API schemas for communication between Production Server and Document Scanner
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from ..core.models import (
    BillingDestination,
    DocumentMetadata,
    PaymentConsensusResult,
    PaymentDetectionMethod,
    PaymentStatus,
    ProcessingStatus,
    SystemType,
)

# Document ID validation pattern — prevents path traversal in URL path params
DOCUMENT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def validate_document_id(document_id: str) -> str:
    """Validate a document ID against the safe pattern."""
    if not DOCUMENT_ID_PATTERN.match(document_id):
        raise ValueError(
            "Invalid document ID: must be 1-64 alphanumeric, hyphen, or underscore characters"
        )
    return document_id


# Auth Schemas


class AuthLoginRequestSchema(BaseModel):
    """Schema for login requests"""

    api_key: str = Field(..., min_length=1, description="API key for authentication")
    tenant_id: str = Field(default="default", description="Tenant identifier")


class AuthLoginResponseSchema(BaseModel):
    """Schema for login responses"""

    authenticated: bool = Field(..., description="Whether authentication succeeded")
    tenant_id: str = Field(..., description="Authenticated tenant")
    message: str = Field(..., description="Status message")
    server_version: str = Field(..., description="Server version")
    capabilities: Dict[str, Any] = Field(
        default_factory=dict, description="Server capabilities"
    )


class AuthMeResponseSchema(BaseModel):
    """Schema for current user info"""

    authenticated: bool = Field(..., description="Whether user is authenticated")
    tenant_id: str = Field(..., description="Current tenant")
    api_keys_required: bool = Field(
        ..., description="Whether API keys are required for auth"
    )


# API Request Schemas


class DocumentUploadSchema(BaseModel):
    """Schema for document upload requests"""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    tenant_id: str = Field(..., description="Tenant identifier")
    scanner_id: Optional[str] = Field(None, description="Scanner client ID")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        max_size = 25 * 1024 * 1024  # 25MB
        if v > max_size:
            raise ValueError(
                f"File size {v} exceeds maximum allowed size of {max_size} bytes"
            )
        return v


class ClassificationRequestSchema(BaseModel):
    """Schema for document classification requests"""

    document_id: str = Field(..., description="Document ID to classify")
    tenant_id: str = Field(..., description="Tenant identifier")
    force_reclassification: bool = Field(
        default=False, description="Force reclassification"
    )
    preferred_gl_accounts: Optional[List[str]] = Field(
        None, description="Tenant-preferred GL accounts"
    )
    payment_detection_methods: Optional[List[PaymentDetectionMethod]] = Field(
        None, description="Enabled payment methods"
    )


class BatchProcessingRequestSchema(BaseModel):
    """Schema for batch document processing"""

    document_ids: List[str] = Field(
        ..., min_length=1, max_length=50, description="Document IDs to process"
    )
    tenant_id: str = Field(..., description="Tenant identifier")
    priority: int = Field(
        default=5, ge=1, le=10, description="Processing priority (1=highest, 10=lowest)"
    )


class ScannerRegistrationSchema(BaseModel):
    """Schema for scanner registration requests"""

    scanner_name: str = Field(..., description="Human-readable scanner name")
    tenant_id: str = Field(..., description="Tenant identifier")
    api_key: str = Field(..., description="Authentication API key")
    capabilities: Dict[str, Any] = Field(
        default_factory=dict, description="Scanner capabilities"
    )


class ScannerHeartbeatSchema(BaseModel):
    """Schema for scanner heartbeat updates"""

    scanner_id: str = Field(..., description="Scanner identifier")
    status: str = Field(..., description="Scanner status")
    queued_documents: int = Field(
        default=0, ge=0, description="Number of queued documents"
    )
    last_upload: Optional[datetime] = Field(
        None, description="Last successful upload timestamp"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Scanner metrics"
    )


class RoutingOverrideSchema(BaseModel):
    """Schema for manual routing overrides"""

    document_id: str = Field(..., description="Document ID")
    new_destination: BillingDestination = Field(
        ..., description="New billing destination"
    )
    reason: str = Field(..., description="Reason for override")
    user_id: str = Field(..., description="User making the override")


# API Response Schemas


class DocumentUploadResponseSchema(BaseModel):
    """Schema for document upload responses"""

    document_id: str = Field(..., description="Unique document identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    upload_url: Optional[str] = Field(
        None, description="Pre-signed upload URL if needed"
    )
    processing_estimate: Optional[int] = Field(
        None, description="Estimated processing time in seconds"
    )
    message: str = Field(..., description="Status message")


class ClassificationResponseSchema(BaseModel):
    """Schema for classification results"""

    document_id: str = Field(..., description="Document identifier")
    classification_successful: bool = Field(
        ..., description="Whether classification succeeded"
    )

    # GL Account classification
    gl_account_code: Optional[str] = Field(None, description="Assigned GL account code")
    gl_account_name: Optional[str] = Field(None, description="GL account name")
    gl_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="GL classification confidence"
    )
    gl_reasoning: Optional[str] = Field(None, description="Reasoning for GL assignment")

    # Payment detection
    payment_status: Optional[PaymentStatus] = Field(
        None, description="Detected payment status"
    )
    payment_consensus: Optional[PaymentConsensusResult] = Field(
        None, description="Payment detection consensus"
    )

    # Document details
    vendor_name: Optional[str] = Field(None, description="Detected vendor name")
    amount: Optional[float] = Field(None, description="Invoice amount")
    invoice_date: Optional[datetime] = Field(None, description="Invoice date")

    # Processing metadata
    processing_time: float = Field(..., description="Processing time in seconds")
    classification_timestamp: datetime = Field(
        ..., description="When classification completed"
    )
    quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall quality score"
    )


class RoutingResponseSchema(BaseModel):
    """Schema for routing decision results"""

    document_id: str = Field(..., description="Document identifier")
    routing_successful: bool = Field(..., description="Whether routing succeeded")
    destination: Optional[BillingDestination] = Field(
        None, description="Selected billing destination"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Routing confidence"
    )
    reasoning: str = Field(..., description="Routing decision explanation")
    routing_factors: Dict[str, Any] = Field(
        ..., description="Factors considered in routing"
    )
    manual_review_required: bool = Field(
        default=False, description="Whether manual review is needed"
    )


class BatchProcessingResponseSchema(BaseModel):
    """Schema for batch processing results"""

    batch_id: str = Field(..., description="Batch identifier")
    total_documents: int = Field(..., description="Total documents in batch")
    successful_documents: int = Field(
        default=0, description="Successfully processed documents"
    )
    failed_documents: int = Field(default=0, description="Failed document processing")
    processing_status: ProcessingStatus = Field(..., description="Overall batch status")
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )
    individual_results: List[ClassificationResponseSchema] = Field(
        default_factory=list, description="Individual document results"
    )


class ScannerDiscoveryResponseSchema(BaseModel):
    """Schema for scanner discovery responses"""

    server_id: str = Field(..., description="Production server identifier")
    server_name: str = Field(..., description="Server display name")
    api_endpoint: str = Field(..., description="API endpoint URL")
    capabilities: List[str] = Field(..., description="Server capabilities")
    supported_file_types: List[str] = Field(..., description="Supported file types")
    max_file_size_mb: int = Field(..., description="Maximum file size in MB")
    version: str = Field(..., description="Server version")


class ScannerStatusResponseSchema(BaseModel):
    """Schema for scanner status responses"""

    scanner_id: str = Field(..., description="Scanner identifier")
    scanner_name: str = Field(..., description="Scanner display name")
    status: str = Field(..., description="Current scanner status")
    tenant_id: str = Field(..., description="Associated tenant")
    last_heartbeat: Optional[datetime] = Field(
        None, description="Last heartbeat timestamp"
    )
    documents_processed_today: int = Field(
        default=0, description="Documents processed today"
    )
    queue_length: int = Field(default=0, description="Current queue length")
    is_online: bool = Field(..., description="Whether scanner is currently online")


class DocumentListResponseSchema(BaseModel):
    """Schema for document listing responses"""

    documents: List[DocumentMetadata] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of matching documents")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Documents per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class SystemHealthResponseSchema(BaseModel):
    """Schema for system health responses"""

    system_type: SystemType = Field(..., description="Type of system")
    overall_status: str = Field(..., description="Overall health status")
    components: Dict[str, Dict[str, Any]] = Field(
        ..., description="Component health details"
    )
    metrics: Dict[str, Any] = Field(..., description="System metrics")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    timestamp: datetime = Field(..., description="Health check timestamp")


class GLAccountListResponseSchema(BaseModel):
    """Schema for GL account listing"""

    gl_accounts: List[Dict[str, Any]] = Field(..., description="Available GL accounts")
    total_count: int = Field(..., description="Total number of GL accounts")
    categories: Dict[str, List[str]] = Field(
        ..., description="GL accounts grouped by category"
    )


class PaymentDetectionResponseSchema(BaseModel):
    """Schema for payment detection analysis results"""

    document_id: str = Field(..., description="Document identifier")
    payment_status: PaymentStatus = Field(..., description="Detected payment status")
    consensus_result: PaymentConsensusResult = Field(
        ..., description="Consensus analysis"
    )
    individual_method_results: Dict[str, Any] = Field(
        ..., description="Results from each detection method"
    )
    processing_time: float = Field(..., description="Analysis processing time")
    quality_indicators: Dict[str, Any] = Field(
        ..., description="Quality assessment indicators"
    )


# Audit Log Schemas


class AuditLogEntrySchema(BaseModel):
    """Schema for a single audit log entry."""

    id: Optional[str] = Field(None, description="Audit entry ID")
    document_id: str = Field(..., description="Associated document ID")
    event_type: str = Field(..., description="Type of audit event")
    event_data: Optional[Dict[str, Any]] = Field(None, description="Event payload data")
    user_id: Optional[str] = Field(None, description="User who triggered the event")
    system_component: Optional[str] = Field(
        None, description="System component that generated the event"
    )
    timestamp: Optional[str] = Field(None, description="ISO-8601 event timestamp")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")


class AuditLogListResponseSchema(BaseModel):
    """Schema for audit log listing responses."""

    entries: List[AuditLogEntrySchema] = Field(
        ..., description="List of audit log entries"
    )
    total_count: int = Field(..., description="Total number of entries returned")


# Settings Schema


class SettingsResponseSchema(BaseModel):
    """Schema for unified settings endpoint."""

    tenant_id: str = Field(..., description="Current tenant identifier")
    system_type: str = Field(..., description="System type identifier")
    version: str = Field(..., description="Server version")
    capabilities: Dict[str, Any] = Field(
        ..., description="Server capabilities configuration"
    )
    limits: Dict[str, Any] = Field(..., description="System limits")
    security: Dict[str, Any] = Field(..., description="Security configuration")
    storage: Dict[str, Any] = Field(..., description="Storage configuration")


# GL Account CRUD Schemas


class GLAccountCreateRequestSchema(BaseModel):
    """Schema for creating a new GL account."""

    code: str = Field(..., min_length=1, max_length=10, description="GL account code")
    name: str = Field(..., min_length=1, max_length=200, description="GL account name")
    category: str = Field(
        ..., min_length=1, max_length=50, description="Account category"
    )
    keywords: Optional[List[str]] = Field(None, description="Classification keywords")
    description: Optional[str] = Field(None, description="Account description")
    tenant_id: str = Field(default="default", description="Tenant identifier")


class GLAccountUpdateRequestSchema(BaseModel):
    """Schema for updating an existing GL account."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="GL account name"
    )
    category: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Account category"
    )
    keywords: Optional[List[str]] = Field(None, description="Classification keywords")
    description: Optional[str] = Field(None, description="Account description")
    active: Optional[bool] = Field(None, description="Whether account is active")


# Vendor Schemas


class VendorCreateRequestSchema(BaseModel):
    """Schema for creating a new vendor."""

    name: str = Field(..., min_length=1, max_length=200, description="Vendor name")
    display_name: Optional[str] = Field(
        None, max_length=200, description="Display name"
    )
    contact_info: Optional[Dict[str, Any]] = Field(None, description="Contact details")
    tenant_id: str = Field(default="default", description="Tenant identifier")
    notes: Optional[str] = Field(None, description="Vendor notes")
    tags: Optional[List[str]] = Field(None, description="Vendor tags")
    default_gl_account: Optional[str] = Field(
        None, max_length=10, description="Default GL account code"
    )
    aliases: Optional[List[str]] = Field(None, description="Alternative vendor names")
    payment_terms: Optional[str] = Field(
        None, max_length=50, description="Payment terms"
    )
    payment_terms_days: Optional[int] = Field(
        None, ge=0, description="Payment terms in days"
    )
    vendor_type: Optional[str] = Field(
        None, max_length=50, description="Vendor type (supplier, subcontractor, etc.)"
    )


class VendorUpdateRequestSchema(BaseModel):
    """Schema for updating an existing vendor."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Vendor name"
    )
    display_name: Optional[str] = Field(
        None, max_length=200, description="Display name"
    )
    contact_info: Optional[Dict[str, Any]] = Field(None, description="Contact details")
    notes: Optional[str] = Field(None, description="Vendor notes")
    tags: Optional[List[str]] = Field(None, description="Vendor tags")
    default_gl_account: Optional[str] = Field(
        None, max_length=10, description="Default GL account code"
    )
    aliases: Optional[List[str]] = Field(None, description="Alternative vendor names")
    payment_terms: Optional[str] = Field(
        None, max_length=50, description="Payment terms"
    )
    payment_terms_days: Optional[int] = Field(
        None, ge=0, description="Payment terms in days"
    )
    vendor_type: Optional[str] = Field(
        None, max_length=50, description="Vendor type (supplier, subcontractor, etc.)"
    )
    active: Optional[bool] = Field(None, description="Whether vendor is active")


# Delete Response Schema


class DeleteDocumentResponseSchema(BaseModel):
    """Schema for document deletion responses."""

    success: bool = Field(..., description="Whether deletion succeeded")
    message: str = Field(..., description="Status message")
    document_id: str = Field(..., description="Deleted document ID")


# Error Response Schemas


class ErrorDetailSchema(BaseModel):
    """Schema for error details"""

    error_code: str = Field(..., description="Error code identifier")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class APIErrorResponseSchema(BaseModel):
    """Schema for API error responses"""

    success: bool = Field(default=False, description="Request success status")
    message: str = Field(..., description="Error message")
    errors: List[ErrorDetailSchema] = Field(
        ..., description="Detailed error information"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    request_id: Optional[str] = Field(
        None, description="Request identifier for tracking"
    )


class ValidationErrorResponseSchema(BaseModel):
    """Schema for validation error responses"""

    success: bool = Field(default=False, description="Validation success status")
    message: str = Field(
        default="Validation failed", description="Validation error message"
    )
    validation_errors: List[Dict[str, Any]] = Field(
        ..., description="Field validation errors"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


# Success Response Wrapper


class APISuccessResponseSchema(BaseModel):
    """Schema for successful API responses"""

    success: bool = Field(default=True, description="Request success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    request_id: Optional[str] = Field(
        None, description="Request identifier for tracking"
    )


# Pagination Schema


class PaginationSchema(BaseModel):
    """Schema for pagination parameters"""

    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort order"
    )


# Filter Schemas


class DocumentFilterSchema(BaseModel):
    """Schema for document filtering"""

    tenant_id: Optional[str] = Field(None, description="Filter by tenant")
    status: Optional[ProcessingStatus] = Field(
        None, description="Filter by processing status"
    )
    payment_status: Optional[PaymentStatus] = Field(
        None, description="Filter by payment status"
    )
    gl_account: Optional[str] = Field(None, description="Filter by GL account")
    vendor_name: Optional[str] = Field(None, description="Filter by vendor name")
    date_from: Optional[datetime] = Field(
        None, description="Filter by date range start"
    )
    date_to: Optional[datetime] = Field(None, description="Filter by date range end")
    amount_min: Optional[float] = Field(None, description="Filter by minimum amount")
    amount_max: Optional[float] = Field(None, description="Filter by maximum amount")
    scanner_id: Optional[str] = Field(None, description="Filter by scanner ID")


class VendorImportRequestSchema(BaseModel):
    """Schema for vendor bulk import request."""

    vendors: List[Dict[str, Any]] = Field(
        ..., min_length=1, description="List of vendor records to import"
    )
    mode: str = Field(
        default="merge",
        pattern="^(merge|overwrite|append)$",
        description="Import mode: merge, overwrite, or append",
    )


class VendorImportResultSchema(BaseModel):
    """Schema for vendor import result."""

    success: bool = Field(..., description="Whether import succeeded")
    created: int = Field(default=0, description="Number of vendors created")
    updated: int = Field(default=0, description="Number of vendors updated")
    skipped: int = Field(default=0, description="Number of vendors skipped")
    errors: List[str] = Field(default_factory=list, description="Validation errors")


# Export all schemas
__all__ = [
    # Auth schemas
    "AuthLoginRequestSchema",
    "AuthLoginResponseSchema",
    "AuthMeResponseSchema",
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
    # Audit log schemas
    "AuditLogEntrySchema",
    "AuditLogListResponseSchema",
    # Settings schema
    "SettingsResponseSchema",
    # GL Account CRUD schemas
    "GLAccountCreateRequestSchema",
    "GLAccountUpdateRequestSchema",
    # Vendor schemas
    "VendorCreateRequestSchema",
    "VendorUpdateRequestSchema",
    "VendorImportRequestSchema",
    "VendorImportResultSchema",
    # Delete response
    "DeleteDocumentResponseSchema",
    # Validation helpers
    "validate_document_id",
    "DOCUMENT_ID_PATTERN",
]
