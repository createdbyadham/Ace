import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/domain/auth/api';
import type { LoginCredentials, RegisterCredentials, User } from '@/domain/auth/types';

export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
};

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginCredentials) => authApi.login(credentials),
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify({
        id: data.user_id,
        email: data.email,
      }));
      queryClient.invalidateQueries({ queryKey: authKeys.user() });
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: RegisterCredentials) => authApi.register(credentials),
    onSuccess: (data) => {
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify({
          id: data.user_id,
          email: data.email,
        }));
        queryClient.invalidateQueries({ queryKey: authKeys.user() });
      }
    },
  });
}

export function useCurrentUser() {
  const token = localStorage.getItem('access_token');

  return useQuery<User>({
    queryKey: authKeys.user(),
    queryFn: authApi.getCurrentUser,
    enabled: !!token,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    queryClient.clear();
    window.location.href = '/';
  };
}

