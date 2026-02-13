import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Login } from '../Login';
import { useAuthStore } from '@/stores/auth';

// Mock AuthService
const mockLogin = vi.fn();
vi.mock('@/services/api/auth', () => ({
  AuthService: {
    login: (...args: unknown[]) => mockLogin(...args),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderLogin = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/login']}>
        <Login />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  useAuthStore.setState({
    isAuthenticated: false,
    tenantId: null,
    apiKey: null,
    userInfo: undefined,
  });
});

describe('Login page', () => {
  // Rendering tests
  it('renders the brand with ASR Records title', () => {
    renderLogin();
    expect(screen.getByText('ASR Records')).toBeInTheDocument();
    expect(screen.getByText('Legacy Edition')).toBeInTheDocument();
  });

  it('renders API key input', () => {
    renderLogin();
    expect(screen.getByLabelText('API Key')).toBeInTheDocument();
  });

  it('renders Tenant ID input with default value', () => {
    renderLogin();
    const input = screen.getByLabelText('Tenant ID');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('default');
  });

  it('renders Sign In button', () => {
    renderLogin();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('masks API key input (type=password)', () => {
    renderLogin();
    const input = screen.getByLabelText('API Key');
    expect(input).toHaveAttribute('type', 'password');
  });

  // Validation tests
  it('shows error when submitting empty API key', async () => {
    const user = userEvent.setup();
    renderLogin();

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(screen.getByRole('alert')).toHaveTextContent('API key is required');
    expect(mockLogin).not.toHaveBeenCalled();
  });

  // Successful login
  it('calls AuthService.login and navigates on success', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce({
      authenticated: true,
      tenant_id: 'default',
      message: 'OK',
      server_version: '2.0.0',
      capabilities: {},
    });

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('sk-ant-key-1234567890', 'default');
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('updates auth store on successful login', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce({
      authenticated: true,
      tenant_id: 'default',
      message: 'OK',
      server_version: '2.0.0',
      capabilities: {},
    });

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });
  });

  // Failed login
  it('shows error on failed login', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: 'Invalid API key' } },
    });

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'short');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid API key');
    });
  });

  it('shows error when authenticated is false', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce({
      authenticated: false,
      tenant_id: 'default',
      message: 'Failed',
      server_version: '2.0.0',
      capabilities: {},
    });

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Authentication failed');
    });
  });

  // Loading state
  it('disables inputs while loading', async () => {
    const user = userEvent.setup();
    // Never resolving promise simulates loading
    mockLogin.mockReturnValueOnce(new Promise(() => {}));

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('API Key')).toBeDisabled();
      expect(screen.getByLabelText('Tenant ID')).toBeDisabled();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
    });
  });

  // Custom tenant
  it('uses custom tenant ID when provided', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce({
      authenticated: true,
      tenant_id: 'acme',
      message: 'OK',
      server_version: '2.0.0',
      capabilities: {},
    });

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.clear(screen.getByLabelText('Tenant ID'));
    await user.type(screen.getByLabelText('Tenant ID'), 'acme');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('sk-ant-key-1234567890', 'acme');
    });
  });

  it('clears error on new submit attempt', async () => {
    const user = userEvent.setup();
    // First: reject
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: 'Bad key' } },
    });
    // Second: resolve
    mockLogin.mockResolvedValueOnce({
      authenticated: true,
      tenant_id: 'default',
      message: 'OK',
      server_version: '2.0.0',
      capabilities: {},
    });

    renderLogin();

    // First attempt — shows error
    await user.type(screen.getByLabelText('API Key'), 'bad');
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    // Second attempt — error is cleared
    await user.clear(screen.getByLabelText('API Key'));
    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // --- Dark mode variants ---

  it('includes dark variant on outer wrapper', () => {
    const { container } = renderLogin();
    const wrapper = container.querySelector('.bg-gray-50.dark\\:bg-gray-950');
    expect(wrapper).toBeInTheDocument();
  });

  it('includes dark variant on card', () => {
    const { container } = renderLogin();
    const card = container.querySelector('.bg-white.dark\\:bg-gray-800');
    expect(card).toBeInTheDocument();
  });

  // --- P58: Tenant ID persistence ---

  it('renders Remember tenant ID checkbox', () => {
    renderLogin();
    expect(screen.getByLabelText('Remember tenant ID')).toBeInTheDocument();
  });

  it('restores tenant ID from localStorage on mount', () => {
    localStorage.setItem('asr-remembered-tenant', 'acme-corp');
    renderLogin();
    expect(screen.getByLabelText('Tenant ID')).toHaveValue('acme-corp');
  });

  it('saves tenant ID to localStorage when remember is checked on login', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValueOnce({
      authenticated: true,
      tenant_id: 'saved-tenant',
      message: 'OK',
      server_version: '2.0.0',
      capabilities: {},
    });

    renderLogin();

    await user.type(screen.getByLabelText('API Key'), 'sk-ant-key-1234567890');
    await user.clear(screen.getByLabelText('Tenant ID'));
    await user.type(screen.getByLabelText('Tenant ID'), 'saved-tenant');
    await user.click(screen.getByLabelText('Remember tenant ID'));
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(localStorage.getItem('asr-remembered-tenant')).toBe('saved-tenant');
    });
  });
});
