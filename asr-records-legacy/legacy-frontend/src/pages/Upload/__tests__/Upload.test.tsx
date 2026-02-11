import { screen } from '@testing-library/react';
import { Upload } from '../Upload';
import { useFileUpload } from '@/hooks/upload/useFileUpload';
import { renderWithProviders } from '@/tests/helpers/renderWithProviders';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockUploadFile = vi.fn();
const mockUploadMultipleFiles = vi.fn();
const mockClearCompleted = vi.fn();
const mockClearAll = vi.fn();
const mockRemoveUpload = vi.fn();

vi.mock('@/hooks/upload/useFileUpload', () => ({
  useFileUpload: vi.fn(() => ({
    uploads: [],
    uploadFile: mockUploadFile,
    uploadMultipleFiles: mockUploadMultipleFiles,
    clearCompleted: mockClearCompleted,
    clearAll: mockClearAll,
    removeUpload: mockRemoveUpload,
    isUploading: false,
    stats: { total: 0, completed: 0, processing: 0, errors: 0 },
  })),
}));

vi.mock('react-dropzone', () => ({
  useDropzone: vi.fn(({ onDrop }: { onDrop: (files: File[]) => void }) => ({
    getRootProps: () => ({ onClick: vi.fn(), onDrop }),
    getInputProps: () => ({ type: 'file' }),
    isDragActive: false,
  })),
}));

// Mock the new hooks used by Upload
vi.mock('@/hooks/api/useSystemStatus', () => ({
  useSystemStatus: vi.fn(() => ({
    data: { status: 'operational' },
  })),
  useSystemInfo: vi.fn(() => ({
    data: {
      capabilities: {
        gl_accounts: { total: 79, enabled: true },
        payment_detection: { methods: 5, consensus_enabled: true },
        billing_router: { destinations: 4, audit_trails: true },
      },
    },
  })),
}));

vi.mock('@/hooks/api/useDashboard', () => ({
  useDashboardMetrics: vi.fn(() => ({
    data: {
      classificationAccuracy: 94,
      paymentAccuracy: 94,
      manualReviewRate: 6,
      averageProcessingTime: 2.3,
    },
  })),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderUpload = () =>
  renderWithProviders(<Upload />, { initialEntries: ['/upload'] });

const setupWithUploads = (overrides: Partial<ReturnType<typeof useFileUpload>> = {}) => {
  (useFileUpload as ReturnType<typeof vi.fn>).mockReturnValue({
    uploads: [],
    uploadFile: mockUploadFile,
    uploadMultipleFiles: mockUploadMultipleFiles,
    clearCompleted: mockClearCompleted,
    clearAll: mockClearAll,
    removeUpload: mockRemoveUpload,
    isUploading: false,
    stats: { total: 0, completed: 0, processing: 0, errors: 0 },
    ...overrides,
  });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Upload', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  // --- Page header ---

  it('renders Upload Documents page title', () => {
    renderUpload();
    expect(screen.getByText('Upload Documents')).toBeInTheDocument();
  });

  it('renders page description', () => {
    renderUpload();
    expect(
      screen.getByText(
        /Upload documents for automated processing and classification using our AI-powered system\./,
      ),
    ).toBeInTheDocument();
  });

  // --- Dropzone ---

  it('renders dropzone area', () => {
    renderUpload();
    expect(screen.getByText('Drop files here to upload')).toBeInTheDocument();
  });

  it('renders "Drop files here to upload" text', () => {
    renderUpload();
    expect(screen.getByText('Drop files here to upload')).toBeInTheDocument();
  });

  it('renders file type info (PDF, PNG, JPG)', () => {
    renderUpload();
    expect(screen.getByText(/PDF, PNG, JPG supported/)).toBeInTheDocument();
  });

  it('renders size limit info (10MB)', () => {
    renderUpload();
    expect(screen.getByText(/Up to 10MB per file/)).toBeInTheDocument();
  });

  it('renders batch upload info', () => {
    renderUpload();
    expect(screen.getByText(/Batch upload available/)).toBeInTheDocument();
  });

  // --- Upload progress (no uploads) ---

  it('does not render upload progress when no uploads', () => {
    renderUpload();
    expect(screen.queryByText('Upload Progress')).not.toBeInTheDocument();
  });

  // --- Upload progress (with uploads) ---

  it('renders upload progress when uploads exist', () => {
    setupWithUploads({
      uploads: [
        {
          id: 'upload-1',
          file: new File(['content'], 'test.pdf', { type: 'application/pdf' }),
          progress: 75,
          status: 'uploading',
        },
      ],
      stats: { total: 1, completed: 0, processing: 0, errors: 0 },
    });
    renderUpload();
    expect(screen.getByText('Upload Progress')).toBeInTheDocument();
  });

  it('renders file name in upload progress', () => {
    setupWithUploads({
      uploads: [
        {
          id: 'upload-1',
          file: new File(['content'], 'test.pdf', { type: 'application/pdf' }),
          progress: 75,
          status: 'uploading',
        },
      ],
      stats: { total: 1, completed: 0, processing: 0, errors: 0 },
    });
    renderUpload();
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
  });

  it('renders progress bar', () => {
    setupWithUploads({
      uploads: [
        {
          id: 'upload-1',
          file: new File(['content'], 'test.pdf', { type: 'application/pdf' }),
          progress: 75,
          status: 'uploading',
        },
      ],
      stats: { total: 1, completed: 0, processing: 0, errors: 0 },
    });
    const { container } = renderUpload();
    const progressBar = container.querySelector('[style*="width: 75%"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('renders completed status', () => {
    setupWithUploads({
      uploads: [
        {
          id: 'upload-2',
          file: new File(['content'], 'done.pdf', { type: 'application/pdf' }),
          progress: 100,
          status: 'completed',
          result: { id: 'doc-1' },
        },
      ],
      stats: { total: 1, completed: 1, processing: 0, errors: 0 },
    });
    renderUpload();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders error status with message', () => {
    setupWithUploads({
      uploads: [
        {
          id: 'upload-3',
          file: new File(['content'], 'bad.pdf', { type: 'application/pdf' }),
          progress: 30,
          status: 'error',
          error: 'Network timeout',
        },
      ],
      stats: { total: 1, completed: 0, processing: 0, errors: 1 },
    });
    renderUpload();
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Network timeout')).toBeInTheDocument();
  });

  // --- Processing feature cards ---

  it('renders GL Account Classifications card with live count', () => {
    renderUpload();
    expect(screen.getByText('79 GL Account Classifications')).toBeInTheDocument();
  });

  it('renders 5-Method Payment Detection card', () => {
    renderUpload();
    expect(screen.getByText('5-Method Payment Detection')).toBeInTheDocument();
  });

  it('renders Smart Billing Routes card', () => {
    renderUpload();
    expect(screen.getByText('Smart Billing Routes')).toBeInTheDocument();
  });

  // --- System Status ---

  it('renders System Status panel with "Online"', () => {
    renderUpload();
    expect(screen.getByText('System Status')).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  it('renders system stats from API (2.3s, 94%, 6%)', () => {
    renderUpload();
    expect(screen.getByText('2.3s')).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
    expect(screen.getByText('6%')).toBeInTheDocument();
  });
});
