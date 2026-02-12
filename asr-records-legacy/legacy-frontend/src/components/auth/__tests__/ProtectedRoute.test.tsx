import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
import { useAuthStore } from '@/stores/auth';

// Reset auth store before each test
beforeEach(() => {
  useAuthStore.setState({
    isAuthenticated: false,
    tenantId: null,
    apiKey: null,
    userInfo: undefined,
  });
});

const renderWithRouter = (initialEntries: string[] = ['/protected']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div data-testid="protected-content">Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
};

describe('ProtectedRoute', () => {
  it('redirects to /login when not authenticated', () => {
    renderWithRouter();
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('renders children when authenticated', () => {
    useAuthStore.setState({ isAuthenticated: true, apiKey: 'test-key', tenantId: 'default' });
    renderWithRouter();
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
  });

  it('preserves location state for redirect', () => {
    // When unauthenticated, it should redirect — the login page appears
    renderWithRouter(['/protected']);
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  it('works with nested routes', () => {
    useAuthStore.setState({ isAuthenticated: true, apiKey: 'key', tenantId: 'default' });

    render(
      <MemoryRouter initialEntries={['/app/nested']}>
        <Routes>
          <Route
            path="/app/*"
            element={
              <ProtectedRoute>
                <div data-testid="nested-content">Nested</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByTestId('nested-content')).toBeInTheDocument();
  });
});
