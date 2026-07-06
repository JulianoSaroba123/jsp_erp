import type { JSX } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import { usePermissions } from '../auth/usePermissions';
import { LoadingBlock } from '../components/ui';
import type { PermissionAction } from './permissions';

export interface AuthorizedRouteProps {
  children: JSX.Element;
  permission?: string;
  resource?: string;
  action?: PermissionAction;
  redirectTo?: string;
  forbiddenRedirectTo?: string;
}

export function AuthorizedRoute({
  children,
  permission,
  resource,
  action,
  redirectTo = '/login',
  forbiddenRedirectTo = '/',
}: AuthorizedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const { hasPermission } = usePermissions();
  const location = useLocation();

  if (loading) {
    return <LoadingBlock title="Validando sessao" description="Aguarde enquanto validamos seu acesso." />;
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  if (permission && !hasPermission(permission)) {
    return <Navigate to={forbiddenRedirectTo} replace />;
  }

  if (resource && !hasPermission(resource, action)) {
    return <Navigate to={forbiddenRedirectTo} replace />;
  }

  return children;
}
