export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

export interface AuthLoginResponse {
  access_token: string;
  user: AuthUser;
}

export interface AuthContextValue {
  isAuthenticated: boolean;
  loading: boolean;
  user: AuthUser | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}
