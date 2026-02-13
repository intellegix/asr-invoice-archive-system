import { useUserInfo } from '@/stores/auth/authStore';
import type { PermissionResource, PermissionAction } from '@/types/auth/auth';

/**
 * Check whether the current user has a specific permission.
 * Returns `true` (permissive) when no permissions array is present,
 * which covers dev/API-key auth where RBAC is not enforced.
 */
export function usePermission(
  resource: PermissionResource,
  action: PermissionAction,
): boolean {
  const userInfo = useUserInfo();

  // No user or no permissions array → permissive fallback (dev / API-key auth)
  const permissions = (userInfo as any)?.permissions;
  if (!permissions || !Array.isArray(permissions)) return true;

  return permissions.some(
    (p: { resource: string; actions: string[] }) =>
      p.resource === resource && p.actions.includes(action),
  );
}
