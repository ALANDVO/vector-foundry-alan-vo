// Vector Foundry - Frontend App Tests
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn().mockResolvedValue({
    issues: [
      {
        number: 31844,
        title: "Tracking issue for specialization (RFC 1210)",
        body: "Test body",
        html_url: "https://github.com/rust-lang/rust/issues/31844",
        state: "open",
        comments: 323,
        labels: [{ name: "F-specialization", color: "ff0000" }],
        author: { login: "rust-lang", avatar_url: "https://github.com/rust-lang.png" },
        created_at: "2019-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        checklist_progress: { completed: 1, total: 7 },
        readiness_score: 45,
      },
    ],
    total: 1,
    page: 1,
    per_page: 20,
  }),
}));

vi.mock('../api/client', () => ({
  apiClient: {
    get: mockGet,
    post: vi.fn(),
    setAccessToken: vi.fn(),
  },
}));

// Mock auth context
vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => ({
    user: { id: '1', username: 'testuser', email: 'test@example.com', roles: ['viewer'], name: 'Test User' },
    isAuthenticated: true,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
  }),
}));

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({
      issues: [
        {
          number: 31844,
          title: "Tracking issue for specialization (RFC 1210)",
          body: "Test body",
          html_url: "https://github.com/rust-lang/rust/issues/31844",
          state: "open",
          comments: 323,
          labels: [{ name: "F-specialization", color: "ff0000" }],
          author: { login: "rust-lang", avatar_url: "https://github.com/rust-lang.png" },
          created_at: "2019-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          checklist_progress: { completed: 1, total: 7 },
          readiness_score: 45,
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
    });
  });

  it('renders dashboard when authenticated', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Tracking Issues')).toBeInTheDocument();
    });
  });

  it('shows navigation with correct links', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Compare')).toBeInTheDocument();
    });
  });

  it('shows user info in header when authenticated', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('viewer')).toBeInTheDocument();
    });
  });
});