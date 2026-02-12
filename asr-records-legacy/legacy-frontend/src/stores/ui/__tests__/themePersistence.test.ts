import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from '../uiStore';

describe('theme persistence', () => {
  beforeEach(() => {
    localStorage.clear();
    useUIStore.setState({ theme: 'light' });
    document.documentElement.classList.remove('light', 'dark');
  });

  it('setTheme persists to localStorage', () => {
    useUIStore.getState().setTheme('dark');
    expect(localStorage.getItem('asr-ui-theme')).toBe('dark');
  });

  it('setTheme applies CSS class to document', () => {
    useUIStore.getState().setTheme('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.classList.contains('light')).toBe(false);
  });

  it('toggleTheme persists new theme', () => {
    useUIStore.getState().setTheme('light');
    useUIStore.getState().toggleTheme();
    expect(useUIStore.getState().theme).toBe('dark');
    expect(localStorage.getItem('asr-ui-theme')).toBe('dark');
  });

  it('switching back to light removes dark class', () => {
    useUIStore.getState().setTheme('dark');
    useUIStore.getState().setTheme('light');
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem('asr-ui-theme')).toBe('light');
  });
});
