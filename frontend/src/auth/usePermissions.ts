import { useAuth } from './useAuth';

interface PermissionMap {
  [key: string]: string[];
}

// Mapa de permissões baseado nas roles do backend (seed_rbac.py)
const ROLE_PERMISSIONS: PermissionMap = {
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

export function usePermissions() {
  const { user } = useAuth();

  // Suporta tanto hasPermission('orders:read') quanto hasPermission('orders', 'read')
  const hasPermission = (resourceOrPermission: string, action?: string): boolean => {
    if (!user) return false;
    
    const userPermissions = ROLE_PERMISSIONS[user.role] || [];
    
    // Se action foi passado, construir permissionKey
    const permissionKey = action 
      ? `${resourceOrPermission}:${action}`
      : resourceOrPermission;
    
    return userPermissions.includes(permissionKey);
  };

  const canCreate = (resource: string) => hasPermission(resource, 'create');
  const canRead = (resource: string) => hasPermission(resource, 'read');
  const canUpdate = (resource: string) => hasPermission(resource, 'update');
  const canDelete = (resource: string) => hasPermission(resource, 'delete');

  return {
    hasPermission,
    canCreate,
    canRead,
    canUpdate,
    canDelete,
    userRole: user?.role,
  };
}
