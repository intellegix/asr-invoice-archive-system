import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentDetailModal } from '../DocumentDetailModal';
import type { Document as ApiDocument } from '@/types/api';

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

const mockDoc = {
  id: 'doc-001',
  filename: 'invoice-001.pdf',
  original_filename: 'invoice-001.pdf',
  file_path: '/uploads/invoice-001.pdf',
  status: 'classified',
  file_size: 102400,
  mime_type: 'application/pdf',
  tenant_id: 'default',
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-15T10:01:00Z',
  metadata: { file_hash: 'abc123' },
  classification: {
    gl_account_code: '6100',
    expense_category: 'Office Supplies',
    suggested_category: 'Operating Expenses',
    category_confidence: 96.5,
    vendor_name: 'Staples',
    amount: 1250,
    invoice_number: 'INV-2026-001',
    invoice_date: '2026-01-10',
    due_date: '2026-02-10',
    payment_status: 'unpaid',
    payment_confidence: 92,
    consensus_methods: ['claude_ai', 'regex_patterns', 'keyword_analysis'],
    payment_details: {},
    routing_destination: 'open_payable',
    routing_confidence: 95,
    routing_reason: 'Unpaid invoice routed to open payable',
    validation_level: 'standard',
  },
  audit_trail: [
    { action: 'Document uploaded', timestamp: '2026-01-15T10:00:00Z', details: {} },
    { action: 'Classification completed', timestamp: '2026-01-15T10:01:00Z', details: {} },
  ],
} as unknown as ApiDocument;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const defaultProps = {
  document: mockDoc,
  onClose: vi.fn(),
};

const renderModal = (props = {}) =>
  render(<DocumentDetailModal {...defaultProps} {...props} />);

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DocumentDetailModal', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders document filename and status', () => {
    renderModal();
    expect(screen.getByText('invoice-001.pdf')).toBeInTheDocument();
    expect(screen.getByText('classified')).toBeInTheDocument();
  });

  it('renders classification details (GL account, vendor, amount)', () => {
    renderModal();
    expect(screen.getByText('6100 - Office Supplies')).toBeInTheDocument();
    expect(screen.getByText('Staples')).toBeInTheDocument();
    expect(screen.getByText('$1,250')).toBeInTheDocument();
  });

  it('renders confidence with correct color (green for >95%)', () => {
    renderModal();
    // category_confidence is 96.5% — should be green
    const confidenceEl = screen.getByText('96.5%');
    expect(confidenceEl).toHaveClass('text-green-600');
  });

  it('calls onClose when Close button clicked', () => {
    renderModal();
    fireEvent.click(screen.getByText('Close'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose on backdrop click', () => {
    const { container } = renderModal();
    // The backdrop is the div with bg-black bg-opacity-50
    const backdrop = container.querySelector('.bg-black.bg-opacity-50')!;
    fireEvent.click(backdrop);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });
});
