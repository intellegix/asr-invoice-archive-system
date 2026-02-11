import React from 'react';
import { Server, Database, Shield, Activity, CheckCircle, AlertCircle } from 'lucide-react';
import { useSystemStatus, useSystemInfo } from '@/hooks/api/useSystemStatus';
import { useTenantId } from '@/stores/auth';

export const Settings: React.FC = () => {
  const { data: systemStatus, isLoading: statusLoading } = useSystemStatus();
  const { data: systemInfo, isLoading: infoLoading } = useSystemInfo();
  const tenantId = useTenantId();

  const isLoading = statusLoading || infoLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-gray-600">Loading system information...</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const capabilities = systemInfo?.capabilities;
  const services = systemStatus?.services || {};
  const isOperational = systemStatus?.status === 'operational';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          System configuration and status overview.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Information */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Server className="h-5 w-5 text-gray-600" />
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
              <Activity className="h-5 w-5 text-gray-600" />
              <h3 className="card-title">API Status</h3>
            </div>
            <div className="flex items-center space-x-2 mt-2">
              <div className={`h-3 w-3 rounded-full ${isOperational ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className={`text-sm font-medium ${isOperational ? 'text-green-700' : 'text-red-700'}`}>
                {isOperational ? 'All Systems Operational' : 'Degraded Performance'}
              </span>
            </div>
          </div>
          <div className="space-y-3">
            {Object.entries(services).map(([name, service]: [string, any]) => (
              <div key={name} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <span className="text-sm text-gray-700 capitalize">
                  {name.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center space-x-2">
                  {service.count != null && (
                    <span className="text-xs text-gray-500">({service.count})</span>
                  )}
                  {service.methods != null && (
                    <span className="text-xs text-gray-500">({service.methods} methods)</span>
                  )}
                  {service.destinations != null && (
                    <span className="text-xs text-gray-500">({service.destinations} destinations)</span>
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
              <p className="text-sm text-gray-500">No service data available</p>
            )}
          </div>
        </div>

        {/* Configuration */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-gray-600" />
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
              <Shield className="h-5 w-5 text-gray-600" />
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
      </div>
    </div>
  );
};

const InfoRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
    <span className="text-sm text-gray-500">{label}</span>
    <span className="text-sm font-medium text-gray-900">{value}</span>
  </div>
);
