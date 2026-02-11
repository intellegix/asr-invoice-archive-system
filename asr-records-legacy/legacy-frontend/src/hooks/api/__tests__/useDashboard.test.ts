import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { metricsAPI } from '@/services/api/metrics';
import {
  useDashboardMetrics,
  useTrendData,
  useDocumentAging,
  useVendorMetrics,
  useExecutiveSummary,
  usePaymentStatusDistribution,
  useGLAccountUsage,
  useProcessingAccuracy,
  useBillingDestinationMetrics,
} from '../useDashboard';

vi.mock('@/services/api/metrics', () => ({
  metricsAPI: {
    getKPIs: vi.fn(),
    getTrends: vi.fn(),
    getAging: vi.fn(),
    getVendorMetrics: vi.fn(),
    getExecutiveSummary: vi.fn(),
    getPaymentStatusDistribution: vi.fn(),
    getGLAccountUsage: vi.fn(),
    getProcessingAccuracy: vi.fn(),
    getBillingDestinationMetrics: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useDashboard hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --- useDashboardMetrics ---

  it('useDashboardMetrics calls metricsAPI.getKPIs', async () => {
    const mockData = { totalDocuments: 100, documentsThisMonth: 25 };
    vi.mocked(metricsAPI.getKPIs).mockResolvedValue(mockData as any);

    renderHook(() => useDashboardMetrics(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(metricsAPI.getKPIs).toHaveBeenCalledTimes(1);
    });
  });

  it('useDashboardMetrics returns data on success', async () => {
    const mockData = { totalDocuments: 100, documentsThisMonth: 25 };
    vi.mocked(metricsAPI.getKPIs).mockResolvedValue(mockData as any);

    const { result } = renderHook(() => useDashboardMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockData);
  });

  it('useDashboardMetrics returns error on failure', async () => {
    vi.mocked(metricsAPI.getKPIs).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useDashboardMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
    expect(result.current.error!.message).toBe('Network error');
  });

  // --- useTrendData ---

  it('useTrendData calls getTrends with default period', async () => {
    const mockTrends = { labels: ['Jan', 'Feb'], values: [10, 20] };
    vi.mocked(metricsAPI.getTrends).mockResolvedValue(mockTrends as any);

    const { result } = renderHook(() => useTrendData(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getTrends).toHaveBeenCalledWith('30d');
    expect(result.current.data).toEqual(mockTrends);
  });

  it('useTrendData calls getTrends with custom period', async () => {
    const mockTrends = { labels: ['Week1'], values: [5] };
    vi.mocked(metricsAPI.getTrends).mockResolvedValue(mockTrends as any);

    const { result } = renderHook(() => useTrendData('7d'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getTrends).toHaveBeenCalledWith('7d');
    expect(result.current.data).toEqual(mockTrends);
  });

  // --- useDocumentAging ---

  it('useDocumentAging calls getAging', async () => {
    const mockAging = { aging_buckets: [{ range: '0-30', count: 50 }] };
    vi.mocked(metricsAPI.getAging).mockResolvedValue(mockAging);

    const { result } = renderHook(() => useDocumentAging(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getAging).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockAging);
  });

  // --- useVendorMetrics ---

  it('useVendorMetrics calls getVendorMetrics', async () => {
    const mockData = { top_vendors: [{ name: 'Staples', amount: 5000 }] };
    vi.mocked(metricsAPI.getVendorMetrics).mockResolvedValue(mockData as any);

    const { result } = renderHook(() => useVendorMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getVendorMetrics).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockData);
  });

  // --- useExecutiveSummary ---

  it('useExecutiveSummary calls getExecutiveSummary', async () => {
    const mockSummary = { revenue: 1000000, efficiency: 95 };
    vi.mocked(metricsAPI.getExecutiveSummary).mockResolvedValue(mockSummary as any);

    const { result } = renderHook(() => useExecutiveSummary(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getExecutiveSummary).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockSummary);
  });

  // --- usePaymentStatusDistribution ---

  it('usePaymentStatusDistribution calls getPaymentStatusDistribution', async () => {
    const mockDistribution = {
      distribution: [{ status: 'paid', count: 120, percentage: 46, totalAmount: 1560000 }],
    };
    vi.mocked(metricsAPI.getPaymentStatusDistribution).mockResolvedValue(mockDistribution);

    const { result } = renderHook(() => usePaymentStatusDistribution(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getPaymentStatusDistribution).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockDistribution);
  });

  // --- useGLAccountUsage ---

  it('useGLAccountUsage calls getGLAccountUsage', async () => {
    const mockUsage = { accounts: [{ code: '6100', name: 'Office Supplies', count: 35 }] };
    vi.mocked(metricsAPI.getGLAccountUsage).mockResolvedValue(mockUsage);

    const { result } = renderHook(() => useGLAccountUsage(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getGLAccountUsage).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockUsage);
  });

  // --- useProcessingAccuracy ---

  it('useProcessingAccuracy calls getProcessingAccuracy', async () => {
    const mockAccuracy = { overall: 96.5, by_method: { claude_ai: 97.2 } };
    vi.mocked(metricsAPI.getProcessingAccuracy).mockResolvedValue(mockAccuracy);

    const { result } = renderHook(() => useProcessingAccuracy(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getProcessingAccuracy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockAccuracy);
  });

  // --- useBillingDestinationMetrics ---

  it('useBillingDestinationMetrics calls getBillingDestinationMetrics', async () => {
    const mockDestinations = {
      destinations: [
        { name: 'open_payable', count: 45 },
        { name: 'closed_payable', count: 120 },
      ],
    };
    vi.mocked(metricsAPI.getBillingDestinationMetrics).mockResolvedValue(mockDestinations);

    const { result } = renderHook(() => useBillingDestinationMetrics(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(metricsAPI.getBillingDestinationMetrics).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockDestinations);
  });
});
