// Vector Foundry - API Client
import { API_CONFIG } from './config';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  skipAuth?: boolean;
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = new URL(path, this.baseUrl || window.location.origin);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    return url.toString();
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, skipAuth, headers, ...fetchOptions } = options;
    
    const requestHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (!skipAuth && this.accessToken) {
      (requestHeaders as Record<string, string>)['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const url = this.buildUrl(path, params);

    const response = await fetch(url, {
      ...fetchOptions,
      headers: requestHeaders,
      credentials: 'include',
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // Use default error message
      }
      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async get<T>(path: string, params?: Record<string, string | number | boolean | undefined>, skipAuth = false): Promise<T> {
    return this.request<T>(path, { method: 'GET', params, skipAuth });
  }

  async post<T>(path: string, body?: unknown, skipAuth = false): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      skipAuth,
    });
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' });
  }

  // Health endpoints
  async healthCheck() {
    return this.get<{ status: string; service: string }>('/health', undefined, true);
  }

  async readinessCheck() {
    return this.get<{ status: string; service: string }>('/health/ready', undefined, true);
  }
}

export const apiClient = new ApiClient(API_CONFIG.baseUrl);