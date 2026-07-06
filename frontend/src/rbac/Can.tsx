import type { ReactNode } from 'react';
import { PermissionGate } from './PermissionGate';
import type { PermissionAction } from './permissions';

export interface CanProps {
  children: ReactNode;
  fallback?: ReactNode;
  permission?: string;
  resource?: string;
  action?: PermissionAction;
}

export function Can(props: CanProps) {
  return <PermissionGate {...props} />;
}
