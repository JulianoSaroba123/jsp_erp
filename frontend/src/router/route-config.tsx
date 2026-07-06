import { Navigate, RouteObject } from 'react-router-dom';
import { RequireAuth } from '../auth/RequireAuth';
import { MainLayout } from '../layouts/MainLayout';
import { Login } from '../pages/Login';
import { Dashboard } from '../pages/Dashboard';
import { Orders } from '../pages/Orders';
import { Financial } from '../pages/Financial';
import { Products } from '../pages/Products';
import { Customers } from '../pages/Customers';
import { Suppliers, SupplierForm } from '../pages/Suppliers';
import { ServiceOrders } from '../pages/ServiceOrders';
import { Proposals } from '../pages/Proposals';
import { ProposalForm } from '../pages/Proposals/ProposalForm';
import { SettingsPage } from '../pages/Settings';

export const routeConfig: RouteObject[] = [
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <MainLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to='/dashboard' replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'financial', element: <Financial /> },
      { path: 'orders', element: <Orders /> },
      { path: 'products', element: <Products /> },
      { path: 'customers', element: <Customers /> },
      { path: 'suppliers', element: <Suppliers /> },
      { path: 'suppliers/new', element: <SupplierForm /> },
      { path: 'suppliers/:id', element: <SupplierForm /> },
      { path: 'service-orders', element: <ServiceOrders /> },
      { path: 'proposals', element: <Proposals /> },
      { path: 'proposals/new', element: <ProposalForm /> },
      { path: 'proposals/:id/edit', element: <ProposalForm /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to='/dashboard' replace />,
  },
];
