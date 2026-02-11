import { useAuthStore } from '../authStore';

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      isAuthenticated: false,
      tenantId: null,
      apiKey: null,
      userInfo: undefined,
    });
  });

  // ---------------------------------------------------------------------------
  // Initial State
  // ---------------------------------------------------------------------------
  describe('initial state', () => {
    it('is unauthenticated', () => {
      const { isAuthenticated } = useAuthStore.getState();
      expect(isAuthenticated).toBe(false);
    });

    it('has null tenantId', () => {
      const { tenantId } = useAuthStore.getState();
      expect(tenantId).toBeNull();
    });

    it('has null apiKey', () => {
      const { apiKey } = useAuthStore.getState();
      expect(apiKey).toBeNull();
    });

    it('has undefined userInfo', () => {
      const { userInfo } = useAuthStore.getState();
      expect(userInfo).toBeUndefined();
    });
  });

  // ---------------------------------------------------------------------------
  // login
  // ---------------------------------------------------------------------------
  describe('login', () => {
    const testApiKey = 'sk-ant-test-key-123';
    const testTenantId = 'tenant-asr-001';
    const testUserInfo = {
      id: 'user-1',
      name: 'Austin Kidwell',
      email: 'austin@asr.com',
      role: 'admin',
    };

    it('sets isAuthenticated to true', () => {
      useAuthStore.getState().login(testApiKey, testTenantId);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });

    it('stores apiKey in state', () => {
      useAuthStore.getState().login(testApiKey, testTenantId);
      expect(useAuthStore.getState().apiKey).toBe(testApiKey);
    });

    it('stores tenantId in state', () => {
      useAuthStore.getState().login(testApiKey, testTenantId);
      expect(useAuthStore.getState().tenantId).toBe(testTenantId);
    });

    it('stores userInfo in state', () => {
      useAuthStore.getState().login(testApiKey, testTenantId, testUserInfo);
      expect(useAuthStore.getState().userInfo).toEqual(testUserInfo);
    });

    it('persists api_key to localStorage', () => {
      useAuthStore.getState().login(testApiKey, testTenantId);
      expect(localStorage.getItem('api_key')).toBe(testApiKey);
    });

    it('persists tenant_id to localStorage', () => {
      useAuthStore.getState().login(testApiKey, testTenantId);
      expect(localStorage.getItem('tenant_id')).toBe(testTenantId);
    });
  });

  // ---------------------------------------------------------------------------
  // logout
  // ---------------------------------------------------------------------------
  describe('logout', () => {
    beforeEach(() => {
      // Set up an authenticated session first
      useAuthStore.getState().login('sk-ant-key', 'tenant-1', {
        id: 'u1',
        name: 'Test',
        email: 'test@asr.com',
        role: 'user',
      });
    });

    it('resets all state to defaults', () => {
      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.apiKey).toBeNull();
      expect(state.tenantId).toBeNull();
      expect(state.userInfo).toBeUndefined();
    });

    it('removes api_key from localStorage', () => {
      useAuthStore.getState().logout();
      expect(localStorage.getItem('api_key')).toBeNull();
    });

    it('removes tenant_id from localStorage', () => {
      useAuthStore.getState().logout();
      expect(localStorage.getItem('tenant_id')).toBeNull();
    });
  });

  // ---------------------------------------------------------------------------
  // updateUserInfo
  // ---------------------------------------------------------------------------
  describe('updateUserInfo', () => {
    it('updates user info without affecting auth state', () => {
      useAuthStore.getState().login('sk-ant-key', 'tenant-1');

      const newUserInfo = {
        id: 'u2',
        name: 'Updated User',
        email: 'updated@asr.com',
        role: 'manager',
      };
      useAuthStore.getState().updateUserInfo(newUserInfo);

      const state = useAuthStore.getState();
      expect(state.userInfo).toEqual(newUserInfo);
      expect(state.isAuthenticated).toBe(true);
      expect(state.apiKey).toBe('sk-ant-key');
      expect(state.tenantId).toBe('tenant-1');
    });
  });

  // ---------------------------------------------------------------------------
  // setTenantId
  // ---------------------------------------------------------------------------
  describe('setTenantId', () => {
    it('updates tenantId and persists to localStorage', () => {
      useAuthStore.getState().setTenantId('new-tenant-99');

      expect(useAuthStore.getState().tenantId).toBe('new-tenant-99');
      expect(localStorage.getItem('tenant_id')).toBe('new-tenant-99');
    });
  });
});
