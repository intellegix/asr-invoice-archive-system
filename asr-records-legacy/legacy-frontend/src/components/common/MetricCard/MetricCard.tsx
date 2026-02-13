import React from 'react';
import { TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ComponentType<{ className?: string }>;
  trend?: TrendData;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gray';
  isLoading?: boolean;
  error?: string;
  onClick?: () => void;
  className?: string;
}

export interface TrendData {
  value: number;
  direction: 'up' | 'down' | 'neutral';
  period: string;
  isPositive: boolean;
}

const colorVariants = {
  blue: {
    icon: 'text-blue-600 dark:text-blue-400',
    accent: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
    trend: 'text-blue-600 dark:text-blue-400',
  },
  green: {
    icon: 'text-green-600 dark:text-green-400',
    accent: 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800',
    trend: 'text-green-600 dark:text-green-400',
  },
  yellow: {
    icon: 'text-yellow-600 dark:text-yellow-400',
    accent: 'bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800',
    trend: 'text-yellow-600 dark:text-yellow-400',
  },
  red: {
    icon: 'text-red-600 dark:text-red-400',
    accent: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800',
    trend: 'text-red-600 dark:text-red-400',
  },
  purple: {
    icon: 'text-purple-600 dark:text-purple-400',
    accent: 'bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800',
    trend: 'text-purple-600 dark:text-purple-400',
  },
  gray: {
    icon: 'text-gray-600 dark:text-gray-400',
    accent: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
    trend: 'text-gray-600 dark:text-gray-400',
  },
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'gray',
  isLoading = false,
  error,
  onClick,
  className,
}) => {
  const colors = colorVariants[color];

  const getTrendIcon = (direction: TrendData['direction']) => {
    switch (direction) {
      case 'up':
        return TrendingUp;
      case 'down':
        return TrendingDown;
      case 'neutral':
      default:
        return Minus;
    }
  };

  const getTrendColor = (trend: TrendData) => {
    if (trend.isPositive) {
      return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950';
    } else {
      return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950';
    }
  };

  if (isLoading) {
    return (
      <div className={clsx('card animate-pulse', className)}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          </div>
          <div className="h-12 w-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={clsx('card border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950', className)}>
        <div className="flex items-center space-x-3">
          <div className="h-12 w-12 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
            <div className="h-6 w-6 text-red-600 dark:text-red-400">!</div>
          </div>
          <div>
            <h3 className="text-sm font-medium text-red-900 dark:text-red-200">{title}</h3>
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'card transition-all duration-200',
        onClick && 'cursor-pointer hover:shadow-medium hover:-translate-y-0.5',
        colors.accent,
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
            {isLoading && <Loader2 className="h-3 w-3 animate-spin text-gray-400" />}
          </div>

          <div className="mt-2">
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</div>
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
            )}
          </div>

          {trend && (
            <div className="mt-3 flex items-center space-x-2">
              <div
                className={clsx(
                  'flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium',
                  getTrendColor(trend)
                )}
              >
                {React.createElement(getTrendIcon(trend.direction), {
                  className: 'h-3 w-3',
                })}
                <span>{Math.abs(trend.value)}%</span>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400">{trend.period}</span>
            </div>
          )}
        </div>

        {Icon && (
          <div className="ml-4">
            <div className="h-12 w-12 bg-white dark:bg-gray-700 rounded-lg shadow-soft flex items-center justify-center">
              <Icon className={clsx('h-6 w-6', colors.icon)} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};