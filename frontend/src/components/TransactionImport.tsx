// ABOUTME: Multi-file CSV upload component with drag-and-drop support
// ABOUTME: Automatically detects file types and displays upload progress

import React, { useState, useRef, DragEvent } from 'react';
import axios from 'axios';
import { usePortfolioRefresh } from '../contexts/PortfolioRefreshContext';
import './TransactionImport.css';
import ProgressBar from './ProgressBar';
import Toast from './Toast';
import useToast from '../hooks/useToast';
import { getErrorMessage } from '../utils/errorMessages';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface FileInfo {
  file: File;
  type: 'METALS' | 'STOCKS' | 'CRYPTO' | 'UNKNOWN';
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  transactionCount?: number;
}

interface UploadResult {
  filename: string;
  status: string;
  file_type: string | null;
  errors: string[];
  transactions_count: number;
  message?: string;
}

const TransactionImport: React.FC = () => {
  const { triggerRefresh } = usePortfolioRefresh();
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toasts, showSuccess, showError, showWarning, showInfo, dismissToast } = useToast();

  // Detect file type based on filename
  const detectFileType = (filename: string): FileInfo['type'] => {
    // Metals: account-statement_*
    if (filename.startsWith('account-statement_')) {
      return 'METALS';
    }

    // Stocks: UUID pattern
    const uuidPattern = /^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\.csv$/i;
    if (uuidPattern.test(filename)) {
      return 'STOCKS';
    }

    // Crypto: Koinly files
    if (filename.toLowerCase().includes('koinly')) {
      return 'CRYPTO';
    }

    return 'UNKNOWN';
  };

  // Handle file selection
  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    const validFiles: FileInfo[] = [];
    const invalidFiles: string[] = [];

    Array.from(selectedFiles).forEach(file => {
      // Check if CSV file
      if (!file.name.toLowerCase().endsWith('.csv')) {
        invalidFiles.push(file.name);
        return;
      }

      // Check file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        showError(`File too large: ${file.name}`, 'Maximum file size is 10MB');
        return;
      }

      const fileType = detectFileType(file.name);
      if (fileType === 'UNKNOWN') {
        showWarning(`Unknown file format: ${file.name}`, 'File will be processed but may not be recognized');
      }

      validFiles.push({
        file,
        type: fileType,
        status: 'pending',
        progress: 0
      });
    });

    if (invalidFiles.length > 0) {
      showError('Invalid files skipped', `Only CSV files are supported: ${invalidFiles.join(', ')}`);
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
      showSuccess(`${validFiles.length} file(s) added`, 'Ready for upload');
    }
  };

  // Handle drag and drop
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = e.dataTransfer.files;
    handleFileSelect(droppedFiles);
  };

  // Remove file from list
  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Upload files with retry logic
  const uploadFiles = async (retryCount = 0) => {
    if (files.length === 0) return;

    const pendingFiles = files.filter(f => f.status === 'pending' || (retryCount > 0 && f.status === 'error'));
    if (pendingFiles.length === 0) {
      showWarning('No files to upload', 'All files have already been processed');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    pendingFiles.forEach(fileInfo => {
      formData.append('files', fileInfo.file);
    });

    // Update pending files to uploading status
    setFiles(prev => prev.map(f =>
      pendingFiles.some(pf => pf.file.name === f.file.name)
        ? { ...f, status: 'uploading', progress: 0 }
        : f
    ));

    try {
      showInfo('Uploading files...', `Processing ${pendingFiles.length} file(s)`);

      // Debug logging
      console.log('Starting upload with files:', pendingFiles.map(f => f.file.name));

      const response = await axios.post(`${API_URL}/api/import/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: any) => {
          // Debug logging
          console.log('Upload progress:', progressEvent.loaded, '/', progressEvent.total);

          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;

          setUploadProgress(progress);

          // Update progress for uploading files
          setFiles(prev => prev.map(f => ({
            ...f,
            progress: f.status === 'uploading' ? progress : f.progress
          })));
        },
        timeout: 30000 // Add 30 second timeout
      });

      // Process results
      console.log('Upload response:', response.data);
      const results = response.data.files as UploadResult[];
      let successCount = 0;
      let errorCount = 0;

      setFiles(prev => prev.map((fileInfo) => {
        const matchingFile = pendingFiles.find(pf => pf.file.name === fileInfo.file.name);
        if (matchingFile) {
          const resultIndex = pendingFiles.indexOf(matchingFile);
          const result = results[resultIndex];

          if (result) {
            if (result.status === 'success') {
              successCount++;
            } else {
              errorCount++;
            }

            return {
              ...fileInfo,
              status: result.status === 'success' ? 'success' : 'error',
              progress: 100,
              error: result.errors.join(', '),
              transactionCount: result.transactions_count
            };
          }
        }
        return fileInfo;
      }));

      // Show summary notifications
      if (successCount > 0) {
        showSuccess(
          `Successfully uploaded ${successCount} file(s)`,
          `${results.reduce((sum, r) => sum + r.transactions_count, 0)} transactions imported`
        );

        // Trigger portfolio refresh to update OpenPositionsCard and HoldingsTable
        console.log('[TransactionImport] CSV import successful, triggering portfolio refresh');
        triggerRefresh();
      }

      if (errorCount > 0) {
        showError(
          `${errorCount} file(s) failed to upload`,
          retryCount < 2 ? 'You can retry the failed uploads' : 'Please check the file formats'
        );
      }

    } catch (error: any) {
      console.error('Upload failed:', error);

      const { title, message } = getErrorMessage(error);
      showError(title, message);

      // Update files with error status
      setFiles(prev => prev.map(f =>
        f.status === 'uploading'
          ? { ...f, status: 'error', error: message }
          : f
      ));

      // Offer retry for network errors
      if (retryCount < 2 && (error.code === 'ECONNABORTED' || !error.response)) {
        setTimeout(() => {
          showWarning('Network error detected', 'Would you like to retry the upload?');
          // Add retry button instead of confirm dialog
          setFiles(prev => prev.map(f =>
            f.status === 'error'
              ? { ...f, status: 'pending' }  // Reset to pending for retry
              : f
          ));
        }, 1000);
      }
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // Get type badge color
  const getTypeBadgeClass = (type: FileInfo['type']) => {
    switch (type) {
      case 'METALS':
        return 'badge-metals';
      case 'STOCKS':
        return 'badge-stocks';
      case 'CRYPTO':
        return 'badge-crypto';
      default:
        return 'badge-unknown';
    }
  };

  // Get status icon
  const getStatusIcon = (status: FileInfo['status']) => {
    switch (status) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'uploading':
        return '⟳';
      default:
        return '•';
    }
  };

  return (
    <div className="transaction-import">
      {/* Toast Notifications */}
      <Toast toasts={toasts} onDismiss={dismissToast} />

      <h2>Import Transactions</h2>
      <p className="import-description">
        Upload your Revolut (metals & stocks) and Koinly (crypto) CSV files
      </p>

      {/* Overall Upload Progress */}
      {isUploading && (
        <ProgressBar
          progress={uploadProgress}
          label="Uploading files..."
          color="primary"
          size="medium"
        />
      )}

      {/* Drop Zone */}
      <div
        className={`drop-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        aria-label="Upload CSV files. Drag and drop or press Enter to browse"
        aria-describedby="supported-formats"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          multiple
          onChange={(e) => handleFileSelect(e.target.files)}
          style={{ display: 'none' }}
          aria-hidden="true"
        />
        <div className="drop-zone-content">
          <div className="upload-icon" aria-hidden="true">📁</div>
          <p>Drag & drop your CSV files here or click to browse</p>
          <p className="file-types" id="supported-formats">
            Supports: Revolut Metals • Revolut Stocks • Koinly Crypto
          </p>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="file-list">
          <h3>Selected Files</h3>
          {files.map((fileInfo, index) => (
            <div key={index} className={`file-item ${fileInfo.status}`}>
              <div className="file-info">
                <span className="file-name">{fileInfo.file.name}</span>
                <span className={`file-type-badge ${getTypeBadgeClass(fileInfo.type)}`}>
                  {fileInfo.type}
                </span>
                <span className="file-size">
                  {(fileInfo.file.size / 1024).toFixed(1)} KB
                </span>
              </div>

              {/* Progress Bar */}
              {fileInfo.status === 'uploading' && (
                <ProgressBar
                  progress={fileInfo.progress}
                  size="small"
                  color="primary"
                  showPercentage={false}
                />
              )}

              {/* Status */}
              <div className="file-status">
                <span className={`status-icon ${fileInfo.status}`}>
                  {getStatusIcon(fileInfo.status)}
                </span>
                {fileInfo.status === 'success' && fileInfo.transactionCount !== undefined && (
                  <span className="transaction-count">
                    {fileInfo.transactionCount} transactions
                  </span>
                )}
                {fileInfo.status === 'error' && fileInfo.error && (
                  <span className="error-message">{fileInfo.error}</span>
                )}
                {fileInfo.status === 'pending' && (
                  <button
                    className="remove-btn"
                    onClick={() => removeFile(index)}
                    disabled={isUploading}
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}

          {/* Action Buttons */}
          <div className="action-buttons">
            <button
              className="upload-btn"
              onClick={() => uploadFiles(0)}
              disabled={isUploading || files.every(f => f.status !== 'pending')}
              aria-label={isUploading ? 'Files are being uploaded' : 'Start uploading selected files'}
            >
              {isUploading ? 'Uploading...' : 'Upload Files'}
            </button>
            {!isUploading && files.some(f => f.status === 'error') && (
              <button
                className="retry-btn"
                onClick={() => uploadFiles(1)}
                aria-label="Retry failed uploads"
              >
                Retry Failed
              </button>
            )}
            {!isUploading && files.length > 0 && (
              <button
                className="clear-btn"
                onClick={() => setFiles([])}
                aria-label="Clear all files from the list"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      )}

      {/* Supported Formats Info */}
      <div className="format-info">
        <h4>Supported File Formats</h4>
        <ul>
          <li>
            <strong>Metals:</strong> account-statement_YYYY-MM-DD_*.csv (Revolut)
          </li>
          <li>
            <strong>Stocks:</strong> [UUID].csv (Revolut stocks export)
          </li>
          <li>
            <strong>Crypto:</strong> Koinly Transactions.csv (Koinly tax export)
          </li>
        </ul>
      </div>
    </div>
  );
};

export default TransactionImport;