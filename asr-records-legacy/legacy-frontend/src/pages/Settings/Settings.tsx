import React, { useState, useEffect } from 'react';
import { Server, Database, Shield, Activity, CheckCircle, AlertCircle, Palette, Bell } from 'lucide-react';
import { useSystemStatus, useSystemInfo } from '@/hooks/api/useSystemStatus';
import { useTenantId } from '@/stores/auth';
import { useTheme, useViewPreferences } from '@/stores/ui/uiStore';

export const Settings: React.FC = () => {
  const { data: systemStatus, isLoading: statusLoading } = useSystemStatus();
  const { data: systemInfo, isLoading: infoLoading } = useSystemInfo();
  const tenantId = useTenantId();
  const { theme, setTheme } = useTheme();
  const { preferences, update: updatePreference } = useViewPreferences();

  // Notification preferences stored in localStorage
  const [notifPrefs, setNotifPrefs] = useState(() => {
    try {
      const stored = localStorage.getItem('asr-notification-prefs');
      return stored ? JSON.parse(stored) : { documentProcessed: true, classificationFailed: true, manualReviewRequired: true };
    } catch {
      return { documentProcessed: true, classificationFailed: true, manualReviewRequired: true };
    }
  });

  useEffect(() => {
    try { localStorage.setItem('asr-notification-prefs', JSON.stringify(notifPrefs)); } catch { /* noop */ }
  }, [notifPrefs]);

  const isLoading = statusLoading || infoLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading system information...</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const capabilities = systemInfo?.capabilities;
  const services: Record<string, { status: string; count?: number; methods?: number; destinations?: number; backend?: string }> = systemStatus?.services || {};
  const isOperational = systemStatus?.status === 'operational';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          System configuration and status overview.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Information */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Server className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <h3 className="card-title">System Information</h3>
            </div>
          </div>
          <div className="space-y-4">
            <InfoRow label="System Type" value={systemInfo?.system_type || 'production_server'} />
            <InfoRow label="Version" value={systemInfo?.version || '--'} />
            <InfoRow
              label="GL Accounts"
              value={`${capabilities?.gl_accounts?.total || 79} accounts${capabilities?.gl_accounts?.enabled ? ' (enabled)' : ''}`}
            />
            <InfoRow
              label="Payment Methods"
              value={`${capabilities?.payment_detection?.methods || 5} methods${capabilities?.payment_detection?.consensus_enabled ? ', consensus enabled' : ''}`}
            />
            <InfoRow
              label="Billing Destinations"
              value={`${capabilities?.billing_router?.destinations || 4} destinations${capabilities?.billing_router?.audit_trails ? ', audit trails on' : ''}`}
            />
            <InfoRow
              label="Multi-tenant"
              value={capabilities?.multi_tenant ? 'Enabled' : 'Disabled'}
            />
            <InfoRow
              label="Scanner API"
              value={capabilities?.scanner_api ? 'Enabled' : 'Disabled'}
            />
          </div>
        </div>

        {/* API Status */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <h3 className="card-title">API Status</h3>
            </div>
            <div className="flex items-center space-x-2 mt-2">
              <div className={`h-3 w-3 rounded-full ${isOperational ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className={`text-sm font-medium ${isOperational ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
                {isOperational ? 'All Systems Operational' : 'Degraded Performance'}
              </span>
            </div>
          </div>
          <div className="space-y-3">
            {Object.entries(services).map(([name, service]) => (
              <div key={name} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                  {name.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center space-x-2">
                  {service.count != null && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">({service.count})</span>
                  )}
                  {service.methods != null && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">({service.methods} methods)</span>
                  )}
                  {service.destinations != null && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">({service.destinations} destinations)</span>
                  )}
                  {service.status === 'active' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  )}
                </div>
              </div>
            ))}
            {Object.keys(services).length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">No service data available</p>
            )}
          </div>
        </div>

        {/* Configuration */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <h3 className="card-title">Configuration</h3>
            </div>
          </div>
          <div className="space-y-4">
            <InfoRow label="Tenant ID" value={tenantId || 'default'} />
            <InfoRow
              label="Claude AI"
              value={systemStatus?.claude_ai === 'configured' ? 'Configured' : 'Not Configured'}
            />
            <InfoRow
              label="Storage Backend"
              value={services?.storage?.backend || 'local'}
            />
            <InfoRow
              label="Max File Size"
              value={`${systemInfo?.limits?.max_file_size_mb || 10} MB`}
            />
            <InfoRow
              label="Max Batch Size"
              value={`${systemInfo?.limits?.max_batch_size || 10} files`}
            />
            <InfoRow
              label="Max Scanner Clients"
              value={`${systemInfo?.limits?.max_scanner_clients || 5}`}
            />
          </div>
        </div>

        {/* Security */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <h3 className="card-title">Security</h3>
            </div>
          </div>
          <div className="space-y-4">
            <InfoRow label="Authentication" value="Bearer Token / JWT" />
            <InfoRow label="CORS" value="Restricted (localhost:3000, localhost:5173)" />
            <InfoRow label="Rate Limiting" value="100 req/min (sliding window)" />
            <InfoRow
              label="Audit Trails"
              value={capabilities?.billing_router?.audit_trails ? 'Enabled' : 'Disabled'}
            />
          </div>
        </div>

        {/* User Preferences */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Palette className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <h3 className="card-title">User Preferences</h3>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-sm text-gray-500 dark:text-gray-400">Theme</span>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
                className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                aria-label="Theme selector"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <span className="text-sm text-gray-500 dark:text-gray-400">Items per Page</span>
              <select
                value={preferences.itemsPerPage}
                onChange={(e) => updatePreference('itemsPerPage', Number(e.target.value))}
                className="text-sm border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                aria-label="Items per page selector"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <h3 className="card-title">Notification Preferences</h3>
            </div>
          </div>
          <div className="space-y-4">
            {([
              ['documentProcessed', 'Document Processed'],
              ['classificationFailed', 'Classification Failed'],
              ['manualReviewRequired', 'Manual Review Required'],
            ] as const).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
                <button
                  role="switch"
                  aria-checked={notifPrefs[key]}
                  aria-label={label}
                  onClick={() => setNotifPrefs((prev: Record<string, boolean>) => ({ ...prev, [key]: !prev[key] }))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notifPrefs[key] ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifPrefs[key] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const InfoRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
    <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{value}</span>
  </div>
);
