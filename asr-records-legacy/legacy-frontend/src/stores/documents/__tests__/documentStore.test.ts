import { renderHook } from '@testing-library/react';
import {
  useDocumentStore,
  useDocumentSelection,
  useDocumentFilters,
  useDocumentView,
  useUploadQueue,
} from '../documentStore';

describe('documentStore', () => {
  beforeEach(() => {
    useDocumentStore.setState({
      selectedDocuments: [],
      activeDocument: undefined,
      filters: {},
      searchQuery: '',
      quickFilters: { needsReview: false, highValue: false },
      viewMode: 'table',
      sortBy: 'created_at',
      sortDirection: 'desc',
      pageSize: 50,
      currentPage: 1,
      uploadQueue: [],
      classificationHistory: [],
    });
  });

  // ---------------------------------------------------------------------------
  // Selection
  // ---------------------------------------------------------------------------
  describe('selection', () => {
    it('selectDocument adds a document id to selection', () => {
      useDocumentStore.getState().selectDocument('doc-1');
      expect(useDocumentStore.getState().selectedDocuments).toEqual(['doc-1']);
    });

    it('selectMultipleDocuments merges ids without duplicates', () => {
      useDocumentStore.getState().selectDocument('doc-1');
      useDocumentStore.getState().selectMultipleDocuments(['doc-1', 'doc-2', 'doc-3']);
      expect(useDocumentStore.getState().selectedDocuments).toEqual(['doc-1', 'doc-2', 'doc-3']);
    });

    it('deselectDocument removes a document id from selection', () => {
      useDocumentStore.setState({ selectedDocuments: ['doc-1', 'doc-2'] });
      useDocumentStore.getState().deselectDocument('doc-1');
      expect(useDocumentStore.getState().selectedDocuments).toEqual(['doc-2']);
    });

    it('clearSelection empties the selected documents array', () => {
      useDocumentStore.setState({ selectedDocuments: ['doc-1', 'doc-2'] });
      useDocumentStore.getState().clearSelection();
      expect(useDocumentStore.getState().selectedDocuments).toEqual([]);
    });

    it('toggleDocumentSelection adds an unselected document', () => {
      useDocumentStore.getState().toggleDocumentSelection('doc-1');
      expect(useDocumentStore.getState().selectedDocuments).toContain('doc-1');
    });

    it('toggleDocumentSelection removes an already selected document', () => {
      useDocumentStore.setState({ selectedDocuments: ['doc-1'] });
      useDocumentStore.getState().toggleDocumentSelection('doc-1');
      expect(useDocumentStore.getState().selectedDocuments).not.toContain('doc-1');
    });

    it('selectAll replaces entire selection with provided ids', () => {
      useDocumentStore.setState({ selectedDocuments: ['doc-old'] });
      useDocumentStore.getState().selectAll(['doc-a', 'doc-b', 'doc-c']);
      expect(useDocumentStore.getState().selectedDocuments).toEqual(['doc-a', 'doc-b', 'doc-c']);
    });

    it('selectDocument is idempotent — no duplicates on repeated calls', () => {
      useDocumentStore.getState().selectDocument('doc-1');
      useDocumentStore.getState().selectDocument('doc-1');
      expect(useDocumentStore.getState().selectedDocuments).toEqual(['doc-1']);
    });

    it('setActiveDocument sets the active document', () => {
      const mockDoc = { id: 'doc-1', filename: 'invoice.pdf' } as any;
      useDocumentStore.getState().setActiveDocument(mockDoc);
      expect(useDocumentStore.getState().activeDocument).toEqual(mockDoc);
    });
  });

  // ---------------------------------------------------------------------------
  // Filters
  // ---------------------------------------------------------------------------
  describe('filters', () => {
    it('setFilters merges partial filters into existing filters', () => {
      useDocumentStore.getState().setFilters({ vendor: 'ACME' });
      useDocumentStore.getState().setFilters({ project: 'Bridge' });

      const { filters } = useDocumentStore.getState();
      expect(filters).toEqual({ vendor: 'ACME', project: 'Bridge' });
    });

    it('updateFilter updates a single filter key', () => {
      useDocumentStore.getState().updateFilter('vendor', 'ACME');
      expect(useDocumentStore.getState().filters.vendor).toBe('ACME');
    });

    it('clearFilters resets filters, searchQuery, and quickFilters', () => {
      useDocumentStore.setState({
        filters: { vendor: 'ACME' },
        searchQuery: 'test query',
        quickFilters: { needsReview: true, highValue: true },
      });

      useDocumentStore.getState().clearFilters();

      const state = useDocumentStore.getState();
      expect(state.filters).toEqual({});
      expect(state.searchQuery).toBe('');
      expect(state.quickFilters).toEqual({ needsReview: false, highValue: false });
    });

    it('setSearchQuery sets the search query string', () => {
      useDocumentStore.getState().setSearchQuery('invoice #1234');
      expect(useDocumentStore.getState().searchQuery).toBe('invoice #1234');
    });

    it('setQuickFilter updates an individual quick filter', () => {
      useDocumentStore.getState().setQuickFilter('needsReview', true);
      expect(useDocumentStore.getState().quickFilters.needsReview).toBe(true);
      expect(useDocumentStore.getState().quickFilters.highValue).toBe(false);
    });
  });

  // ---------------------------------------------------------------------------
  // View
  // ---------------------------------------------------------------------------
  describe('view', () => {
    it('setViewMode changes the view mode', () => {
      useDocumentStore.getState().setViewMode('grid');
      expect(useDocumentStore.getState().viewMode).toBe('grid');
    });

    it('setSortBy toggles direction when called with the same field', () => {
      // Initial: sortBy='created_at', sortDirection='desc'
      // Calling with same field and no explicit direction should toggle
      useDocumentStore.getState().setSortBy('created_at');
      expect(useDocumentStore.getState().sortDirection).toBe('asc');

      useDocumentStore.getState().setSortBy('created_at');
      expect(useDocumentStore.getState().sortDirection).toBe('desc');
    });

    it('setSortBy accepts an explicit direction', () => {
      useDocumentStore.getState().setSortBy('amount', 'asc');
      const state = useDocumentStore.getState();
      expect(state.sortBy).toBe('amount');
      expect(state.sortDirection).toBe('asc');
    });

    it('setPageSize resets currentPage to 1', () => {
      useDocumentStore.setState({ currentPage: 5 });
      useDocumentStore.getState().setPageSize(25);

      const state = useDocumentStore.getState();
      expect(state.pageSize).toBe(25);
      expect(state.currentPage).toBe(1);
    });

    it('setCurrentPage updates the current page', () => {
      useDocumentStore.getState().setCurrentPage(3);
      expect(useDocumentStore.getState().currentPage).toBe(3);
    });
  });

  // ---------------------------------------------------------------------------
  // Upload Queue
  // ---------------------------------------------------------------------------
  describe('upload queue', () => {
    const mockFile = new File(['invoice content'], 'test-invoice.pdf', {
      type: 'application/pdf',
    });

    it('addToUploadQueue returns a unique id', () => {
      const id1 = useDocumentStore.getState().addToUploadQueue(mockFile);
      const id2 = useDocumentStore.getState().addToUploadQueue(mockFile);
      expect(id1).toBeDefined();
      expect(id2).toBeDefined();
      expect(id1).not.toBe(id2);
    });

    it('addToUploadQueue creates a pending entry with zero progress', () => {
      const id = useDocumentStore.getState().addToUploadQueue(mockFile);
      const entry = useDocumentStore.getState().uploadQueue.find((e) => e.id === id);

      expect(entry).toBeDefined();
      expect(entry!.status).toBe('pending');
      expect(entry!.progress).toBe(0);
      expect(entry!.file).toBe(mockFile);
    });

    it('updateUploadProgress changes progress on the correct entry', () => {
      const id = useDocumentStore.getState().addToUploadQueue(mockFile);
      useDocumentStore.getState().updateUploadProgress(id, 55);

      const entry = useDocumentStore.getState().uploadQueue.find((e) => e.id === id);
      expect(entry!.progress).toBe(55);
    });

    it('updateUploadStatus updates status, result, and error', () => {
      const id = useDocumentStore.getState().addToUploadQueue(mockFile);
      const mockResult = { document_id: 'doc-99' };
      useDocumentStore.getState().updateUploadStatus(id, 'completed', mockResult);

      const entry = useDocumentStore.getState().uploadQueue.find((e) => e.id === id);
      expect(entry!.status).toBe('completed');
      expect(entry!.result).toEqual(mockResult);

      // Test error case
      const id2 = useDocumentStore.getState().addToUploadQueue(mockFile);
      useDocumentStore.getState().updateUploadStatus(id2, 'error', undefined, 'Upload failed');

      const errorEntry = useDocumentStore.getState().uploadQueue.find((e) => e.id === id2);
      expect(errorEntry!.status).toBe('error');
      expect(errorEntry!.error).toBe('Upload failed');
    });

    it('removeFromUploadQueue filters out the specified entry', () => {
      const id1 = useDocumentStore.getState().addToUploadQueue(mockFile);
      const id2 = useDocumentStore.getState().addToUploadQueue(mockFile);

      useDocumentStore.getState().removeFromUploadQueue(id1);

      const queue = useDocumentStore.getState().uploadQueue;
      expect(queue).toHaveLength(1);
      expect(queue[0].id).toBe(id2);
    });

    it('clearUploadQueue empties the upload queue', () => {
      useDocumentStore.getState().addToUploadQueue(mockFile);
      useDocumentStore.getState().addToUploadQueue(mockFile);

      useDocumentStore.getState().clearUploadQueue();
      expect(useDocumentStore.getState().uploadQueue).toEqual([]);
    });

    it('supports multiple items in the queue simultaneously', () => {
      const file1 = new File(['a'], 'a.pdf', { type: 'application/pdf' });
      const file2 = new File(['b'], 'b.pdf', { type: 'application/pdf' });
      const file3 = new File(['c'], 'c.pdf', { type: 'application/pdf' });

      useDocumentStore.getState().addToUploadQueue(file1);
      useDocumentStore.getState().addToUploadQueue(file2);
      useDocumentStore.getState().addToUploadQueue(file3);

      expect(useDocumentStore.getState().uploadQueue).toHaveLength(3);
    });
  });

  // ---------------------------------------------------------------------------
  // Classification History
  // ---------------------------------------------------------------------------
  describe('classification history', () => {
    const makeEntry = (docId: string) => ({
      documentId: docId,
      timestamp: new Date().toISOString(),
      glAccount: '6100-Materials',
      paymentStatus: 'paid' as const,
      confidence: 0.95,
      method: 'claude_ai',
    });

    it('addClassificationHistory prepends new entries', () => {
      useDocumentStore.getState().addClassificationHistory(makeEntry('doc-1'));
      useDocumentStore.getState().addClassificationHistory(makeEntry('doc-2'));

      const history = useDocumentStore.getState().classificationHistory;
      expect(history[0].documentId).toBe('doc-2');
      expect(history[1].documentId).toBe('doc-1');
    });

    it('addClassificationHistory caps at 100 entries', () => {
      // Add 105 entries
      for (let i = 0; i < 105; i++) {
        useDocumentStore.getState().addClassificationHistory(makeEntry(`doc-${i}`));
      }

      expect(useDocumentStore.getState().classificationHistory).toHaveLength(100);
      // The most recent entry should be at index 0
      expect(useDocumentStore.getState().classificationHistory[0].documentId).toBe('doc-104');
    });

    it('clearClassificationHistory empties the array', () => {
      useDocumentStore.getState().addClassificationHistory(makeEntry('doc-1'));
      useDocumentStore.getState().clearClassificationHistory();

      expect(useDocumentStore.getState().classificationHistory).toEqual([]);
    });
  });

  // ---------------------------------------------------------------------------
  // Selectors
  // ---------------------------------------------------------------------------
  describe('selectors', () => {
    it('useDocumentSelection returns the expected shape', () => {
      const { result } = renderHook(() => useDocumentSelection());
      expect(result.current).toHaveProperty('selectedDocuments');
      expect(result.current).toHaveProperty('activeDocument');
      expect(result.current).toHaveProperty('select');
      expect(result.current).toHaveProperty('selectMultiple');
      expect(result.current).toHaveProperty('deselect');
      expect(result.current).toHaveProperty('toggle');
      expect(result.current).toHaveProperty('clear');
      expect(result.current).toHaveProperty('selectAll');
      expect(result.current).toHaveProperty('setActive');
    });

    it('useDocumentFilters returns the expected shape', () => {
      const { result } = renderHook(() => useDocumentFilters());
      expect(result.current).toHaveProperty('filters');
      expect(result.current).toHaveProperty('searchQuery');
      expect(result.current).toHaveProperty('quickFilters');
      expect(result.current).toHaveProperty('setFilters');
      expect(result.current).toHaveProperty('updateFilter');
      expect(result.current).toHaveProperty('clearFilters');
      expect(result.current).toHaveProperty('setSearchQuery');
      expect(result.current).toHaveProperty('setQuickFilter');
    });

    it('useDocumentView returns the expected shape', () => {
      const { result } = renderHook(() => useDocumentView());
      expect(result.current).toHaveProperty('viewMode');
      expect(result.current).toHaveProperty('sortBy');
      expect(result.current).toHaveProperty('sortDirection');
      expect(result.current).toHaveProperty('pageSize');
      expect(result.current).toHaveProperty('currentPage');
      expect(result.current).toHaveProperty('setViewMode');
      expect(result.current).toHaveProperty('setSortBy');
      expect(result.current).toHaveProperty('setPageSize');
      expect(result.current).toHaveProperty('setCurrentPage');
    });

    it('useUploadQueue returns the expected shape', () => {
      const { result } = renderHook(() => useUploadQueue());
      expect(result.current).toHaveProperty('queue');
      expect(result.current).toHaveProperty('add');
      expect(result.current).toHaveProperty('updateProgress');
      expect(result.current).toHaveProperty('updateStatus');
      expect(result.current).toHaveProperty('remove');
      expect(result.current).toHaveProperty('clear');
    });
  });
});
