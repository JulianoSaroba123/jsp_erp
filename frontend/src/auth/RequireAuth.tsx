import { AuthorizedRoute } from '../rbac';

interface RequireAuthProps {
  children: JSX.Element;
}

export function RequireAuth({ children }: RequireAuthProps) {
  return <AuthorizedRoute>{children}</AuthorizedRoute>;
}
