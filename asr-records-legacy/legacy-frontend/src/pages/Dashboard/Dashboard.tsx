import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  CheckCircle,
  DollarSign,
  Clock,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { MetricCard } from '@/components/common/MetricCard';
import { DashboardSkeleton } from '@/components/common/Skeleton';
import { useDashboardMetrics, usePaymentStatusDistribution } from '@/hooks/api/useDashboard';
import type { PaymentStatusDistribution } from '@/types/api';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  // Real API calls - preserves all backend sophistication
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics();
  const { data: paymentDistribution } = usePaymentStatusDistribution();

  // Show skeleton loading state while data is being fetched
  if (metricsLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Welcome back! Here's what's happening with your document processing.
        </p>
      </div>

      {/* Key Metrics - preserves all backend sophistication */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Documents"
          value={metrics?.totalDocuments?.toLocaleString() || '0'}
          subtitle={`+${metrics?.documentsThisMonth || 0} this month`}
          icon={FileText}
          trend={metrics?.documentsTrend || { value: 0, direction: 'up', period: 'vs last month', isPositive: true }}
          color="blue"
        />

        <MetricCard
          title="Payment Accuracy"
          value={`${metrics?.paymentAccuracy || 0}%`}
          subtitle="5-method consensus detection"
          icon={CheckCircle}
          trend={metrics?.paymentAccuracyTrend || { value: 0, direction: 'up', period: 'vs last month', isPositive: true }}
          color="green"
        />

        <MetricCard
          title="Total Amount Processed"
          value={`$${((metrics?.totalAmountProcessed || 0) / 1000000).toFixed(1)}M`}
          subtitle="Lifetime processing value"
          icon={DollarSign}
          trend={undefined}
          color="purple"
        />

        <MetricCard
          title="GL Accounts Used"
          value={`${metrics?.glAccountsUsed || 0}/${metrics?.totalGLAccounts || 40}`}
          subtitle={`${metrics?.manualReviewRate || 0}% manual review`}
          icon={Clock}
          trend={metrics?.processingTimeTrend || { value: 0, direction: 'down', period: 'vs last month', isPositive: true }}
          color="yellow"
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Recent Documents</h3>
            <p className="card-description">
              Latest processed documents with AI classification
            </p>
          </div>
          <div className="space-y-4">
            {(metrics?.recentDocuments || []).map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <FileText className="h-5 w-5 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {doc.vendor} • ${doc.amount.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center space-x-4 text-xs">
                    <span className="text-gray-600 dark:text-gray-400">{doc.glAccount}</span>
                    <span
                      aria-label={`Payment status: ${doc.status}`}
                      className={`px-2 py-1 rounded-full ${
                        doc.status === 'paid'
                          ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                          : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300'
                      }`}
                    >
                      {doc.status}
                    </span>
                    <span className="px-2 py-1 text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-300 rounded-md">
                      {doc.billingDestination?.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">{doc.confidence}%</span>
                    {doc.confidence > 95 ? (
                      <CheckCircle className="h-4 w-4 text-green-500" aria-label="High confidence" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-yellow-500" aria-label="Low confidence" />
                    )}
                  </div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {new Date(doc.processedAt).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {(!metrics?.recentDocuments || metrics.recentDocuments.length === 0) && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <FileText className="mx-auto h-8 w-8 text-gray-400 dark:text-gray-500 mb-2" />
                <p>No recent documents processed</p>
              </div>
            )}
          </div>
        </div>

        {/* Payment Status Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Payment Status Distribution</h3>
            <p className="card-description">
              Breakdown of payment statuses across all documents
            </p>
          </div>
          <div className="space-y-4">
            {(paymentDistribution as PaymentStatusDistribution | undefined)?.distribution?.map((item) => {
              const colors = {
                paid: 'bg-green-500',
                unpaid: 'bg-yellow-500',
                partial: 'bg-blue-500',
                void: 'bg-red-500',
                unknown: 'bg-gray-500'
              };

              return (
                <div key={item.status} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                      {item.status}
                    </span>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {item.count} documents
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${colors[item.status as keyof typeof colors]}`}
                      style={{ width: `${item.percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}

            {(!(paymentDistribution as PaymentStatusDistribution | undefined)?.distribution || (paymentDistribution as PaymentStatusDistribution | undefined)?.distribution?.length === 0) && (
              <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                <p>No payment status data available</p>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">5-Method Consensus Accuracy</span>
              <span className="font-semibold text-green-600">
                {metrics?.paymentAccuracy || 0}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Quick Actions</h3>
          <p className="card-description">
            Common tasks to keep your document processing running smoothly
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={() => navigate('/upload')} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-300 dark:hover:border-primary-600 hover:bg-primary-50 dark:hover:bg-primary-950 transition-colors text-left">
            <FileText className="h-6 w-6 text-primary-600 dark:text-primary-400 mb-2" />
            <h4 className="font-medium text-gray-900 dark:text-gray-100">Upload Documents</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Add new documents for processing
            </p>
          </button>

          <button onClick={() => navigate('/reports')} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-300 dark:hover:border-primary-600 hover:bg-primary-50 dark:hover:bg-primary-950 transition-colors text-left">
            <TrendingUp className="h-6 w-6 text-primary-600 dark:text-primary-400 mb-2" />
            <h4 className="font-medium text-gray-900 dark:text-gray-100">View Reports</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Generate analytics and insights
            </p>
          </button>

          <button onClick={() => navigate('/documents')} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-300 dark:hover:border-primary-600 hover:bg-primary-50 dark:hover:bg-primary-950 transition-colors text-left">
            <AlertCircle className="h-6 w-6 text-primary-600 dark:text-primary-400 mb-2" />
            <h4 className="font-medium text-gray-900 dark:text-gray-100">Review Queue</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Check items needing manual review
            </p>
          </button>
        </div>
      </div>
    </div>
  );
};