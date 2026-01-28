import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsAPI } from '@/services/api/documents';
import { invalidateQueries } from '@/services/api/client';
import type { DocumentFilters } from '@/types/api';
import toast from 'react-hot-toast';

// List documents with filters
export const useDocuments = (filters?: DocumentFilters) => {
  return useQuery({
    queryKey: ['documents', filters],
    queryFn: () => documentsAPI.list(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Single document
export const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: () => documentsAPI.getById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Upload document - preserves all backend sophistication
export const useDocumentUpload = () => {
  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (progress: number) => void }) =>
      documentsAPI.upload(file, onProgress),
    onSuccess: (_, { file }) => {
      // Invalidate documents list to show new upload
      invalidateQueries.documents();
      invalidateQueries.metrics();

      toast.success(`${file.name} uploaded successfully and being processed`);
    },
    onError: (error: any, { file }) => {
      console.error('Upload error:', error);
      toast.error(`Failed to upload ${file.name}: ${error.message}`);
    },
  });
};

// Search documents
export const useDocumentSearch = () => {
  return useMutation({
    mutationFn: ({ query, filters }: { query: string; filters?: DocumentFilters }) =>
      documentsAPI.search(query, filters),
    onError: (error: any) => {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
    },
  });
};

// Quick search for autocomplete
export const useDocumentQuickSearch = (query: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['documents', 'quickSearch', query],
    queryFn: () => documentsAPI.quickSearch(query),
    enabled: enabled && query.length > 2,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Reprocess document (preserves 40+ GL accounts and 5-method payment detection)
export const useDocumentReprocess = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => documentsAPI.reprocess(documentId),
    onSuccess: (_, documentId) => {
      // Invalidate specific document and lists
      queryClient.invalidateQueries({ queryKey: ['documents', documentId] });
      invalidateQueries.documents();
      invalidateQueries.metrics();

      toast.success('Document reprocessing started');
    },
    onError: (error: any) => {
      console.error('Reprocess error:', error);
      toast.error('Failed to reprocess document');
    },
  });
};

// Delete document
export const useDocumentDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => documentsAPI.delete(documentId),
    onSuccess: (_, documentId) => {
      // Remove from cache and invalidate lists
      queryClient.removeQueries({ queryKey: ['documents', documentId] });
      invalidateQueries.documents();
      invalidateQueries.metrics();

      toast.success('Document deleted successfully');
    },
    onError: (error: any) => {
      console.error('Delete error:', error);
      toast.error('Failed to delete document');
    },
  });
};

// Get classification details - shows all backend sophistication
export const useDocumentClassification = (documentId: string) => {
  return useQuery({
    queryKey: ['documents', documentId, 'classification'],
    queryFn: () => documentsAPI.getClassification(documentId),
    enabled: !!documentId,
    staleTime: 10 * 60 * 1000, // 10 minutes - classification doesn't change often
  });
};

// Batch processing
export const useDocumentBatchProcess = () => {
  return useMutation({
    mutationFn: (documentIds: string[]) => documentsAPI.batchProcess(documentIds),
    onSuccess: (_, documentIds) => {
      // Invalidate all document-related queries
      invalidateQueries.documents();
      invalidateQueries.metrics();

      toast.success(`Started batch processing of ${documentIds.length} documents`);
    },
    onError: (error: any) => {
      console.error('Batch process error:', error);
      toast.error('Failed to start batch processing');
    },
  });
};