import { renderHook, act } from '@testing-library/react';
import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns the initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 300));
    expect(result.current).toBe('hello');
  });

  it('delays updating the value', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'a', delay: 300 } },
    );

    rerender({ value: 'ab', delay: 300 });
    // Still old value before timeout
    expect(result.current).toBe('a');

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toBe('ab');
  });

  it('resets timer on rapid changes and only fires once', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: '', delay: 300 } },
    );

    rerender({ value: 'i', delay: 300 });
    act(() => vi.advanceTimersByTime(100));
    rerender({ value: 'in', delay: 300 });
    act(() => vi.advanceTimersByTime(100));
    rerender({ value: 'inv', delay: 300 });
    act(() => vi.advanceTimersByTime(100));
    rerender({ value: 'invo', delay: 300 });

    // Should still be initial value
    expect(result.current).toBe('');

    act(() => vi.advanceTimersByTime(300));
    expect(result.current).toBe('invo');
  });

  it('cleans up timeout on unmount', () => {
    const { result, unmount, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'start', delay: 300 } },
    );

    rerender({ value: 'updated', delay: 300 });
    unmount();

    // Advancing timers after unmount should not cause errors
    act(() => vi.advanceTimersByTime(500));
    // result.current still holds last rendered value before unmount
    expect(result.current).toBe('start');
  });
});
