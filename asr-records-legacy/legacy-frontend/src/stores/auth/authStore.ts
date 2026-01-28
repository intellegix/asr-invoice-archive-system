import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  isAuthenticated: boolean;
  tenantId: string | null;
  apiKey: string | null;
  userInfo?: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
}

interface AuthActions {
  login: (apiKey: string, tenantId: string, userInfo?: AuthState['userInfo']) => void;
  logout: () => void;
  updateUserInfo: (userInfo: AuthState['userInfo']) => void;
  setTenantId: (tenantId: string) => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      isAuthenticated: false,
      tenantId: null,
      apiKey: null,
      userInfo: undefined,

      // Actions
      login: (apiKey, tenantId, userInfo) => {
        localStorage.setItem('api_key', apiKey);
        localStorage.setItem('tenant_id', tenantId);

        set({
          isAuthenticated: true,
          apiKey,
          tenantId,
          userInfo,
        });
      },

      logout: () => {
        localStorage.removeItem('api_key');
        localStorage.removeItem('tenant_id');

        set({
          isAuthenticated: false,
          apiKey: null,
          tenantId: null,
          userInfo: undefined,
        });
      },

      updateUserInfo: (userInfo) => {
        set({ userInfo });
      },

      setTenantId: (tenantId) => {
        localStorage.setItem('tenant_id', tenantId);
        set({ tenantId });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        tenantId: state.tenantId,
        apiKey: state.apiKey,
        userInfo: state.userInfo,
      }),
    }
  )
);

// Selectors
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useTenantId = () => useAuthStore((state) => state.tenantId);
export const useApiKey = () => useAuthStore((state) => state.apiKey);
export const useUserInfo = () => useAuthStore((state) => state.userInfo);

// Actions
export const useAuthActions = () => useAuthStore((state) => ({
  login: state.login,
  logout: state.logout,
  updateUserInfo: state.updateUserInfo,
  setTenantId: state.setTenantId,
}));