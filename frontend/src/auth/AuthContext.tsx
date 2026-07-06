import { createContext, useEffect, useState, type ReactNode } from 'react';
import { apiClient } from '../api/client';
import { clearAccessToken, getAccessToken, setAccessToken } from './auth-storage';
import type { AuthContextValue, AuthLoginResponse, AuthUser } from './auth-types';
import { setForbiddenHandler, setUnauthorizedHandler } from '../services/http/client';

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);

  const clearSession = () => {
    clearAccessToken();
    setIsAuthenticated(false);
    setUser(null);
  };

  const refreshUser = async () => {
    const response = await apiClient.get<AuthUser>('/auth/me');
    setUser(response.data);
    setIsAuthenticated(true);
  };

  useEffect(() => {
    const disposeUnauthorizedHandler = setUnauthorizedHandler(() => {
      clearSession();
    });
    const disposeForbiddenHandler = setForbiddenHandler(() => {
      return;
    });

    async function bootstrapAuth() {
      const token = getAccessToken();

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        await refreshUser();
      } catch (error) {
        clearSession();
      } finally {
        setLoading(false);
      }
    }

    void bootstrapAuth();

    return () => {
      disposeUnauthorizedHandler();
      disposeForbiddenHandler();
    };
  }, []);

  const login = async (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    const response = await apiClient.post<AuthLoginResponse>('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    
    const { access_token, user: userData } = response.data;
    setAccessToken(access_token);
    setIsAuthenticated(true);
    setUser(userData);
  };

  const logout = () => {
    clearSession();
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, user, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}
