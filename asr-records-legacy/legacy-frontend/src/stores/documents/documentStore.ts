import { create } from 'zustand';
import type { Document, DocumentFilters, DocumentStatus, PaymentStatus } from '@/types/api';

interface DocumentState {
  // Current document selection
  selectedDocuments: string[];
  activeDocument?: Document;

  // Filters and search
  filters: DocumentFilters;
  searchQuery: string;
  quickFilters: {
    status?: DocumentStatus;
    paymentStatus?: PaymentStatus;
    needsReview: boolean;
    highValue: boolean;
  };

  // View state
  viewMode: 'table' | 'grid';
  sortBy: string;
  sortDirection: 'asc' | 'desc';
  pageSize: number;
  currentPage: number;

  // Processing state
  uploadQueue: Array<{
    id: string;
    file: File;
    status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
    progress: number;
    result?: any;
    error?: string;
  }>;

  // Classification state (preserves backend sophistication)
  classificationHistory: Array<{
    documentId: string;
    timestamp: string;
    glAccount: string;
    paymentStatus: PaymentStatus;
    confidence: number;
    method: string;
  }>;
}

interface DocumentActions {
  // Selection actions
  selectDocument: (id: string) => void;
  selectMultipleDocuments: (ids: string[]) => void;
  deselectDocument: (id: string) => void;
  clearSelection: () => void;
  toggleDocumentSelection: (id: string) => void;
  selectAll: (documentIds: string[]) => void;
  setActiveDocument: (document?: Document) => void;

  // Filter actions
  setFilters: (filters: Partial<DocumentFilters>) => void;
  updateFilter: <K extends keyof DocumentFilters>(key: K, value: DocumentFilters[K]) => void;
  clearFilters: () => void;
  setSearchQuery: (query: string) => void;
  setQuickFilter: <K extends keyof DocumentState['quickFilters']>(
    key: K,
    value: DocumentState['quickFilters'][K]
  ) => void;

  // View actions
  setViewMode: (mode: 'table' | 'grid') => void;
  setSortBy: (field: string, direction?: 'asc' | 'desc') => void;
  setPageSize: (size: number) => void;
  setCurrentPage: (page: number) => void;

  // Upload queue actions
  addToUploadQueue: (file: File) => string;
  updateUploadProgress: (id: string, progress: number) => void;
  updateUploadStatus: (
    id: string,
    status: DocumentState['uploadQueue'][0]['status'],
    result?: any,
    error?: string
  ) => void;
  removeFromUploadQueue: (id: string) => void;
  clearUploadQueue: () => void;

  // Classification actions
  addClassificationHistory: (entry: DocumentState['classificationHistory'][0]) => void;
  clearClassificationHistory: () => void;
}

type DocumentStore = DocumentState & DocumentActions;

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  // Initial state
  selectedDocuments: [],
  activeDocument: undefined,
  filters: {},
  searchQuery: '',
  quickFilters: {
    needsReview: false,
    highValue: false,
  },
  viewMode: 'table',
  sortBy: 'created_at',
  sortDirection: 'desc',
  pageSize: 50,
  currentPage: 1,
  uploadQueue: [],
  classificationHistory: [],

  // Selection actions
  selectDocument: (id) =>
    set((state) => ({
      selectedDocuments: state.selectedDocuments.includes(id)
        ? state.selectedDocuments
        : [...state.selectedDocuments, id],
    })),

  selectMultipleDocuments: (ids) =>
    set((state) => ({
      selectedDocuments: [...new Set([...state.selectedDocuments, ...ids])],
    })),

  deselectDocument: (id) =>
    set((state) => ({
      selectedDocuments: state.selectedDocuments.filter((docId) => docId !== id),
    })),

  clearSelection: () => set({ selectedDocuments: [] }),

  toggleDocumentSelection: (id) => {
    const state = get();
    if (state.selectedDocuments.includes(id)) {
      state.deselectDocument(id);
    } else {
      state.selectDocument(id);
    }
  },

  selectAll: (documentIds) => set({ selectedDocuments: documentIds }),

  setActiveDocument: (document) => set({ activeDocument: document }),

  // Filter actions
  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),

  updateFilter: (key, value) =>
    set((state) => ({ filters: { ...state.filters, [key]: value } })),

  clearFilters: () => set({ filters: {}, searchQuery: '', quickFilters: { needsReview: false, highValue: false } }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  setQuickFilter: (key, value) =>
    set((state) => ({
      quickFilters: { ...state.quickFilters, [key]: value },
    })),

  // View actions
  setViewMode: (mode) => set({ viewMode: mode }),

  setSortBy: (field, direction) =>
    set((state) => ({
      sortBy: field,
      sortDirection: direction || (state.sortBy === field && state.sortDirection === 'asc' ? 'desc' : 'asc'),
    })),

  setPageSize: (size) => set({ pageSize: size, currentPage: 1 }),

  setCurrentPage: (page) => set({ currentPage: page }),

  // Upload queue actions
  addToUploadQueue: (file) => {
    const id = `${file.name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    set((state) => ({
      uploadQueue: [
        ...state.uploadQueue,
        {
          id,
          file,
          status: 'pending',
          progress: 0,
        },
      ],
    }));
    return id;
  },

  updateUploadProgress: (id, progress) =>
    set((state) => ({
      uploadQueue: state.uploadQueue.map((item) =>
        item.id === id ? { ...item, progress } : item
      ),
    })),

  updateUploadStatus: (id, status, result, error) =>
    set((state) => ({
      uploadQueue: state.uploadQueue.map((item) =>
        item.id === id ? { ...item, status, result, error } : item
      ),
    })),

  removeFromUploadQueue: (id) =>
    set((state) => ({
      uploadQueue: state.uploadQueue.filter((item) => item.id !== id),
    })),

  clearUploadQueue: () => set({ uploadQueue: [] }),

  // Classification actions (preserves backend sophistication)
  addClassificationHistory: (entry) =>
    set((state) => ({
      classificationHistory: [entry, ...state.classificationHistory.slice(0, 99)], // Keep last 100
    })),

  clearClassificationHistory: () => set({ classificationHistory: [] }),
}));

// Selectors for convenience
export const useDocumentSelection = () => useDocumentStore((state) => ({
  selectedDocuments: state.selectedDocuments,
  activeDocument: state.activeDocument,
  select: state.selectDocument,
  selectMultiple: state.selectMultipleDocuments,
  deselect: state.deselectDocument,
  toggle: state.toggleDocumentSelection,
  clear: state.clearSelection,
  selectAll: state.selectAll,
  setActive: state.setActiveDocument,
}));

export const useDocumentFilters = () => useDocumentStore((state) => ({
  filters: state.filters,
  searchQuery: state.searchQuery,
  quickFilters: state.quickFilters,
  setFilters: state.setFilters,
  updateFilter: state.updateFilter,
  clearFilters: state.clearFilters,
  setSearchQuery: state.setSearchQuery,
  setQuickFilter: state.setQuickFilter,
}));

export const useDocumentView = () => useDocumentStore((state) => ({
  viewMode: state.viewMode,
  sortBy: state.sortBy,
  sortDirection: state.sortDirection,
  pageSize: state.pageSize,
  currentPage: state.currentPage,
  setViewMode: state.setViewMode,
  setSortBy: state.setSortBy,
  setPageSize: state.setPageSize,
  setCurrentPage: state.setCurrentPage,
}));

export const useUploadQueue = () => useDocumentStore((state) => ({
  queue: state.uploadQueue,
  add: state.addToUploadQueue,
  updateProgress: state.updateUploadProgress,
  updateStatus: state.updateUploadStatus,
  remove: state.removeFromUploadQueue,
  clear: state.clearUploadQueue,
}));

export const useClassificationHistory = () => useDocumentStore((state) => ({
  history: state.classificationHistory,
  add: state.addClassificationHistory,
  clear: state.clearClassificationHistory,
}));