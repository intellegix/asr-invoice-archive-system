import React, { type ReactNode } from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface PageErrorBoundaryProps {
  children: ReactNode;
  pageName: string;
}

export const PageErrorBoundary: React.FC<PageErrorBoundaryProps> = ({ children, pageName }) => {
  return (
    <ErrorBoundary
      fallback={
        <div role="alert" className="flex flex-col items-center justify-center h-64 text-center">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            {pageName} failed to load
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            An error occurred while rendering this page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
          >
            Reload page
          </button>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
};
