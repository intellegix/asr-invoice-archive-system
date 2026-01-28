import { Document, PaymentStatus, BillingDestination } from '@/types/api';
import { DateRange } from '@/types/common';

// Dashboard component types
export interface DashboardProps {
  tenantId: string;
  dateRange?: DateRange;
  refreshInterval?: number;
  className?: string;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ComponentType<{ className?: string }>;
  trend?: TrendData;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gray';
  isLoading?: boolean;
  error?: string;
  onClick?: () => void;
  className?: string;
}

export interface TrendData {
  value: number;
  direction: 'up' | 'down' | 'neutral';
  period: string;
  isPositive: boolean;
}

// Dashboard metrics and data
export interface DashboardMetrics {
  summary: DashboardSummary;
  paymentStatus: PaymentStatusMetrics;
  billingDestinations: BillingDestinationMetrics;
  glAccounts: GLAccountMetrics;
  processing: ProcessingMetrics;
  recentActivity: ActivityMetrics;
  trends: TrendMetrics;
}

export interface DashboardSummary {
  totalDocuments: number;
  documentsThisMonth: number;
  totalAmount: number;
  amountThisMonth: number;
  averageProcessingTime: number;
  classificationAccuracy: number;
  manualReviewRate: number;
  systemHealth: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface PaymentStatusMetrics {
  paid: StatusBreakdown;
  unpaid: StatusBreakdown;
  partial: StatusBreakdown;
  void: StatusBreakdown;
  unknown: StatusBreakdown;
  total: number;
  accuracy: number;
  consensusRate: number;
}

export interface StatusBreakdown {
  count: number;
  amount: number;
  percentage: number;
  trend: TrendData;
}

export interface BillingDestinationMetrics {
  openPayable: DestinationBreakdown;
  closedPayable: DestinationBreakdown;
  openReceivable: DestinationBreakdown;
  closedReceivable: DestinationBreakdown;
  routingAccuracy: number;
  manualOverrides: number;
}

export interface DestinationBreakdown {
  count: number;
  amount: number;
  percentage: number;
  averageProcessingTime: number;
  errorRate: number;
}

export interface GLAccountMetrics {
  totalAccounts: number;
  activeAccounts: number;
  accountsUsed: number;
  mostUsedAccounts: AccountUsage[];
  classificationAccuracy: number;
  newAccountsThisMonth: number;
  quickBooksSync: {
    lastSync: string;
    status: 'success' | 'error' | 'pending';
    accountsSynced: number;
  };
}

export interface AccountUsage {
  accountCode: string;
  accountName: string;
  documentCount: number;
  totalAmount: number;
  percentage: number;
}

export interface ProcessingMetrics {
  averageTime: number;
  medianTime: number;
  fastestTime: number;
  slowestTime: number;
  timesByStage: {
    upload: number;
    ocr: number;
    classification: number;
    routing: number;
  };
  throughput: {
    documentsPerHour: number;
    documentsPerDay: number;
    peakHour: string;
  };
}

export interface ActivityMetrics {
  recentDocuments: Document[];
  recentClassifications: RecentClassification[];
  systemEvents: SystemEvent[];
  userActivity: UserActivity[];
}

export interface RecentClassification {
  documentId: string;
  filename: string;
  category: string;
  paymentStatus: PaymentStatus;
  confidence: number;
  timestamp: string;
  processingTime: number;
}

export interface SystemEvent {
  id: string;
  type: 'upload' | 'classification' | 'error' | 'sync' | 'override';
  message: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'error';
  details?: Record<string, any>;
}

export interface UserActivity {
  userId: string;
  userName: string;
  action: string;
  timestamp: string;
  documentId?: string;
  details?: string;
}

export interface TrendMetrics {
  documentVolume: TimeSeries[];
  processingTime: TimeSeries[];
  accuracy: TimeSeries[];
  errorRate: TimeSeries[];
  userAdoption: TimeSeries[];
}

export interface TimeSeries {
  timestamp: string;
  value: number;
  label?: string;
}

// Chart component types
export interface PaymentStatusChartProps {
  data: PaymentStatusMetrics;
  showPercentages?: boolean;
  showAmounts?: boolean;
  height?: number;
  className?: string;
}

export interface TrendChartProps {
  data: TimeSeries[];
  title: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  color?: string;
  className?: string;
}

export interface DistributionChartProps {
  data: Array<{
    label: string;
    value: number;
    color?: string;
  }>;
  type?: 'pie' | 'doughnut' | 'bar';
  height?: number;
  showLabels?: boolean;
  className?: string;
}

// Recent documents component types
export interface RecentDocumentsProps {
  documents: Document[];
  maxItems?: number;
  showGLCodes?: boolean;
  showAuditTrail?: boolean;
  onDocumentClick?: (document: Document) => void;
  isLoading?: boolean;
  error?: string;
  className?: string;
}

export interface RecentDocumentItem {
  document: Document;
  isNew?: boolean;
  hasIssues?: boolean;
  requiresReview?: boolean;
}

// Dashboard filters and controls
export interface DashboardFilters {
  dateRange: DateRange;
  documentStatus?: string[];
  paymentStatus?: PaymentStatus[];
  billingDestinations?: BillingDestination[];
  glAccountCodes?: string[];
  vendorNames?: string[];
  amountRange?: {
    min: number;
    max: number;
  };
}

export interface DashboardSettings {
  refreshInterval: number;
  autoRefresh: boolean;
  showTrends: boolean;
  showRecentActivity: boolean;
  defaultDateRange: '7d' | '30d' | '90d' | '1y';
  metricsToShow: DashboardMetricType[];
  chartTypes: Record<string, 'line' | 'bar' | 'pie' | 'doughnut'>;
}

export type DashboardMetricType =
  | 'summary'
  | 'paymentStatus'
  | 'billingDestinations'
  | 'glAccounts'
  | 'processing'
  | 'activity'
  | 'trends';

// Real-time updates
export interface DashboardUpdate {
  type: 'metric' | 'document' | 'alert' | 'system';
  timestamp: string;
  data: any;
  tenantId: string;
}

export interface MetricUpdate {
  metricType: DashboardMetricType;
  newValue: any;
  previousValue?: any;
  change?: number;
  trend?: TrendData;
}

// Alert and notification types
export interface DashboardAlert {
  id: string;
  type: 'warning' | 'error' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  isRead: boolean;
  actions?: AlertAction[];
  autoHide?: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AlertAction {
  label: string;
  action: () => void;
  primary?: boolean;
}