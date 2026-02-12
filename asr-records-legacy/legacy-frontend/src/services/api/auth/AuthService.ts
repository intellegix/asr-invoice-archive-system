import { apiClient } from '../client';

export interface LoginResponse {
  authenticated: boolean;
  tenant_id: string;
  message: string;
  server_version: string;
  capabilities: Record<string, unknown>;
}

export interface AuthMeResponse {
  authenticated: boolean;
  tenant_id: string;
  api_keys_required: boolean;
}

export const AuthService = {
  async login(apiKey: string, tenantId: string = 'default'): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/auth/login', {
      api_key: apiKey,
      tenant_id: tenantId,
    });
  },

  async me(): Promise<AuthMeResponse> {
    return apiClient.get<AuthMeResponse>('/auth/me');
  },
};
