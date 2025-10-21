// ABOUTME: Unit tests for TransactionImport component
// ABOUTME: Tests file selection, drag-drop, validation, and upload functionality

import { describe, it, expect, beforeEach, vi, Mock } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TransactionImport from './TransactionImport';
import axios from 'axios';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

describe('TransactionImport Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('File Type Detection', () => {
    it('should detect metals file type correctly', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'account-statement_2024-01-01_2024-12-31_en_123456.csv', {
        type: 'text/csv'
      });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      // Check if METALS badge appears
      expect(screen.getByText('METALS')).toBeInTheDocument();
    });

    it('should detect stocks file type correctly', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', {
        type: 'text/csv'
      });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      expect(screen.getByText('STOCKS')).toBeInTheDocument();
    });

    it('should detect crypto file type correctly', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'Koinly Transactions.csv', {
        type: 'text/csv'
      });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      expect(screen.getByText('CRYPTO')).toBeInTheDocument();
    });

    it('should mark unknown file types as UNKNOWN', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'random_data.csv', {
        type: 'text/csv'
      });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
    });
  });

  describe('Drag and Drop', () => {
    it('should handle drag over events', () => {
      const { container } = render(<TransactionImport />);
      const dropZone = container.querySelector('.drop-zone') as HTMLElement;

      fireEvent.dragOver(dropZone);
      expect(dropZone).toHaveClass('dragging');
    });

    it('should handle drag leave events', () => {
      const { container } = render(<TransactionImport />);
      const dropZone = container.querySelector('.drop-zone') as HTMLElement;

      fireEvent.dragOver(dropZone);
      expect(dropZone).toHaveClass('dragging');

      fireEvent.dragLeave(dropZone);
      expect(dropZone).not.toHaveClass('dragging');
    });

    it('should handle file drop', () => {
      const { container } = render(<TransactionImport />);
      const dropZone = container.querySelector('.drop-zone') as HTMLElement;

      const file = new File(['content'], 'Koinly Transactions.csv', {
        type: 'text/csv'
      });

      const dataTransfer = {
        files: [file],
        items: [
          {
            kind: 'file',
            type: 'text/csv',
            getAsFile: () => file
          }
        ],
        types: ['Files']
      };

      fireEvent.drop(dropZone, { dataTransfer });

      expect(screen.getByText('Koinly Transactions.csv')).toBeInTheDocument();
      expect(screen.getByText('CRYPTO')).toBeInTheDocument();
    });
  });

  describe('File Management', () => {
    it('should display selected files in a list', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const files = [
        new File(['content1'], 'account-statement_2024-01-01_2024-12-31_en_123456.csv', { type: 'text/csv' }),
        new File(['content2'], 'B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', { type: 'text/csv' }),
        new File(['content3'], 'Koinly Transactions.csv', { type: 'text/csv' })
      ];

      Object.defineProperty(input, 'files', {
        value: files,
        writable: false
      });

      fireEvent.change(input);

      expect(screen.getByText('account-statement_2024-01-01_2024-12-31_en_123456.csv')).toBeInTheDocument();
      expect(screen.getByText('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv')).toBeInTheDocument();
      expect(screen.getByText('Koinly Transactions.csv')).toBeInTheDocument();
    });

    it('should allow removing files from the list', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'test.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      expect(screen.getByText('test.csv')).toBeInTheDocument();

      const removeBtn = screen.getByText('Remove');
      fireEvent.click(removeBtn);

      expect(screen.queryByText('test.csv')).not.toBeInTheDocument();
    });

    it('should display file size', () => {
      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      // Create a file with specific size (1024 bytes = 1KB)
      const content = new Array(1024).fill('a').join('');
      const file = new File([content], 'test.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
    });
  });

  describe('File Upload', () => {
    it('should upload files when upload button is clicked', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          summary: {
            total_files: 1,
            successful: 1,
            failed: 0,
            total_transactions: 10
          },
          files: [
            {
              filename: 'test.csv',
              status: 'success',
              file_type: 'CRYPTO',
              errors: [],
              transactions_count: 10
            }
          ]
        }
      });

      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'Koinly Transactions.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      const uploadBtn = screen.getByText('Upload Files');
      fireEvent.click(uploadBtn);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/import/upload',
          expect.any(FormData),
          expect.objectContaining({
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
        );
      });
    });

    it('should show upload progress', async () => {
      let progressCallback: any;

      mockedAxios.post.mockImplementation((url, data, config) => {
        progressCallback = config?.onUploadProgress;

        // Simulate progress
        setTimeout(() => {
          progressCallback?.({ loaded: 50, total: 100 });
        }, 10);

        return Promise.resolve({
          data: {
            summary: { total_files: 1, successful: 1, failed: 0, total_transactions: 0 },
            files: [{ filename: 'test.csv', status: 'success', file_type: 'CRYPTO', errors: [], transactions_count: 0 }]
          }
        });
      });

      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'test.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);
      fireEvent.click(screen.getByText('Upload Files'));

      await waitFor(() => {
        const progressBar = container.querySelector('.progress-fill');
        expect(progressBar).toBeInTheDocument();
      });
    });

    it('should handle upload errors', async () => {
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          data: {
            detail: 'Server error'
          }
        }
      });

      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'test.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);
      fireEvent.click(screen.getByText('Upload Files'));

      await waitFor(() => {
        // Check for the mapped error message - appears in both toast and file error
        expect(screen.getByText('Server error')).toBeInTheDocument();
        const errorMessages = screen.getAllByText('The server is experiencing issues. Please try again in a few moments');
        expect(errorMessages.length).toBeGreaterThan(0);
      });
    });

    it('should display transaction count on successful upload', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          summary: {
            total_files: 1,
            successful: 1,
            failed: 0,
            total_transactions: 25
          },
          files: [
            {
              filename: 'test.csv',
              status: 'success',
              file_type: 'CRYPTO',
              errors: [],
              transactions_count: 25
            }
          ]
        }
      });

      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'Koinly Transactions.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);
      fireEvent.click(screen.getByText('Upload Files'));

      await waitFor(() => {
        expect(screen.getByText('25 transactions')).toBeInTheDocument();
      });
    });
  });

  describe('UI Elements', () => {
    it('should display supported file formats information', () => {
      render(<TransactionImport />);

      expect(screen.getByText('Supported File Formats')).toBeInTheDocument();
      expect(screen.getByText(/Metals:/)).toBeInTheDocument();
      expect(screen.getByText(/Stocks:/)).toBeInTheDocument();
      expect(screen.getByText(/Crypto:/)).toBeInTheDocument();
    });

    it('should disable upload button when no pending files', () => {
      render(<TransactionImport />);

      // Initially no files selected, so no upload button should be shown
      expect(screen.queryByText('Upload Files')).not.toBeInTheDocument();
    });

    it('should show clear all button after upload', async () => {
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          summary: { total_files: 1, successful: 1, failed: 0, total_transactions: 0 },
          files: [{ filename: 'test.csv', status: 'success', file_type: 'CRYPTO', errors: [], transactions_count: 0 }]
        }
      });

      const { container } = render(<TransactionImport />);
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['content'], 'test.csv', { type: 'text/csv' });

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);
      fireEvent.click(screen.getByText('Upload Files'));

      await waitFor(() => {
        expect(screen.getByText('Clear All')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Clear All'));
      expect(screen.queryByText('test.csv')).not.toBeInTheDocument();
    });
  });
});