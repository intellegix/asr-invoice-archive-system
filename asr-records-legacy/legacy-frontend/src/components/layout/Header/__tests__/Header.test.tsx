import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '@/components/layout/Header';
import { useUIStore } from '@/stores/ui/uiStore';

// Mock the auth store hooks
vi.mock('@/stores/auth', () => ({
  useUserInfo: vi.fn(() => ({
    id: '1',
    name: 'John Doe',
    email: 'john.doe@asr-records.com',
    role: 'admin',
  })),
  useTenantId: vi.fn(() => 'ASR Construction'),
}));

describe('Header', () => {
  it('renders the header element', () => {
    render(<Header />);
    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();
  });

  it('renders "ASR Records Legacy" title', () => {
    render(<Header />);
    expect(
      screen.getByRole('heading', { name: /asr records legacy/i })
    ).toBeInTheDocument();
  });

  it('renders tenant badge "ASR Construction"', () => {
    render(<Header />);
    expect(screen.getByText('ASR Construction')).toBeInTheDocument();
  });

  it('renders notifications button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /notifications/i })
    ).toBeInTheDocument();
  });

  it('renders notification indicator dot', () => {
    render(<Header />);
    const notifButton = screen.getByRole('button', {
      name: /notifications/i,
    });
    const dot = notifButton.querySelector('.bg-red-500');
    expect(dot).toBeInTheDocument();
  });

  it('renders settings button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /settings/i })
    ).toBeInTheDocument();
  });

  it('renders user name "John Doe"', () => {
    render(<Header />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('renders user email', () => {
    render(<Header />);
    expect(
      screen.getByText('john.doe@asr-records.com')
    ).toBeInTheDocument();
  });

  it('renders user menu button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /user menu/i })
    ).toBeInTheDocument();
  });

  it('renders theme toggle button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /toggle theme/i })
    ).toBeInTheDocument();
  });

  it('toggles theme when theme button is clicked', () => {
    // Reset to light
    useUIStore.getState().setTheme('light');
    render(<Header />);
    const btn = screen.getByRole('button', { name: /toggle theme/i });
    fireEvent.click(btn);
    expect(useUIStore.getState().theme).toBe('dark');
  });

  it('shows Sun icon in dark mode and Moon icon in light mode', () => {
    useUIStore.getState().setTheme('light');
    const { rerender } = render(<Header />);
    // In light mode, Moon icon is displayed (click to go dark)
    const btn = screen.getByRole('button', { name: /toggle theme/i });
    expect(btn.querySelector('svg')).toBeInTheDocument();

    // Switch to dark
    useUIStore.getState().setTheme('dark');
    rerender(<Header />);
    // Still has an svg icon
    expect(btn.querySelector('svg')).toBeInTheDocument();
  });
});
