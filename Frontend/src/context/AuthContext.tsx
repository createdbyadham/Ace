import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { User, AuthState } from '@/domain/auth/types';
import { useCurrentUser, authKeys } from '@/application/auth/useAuth';
import { 
  registerAuthCallbacks, 
  unregisterAuthCallbacks, 
  getTokenExpiration,
  isTokenExpired,
  getTimeUntilExpiry 
} from '@/infrastructure/api/client';
import { authApi } from '@/domain/auth/api';

interface AuthContextValue extends AuthState {
  login: (token: string, refreshToken: string, userData: Partial<User>) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Refresh token 5 minutes before expiry
const REFRESH_BUFFER_MS = 5 * 60 * 1000;
// Check token every 60 seconds as a fallback
const TOKEN_CHECK_INTERVAL_MS = 60 * 1000;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const refreshTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const checkIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isRefreshingRef = useRef(false);

  const [authState, setAuthState] = useState<AuthState>(() => {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    
    // Check if stored token is already expired
    if (token && isTokenExpired(token, 0)) {
      // Token is expired, clear it
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      return {
        token: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      };
    }
    
    return {
      token,
      user: userStr ? JSON.parse(userStr) : null,
      isAuthenticated: !!token,
      isLoading: !!token,
    };
  });

  const { data: userData, isLoading, isError } = useCurrentUser();

  // ============================================================================
  // Core Auth Functions
  // ============================================================================

  const clearAuthState = useCallback(() => {
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

    // Clear scheduled refresh
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current);
      refreshTimeoutRef.current = null;
    }
  }, [queryClient]);

  const logout = useCallback(() => {
    clearAuthState();
    
    // Redirect to login if not already there
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }, [clearAuthState]);

  // ============================================================================
  // Token Refresh Logic
  // ============================================================================

  const refreshToken = useCallback(async (): Promise<string | null> => {
    if (isRefreshingRef.current) {
      return null;
    }

    const currentRefreshToken = localStorage.getItem('refresh_token');
    if (!currentRefreshToken) {
      return null;
    }

    isRefreshingRef.current = true;

    try {
      const response = await authApi.refreshToken(currentRefreshToken);
      
      // Update storage
      localStorage.setItem('access_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }

      // Update state
      setAuthState((prev) => ({
        ...prev,
        token: response.access_token,
      }));

      // Schedule next refresh
      scheduleTokenRefresh(response.access_token);

      console.log('Token refreshed successfully');
      return response.access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    } finally {
      isRefreshingRef.current = false;
    }
  }, []);

  const scheduleTokenRefresh = useCallback((token: string) => {
    // Clear any existing scheduled refresh
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current);
    }

    const timeUntilExpiry = getTimeUntilExpiry(token);
    const refreshIn = Math.max(0, timeUntilExpiry - REFRESH_BUFFER_MS);

    if (refreshIn > 0) {
      console.log(`Token refresh scheduled in ${Math.floor(refreshIn / 60000)} minutes`);
      
      refreshTimeoutRef.current = setTimeout(() => {
        refreshToken();
      }, refreshIn);
    } else if (timeUntilExpiry > 0) {
      // Token is about to expire, refresh immediately
      refreshToken();
    }
  }, [refreshToken]);

  // ============================================================================
  // Register callbacks with API client (dependency injection)
  // ============================================================================

  useEffect(() => {
    registerAuthCallbacks(refreshToken, logout);
    
    return () => {
      unregisterAuthCallbacks();
    };
  }, [refreshToken, logout]);

  // ============================================================================
  // Initial token check and schedule refresh
  // ============================================================================

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      // Check if token needs immediate refresh
      if (isTokenExpired(token, REFRESH_BUFFER_MS)) {
        refreshToken();
      } else {
        // Schedule refresh for later
        scheduleTokenRefresh(token);
      }
    }

    // Fallback interval check (in case setTimeout drifts or tab was inactive)
    checkIntervalRef.current = setInterval(() => {
      const currentToken = localStorage.getItem('access_token');
      
      if (!currentToken) return;

      // If token is expired, logout immediately
      if (isTokenExpired(currentToken, 0)) {
        console.log('Token expired during interval check');
        logout();
        return;
      }

      // If token is about to expire and we don't have a scheduled refresh, do it now
      if (isTokenExpired(currentToken, REFRESH_BUFFER_MS) && !refreshTimeoutRef.current) {
        refreshToken();
      }
    }, TOKEN_CHECK_INTERVAL_MS);

    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [refreshToken, scheduleTokenRefresh, logout]);

  // ============================================================================
  // Handle user data updates
  // ============================================================================

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

  // ============================================================================
  // Login handler
  // ============================================================================

  const login = useCallback((token: string, refreshTokenValue: string, userData: Partial<User>) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refreshTokenValue);
    
    const user = { 
      id: userData.id || '', 
      email: userData.email || '', 
      username: userData.username || '' 
    };
    localStorage.setItem('user', JSON.stringify(user));
    
    setAuthState({
      token,
      user: user as User,
      isAuthenticated: true,
      isLoading: false,
    });
    
    queryClient.invalidateQueries({ queryKey: authKeys.user() });

    // Schedule token refresh
    scheduleTokenRefresh(token);

    // Log token info
    const expiration = getTokenExpiration(token);
    if (expiration) {
      const expiresIn = Math.floor((expiration - Date.now()) / 60000);
      console.log(`Logged in. Token expires in ${expiresIn} minutes`);
    }
  }, [queryClient, scheduleTokenRefresh]);

  const updateUser = useCallback((user: User) => {
    setAuthState((prev) => ({ ...prev, user }));
    localStorage.setItem('user', JSON.stringify(user));
  }, []);

  // ============================================================================
  // Render
  // ============================================================================

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
