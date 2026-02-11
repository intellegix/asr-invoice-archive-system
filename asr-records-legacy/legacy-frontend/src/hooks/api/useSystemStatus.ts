import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api/client';

interface SystemStatusData {
  system_type: string;
  version: string;
  status: 'operational' | 'degraded';
  services: Record<string, { status: string; count?: number; methods?: number; destinations?: number }>;
  claude_ai: string;
}

interface SystemInfoData {
  system_type: string;
  version: string;
  capabilities: {
    gl_accounts: { total: number; enabled: boolean };
    payment_detection: { methods: number; consensus_enabled: boolean };
    billing_router: { destinations: number; audit_trails: boolean };
    multi_tenant: boolean;
    scanner_api: boolean;
  };
  limits: {
    max_file_size_mb: number;
    max_batch_size: number;
    max_scanner_clients: number;
  };
}

export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: async () => {
      const response = await apiClient.get<{ data: SystemStatusData }>('/api/status');
      return (response as any).data || response;
    },
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  });
};

export const useSystemInfo = () => {
  return useQuery({
    queryKey: ['system', 'info'],
    queryFn: async () => {
      const response = await apiClient.get<{ data: SystemInfoData }>('/api/v1/system/info');
      return (response as any).data || response;
    },
    staleTime: 10 * 60 * 1000,
    gcTime: 60 * 60 * 1000,
  });
};
