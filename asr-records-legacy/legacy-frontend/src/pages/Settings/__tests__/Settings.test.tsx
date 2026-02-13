import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Settings } from '../Settings';
import { useSystemStatus, useSystemInfo } from '@/hooks/api/useSystemStatus';
import { useTenantId } from '@/stores/auth';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/hooks/api/useSystemStatus', () => ({
  useSystemStatus: vi.fn(),
  useSystemInfo: vi.fn(),
}));

vi.mock('@/stores/auth', () => ({
  useTenantId: vi.fn(),
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

const mockSetTheme = vi.fn();
const mockUpdatePreference = vi.fn();
vi.mock('@/stores/ui/uiStore', () => ({
  useTheme: () => ({ theme: 'light', setTheme: mockSetTheme, toggle: vi.fn() }),
  useViewPreferences: () => ({
    preferences: { documentsView: 'table', itemsPerPage: 50, sortBy: 'created_at', sortDirection: 'desc' },
    update: mockUpdatePreference,
  }),
}));

const mockStatus = {
  system_type: 'production_server',
  version: '2.0.0',
  status: 'operational',
  services: {
    gl_accounts: { status: 'active', count: 79 },
    payment_detection: { status: 'active', methods: 5 },
    billing_router: { status: 'active', destinations: 4 },
    storage: { status: 'active', backend: 'local' },
  },
  claude_ai: 'configured',
};

const mockInfo = {
  system_type: 'production_server',
  version: '2.0.0',
  capabilities: {
    gl_accounts: { total: 79, enabled: true },
    payment_detection: { methods: 5, consensus_enabled: true },
    billing_router: { destinations: 4, audit_trails: true },
    multi_tenant: false,
    scanner_api: true,
  },
  limits: {
    max_file_size_mb: 10,
    max_batch_size: 10,
    max_scanner_clients: 5,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderSettings = () =>
  render(
    <MemoryRouter>
      <Settings />
    </MemoryRouter>,
  );

const setupLoaded = () => {
  (useSystemStatus as ReturnType<typeof vi.fn>).mockReturnValue({
    data: mockStatus,
    isLoading: false,
  });
  (useSystemInfo as ReturnType<typeof vi.fn>).mockReturnValue({
    data: mockInfo,
    isLoading: false,
  });
  (useTenantId as ReturnType<typeof vi.fn>).mockReturnValue('test-tenant');
};

const setupLoading = () => {
  (useSystemStatus as ReturnType<typeof vi.fn>).mockReturnValue({
    data: undefined,
    isLoading: true,
  });
  (useSystemInfo as ReturnType<typeof vi.fn>).mockReturnValue({
    data: undefined,
    isLoading: true,
  });
  (useTenantId as ReturnType<typeof vi.fn>).mockReturnValue('default');
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Settings', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders Settings page title', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders System Information panel with version and GL accounts', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('System Information')).toBeInTheDocument();
    expect(screen.getByText('2.0.0')).toBeInTheDocument();
    expect(screen.getByText('79 accounts (enabled)')).toBeInTheDocument();
  });

  it('renders API Status panel with operational indicator', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('API Status')).toBeInTheDocument();
    expect(screen.getByText('All Systems Operational')).toBeInTheDocument();
  });

  it('renders Configuration panel with tenant ID', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('test-tenant')).toBeInTheDocument();
  });

  it('renders Security panel with auth and rate limiting info', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('Security')).toBeInTheDocument();
    expect(screen.getByText('Bearer Token / JWT')).toBeInTheDocument();
    expect(screen.getByText('100 req/min (sliding window)')).toBeInTheDocument();
  });

  it('shows loading state when statusLoading is true', () => {
    setupLoading();
    const { container } = renderSettings();
    expect(screen.getByText('Loading system information...')).toBeInTheDocument();
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });

  it('shows degraded indicator when status is not operational', () => {
    (useSystemStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { ...mockStatus, status: 'degraded' },
      isLoading: false,
    });
    (useSystemInfo as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockInfo,
      isLoading: false,
    });
    (useTenantId as ReturnType<typeof vi.fn>).mockReturnValue('default');

    renderSettings();
    expect(screen.getByText('Degraded Performance')).toBeInTheDocument();
  });

  it('renders InfoRow with label and value', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('Version')).toBeInTheDocument();
    expect(screen.getByText('2.0.0')).toBeInTheDocument();
    expect(screen.getByText('Tenant ID')).toBeInTheDocument();
  });

  it('renders User Preferences card with theme selector', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('User Preferences')).toBeInTheDocument();
    expect(screen.getByLabelText('Theme selector')).toBeInTheDocument();
  });

  it('renders Notification Preferences card with toggle switches', () => {
    setupLoaded();
    renderSettings();
    expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
    expect(screen.getByText('Document Processed')).toBeInTheDocument();
    expect(screen.getByText('Classification Failed')).toBeInTheDocument();
    expect(screen.getByText('Manual Review Required')).toBeInTheDocument();
  });

  // --- P57: Settings save toast feedback ---

  it('shows toast when theme is changed', async () => {
    setupLoaded();
    renderSettings();
    const themeSelect = screen.getByLabelText('Theme selector');
    await userEvent.selectOptions(themeSelect, 'dark');
    expect(toast.success).toHaveBeenCalledWith('Theme updated');
  });

  it('shows toast when items per page is changed', async () => {
    setupLoaded();
    renderSettings();
    const pageSelect = screen.getByLabelText('Items per page selector');
    await userEvent.selectOptions(pageSelect, '100');
    expect(toast.success).toHaveBeenCalledWith('Preferences updated');
  });
});
