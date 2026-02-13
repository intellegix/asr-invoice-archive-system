import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Vendors } from '../Vendors';
import { renderWithProviders } from '@/tests/helpers/renderWithProviders';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockVendors = [
  {
    id: 'v-1',
    name: 'Acme Corp',
    display_name: 'Acme',
    contact_info: { email: 'info@acme.com', phone: '555-1111' },
    document_count: 12,
    total_amount_processed: 54000,
    average_amount: 4500,
    last_document_date: '2026-02-10T00:00:00Z',
    common_gl_accounts: [],
    payment_accuracy: 0.95,
    payment_patterns: { paid: 10, unpaid: 2, partial: 0, void: 0 },
    tenant_id: 'default',
    notes: 'Primary supplier',
    tags: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-02-01T00:00:00Z',
  },
  {
    id: 'v-2',
    name: 'BuildRight Inc',
    display_name: 'BuildRight',
    contact_info: {},
    document_count: 5,
    total_amount_processed: 12000,
    average_amount: 2400,
    last_document_date: null,
    common_gl_accounts: [],
    payment_accuracy: 0.8,
    payment_patterns: { paid: 3, unpaid: 1, partial: 1, void: 0 },
    tenant_id: 'default',
    notes: '',
    tags: ['lumber'],
    created_at: '2026-01-10T00:00:00Z',
    updated_at: '2026-01-15T00:00:00Z',
  },
];

const mockCreateMutate = vi.fn();
const mockUpdateMutate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('@/hooks/api/useVendors', () => ({
  useVendors: vi.fn(() => ({ data: mockVendors, isLoading: false })),
  useVendor: vi.fn(() => ({ data: null })),
  useVendorStats: vi.fn(() => ({ data: null })),
  useCreateVendor: vi.fn(() => ({ mutate: mockCreateMutate, isPending: false })),
  useUpdateVendor: vi.fn(() => ({ mutate: mockUpdateMutate, isPending: false })),
  useDeleteVendor: vi.fn(() => ({ mutate: mockDeleteMutate, isPending: false })),
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderVendors = () =>
  renderWithProviders(<Vendors />, { initialEntries: ['/vendors'] });

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Vendors', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  // --- Page header ---

  it('renders Vendors page title', () => {
    renderVendors();
    expect(screen.getByRole('heading', { name: 'Vendors' })).toBeInTheDocument();
  });

  it('renders page description', () => {
    renderVendors();
    expect(screen.getByText(/Manage vendors and view their document processing statistics/)).toBeInTheDocument();
  });

  // --- Vendor list ---

  it('renders vendor names in the table', () => {
    renderVendors();
    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('BuildRight Inc')).toBeInTheDocument();
  });

  it('displays document count for vendors', () => {
    renderVendors();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays summary stats', () => {
    renderVendors();
    // Total Vendors = 2
    expect(screen.getByText('2')).toBeInTheDocument();
    // Total Documents = 17
    expect(screen.getByText('17')).toBeInTheDocument();
  });

  // --- Search ---

  it('filters vendors by search query', async () => {
    renderVendors();
    const searchInput = screen.getByPlaceholderText('Search vendors...');
    await userEvent.type(searchInput, 'Acme');
    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.queryByText('BuildRight Inc')).not.toBeInTheDocument();
  });

  // --- Empty state ---

  it('shows empty state when search has no results', async () => {
    renderVendors();
    const searchInput = screen.getByPlaceholderText('Search vendors...');
    await userEvent.type(searchInput, 'NonExistentVendor');
    expect(screen.getByText('No vendors found')).toBeInTheDocument();
  });

  // --- Add vendor ---

  it('opens add vendor modal when clicking Add Vendor', async () => {
    renderVendors();
    await userEvent.click(screen.getByRole('button', { name: /add vendor/i }));
    expect(screen.getByRole('dialog', { name: /add vendor/i })).toBeInTheDocument();
    expect(screen.getByLabelText('Name *')).toBeInTheDocument();
  });

  // --- Edit vendor ---

  it('opens edit vendor modal when clicking edit button', async () => {
    renderVendors();
    const editButtons = screen.getAllByLabelText(/^Edit /);
    await userEvent.click(editButtons[0]);
    expect(screen.getByText('Edit Vendor')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Acme Corp')).toBeInTheDocument();
  });

  // --- Delete vendor ---

  it('shows delete confirmation when clicking delete button', async () => {
    renderVendors();
    const deleteButtons = screen.getAllByLabelText(/^Delete /);
    await userEvent.click(deleteButtons[0]);
    expect(screen.getByText('Delete?')).toBeInTheDocument();
  });

  // --- Dark mode classes ---

  it('has dark mode background classes on the page wrapper', () => {
    const { container } = renderVendors();
    const heading = container.querySelector('h1');
    expect(heading?.className).toContain('dark:text-gray-100');
  });
});
