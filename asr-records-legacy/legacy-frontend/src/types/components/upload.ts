import { Document, DocumentClassification, ValidationLevel } from '@/types/api';

// Upload component types
export interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  onFilesDrop: (files: File[]) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
}

export interface UploadProgressProps {
  uploads: UploadItem[];
  onCancel?: (uploadId: string) => void;
  onRetry?: (uploadId: string) => void;
  className?: string;
}

export interface UploadItem {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  error?: string;
  result?: UploadResult;
  startTime: Date;
  endTime?: Date;
}

export type UploadStatus =
  | 'pending'
  | 'uploading'
  | 'processing'
  | 'classifying'
  | 'completed'
  | 'error'
  | 'cancelled';

export interface UploadResult {
  documentId: string;
  classification: DocumentClassification;
  processingTime: number;
  confidence: number;
}

export interface ClassificationViewProps {
  document?: Document;
  classification?: DocumentClassification;
  isLoading?: boolean;
  onAccept?: (classification: DocumentClassification) => void;
  onReject?: (reason: string) => void;
  onModify?: (updates: Partial<DocumentClassification>) => void;
  showDetails?: boolean;
  className?: string;
}

export interface FileValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: string[];
  fileInfo: FileInfo;
}

export interface ValidationError {
  code: string;
  message: string;
  field?: string;
}

export interface FileInfo {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  isImage: boolean;
  isPDF: boolean;
  extension: string;
}

// Upload configuration
export interface UploadConfig {
  maxFileSize: number; // bytes
  maxFiles: number;
  acceptedTypes: string[];
  validationLevel: ValidationLevel;
  autoClassify: boolean;
  allowedExtensions: string[];
  requiresApproval: boolean;
  tenantId: string;
}

export interface UploadSettings {
  chunkSize: number;
  maxRetries: number;
  retryDelay: number;
  concurrentUploads: number;
  enablePreview: boolean;
  enableProgress: boolean;
  enableClassification: boolean;
}

// Drag and drop types
export interface DragDropState {
  isDragging: boolean;
  draggedOver: boolean;
  dragCounter: number;
}

export interface DropEvent {
  files: File[];
  event: React.DragEvent<HTMLElement>;
}

// Upload hooks types
export interface UseUploadProps {
  config?: Partial<UploadConfig>;
  settings?: Partial<UploadSettings>;
  onSuccess?: (result: UploadResult) => void;
  onError?: (error: Error) => void;
  onProgress?: (progress: UploadProgress) => void;
}

export interface UploadProgress {
  uploadId: string;
  file: File;
  loaded: number;
  total: number;
  percentage: number;
  stage: UploadStage;
  timeRemaining?: number;
  speed?: number;
}

export type UploadStage = 'validation' | 'upload' | 'processing' | 'classification' | 'complete';

export interface UseUploadReturn {
  uploads: UploadItem[];
  uploadFiles: (files: File[]) => Promise<void>;
  cancelUpload: (uploadId: string) => void;
  retryUpload: (uploadId: string) => void;
  clearCompleted: () => void;
  clearAll: () => void;
  isUploading: boolean;
  hasErrors: boolean;
  totalProgress: number;
}

// File preview types
export interface FilePreviewProps {
  file: File;
  maxWidth?: number;
  maxHeight?: number;
  showMetadata?: boolean;
  className?: string;
}

export interface PreviewMetadata {
  filename: string;
  filesize: string;
  filetype: string;
  dimensions?: {
    width: number;
    height: number;
  };
  pageCount?: number;
  created?: Date;
  modified?: Date;
}

// Multi-file upload types
export interface BatchUploadProps {
  files: File[];
  config?: UploadConfig;
  onBatchComplete?: (results: UploadResult[]) => void;
  onBatchProgress?: (progress: BatchProgress) => void;
  onFileComplete?: (result: UploadResult) => void;
  onFileError?: (error: UploadError) => void;
}

export interface BatchProgress {
  totalFiles: number;
  completedFiles: number;
  failedFiles: number;
  overallProgress: number;
  currentFile?: string;
}

export interface UploadError {
  uploadId: string;
  file: File;
  error: Error;
  stage: UploadStage;
  retryable: boolean;
}

// Classification feedback types
export interface ClassificationFeedback {
  documentId: string;
  isCorrect: boolean;
  suggestedCategory?: string;
  suggestedPaymentStatus?: string;
  comments?: string;
  userId: string;
  timestamp: Date;
}