import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import { useAuthStore } from '@/stores/auth';

// ---------------------------------------------------------------------------
// Mocks — replace page components and layout to avoid their internal hooks
// ---------------------------------------------------------------------------

vi.mock('@/components/layout/Header', () => ({
  Header: () => <div data-testid="header">Header</div>,
}));

vi.mock('@/components/layout/Navigation', () => ({
  Navigation: () => <nav data-testid="navigation">Navigation</nav>,
}));

vi.mock('@/pages/Dashboard', () => ({
  Dashboard: () => <div data-testid="dashboard-page">Dashboard</div>,
}));

vi.mock('@/pages/Upload', () => ({
  Upload: () => <div data-testid="upload-page">Upload</div>,
}));

vi.mock('@/pages/Documents', () => ({
  Documents: () => <div data-testid="documents-page">Documents</div>,
}));

vi.mock('@/pages/Login', () => ({
  Login: () => <div data-testid="login-page">Login</div>,
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderApp = (initialEntries: string[] = ['/dashboard']) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  // Default: authenticated
  useAuthStore.setState({
    isAuthenticated: true,
    apiKey: 'test-key',
    tenantId: 'default',
    userInfo: undefined,
  });
});

describe('App routing (authenticated)', () => {
  it('renders Navigation sidebar', () => {
    renderApp();
    expect(screen.getByTestId('navigation')).toBeInTheDocument();
  });

  it('renders Header', () => {
    renderApp();
    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  it('renders Dashboard page on /dashboard', () => {
    renderApp(['/dashboard']);
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  it('renders Upload page on /upload', () => {
    renderApp(['/upload']);
    expect(screen.getByTestId('upload-page')).toBeInTheDocument();
  });

  it('renders Documents page on /documents', () => {
    renderApp(['/documents']);
    expect(screen.getByTestId('documents-page')).toBeInTheDocument();
  });

  it('redirects / to /dashboard', () => {
    renderApp(['/']);
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  it('redirects unknown route to /dashboard', () => {
    renderApp(['/some/unknown/route']);
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });
});

describe('App routing (unauthenticated)', () => {
  beforeEach(() => {
    useAuthStore.setState({
      isAuthenticated: false,
      apiKey: null,
      tenantId: null,
      userInfo: undefined,
    });
  });

  it('redirects to /login when unauthenticated', () => {
    renderApp(['/dashboard']);
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
  });

  it('does not render sidebar or header on /login', () => {
    renderApp(['/login']);
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('navigation')).not.toBeInTheDocument();
    expect(screen.queryByTestId('header')).not.toBeInTheDocument();
  });

  it('renders login page directly on /login', () => {
    renderApp(['/login']);
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });
});
