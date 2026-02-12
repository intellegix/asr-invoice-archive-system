import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Reports } from '../Reports';
import {
  useDashboardMetrics,
  usePaymentStatusDistribution,
  useGLAccountUsage,
  useTrendData,
} from '@/hooks/api/useDashboard';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/hooks/api/useDashboard', () => ({
  useDashboardMetrics: vi.fn(),
  usePaymentStatusDistribution: vi.fn(),
  useGLAccountUsage: vi.fn(),
  useTrendData: vi.fn(),
}));

vi.mock('react-chartjs-2', () => ({
  Bar: (props: any) => <div data-testid="bar-chart" {...props} />,
  Doughnut: (props: any) => <div data-testid="doughnut-chart" {...props} />,
  Line: (props: any) => <div data-testid="line-chart" {...props} />,
}));

vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  CategoryScale: vi.fn(),
  LinearScale: vi.fn(),
  BarElement: vi.fn(),
  ArcElement: vi.fn(),
  PointElement: vi.fn(),
  LineElement: vi.fn(),
  Title: vi.fn(),
  Tooltip: vi.fn(),
  Legend: vi.fn(),
  Filler: vi.fn(),
}));

const mockMetrics = {
  totalDocuments: 1234,
  documentsThisMonth: 87,
  classificationAccuracy: 96,
  paymentAccuracy: 94,
  totalAmountProcessed: 5200000,
  glAccountsUsed: 32,
  totalGLAccounts: 79,
  manualReviewRate: 6,
  openPayable: 45,
  closedPayable: 120,
  openReceivable: 18,
  closedReceivable: 72,
  recentDocuments: [],
};

const mockGlUsage = {
  accounts: [
    { code: '6100', name: 'Office Supplies', documentCount: 50, totalAmount: 25000, accuracy: 97, lastUsed: '2026-01-15', category: 'Operating' },
    { code: '6200', name: 'Utilities', documentCount: 30, totalAmount: 12000, accuracy: 95, lastUsed: '2026-01-14', category: 'Operating' },
  ],
};

const mockPaymentDist = {
  distribution: [
    { status: 'paid', count: 120, percentage: 46, totalAmount: 500000 },
    { status: 'unpaid', count: 85, percentage: 33, totalAmount: 200000 },
  ],
};

const mockTrends = {
  period: '30d' as const,
  documents: [
    { date: '2026-01-01', total: 10, classified: 8, manualReview: 2 },
    { date: '2026-01-02', total: 15, classified: 12, manualReview: 3 },
  ],
  amounts: [],
  accuracy: [],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderReports = () =>
  render(
    <MemoryRouter>
      <Reports />
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
  (useGLAccountUsage as ReturnType<typeof vi.fn>).mockReturnValue({
    data: mockGlUsage,
  });
  (useTrendData as ReturnType<typeof vi.fn>).mockReturnValue({
    data: mockTrends,
  });
};

const setupLoading = () => {
  (useDashboardMetrics as ReturnType<typeof vi.fn>).mockReturnValue({
    data: undefined,
    isLoading: true,
  });
  (usePaymentStatusDistribution as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined });
  (useGLAccountUsage as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined });
  (useTrendData as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Reports', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders Reports page title', () => {
    setupLoaded();
    renderReports();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('renders 4 MetricCards', () => {
    setupLoaded();
    renderReports();
    expect(screen.getByText('Total Documents')).toBeInTheDocument();
    expect(screen.getByText('Classification Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Total Amount')).toBeInTheDocument();
    expect(screen.getByText('GL Accounts Used')).toBeInTheDocument();
  });

  it('renders GL Account Distribution chart section', () => {
    setupLoaded();
    renderReports();
    expect(screen.getByText('Documents by GL Account')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('renders Payment Status Distribution chart section', () => {
    setupLoaded();
    renderReports();
    expect(screen.getByText('Payment Status Distribution')).toBeInTheDocument();
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
  });

  it('renders Processing Volume Trend chart section', () => {
    setupLoaded();
    renderReports();
    expect(screen.getByText(/Processing Volume/)).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('renders billing destinations summary with 4 boxes', () => {
    setupLoaded();
    renderReports();
    expect(screen.getByText('Open Payable')).toBeInTheDocument();
    expect(screen.getByText('Closed Payable')).toBeInTheDocument();
    expect(screen.getByText('Open Receivable')).toBeInTheDocument();
    expect(screen.getByText('Closed Receivable')).toBeInTheDocument();
  });

  it('shows loading state when metricsLoading is true', () => {
    setupLoading();
    const { container } = renderReports();
    expect(screen.getByText('Loading reports...')).toBeInTheDocument();
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });

  it('handles empty/null data gracefully', () => {
    (useDashboardMetrics as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {},
      isLoading: false,
    });
    (usePaymentStatusDistribution as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined });
    (useGLAccountUsage as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined });
    (useTrendData as ReturnType<typeof vi.fn>).mockReturnValue({ data: undefined });

    renderReports();
    expect(screen.getByText('No GL account data available')).toBeInTheDocument();
    expect(screen.getByText('No payment data available')).toBeInTheDocument();
    expect(screen.getByText('No trend data available')).toBeInTheDocument();
  });
});
