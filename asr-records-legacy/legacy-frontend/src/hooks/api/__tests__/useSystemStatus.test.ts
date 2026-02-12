import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { apiClient } from '@/services/api/client';
import { useSystemStatus, useSystemInfo } from '../useSystemStatus';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/services/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
  ApiClient: vi.fn(),
  queryClient: {
    invalidateQueries: vi.fn(),
  },
  invalidateQueries: {
    documents: vi.fn(),
    metrics: vi.fn(),
    vendors: vi.fn(),
    projects: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useSystemStatus hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('useSystemStatus calls /api/status endpoint', async () => {
    const mockData = {
      data: {
        system_type: 'production_server',
        version: '2.0.0',
        status: 'operational',
        services: {},
        claude_ai: 'configured',
      },
    };
    vi.mocked(apiClient.get).mockResolvedValue(mockData);

    const { result } = renderHook(() => useSystemStatus(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(apiClient.get).toHaveBeenCalledWith('/api/status');
  });

  it('useSystemInfo calls /api/v1/system/info endpoint', async () => {
    const mockData = {
      data: {
        system_type: 'production_server',
        version: '2.0.0',
        capabilities: {
          gl_accounts: { total: 79, enabled: true },
          payment_detection: { methods: 5, consensus_enabled: true },
          billing_router: { destinations: 4, audit_trails: true },
          multi_tenant: false,
          scanner_api: true,
        },
        limits: {
          max_file_size_mb: 10,
          max_batch_size: 10,
          max_scanner_clients: 5,
        },
      },
    };
    vi.mocked(apiClient.get).mockResolvedValue(mockData);

    const { result } = renderHook(() => useSystemInfo(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/info');
  });

  it('returns data from API response', async () => {
    const innerData = {
      system_type: 'production_server',
      version: '2.0.0',
      status: 'operational',
      services: { gl_accounts: { status: 'active', count: 79 } },
      claude_ai: 'configured',
    };
    vi.mocked(apiClient.get).mockResolvedValue({ data: innerData });

    const { result } = renderHook(() => useSystemStatus(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(innerData);
  });
});
