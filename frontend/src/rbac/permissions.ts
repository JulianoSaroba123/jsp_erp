export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'export';

export interface PermissionMap {
  [role: string]: string[];
}

export const ROLE_PERMISSIONS: PermissionMap = {
  admin: [
    'orders:read',
    'orders:create',
    'orders:update',
    'orders:delete',
    'service_orders:read',
    'service_orders:create',
    'service_orders:update',
    'service_orders:delete',
    'proposals:read',
    'proposals:create',
    'proposals:update',
    'proposals:delete',
    'financial:read',
    'financial:create',
    'financial:update',
    'financial:delete',
    'customers:read',
    'customers:create',
    'customers:update',
    'customers:delete',
    'products:read',
    'products:create',
    'products:update',
    'products:delete',
    'reports:read',
    'reports:export',
    'users:read',
    'users:create',
    'users:update',
    'users:delete',
    'settings:read',
    'settings:update',
  ],
  user: [
    'orders:read',
    'orders:create',
    'orders:update',
    'service_orders:read',
    'service_orders:create',
    'service_orders:update',
    'proposals:read',
    'proposals:create',
    'proposals:update',
    'financial:read',
    'financial:create',
    'customers:read',
    'customers:create',
    'customers:update',
    'products:read',
    'products:create',
    'products:update',
    'reports:read',
    'settings:read',
  ],
  finance: [
    'financial:read',
    'financial:create',
    'financial:update',
    'financial:delete',
    'proposals:read',
    'proposals:create',
    'proposals:update',
    'proposals:delete',
    'customers:read',
    'products:read',
    'service_orders:read',
    'reports:read',
    'reports:export',
    'orders:read',
    'settings:read',
  ],
  technician: [
    'orders:read',
    'orders:create',
    'orders:update',
    'service_orders:read',
    'service_orders:create',
    'service_orders:update',
    'proposals:read',
    'proposals:create',
    'customers:read',
    'products:read',
    'reports:read',
    'settings:read',
  ],
};

export function resolvePermission(resourceOrPermission: string, action?: PermissionAction) {
  return action ? `${resourceOrPermission}:${action}` : resourceOrPermission;
}

export function hasRolePermission(
  role: string | undefined,
  resourceOrPermission: string,
  action?: PermissionAction
) {
  if (!role) {
    return false;
  }

  const rolePermissions = ROLE_PERMISSIONS[role] || [];
  return rolePermissions.includes(resolvePermission(resourceOrPermission, action));
}
