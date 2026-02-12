import { type Mock } from 'vitest';

// vi.hoisted runs before vi.mock factories, so the mock instance is available
const { mockAxiosInstance } = vi.hoisted(() => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { baseURL: 'http://localhost:8000' },
  };
  return { mockAxiosInstance };
});

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}));

import axios from 'axios';
import toast from 'react-hot-toast';
import { ApiClient } from '../ApiClient';

describe('ApiClient', () => {
  let client: ApiClient;
  let requestInterceptor: (config: any) => any;
  let responseErrorInterceptor: (error: any) => any;

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();

    client = new ApiClient();

    // Extract interceptor callbacks registered during construction
    requestInterceptor = (
      mockAxiosInstance.interceptors.request.use as Mock
    ).mock.calls[0][0];

    responseErrorInterceptor = (
      mockAxiosInstance.interceptors.response.use as Mock
    ).mock.calls[0][1];
  });

  // ---------- Construction ----------

  describe('constructor', () => {
    it('creates axios instance with correct baseURL', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'http://localhost:8000',
        }),
      );
    });

    it('creates axios instance with correct timeout', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          timeout: 30000,
        }),
      );
    });

    it('creates axios instance with correct headers', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        }),
      );
    });

    it('registers request interceptor', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalledTimes(
        1,
      );
      expect(
        mockAxiosInstance.interceptors.request.use,
      ).toHaveBeenCalledWith(expect.any(Function));
    });

    it('registers response interceptor', () => {
      expect(
        mockAxiosInstance.interceptors.response.use,
      ).toHaveBeenCalledTimes(1);
      expect(
        mockAxiosInstance.interceptors.response.use,
      ).toHaveBeenCalledWith(expect.any(Function), expect.any(Function));
    });
  });

  // ---------- Request interceptor ----------

  describe('request interceptor', () => {
    it('adds Authorization header when api_key exists in sessionStorage', () => {
      sessionStorage.setItem('api_key', 'test-api-key-123');

      const config = { headers: {} as Record<string, string> };
      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBe('Bearer test-api-key-123');
    });

    it('skips Authorization header when no api_key in sessionStorage', () => {
      const config = { headers: {} as Record<string, string> };
      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  // ---------- HTTP methods ----------

  describe('get', () => {
    it('calls client.get and returns data', async () => {
      const mockData = { id: 1, name: 'test' };
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockData });

      const result = await client.get('/test', { page: 1 });

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', {
        params: { page: 1 },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('post', () => {
    it('calls client.post and returns data', async () => {
      const mockData = { success: true };
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

      const result = await client.post('/test', { name: 'value' });

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', {
        name: 'value',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('put', () => {
    it('calls client.put and returns data', async () => {
      const mockData = { updated: true };
      mockAxiosInstance.put.mockResolvedValueOnce({ data: mockData });

      const result = await client.put('/test/1', { name: 'updated' });

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test/1', {
        name: 'updated',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('delete', () => {
    it('calls client.delete and returns data', async () => {
      const mockData = { deleted: true };
      mockAxiosInstance.delete.mockResolvedValueOnce({ data: mockData });

      const result = await client.delete('/test/1');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/1');
      expect(result).toEqual(mockData);
    });
  });

  // ---------- File upload ----------

  describe('uploadFile', () => {
    it('creates FormData with file and calls client.post', async () => {
      const file = new File(['content'], 'invoice.pdf', {
        type: 'application/pdf',
      });
      const mockData = { document_id: 'abc-123' };
      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockData });

      const result = await client.uploadFile('/invoices', file);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/invoices',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
        }),
      );
      expect(result).toEqual(mockData);
    });

    it('tracks progress via onUploadProgress callback', async () => {
      const file = new File(['content'], 'invoice.pdf', {
        type: 'application/pdf',
      });
      mockAxiosInstance.post.mockResolvedValueOnce({ data: {} });

      const onProgress = vi.fn();
      await client.uploadFile('/invoices', file, onProgress);

      // Extract the onUploadProgress callback passed to axios
      const callArgs = mockAxiosInstance.post.mock.calls[0][2];
      expect(callArgs).toHaveProperty('onUploadProgress');

      // Simulate a progress event
      callArgs.onUploadProgress({ loaded: 50, total: 100 });
      expect(onProgress).toHaveBeenCalledWith(50);

      callArgs.onUploadProgress({ loaded: 100, total: 100 });
      expect(onProgress).toHaveBeenCalledWith(100);
    });
  });

  // ---------- Error handler (via response interceptor) ----------

  describe('error handler', () => {
    const makeAxiosError = (status: number, message?: string) => ({
      response: {
        status,
        data: message ? { message } : {},
      },
      message: 'Request failed',
    });

    it('shows toast for 400 error with message', async () => {
      const error = makeAxiosError(400, 'Bad input');

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith('Invalid request: Bad input');
    });

    it('shows toast for 401 error', async () => {
      const error = makeAxiosError(401);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith('Authentication required');
    });

    it('shows toast for 403 error', async () => {
      const error = makeAxiosError(403);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith('Access denied');
    });

    it('shows toast for 404 error', async () => {
      const error = makeAxiosError(404);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith('Resource not found');
    });

    it('shows toast for 413 error', async () => {
      const error = makeAxiosError(413);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith('File too large (max 10MB)');
    });

    it('shows toast for 429 error', async () => {
      const error = makeAxiosError(429);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith(
        'Too many requests. Please wait.',
      );
    });

    it('shows toast for 500 error', async () => {
      const error = makeAxiosError(500);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith(
        'Server error. Please try again.',
      );
    });

    it('shows default toast for unknown error status', async () => {
      const error = makeAxiosError(502);

      await expect(responseErrorInterceptor(error)).rejects.toEqual(error);
      expect(toast.error).toHaveBeenCalledWith(
        'An unexpected error occurred',
      );
    });
  });
});
