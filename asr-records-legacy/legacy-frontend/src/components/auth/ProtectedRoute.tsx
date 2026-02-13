import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useIsAuthenticated, useAuthActions } from '@/stores/auth';
import { useSessionTimeout } from '@/hooks/useSessionTimeout';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = useIsAuthenticated();
  const { logout } = useAuthActions();
  const location = useLocation();

  useSessionTimeout(logout);

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
