import { renderHook } from '@testing-library/react';
import {
  useUIStore,
  useSidebarState,
  useTheme,
  useNotifications,
  useModal,
} from '../uiStore';

describe('uiStore', () => {
  beforeEach(() => {
    vi.clearAllTimers();
    useUIStore.setState({
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
    });
  });

  // ---------------------------------------------------------------------------
  // Layout
  // ---------------------------------------------------------------------------
  describe('layout', () => {
    it('setSidebarCollapsed sets the collapsed state', () => {
      useUIStore.getState().setSidebarCollapsed(true);
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);

      useUIStore.getState().setSidebarCollapsed(false);
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    });

    it('toggleSidebar flips the collapsed state', () => {
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);

      useUIStore.getState().toggleSidebar();
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);

      useUIStore.getState().toggleSidebar();
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    });

    it('setTheme changes the theme value', () => {
      useUIStore.getState().setTheme('dark');
      expect(useUIStore.getState().theme).toBe('dark');

      useUIStore.getState().setTheme('light');
      expect(useUIStore.getState().theme).toBe('light');
    });

    it('toggleTheme cycles light to dark and back', () => {
      expect(useUIStore.getState().theme).toBe('light');

      useUIStore.getState().toggleTheme();
      expect(useUIStore.getState().theme).toBe('dark');

      useUIStore.getState().toggleTheme();
      expect(useUIStore.getState().theme).toBe('light');
    });
  });

  // ---------------------------------------------------------------------------
  // Notifications
  // ---------------------------------------------------------------------------
  describe('notifications', () => {
    it('addNotification adds a notification to the list', () => {
      vi.useFakeTimers();

      useUIStore.getState().addNotification({
        type: 'success',
        title: 'Document processed',
        message: 'Invoice classified successfully',
      });

      const notifications = useUIStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('success');
      expect(notifications[0].title).toBe('Document processed');
      expect(notifications[0].message).toBe('Invoice classified successfully');

      vi.useRealTimers();
    });

    it('addNotification generates a unique id for each notification', () => {
      vi.useFakeTimers();

      useUIStore.getState().addNotification({ type: 'info', title: 'First' });
      useUIStore.getState().addNotification({ type: 'info', title: 'Second' });

      const notifications = useUIStore.getState().notifications;
      expect(notifications).toHaveLength(2);
      expect(notifications[0].id).toBeDefined();
      expect(notifications[1].id).toBeDefined();
      expect(notifications[0].id).not.toBe(notifications[1].id);

      vi.useRealTimers();
    });

    it('removeNotification filters out the specified notification', () => {
      vi.useFakeTimers();

      useUIStore.getState().addNotification({ type: 'info', title: 'Keep' });
      useUIStore.getState().addNotification({ type: 'error', title: 'Remove' });

      const idToRemove = useUIStore.getState().notifications[1].id;
      useUIStore.getState().removeNotification(idToRemove);

      const remaining = useUIStore.getState().notifications;
      expect(remaining).toHaveLength(1);
      expect(remaining[0].title).toBe('Keep');

      vi.useRealTimers();
    });

    it('clearNotifications empties the notifications array', () => {
      vi.useFakeTimers();

      useUIStore.getState().addNotification({ type: 'info', title: 'A' });
      useUIStore.getState().addNotification({ type: 'warning', title: 'B' });

      useUIStore.getState().clearNotifications();
      expect(useUIStore.getState().notifications).toEqual([]);

      vi.useRealTimers();
    });

    it('addNotification auto-removes after the specified duration', () => {
      vi.useFakeTimers();

      useUIStore.getState().addNotification({
        type: 'success',
        title: 'Temporary',
        duration: 1000,
      });

      expect(useUIStore.getState().notifications).toHaveLength(1);

      vi.advanceTimersByTime(1000);

      expect(useUIStore.getState().notifications).toHaveLength(0);

      vi.useRealTimers();
    });
  });

  // ---------------------------------------------------------------------------
  // Loading
  // ---------------------------------------------------------------------------
  describe('loading', () => {
    it('initial loading state is false', () => {
      expect(useUIStore.getState().globalLoading).toBe(false);
      expect(useUIStore.getState().loadingMessage).toBeUndefined();
    });

    it('setGlobalLoading true sets loading with a message', () => {
      useUIStore.getState().setGlobalLoading(true, 'Processing documents...');

      expect(useUIStore.getState().globalLoading).toBe(true);
      expect(useUIStore.getState().loadingMessage).toBe('Processing documents...');
    });

    it('setGlobalLoading false clears the loading message', () => {
      useUIStore.getState().setGlobalLoading(true, 'Loading...');
      useUIStore.getState().setGlobalLoading(false);

      expect(useUIStore.getState().globalLoading).toBe(false);
      expect(useUIStore.getState().loadingMessage).toBeUndefined();
    });
  });

  // ---------------------------------------------------------------------------
  // Modals
  // ---------------------------------------------------------------------------
  describe('modals', () => {
    it('openModal sets activeModal and modalData', () => {
      const data = { documentId: 'doc-123', action: 'delete' };
      useUIStore.getState().openModal('confirm-delete', data);

      expect(useUIStore.getState().activeModal).toBe('confirm-delete');
      expect(useUIStore.getState().modalData).toEqual(data);
    });

    it('closeModal clears both activeModal and modalData', () => {
      useUIStore.getState().openModal('edit-document', { id: '1' });
      useUIStore.getState().closeModal();

      expect(useUIStore.getState().activeModal).toBeUndefined();
      expect(useUIStore.getState().modalData).toBeUndefined();
    });

    it('modal data is optional', () => {
      useUIStore.getState().openModal('settings');

      expect(useUIStore.getState().activeModal).toBe('settings');
      expect(useUIStore.getState().modalData).toBeUndefined();
    });
  });

  // ---------------------------------------------------------------------------
  // Filters & Preferences
  // ---------------------------------------------------------------------------
  describe('filters and preferences', () => {
    it('setDocumentFilters replaces the entire filters object', () => {
      const filters = { status: 'pending', vendor: 'ACME' };
      useUIStore.getState().setDocumentFilters(filters);

      expect(useUIStore.getState().documentFilters).toEqual(filters);
    });

    it('updateViewPreference updates a single preference key', () => {
      useUIStore.getState().updateViewPreference('itemsPerPage', 25);

      const prefs = useUIStore.getState().viewPreferences;
      expect(prefs.itemsPerPage).toBe(25);
      // Other preferences remain unchanged
      expect(prefs.documentsView).toBe('table');
      expect(prefs.sortBy).toBe('created_at');
      expect(prefs.sortDirection).toBe('desc');
    });

    it('resetFilters clears documentFilters', () => {
      useUIStore.getState().setDocumentFilters({ status: 'completed' });
      useUIStore.getState().resetFilters();

      expect(useUIStore.getState().documentFilters).toEqual({});
    });

    it('has correct initial viewPreferences', () => {
      const prefs = useUIStore.getState().viewPreferences;
      expect(prefs).toEqual({
        documentsView: 'table',
        itemsPerPage: 50,
        sortBy: 'created_at',
        sortDirection: 'desc',
      });
    });
  });

  // ---------------------------------------------------------------------------
  // Selectors
  // ---------------------------------------------------------------------------
  describe('selectors', () => {
    it('useSidebarState returns the expected shape', () => {
      const { result } = renderHook(() => useSidebarState());
      expect(result.current).toHaveProperty('collapsed');
      expect(result.current).toHaveProperty('toggle');
      expect(result.current).toHaveProperty('setCollapsed');
    });

    it('useTheme returns the expected shape', () => {
      const { result } = renderHook(() => useTheme());
      expect(result.current).toHaveProperty('theme');
      expect(result.current).toHaveProperty('setTheme');
      expect(result.current).toHaveProperty('toggle');
    });

    it('useNotifications returns the expected shape', () => {
      const { result } = renderHook(() => useNotifications());
      expect(result.current).toHaveProperty('notifications');
      expect(result.current).toHaveProperty('add');
      expect(result.current).toHaveProperty('remove');
      expect(result.current).toHaveProperty('clear');
    });

    it('useModal returns the expected shape', () => {
      const { result } = renderHook(() => useModal());
      expect(result.current).toHaveProperty('activeModal');
      expect(result.current).toHaveProperty('modalData');
      expect(result.current).toHaveProperty('open');
      expect(result.current).toHaveProperty('close');
    });
  });
});
