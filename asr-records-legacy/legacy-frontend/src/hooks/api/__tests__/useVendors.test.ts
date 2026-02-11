import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { vendorsAPI } from '@/services/api/vendors';
import toast from 'react-hot-toast';
import {
  useVendors,
  useVendor,
  useVendorStats,
  useCreateVendor,
  useUpdateVendor,
  useDeleteVendor,
} from '../useVendors';

vi.mock('@/services/api/vendors', () => ({
  vendorsAPI: {
    list: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getStats: vi.fn(),
  },
}));

vi.mock('@/services/api/client', () => ({
  invalidateQueries: {
    documents: vi.fn(),
    metrics: vi.fn(),
    vendors: vi.fn(),
    projects: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
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

describe('useVendors hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --- useVendors (query) ---

  it('useVendors fetches vendor list', async () => {
    const mockVendors = [
      { id: 'vendor-001', name: 'Staples Inc.' },
      { id: 'vendor-002', name: 'Home Depot' },
    ];
    vi.mocked(vendorsAPI.list).mockResolvedValue(mockVendors as any);

    const { result } = renderHook(() => useVendors(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(vendorsAPI.list).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockVendors);
  });

  // --- useVendor (single) ---

  it('useVendor fetches by id', async () => {
    const mockVendor = { id: 'vendor-001', name: 'Staples Inc.' };
    vi.mocked(vendorsAPI.getById).mockResolvedValue(mockVendor as any);

    const { result } = renderHook(() => useVendor('vendor-001'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(vendorsAPI.getById).toHaveBeenCalledWith('vendor-001');
    expect(result.current.data).toEqual(mockVendor);
  });

  // --- useVendorStats ---

  it('useVendorStats fetches stats for vendor', async () => {
    const mockStats = {
      document_count: 45,
      total_amount: 56780.5,
      common_gl_accounts: [{ code: '6100', name: 'Office Supplies' }],
    };
    vi.mocked(vendorsAPI.getStats).mockResolvedValue(mockStats);

    const { result } = renderHook(() => useVendorStats('vendor-001'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(vendorsAPI.getStats).toHaveBeenCalledWith('vendor-001');
    expect(result.current.data).toEqual(mockStats);
  });

  // --- useCreateVendor (mutation) ---

  it('useCreateVendor calls create and shows success toast', async () => {
    const newVendor = { name: 'New Vendor Co.', id: 'vendor-new' };
    vi.mocked(vendorsAPI.create).mockResolvedValue(newVendor as any);

    const { result } = renderHook(() => useCreateVendor(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ name: 'New Vendor Co.' } as any);
    });

    expect(vendorsAPI.create).toHaveBeenCalledWith({ name: 'New Vendor Co.' });
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('New Vendor Co.')
    );
  });

  // --- useUpdateVendor (mutation) ---

  it('useUpdateVendor calls update and shows success toast', async () => {
    const updatedVendor = { id: 'vendor-001', name: 'Updated Staples' };
    vi.mocked(vendorsAPI.update).mockResolvedValue(updatedVendor as any);

    const { result } = renderHook(() => useUpdateVendor(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        id: 'vendor-001',
        vendor: { name: 'Updated Staples' },
      });
    });

    expect(vendorsAPI.update).toHaveBeenCalledWith('vendor-001', { name: 'Updated Staples' });
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('Updated Staples')
    );
  });

  // --- useDeleteVendor (mutation) ---

  it('useDeleteVendor calls delete and shows success toast', async () => {
    vi.mocked(vendorsAPI.delete).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteVendor(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync('vendor-001');
    });

    expect(vendorsAPI.delete).toHaveBeenCalledWith('vendor-001');
    expect(toast.success).toHaveBeenCalledWith('Vendor deleted successfully');
  });
});
