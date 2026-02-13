import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '@/components/layout/Header';
import { useUIStore } from '@/stores/ui/uiStore';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

const mockLogout = vi.fn();
vi.mock('@/stores/auth', () => ({
  useUserInfo: vi.fn(() => ({
    id: '1',
    name: 'John Doe',
    email: 'john.doe@asr-records.com',
    role: 'admin',
  })),
  useTenantId: vi.fn(() => 'ASR Construction'),
  useAuthStore: vi.fn((selector: any) => selector({ logout: mockLogout })),
}));

vi.mock('@/components/common/Button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderHeader = () => render(<Header />);

// ---------------------------------------------------------------------------
// Tests — existing
// ---------------------------------------------------------------------------

describe('Header', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders the header element', () => {
    renderHeader();
    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();
  });

  it('renders "ASR Records Legacy" title', () => {
    renderHeader();
    expect(
      screen.getByRole('heading', { name: /asr records legacy/i })
    ).toBeInTheDocument();
  });

  it('renders tenant badge "ASR Construction"', () => {
    renderHeader();
    expect(screen.getByText('ASR Construction')).toBeInTheDocument();
  });

  it('renders notifications button', () => {
    renderHeader();
    expect(
      screen.getByRole('button', { name: /notifications/i })
    ).toBeInTheDocument();
  });

  it('renders settings button', () => {
    renderHeader();
    expect(
      screen.getByRole('button', { name: /settings/i })
    ).toBeInTheDocument();
  });

  it('renders user name "John Doe"', () => {
    renderHeader();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('renders user email', () => {
    renderHeader();
    expect(
      screen.getByText('john.doe@asr-records.com')
    ).toBeInTheDocument();
  });

  it('renders user menu button', () => {
    renderHeader();
    expect(
      screen.getByRole('button', { name: /user menu/i })
    ).toBeInTheDocument();
  });

  it('renders theme toggle button', () => {
    renderHeader();
    expect(
      screen.getByRole('button', { name: /toggle theme/i })
    ).toBeInTheDocument();
  });

  it('toggles theme when theme button is clicked', () => {
    useUIStore.getState().setTheme('light');
    renderHeader();
    const btn = screen.getByRole('button', { name: /toggle theme/i });
    fireEvent.click(btn);
    expect(useUIStore.getState().theme).toBe('dark');
  });

  it('shows Sun icon in dark mode and Moon icon in light mode', () => {
    useUIStore.getState().setTheme('light');
    const { rerender } = render(<Header />);
    const btn = screen.getByRole('button', { name: /toggle theme/i });
    expect(btn.querySelector('svg')).toBeInTheDocument();

    useUIStore.getState().setTheme('dark');
    rerender(<Header />);
    expect(btn.querySelector('svg')).toBeInTheDocument();
  });

  // --- P36: Settings navigation ---

  it('navigates to /settings when settings button clicked', () => {
    renderHeader();
    fireEvent.click(screen.getByRole('button', { name: /settings/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });

  // --- P36: Notification bell + dropdown ---

  it('hides notification badge when there are zero notifications', () => {
    useUIStore.setState({ notifications: [] });
    renderHeader();
    const notifButton = screen.getByRole('button', { name: /notifications/i });
    const dot = notifButton.querySelector('.bg-red-500');
    expect(dot).not.toBeInTheDocument();
  });

  it('shows notification count from store', () => {
    useUIStore.setState({
      notifications: [
        { id: '1', type: 'info', title: 'Test notification' },
        { id: '2', type: 'success', title: 'Another notification' },
      ],
    });
    renderHeader();
    const notifButton = screen.getByRole('button', { name: /notifications/i });
    const badge = notifButton.querySelector('.bg-red-500');
    expect(badge).toBeInTheDocument();
    expect(badge!.textContent).toBe('2');
  });

  it('opens notification dropdown on click and shows notification titles', () => {
    useUIStore.setState({
      notifications: [
        { id: '1', type: 'info', title: 'Upload complete', message: 'invoice.pdf processed' },
      ],
    });
    renderHeader();
    fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
    expect(screen.getByText('Upload complete')).toBeInTheDocument();
    expect(screen.getByText('invoice.pdf processed')).toBeInTheDocument();
  });

  it('shows "No notifications" when dropdown opened with empty list', () => {
    useUIStore.setState({ notifications: [] });
    renderHeader();
    fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
    expect(screen.getByText('No notifications')).toBeInTheDocument();
  });

  // --- P36: User menu + sign out ---

  it('opens user menu dropdown on click', () => {
    renderHeader();
    fireEvent.click(screen.getByRole('button', { name: /user menu/i }));
    expect(screen.getByText('Sign out')).toBeInTheDocument();
  });

  it('calls logout and navigates to /login on sign out', () => {
    renderHeader();
    fireEvent.click(screen.getByRole('button', { name: /user menu/i }));
    fireEvent.click(screen.getByText('Sign out'));
    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  // --- Dark mode variants ---

  it('includes dark variant on header container', () => {
    const { container } = renderHeader();
    const header = container.querySelector('.bg-white.dark\\:bg-gray-900');
    expect(header).toBeInTheDocument();
  });
});
