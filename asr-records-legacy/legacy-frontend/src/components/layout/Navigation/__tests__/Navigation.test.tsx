import { screen, fireEvent } from '@testing-library/react';
import { Navigation } from '@/components/layout/Navigation';
import { renderWithProviders } from '@/tests/helpers/renderWithProviders';
import { useUIStore } from '@/stores/ui/uiStore';

// Mock the hooks that Navigation now uses
vi.mock('@/hooks/api/useDashboard', () => ({
  useDashboardMetrics: vi.fn(() => ({
    data: { totalDocuments: 1234, classificationAccuracy: 94, paymentAccuracy: 94 },
    isLoading: false,
    dataUpdatedAt: Date.now() - 120000, // 2 minutes ago
  })),
}));

vi.mock('@/hooks/api/useSystemStatus', () => ({
  useSystemStatus: vi.fn(() => ({
    data: { status: 'operational' },
  })),
  useSystemInfo: vi.fn(() => ({
    data: null,
  })),
}));

const renderNavigation = (initialEntries = ['/dashboard']) => {
  return renderWithProviders(<Navigation />, { initialEntries });
};

/**
 * Helper to find a nav link by its label text.
 * Uses the link role to avoid ambiguity with stat labels and wrapper elements.
 */
const getNavLink = (name: string): HTMLAnchorElement => {
  const links = screen.getAllByRole('link');
  const match = links.find((link) => {
    const span = link.querySelector(':scope > div > div > span');
    return span?.textContent === name;
  });
  if (!match) {
    throw new Error(`Could not find nav link with label "${name}"`);
  }
  return match as HTMLAnchorElement;
};

describe('Navigation', () => {
  // --- Branding ---

  it('renders ASR Records brand name', () => {
    renderNavigation();
    expect(
      screen.getByRole('heading', { name: /asr records/i })
    ).toBeInTheDocument();
  });

  it('renders Legacy Edition subtitle', () => {
    renderNavigation();
    expect(screen.getByText('Legacy Edition')).toBeInTheDocument();
  });

  // --- Quick stats (live data from mocked hooks) ---

  it('renders document count stat from API', () => {
    renderNavigation();
    expect(screen.getByText('1,234')).toBeInTheDocument();
  });

  it('renders accuracy stat from API', () => {
    renderNavigation();
    expect(screen.getByText('94%')).toBeInTheDocument();
  });

  // --- Primary nav links ---

  it('renders Dashboard nav link', () => {
    renderNavigation();
    const link = getNavLink('Dashboard');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/dashboard');
  });

  it('renders Upload nav link', () => {
    renderNavigation();
    const link = getNavLink('Upload');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/upload');
  });

  it('renders Documents nav link', () => {
    renderNavigation();
    const link = getNavLink('Documents');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/documents');
  });

  // --- Secondary nav links ---

  it('renders Reports nav link', () => {
    renderNavigation();
    const link = getNavLink('Reports');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/reports');
  });

  it('renders Settings nav link', () => {
    renderNavigation();
    const link = getNavLink('Settings');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/settings');
  });

  // --- Active state ---

  it('highlights active Dashboard link when on /dashboard', () => {
    renderNavigation(['/dashboard']);
    const dashboardLink = getNavLink('Dashboard');
    expect(dashboardLink).toBeInTheDocument();
    expect(dashboardLink.className).toContain('bg-primary-50');
  });

  it('highlights active Documents link when on /documents', () => {
    renderNavigation(['/documents']);
    const documentsLink = getNavLink('Documents');
    expect(documentsLink).toBeInTheDocument();
    expect(documentsLink.className).toContain('bg-primary-50');
  });

  // --- Footer ---

  it('renders System Online status when operational', () => {
    renderNavigation();
    expect(screen.getByText('System Online')).toBeInTheDocument();
  });

  it('renders last sync time', () => {
    renderNavigation();
    expect(
      screen.getByText(/Last sync:/)
    ).toBeInTheDocument();
  });

  // --- P41: Mobile responsive navigation ---

  it('desktop sidebar has hidden md:flex classes', () => {
    renderNavigation();
    const desktopNav = screen.getAllByRole('navigation', { name: /main navigation/i })[0];
    expect(desktopNav.className).toContain('hidden');
    expect(desktopNav.className).toContain('md:flex');
  });

  it('renders mobile overlay when sidebarCollapsed is false', () => {
    // sidebarCollapsed: false means mobile drawer is open
    useUIStore.setState({ sidebarCollapsed: false });
    renderNavigation();
    expect(screen.getByTestId('nav-backdrop')).toBeInTheDocument();
  });

  it('closes mobile overlay on backdrop click', () => {
    useUIStore.setState({ sidebarCollapsed: false });
    renderNavigation();
    fireEvent.click(screen.getByTestId('nav-backdrop'));
    // After clicking backdrop, sidebarCollapsed should toggle to true
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
  });

  it('closes mobile overlay on Escape key', () => {
    useUIStore.setState({ sidebarCollapsed: false });
    renderNavigation();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(useUIStore.getState().sidebarCollapsed).toBe(true);
  });
});
