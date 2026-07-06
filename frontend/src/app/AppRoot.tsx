import { AppProviders } from '../providers/AppProviders';
import { AppRouterProvider } from '../router/AppRouterProvider';

export function AppRoot() {
  return (
    <AppProviders>
      <AppRouterProvider />
    </AppProviders>
  );
}
