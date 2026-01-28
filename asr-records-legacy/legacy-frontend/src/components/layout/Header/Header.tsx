import React from 'react';
import { Bell, User, Settings } from 'lucide-react';
import { Button } from '@/components/common/Button';

interface HeaderProps {
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({ className }) => {
  const currentUser = {
    name: 'John Doe',
    email: 'john.doe@asr-records.com',
    tenant: 'ASR Construction',
  };

  return (
    <header className={`bg-white border-b border-gray-200 px-6 py-4 ${className || ''}`}>
      <div className="flex items-center justify-between">
        {/* Left side - Page title and breadcrumbs will be added here later */}
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-semibold text-gray-900">
            ASR Records Legacy
          </h1>
          <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
            {currentUser.tenant}
          </span>
        </div>

        {/* Right side - User actions */}
        <div className="flex items-center space-x-3">
          {/* Notifications */}
          <Button
            variant="ghost"
            size="sm"
            className="relative p-2"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5 text-gray-600" />
            {/* Notification indicator */}
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
          </Button>

          {/* Settings */}
          <Button
            variant="ghost"
            size="sm"
            className="p-2"
            aria-label="Settings"
          >
            <Settings className="h-5 w-5 text-gray-600" />
          </Button>

          {/* User menu */}
          <div className="flex items-center space-x-3 pl-3 border-l border-gray-200">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">
                {currentUser.name}
              </p>
              <p className="text-xs text-gray-500">
                {currentUser.email}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="p-2"
              aria-label="User menu"
            >
              <User className="h-5 w-5 text-gray-600" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};