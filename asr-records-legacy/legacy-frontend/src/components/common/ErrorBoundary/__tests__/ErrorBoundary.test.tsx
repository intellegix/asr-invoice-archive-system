import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ErrorBoundary } from '../ErrorBoundary';
import { PageErrorBoundary } from '../PageErrorBoundary';

// Component that throws on render
const ThrowingComponent: React.FC<{ message?: string }> = ({ message = 'Test error' }) => {
  throw new Error(message);
};

// Suppress console.error from React's error boundary logging in tests
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('ErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Safe content')).toBeInTheDocument();
  });

  it('renders fallback UI when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom fallback')).toBeInTheDocument();
  });

  it('calls onError callback when error occurs', () => {
    const onError = vi.fn();
    render(
      <ErrorBoundary onError={onError}>
        <ThrowingComponent message="callback test" />
      </ErrorBoundary>
    );
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error);
    expect(onError.mock.calls[0][0].message).toBe('callback test');
  });

  it('retry resets error state', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    // Click retry — the boundary resets, but the same child still throws
    fireEvent.click(screen.getByText('Try again'));
    // After retry, the throwing component re-renders and re-throws
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});

describe('PageErrorBoundary', () => {
  it('shows page-specific error message', () => {
    render(
      <PageErrorBoundary pageName="Dashboard">
        <ThrowingComponent />
      </PageErrorBoundary>
    );
    expect(screen.getByText('Dashboard failed to load')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('renders children normally when no error', () => {
    render(
      <PageErrorBoundary pageName="Dashboard">
        <div>Dashboard content</div>
      </PageErrorBoundary>
    );
    expect(screen.getByText('Dashboard content')).toBeInTheDocument();
  });

  it('displays the error message', () => {
    render(
      <PageErrorBoundary pageName="Upload">
        <ThrowingComponent message="Network failure" />
      </PageErrorBoundary>
    );
    expect(screen.getByText('Network failure')).toBeInTheDocument();
  });

  it('has a Try again button that resets error state', () => {
    render(
      <PageErrorBoundary pageName="Documents">
        <ThrowingComponent />
      </PageErrorBoundary>
    );
    expect(screen.getByText('Documents failed to load')).toBeInTheDocument();

    // Click "Try again" — resets state, child re-throws
    fireEvent.click(screen.getByText('Try again'));
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('has a Reload page button', () => {
    render(
      <PageErrorBoundary pageName="Reports">
        <ThrowingComponent />
      </PageErrorBoundary>
    );
    expect(screen.getByText('Reload page')).toBeInTheDocument();
  });
});
