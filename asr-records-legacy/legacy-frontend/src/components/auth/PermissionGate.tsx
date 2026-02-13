import React from 'react';
import { usePermission } from '@/hooks/usePermission';
import type { PermissionResource, PermissionAction } from '@/types/auth/auth';

interface PermissionGateProps {
  resource: PermissionResource;
  action: PermissionAction;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  resource,
  action,
  fallback = null,
  children,
}) => {
  const allowed = usePermission(resource, action);
  return <>{allowed ? children : fallback}</>;
};
