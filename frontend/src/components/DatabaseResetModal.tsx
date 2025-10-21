// ABOUTME: Database reset modal component with safety confirmations
// ABOUTME: Requires explicit user confirmation before clearing all data

import React, { useState } from 'react';
import { Modal } from './Modal';
import './DatabaseResetModal.css';

interface DatabaseResetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReset: () => void;
}

const CONFIRMATION_TEXT = 'DELETE_ALL_TRANSACTIONS';

export const DatabaseResetModal: React.FC<DatabaseResetModalProps> = ({
  isOpen,
  onClose,
  onReset
}) => {
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReset = async () => {
    // Clear any previous errors
    setError(null);

    // Validate confirmation text
    if (confirmText !== CONFIRMATION_TEXT) {
      setError(`Please type exactly: ${CONFIRMATION_TEXT}`);
      return;
    }

    // Show final confirmation
    const finalConfirmation = window.confirm(
      'This will permanently delete ALL transactions and portfolio data. This action cannot be undone. Are you absolutely sure?'
    );

    if (!finalConfirmation) {
      return;
    }

    setIsDeleting(true);

    try {
      // Call the API to reset the database
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/database/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          confirmation: CONFIRMATION_TEXT
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reset database');
      }

      const result = await response.json();

      // Success - notify parent and close modal
      alert(`Success: ${result.message}`);
      setConfirmText('');
      onReset();
      onClose();

      // Reload the page to show empty state
      setTimeout(() => {
        window.location.reload();
      }, 500);

    } catch (error) {
      console.error('Database reset failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to reset database');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    if (isDeleting) return; // Don't allow closing while operation is in progress
    setConfirmText('');
    setError(null);
    onClose();
  };

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (!isOpen) {
      setConfirmText('');
      setError(null);
    }
  }, [isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="⚠️ Database Reset"
      className="database-reset-modal"
      closeOnBackdropClick={!isDeleting}
      closeOnEscape={!isDeleting}
      showCloseButton={!isDeleting}
    >
      <div className="reset-warning">
        <h3>⚠️ This will permanently delete all data</h3>
        <p className="warning-summary">
          All transactions, positions, price history, and calculations will be removed.
          You'll need to re-import CSV files. <strong>This cannot be undone.</strong>
        </p>
      </div>

      <div className="confirmation-section">
        <p className="confirmation-prompt">
          To confirm this action, type <code>{CONFIRMATION_TEXT}</code> below:
        </p>
        <input
          type="text"
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
          placeholder="Type confirmation here"
          className={`confirmation-input ${error ? 'error' : ''}`}
          disabled={isDeleting}
          autoComplete="off"
          spellCheck={false}
        />
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}
      </div>

      <div className="modal-actions">
        <button
          type="button"
          onClick={handleClose}
          className="btn btn-cancel"
          disabled={isDeleting}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleReset}
          disabled={isDeleting || confirmText !== CONFIRMATION_TEXT}
          className="btn btn-danger"
        >
          {isDeleting ? (
            <>
              <span className="spinner"></span>
              Deleting All Data...
            </>
          ) : (
            'Reset Database'
          )}
        </button>
      </div>

      {isDeleting && (
        <div className="deletion-progress">
          <div className="progress-bar">
            <div className="progress-bar-fill"></div>
          </div>
          <p>Please wait while we clear all data...</p>
        </div>
      )}
    </Modal>
  );
};

// Hook to manage the database reset modal
export const useDatabaseReset = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openResetModal = () => setIsModalOpen(true);
  const closeResetModal = () => setIsModalOpen(false);

  const handleReset = () => {
    console.log('Database reset completed');
    // Additional logic can be added here if needed
  };

  return {
    isModalOpen,
    openResetModal,
    closeResetModal,
    handleReset,
    DatabaseResetModal: (props: Partial<DatabaseResetModalProps>) => (
      <DatabaseResetModal
        isOpen={isModalOpen}
        onClose={closeResetModal}
        onReset={handleReset}
        {...props}
      />
    )
  };
};