import React, { useEffect, useRef } from 'react';
import { X, FileText, CheckCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { PermissionGate } from '@/components/auth/PermissionGate';
import { useDocumentReprocess } from '@/hooks/api/useDocuments';
import type { Document as ApiDocument, AuditStep } from '@/types/api';

interface DocumentDetailModalProps {
  document: ApiDocument | null;
  onClose: () => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  document: doc,
  onClose,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const reprocessMutation = useDocumentReprocess();

  useEffect(() => {
    if (!doc) return;

    // Save previously focused element
    previousFocusRef.current = document.activeElement as HTMLElement;

    // Focus the modal
    modalRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      // Focus trap: keep Tab cycling within the modal
      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      // Return focus on unmount
      previousFocusRef.current?.focus();
    };
  }, [doc, onClose]);

  if (!doc) return null;

  const classification = doc.classification;

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 95) return 'text-green-600';
    if (confidence > 85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDestination = (destination: string) =>
    destination
      ?.split('_')
      .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ') || 'Unknown';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabIndex={-1}
        className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto mx-4"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center space-x-3">
            <FileText className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h2 id="modal-title" className="text-lg font-semibold text-gray-900 dark:text-gray-100">Document Details</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Document Info */}
          <Section title="Document Information">
            <DetailRow label="Filename" value={doc.filename || doc.original_filename || '--'} />
            <DetailRow label="Status" value={doc.status?.replace('_', ' ')} />
            <DetailRow label="File Size" value={doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : '--'} />
            <DetailRow label="MIME Type" value={doc.mime_type || '--'} />
            <DetailRow label="Tenant" value={doc.tenant_id || '--'} />
            <DetailRow label="Created" value={doc.created_at ? new Date(doc.created_at).toLocaleString() : '--'} />
          </Section>

          {/* Classification */}
          {classification && (
            <Section title="Classification">
              <DetailRow label="GL Account" value={`${classification.gl_account_code || '--'} - ${classification.expense_category || '--'}`} />
              <DetailRow label="Suggested Category" value={classification.suggested_category || '--'} />
              <DetailRow
                label="Category Confidence"
                value={
                  <span className={getConfidenceColor(classification.category_confidence || 0)}>
                    {classification.category_confidence || 0}%
                  </span>
                }
              />
              <DetailRow label="Vendor" value={classification.vendor_name || '--'} />
              <DetailRow label="Amount" value={classification.amount ? `$${classification.amount.toLocaleString()}` : '--'} />
              <DetailRow label="Invoice Number" value={classification.invoice_number || '--'} />
              <DetailRow label="Invoice Date" value={classification.invoice_date || '--'} />
              <DetailRow label="Due Date" value={classification.due_date || '--'} />
            </Section>
          )}

          {/* Payment Detection */}
          {classification && (
            <Section title="Payment Detection (5-Method Consensus)">
              <DetailRow
                label="Payment Status"
                value={
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                    classification.payment_status === 'paid' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' :
                    classification.payment_status === 'unpaid' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300' :
                    'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                  }`}>
                    {classification.payment_status || 'unknown'}
                  </span>
                }
              />
              <DetailRow
                label="Payment Confidence"
                value={
                  <span className={getConfidenceColor(classification.payment_confidence || 0)}>
                    {classification.payment_confidence || 0}%
                  </span>
                }
              />
              {classification.consensus_methods && (
                <DetailRow
                  label="Methods Used"
                  value={classification.consensus_methods.join(', ')}
                />
              )}
            </Section>
          )}

          {/* Billing Route */}
          {classification && (
            <Section title="Billing Route">
              <DetailRow
                label="Destination"
                value={
                  <span className="px-2 py-1 text-xs rounded-md font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-300">
                    {formatDestination(classification.routing_destination)}
                  </span>
                }
              />
              <DetailRow
                label="Routing Confidence"
                value={`${classification.routing_confidence || 0}%`}
              />
              <DetailRow label="Routing Reason" value={classification.routing_reason || '--'} />
            </Section>
          )}

          {/* Claude AI Analysis */}
          {classification?.claude_analysis && (
            <Section title="Claude AI Analysis">
              <DetailRow label="Summary" value={classification.claude_analysis.summary || '--'} />
              <DetailRow
                label="AI Confidence"
                value={`${classification.claude_analysis.confidence || 0}%`}
              />
              {classification.claude_analysis.recommendations?.length > 0 && (
                <div className="py-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Recommendations</span>
                  <ul className="mt-1 text-sm text-gray-900 dark:text-gray-100 list-disc list-inside">
                    {classification.claude_analysis.recommendations.map((r: string, i: number) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Section>
          )}

          {/* Audit Trail */}
          {doc.audit_trail && doc.audit_trail.length > 0 && (
            <Section title="Audit Trail">
              <div className="space-y-2">
                {doc.audit_trail.map((step: AuditStep, i: number) => (
                  <div key={i} className="flex items-start space-x-3 py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                    <CheckCircle className="h-4 w-4 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{step.action}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(step.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4 rounded-b-xl">
          <div className="flex justify-end space-x-3">
            <PermissionGate resource="classifications" action="classify">
              <Button
                variant="primary"
                onClick={() => reprocessMutation.mutate(doc.id)}
                disabled={reprocessMutation.isPending}
              >
                <RefreshCw className={`h-4 w-4 mr-1.5 inline-block ${reprocessMutation.isPending ? 'animate-spin' : ''}`} />
                {reprocessMutation.isPending ? 'Re-Classifying...' : 'Re-Classify'}
              </Button>
            </PermissionGate>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div>
    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
      {title}
    </h3>
    <div className="space-y-1">{children}</div>
  </div>
);

const DetailRow: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex items-start justify-between py-1.5">
    <span className="text-sm text-gray-500 dark:text-gray-400 flex-shrink-0 mr-4">{label}</span>
    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 text-right">{value}</span>
  </div>
);
