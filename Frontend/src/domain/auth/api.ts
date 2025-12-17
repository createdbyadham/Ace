import apiClient from '@/infrastructure/api/client';
import type { LoginCredentials, RegisterCredentials, AuthResponse, User } from './types';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>('/test/signin', credentials);
    return data;
  },

  register: async (credentials: RegisterCredentials): Promise<AuthResponse> => {
    const { data } = await apiClient.post<AuthResponse>('/test/signup', credentials);
    return data;
  },

  getCurrentUser: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/users/me');
    return data;
  },
};

export default authApi;

