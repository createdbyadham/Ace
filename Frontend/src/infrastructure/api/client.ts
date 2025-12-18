import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Token Management - Centralized token operations
// ============================================================================

type TokenRefreshCallback = () => Promise<string | null>;
type LogoutCallback = () => void;

let onTokenRefresh: TokenRefreshCallback | null = null;
let onLogout: LogoutCallback | null = null;

/**
 * Register callbacks from AuthContext - this creates a clean dependency injection
 * pattern instead of using window events or direct imports that create circular deps.
 */
export const registerAuthCallbacks = (
  refreshCallback: TokenRefreshCallback,
  logoutCallback: LogoutCallback
) => {
  onTokenRefresh = refreshCallback;
  onLogout = logoutCallback;
};

export const unregisterAuthCallbacks = () => {
  onTokenRefresh = null;
  onLogout = null;
};

// ============================================================================
// Token Utilities
// ============================================================================

export const getTokenExpiration = (token: string): number | null => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
};

export const isTokenExpired = (token: string, bufferMs = 0): boolean => {
  const expiration = getTokenExpiration(token);
  if (!expiration) return true;
  return Date.now() >= expiration - bufferMs;
};

export const getTimeUntilExpiry = (token: string): number => {
  const expiration = getTokenExpiration(token);
  if (!expiration) return 0;
  return Math.max(0, expiration - Date.now());
};

// ============================================================================
// Request Queue for handling concurrent requests during token refresh
// ============================================================================

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// ============================================================================
// Interceptors
// ============================================================================

// Request interceptor - attach token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response interceptor - handle 401 and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Skip refresh for auth endpoints or already retried requests
    const isAuthEndpoint = originalRequest.url?.includes('/test/signin') ||
                          originalRequest.url?.includes('/test/signup') ||
                          originalRequest.url?.includes('/test/refresh');

    if (error.response?.status !== 401 || originalRequest._retry || isAuthEndpoint) {
      return Promise.reject(error);
    }

    // If we don't have a refresh callback registered, just logout
    if (!onTokenRefresh) {
      onLogout?.();
      return Promise.reject(error);
    }

    // Queue concurrent requests while refreshing
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }
        return apiClient(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const newToken = await onTokenRefresh();

      if (newToken) {
        processQueue(null, newToken);
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } else {
        const refreshError = new Error('Token refresh failed');
        processQueue(refreshError, null);
        onLogout?.();
        return Promise.reject(refreshError);
      }
    } catch (refreshError) {
      processQueue(refreshError as Error, null);
      onLogout?.();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;
