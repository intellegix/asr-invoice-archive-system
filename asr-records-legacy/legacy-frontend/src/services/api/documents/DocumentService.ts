import { apiClient } from '../client';
import type {
  DocumentFilters,
  DocumentUploadResponse,
  SearchResult
} from '@/types/api';

export const documentsAPI = {
  // List documents with filtering and pagination
  async list(filters?: DocumentFilters) {
    const params = {
      limit: filters?.limit || 50,
      offset: filters?.offset || 0,
      vendor: filters?.vendor,
      project: filters?.project,
      start_date: filters?.date_range?.start,
      end_date: filters?.date_range?.end,
      min_amount: filters?.amount_range?.min,
      max_amount: filters?.amount_range?.max,
    };

    return apiClient.get<Document[]>('/invoices', params);
  },

  // Get single document
  async getById(id: string) {
    return apiClient.get<Document>(`/invoices/${id}`);
  },

  // Upload and process document - preserves all backend sophistication
  async upload(file: File, onProgress?: (progress: number) => void) {
    return apiClient.uploadFile<DocumentUploadResponse>('/invoices', file, onProgress);
  },

  // Search documents - leverages backend search capabilities
  async search(query: string, filters?: DocumentFilters) {
    return apiClient.post<SearchResult>('/search', {
      query,
      filters,
      limit: filters?.limit || 20,
    });
  },

  // Quick search - fast document lookup
  async quickSearch(query: string) {
    const params = { q: query, limit: 10 };
    return apiClient.get<Document[]>('/search/quick', params);
  },

  // Trigger document reprocessing - uses all 40+ GL accounts and 5-method payment detection
  async reprocess(id: string) {
    return apiClient.post(`/extract/invoice/${id}`);
  },

  // Delete document
  async delete(id: string) {
    return apiClient.delete(`/invoices/${id}`);
  },

  // Download document
  async download(id: string): Promise<Blob> {
    const response = await fetch(`${apiClient['client'].defaults.baseURL}/files/${id}/download`);
    return response.blob();
  },

  // Get classification details - shows all backend sophistication
  async getClassification(id: string) {
    return apiClient.get(`/extract/invoice/${id}/details`);
  },

  // Batch processing - maintains all backend capabilities
  async batchProcess(fileIds: string[]) {
    return apiClient.post('/extract/batch', { file_ids: fileIds });
  },
};