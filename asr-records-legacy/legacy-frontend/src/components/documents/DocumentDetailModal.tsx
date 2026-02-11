import React from 'react';
import { X, FileText, CheckCircle } from 'lucide-react';
import { Button } from '@/components/common/Button';

interface DocumentDetailModalProps {
  document: any;
  onClose: () => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  document: doc,
  onClose,
}) => {
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
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto mx-4">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center space-x-3">
            <FileText className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Document Details</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
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
                    classification.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                    classification.payment_status === 'unpaid' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
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
                  <span className="px-2 py-1 text-xs rounded-md font-medium bg-purple-100 text-purple-800">
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
                  <span className="text-sm text-gray-500">Recommendations</span>
                  <ul className="mt-1 text-sm text-gray-900 list-disc list-inside">
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
                {doc.audit_trail.map((step: any, i: number) => (
                  <div key={i} className="flex items-start space-x-3 py-2 border-b border-gray-100 last:border-0">
                    <CheckCircle className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-gray-900">{step.action}</p>
                      <p className="text-xs text-gray-500">
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
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 rounded-b-xl">
          <div className="flex justify-end">
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
    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b border-gray-200">
      {title}
    </h3>
    <div className="space-y-1">{children}</div>
  </div>
);

const DetailRow: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex items-start justify-between py-1.5">
    <span className="text-sm text-gray-500 flex-shrink-0 mr-4">{label}</span>
    <span className="text-sm font-medium text-gray-900 text-right">{value}</span>
  </div>
);
