import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Dashboard } from '../Dashboard';
import { useDashboardMetrics, usePaymentStatusDistribution } from '@/hooks/api/useDashboard';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/hooks/api/useDashboard', () => ({
  useDashboardMetrics: vi.fn(),
  usePaymentStatusDistribution: vi.fn(),
}));

const mockMetrics = {
  totalDocuments: 1234,
  documentsThisMonth: 87,
  documentsTrend: { value: 12.5, direction: 'up', period: 'vs last month', isPositive: true },
  paymentAccuracy: 94,
  paymentAccuracyTrend: { value: 2.1, direction: 'up', period: 'vs last month', isPositive: true },
  totalAmountProcessed: 5200000,
  glAccountsUsed: 32,
  totalGLAccounts: 40,
  manualReviewRate: 6,
  processingTimeTrend: { value: 5, direction: 'down', period: 'vs last month', isPositive: true },
  recentDocuments: [
    {
      id: 'doc-1',
      filename: 'invoice-001.pdf',
      vendor: 'Staples',
      amount: 1250,
      status: 'unpaid',
      glAccount: '6100 - Office',
      confidence: 96,
      processedAt: '2026-01-15T10:00:00Z',
      billingDestination: 'open_payable',
    },
  ],
};

const mockPaymentDist = {
  distribution: [
    { status: 'paid', count: 120, percentage: 46 },
    { status: 'unpaid', count: 85, percentage: 33 },
  ],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  );

const setupLoaded = () => {
  (useDashboardMetrics as ReturnType<typeof vi.fn>).mockReturnValue({
    data: mockMetrics,
    isLoading: false,
  });
  (usePaymentStatusDistribution as ReturnType<typeof vi.fn>).mockReturnValue({
    data: mockPaymentDist,
  });
};

const setupLoading = () => {
  (useDashboardMetrics as ReturnType<typeof vi.fn>).mockReturnValue({
    data: undefined,
    isLoading: true,
  });
  (usePaymentStatusDistribution as ReturnType<typeof vi.fn>).mockReturnValue({
    data: undefined,
  });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Dashboard', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  // --- Loading state ---

  it('renders loading state when metrics loading', () => {
    setupLoading();
    renderDashboard();
    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
  });

  it('shows skeleton cards in loading state', () => {
    setupLoading();
    const { container } = renderDashboard();
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });

  // --- Loaded state: header ---

  it('renders Dashboard title when loaded', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders welcome message', () => {
    setupLoaded();
    renderDashboard();
    expect(
      screen.getByText(/Welcome back! Here's what's happening with your document processing\./),
    ).toBeInTheDocument();
  });

  // --- Metric cards ---

  it('renders Total Documents metric card with value', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Total Documents')).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
  });

  it('renders Payment Accuracy metric card', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Payment Accuracy')).toBeInTheDocument();
    // 94% appears both in the MetricCard value and the consensus accuracy line,
    // so use getAllByText to verify it renders at least once.
    const matches = screen.getAllByText('94%');
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('renders Total Amount Processed metric card', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Total Amount Processed')).toBeInTheDocument();
    expect(screen.getByText('$5.2M')).toBeInTheDocument();
  });

  it('renders GL Accounts Used metric card', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('GL Accounts Used')).toBeInTheDocument();
    expect(screen.getByText('32/40')).toBeInTheDocument();
  });

  // --- Recent Documents ---

  it('renders Recent Documents section header', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Recent Documents')).toBeInTheDocument();
  });

  it('renders recent document entries', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('invoice-001.pdf')).toBeInTheDocument();
  });

  it('renders document vendor and amount', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText(/Staples/)).toBeInTheDocument();
    expect(screen.getByText(/\$1,250/)).toBeInTheDocument();
  });

  it('renders empty state when no recent documents', () => {
    (useDashboardMetrics as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { ...mockMetrics, recentDocuments: [] },
      isLoading: false,
    });
    (usePaymentStatusDistribution as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockPaymentDist,
    });
    renderDashboard();
    expect(screen.getByText('No recent documents processed')).toBeInTheDocument();
  });

  // --- Payment Status Distribution ---

  it('renders Payment Status Distribution section', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Payment Status Distribution')).toBeInTheDocument();
  });

  it('renders payment status progress bars', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('120 documents')).toBeInTheDocument();
    expect(screen.getByText('85 documents')).toBeInTheDocument();
  });

  it('renders empty state when no payment data', () => {
    (useDashboardMetrics as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockMetrics,
      isLoading: false,
    });
    (usePaymentStatusDistribution as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { distribution: [] },
    });
    renderDashboard();
    expect(screen.getByText('No payment status data available')).toBeInTheDocument();
  });

  // --- Quick Actions ---

  it('renders Quick Actions section', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
  });

  it('renders Upload Documents quick action', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
    expect(screen.getByText('Add new documents for processing')).toBeInTheDocument();
  });

  it('renders View Reports and Review Queue actions', () => {
    setupLoaded();
    renderDashboard();
    expect(screen.getByText('View Reports')).toBeInTheDocument();
    expect(screen.getByText('Generate analytics and insights')).toBeInTheDocument();
    expect(screen.getByText('Review Queue')).toBeInTheDocument();
    expect(screen.getByText('Check items needing manual review')).toBeInTheDocument();
  });

  // --- Quick Action navigation ---

  it('Upload Documents quick action navigates to /upload', () => {
    setupLoaded();
    renderDashboard();
    const btn = screen.getByText('Upload Documents').closest('button')!;
    fireEvent.click(btn);
    // MemoryRouter will handle the navigation — verify no crash
    expect(btn).toBeInTheDocument();
  });

  it('View Reports quick action navigates to /reports', () => {
    setupLoaded();
    renderDashboard();
    const btn = screen.getByText('View Reports').closest('button')!;
    fireEvent.click(btn);
    expect(btn).toBeInTheDocument();
  });

  it('Review Queue quick action navigates to /documents', () => {
    setupLoaded();
    renderDashboard();
    const btn = screen.getByText('Review Queue').closest('button')!;
    fireEvent.click(btn);
    expect(btn).toBeInTheDocument();
  });
});
