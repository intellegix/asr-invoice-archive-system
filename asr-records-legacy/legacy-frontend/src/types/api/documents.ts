import { BaseEntity } from '@/types/common/base';

// Document types that preserve all backend sophistication
export interface Document extends BaseEntity {
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  tenant_id: string;

  // Classification results from sophisticated backend
  classification: DocumentClassification;

  // Processing status
  status: DocumentStatus;
  processing_start_time?: string;
  processing_end_time?: string;

  // Metadata
  metadata: DocumentMetadata;

  // Audit trail
  audit_trail: AuditStep[];
}

export interface DocumentClassification {
  // Expense category from 40+ GL account mapping
  expense_category: string;
  gl_account_code: string;
  suggested_category: string;
  category_confidence: number;

  // Payment status from 5-method consensus
  payment_status: PaymentStatus;
  payment_confidence: number;
  consensus_methods: PaymentDetectionMethod[];
  payment_details: PaymentDetails;

  // Billing routing from 4 destination system
  routing_destination: BillingDestination;
  routing_confidence: number;
  routing_reason: string;

  // Vendor/Company extraction
  vendor_name?: string;
  vendor_confidence?: number;
  company_name?: string;

  // Financial information
  amount?: number;
  currency?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;

  // AI analysis
  claude_analysis?: ClaudeAnalysis;
  validation_level: ValidationLevel;
}

export type DocumentStatus =
  | 'pending'
  | 'processing'
  | 'classified'
  | 'manual_review'
  | 'completed'
  | 'error'
  | 'archived';

export type PaymentStatus = 'paid' | 'unpaid' | 'partial' | 'void' | 'unknown';

export type PaymentDetectionMethod =
  | 'claude_ai'
  | 'regex_patterns'
  | 'keyword_analysis'
  | 'amount_analysis'
  | 'date_analysis';

export interface PaymentDetails {
  amount_paid?: number;
  payment_date?: string;
  payment_method?: string;
  reference_number?: string;
  partial_payments?: PartialPayment[];
}

export interface PartialPayment {
  amount: number;
  date: string;
  method?: string;
  reference?: string;
}

export type BillingDestination =
  | 'open_payable'
  | 'closed_payable'
  | 'open_receivable'
  | 'closed_receivable';

export interface ClaudeAnalysis {
  summary: string;
  confidence: number;
  extracted_entities: ExtractedEntity[];
  recommendations: string[];
  analysis_timestamp: string;
}

export interface ExtractedEntity {
  type: 'vendor' | 'amount' | 'date' | 'invoice_number' | 'payment_status';
  value: string;
  confidence: number;
  location?: {
    page: number;
    x: number;
    y: number;
  };
}

export type ValidationLevel = 'standard' | 'strict' | 'permissive';

export interface DocumentMetadata {
  page_count?: number;
  word_count?: number;
  language?: string;
  ocr_confidence?: number;
  file_hash: string;
  scan_quality?: 'low' | 'medium' | 'high';
  document_type?: string;
}

export interface AuditStep {
  timestamp: string;
  action: string;
  user_id?: string;
  details: Record<string, any>;
  previous_values?: Record<string, any>;
  new_values?: Record<string, any>;
}

// Document upload and processing
export interface DocumentUploadRequest {
  file: File;
  tenant_id: string;
  auto_classify?: boolean;
  validation_level?: ValidationLevel;
  metadata?: Partial<DocumentMetadata>;
}

export interface DocumentUploadResponse {
  document_id: string;
  upload_url?: string;
  processing_status: DocumentStatus;
  estimated_processing_time?: number;
}

export interface DocumentClassificationRequest {
  document_id: string;
  force_reclassify?: boolean;
  validation_level?: ValidationLevel;
  user_context?: {
    user_id: string;
    preferences: Record<string, any>;
  };
}

// Search and filtering
export interface DocumentFilters {
  tenant_id?: string;
  status?: DocumentStatus[];
  payment_status?: PaymentStatus[];
  gl_account_codes?: string[];
  routing_destinations?: BillingDestination[];
  vendor_names?: string[];
  vendor?: string;
  project?: string;
  limit?: number;
  offset?: number;
  date_range?: {
    start: string;
    end: string;
    field: 'created_at' | 'invoice_date' | 'due_date';
  };
  amount_range?: {
    min: number;
    max: number;
  };
  search_query?: string;
  filename_contains?: string;
  has_classification?: boolean;
  confidence_threshold?: number;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
}

export interface DocumentSortOptions {
  field: 'created_at' | 'filename' | 'amount' | 'vendor_name' | 'classification.category_confidence';
  direction: 'asc' | 'desc';
}

// Batch operations
export interface BatchClassificationRequest {
  document_ids: string[];
  validation_level?: ValidationLevel;
  force_reclassify?: boolean;
}

export interface BatchClassificationResponse {
  total_documents: number;
  successful_classifications: number;
  failed_classifications: number;
  results: {
    document_id: string;
    success: boolean;
    error?: string;
  }[];
}

// Export functionality
export interface DocumentExportRequest {
  document_ids?: string[];
  filters?: DocumentFilters;
  format: 'csv' | 'xlsx' | 'pdf' | 'json';
  include_audit_trail?: boolean;
  include_metadata?: boolean;
}

export interface DocumentExportResponse {
  export_id: string;
  download_url: string;
  expires_at: string;
  file_size: number;
}