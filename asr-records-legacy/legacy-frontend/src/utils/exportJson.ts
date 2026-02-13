import type { Document as ApiDocument } from '@/types/api';

export function exportDocumentsJson(documents: ApiDocument[]): void {
  const data = documents.map((doc) => ({
    id: doc.id,
    filename: doc.filename || doc.original_filename || '',
    status: doc.status || '',
    tenant_id: doc.tenant_id || '',
    created_at: doc.created_at || '',
    vendor: doc.classification?.vendor_name || '',
    amount: doc.classification?.amount || 0,
    payment_status: doc.classification?.payment_status || '',
    gl_account_code: doc.classification?.gl_account_code || '',
    expense_category: doc.classification?.expense_category || '',
    routing_destination: doc.classification?.routing_destination || '',
    category_confidence: doc.classification?.category_confidence || 0,
  }));

  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const date = new Date().toISOString().split('T')[0];
  link.href = url;
  link.download = `asr-documents-export-${date}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
