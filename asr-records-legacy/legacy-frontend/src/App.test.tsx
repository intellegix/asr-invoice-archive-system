import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';

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

describe('App routing', () => {
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
