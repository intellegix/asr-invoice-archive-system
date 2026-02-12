vi.mock('../../client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { apiClient } from '../../client';
import { AuthService } from '../AuthService';

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('calls POST /auth/login with api_key and tenant_id', async () => {
      const mockResponse = {
        authenticated: true,
        tenant_id: 'default',
        message: 'Authenticated successfully',
        server_version: '2.0.0',
        capabilities: { gl_accounts: 79 },
      };
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await AuthService.login('sk-ant-key-123456', 'default');

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        api_key: 'sk-ant-key-123456',
        tenant_id: 'default',
      });
      expect(result).toEqual(mockResponse);
    });

    it('uses default tenant when none provided', async () => {
      (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ authenticated: true });

      await AuthService.login('sk-ant-key-123456');

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        api_key: 'sk-ant-key-123456',
        tenant_id: 'default',
      });
    });

    it('propagates errors from apiClient', async () => {
      const error = new Error('Network error');
      (apiClient.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(AuthService.login('key')).rejects.toThrow('Network error');
    });
  });

  describe('me', () => {
    it('calls GET /auth/me', async () => {
      const mockResponse = {
        authenticated: true,
        tenant_id: 'default',
        api_keys_required: true,
      };
      (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      const result = await AuthService.me();

      expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockResponse);
    });

    it('propagates errors from apiClient', async () => {
      const error = new Error('Unauthorized');
      (apiClient.get as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      await expect(AuthService.me()).rejects.toThrow('Unauthorized');
    });
  });
});
