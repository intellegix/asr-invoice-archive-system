import { apiClient } from '../client';
import type { Vendor, VendorCreateRequest } from '@/types/api';

export const vendorsAPI = {
  // List all vendors
  async list() {
    return apiClient.get<Vendor[]>('/vendors');
  },

  // Get single vendor details
  async getById(id: string) {
    return apiClient.get<Vendor>(`/vendors/${id}`);
  },

  // Create new vendor
  async create(vendor: VendorCreateRequest) {
    return apiClient.post<Vendor>('/vendors', vendor);
  },

  // Update vendor
  async update(id: string, vendor: Partial<Vendor>) {
    return apiClient.put<Vendor>(`/vendors/${id}`, vendor);
  },

  // Delete vendor
  async delete(id: string) {
    return apiClient.delete(`/vendors/${id}`);
  },

  // Get vendor statistics - shows GL account patterns and payment history
  async getStats(id: string) {
    return apiClient.get(`/vendors/${id}/stats`);
  },
};