import { BaseEntity } from '@/types/common/base';

export interface Vendor extends BaseEntity {
  name: string;
  display_name?: string;
  contact_info?: {
    email?: string;
    phone?: string;
    address?: string;
    website?: string;
  };

  // Statistics from document processing
  document_count: number;
  total_amount_processed: number;
  average_amount: number;
  last_document_date?: string;

  // GL account patterns
  common_gl_accounts: Array<{
    code: string;
    name: string;
    frequency: number;
    percentage: number;
  }>;

  // Payment patterns
  payment_accuracy: number;
  payment_patterns: {
    paid: number;
    unpaid: number;
    partial: number;
    void: number;
  };

  // Metadata
  tenant_id: string;
  notes?: string;
  tags?: string[];
}

export interface VendorCreateRequest {
  name: string;
  display_name?: string;
  contact_info?: {
    email?: string;
    phone?: string;
    address?: string;
    website?: string;
  };
  tenant_id: string;
  notes?: string;
  tags?: string[];
}

export interface VendorStats {
  // Document processing stats
  documents: {
    total: number;
    by_month: Array<{
      month: string;
      count: number;
      amount: number;
    }>;
    by_gl_account: Array<{
      code: string;
      name: string;
      count: number;
      amount: number;
      accuracy: number;
    }>;
  };

  // Payment analysis
  payments: {
    accuracy: number;
    detection_methods: Array<{
      method: string;
      usage: number;
      accuracy: number;
    }>;
    status_distribution: {
      paid: number;
      unpaid: number;
      partial: number;
      void: number;
    };
  };

  // Trends
  trends: {
    document_volume: Array<{
      date: string;
      count: number;
    }>;
    amount_processed: Array<{
      date: string;
      amount: number;
    }>;
    accuracy_over_time: Array<{
      date: string;
      accuracy: number;
    }>;
  };
}