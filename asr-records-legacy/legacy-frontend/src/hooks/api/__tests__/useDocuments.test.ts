import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { documentsAPI } from '@/services/api/documents';
import { invalidateQueries } from '@/services/api/client';
import toast from 'react-hot-toast';
import {
  useDocuments,
  useDocument,
  useDocumentQuickSearch,
  useDocumentClassification,
  useDocumentUpload,
  useDocumentSearch,
  useDocumentReprocess,
  useDocumentDelete,
  useDocumentBatchProcess,
} from '../useDocuments';

vi.mock('@/services/api/documents', () => ({
  documentsAPI: {
    list: vi.fn(),
    getById: vi.fn(),
    upload: vi.fn(),
    search: vi.fn(),
    quickSearch: vi.fn(),
    reprocess: vi.fn(),
    delete: vi.fn(),
    getClassification: vi.fn(),
    batchProcess: vi.fn(),
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

let queryClient: QueryClient;

const createWrapper = () => {
  queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useDocuments hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // --- useDocuments (query) ---

  it('useDocuments fetches documents list', async () => {
    const mockDocs = [
      { id: 'doc-001', filename: 'invoice-001.pdf' },
      { id: 'doc-002', filename: 'invoice-002.pdf' },
    ];
    vi.mocked(documentsAPI.list).mockResolvedValue(mockDocs as any);

    const { result } = renderHook(() => useDocuments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(documentsAPI.list).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockDocs);
  });

  it('useDocuments passes filters to API', async () => {
    const filters = { vendor: 'Staples', limit: 10, offset: 0 };
    const mockDocs = [{ id: 'doc-001', filename: 'invoice-001.pdf' }];
    vi.mocked(documentsAPI.list).mockResolvedValue(mockDocs as any);

    const { result } = renderHook(() => useDocuments(filters), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(documentsAPI.list).toHaveBeenCalledWith(filters);
  });

  // --- useDocument (single) ---

  it('useDocument fetches by id', async () => {
    const mockDoc = { id: 'doc-001', filename: 'invoice-001.pdf' };
    vi.mocked(documentsAPI.getById).mockResolvedValue(mockDoc as any);

    const { result } = renderHook(() => useDocument('doc-001'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(documentsAPI.getById).toHaveBeenCalledWith('doc-001');
    expect(result.current.data).toEqual(mockDoc);
  });

  it('useDocument is disabled when id is empty', () => {
    const { result } = renderHook(() => useDocument(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(documentsAPI.getById).not.toHaveBeenCalled();
  });

  // --- useDocumentQuickSearch ---

  it('useDocumentQuickSearch fetches when query > 2 chars', async () => {
    const mockResults = [{ id: 'doc-001', filename: 'invoice.pdf' }];
    vi.mocked(documentsAPI.quickSearch).mockResolvedValue(mockResults as any);

    const { result } = renderHook(() => useDocumentQuickSearch('inv', true), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(documentsAPI.quickSearch).toHaveBeenCalledWith('inv');
    expect(result.current.data).toEqual(mockResults);
  });

  it('useDocumentQuickSearch is disabled when query <= 2 chars', () => {
    const { result } = renderHook(() => useDocumentQuickSearch('in', true), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(documentsAPI.quickSearch).not.toHaveBeenCalled();
  });

  // --- useDocumentClassification ---

  it('useDocumentClassification fetches classification details', async () => {
    const mockClassification = {
      gl_account_code: '6100',
      payment_status: 'unpaid',
      confidence: 96.5,
    };
    vi.mocked(documentsAPI.getClassification).mockResolvedValue(mockClassification);

    const { result } = renderHook(() => useDocumentClassification('doc-001'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(documentsAPI.getClassification).toHaveBeenCalledWith('doc-001');
    expect(result.current.data).toEqual(mockClassification);
  });

  it('useDocumentClassification is disabled when id is empty', () => {
    const { result } = renderHook(() => useDocumentClassification(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(documentsAPI.getClassification).not.toHaveBeenCalled();
  });

  // --- useDocumentUpload (mutation) ---

  it('useDocumentUpload calls upload and returns result', async () => {
    const mockResponse = { document_id: 'doc-new-001', processing_status: 'processing' };
    vi.mocked(documentsAPI.upload).mockResolvedValue(mockResponse as any);

    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    const { result } = renderHook(() => useDocumentUpload(), {
      wrapper: createWrapper(),
    });

    let uploadResult: any;
    await act(async () => {
      uploadResult = await result.current.mutateAsync({ file: mockFile });
    });

    expect(documentsAPI.upload).toHaveBeenCalledWith(mockFile, undefined);
    expect(uploadResult).toEqual(mockResponse);
  });

  it('useDocumentUpload invalidates documents and metrics on success', async () => {
    vi.mocked(documentsAPI.upload).mockResolvedValue({ document_id: 'doc-new' } as any);

    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    const { result } = renderHook(() => useDocumentUpload(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ file: mockFile });
    });

    expect(invalidateQueries.documents).toHaveBeenCalled();
    expect(invalidateQueries.metrics).toHaveBeenCalled();
  });

  it('useDocumentUpload shows toast on success', async () => {
    vi.mocked(documentsAPI.upload).mockResolvedValue({ document_id: 'doc-new' } as any);

    const mockFile = new File(['content'], 'invoice.pdf', { type: 'application/pdf' });

    const { result } = renderHook(() => useDocumentUpload(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ file: mockFile });
    });

    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('invoice.pdf')
    );
  });

  // --- useDocumentSearch (mutation) ---

  it('useDocumentSearch calls search mutation', async () => {
    const mockResults = { documents: [], total: 0, filters: {}, facets: [] };
    vi.mocked(documentsAPI.search).mockResolvedValue(mockResults);

    const { result } = renderHook(() => useDocumentSearch(), {
      wrapper: createWrapper(),
    });

    let searchResult: any;
    await act(async () => {
      searchResult = await result.current.mutateAsync({
        query: 'staples',
        filters: { limit: 20 },
      });
    });

    expect(documentsAPI.search).toHaveBeenCalledWith('staples', { limit: 20 });
    expect(searchResult).toEqual(mockResults);
  });

  // --- useDocumentReprocess (mutation) ---

  it('useDocumentReprocess invalidates after success', async () => {
    vi.mocked(documentsAPI.reprocess).mockResolvedValue({ status: 'reprocessing' });

    const { result } = renderHook(() => useDocumentReprocess(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync('doc-001');
    });

    expect(documentsAPI.reprocess).toHaveBeenCalledWith('doc-001');
    expect(invalidateQueries.documents).toHaveBeenCalled();
    expect(invalidateQueries.metrics).toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith('Document reprocessing started');
  });

  // --- useDocumentDelete (mutation) ---

  it('useDocumentDelete removes from cache on success', async () => {
    vi.mocked(documentsAPI.delete).mockResolvedValue(undefined);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDocumentDelete(), { wrapper });

    // Spy on the queryClient created by the wrapper
    const removeSpy = vi.spyOn(queryClient, 'removeQueries');

    await act(async () => {
      await result.current.mutateAsync('doc-001');
    });

    expect(documentsAPI.delete).toHaveBeenCalledWith('doc-001');
    expect(removeSpy).toHaveBeenCalledWith({ queryKey: ['documents', 'doc-001'] });
    expect(invalidateQueries.documents).toHaveBeenCalled();
    expect(invalidateQueries.metrics).toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith('Document deleted successfully');
  });

  it('useDocumentDelete shows error toast on failure', async () => {
    vi.mocked(documentsAPI.delete).mockRejectedValue(new Error('Not found'));

    const { result } = renderHook(() => useDocumentDelete(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      try {
        await result.current.mutateAsync('doc-999');
      } catch {
        // expected to throw
      }
    });

    expect(toast.error).toHaveBeenCalledWith('Failed to delete document');
  });

  // --- useDocumentBatchProcess (mutation) ---

  it('useDocumentBatchProcess invalidates on success', async () => {
    vi.mocked(documentsAPI.batchProcess).mockResolvedValue({ status: 'started' });

    const { result } = renderHook(() => useDocumentBatchProcess(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync(['doc-001', 'doc-002', 'doc-003']);
    });

    expect(documentsAPI.batchProcess).toHaveBeenCalledWith(['doc-001', 'doc-002', 'doc-003']);
    expect(invalidateQueries.documents).toHaveBeenCalled();
    expect(invalidateQueries.metrics).toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('3')
    );
  });
});
