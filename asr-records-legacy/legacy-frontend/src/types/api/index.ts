// API type exports - barrel exports for clean imports

// Document types
export type {
  Document,
  DocumentClassification,
  DocumentStatus,
  PaymentStatus,
  PaymentDetectionMethod,
  PaymentDetails,
  PartialPayment,
  BillingDestination,
  ClaudeAnalysis,
  ExtractedEntity,
  ValidationLevel,
  DocumentMetadata,
  AuditStep,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentClassificationRequest,
  DocumentFilters,
  DocumentSortOptions,
  BatchClassificationRequest,
  BatchClassificationResponse,
  DocumentExportRequest,
  DocumentExportResponse,
} from './documents';

// GL Code types
export type {
  GLAccount,
  GLAccountType,
  ClassificationRule,
  RuleCondition,
  MonthlyUsage,
  ExpenseCategory,
  VendorMapping,
  CategoryPattern,
  CategoryUsageStats,
  GLAccountHierarchy,
  GLAccountSetupRequest,
  DefaultAccountMapping,
  QuickBooksSync,
  SyncConflict,
  GLAccountFilters,
  GLAccountSearchResult,
  GLAccountAnalytics,
  AccountUsageSummary,
  AccountTrend,
  MisclassificationSummary,
  ExpenseDistribution,
  SeasonalPattern,
  VendorAccountRelationship,
} from './glcodes';

// Billing types
export type {
  BillingRoute,
  RoutingAlgorithm,
  RoutingFactor,
  RuleMatch,
  RoutingHistory,
  ValidationStatus,
  PaymentDetection,
  PaymentMethodResult,
  ConsensusAlgorithm,
  Evidence,
  DocumentLocation,
  PaymentIndicator,
  ConflictingSignal,
  BillingDestinationConfig,
  DestinationRule,
  RuleAction,
  ApprovalWorkflow,
  EscalationRule,
  NotificationSettings,
  NotificationEvent,
  PaymentAnalytics,
  MethodPerformance,
  VendorPaymentPattern,
  PaymentSeasonalTrend,
  RouteOptimization,
  RoutePerformanceMetrics,
  SuggestedRule,
  ThresholdAdjustment,
  TrainingRecommendation,
} from './billing';

// Metrics types
export type {
  DashboardMetrics,
  TrendData,
  VendorMetrics,
  ExecutiveSummary,
  PaymentStatusDistribution,
  GLAccountUsage,
  ProcessingAccuracy,
  BillingDestinationMetrics,
  SearchResult,
} from './metrics';

// Vendor types
export type {
  Vendor,
  VendorCreateRequest,
  VendorStats,
} from './vendors';

// Re-export common types for convenience
export type {
  BaseEntity,
  PaginatedResponse,
  ApiResponse,
  ErrorResponse,
  LoadingState,
  SelectOption,
  DateRange,
  FileUploadProgress,
  TenantContext,
  TenantLimits,
  SortDirection,
  SortConfig,
  FilterConfig,
} from '@/types/common/base';