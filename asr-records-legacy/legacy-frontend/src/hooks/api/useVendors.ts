import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { vendorsAPI } from '@/services/api/vendors';
import { invalidateQueries } from '@/services/api/client';
import type { Vendor, VendorCreateRequest } from '@/types/api';
import toast from 'react-hot-toast';

// List all vendors
export const useVendors = () => {
  return useQuery({
    queryKey: ['vendors'],
    queryFn: vendorsAPI.list,
    staleTime: 10 * 60 * 1000, // 10 minutes - vendor list doesn't change often
    gcTime: 60 * 60 * 1000, // 1 hour
  });
};

// Single vendor
export const useVendor = (id: string) => {
  return useQuery({
    queryKey: ['vendors', id],
    queryFn: () => vendorsAPI.getById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Vendor statistics - shows GL account patterns and payment history
export const useVendorStats = (id: string) => {
  return useQuery({
    queryKey: ['vendors', id, 'stats'],
    queryFn: () => vendorsAPI.getStats(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Create vendor
export const useCreateVendor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vendor: VendorCreateRequest) => vendorsAPI.create(vendor),
    onSuccess: (newVendor) => {
      // Update vendor list cache
      queryClient.setQueryData(['vendors'], (oldData: Vendor[] | undefined) => {
        return oldData ? [...oldData, newVendor] : [newVendor];
      });

      invalidateQueries.vendors();
      toast.success(`Vendor "${newVendor.name}" created successfully`);
    },
    onError: () => {
      toast.error('Failed to create vendor');
    },
  });
};

// Update vendor
export const useUpdateVendor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, vendor }: { id: string; vendor: Partial<Vendor> }) =>
      vendorsAPI.update(id, vendor),
    onSuccess: (updatedVendor, { id }) => {
      // Update specific vendor cache
      queryClient.setQueryData(['vendors', id], updatedVendor);

      // Update vendor list cache
      queryClient.setQueryData(['vendors'], (oldData: Vendor[] | undefined) => {
        return oldData?.map(v => v.id === id ? updatedVendor : v) || [];
      });

      invalidateQueries.vendors();
      toast.success(`Vendor "${updatedVendor.name}" updated successfully`);
    },
    onError: () => {
      toast.error('Failed to update vendor');
    },
  });
};

// Delete vendor
export const useDeleteVendor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => vendorsAPI.delete(id),
    onSuccess: (_, deletedId) => {
      // Remove from caches
      queryClient.removeQueries({ queryKey: ['vendors', deletedId] });
      queryClient.removeQueries({ queryKey: ['vendors', deletedId, 'stats'] });

      // Update vendor list cache
      queryClient.setQueryData(['vendors'], (oldData: Vendor[] | undefined) => {
        return oldData?.filter(v => v.id !== deletedId) || [];
      });

      invalidateQueries.vendors();
      toast.success('Vendor deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete vendor');
    },
  });
};