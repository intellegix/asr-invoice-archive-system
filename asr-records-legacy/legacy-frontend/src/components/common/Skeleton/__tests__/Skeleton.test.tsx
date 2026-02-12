import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Skeleton, MetricCardSkeleton, TableRowSkeleton, DashboardSkeleton } from '../Skeleton';

describe('Skeleton', () => {
  it('renders a single skeleton element', () => {
    render(<Skeleton />);
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('applies animate-pulse class', () => {
    render(<Skeleton />);
    expect(screen.getByTestId('skeleton')).toHaveClass('animate-pulse');
  });

  it('applies custom className', () => {
    render(<Skeleton className="h-6 w-32" />);
    expect(screen.getByTestId('skeleton')).toHaveClass('h-6');
    expect(screen.getByTestId('skeleton')).toHaveClass('w-32');
  });

  it('applies inline width and height styles', () => {
    render(<Skeleton width="100px" height="20px" />);
    const el = screen.getByTestId('skeleton');
    expect(el.style.width).toBe('100px');
    expect(el.style.height).toBe('20px');
  });

  it('renders rounded-full when circle is true', () => {
    render(<Skeleton circle />);
    expect(screen.getByTestId('skeleton')).toHaveClass('rounded-full');
  });

  it('renders multiple skeleton elements when count > 1', () => {
    render(<Skeleton count={3} />);
    expect(screen.getAllByTestId('skeleton')).toHaveLength(3);
  });
});

describe('MetricCardSkeleton', () => {
  it('renders a metric card skeleton', () => {
    render(<MetricCardSkeleton />);
    expect(screen.getByTestId('metric-card-skeleton')).toBeInTheDocument();
  });
});

describe('TableRowSkeleton', () => {
  it('renders a table row skeleton with default columns', () => {
    render(<TableRowSkeleton />);
    const el = screen.getByTestId('table-row-skeleton');
    expect(el).toBeInTheDocument();
    // Default 5 columns
    expect(el.children).toHaveLength(5);
  });

  it('renders specified number of columns', () => {
    render(<TableRowSkeleton columns={3} />);
    expect(screen.getByTestId('table-row-skeleton').children).toHaveLength(3);
  });
});

describe('DashboardSkeleton', () => {
  it('renders the dashboard skeleton', () => {
    render(<DashboardSkeleton />);
    expect(screen.getByTestId('dashboard-skeleton')).toBeInTheDocument();
  });

  it('renders 4 metric card skeletons', () => {
    render(<DashboardSkeleton />);
    expect(screen.getAllByTestId('metric-card-skeleton')).toHaveLength(4);
  });
});
