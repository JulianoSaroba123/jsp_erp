import { useAuth } from './useAuth';
import { hasRolePermission } from '../rbac';
import type { PermissionAction } from '../rbac';

export function usePermissions() {
  const { user } = useAuth();

  const hasPermission = (resourceOrPermission: string, action?: PermissionAction): boolean => {
    return hasRolePermission(user?.role, resourceOrPermission, action);
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
