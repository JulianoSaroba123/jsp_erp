import type { ReactNode } from 'react';
import { PermissionGate } from './PermissionGate';
import type { PermissionAction } from './permissions';

export interface MenuPermissionProps {
  children: ReactNode;
  fallback?: ReactNode;
  permission?: string;
  resource?: string;
  action?: PermissionAction;
}

export function MenuPermission(props: MenuPermissionProps) {
  return <PermissionGate {...props} />;
}
