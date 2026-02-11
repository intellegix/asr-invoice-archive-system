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
import { vendorsAPI } from '../VendorService';

describe('VendorService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------- list ----------

  describe('list', () => {
    it('calls get with /vendors', async () => {
      const mockVendors = [
        { id: 'v-1', name: 'Acme Corp' },
        { id: 'v-2', name: 'BuildRight LLC' },
      ];
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockVendors,
      );

      const result = await vendorsAPI.list();

      expect(apiClient.get).toHaveBeenCalledWith('/vendors');
      expect(result).toEqual(mockVendors);
    });
  });

  // ---------- getById ----------

  describe('getById', () => {
    it('calls get with /vendors/{id}', async () => {
      const mockVendor = { id: 'v-1', name: 'Acme Corp' };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockVendor,
      );

      const result = await vendorsAPI.getById('v-1');

      expect(apiClient.get).toHaveBeenCalledWith('/vendors/v-1');
      expect(result).toEqual(mockVendor);
    });
  });

  // ---------- create ----------

  describe('create', () => {
    it('calls post with /vendors and vendor data', async () => {
      const newVendor = {
        name: 'New Vendor',
        tenant_id: 'default',
        contact_info: { email: 'vendor@example.com' },
      };
      const mockResponse = { id: 'v-new', ...newVendor };
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse,
      );

      const result = await vendorsAPI.create(newVendor);

      expect(apiClient.post).toHaveBeenCalledWith('/vendors', newVendor);
      expect(result).toEqual(mockResponse);
    });
  });

  // ---------- update ----------

  describe('update', () => {
    it('calls put with /vendors/{id} and partial data', async () => {
      const updateData = { name: 'Updated Vendor Name' };
      const mockResponse = { id: 'v-1', name: 'Updated Vendor Name' };
      (apiClient.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse,
      );

      const result = await vendorsAPI.update('v-1', updateData);

      expect(apiClient.put).toHaveBeenCalledWith('/vendors/v-1', updateData);
      expect(result).toEqual(mockResponse);
    });
  });

  // ---------- delete ----------

  describe('delete', () => {
    it('calls delete with /vendors/{id}', async () => {
      (apiClient.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        deleted: true,
      });

      await vendorsAPI.delete('v-1');

      expect(apiClient.delete).toHaveBeenCalledWith('/vendors/v-1');
    });
  });

  // ---------- getStats ----------

  describe('getStats', () => {
    it('calls get with /vendors/{id}/stats', async () => {
      const mockStats = {
        documents: { total: 42, by_month: [], by_gl_account: [] },
        payments: {
          accuracy: 0.95,
          detection_methods: [],
          status_distribution: { paid: 30, unpaid: 10, partial: 2, void: 0 },
        },
        trends: {
          document_volume: [],
          amount_processed: [],
          accuracy_over_time: [],
        },
      };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockStats,
      );

      const result = await vendorsAPI.getStats('v-1');

      expect(apiClient.get).toHaveBeenCalledWith('/vendors/v-1/stats');
      expect(result).toEqual(mockStats);
    });
  });
});
