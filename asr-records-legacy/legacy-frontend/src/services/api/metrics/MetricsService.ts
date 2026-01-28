import { apiClient } from '../client';
import type { DashboardMetrics, TrendData, VendorMetrics, ExecutiveSummary } from '@/types/api';

export const metricsAPI = {
  // Dashboard KPIs - preserves all backend sophistication
  async getKPIs() {
    return apiClient.get<DashboardMetrics>('/metrics/kpis');
  },

  // Trend data for charts - shows payment detection accuracy over time
  async getTrends(period: '7d' | '30d' | '90d' = '30d') {
    return apiClient.get<TrendData>(`/metrics/trends?period=${period}`);
  },

  // Document aging analysis - leverages 4 billing destinations
  async getAging() {
    return apiClient.get('/metrics/aging');
  },

  // Vendor analytics - shows GL account usage and payment patterns
  async getVendorMetrics() {
    return apiClient.get<VendorMetrics>('/metrics/vendors');
  },

  // Executive summary - high-level view of all backend capabilities
  async getExecutiveSummary() {
    return apiClient.get<ExecutiveSummary>('/metrics/executive');
  },

  // Payment status distribution - shows results from 5-method payment detection
  async getPaymentStatusDistribution() {
    return apiClient.get('/metrics/payment-status');
  },

  // GL account usage - shows all 40+ account classifications in use
  async getGLAccountUsage() {
    return apiClient.get('/metrics/gl-accounts');
  },

  // Processing accuracy - shows confidence scores and manual review rates
  async getProcessingAccuracy() {
    return apiClient.get('/metrics/accuracy');
  },

  // Billing destination analytics - tracks routing to 4 destinations
  async getBillingDestinationMetrics() {
    return apiClient.get('/metrics/billing-destinations');
  },
};