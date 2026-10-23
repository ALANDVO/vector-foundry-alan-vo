// Vector Foundry - Auth Context Tests
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { apiClient } from '../api/client';

// Mock apiClient
vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    setAccessToken: vi.fn(),
  },
}));

const mockApiClient = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  setAccessToken: ReturnType<typeof vi.fn>;
};

function TestComponent() {
  const { user, isAuthenticated, loading, login, logout, checkAuth } = useAuth();
  return (
    <div>
      <div data-testid="loading">{loading ? 'true' : 'false'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'true' : 'false'}</div>
      <div data-testid="user">{user ? JSON.stringify(user) : 'null'}</div>
      <button data-testid="login-btn" onClick={() => login()}>Login</button>
      <button data-testid="logout-btn" onClick={() => logout()}>Logout</button>
      <button data-testid="checkauth-btn" onClick={() => checkAuth()}>Check Auth</button>
    </div>
  );
}

function renderWithAuth(ui: React.ReactElement) {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it('provides loading state initially', async () => {
    renderWithAuth(<TestComponent />);
    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });
  });

  it('sets authenticated state when user data and valid tokens exist in sessionStorage', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['viewer'],
    };
    const mockTokens = {
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
      expiresAt: Date.now() + 3600000,
    };

    sessionStorage.setItem('vector-foundry-auth', JSON.stringify(mockUser));
    sessionStorage.setItem('vector-foundry-tokens', JSON.stringify(mockTokens));

    mockApiClient.get.mockResolvedValue(mockUser);

    renderWithAuth(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(screen.getByTestId('authenticated').textContent).toBe('true');
    expect(screen.getByTestId('user').textContent).toContain('testuser');
    expect(mockApiClient.setAccessToken).toHaveBeenCalledWith('test-access-token');
  });

  it('clears auth when tokens are expired', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['viewer'],
    };
    const mockTokens = {
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
      expiresAt: Date.now() - 3600000, // expired
    };

    sessionStorage.setItem('vector-foundry-auth', JSON.stringify(mockUser));
    sessionStorage.setItem('vector-foundry-tokens', JSON.stringify(mockTokens));

    renderWithAuth(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(screen.getByTestId('authenticated').textContent).toBe('false');
    expect(screen.getByTestId('user').textContent).toBe('null');
  });

  it('login redirects to backend auth endpoint', () => {
    const originalHref = window.location.href;
    Object.defineProperty(window, 'location', {
      value: { href: '', assign: vi.fn() },
      configurable: true,
    });

    renderWithAuth(<TestComponent />);

    fireEvent.click(screen.getByTestId('login-btn'));

    expect(window.location.href).toContain('/api/v1/auth/login');

    // Restore
    Object.defineProperty(window, 'location', {
      value: { href: originalHref },
      configurable: true,
    });
  });

  it('logout clears session and redirects', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['viewer'],
    };
    const mockTokens = {
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
      expiresAt: Date.now() + 3600000,
    };

    sessionStorage.setItem('vector-foundry-auth', JSON.stringify(mockUser));
    sessionStorage.setItem('vector-foundry-tokens', JSON.stringify(mockTokens));

    mockApiClient.get.mockResolvedValue(mockUser);
    mockApiClient.post.mockResolvedValue({ message: 'Logged out' });

    // Mock window.location.href setter
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      value: { href: '/', assign: vi.fn() },
      configurable: true,
    });

    renderWithAuth(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('authenticated').textContent).toBe('true');
    });

    fireEvent.click(screen.getByTestId('logout-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
    });

    expect(sessionStorage.getItem('vector-foundry-auth')).toBeNull();
    expect(sessionStorage.getItem('vector-foundry-tokens')).toBeNull();
    expect(mockApiClient.setAccessToken).toHaveBeenCalledWith(null);
    expect(window.location.href).toBe('/login');

    // Restore original location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      configurable: true,
    });
  });

  it('checkAuth fetches user when tokens are valid', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['viewer'],
    };
    const mockTokens = {
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
      expiresAt: Date.now() + 3600000,
    };

    sessionStorage.setItem('vector-foundry-auth', JSON.stringify(mockUser));
    sessionStorage.setItem('vector-foundry-tokens', JSON.stringify(mockTokens));

    mockApiClient.get.mockResolvedValue(mockUser);

    renderWithAuth(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    fireEvent.click(screen.getByTestId('checkauth-btn'));

    await waitFor(() => {
      expect(mockApiClient.get).toHaveBeenCalledWith('/auth/me');
    });
  });

  it('checkAuth clears auth on API failure', async () => {
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      roles: ['viewer'],
    };
    const mockTokens = {
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
      expiresAt: Date.now() + 3600000,
    };

    sessionStorage.setItem('vector-foundry-auth', JSON.stringify(mockUser));
    sessionStorage.setItem('vector-foundry-tokens', JSON.stringify(mockTokens));

    mockApiClient.get.mockRejectedValue(new Error('Unauthorized'));

    renderWithAuth(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    fireEvent.click(screen.getByTestId('checkauth-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
    });

    expect(sessionStorage.getItem('vector-foundry-auth')).toBeNull();
    expect(sessionStorage.getItem('vector-foundry-tokens')).toBeNull();
  });
});