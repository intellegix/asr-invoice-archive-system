import type { Document as ApiDocument } from '@/types/api';

export function exportDocumentsCsv(documents: ApiDocument[]): void {
  const headers = [
    'Document Name',
    'Vendor',
    'Amount',
    'Payment Status',
    'GL Account Code',
    'Expense Category',
    'Destination',
    'Confidence',
    'Date',
  ];

  const rows = documents.map((doc) => [
    doc.filename || doc.original_filename || '',
    doc.classification?.vendor_name || '',
    doc.classification?.amount || 0,
    doc.classification?.payment_status || '',
    doc.classification?.gl_account_code || '',
    doc.classification?.expense_category || '',
    doc.classification?.routing_destination || '',
    doc.classification?.category_confidence || 0,
    doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '',
  ]);

  const escapeCsvField = (field: string | number | undefined): string => {
    const str = String(field);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const csvContent = [
    headers.join(','),
    ...rows.map((row) => row.map(escapeCsvField).join(',')),
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const date = new Date().toISOString().split('T')[0];
  link.href = url;
  link.download = `asr-documents-export-${date}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
