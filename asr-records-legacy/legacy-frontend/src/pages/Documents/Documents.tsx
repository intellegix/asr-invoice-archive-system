import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, FileText, CheckCircle, Clock, AlertCircle, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/common/Button';
import { useDocuments, useDocumentSearch, useDocumentDelete, useDocument } from '@/hooks/api/useDocuments';
import { useDocumentView } from '@/stores/documents';
import { useDebounce } from '@/hooks/useDebounce';
import { FilterPanel } from '@/components/documents/FilterPanel';
import { DocumentDetailModal } from '@/components/documents/DocumentDetailModal';
import { exportDocumentsCsv } from '@/utils/exportCsv';
import { exportDocumentsJson } from '@/utils/exportJson';
import type { DocumentFilters } from '@/types/api';

export const Documents: React.FC = () => {
  const [filters, setFilters] = useState<DocumentFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [activeQuickFilter, setActiveQuickFilter] = useState<string>('all');
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [viewingDocumentId, setViewingDocumentId] = useState<string | null>(null);
  const { currentPage, pageSize, setCurrentPage, setPageSize } = useDocumentView();

  // Real API calls - preserves all backend sophistication
  const { data: documents = [], isLoading } = useDocuments(filters, currentPage, pageSize);
  const searchMutation = useDocumentSearch();
  const deleteMutation = useDocumentDelete();
  const { data: viewingDocument } = useDocument(viewingDocumentId || '');

  const debouncedQuery = useDebounce(searchQuery, 300);

  useEffect(() => {
    if (debouncedQuery.trim()) {
      searchMutation.mutate({ query: debouncedQuery, filters });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQuery, filters]);

  const displayedDocuments = debouncedQuery && searchMutation.data?.documents
    ? searchMutation.data.documents
    : documents;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'classified':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'manual_review':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  const getPaymentStatusBadge = (status: string) => {
    const baseClasses = 'px-2 py-1 text-xs rounded-full font-medium';
    switch (status) {
      case 'paid':
        return `${baseClasses} bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300`;
      case 'unpaid':
        return `${baseClasses} bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300`;
      case 'partial':
        return `${baseClasses} bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300`;
      case 'void':
        return `${baseClasses} bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300`;
      default:
        return `${baseClasses} bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300`;
    }
  };

  const getBillingDestinationBadge = (destination: string) => {
    const baseClasses = 'px-2 py-1 text-xs rounded-md font-medium';
    switch (destination) {
      case 'open_payable':
        return `${baseClasses} bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-300`;
      case 'closed_payable':
        return `${baseClasses} bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300`;
      case 'open_receivable':
        return `${baseClasses} bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300`;
      case 'closed_receivable':
        return `${baseClasses} bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-300`;
      default:
        return `${baseClasses} bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300`;
    }
  };

  const formatDestination = (destination: string) => {
    return destination
      ?.split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ') || 'Unknown';
  };

  const renderLoadingState = () => (
    <div className="p-6">
      <div className="animate-pulse space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex space-x-4">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6"></div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderEmptyState = () => (
    <div className="p-12 text-center">
      <FileText className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No documents found</h3>
      <p className="text-gray-500 dark:text-gray-400">
        {searchQuery
          ? `No documents match "${searchQuery}". Try adjusting your search.`
          : 'Upload documents to get started with AI classification.'
        }
      </p>
    </div>
  );

  const renderDocumentsTable = () => (
    <div className="overflow-x-auto">
      <table className="table">
        <thead>
          <tr>
            <th>Document</th>
            <th>Vendor</th>
            <th>Amount</th>
            <th>Payment Status</th>
            <th>GL Account</th>
            <th>Destination</th>
            <th>Confidence</th>
            <th>Processed</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {displayedDocuments.map((doc: any) => (
            <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
              <td>
                <div className="flex items-center space-x-3">
                  {getStatusIcon(doc.status)}
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {doc.filename || doc.original_filename || 'Unknown'}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                      {doc.status?.replace('_', ' ') || 'Unknown'}
                    </div>
                  </div>
                </div>
              </td>
              <td>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {doc.classification?.vendor_name || 'Unknown'}
                </div>
              </td>
              <td>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  ${doc.classification?.amount?.toLocaleString() || '0'}
                </div>
              </td>
              <td>
                <span className={getPaymentStatusBadge(doc.classification?.payment_status)}>
                  {doc.classification?.payment_status || 'unknown'}
                </span>
              </td>
              <td>
                <div className="text-sm text-gray-900 dark:text-gray-100">
                  {doc.classification?.gl_account_code} - {doc.classification?.expense_category}
                </div>
              </td>
              <td>
                <span className={getBillingDestinationBadge(doc.classification?.routing_destination)}>
                  {formatDestination(doc.classification?.routing_destination)}
                </span>
              </td>
              <td>
                <div className="flex items-center space-x-1">
                  <span
                    className={`text-sm font-medium ${
                      (doc.classification?.category_confidence || 0) > 95
                        ? 'text-green-600'
                        : (doc.classification?.category_confidence || 0) > 85
                        ? 'text-yellow-600'
                        : 'text-red-600'
                    }`}
                  >
                    {doc.classification?.category_confidence || 0}%
                  </span>
                  {(doc.classification?.category_confidence || 0) > 95 ? (
                    <CheckCircle className="h-4 w-4 text-green-500" aria-label="High confidence" />
                  ) : (doc.classification?.category_confidence || 0) > 85 ? (
                    <AlertTriangle className="h-4 w-4 text-yellow-500" aria-label="Medium confidence" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" aria-label="Low confidence" />
                  )}
                </div>
              </td>
              <td>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(doc.created_at).toLocaleDateString()}
                </div>
                <div className="text-xs text-gray-400 dark:text-gray-500">
                  {new Date(doc.created_at).toLocaleTimeString()}
                </div>
              </td>
              <td>
                <div className="flex space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setViewingDocumentId(doc.id);
                    }}
                  >
                    View
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteMutation.mutate(doc.id, {
                      onSuccess: () => toast.success('Document deleted'),
                      onError: () => toast.error('Failed to delete document'),
                    })}
                    className="text-red-600 hover:text-red-700"
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Documents</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Browse and manage all processed documents with their classifications and routing information.
        </p>
      </div>

      {/* Filters and Search */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents, vendors, or GL accounts..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Filter buttons */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              leftIcon={<Filter className="h-4 w-4" />}
              onClick={() => setShowFilterPanel(!showFilterPanel)}
            >
              Filters
            </Button>
            <div className="relative">
              <Button
                variant="outline"
                leftIcon={<Download className="h-4 w-4" />}
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={displayedDocuments.length === 0}
              >
                Export
              </Button>
              {showExportMenu && (
                <div className="absolute right-0 mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg z-10">
                  <button
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-md"
                    onClick={() => { exportDocumentsCsv(displayedDocuments); setShowExportMenu(false); }}
                  >
                    Export CSV
                  </button>
                  <button
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-md"
                    onClick={() => { exportDocumentsJson(displayedDocuments); setShowExportMenu(false); }}
                  >
                    Export JSON
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilterPanel && (
          <FilterPanel
            currentFilters={filters}
            onApply={(newFilters) => {
              setFilters(newFilters);
              setActiveQuickFilter('all');
              setCurrentPage(1);
            }}
            onClose={() => setShowFilterPanel(false)}
          />
        )}

        {/* Quick filters */}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            className={`px-3 py-1 text-sm rounded-full ${
              activeQuickFilter === 'all'
                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
            onClick={() => {
              setActiveQuickFilter('all');
              setFilters({});
              setCurrentPage(1);
            }}
          >
            All Documents ({displayedDocuments.length})
          </button>
          <button
            className={`px-3 py-1 text-sm rounded-full ${
              activeQuickFilter === 'review'
                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
            onClick={() => {
              setActiveQuickFilter('review');
              setFilters({ confidence_threshold: 0.7 });
              setCurrentPage(1);
            }}
          >
            Manual Review ({displayedDocuments.filter((doc: any) => doc.status === 'manual_review').length})
          </button>
          <button
            className={`px-3 py-1 text-sm rounded-full ${
              activeQuickFilter === 'unpaid'
                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
            onClick={() => {
              setActiveQuickFilter('unpaid');
              setFilters({ payment_status: ['unpaid'] });
              setCurrentPage(1);
            }}
          >
            Unpaid ({displayedDocuments.filter((doc: any) => doc.classification?.payment_status === 'unpaid').length})
          </button>
          <button
            className={`px-3 py-1 text-sm rounded-full ${
              activeQuickFilter === 'highvalue'
                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
            onClick={() => {
              setActiveQuickFilter('highvalue');
              setFilters({ amount_range: { min: 10000, max: Number.MAX_SAFE_INTEGER } });
              setCurrentPage(1);
            }}
          >
            High Value ($10K+) ({displayedDocuments.filter((doc: any) => (doc.classification?.amount || 0) > 10000).length})
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="card overflow-hidden">
        {isLoading && renderLoadingState()}
        {!isLoading && displayedDocuments.length === 0 && renderEmptyState()}
        {!isLoading && displayedDocuments.length > 0 && renderDocumentsTable()}

        {/* Pagination */}
        {displayedDocuments.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Showing {((currentPage - 1) * pageSize) + 1}-{((currentPage - 1) * pageSize) + displayedDocuments.length} documents
                  {searchQuery && searchMutation.data?.total && ` of ${searchMutation.data.total} total`}
                </span>
                <select
                  className="text-sm border border-gray-200 dark:border-gray-700 rounded-md px-2 py-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                >
                  <option value={25}>25/page</option>
                  <option value={50}>50/page</option>
                  <option value={100}>100/page</option>
                </select>
              </div>
              <div className="flex space-x-1">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                >
                  Previous
                </Button>
                <Button variant="outline" size="sm" className="bg-primary-50 text-primary-600">
                  {currentPage}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={displayedDocuments.length < pageSize}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats - shows preserved backend sophistication */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {displayedDocuments.length}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {searchQuery ? 'Search Results' : 'Total Documents'}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {displayedDocuments.length > 0
              ? Math.round(
                  (displayedDocuments.filter((doc: any) =>
                    (doc.classification?.category_confidence || 0) > 85
                  ).length / displayedDocuments.length) * 100
                )
              : 0}%
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">High Confidence Classifications</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
            $
            {displayedDocuments.length > 0
              ? (displayedDocuments.reduce((sum: number, doc: any) =>
                  sum + (doc.classification?.amount || 0), 0
                ) / 1000000).toFixed(1)
              : 0}M
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Amount Processed</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {displayedDocuments.length > 0
              ? new Set(displayedDocuments.map((doc: any) =>
                  doc.classification?.gl_account_code
                ).filter(Boolean)).size
              : 0}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">GL Accounts in Use</div>
        </div>
      </div>

      {/* Document Detail Modal */}
      {viewingDocumentId && viewingDocument && (
        <DocumentDetailModal
          document={viewingDocument}
          onClose={() => setViewingDocumentId(null)}
        />
      )}
    </div>
  );
};