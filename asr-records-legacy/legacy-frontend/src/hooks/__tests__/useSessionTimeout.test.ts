import { renderHook, act } from '@testing-library/react';

// Mock dependencies before importing the hook
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn() },
}));

import { useSessionTimeout } from '../useSessionTimeout';

describe('useSessionTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('resets timer on user activity', () => {
    const logout = vi.fn();
    renderHook(() => useSessionTimeout(logout, 5000));

    // Advance 3 seconds — still within timeout
    act(() => { vi.advanceTimersByTime(3000); });
    expect(logout).not.toHaveBeenCalled();

    // Simulate activity
    act(() => { window.dispatchEvent(new Event('mousemove')); });

    // Advance another 3 seconds — still within new timeout window
    act(() => { vi.advanceTimersByTime(3000); });
    expect(logout).not.toHaveBeenCalled();
  });

  it('triggers logout on timeout', () => {
    const logout = vi.fn();
    renderHook(() => useSessionTimeout(logout, 5000));

    act(() => { vi.advanceTimersByTime(5001); });

    expect(logout).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});
