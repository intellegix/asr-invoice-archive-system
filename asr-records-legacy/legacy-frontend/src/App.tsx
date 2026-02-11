import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Navigation } from '@/components/layout/Navigation';
import { Dashboard } from '@/pages/Dashboard';
import { Upload } from '@/pages/Upload';
import { Documents } from '@/pages/Documents';

const Reports = lazy(() => import('@/pages/Reports/Reports').then(m => ({ default: m.Reports })));
const Settings = lazy(() => import('@/pages/Settings/Settings').then(m => ({ default: m.Settings })));

const PageFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-pulse text-gray-500">Loading...</div>
  </div>
);

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Navigation Sidebar */}
      <Navigation />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 p-6">
          <Suspense fallback={<PageFallback />}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />

              {/* Catch all route - redirect to dashboard */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
};

export default App;