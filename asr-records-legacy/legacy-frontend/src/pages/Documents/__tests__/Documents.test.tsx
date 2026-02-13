import { screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import toast from 'react-hot-toast';
import { Documents } from '../Documents';
import { useDocuments } from '@/hooks/api/useDocuments';
import { useDocumentStore } from '@/stores/documents';
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

// Capture the real mock references for assertions
const mockToastSuccess = vi.mocked(toast.success);
const mockToastError = vi.mocked(toast.error);

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

  it('disables Previous button on first page', () => {
    renderDocuments();
    const prevButton = screen.getByText('Previous').closest('button');
    expect(prevButton).toBeDisabled();
  });

  it('renders page size selector with options', () => {
    renderDocuments();
    const select = screen.getByDisplayValue('50/page');
    expect(select).toBeInTheDocument();
    expect(screen.getByText('25/page')).toBeInTheDocument();
    expect(screen.getByText('100/page')).toBeInTheDocument();
  });

  it('shows "Showing X-Y documents" text', () => {
    renderDocuments();
    expect(screen.getByText(/Showing 1-2 documents/)).toBeInTheDocument();
  });

  it('does not render pagination when documents list is empty', () => {
    (useDocuments as ReturnType<typeof vi.fn>).mockReturnValue({
      data: [],
      isLoading: false,
    });
    renderDocuments();
    expect(screen.queryByText('Previous')).not.toBeInTheDocument();
    expect(screen.queryByText('Next')).not.toBeInTheDocument();
  });

  it('advances to next page when Next is clicked', async () => {
    (useDocuments as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockDocuments,
      isLoading: false,
    });
    // Set pageSize to match document count so Next button is enabled
    useDocumentStore.setState({ currentPage: 1, pageSize: 2 });
    renderDocuments();
    const nextButton = screen.getByText('Next').closest('button')!;
    expect(nextButton).not.toBeDisabled();
    await userEvent.click(nextButton);
    expect(useDocumentStore.getState().currentPage).toBe(2);
  });

  // --- P39: Search debounce ---

  it('does not call search mutation immediately on typing', async () => {
    renderDocuments();
    const input = screen.getByPlaceholderText(/Search documents/);
    await userEvent.type(input, 'inv');
    // mutation should not be called yet (debounce pending)
    expect(mockSearchMutate).not.toHaveBeenCalled();
  });

  it('calls search mutation after debounce delay', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderDocuments();
    const input = screen.getByPlaceholderText(/Search documents/);
    await userEvent.type(input, 'invoice');
    // Advance past debounce delay
    await vi.advanceTimersByTimeAsync(350);
    expect(mockSearchMutate).toHaveBeenCalledTimes(1);
    expect(mockSearchMutate).toHaveBeenCalledWith(
      expect.objectContaining({ query: 'invoice' }),
    );
    vi.useRealTimers();
  });

  // --- P38: Delete feedback toasts (with P51 confirmation) ---

  it('shows confirmation before deleting', async () => {
    renderDocuments();
    const deleteButtons = screen.getAllByText('Delete');
    await userEvent.click(deleteButtons[0]);
    // After first click, confirmation prompt appears
    expect(screen.getByText('Delete?')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('shows success toast when delete confirmed', async () => {
    mockDeleteMutate.mockImplementation((_id: string, opts: any) => {
      opts?.onSuccess?.();
    });
    renderDocuments();
    const deleteButtons = screen.getAllByText('Delete');
    await userEvent.click(deleteButtons[0]);
    // Confirm deletion
    await userEvent.click(screen.getByText('Yes'));
    expect(mockToastSuccess).toHaveBeenCalledWith('Document deleted');
  });

  it('cancels delete when Cancel is clicked', async () => {
    renderDocuments();
    const deleteButtons = screen.getAllByText('Delete');
    await userEvent.click(deleteButtons[0]);
    await userEvent.click(screen.getByText('Cancel'));
    // Confirmation should be dismissed, Delete button visible again
    expect(screen.queryByText('Delete?')).not.toBeInTheDocument();
  });

  it('shows error toast when delete fails', async () => {
    mockDeleteMutate.mockImplementation((_id: string, opts: any) => {
      opts?.onError?.();
    });
    renderDocuments();
    const deleteButtons = screen.getAllByText('Delete');
    await userEvent.click(deleteButtons[0]);
    await userEvent.click(screen.getByText('Yes'));
    expect(mockToastError).toHaveBeenCalledWith('Failed to delete document');
  });

  // --- P51: Accessibility ---

  it('search input has aria-label', () => {
    renderDocuments();
    const input = screen.getByPlaceholderText(/Search documents/);
    expect(input).toHaveAttribute('aria-label', 'Search documents, vendors, or GL accounts');
  });

  it('pagination has nav with aria-label', () => {
    renderDocuments();
    const nav = screen.getByRole('navigation', { name: 'Pagination' });
    expect(nav).toBeInTheDocument();
  });

  it('current page button has aria-current="page"', () => {
    renderDocuments();
    const nav = screen.getByRole('navigation', { name: 'Pagination' });
    const buttons = nav.querySelectorAll('button');
    const currentBtn = Array.from(buttons).find(btn => btn.getAttribute('aria-current') === 'page');
    expect(currentBtn).toBeTruthy();
  });

  // --- P56: Export menu accessibility ---

  it('export button has aria-haspopup and aria-expanded attributes', () => {
    renderDocuments();
    const exportBtn = screen.getByText('Export').closest('button')!;
    expect(exportBtn).toHaveAttribute('aria-haspopup', 'true');
    expect(exportBtn).toHaveAttribute('aria-expanded', 'false');
  });

  it('closes export menu on Escape key', async () => {
    renderDocuments();
    const exportBtn = screen.getByText('Export').closest('button')!;
    await userEvent.click(exportBtn);
    expect(screen.getByRole('menu')).toBeInTheDocument();
    // Fire Escape on the menu container
    fireEvent.keyDown(exportBtn.parentElement!, { key: 'Escape' });
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});
