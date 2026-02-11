vi.mock('../../client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    uploadFile: vi.fn(),
  },
}));

import { apiClient } from '../../client';
import { metricsAPI } from '../MetricsService';

describe('MetricsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------- getKPIs ----------

  describe('getKPIs', () => {
    it('calls get with /metrics/kpis', async () => {
      const mockKPIs = { totalDocuments: 150, paymentAccuracy: 0.97 };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockKPIs,
      );

      const result = await metricsAPI.getKPIs();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/kpis');
      expect(result).toEqual(mockKPIs);
    });
  });

  // ---------- getTrends ----------

  describe('getTrends', () => {
    it('calls get with default 30d period', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getTrends();

      expect(apiClient.get).toHaveBeenCalledWith(
        '/metrics/trends?period=30d',
      );
    });

    it('calls get with custom period', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getTrends('7d');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/metrics/trends?period=7d',
      );
    });
  });

  // ---------- getAging ----------

  describe('getAging', () => {
    it('calls get with /metrics/aging', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getAging();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/aging');
    });
  });

  // ---------- getVendorMetrics ----------

  describe('getVendorMetrics', () => {
    it('calls get with /metrics/vendors', async () => {
      const mockVendors = { topVendors: [], vendorGrowth: [] };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockVendors,
      );

      const result = await metricsAPI.getVendorMetrics();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/vendors');
      expect(result).toEqual(mockVendors);
    });
  });

  // ---------- getExecutiveSummary ----------

  describe('getExecutiveSummary', () => {
    it('calls get with /metrics/executive', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getExecutiveSummary();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/executive');
    });
  });

  // ---------- getPaymentStatusDistribution ----------

  describe('getPaymentStatusDistribution', () => {
    it('calls get with /metrics/payment-status', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getPaymentStatusDistribution();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/payment-status');
    });
  });

  // ---------- getGLAccountUsage ----------

  describe('getGLAccountUsage', () => {
    it('calls get with /metrics/gl-accounts', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getGLAccountUsage();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/gl-accounts');
    });
  });

  // ---------- getProcessingAccuracy ----------

  describe('getProcessingAccuracy', () => {
    it('calls get with /metrics/accuracy', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getProcessingAccuracy();

      expect(apiClient.get).toHaveBeenCalledWith('/metrics/accuracy');
    });
  });

  // ---------- getBillingDestinationMetrics ----------

  describe('getBillingDestinationMetrics', () => {
    it('calls get with /metrics/billing-destinations', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

      await metricsAPI.getBillingDestinationMetrics();

      expect(apiClient.get).toHaveBeenCalledWith(
        '/metrics/billing-destinations',
      );
    });
  });
});
