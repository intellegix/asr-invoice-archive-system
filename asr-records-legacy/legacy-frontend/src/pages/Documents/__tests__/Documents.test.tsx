import { screen } from '@testing-library/react';
import { Documents } from '../Documents';
import { useDocuments } from '@/hooks/api/useDocuments';
import { renderWithProviders } from '@/tests/helpers/renderWithProviders';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockDocuments = [
  {
    id: 'doc-1',
    filename: 'invoice-001.pdf',
    original_filename: 'Invoice.pdf',
    status: 'classified',
    created_at: '2026-01-15T10:00:00Z',
    classification: {
      vendor_name: 'Staples',
      amount: 1250,
      payment_status: 'unpaid',
      gl_account_code: '6100',
      expense_category: 'Office Supplies',
      routing_destination: 'open_payable',
      category_confidence: 96,
    },
  },
  {
    id: 'doc-2',
    filename: 'invoice-002.pdf',
    original_filename: 'Receipt.pdf',
    status: 'manual_review',
    created_at: '2026-01-14T10:00:00Z',
    classification: {
      vendor_name: 'Home Depot',
      amount: 15000,
      payment_status: 'paid',
      gl_account_code: '5200',
      expense_category: 'Materials',
      routing_destination: 'closed_payable',
      category_confidence: 72,
    },
  },
];

const mockDeleteMutate = vi.fn();
const mockSearchMutate = vi.fn();

vi.mock('@/hooks/api/useDocuments', () => ({
  useDocuments: vi.fn(() => ({ data: mockDocuments, isLoading: false })),
  useDocumentSearch: vi.fn(() => ({ mutate: mockSearchMutate, data: null })),
  useDocumentDelete: vi.fn(() => ({ mutate: mockDeleteMutate, isPending: false })),
  useDocument: vi.fn(() => ({ data: null })),
}));

// react-hot-toast is imported transitively — stub it to prevent side-effects
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderDocuments = () =>
  renderWithProviders(<Documents />, { initialEntries: ['/documents'] });

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Documents', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  // --- Page header ---

  it('renders Documents page title', () => {
    renderDocuments();
    expect(screen.getByText('Documents')).toBeInTheDocument();
  });

  it('renders page description', () => {
    renderDocuments();
    expect(
      screen.getByText(
        /Browse and manage all processed documents with their classifications and routing information\./,
      ),
    ).toBeInTheDocument();
  });

  // --- Search & filters ---

  it('renders search input', () => {
    renderDocuments();
    expect(
      screen.getByPlaceholderText(/Search documents, vendors, or GL accounts/),
    ).toBeInTheDocument();
  });

  it('renders Filter button', () => {
    renderDocuments();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('renders Export button', () => {
    renderDocuments();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  // --- Quick filters ---

  it('renders All Documents quick filter with count', () => {
    renderDocuments();
    expect(screen.getByText(/All Documents \(2\)/)).toBeInTheDocument();
  });

  it('renders Manual Review quick filter', () => {
    renderDocuments();
    expect(screen.getByText(/Manual Review/)).toBeInTheDocument();
  });

  it('renders Unpaid quick filter', () => {
    renderDocuments();
    expect(screen.getByText(/Unpaid/)).toBeInTheDocument();
  });

  it('renders High Value quick filter', () => {
    renderDocuments();
    expect(screen.getByText(/High Value \(\$10K\+\)/)).toBeInTheDocument();
  });

  // --- Table ---

  it('renders table headers (Document, Vendor, Amount, etc.)', () => {
    renderDocuments();
    expect(screen.getByText('Document')).toBeInTheDocument();
    expect(screen.getByText('Vendor')).toBeInTheDocument();
    expect(screen.getByText('Amount')).toBeInTheDocument();
    expect(screen.getByText('Payment Status')).toBeInTheDocument();
    expect(screen.getByText('GL Account')).toBeInTheDocument();
    expect(screen.getByText('Destination')).toBeInTheDocument();
    expect(screen.getByText('Confidence')).toBeInTheDocument();
    expect(screen.getByText('Processed')).toBeInTheDocument();
  });

  it('renders document rows', () => {
    renderDocuments();
    expect(screen.getByText('invoice-001.pdf')).toBeInTheDocument();
    expect(screen.getByText('invoice-002.pdf')).toBeInTheDocument();
  });

  it('renders vendor name in row', () => {
    renderDocuments();
    expect(screen.getByText('Staples')).toBeInTheDocument();
    expect(screen.getByText('Home Depot')).toBeInTheDocument();
  });

  it('renders amount in row', () => {
    renderDocuments();
    expect(screen.getByText('$1,250')).toBeInTheDocument();
    expect(screen.getByText('$15,000')).toBeInTheDocument();
  });

  it('renders payment status badge', () => {
    renderDocuments();
    expect(screen.getByText('unpaid')).toBeInTheDocument();
    expect(screen.getByText('paid')).toBeInTheDocument();
  });

  it('renders GL account code', () => {
    renderDocuments();
    expect(screen.getByText(/6100 - Office Supplies/)).toBeInTheDocument();
    expect(screen.getByText(/5200 - Materials/)).toBeInTheDocument();
  });

  it('renders billing destination', () => {
    renderDocuments();
    expect(screen.getByText('Open Payable')).toBeInTheDocument();
    expect(screen.getByText('Closed Payable')).toBeInTheDocument();
  });

  it('renders confidence percentage', () => {
    renderDocuments();
    expect(screen.getByText('96%')).toBeInTheDocument();
    expect(screen.getByText('72%')).toBeInTheDocument();
  });

  // --- Loading state ---

  it('renders loading skeleton when loading', () => {
    (useDocuments as ReturnType<typeof vi.fn>).mockReturnValue({
      data: [],
      isLoading: true,
    });
    const { container } = renderDocuments();
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  // --- Empty state ---

  it('renders empty state when no documents', () => {
    (useDocuments as ReturnType<typeof vi.fn>).mockReturnValue({
      data: [],
      isLoading: false,
    });
    renderDocuments();
    expect(screen.getByText('No documents found')).toBeInTheDocument();
  });

  // --- Pagination ---

  it('renders pagination controls', () => {
    (useDocuments as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
    });
    renderDocuments();
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
    // Current page number shown in pagination
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1);
  });
});
