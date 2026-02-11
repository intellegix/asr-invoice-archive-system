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
import { documentsAPI } from '../DocumentService';

describe('DocumentService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------- list ----------

  describe('list', () => {
    it('calls get with /invoices and default params when no filters provided', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce([]);

      await documentsAPI.list();

      expect(apiClient.get).toHaveBeenCalledWith('/invoices', {
        limit: 50,
        offset: 0,
        vendor: undefined,
        project: undefined,
        start_date: undefined,
        end_date: undefined,
        min_amount: undefined,
        max_amount: undefined,
      });
    });

    it('passes filter params correctly', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce([]);

      await documentsAPI.list({
        limit: 25,
        offset: 10,
        vendor: 'Acme Corp',
        project: 'Project Alpha',
        date_range: { start: '2026-01-01', end: '2026-01-31', field: 'created_at' },
        amount_range: { min: 100, max: 5000 },
      });

      expect(apiClient.get).toHaveBeenCalledWith('/invoices', {
        limit: 25,
        offset: 10,
        vendor: 'Acme Corp',
        project: 'Project Alpha',
        start_date: '2026-01-01',
        end_date: '2026-01-31',
        min_amount: 100,
        max_amount: 5000,
      });
    });
  });

  // ---------- getById ----------

  describe('getById', () => {
    it('calls get with /invoices/{id}', async () => {
      const mockDoc = { id: 'doc-1', filename: 'invoice.pdf' };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockDoc,
      );

      const result = await documentsAPI.getById('doc-1');

      expect(apiClient.get).toHaveBeenCalledWith('/invoices/doc-1');
      expect(result).toEqual(mockDoc);
    });
  });

  // ---------- upload ----------

  describe('upload', () => {
    it('calls uploadFile with /invoices and the file', async () => {
      const file = new File(['content'], 'invoice.pdf', {
        type: 'application/pdf',
      });
      const mockResponse = {
        document_id: 'abc-123',
        processing_status: 'pending',
      };
      (apiClient.uploadFile as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse,
      );

      const onProgress = vi.fn();
      const result = await documentsAPI.upload(file, onProgress);

      expect(apiClient.uploadFile).toHaveBeenCalledWith(
        '/invoices',
        file,
        onProgress,
      );
      expect(result).toEqual(mockResponse);
    });
  });

  // ---------- search ----------

  describe('search', () => {
    it('calls post with /search and query/filters', async () => {
      const mockResult = { documents: [], total: 0, filters: {} };
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResult,
      );

      const filters = { limit: 15 };
      const result = await documentsAPI.search('plumbing invoice', filters);

      expect(apiClient.post).toHaveBeenCalledWith('/search', {
        query: 'plumbing invoice',
        filters,
        limit: 15,
      });
      expect(result).toEqual(mockResult);
    });
  });

  // ---------- quickSearch ----------

  describe('quickSearch', () => {
    it('calls get with /search/quick and query params', async () => {
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce([]);

      await documentsAPI.quickSearch('lumber');

      expect(apiClient.get).toHaveBeenCalledWith('/search/quick', {
        q: 'lumber',
        limit: 10,
      });
    });
  });

  // ---------- reprocess ----------

  describe('reprocess', () => {
    it('calls post with /extract/invoice/{id}', async () => {
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        status: 'processing',
      });

      await documentsAPI.reprocess('doc-42');

      expect(apiClient.post).toHaveBeenCalledWith('/extract/invoice/doc-42');
    });
  });

  // ---------- delete ----------

  describe('delete', () => {
    it('calls delete with /invoices/{id}', async () => {
      (apiClient.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        deleted: true,
      });

      await documentsAPI.delete('doc-99');

      expect(apiClient.delete).toHaveBeenCalledWith('/invoices/doc-99');
    });
  });

  // ---------- getClassification ----------

  describe('getClassification', () => {
    it('calls get with /extract/invoice/{id}/details', async () => {
      const mockDetails = { gl_account_code: '5000', confidence: 0.95 };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockDetails,
      );

      const result = await documentsAPI.getClassification('doc-7');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/extract/invoice/doc-7/details',
      );
      expect(result).toEqual(mockDetails);
    });
  });

  // ---------- batchProcess ----------

  describe('batchProcess', () => {
    it('calls post with /extract/batch and file_ids', async () => {
      const mockResponse = {
        total_documents: 3,
        successful_classifications: 3,
        failed_classifications: 0,
      };
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockResponse,
      );

      const result = await documentsAPI.batchProcess([
        'id-1',
        'id-2',
        'id-3',
      ]);

      expect(apiClient.post).toHaveBeenCalledWith('/extract/batch', {
        file_ids: ['id-1', 'id-2', 'id-3'],
      });
      expect(result).toEqual(mockResponse);
    });
  });
});
