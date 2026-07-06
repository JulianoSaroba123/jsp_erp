import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { routeConfig } from './route-config';

const router = createBrowserRouter(routeConfig);

export function AppRouterProvider() {
  return <RouterProvider router={router} />;
}
