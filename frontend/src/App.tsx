import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './auth/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { RequireAuth } from './auth/RequireAuth';
import { Layout } from './components/Layout/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Orders } from './pages/Orders';
import { Financial } from './pages/Financial';
import { Products } from './pages/Products';
import { Customers } from './pages/Customers';
import { Suppliers, SupplierForm } from './pages/Suppliers';
import { ServiceOrders } from './pages/ServiceOrders';
import { Proposals } from './pages/Proposals';
import { ProposalForm } from './pages/Proposals/ProposalForm';
import { SettingsPage } from './pages/Settings';
import { queryClient } from './lib/queryClient';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route
              path="/"
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="financial" element={<Financial />} />
              <Route path="orders" element={<Orders />} />
              <Route path="products" element={<Products />} />
              <Route path="customers" element={<Customers />} />
              <Route path="suppliers" element={<Suppliers />} />
              <Route path="suppliers/new" element={<SupplierForm />} />
              <Route path="suppliers/:id" element={<SupplierForm />} />
              <Route path="service-orders" element={<ServiceOrders />} />
              <Route path="proposals" element={<Proposals />} />
              <Route path="proposals/new" element={<ProposalForm />} />
              <Route path="proposals/:id/edit" element={<ProposalForm />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
