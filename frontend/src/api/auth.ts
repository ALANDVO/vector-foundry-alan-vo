// Vector Foundry - Auth API Client
// Typed API client for authentication endpoints.

import { apiClient } from './client';

export interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  first_name?: string;
  last_name?: string;
  full_name?: string;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  roles: string[];
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  last_login: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
  token_type: string;
  expires_in: number;
}

export interface LogoutResponse {
  logout_url?: string;
  message?: string;
}

export interface ProviderInfoResponse {
  provider: string;
  model: string;
  configured: boolean;
}

export const authApi = {
  async getMe(): Promise<UserResponse> {
    return apiClient.get<UserResponse>('/auth/me');
  },

  async login(redirectUrl: string = '/'): Promise<void> {
    window.location.href = `/api/v1/auth/login?redirect=${encodeURIComponent(redirectUrl)}`;
  },

  async logout(): Promise<LogoutResponse> {
    return apiClient.post<LogoutResponse>('/auth/logout');
  },

  async getProviderInfo(): Promise<ProviderInfoResponse> {
    return apiClient.get<ProviderInfoResponse>('/llm/provider', undefined, true);
  },
};