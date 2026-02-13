import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Navigation } from '@/components/layout/Navigation';
import { ProtectedRoute } from '@/components/auth';
import { PageErrorBoundary } from '@/components/common/ErrorBoundary';
import { Dashboard } from '@/pages/Dashboard';
import { Upload } from '@/pages/Upload';
import { Documents } from '@/pages/Documents';
import { Login } from '@/pages/Login';

const Reports = lazy(() => import('@/pages/Reports/Reports').then(m => ({ default: m.Reports })));
const Settings = lazy(() => import('@/pages/Settings/Settings').then(m => ({ default: m.Settings })));
const Vendors = lazy(() => import('@/pages/Vendors/Vendors').then(m => ({ default: m.Vendors })));

const PageFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-pulse text-gray-500">Loading...</div>
  </div>
);

const App: React.FC = () => {
  return (
    <Routes>
      {/* Login — outside layout */}
      <Route path="/login" element={<Login />} />

      {/* All other routes — protected + full layout */}
      <Route path="/*" element={
        <ProtectedRoute>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
            <a
              href="#main-content"
              className="skip-to-content"
            >
              Skip to content
            </a>
            <Navigation />
            <div className="flex-1 flex flex-col">
              <Header />
              <main id="main-content" className="flex-1 p-6" tabIndex={-1}>
                <Suspense fallback={<PageFallback />}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<PageErrorBoundary pageName="Dashboard"><Dashboard /></PageErrorBoundary>} />
                    <Route path="/upload" element={<PageErrorBoundary pageName="Upload"><Upload /></PageErrorBoundary>} />
                    <Route path="/documents" element={<PageErrorBoundary pageName="Documents"><Documents /></PageErrorBoundary>} />
                    <Route path="/vendors" element={<PageErrorBoundary pageName="Vendors"><Vendors /></PageErrorBoundary>} />
                    <Route path="/reports" element={<PageErrorBoundary pageName="Reports"><Reports /></PageErrorBoundary>} />
                    <Route path="/settings" element={<PageErrorBoundary pageName="Settings"><Settings /></PageErrorBoundary>} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Suspense>
              </main>
            </div>
          </div>
        </ProtectedRoute>
      } />
    </Routes>
  );
};

export default App;
