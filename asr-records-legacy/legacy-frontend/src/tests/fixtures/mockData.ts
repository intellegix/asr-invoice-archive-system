import type {
  Document,
  DashboardMetrics,
  Vendor,
  DocumentUploadResponse,
  PaymentStatusDistribution,
  SearchResult,
} from '@/types/api';

export const mockDocument: Document = {
  id: 'doc-001',
  created_at: '2026-01-15T10:30:00Z',
  updated_at: '2026-01-15T10:35:00Z',
  filename: 'invoice-001.pdf',
  original_filename: 'Invoice January 2026.pdf',
  file_path: '/uploads/default/doc-001/invoice-001.pdf',
  file_size: 524288,
  mime_type: 'application/pdf',
  tenant_id: 'default',
  classification: {
    expense_category: 'Office Supplies',
    gl_account_code: '6100',
    suggested_category: 'Office Supplies',
    category_confidence: 96.5,
    payment_status: 'unpaid',
    payment_confidence: 92.3,
    consensus_methods: ['claude_ai', 'regex_patterns', 'keyword_analysis'],
    payment_details: {
      amount_paid: 0,
    },
    routing_destination: 'open_payable',
    routing_confidence: 94.1,
    routing_reason: 'Unpaid invoice for office supplies, routed to open payable',
    vendor_name: 'Staples Inc.',
    vendor_confidence: 97.2,
    company_name: 'ASR Construction',
    amount: 1250.0,
    currency: 'USD',
    invoice_number: 'INV-2026-001',
    invoice_date: '2026-01-10',
    due_date: '2026-02-10',
    validation_level: 'standard',
  },
  status: 'classified',
  processing_start_time: '2026-01-15T10:30:00Z',
  processing_end_time: '2026-01-15T10:32:15Z',
  metadata: {
    page_count: 2,
    word_count: 450,
    language: 'en',
    ocr_confidence: 98.5,
    file_hash: 'sha256:abc123def456',
    scan_quality: 'high',
    document_type: 'invoice',
  },
  audit_trail: [
    {
      timestamp: '2026-01-15T10:30:00Z',
      action: 'upload',
      user_id: 'system',
      details: { source: 'web_upload' },
    },
    {
      timestamp: '2026-01-15T10:32:15Z',
      action: 'classification_complete',
      user_id: 'system',
      details: {
        gl_account: '6100',
        payment_status: 'unpaid',
        confidence: 96.5,
      },
    },
  ],
};

export const mockDocumentList: Document[] = [
  mockDocument,
  {
    ...mockDocument,
    id: 'doc-002',
    filename: 'invoice-002.pdf',
    original_filename: 'Invoice February 2026.pdf',
    classification: {
      ...mockDocument.classification,
      expense_category: 'Materials',
      gl_account_code: '5200',
      category_confidence: 88.0,
      payment_status: 'paid',
      routing_destination: 'closed_payable',
      vendor_name: 'Home Depot',
      amount: 5430.75,
      invoice_number: 'INV-2026-002',
    },
    status: 'completed',
  },
  {
    ...mockDocument,
    id: 'doc-003',
    filename: 'receipt-001.png',
    original_filename: 'Scan Receipt.png',
    mime_type: 'image/png',
    classification: {
      ...mockDocument.classification,
      expense_category: 'Equipment Rental',
      gl_account_code: '6500',
      category_confidence: 72.0,
      payment_status: 'partial',
      routing_destination: 'open_payable',
      vendor_name: 'United Rentals',
      amount: 15000.0,
      invoice_number: 'INV-2026-003',
    },
    status: 'manual_review',
  },
];

export const mockDashboardMetrics: DashboardMetrics = {
  totalDocuments: 1234,
  documentsThisMonth: 87,
  documentsTrend: {
    value: 12.5,
    direction: 'up',
    period: 'vs last month',
    isPositive: true,
  },
  paymentAccuracy: 94,
  paymentAccuracyTrend: {
    value: 2.1,
    direction: 'up',
    period: 'vs last month',
    isPositive: true,
  },
  glAccountsUsed: 32,
  totalGLAccounts: 40,
  classificationAccuracy: 96.5,
  totalAmountProcessed: 5200000,
  averageProcessingTime: 2.3,
  manualReviewRate: 6,
  processingTimeTrend: {
    value: 5,
    direction: 'down',
    period: 'vs last month',
    isPositive: true,
  },
  openPayable: 45,
  closedPayable: 120,
  openReceivable: 15,
  closedReceivable: 80,
  recentDocuments: [
    {
      id: 'doc-001',
      filename: 'invoice-001.pdf',
      vendor: 'Staples Inc.',
      amount: 1250.0,
      status: 'unpaid',
      glAccount: '6100 - Office Supplies',
      confidence: 96,
      processedAt: '2026-01-15T10:32:15Z',
      billingDestination: 'open_payable',
    },
    {
      id: 'doc-002',
      filename: 'invoice-002.pdf',
      vendor: 'Home Depot',
      amount: 5430.75,
      status: 'paid',
      glAccount: '5200 - Materials',
      confidence: 88,
      processedAt: '2026-01-14T15:20:00Z',
      billingDestination: 'closed_payable',
    },
  ],
};

export const mockPaymentDistribution: PaymentStatusDistribution = {
  distribution: [
    { status: 'paid', count: 120, percentage: 46, totalAmount: 1560000 },
    { status: 'unpaid', count: 85, percentage: 33, totalAmount: 890000 },
    { status: 'partial', count: 30, percentage: 12, totalAmount: 420000 },
    { status: 'void', count: 10, percentage: 4, totalAmount: 52000 },
    { status: 'unknown', count: 15, percentage: 5, totalAmount: 78000 },
  ],
  trends: [
    { date: '2026-01-08', paid: 28, unpaid: 20, partial: 7, void: 2 },
    { date: '2026-01-09', paid: 30, unpaid: 18, partial: 8, void: 1 },
    { date: '2026-01-10', paid: 25, unpaid: 22, partial: 6, void: 3 },
    { date: '2026-01-11', paid: 32, unpaid: 15, partial: 5, void: 2 },
    { date: '2026-01-12', paid: 5, unpaid: 10, partial: 4, void: 2 },
  ],
};

export const mockVendor: Vendor = {
  id: 'vendor-001',
  created_at: '2025-06-01T00:00:00Z',
  updated_at: '2026-01-15T00:00:00Z',
  name: 'Staples Inc.',
  display_name: 'Staples',
  contact_info: {
    email: 'orders@staples.com',
    phone: '800-333-3330',
    address: '500 Staples Drive, Framingham, MA',
    website: 'https://www.staples.com',
  },
  document_count: 45,
  total_amount_processed: 56780.5,
  average_amount: 1261.79,
  last_document_date: '2026-01-15T10:30:00Z',
  common_gl_accounts: [
    { code: '6100', name: 'Office Supplies', frequency: 35, percentage: 78 },
    {
      code: '6200',
      name: 'Computer Equipment',
      frequency: 10,
      percentage: 22,
    },
  ],
  payment_accuracy: 95.6,
  payment_patterns: { paid: 30, unpaid: 10, partial: 3, void: 2 },
  tenant_id: 'default',
  notes: 'Primary office supply vendor',
  tags: ['office', 'supplies', 'preferred'],
};

export const mockUploadResponse: DocumentUploadResponse = {
  document_id: 'doc-new-001',
  processing_status: 'processing',
  estimated_processing_time: 5,
};

export const mockSearchResult: SearchResult = {
  documents: mockDocumentList,
  total: 3,
  filters: {},
  facets: [
    {
      field: 'payment_status',
      values: [
        { value: 'unpaid', count: 1 },
        { value: 'paid', count: 1 },
        { value: 'partial', count: 1 },
      ],
    },
    {
      field: 'gl_account_code',
      values: [
        { value: '6100', count: 1 },
        { value: '5200', count: 1 },
        { value: '6500', count: 1 },
      ],
    },
  ],
};

export const createMockFile = (
  name: string = 'test-invoice.pdf',
  type: string = 'application/pdf',
  size: number = 1024 * 1024
): File => {
  const file = new File(['mock-content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};
