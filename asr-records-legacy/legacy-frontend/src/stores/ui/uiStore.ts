import { create } from 'zustand';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

interface UIState {
  // Layout state
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';

  // Notifications
  notifications: Notification[];

  // Loading states
  globalLoading: boolean;
  loadingMessage?: string;

  // Modals and overlays
  activeModal?: string;
  modalData?: any;

  // Filters and preferences
  documentFilters: Record<string, any>;
  viewPreferences: {
    documentsView: 'table' | 'grid';
    itemsPerPage: number;
    sortBy: string;
    sortDirection: 'asc' | 'desc';
  };
}

interface UIActions {
  // Layout actions
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;

  // Notification actions
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // Loading actions
  setGlobalLoading: (loading: boolean, message?: string) => void;

  // Modal actions
  openModal: (modalId: string, data?: any) => void;
  closeModal: () => void;

  // Filter and preference actions
  setDocumentFilters: (filters: Record<string, any>) => void;
  updateViewPreference: <K extends keyof UIState['viewPreferences']>(
    key: K,
    value: UIState['viewPreferences'][K]
  ) => void;
  resetFilters: () => void;
}

type UIStore = UIState & UIActions;

export const useUIStore = create<UIStore>((set, get) => ({
  // Initial state
  sidebarCollapsed: false,
  theme: 'light',
  notifications: [],
  globalLoading: false,
  loadingMessage: undefined,
  activeModal: undefined,
  modalData: undefined,
  documentFilters: {},
  viewPreferences: {
    documentsView: 'table',
    itemsPerPage: 50,
    sortBy: 'created_at',
    sortDirection: 'desc',
  },

  // Layout actions
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setTheme: (theme) => {
    set({ theme });
    // Update document class for CSS theming
    if (typeof document !== 'undefined') {
      document.documentElement.className = theme;
    }
  },

  toggleTheme: () => {
    const currentTheme = get().theme;
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    get().setTheme(newTheme);
  },

  // Notification actions
  addNotification: (notification) => {
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification = { ...notification, id };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-remove notification after duration (default 5 seconds)
    const duration = notification.duration || 5000;
    setTimeout(() => {
      get().removeNotification(id);
    }, duration);
  },

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clearNotifications: () => set({ notifications: [] }),

  // Loading actions
  setGlobalLoading: (loading, message) =>
    set({ globalLoading: loading, loadingMessage: message }),

  // Modal actions
  openModal: (modalId, data) =>
    set({ activeModal: modalId, modalData: data }),

  closeModal: () =>
    set({ activeModal: undefined, modalData: undefined }),

  // Filter and preference actions
  setDocumentFilters: (filters) => set({ documentFilters: filters }),

  updateViewPreference: (key, value) =>
    set((state) => ({
      viewPreferences: {
        ...state.viewPreferences,
        [key]: value,
      },
    })),

  resetFilters: () => set({ documentFilters: {} }),
}));

// Selectors for convenience
export const useSidebarState = () => useUIStore((state) => ({
  collapsed: state.sidebarCollapsed,
  toggle: state.toggleSidebar,
  setCollapsed: state.setSidebarCollapsed,
}));

export const useTheme = () => useUIStore((state) => ({
  theme: state.theme,
  setTheme: state.setTheme,
  toggle: state.toggleTheme,
}));

export const useNotifications = () => useUIStore((state) => ({
  notifications: state.notifications,
  add: state.addNotification,
  remove: state.removeNotification,
  clear: state.clearNotifications,
}));

export const useGlobalLoading = () => useUIStore((state) => ({
  loading: state.globalLoading,
  message: state.loadingMessage,
  setLoading: state.setGlobalLoading,
}));

export const useModal = () => useUIStore((state) => ({
  activeModal: state.activeModal,
  modalData: state.modalData,
  open: state.openModal,
  close: state.closeModal,
}));

export const useViewPreferences = () => useUIStore((state) => ({
  preferences: state.viewPreferences,
  update: state.updateViewPreference,
}));

export const useDocumentFilters = () => useUIStore((state) => ({
  filters: state.documentFilters,
  setFilters: state.setDocumentFilters,
  reset: state.resetFilters,
}));