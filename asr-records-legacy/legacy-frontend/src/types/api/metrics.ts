import { PaymentStatus, BillingDestination } from './documents';

// Dashboard metrics that preserve backend sophistication
export interface DashboardMetrics {
  // Core document metrics
  totalDocuments: number;
  documentsThisMonth: number;
  documentsTrend: {
    value: number;
    direction: 'up' | 'down';
    period: string;
    isPositive: boolean;
  };

  // Payment detection metrics (preserves 5-method consensus)
  paymentAccuracy: number;
  paymentAccuracyTrend: {
    value: number;
    direction: 'up' | 'down';
    period: string;
    isPositive: boolean;
  };

  // GL account classification metrics (preserves 40+ accounts)
  glAccountsUsed: number;
  totalGLAccounts: number;
  classificationAccuracy: number;

  // Processing metrics
  totalAmountProcessed: number;
  averageProcessingTime: number;
  manualReviewRate: number;
  processingTimeTrend: {
    value: number;
    direction: 'up' | 'down';
    period: string;
    isPositive: boolean;
  };

  // Billing destination metrics (preserves 4 destinations)
  openPayable: number;
  closedPayable: number;
  openReceivable: number;
  closedReceivable: number;

  // Recently processed documents
  recentDocuments: Array<{
    id: string;
    filename: string;
    vendor: string;
    amount: number;
    status: PaymentStatus;
    glAccount: string;
    confidence: number;
    processedAt: string;
    billingDestination: BillingDestination;
  }>;
}

export interface TrendData {
  period: '7d' | '30d' | '90d';
  documents: Array<{
    date: string;
    total: number;
    classified: number;
    manualReview: number;
  }>;
  amounts: Array<{
    date: string;
    total: number;
    paid: number;
    unpaid: number;
  }>;
  accuracy: Array<{
    date: string;
    paymentDetection: number;
    glClassification: number;
    overall: number;
  }>;
}

export interface VendorMetrics {
  topVendors: Array<{
    name: string;
    documentCount: number;
    totalAmount: number;
    averageAmount: number;
    paymentAccuracy: number;
    commonGLAccounts: string[];
  }>;
  vendorGrowth: Array<{
    month: string;
    newVendors: number;
    activeVendors: number;
  }>;
}

export interface ExecutiveSummary {
  // High-level overview
  totalDocumentsProcessed: number;
  totalValueProcessed: number;
  averageProcessingTime: number;

  // Quality metrics
  overallAccuracy: number;
  paymentDetectionAccuracy: number;
  glClassificationAccuracy: number;
  manualReviewRate: number;

  // Growth metrics
  monthlyGrowth: {
    documents: number;
    value: number;
    vendors: number;
  };

  // Top performers
  topGLAccounts: Array<{
    code: string;
    name: string;
    documentCount: number;
    accuracy: number;
  }>;

  topVendors: Array<{
    name: string;
    documentCount: number;
    totalValue: number;
  }>;

  // Alert conditions
  alerts: Array<{
    type: 'low_accuracy' | 'high_manual_review' | 'processing_delays';
    severity: 'low' | 'medium' | 'high';
    message: string;
    count: number;
  }>;
}

export interface PaymentStatusDistribution {
  distribution: Array<{
    status: PaymentStatus;
    count: number;
    percentage: number;
    totalAmount: number;
  }>;
  trends: Array<{
    date: string;
    paid: number;
    unpaid: number;
    partial: number;
    void: number;
  }>;
}

export interface GLAccountUsage {
  accounts: Array<{
    code: string;
    name: string;
    category: string;
    documentCount: number;
    totalAmount: number;
    accuracy: number;
    lastUsed: string;
  }>;
  categories: Array<{
    name: string;
    accountCount: number;
    documentCount: number;
    percentage: number;
  }>;
}

export interface ProcessingAccuracy {
  overall: {
    accuracy: number;
    confidenceScores: Array<{
      range: string;
      count: number;
      percentage: number;
    }>;
  };
  methods: Array<{
    method: string;
    accuracy: number;
    usage: number;
    averageConfidence: number;
  }>;
  trends: Array<{
    date: string;
    accuracy: number;
    manualReviewRate: number;
  }>;
}

export interface BillingDestinationMetrics {
  destinations: Array<{
    destination: BillingDestination;
    count: number;
    percentage: number;
    averageAmount: number;
    accuracy: number;
  }>;
  routing: {
    automaticRouting: number;
    manualOverrides: number;
    routingAccuracy: number;
  };
  trends: Array<{
    date: string;
    openPayable: number;
    closedPayable: number;
    openReceivable: number;
    closedReceivable: number;
  }>;
}

// Search result type
export interface SearchResult {
  documents: Array<any>; // Uses Document type from documents.ts
  total: number;
  filters: any;
  facets?: Array<{
    field: string;
    values: Array<{
      value: string;
      count: number;
    }>;
  }>;
}