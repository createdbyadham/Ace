import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { User, AuthState } from '@/domain/auth/types';
import { useCurrentUser, authKeys } from '@/application/auth/useAuth';

interface AuthContextValue extends AuthState {
  login: (token: string, refreshToken: string, userData: Partial<User>) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [authState, setAuthState] = useState<AuthState>(() => {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    return {
      token,
      user: userStr ? JSON.parse(userStr) : null,
      isAuthenticated: !!token,
      isLoading: !!token,
    };
  });

  const { data: userData, isLoading, isError } = useCurrentUser();

  useEffect(() => {
    if (userData) {
      setAuthState((prev) => ({
        ...prev,
        user: userData,
        isLoading: false,
        isAuthenticated: true,
      }));
      localStorage.setItem('user', JSON.stringify(userData));
    } else if (isError) {
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
      }));
    } else if (!authState.token) {
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
      }));
    }
  }, [userData, isError, isLoading, authState.token]);

  const login = useCallback((token: string, refreshToken: string, userData: Partial<User>) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refreshToken);
    const user = { id: userData.id || '', email: userData.email || '', username: userData.username || '' };
    localStorage.setItem('user', JSON.stringify(user));
    setAuthState({
      token,
      user: user as User,
      isAuthenticated: true,
      isLoading: false,
    });
    queryClient.invalidateQueries({ queryKey: authKeys.user() });
  }, [queryClient]);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setAuthState({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
    queryClient.clear();
  }, [queryClient]);

  const updateUser = useCallback((user: User) => {
    setAuthState((prev) => ({ ...prev, user }));
    localStorage.setItem('user', JSON.stringify(user));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;

