import React from 'react';

interface SkeletonProps {
  className?: string;
  /** Width — accepts Tailwind class or CSS value */
  width?: string;
  /** Height — accepts Tailwind class or CSS value */
  height?: string;
  /** Render a circle instead of a rectangle */
  circle?: boolean;
  /** Number of skeleton lines to render */
  count?: number;
}

/** Animated placeholder shown while content loads. */
export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  width,
  height,
  circle = false,
  count = 1,
}) => {
  const base = 'animate-pulse bg-gray-200 dark:bg-gray-700';
  const shape = circle ? 'rounded-full' : 'rounded';
  const style: React.CSSProperties = {};
  if (width) style.width = width;
  if (height) style.height = height;

  if (count > 1) {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={`${base} ${shape} ${className}`}
            style={style}
            data-testid="skeleton"
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${base} ${shape} ${className}`}
      style={style}
      data-testid="skeleton"
    />
  );
};

/** Pre-composed skeleton matching a MetricCard layout. */
export const MetricCardSkeleton: React.FC = () => (
  <div className="card animate-pulse" data-testid="metric-card-skeleton">
    <div className="flex items-center justify-between mb-4">
      <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
      <div className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded" />
    </div>
    <div className="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
    <div className="h-3 w-32 bg-gray-200 dark:bg-gray-700 rounded" />
  </div>
);

/** Pre-composed skeleton matching a table row. */
export const TableRowSkeleton: React.FC<{ columns?: number }> = ({ columns = 5 }) => (
  <div className="flex space-x-4 py-3" data-testid="table-row-skeleton">
    {Array.from({ length: columns }).map((_, i) => (
      <div
        key={i}
        className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
        style={{ width: `${100 / columns}%` }}
      />
    ))}
  </div>
);

/** Pre-composed skeleton for dashboard loading. */
export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6" data-testid="dashboard-skeleton">
    {/* Header */}
    <div className="mb-8">
      <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2" />
      <div className="h-4 w-72 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
    </div>

    {/* Metric cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <MetricCardSkeleton key={i} />
      ))}
    </div>

    {/* Content grid */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Recent docs skeleton */}
      <div className="card animate-pulse">
        <div className="h-5 w-40 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
        <div className="h-3 w-56 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>

      {/* Payment distribution skeleton */}
      <div className="card animate-pulse">
        <div className="h-5 w-52 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
        <div className="h-3 w-64 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="flex justify-between">
                <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
              </div>
              <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);
