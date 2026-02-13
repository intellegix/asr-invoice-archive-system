import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Folder, Key, Building2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/common/Button';
import { useAuthStore } from '@/stores/auth';
import { AuthService } from '@/services/api/auth';

export const Login: React.FC = () => {
  const [apiKey, setApiKey] = useState('');
  const [tenantId, setTenantId] = useState('default');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!apiKey.trim()) {
      setError('API key is required');
      return;
    }

    setIsLoading(true);
    try {
      const response = await AuthService.login(apiKey, tenantId);
      if (response.authenticated) {
        login(apiKey, tenantId);
        toast.success('Signed in successfully');
        navigate(from, { replace: true });
      } else {
        setError('Authentication failed');
        toast.error('Authentication failed');
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Authentication failed';
      setError(detail);
      toast.error(detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
          {/* Brand */}
          <div className="flex items-center justify-center space-x-3 mb-8">
            <div className="h-12 w-12 bg-primary-600 rounded-lg flex items-center justify-center">
              <Folder className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">ASR Records</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">Legacy Edition</p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 flex items-center gap-2 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300" role="alert">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* API Key */}
            <div>
              <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Key className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  disabled={isLoading}
                  placeholder="Enter your API key"
                  className="input pl-10 w-full"
                  autoComplete="off"
                />
              </div>
            </div>

            {/* Tenant ID */}
            <div>
              <label htmlFor="tenant-id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tenant ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building2 className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  id="tenant-id"
                  type="text"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  disabled={isLoading}
                  placeholder="default"
                  className="input pl-10 w-full"
                />
              </div>
            </div>

            {/* Submit */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isLoading}
              className="w-full"
            >
              Sign In
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};
