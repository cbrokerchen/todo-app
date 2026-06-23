import { createContext, useContext, useState, useMemo, useCallback } from 'react';
import type { ReactNode } from 'react';
import { login as apiLogin, register as apiRegister } from './api';
import type { AuthResponse } from './api';

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = 'token';

function readToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readToken());

  const handleAuthSuccess = useCallback((data: AuthResponse) => {
    storeToken(data.access_token);
    setToken(data.access_token);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const data = await apiLogin(username, password);
      handleAuthSuccess(data);
    },
    [handleAuthSuccess],
  );

  const register = useCallback(
    async (username: string, password: string) => {
      const data = await apiRegister(username, password);
      handleAuthSuccess(data);
    },
    [handleAuthSuccess],
  );

  const logout = useCallback(() => {
    clearToken();
    setToken(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: token !== null,
      login,
      register,
      logout,
    }),
    [token, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
