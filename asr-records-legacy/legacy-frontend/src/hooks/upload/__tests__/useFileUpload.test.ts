import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import toast from 'react-hot-toast';
import { useFileUpload } from '../useFileUpload';

const mockMutateAsync = vi.fn();

vi.mock('@/hooks/api/useDocuments', () => ({
  useDocumentUpload: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
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

const createMockFile = (
  name: string = 'test-invoice.pdf',
  type: string = 'application/pdf',
  size: number = 1024 * 1024
): File => {
  const file = new File(['mock-content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // --- Initial state ---

  it('initial state has empty uploads', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    expect(result.current.uploads).toEqual([]);
  });

  it('initial stats are all zero', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    expect(result.current.stats).toEqual({
      total: 0,
      completed: 0,
      processing: 0,
      errors: 0,
    });
  });

  // --- File validation ---

  it('uploadFile rejects unsupported file type', async () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const badFile = createMockFile('document.exe', 'application/x-msdownload', 1024);

    await act(async () => {
      await result.current.uploadFile(badFile);
    });

    expect(toast.error).toHaveBeenCalledWith(
      expect.stringContaining('not supported')
    );
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('uploadFile rejects file over 10MB', async () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const largeFile = createMockFile('big-invoice.pdf', 'application/pdf', 11 * 1024 * 1024);

    await act(async () => {
      await result.current.uploadFile(largeFile);
    });

    expect(toast.error).toHaveBeenCalledWith(
      expect.stringContaining('too large')
    );
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it('uploadFile rejects file with empty name', async () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const emptyNameFile = new File(['content'], '', { type: 'application/pdf' });
    Object.defineProperty(emptyNameFile, 'size', { value: 1024 });
    // File constructor with empty string name results in name being ''
    // which should fail the !file.name || file.name.trim() === '' check

    await act(async () => {
      await result.current.uploadFile(emptyNameFile);
    });

    expect(toast.error).toHaveBeenCalledWith('Invalid file name.');
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  // --- Accepted file types ---

  it('uploadFile accepts PDF file', async () => {
    mockMutateAsync.mockResolvedValue({ document_id: 'doc-new' });

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const pdfFile = createMockFile('invoice.pdf', 'application/pdf', 1024);

    await act(async () => {
      const promise = result.current.uploadFile(pdfFile);
      // Advance past the 2000ms setTimeout in the hook
      vi.advanceTimersByTime(2500);
      await promise;
    });

    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ file: pdfFile })
    );
  });

  it('uploadFile accepts JPEG file', async () => {
    mockMutateAsync.mockResolvedValue({ document_id: 'doc-new' });

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const jpegFile = createMockFile('receipt.jpg', 'image/jpeg', 2048);

    await act(async () => {
      const promise = result.current.uploadFile(jpegFile);
      vi.advanceTimersByTime(2500);
      await promise;
    });

    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ file: jpegFile })
    );
  });

  it('uploadFile accepts PNG file', async () => {
    mockMutateAsync.mockResolvedValue({ document_id: 'doc-new' });

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const pngFile = createMockFile('scan.png', 'image/png', 4096);

    await act(async () => {
      const promise = result.current.uploadFile(pngFile);
      vi.advanceTimersByTime(2500);
      await promise;
    });

    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ file: pngFile })
    );
  });

  // --- Upload progress & lifecycle ---

  it('uploadFile tracks upload progress', async () => {
    let capturedOnProgress: ((progress: number) => void) | undefined;
    mockMutateAsync.mockImplementation(({ onProgress }) => {
      capturedOnProgress = onProgress;
      return new Promise((resolve) => {
        // Simulate delayed resolution
        setTimeout(() => resolve({ document_id: 'doc-new' }), 100);
      });
    });

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const file = createMockFile('invoice.pdf', 'application/pdf', 1024);

    // Start the upload without awaiting completion
    let uploadPromise: Promise<any>;
    act(() => {
      uploadPromise = result.current.uploadFile(file);
    });

    // The upload should now be tracked
    await waitFor(() => {
      expect(result.current.uploads.length).toBe(1);
    });

    expect(result.current.uploads[0].status).toBe('uploading');

    // Simulate progress callback
    if (capturedOnProgress) {
      act(() => {
        capturedOnProgress!(50);
      });
    }

    await waitFor(() => {
      expect(result.current.uploads[0].progress).toBe(50);
    });

    // Complete the upload
    await act(async () => {
      vi.advanceTimersByTime(2500);
      await uploadPromise!;
    });
  });

  it('uploadFile transitions from uploading to processing to completed', async () => {
    let resolveUpload: (value: any) => void;
    mockMutateAsync.mockImplementation(() => {
      return new Promise((resolve) => {
        resolveUpload = resolve;
      });
    });

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const file = createMockFile('invoice.pdf', 'application/pdf', 1024);

    // Start the upload
    let uploadPromise: Promise<any>;
    act(() => {
      uploadPromise = result.current.uploadFile(file);
    });

    // Should be in uploading state
    await waitFor(() => {
      expect(result.current.uploads.length).toBe(1);
      expect(result.current.uploads[0].status).toBe('uploading');
    });

    // Resolve the mutation - transitions to processing
    await act(async () => {
      resolveUpload!({ document_id: 'doc-new' });
    });

    await waitFor(() => {
      expect(result.current.uploads[0].status).toBe('processing');
    });

    // Advance past the setTimeout to transition to completed
    await act(async () => {
      vi.advanceTimersByTime(2500);
      await uploadPromise!;
    });

    await waitFor(() => {
      expect(result.current.uploads[0].status).toBe('completed');
    });
  });

  it('uploadFile handles upload error', async () => {
    mockMutateAsync.mockRejectedValue(new Error('Upload failed'));

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const file = createMockFile('invoice.pdf', 'application/pdf', 1024);

    await act(async () => {
      try {
        await result.current.uploadFile(file);
      } catch {
        // expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.uploads[0].status).toBe('error');
    });

    expect(result.current.uploads[0].error).toBe('Upload failed');
    expect(toast.error).toHaveBeenCalledWith(
      expect.stringContaining('invoice.pdf')
    );
  });

  // --- Clear and remove operations ---

  it('clearCompleted removes only completed uploads', async () => {
    // Set up one completed and one errored upload
    mockMutateAsync
      .mockResolvedValueOnce({ document_id: 'doc-1' })
      .mockRejectedValueOnce(new Error('fail'));

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const goodFile = createMockFile('good.pdf', 'application/pdf', 1024);
    const badFile = createMockFile('bad.pdf', 'application/pdf', 1024);

    // Upload the good file (will complete)
    await act(async () => {
      const promise = result.current.uploadFile(goodFile);
      vi.advanceTimersByTime(2500);
      await promise;
    });

    // Upload the bad file (will error)
    await act(async () => {
      try {
        await result.current.uploadFile(badFile);
      } catch {
        // expected
      }
    });

    await waitFor(() => {
      expect(result.current.uploads.length).toBe(2);
    });

    // Clear only completed
    act(() => {
      result.current.clearCompleted();
    });

    await waitFor(() => {
      expect(result.current.uploads.length).toBe(1);
    });

    expect(result.current.uploads[0].status).toBe('error');
  });

  it('clearAll removes all uploads', async () => {
    mockMutateAsync.mockResolvedValue({ document_id: 'doc-new' });

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const file = createMockFile('invoice.pdf', 'application/pdf', 1024);

    await act(async () => {
      const promise = result.current.uploadFile(file);
      vi.advanceTimersByTime(2500);
      await promise;
    });

    await waitFor(() => {
      expect(result.current.uploads.length).toBe(1);
    });

    act(() => {
      result.current.clearAll();
    });

    expect(result.current.uploads).toEqual([]);
    expect(result.current.stats.total).toBe(0);
  });

  it('removeUpload removes specific upload by id', async () => {
    // First upload succeeds, second upload fails (no timer delay for error path)
    mockMutateAsync
      .mockResolvedValueOnce({ document_id: 'doc-1' })
      .mockRejectedValueOnce(new Error('fail'));

    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    });

    const file1 = createMockFile('first.pdf', 'application/pdf', 1024);
    const file2 = createMockFile('second.pdf', 'application/pdf', 1024);

    // Upload the first file (will complete)
    await act(async () => {
      const promise = result.current.uploadFile(file1);
      vi.advanceTimersByTime(2500);
      await promise;
    });

    // Upload the second file (will error -- no setTimeout in error path)
    await act(async () => {
      try {
        await result.current.uploadFile(file2);
      } catch {
        // expected
      }
    });

    await waitFor(() => {
      expect(result.current.uploads.length).toBe(2);
    });

    // Remove the first upload by its id
    const firstUploadId = result.current.uploads[0].id;
    const secondUploadId = result.current.uploads[1].id;

    act(() => {
      result.current.removeUpload(firstUploadId);
    });

    await waitFor(() => {
      expect(result.current.uploads.length).toBe(1);
    });

    expect(result.current.uploads[0].id).toBe(secondUploadId);
  });
});
