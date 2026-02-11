import { render, screen, fireEvent } from '@testing-library/react';
import { MetricCard } from '@/components/common/MetricCard';
import type { TrendData } from '@/components/common/MetricCard';

const MockIcon = ({ className }: { className?: string }) => (
  <span data-testid="mock-icon" className={className}>
    Icon
  </span>
);

describe('MetricCard', () => {
  // --- Basic rendering ---

  it('renders title', () => {
    render(<MetricCard title="Total Documents" value="1,234" />);
    expect(screen.getByText('Total Documents')).toBeInTheDocument();
  });

  it('renders value as string', () => {
    render(<MetricCard title="Revenue" value="$45,000" />);
    expect(screen.getByText('$45,000')).toBeInTheDocument();
  });

  it('renders value as number', () => {
    render(<MetricCard title="Count" value={42} />);
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(
      <MetricCard title="Docs" value="100" subtitle="Last 30 days" />
    );
    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    render(<MetricCard title="Docs" value="100" />);
    expect(screen.queryByText('Last 30 days')).not.toBeInTheDocument();
  });

  it('renders icon when provided', () => {
    render(<MetricCard title="Docs" value="100" icon={MockIcon} />);
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
  });

  // --- Color variants ---

  it('renders with blue color variant', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" color="blue" />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('bg-blue-50');
  });

  it('renders with green color variant', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" color="green" />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('bg-green-50');
  });

  it('renders with yellow color variant', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" color="yellow" />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('bg-yellow-50');
  });

  it('renders with red color variant', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" color="red" />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('bg-red-50');
  });

  it('renders with purple color variant', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" color="purple" />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('bg-purple-50');
  });

  it('renders with gray color (default)', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('bg-gray-50');
  });

  // --- Loading state ---

  it('renders loading skeleton when isLoading', () => {
    const { container } = render(
      <MetricCard title="Docs" value="100" isLoading />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('animate-pulse');
  });

  it('does not render title/value in loading state', () => {
    render(<MetricCard title="Docs" value="100" isLoading />);
    expect(screen.queryByText('Docs')).not.toBeInTheDocument();
    expect(screen.queryByText('100')).not.toBeInTheDocument();
  });

  // --- Error state ---

  it('renders error state with error message', () => {
    render(
      <MetricCard title="Docs" value="100" error="Failed to load" />
    );
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('renders error state with title', () => {
    render(
      <MetricCard title="Documents" value="100" error="Connection lost" />
    );
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Connection lost')).toBeInTheDocument();
  });

  // --- Trend ---

  it('renders trend with up direction', () => {
    const trend: TrendData = {
      value: 12,
      direction: 'up',
      period: 'vs last month',
      isPositive: true,
    };
    render(<MetricCard title="Docs" value="100" trend={trend} />);
    expect(screen.getByText('12%')).toBeInTheDocument();
    expect(screen.getByText('vs last month')).toBeInTheDocument();
  });

  it('renders trend with down direction', () => {
    const trend: TrendData = {
      value: 5,
      direction: 'down',
      period: 'vs last week',
      isPositive: false,
    };
    render(<MetricCard title="Docs" value="100" trend={trend} />);
    expect(screen.getByText('5%')).toBeInTheDocument();
    expect(screen.getByText('vs last week')).toBeInTheDocument();
  });

  it('renders trend with neutral direction', () => {
    const trend: TrendData = {
      value: 0,
      direction: 'neutral',
      period: 'no change',
      isPositive: true,
    };
    render(<MetricCard title="Docs" value="100" trend={trend} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByText('no change')).toBeInTheDocument();
  });

  // --- onClick ---

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    const { container } = render(
      <MetricCard title="Docs" value="100" onClick={handleClick} />
    );
    const card = container.firstElementChild as HTMLElement;
    expect(card.className).toContain('cursor-pointer');
    fireEvent.click(card);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
