import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  FileText,
  Settings,
  BarChart3,
  Folder,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useDashboardMetrics } from '@/hooks/api/useDashboard';
import { useSystemStatus } from '@/hooks/api/useSystemStatus';

interface NavigationProps {
  className?: string;
}

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  badge?: string | number;
}

const navItems: NavItem[] = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'Overview and metrics',
  },
  {
    to: '/upload',
    label: 'Upload',
    icon: Upload,
    description: 'Upload new documents',
  },
  {
    to: '/documents',
    label: 'Documents',
    icon: FileText,
    description: 'Browse and search documents',
  },
];

const secondaryNavItems: NavItem[] = [
  {
    to: '/reports',
    label: 'Reports',
    icon: BarChart3,
    description: 'Analytics and reporting',
  },
  {
    to: '/settings',
    label: 'Settings',
    icon: Settings,
    description: 'System configuration',
  },
];

export const Navigation: React.FC<NavigationProps> = ({ className }) => {
  const { data: metrics, isLoading: metricsLoading, dataUpdatedAt } = useDashboardMetrics();
  const { data: systemStatus } = useSystemStatus();

  const isOnline = systemStatus?.status === 'operational';

  const lastSyncLabel = React.useMemo(() => {
    if (!dataUpdatedAt) return 'Not synced yet';
    const seconds = Math.floor((Date.now() - dataUpdatedAt) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  }, [dataUpdatedAt]);

  return (
    <nav
      className={clsx(
        'w-64 bg-white border-r border-gray-200 flex flex-col',
        className
      )}
    >
      {/* Logo and brand */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <Folder className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              ASR Records
            </h2>
            <p className="text-xs text-gray-500">Legacy Edition</p>
          </div>
        </div>
      </div>

      {/* Quick stats */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-white rounded-lg p-3 shadow-soft">
            <div className="text-lg font-semibold text-gray-900">
              {metricsLoading ? '--' : (metrics?.totalDocuments?.toLocaleString() ?? '0')}
            </div>
            <div className="text-xs text-gray-500">Documents</div>
          </div>
          <div className="bg-white rounded-lg p-3 shadow-soft">
            <div className="text-lg font-semibold text-green-600">
              {metricsLoading ? '--' : `${metrics?.classificationAccuracy ?? metrics?.paymentAccuracy ?? 0}%`}
            </div>
            <div className="text-xs text-gray-500">Accuracy</div>
          </div>
        </div>
      </div>

      {/* Primary Navigation */}
      <div className="flex-1 px-4 py-6">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavigationItem key={item.to} item={item} />
          ))}
        </div>

        {/* Secondary Navigation */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Tools
          </h3>
          <div className="space-y-1">
            {secondaryNavItems.map((item) => (
              <NavigationItem key={item.to} item={item} />
            ))}
          </div>
        </div>
      </div>

      {/* Footer info */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <div className={clsx('h-2 w-2 rounded-full', isOnline ? 'bg-green-500' : 'bg-red-500')}></div>
          <span>{isOnline ? 'System Online' : 'System Offline'}</span>
        </div>
        <div className="mt-1 text-xs text-gray-400">
          Last sync: {lastSyncLabel}
        </div>
      </div>
    </nav>
  );
};

// Navigation Item Component
interface NavigationItemProps {
  item: NavItem;
}

const NavigationItem: React.FC<NavigationItemProps> = ({ item }) => {
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        clsx(
          'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors group',
          isActive
            ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        )
      }
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={clsx(
              'mr-3 h-5 w-5 flex-shrink-0',
              isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-gray-500'
            )}
          />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span>{item.label}</span>
              {item.badge && (
                <span className="ml-auto bg-primary-100 text-primary-800 text-xs px-2 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
            </div>
            {item.description && (
              <p
                className={clsx(
                  'text-xs mt-0.5',
                  isActive ? 'text-primary-600' : 'text-gray-500'
                )}
              >
                {item.description}
              </p>
            )}
          </div>
        </>
      )}
    </NavLink>
  );
};