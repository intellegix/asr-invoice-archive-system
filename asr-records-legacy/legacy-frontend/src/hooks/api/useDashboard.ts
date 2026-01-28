import { useQuery } from '@tanstack/react-query';
import { metricsAPI } from '@/services/api/metrics';

// Dashboard metrics - preserves all backend sophistication
export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: ['metrics', 'dashboard'],
    queryFn: metricsAPI.getKPIs,
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true, // Keep dashboard fresh
  });
};

// Trend data for charts - shows payment detection accuracy over time
export const useTrendData = (period: '7d' | '30d' | '90d' = '30d') => {
  return useQuery({
    queryKey: ['metrics', 'trends', period],
    queryFn: () => metricsAPI.getTrends(period),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Document aging analysis - leverages 4 billing destinations
export const useDocumentAging = () => {
  return useQuery({
    queryKey: ['metrics', 'aging'],
    queryFn: metricsAPI.getAging,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
  });
};

// Vendor analytics - shows GL account patterns per vendor
export const useVendorMetrics = () => {
  return useQuery({
    queryKey: ['metrics', 'vendors'],
    queryFn: metricsAPI.getVendorMetrics,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Executive summary - high-level overview of all capabilities
export const useExecutiveSummary = () => {
  return useQuery({
    queryKey: ['metrics', 'executive'],
    queryFn: metricsAPI.getExecutiveSummary,
    staleTime: 10 * 60 * 1000, // 10 minutes - executive data changes less frequently
    gcTime: 60 * 60 * 1000, // 1 hour
  });
};

// Payment status distribution - shows results from 5-method consensus
export const usePaymentStatusDistribution = () => {
  return useQuery({
    queryKey: ['metrics', 'payment-status'],
    queryFn: metricsAPI.getPaymentStatusDistribution,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
};

// GL account usage - shows all 40+ accounts in use
export const useGLAccountUsage = () => {
  return useQuery({
    queryKey: ['metrics', 'gl-accounts'],
    queryFn: metricsAPI.getGLAccountUsage,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
  });
};

// Processing accuracy - shows confidence scores from all methods
export const useProcessingAccuracy = () => {
  return useQuery({
    queryKey: ['metrics', 'accuracy'],
    queryFn: metricsAPI.getProcessingAccuracy,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Billing destination analytics - tracks routing to 4 destinations
export const useBillingDestinationMetrics = () => {
  return useQuery({
    queryKey: ['metrics', 'billing-destinations'],
    queryFn: metricsAPI.getBillingDestinationMetrics,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
  });
};