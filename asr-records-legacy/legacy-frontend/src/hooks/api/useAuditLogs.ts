import { useQuery } from '@tanstack/react-query';
import { documentsAPI } from '@/services/api/documents';

interface AuditLogParams {
  tenant_id?: string;
  event_type?: string;
  limit?: number;
}

export const useAuditLogs = (params?: AuditLogParams) => {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => documentsAPI.fetchAuditLogs(params),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
};

export const useDocumentAuditLogs = (documentId: string) => {
  return useQuery({
    queryKey: ['audit-logs', 'document', documentId],
    queryFn: () => documentsAPI.fetchDocumentAuditLogs(documentId),
    enabled: !!documentId,
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
};
