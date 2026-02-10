"""
ASR Systems - Shared Core Models
Common Pydantic data models for both Production Server and Document Scanner
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class SystemType(str, Enum):
    """System type enumeration"""

    PRODUCTION_SERVER = "production_server"
    DOCUMENT_SCANNER = "document_scanner"


class ProcessingStatus(str, Enum):
    """Document processing status"""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    ROUTED = "routed"
    COMPLETED = "completed"
    ERROR = "error"
    MANUAL_REVIEW = "manual_review"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""

    PAID = "paid"
    UNPAID = "unpaid"
    PARTIAL = "partial"
    VOID = "void"
    UNKNOWN = "unknown"


class BillingDestination(str, Enum):
    """Billing routing destinations"""

    OPEN_PAYABLE = "open_payable"
    CLOSED_PAYABLE = "closed_payable"
    OPEN_RECEIVABLE = "open_receivable"
    CLOSED_RECEIVABLE = "closed_receivable"


class GLAccount(BaseModel):
    """QuickBooks GL Account"""

    code: str = Field(..., description="GL account code")
    name: str = Field(..., description="Account name")
    category: str = Field(..., description="Expense category")
    keywords: List[str] = Field(
        default_factory=list, description="Keyword matching patterns"
    )
    active: bool = Field(default=True, description="Account is active")


class PaymentDetectionMethod(str, Enum):
    """Payment detection methods"""

    CLAUDE_VISION = "claude_vision"
    CLAUDE_TEXT = "claude_text"
    REGEX_PATTERNS = "regex_patterns"
    KEYWORD_MATCHING = "keyword_matching"
    AMOUNT_ANALYSIS = "amount_analysis"


class PaymentConsensusResult(BaseModel):
    """Payment detection consensus result"""

    payment_status: PaymentStatus
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    methods_used: List[PaymentDetectionMethod] = Field(
        ..., description="Methods that contributed"
    )
    method_results: Dict[str, Any] = Field(..., description="Individual method results")
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Quality validation score"
    )
    consensus_reached: bool = Field(..., description="Whether consensus was achieved")


class DocumentMetadata(BaseModel):
    """Shared document metadata"""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique document ID"
    )
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str = Field(..., description="Tenant identifier")
    scanner_id: Optional[str] = Field(
        None, description="Scanner client ID if from scanner"
    )

    # Processing status
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    # Classification results
    gl_account: Optional[str] = Field(None, description="Assigned GL account code")
    vendor_name: Optional[str] = Field(None, description="Detected vendor")
    amount: Optional[float] = Field(None, description="Invoice amount")
    invoice_date: Optional[datetime] = Field(None, description="Invoice date")

    # Payment detection
    payment_consensus: Optional[PaymentConsensusResult] = None

    # Routing
    billing_destination: Optional[BillingDestination] = None
    routing_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Storage
    storage_path: Optional[str] = Field(None, description="Storage location")

    @validator("routing_confidence")
    def validate_confidence_range(cls, v):
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Confidence scores must be between 0.0 and 1.0")
        return v


class DocumentUploadRequest(BaseModel):
    """Document upload request from scanner"""

    filename: str
    file_data: bytes
    tenant_id: str
    scanner_id: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentUploadResponse(BaseModel):
    """Document upload response to scanner"""

    document_id: str
    status: ProcessingStatus
    message: str
    processing_time_estimate: Optional[int] = Field(
        None, description="Estimated processing time in seconds"
    )
    upload_success: bool = Field(default=True)


class ClassificationRequest(BaseModel):
    """Document classification request"""

    document_id: str
    tenant_id: str
    force_reclassification: bool = Field(default=False)
    preferred_gl_accounts: Optional[List[str]] = Field(
        None, description="Tenant-specific GL accounts"
    )
    payment_detection_methods: Optional[List[PaymentDetectionMethod]] = Field(
        None, description="Enabled methods"
    )


class ClassificationResult(BaseModel):
    """Document classification result"""

    document_id: str
    classification_successful: bool

    # GL Account classification
    gl_account: Optional[str] = None
    gl_confidence: Optional[float] = None
    gl_reasoning: Optional[str] = None

    # Payment detection
    payment_consensus: Optional[PaymentConsensusResult] = None

    # Vendor/Amount extraction
    vendor_name: Optional[str] = None
    amount: Optional[float] = None
    invoice_date: Optional[datetime] = None

    # Quality metrics
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    classification_timestamp: datetime = Field(default_factory=datetime.utcnow)


class RoutingDecision(BaseModel):
    """Billing routing decision"""

    document_id: str
    destination: BillingDestination
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Routing decision reasoning")
    factors: Dict[str, Any] = Field(..., description="Decision factors")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    manual_override: bool = Field(default=False)


class AuditTrailEntry(BaseModel):
    """Audit trail entry for transparency"""

    document_id: str
    event_type: str
    event_data: Dict[str, Any]
    user_id: Optional[str] = None
    system_component: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str


class TenantConfiguration(BaseModel):
    """Tenant-specific configuration"""

    tenant_id: str
    company_name: str

    # GL Account configuration
    enabled_gl_accounts: List[str] = Field(..., description="Enabled GL account codes")
    default_gl_account: Optional[str] = None

    # Payment detection configuration
    enabled_payment_methods: List[PaymentDetectionMethod]
    payment_confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

    # Routing configuration
    routing_preferences: Dict[str, Any] = Field(default_factory=dict)
    require_manual_review_below_confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    # Storage configuration
    storage_quota_gb: int = Field(default=100, description="Storage quota in GB")
    document_retention_days: int = Field(
        default=2555, description="Document retention period"
    )

    # Active status
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScannerConfiguration(BaseModel):
    """Document scanner configuration"""

    scanner_id: str = Field(..., description="Unique scanner identifier")
    name: str = Field(..., description="Scanner display name")
    tenant_id: str

    # Connection settings
    production_server_url: str
    api_key: str

    # Scanning settings
    watch_folders: List[str] = Field(default_factory=list)
    auto_upload: bool = Field(default=True)
    batch_size: int = Field(default=10, description="Max files per batch")
    retry_attempts: int = Field(default=3)

    # Offline queue settings
    offline_queue_enabled: bool = Field(default=True)
    max_offline_documents: int = Field(default=1000)

    # Active status
    active: bool = Field(default=True)
    last_heartbeat: Optional[datetime] = None


class SystemHealth(BaseModel):
    """System health status"""

    system_type: SystemType
    status: str  # "healthy", "degraded", "unhealthy"
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScannerHealth(BaseModel):
    """Scanner system health status"""

    status: str = Field(..., description="Overall status: healthy, degraded, error")
    services: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Service health statuses"
    )
    gui_active: bool = Field(default=False, description="GUI active status")
    server_connected: bool = Field(
        default=False, description="Production server connection status"
    )
    error: Optional[str] = Field(None, description="Error message if status is error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadResult(BaseModel):
    """Result of document upload operation"""

    success: bool = Field(..., description="Upload success status")
    document_id: Optional[str] = Field(None, description="Assigned document ID")
    processing_status: str = Field(default="uploaded", description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    classification_result: Optional[Dict[str, Any]] = Field(
        None, description="Document classification result"
    )
    processing_time_ms: int = Field(
        default=0, description="Processing time in milliseconds"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GLClassificationResult(BaseModel):
    """GL account classification result"""

    gl_account_code: str = Field(..., description="Selected GL account code")
    gl_account_name: str = Field(..., description="GL account name")
    category: str = Field(..., description="GL account category")
    confidence: float = Field(
        ..., description="Classification confidence score", ge=0.0, le=1.0
    )
    reasoning: str = Field(..., description="Classification reasoning")
    keywords_matched: List[str] = Field(
        default_factory=list, description="Matched keywords"
    )
    classification_method: str = Field(
        ..., description="Method used for classification"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    """Standard API response wrapper"""

    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Export all models
__all__ = [
    "SystemType",
    "ProcessingStatus",
    "PaymentStatus",
    "BillingDestination",
    "GLAccount",
    "PaymentDetectionMethod",
    "PaymentConsensusResult",
    "DocumentMetadata",
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "ClassificationRequest",
    "ClassificationResult",
    "RoutingDecision",
    "AuditTrailEntry",
    "TenantConfiguration",
    "ScannerConfiguration",
    "SystemHealth",
    "ScannerHealth",
    "APIResponse",
    "UploadResult",
    "GLClassificationResult",
]
