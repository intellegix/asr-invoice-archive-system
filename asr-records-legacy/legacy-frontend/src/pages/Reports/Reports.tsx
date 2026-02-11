import React from 'react';
import { FileText, CheckCircle, DollarSign, BarChart3 } from 'lucide-react';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { MetricCard } from '@/components/common/MetricCard';
import {
  useDashboardMetrics,
  usePaymentStatusDistribution,
  useGLAccountUsage,
  useTrendData,
} from '@/hooks/api/useDashboard';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const Reports: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics();
  const { data: paymentDistribution } = usePaymentStatusDistribution();
  const { data: glUsage } = useGLAccountUsage();
  const { data: trends } = useTrendData('30d');

  const glChartData = React.useMemo(() => {
    const accounts = (glUsage as any)?.accounts?.slice(0, 10) || [];
    return {
      labels: accounts.map((a: any) => a.name || a.code),
      datasets: [
        {
          label: 'Documents',
          data: accounts.map((a: any) => a.documentCount || 0),
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1,
        },
      ],
    };
  }, [glUsage]);

  const paymentChartData = React.useMemo(() => {
    const dist = (paymentDistribution as any)?.distribution || [];
    const colors = {
      paid: 'rgba(34, 197, 94, 0.8)',
      unpaid: 'rgba(234, 179, 8, 0.8)',
      partial: 'rgba(59, 130, 246, 0.8)',
      void: 'rgba(239, 68, 68, 0.8)',
      unknown: 'rgba(156, 163, 175, 0.8)',
    };
    return {
      labels: dist.map((d: any) => d.status?.charAt(0).toUpperCase() + d.status?.slice(1)),
      datasets: [
        {
          data: dist.map((d: any) => d.count || 0),
          backgroundColor: dist.map(
            (d: any) => colors[d.status as keyof typeof colors] || colors.unknown
          ),
          borderWidth: 2,
          borderColor: '#fff',
        },
      ],
    };
  }, [paymentDistribution]);

  const trendChartData = React.useMemo(() => {
    const docs = trends?.documents || [];
    return {
      labels: docs.map((d: any) => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
      datasets: [
        {
          label: 'Classified',
          data: docs.map((d: any) => d.classified || 0),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.3,
        },
        {
          label: 'Manual Review',
          data: docs.map((d: any) => d.manualReview || 0),
          borderColor: 'rgb(234, 179, 8)',
          backgroundColor: 'rgba(234, 179, 8, 0.1)',
          fill: true,
          tension: 0.3,
        },
      ],
    };
  }, [trends]);

  if (metricsLoading) {
    return (
      <div className="space-y-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
          <p className="mt-2 text-gray-600">Loading reports...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
        <p className="mt-2 text-gray-600">
          Analytics and insights from your document processing pipeline.
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Documents"
          value={metrics?.totalDocuments?.toLocaleString() || '0'}
          subtitle={`+${metrics?.documentsThisMonth || 0} this month`}
          icon={FileText}
          color="blue"
        />
        <MetricCard
          title="Classification Accuracy"
          value={`${metrics?.classificationAccuracy ?? metrics?.paymentAccuracy ?? 0}%`}
          subtitle="5-method consensus"
          icon={CheckCircle}
          color="green"
        />
        <MetricCard
          title="Total Amount"
          value={`$${((metrics?.totalAmountProcessed || 0) / 1000000).toFixed(1)}M`}
          subtitle="Lifetime value"
          icon={DollarSign}
          color="purple"
        />
        <MetricCard
          title="GL Accounts Used"
          value={`${metrics?.glAccountsUsed || 0}/${metrics?.totalGLAccounts || 79}`}
          subtitle={`${metrics?.manualReviewRate || 0}% manual review`}
          icon={BarChart3}
          color="yellow"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GL Account Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Documents by GL Account</h3>
            <p className="card-description">Top 10 most-used GL account classifications</p>
          </div>
          <div className="h-72">
            {glChartData.labels.length > 0 ? (
              <Bar
                data={glChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                  },
                  scales: {
                    x: { ticks: { maxRotation: 45, minRotation: 25 } },
                    y: { beginAtZero: true },
                  },
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No GL account data available
              </div>
            )}
          </div>
        </div>

        {/* Payment Status Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Payment Status Distribution</h3>
            <p className="card-description">5-method consensus detection results</p>
          </div>
          <div className="h-72 flex items-center justify-center">
            {paymentChartData.labels.length > 0 ? (
              <Doughnut
                data={paymentChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'right' },
                  },
                }}
              />
            ) : (
              <div className="text-gray-500">No payment data available</div>
            )}
          </div>
        </div>
      </div>

      {/* Processing Volume Trend */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Processing Volume (30 Days)</h3>
          <p className="card-description">Document processing volume over time</p>
        </div>
        <div className="h-72">
          {trendChartData.labels.length > 0 ? (
            <Line
              data={trendChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: 'top' },
                },
                scales: {
                  y: { beginAtZero: true },
                },
              }}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              No trend data available
            </div>
          )}
        </div>
      </div>

      {/* Billing Destinations Summary */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Billing Destination Routing</h3>
          <p className="card-description">Document routing across 4 billing destinations</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {metrics?.openPayable || 0}
            </div>
            <div className="text-sm text-gray-600">Open Payable</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {metrics?.closedPayable || 0}
            </div>
            <div className="text-sm text-gray-600">Closed Payable</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {metrics?.openReceivable || 0}
            </div>
            <div className="text-sm text-gray-600">Open Receivable</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {metrics?.closedReceivable || 0}
            </div>
            <div className="text-sm text-gray-600">Closed Receivable</div>
          </div>
        </div>
      </div>
    </div>
  );
};
