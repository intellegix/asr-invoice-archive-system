import React, { useCallback } from 'react';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { useFileUpload } from '@/hooks/upload/useFileUpload';
import { useSystemStatus, useSystemInfo } from '@/hooks/api/useSystemStatus';
import { useDashboardMetrics } from '@/hooks/api/useDashboard';

export const Upload: React.FC = () => {
  const { uploads, uploadFile, uploadMultipleFiles, clearCompleted, stats } = useFileUpload();
  const { data: systemStatus } = useSystemStatus();
  const { data: systemInfo } = useSystemInfo();
  const { data: metrics } = useDashboardMetrics();

  const glAccountCount = systemInfo?.capabilities?.gl_accounts?.total ?? 79;
  const isOnline = systemStatus?.status === 'operational';
  const accuracy = metrics?.classificationAccuracy ?? metrics?.paymentAccuracy ?? 0;
  const manualReviewRate = metrics?.manualReviewRate ?? 0;
  const avgProcessingTime = metrics?.averageProcessingTime;

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 1) {
      uploadFile(acceptedFiles[0]);
    } else if (acceptedFiles.length > 1) {
      uploadMultipleFiles(acceptedFiles);
    }
  }, [uploadFile, uploadMultipleFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.tiff']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Documents</h1>
        <p className="mt-2 text-gray-600">
          Upload documents for automated processing and classification using our AI-powered system.
        </p>
      </div>

      {/* Upload Zone - Real functionality */}
      <div className="card">
        <div
          {...getRootProps()}
          className={`upload-zone cursor-pointer transition-colors ${
            isDragActive ? 'bg-primary-50 border-primary-300' : ''
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-center">
            <UploadIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive ? 'Drop files here' : 'Drop files here to upload'}
            </h3>
            <p className="text-gray-500 mb-4">
              Or click to browse and select files from your computer
            </p>
            <div className="flex justify-center space-x-4 text-sm text-gray-500">
              <span>• PDF, PNG, JPG supported</span>
              <span>• Up to 10MB per file</span>
              <span>• Batch upload available</span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {uploads.length > 0 && (
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3 className="card-title">Upload Progress</h3>
            <div className="flex items-center space-x-4 text-sm">
              <span className="text-gray-600">
                {stats.completed}/{stats.total} completed
              </span>
              {stats.completed > 0 && (
                <button
                  onClick={clearCompleted}
                  className="text-primary-600 hover:text-primary-700"
                >
                  Clear completed
                </button>
              )}
            </div>
          </div>
          <div className="space-y-4">
            {uploads.map((upload) => (
              <div key={upload.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(upload.status)}
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {upload.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(upload.file.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      {upload.status === 'uploading' ? 'Uploading...' :
                       upload.status === 'processing' ? 'Processing with AI...' :
                       upload.status === 'completed' ? 'Completed' :
                       upload.status === 'error' ? 'Error' : upload.status}
                    </p>
                    {upload.progress > 0 && upload.status !== 'completed' && (
                      <p className="text-xs text-gray-500">{upload.progress}%</p>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      upload.status === 'error' ? 'bg-red-500' :
                      upload.status === 'completed' ? 'bg-green-500' :
                      'bg-blue-500'
                    }`}
                    style={{
                      width: upload.status === 'completed' ? '100%' :
                             upload.status === 'processing' ? '100%' :
                             `${upload.progress}%`
                    }}
                  />
                </div>

                {/* Error message */}
                {upload.error && (
                  <p className="mt-2 text-sm text-red-600">{upload.error}</p>
                )}

                {/* Success result preview */}
                {upload.result && (
                  <div className="mt-3 p-3 bg-green-50 rounded-md">
                    <p className="text-sm text-green-800">
                      ✓ Document processed successfully with AI classification
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <FileText className="mx-auto h-8 w-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">
            {glAccountCount} GL Account Classifications
          </h3>
          <p className="text-sm text-gray-600">
            Automated mapping to QuickBooks accounts with keyword matching and machine learning.
          </p>
        </div>

        <div className="card text-center">
          <CheckCircle className="mx-auto h-8 w-8 text-green-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">
            5-Method Payment Detection
          </h3>
          <p className="text-sm text-gray-600">
            Claude AI, regex patterns, keywords, amount analysis, and date correlation for accuracy.
          </p>
        </div>

        <div className="card text-center">
          <div className="mx-auto h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center mb-3">
            <span className="text-purple-600 font-bold text-sm">4</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">
            Smart Billing Routes
          </h3>
          <p className="text-sm text-gray-600">
            Automatic routing to Open/Closed Payable/Receivable destinations with enhanced logic.
          </p>
        </div>
      </div>

      {/* Status Panel */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">System Status</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
              {isOnline ? 'Online' : 'Offline'}
            </div>
            <div className="text-sm text-gray-500">Processing System</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {avgProcessingTime != null ? `${avgProcessingTime.toFixed(1)}s` : '--'}
            </div>
            <div className="text-sm text-gray-500">Average Processing</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{accuracy}%</div>
            <div className="text-sm text-gray-500">Classification Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{manualReviewRate}%</div>
            <div className="text-sm text-gray-500">Manual Review Rate</div>
          </div>
        </div>
      </div>
    </div>
  );
};