import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useAuditLogs, useDocumentAuditLogs } from '../api/useAuditLogs';
import { documentsAPI } from '@/services/api/documents';

vi.mock('@/services/api/documents', () => ({
  documentsAPI: {
    fetchAuditLogs: vi.fn(),
    fetchDocumentAuditLogs: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useAuditLogs', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns data on success', async () => {
    const mockEntries = [{ id: 1, event_type: 'upload', document_id: 'doc-1' }];
    (documentsAPI.fetchAuditLogs as ReturnType<typeof vi.fn>).mockResolvedValue(mockEntries);

    const { result } = renderHook(() => useAuditLogs(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockEntries);
  });

  it('handles empty response', async () => {
    (documentsAPI.fetchAuditLogs as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const { result } = renderHook(() => useAuditLogs(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('passes params correctly', async () => {
    (documentsAPI.fetchAuditLogs as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    const params = { tenant_id: 'tenant-1', event_type: 'upload', limit: 50 };

    renderHook(() => useAuditLogs(params), { wrapper: createWrapper() });

    await waitFor(() =>
      expect(documentsAPI.fetchAuditLogs).toHaveBeenCalledWith(params),
    );
  });
});

describe('useDocumentAuditLogs', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('is disabled when documentId is empty', () => {
    const { result } = renderHook(() => useDocumentAuditLogs(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});
