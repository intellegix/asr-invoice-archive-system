import { renderHook } from '@testing-library/react';
import { usePermission } from '../usePermission';
import { useAuthStore } from '@/stores/auth/authStore';

describe('usePermission', () => {
  afterEach(() => {
    useAuthStore.setState({ userInfo: undefined });
  });

  it('returns true when user has no permissions array (permissive fallback)', () => {
    useAuthStore.setState({ userInfo: { authenticated: true } as any });
    const { result } = renderHook(() => usePermission('documents', 'read'));
    expect(result.current).toBe(true);
  });

  it('returns true when user is null (no user)', () => {
    useAuthStore.setState({ userInfo: undefined });
    const { result } = renderHook(() => usePermission('documents', 'read'));
    expect(result.current).toBe(true);
  });

  it('returns true when user has matching permission', () => {
    useAuthStore.setState({
      userInfo: {
        authenticated: true,
        permissions: [{ resource: 'documents', actions: ['read', 'create'] }],
      } as any,
    });
    const { result } = renderHook(() => usePermission('documents', 'read'));
    expect(result.current).toBe(true);
  });

  it('returns false when user does not have matching permission', () => {
    useAuthStore.setState({
      userInfo: {
        authenticated: true,
        permissions: [{ resource: 'documents', actions: ['read'] }],
      } as any,
    });
    const { result } = renderHook(() => usePermission('classifications', 'classify'));
    expect(result.current).toBe(false);
  });
});
