import type { ReactNode } from 'react';
import { usePermissions } from '../auth/usePermissions';
import type { PermissionAction } from './permissions';

export interface PermissionGateProps {
  children: ReactNode;
  fallback?: ReactNode;
  permission?: string;
  resource?: string;
  action?: PermissionAction;
  anyOf?: string[];
  allOf?: string[];
}

export function PermissionGate({
  children,
  fallback = null,
  permission,
  resource,
  action,
  anyOf,
  allOf,
}: PermissionGateProps) {
  const { hasPermission } = usePermissions();

  let allowed = true;

  if (permission) {
    allowed = hasPermission(permission);
  }

  if (resource) {
    allowed = hasPermission(resource, action);
  }

  if (anyOf && anyOf.length > 0) {
    allowed = anyOf.some((currentPermission) => hasPermission(currentPermission));
  }

  if (allOf && allOf.length > 0) {
    allowed = allOf.every((currentPermission) => hasPermission(currentPermission));
  }

  return allowed ? <>{children}</> : <>{fallback}</>;
}
