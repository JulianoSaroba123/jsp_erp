import { ReactNode } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../auth/AuthContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import { queryClient } from '../lib/queryClient';

interface AppProvidersProps {
  children: ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
