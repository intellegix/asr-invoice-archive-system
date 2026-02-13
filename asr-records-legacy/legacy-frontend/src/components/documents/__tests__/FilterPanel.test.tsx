import { render, screen, fireEvent } from '@testing-library/react';
import { FilterPanel } from '../FilterPanel';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

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

const defaultProps = {
  onApply: vi.fn(),
  onClose: vi.fn(),
  currentFilters: {},
};

const renderFilterPanel = (props = {}) =>
  render(<FilterPanel {...defaultProps} {...props} />);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('FilterPanel', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders date, vendor, amount, and payment status fields', () => {
    renderFilterPanel();
    expect(screen.getByText('Date From')).toBeInTheDocument();
    expect(screen.getByText('Date To')).toBeInTheDocument();
    expect(screen.getByText('Vendor')).toBeInTheDocument();
    expect(screen.getByText('Min Amount ($)')).toBeInTheDocument();
    expect(screen.getByText('Max Amount ($)')).toBeInTheDocument();
    expect(screen.getByText('Payment Status')).toBeInTheDocument();
  });

  it('calls onApply with filter object when Apply Filters clicked', () => {
    renderFilterPanel();
    const vendorInput = screen.getByPlaceholderText('Filter by vendor...');
    fireEvent.change(vendorInput, { target: { value: 'Staples' } });
    fireEvent.click(screen.getByText('Apply Filters'));
    expect(defaultProps.onApply).toHaveBeenCalledWith(
      expect.objectContaining({ vendor: 'Staples' }),
    );
  });

  it('clears all fields when Clear All clicked', () => {
    renderFilterPanel();
    const vendorInput = screen.getByPlaceholderText('Filter by vendor...');
    fireEvent.change(vendorInput, { target: { value: 'Staples' } });
    fireEvent.click(screen.getByText('Clear All'));
    expect(defaultProps.onApply).toHaveBeenCalledWith({});
  });

  it('calls onClose when close button clicked', () => {
    renderFilterPanel();
    // The close button contains the X icon — it's the first button in the header
    const closeButton = screen.getByText('Filters').parentElement!.querySelector('button')!;
    fireEvent.click(closeButton);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('renders payment status dropdown with 5 options', () => {
    renderFilterPanel();
    const select = screen.getByRole('combobox');
    const options = select.querySelectorAll('option');
    // 6 options: "All statuses" + paid, unpaid, partial, void, unknown
    expect(options).toHaveLength(6);
    expect(options[1].textContent).toBe('Paid');
    expect(options[2].textContent).toBe('Unpaid');
    expect(options[3].textContent).toBe('Partial');
    expect(options[4].textContent).toBe('Void');
    expect(options[5].textContent).toBe('Unknown');
  });

  // --- Dark mode variants ---

  it('includes dark variant on container', () => {
    const { container } = renderFilterPanel();
    const panel = container.querySelector('.bg-gray-50.dark\\:bg-gray-800');
    expect(panel).toBeInTheDocument();
  });

  it('includes dark variant on label text', () => {
    const { container } = renderFilterPanel();
    const labels = container.querySelectorAll('.dark\\:text-gray-400');
    expect(labels.length).toBeGreaterThanOrEqual(6);
  });

  // --- Accessibility: label associations ---

  it('associates Date From label with input via htmlFor', () => {
    renderFilterPanel();
    const label = screen.getByText('Date From');
    expect(label).toHaveAttribute('for', 'filter-date-from');
    expect(document.getElementById('filter-date-from')).toBeInTheDocument();
  });

  it('associates Date To label with input via htmlFor', () => {
    renderFilterPanel();
    const label = screen.getByText('Date To');
    expect(label).toHaveAttribute('for', 'filter-date-to');
    expect(document.getElementById('filter-date-to')).toBeInTheDocument();
  });

  it('associates Vendor label with input via htmlFor', () => {
    renderFilterPanel();
    const label = screen.getByText('Vendor');
    expect(label).toHaveAttribute('for', 'filter-vendor');
    expect(document.getElementById('filter-vendor')).toBeInTheDocument();
  });

  it('associates Min Amount label with input via htmlFor', () => {
    renderFilterPanel();
    const label = screen.getByText('Min Amount ($)');
    expect(label).toHaveAttribute('for', 'filter-min-amount');
    expect(document.getElementById('filter-min-amount')).toBeInTheDocument();
  });

  it('associates Max Amount label with input via htmlFor', () => {
    renderFilterPanel();
    const label = screen.getByText('Max Amount ($)');
    expect(label).toHaveAttribute('for', 'filter-max-amount');
    expect(document.getElementById('filter-max-amount')).toBeInTheDocument();
  });

  it('associates Payment Status label with select via htmlFor', () => {
    renderFilterPanel();
    const label = screen.getByText('Payment Status');
    expect(label).toHaveAttribute('for', 'filter-payment-status');
    expect(document.getElementById('filter-payment-status')).toBeInTheDocument();
  });
});
