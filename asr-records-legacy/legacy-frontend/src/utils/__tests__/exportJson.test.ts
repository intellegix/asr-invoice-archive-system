import { exportDocumentsJson } from '../exportJson';
import type { Document as ApiDocument } from '@/types/api';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockClick = vi.fn();
const mockCreateObjectURL = vi.fn().mockReturnValue('blob:test-url');
const mockRevokeObjectURL = vi.fn();

let linkElement: { href: string; download: string; click: () => void };

beforeEach(() => {
  vi.stubGlobal('URL', {
    createObjectURL: mockCreateObjectURL,
    revokeObjectURL: mockRevokeObjectURL,
  });

  linkElement = { href: '', download: '', click: mockClick };
  vi.spyOn(document, 'createElement').mockReturnValue(linkElement as any);
  vi.spyOn(document.body, 'appendChild').mockImplementation(() => null as any);
  vi.spyOn(document.body, 'removeChild').mockImplementation(() => null as any);
});

afterEach(() => {
  vi.restoreAllMocks();
});

const mockDocuments = [
  {
    id: 'doc-001',
    filename: 'invoice-001.pdf',
    status: 'classified',
    tenant_id: 'default',
    created_at: '2026-01-15T10:00:00Z',
    classification: {
      vendor_name: 'Staples',
      amount: 1250.5,
      payment_status: 'paid',
      gl_account_code: '6100',
      expense_category: 'Office Supplies',
      routing_destination: 'closed_payable',
      category_confidence: 96.5,
    },
  },
] as unknown as ApiDocument[];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('exportDocumentsJson', () => {
  it('generates valid JSON blob and triggers download with correct filename', () => {
    exportDocumentsJson(mockDocuments);

    expect(mockCreateObjectURL).toHaveBeenCalledTimes(1);
    expect(mockClick).toHaveBeenCalledTimes(1);
    expect(mockRevokeObjectURL).toHaveBeenCalledTimes(1);

    // Verify the Blob was created with JSON content type
    const blobArg = mockCreateObjectURL.mock.calls[0][0] as Blob;
    expect(blobArg).toBeInstanceOf(Blob);
    expect(blobArg.type).toBe('application/json;charset=utf-8;');

    // Verify the download filename pattern
    expect(linkElement.download).toMatch(/^asr-documents-export-\d{4}-\d{2}-\d{2}\.json$/);
  });
});
