import { BaseEntity } from '@/types/common/base';

// GL Account types preserving 40+ account QuickBooks integration
export interface GLAccount extends BaseEntity {
  code: string;
  name: string;
  description?: string;
  account_type: GLAccountType;
  parent_code?: string;
  level: number;
  is_active: boolean;
  tenant_id: string;

  // QuickBooks integration
  quickbooks_id?: string;
  quickbooks_sync_status: 'synced' | 'pending' | 'error' | 'disabled';
  last_sync_date?: string;

  // Classification settings
  classification_keywords: string[];
  classification_rules: ClassificationRule[];
  auto_classify: boolean;
  confidence_threshold: number;

  // Usage statistics
  usage_count: number;
  last_used_date?: string;
  monthly_usage: MonthlyUsage[];

  // Hierarchy information
  children?: GLAccount[];
  full_path: string;
}

export type GLAccountType =
  | 'asset'
  | 'liability'
  | 'equity'
  | 'income'
  | 'expense'
  | 'cost_of_goods_sold'
  | 'other_income'
  | 'other_expense';

export interface ClassificationRule {
  id: string;
  name: string;
  description?: string;
  conditions: RuleCondition[];
  priority: number;
  is_active: boolean;
  confidence_boost: number;
}

export interface RuleCondition {
  field: 'vendor_name' | 'description' | 'amount' | 'filename' | 'invoice_number';
  operator: 'contains' | 'equals' | 'starts_with' | 'ends_with' | 'regex' | 'greater_than' | 'less_than';
  value: string | number;
  case_sensitive?: boolean;
}

export interface MonthlyUsage {
  year: number;
  month: number;
  document_count: number;
  total_amount: number;
}

// Expense categories and mapping
export interface ExpenseCategory {
  id: string;
  name: string;
  description?: string;
  gl_account_code: string;
  tenant_id: string;

  // Classification settings
  keywords: string[];
  vendor_mappings: VendorMapping[];
  patterns: CategoryPattern[];

  // Business rules
  requires_receipt: boolean;
  approval_threshold?: number;
  tax_deductible: boolean;
  default_for_vendors: string[];

  // Statistics
  usage_stats: CategoryUsageStats;
}

export interface VendorMapping {
  vendor_name: string;
  confidence: number;
  is_active: boolean;
  created_by?: string;
  created_at: string;
}

export interface CategoryPattern {
  pattern: string;
  pattern_type: 'regex' | 'keyword' | 'phrase';
  confidence_weight: number;
  is_active: boolean;
}

export interface CategoryUsageStats {
  total_documents: number;
  total_amount: number;
  average_amount: number;
  last_30_days_count: number;
  most_common_vendors: string[];
  accuracy_rate: number;
}

// GL Account hierarchy and structure
export interface GLAccountHierarchy {
  root_accounts: GLAccount[];
  total_accounts: number;
  by_type: Record<GLAccountType, GLAccount[]>;
  recently_used: GLAccount[];
  most_used: GLAccount[];
}

// Account configuration and setup
export interface GLAccountSetupRequest {
  tenant_id: string;
  quickbooks_integration?: {
    company_id: string;
    access_token: string;
    realm_id: string;
  };
  default_accounts: DefaultAccountMapping[];
  import_existing: boolean;
}

export interface DefaultAccountMapping {
  account_type: GLAccountType;
  gl_account_code: string;
  is_default: boolean;
  priority: number;
}

// QuickBooks integration types
export interface QuickBooksSync {
  id: string;
  tenant_id: string;
  sync_type: 'full' | 'incremental' | 'manual';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  error_message?: string;

  // Sync results
  accounts_synced: number;
  accounts_created: number;
  accounts_updated: number;
  accounts_deactivated: number;
  sync_conflicts: SyncConflict[];
}

export interface SyncConflict {
  gl_account_code: string;
  conflict_type: 'name_mismatch' | 'type_mismatch' | 'status_mismatch' | 'hierarchy_mismatch';
  local_value: any;
  quickbooks_value: any;
  resolution: 'use_local' | 'use_quickbooks' | 'manual_review';
}

// Account search and filtering
export interface GLAccountFilters {
  tenant_id: string;
  account_types?: GLAccountType[];
  is_active?: boolean;
  has_children?: boolean;
  level?: number;
  parent_code?: string;
  quickbooks_synced?: boolean;
  search_query?: string;
  min_usage_count?: number;
  used_since?: string;
}

export interface GLAccountSearchResult {
  account: GLAccount;
  match_score: number;
  match_reasons: string[];
  suggested_for_vendor?: string;
}

// Account analytics and insights
export interface GLAccountAnalytics {
  tenant_id: string;
  period: {
    start_date: string;
    end_date: string;
  };

  // Usage analytics
  most_used_accounts: AccountUsageSummary[];
  least_used_accounts: AccountUsageSummary[];
  trending_accounts: AccountTrend[];

  // Classification analytics
  classification_accuracy: number;
  manual_review_rate: number;
  auto_classification_rate: number;
  top_misclassified_vendors: MisclassificationSummary[];

  // Financial insights
  expense_distribution: ExpenseDistribution[];
  seasonal_patterns: SeasonalPattern[];
  vendor_account_relationships: VendorAccountRelationship[];
}

export interface AccountUsageSummary {
  gl_account: GLAccount;
  document_count: number;
  total_amount: number;
  unique_vendors: number;
  growth_rate: number;
}

export interface AccountTrend {
  gl_account_code: string;
  trend: 'increasing' | 'decreasing' | 'stable';
  percentage_change: number;
  period_over_period: number[];
}

export interface MisclassificationSummary {
  vendor_name: string;
  expected_account: string;
  actual_account: string;
  frequency: number;
  impact_amount: number;
}

export interface ExpenseDistribution {
  gl_account_code: string;
  percentage: number;
  amount: number;
  comparison_to_budget?: number;
}

export interface SeasonalPattern {
  gl_account_code: string;
  pattern_type: 'seasonal' | 'monthly' | 'weekly';
  peak_periods: string[];
  variance: number;
}

export interface VendorAccountRelationship {
  vendor_name: string;
  primary_account: string;
  secondary_accounts: string[];
  consistency_score: number;
  total_amount: number;
}