// Vector Foundry - Authentication Context
import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { apiClient } from '../api/client';

interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  name?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (redirectUrl?: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'vector-foundry-auth';
const TOKEN_KEY = 'vector-foundry-tokens';

interface TokenData {
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
  idToken?: string;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStoredAuth = useCallback(async () => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      const tokenData = sessionStorage.getItem(TOKEN_KEY);
      
      if (stored && tokenData) {
        const parsedUser = JSON.parse(stored) as User;
        const parsedTokens = JSON.parse(tokenData) as TokenData;
        
        // Check if token is still valid
        if (parsedTokens.expiresAt > Date.now() + 30000) {
          setUser(parsedUser);
          apiClient.setAccessToken(parsedTokens.accessToken);
          return;
        }
      }
    } catch {
      // Ignore parse errors
    } finally {
      setLoading(false);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadStoredAuth();
  }, [loadStoredAuth]);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const userData = await apiClient.get<{ id: string; email: string; roles: string[] }>('/auth/me');
      setUser(userData);
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        parsed.id = userData.id;
        parsed.email = userData.email;
        parsed.roles = userData.roles;
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
      }
    } catch {
      clearAuth();
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAuth = () => {
    setUser(null);
    sessionStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    apiClient.setAccessToken(null);
  };

  const login = (redirectUrl?: string) => {
    const params = new URLSearchParams();
    if (redirectUrl) params.set('redirect', redirectUrl);
    window.location.href = `/api/v1/auth/login?${params.toString()}`;
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore logout errors
    } finally {
      clearAuth();
      window.location.href = '/login';
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}