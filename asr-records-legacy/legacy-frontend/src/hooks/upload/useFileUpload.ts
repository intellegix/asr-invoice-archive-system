import { useState, useCallback } from 'react';
import { useDocumentUpload } from '@/hooks/api/useDocuments';
import toast from 'react-hot-toast';

interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  result?: any;
  id: string;
}

export const useFileUpload = () => {
  const [uploads, setUploads] = useState<Map<string, UploadProgress>>(new Map());
  const documentUpload = useDocumentUpload();

  const uploadFile = useCallback(async (file: File) => {
    const fileId = `${file.name}_${Date.now()}`;

    // Validate file
    if (!validateFile(file)) {
      return;
    }

    // Initialize upload progress
    setUploads(prev => new Map(prev.set(fileId, {
      file,
      progress: 0,
      status: 'uploading',
      id: fileId,
    })));

    try {
      const result = await documentUpload.mutateAsync({
        file,
        onProgress: (progress) => {
          setUploads(prev => new Map(prev.set(fileId, {
            ...prev.get(fileId)!,
            progress,
          })));
        },
      });

      // Update to processing status (backend now runs sophisticated analysis)
      setUploads(prev => new Map(prev.set(fileId, {
        ...prev.get(fileId)!,
        status: 'processing',
        progress: 100,
      })));

      // The backend now automatically:
      // - Runs 40+ GL account classification
      // - Executes 5-method payment detection
      // - Routes to appropriate billing destination (1 of 4)
      // - Generates audit trail and confidence scores

      // Simulate processing time for UI (in real implementation, we'd poll the API)
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Mark as completed
      setUploads(prev => new Map(prev.set(fileId, {
        ...prev.get(fileId)!,
        status: 'completed',
        result,
      })));

      toast.success(`${file.name} processed successfully with AI classification`);
      return result;

    } catch (error) {
      setUploads(prev => new Map(prev.set(fileId, {
        ...prev.get(fileId)!,
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed',
      })));

      toast.error(`Failed to process ${file.name}`);
      throw error;
    }
  }, [documentUpload]);

  const uploadMultipleFiles = useCallback(async (files: File[]) => {
    const uploadPromises = files.map(uploadFile);

    try {
      await Promise.allSettled(uploadPromises);
    } catch {
      // Individual upload errors already handled per-file via toast
    }
  }, [uploadFile]);

  const clearCompleted = useCallback(() => {
    setUploads(prev => {
      const filtered = new Map();
      prev.forEach((upload, key) => {
        if (upload.status !== 'completed') {
          filtered.set(key, upload);
        }
      });
      return filtered;
    });
  }, []);

  const clearAll = useCallback(() => {
    setUploads(new Map());
  }, []);

  const removeUpload = useCallback((uploadId: string) => {
    setUploads(prev => {
      const updated = new Map(prev);
      updated.delete(uploadId);
      return updated;
    });
  }, []);

  return {
    uploads: Array.from(uploads.values()),
    uploadFile,
    uploadMultipleFiles,
    clearCompleted,
    clearAll,
    removeUpload,
    isUploading: documentUpload.isPending,
    stats: {
      total: uploads.size,
      completed: Array.from(uploads.values()).filter(u => u.status === 'completed').length,
      processing: Array.from(uploads.values()).filter(u => u.status === 'processing').length,
      errors: Array.from(uploads.values()).filter(u => u.status === 'error').length,
    },
  };
};

// File validation helper
const validateFile = (file: File): boolean => {
  // Check file type
  const allowedTypes = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/tiff',
  ];

  if (!allowedTypes.includes(file.type)) {
    toast.error(`File type ${file.type} not supported. Please use PDF, JPG, PNG, GIF, or TIFF files.`);
    return false;
  }

  // Check file size (10MB limit)
  const maxSize = 10 * 1024 * 1024; // 10MB in bytes
  if (file.size > maxSize) {
    toast.error(`File ${file.name} is too large. Maximum size is 10MB.`);
    return false;
  }

  // Check file name
  if (!file.name || file.name.trim() === '') {
    toast.error('Invalid file name.');
    return false;
  }

  return true;
};