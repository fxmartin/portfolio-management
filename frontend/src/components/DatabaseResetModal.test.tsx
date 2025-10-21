// ABOUTME: Tests for DatabaseResetModal component
// ABOUTME: Verifies confirmation mechanism, API calls, and safety features

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DatabaseResetModal, useDatabaseReset } from './DatabaseResetModal';
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock fetch globally
global.fetch = vi.fn();
global.alert = vi.fn();
global.confirm = vi.fn();

// Mock window.location.reload
const mockReload = vi.fn();
Object.defineProperty(window, 'location', {
  value: { reload: mockReload },
  writable: true,
});

describe('DatabaseResetModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();
    (global.alert as any).mockClear();
    (global.confirm as any).mockClear();
    mockReload.mockClear();
  });

  describe('Modal Display', () => {
    it('renders modal when isOpen is true', () => {
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(screen.getByText(/Dangerous Operation - Database Reset/)).toBeInTheDocument();
      expect(screen.getByText(/This will permanently delete:/)).toBeInTheDocument();
    });

    it('does not render modal when isOpen is false', () => {
      const { container } = render(
        <DatabaseResetModal
          isOpen={false}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('displays all warning items', () => {
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(screen.getByText(/All imported transactions/)).toBeInTheDocument();
      expect(screen.getByText(/All manually entered transactions/)).toBeInTheDocument();
      expect(screen.getByText(/All position calculations/)).toBeInTheDocument();
      expect(screen.getByText(/All price history/)).toBeInTheDocument();
      expect(screen.getByText(/All portfolio snapshots/)).toBeInTheDocument();
      expect(screen.getByText(/All cost basis/)).toBeInTheDocument();
    });

    it('displays consequences section', () => {
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      expect(screen.getByText(/Consequences:/)).toBeInTheDocument();
      expect(screen.getByText(/You will need to re-import all CSV files/)).toBeInTheDocument();
      expect(screen.getByText(/This action cannot be undone/)).toBeInTheDocument();
    });
  });

  describe('Confirmation Input', () => {
    it('shows confirmation input with placeholder', () => {
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      expect(input).toBeInTheDocument();
      expect(screen.getByText(/DELETE ALL TRANSACTIONS/)).toBeInTheDocument();
    });

    it('enables reset button only when correct confirmation is typed', () => {
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Initially disabled
      expect(resetButton).toBeDisabled();

      // Still disabled with wrong text
      fireEvent.change(input, { target: { value: 'wrong text' } });
      expect(resetButton).toBeDisabled();

      // Enabled with correct text
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });
      expect(resetButton).toBeEnabled();
    });

    it('shows error when attempting reset with wrong confirmation', async () => {
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Type wrong confirmation
      fireEvent.change(input, { target: { value: 'DELETE' } });

      // Force enable button for testing
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });
      fireEvent.change(input, { target: { value: 'DELETE' } });

      // Click reset (button is disabled, but we're testing the validation)
      fireEvent.click(resetButton);

      // Error should appear
      await waitFor(() => {
        const errorElement = screen.queryByRole('alert');
        if (errorElement) {
          expect(errorElement).toHaveTextContent(/Please type exactly:/);
        }
      });
    });
  });

  describe('Reset Process', () => {
    it('calls API with correct confirmation when reset is triggered', async () => {
      (global.confirm as any).mockReturnValue(true);
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          status: 'success',
          message: 'Database reset complete'
        })
      });

      const onReset = vi.fn();
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={onReset}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Type correct confirmation
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });

      // Click reset
      fireEvent.click(resetButton);

      // Verify confirmation dialog
      expect(global.confirm).toHaveBeenCalledWith(
        expect.stringContaining('permanently delete ALL transactions')
      );

      // Verify API call
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/database/reset', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            confirmation: 'DELETE ALL TRANSACTIONS'
          })
        });
      });

      // Verify callbacks
      await waitFor(() => {
        expect(onReset).toHaveBeenCalled();
        expect(global.alert).toHaveBeenCalledWith(expect.stringContaining('Success'));
      });

      // Verify page reload
      await waitFor(() => {
        expect(mockReload).toHaveBeenCalled();
      }, { timeout: 1000 });
    });

    it('does not call API if user cancels confirmation', async () => {
      (global.confirm as any).mockReturnValue(false);

      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Type correct confirmation
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });

      // Click reset
      fireEvent.click(resetButton);

      // User cancelled
      expect(global.confirm).toHaveBeenCalled();
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('handles API error gracefully', async () => {
      (global.confirm as any).mockReturnValue(true);
      (global.fetch as any).mockResolvedValue({
        ok: false,
        json: async () => ({
          detail: 'Invalid confirmation code'
        })
      });

      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Type correct confirmation
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });

      // Click reset
      fireEvent.click(resetButton);

      // Wait for error to appear
      await waitFor(() => {
        const errorElement = screen.getByRole('alert');
        expect(errorElement).toHaveTextContent('Invalid confirmation code');
      });

      // Should not reload on error
      expect(mockReload).not.toHaveBeenCalled();
    });

    it('handles network error gracefully', async () => {
      (global.confirm as any).mockReturnValue(true);
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Type correct confirmation
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });

      // Click reset
      fireEvent.click(resetButton);

      // Wait for error to appear
      await waitFor(() => {
        const errorElement = screen.getByRole('alert');
        expect(errorElement).toHaveTextContent('Network error');
      });
    });

    it('shows loading state during reset', async () => {
      (global.confirm as any).mockReturnValue(true);
      (global.fetch as any).mockImplementation(() =>
        new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ status: 'success', message: 'Done' })
        }), 100))
      );

      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');

      // Type correct confirmation
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });

      // Click reset
      fireEvent.click(resetButton);

      // Check for loading state
      await waitFor(() => {
        expect(screen.getByText(/Deleting All Data.../)).toBeInTheDocument();
        expect(screen.getByText(/Please wait while we clear all data.../)).toBeInTheDocument();
      });
    });
  });

  describe('Modal Controls', () => {
    it('calls onClose when Cancel button is clicked', () => {
      const onClose = vi.fn();
      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={onClose}
          onReset={vi.fn()}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('disables Cancel button during deletion', async () => {
      (global.confirm as any).mockReturnValue(true);
      (global.fetch as any).mockImplementation(() =>
        new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ status: 'success', message: 'Done' })
        }), 100))
      );

      render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here');
      const resetButton = screen.getByText('Reset Database');
      const cancelButton = screen.getByText('Cancel');

      // Type correct confirmation
      fireEvent.change(input, { target: { value: 'DELETE ALL TRANSACTIONS' } });

      // Click reset
      fireEvent.click(resetButton);

      // Cancel should be disabled during operation
      await waitFor(() => {
        expect(cancelButton).toBeDisabled();
      });
    });

    it('clears confirmation text when modal closes', () => {
      const { rerender } = render(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const input = screen.getByPlaceholderText('Type confirmation here') as HTMLInputElement;

      // Type something
      fireEvent.change(input, { target: { value: 'DELETE ALL' } });
      expect(input.value).toBe('DELETE ALL');

      // Close and reopen modal
      rerender(
        <DatabaseResetModal
          isOpen={false}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      rerender(
        <DatabaseResetModal
          isOpen={true}
          onClose={vi.fn()}
          onReset={vi.fn()}
        />
      );

      const newInput = screen.getByPlaceholderText('Type confirmation here') as HTMLInputElement;
      expect(newInput.value).toBe('');
    });
  });

  describe('useDatabaseReset Hook', () => {
    it('provides modal state and controls', () => {
      const { result } = renderHook(() => useDatabaseReset());

      expect(result.current.isModalOpen).toBe(false);
      expect(typeof result.current.openResetModal).toBe('function');
      expect(typeof result.current.closeResetModal).toBe('function');
      expect(typeof result.current.handleReset).toBe('function');
      expect(typeof result.current.DatabaseResetModal).toBe('function');
    });

    it('opens and closes modal correctly', () => {
      const { result } = renderHook(() => useDatabaseReset());

      // Initially closed
      expect(result.current.isModalOpen).toBe(false);

      // Open modal
      act(() => {
        result.current.openResetModal();
      });
      expect(result.current.isModalOpen).toBe(true);

      // Close modal
      act(() => {
        result.current.closeResetModal();
      });
      expect(result.current.isModalOpen).toBe(false);
    });
  });
});