// ABOUTME: Modal component for viewing and restoring prompt version history
// ABOUTME: Integrates VersionTimeline with restore functionality and confirmation dialogs

import { useState, useEffect } from 'react'
import { X, Loader2 } from 'lucide-react'
import { toast } from 'react-toastify'
import { promptService } from '../services/promptService'
import { VersionTimeline } from './VersionTimeline'
import type { PromptResponse, PromptVersionResponse } from '../types/prompt.types'
import './PromptVersionHistory.css'

export interface PromptVersionHistoryProps {
  prompt: PromptResponse
  onClose: () => void
  onRestore: () => void
}

export const PromptVersionHistory: React.FC<PromptVersionHistoryProps> = ({
  prompt,
  onClose,
  onRestore
}) => {
  // Data state
  const [versions, setVersions] = useState<PromptVersionResponse[]>([])
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)

  // UI state
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [restoring, setRestoring] = useState(false)
  const [showRestoreConfirm, setShowRestoreConfirm] = useState(false)

  // Fetch version history on mount
  useEffect(() => {
    fetchVersionHistory()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prompt.id])

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !showRestoreConfirm && !restoring) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [showRestoreConfirm, restoring, onClose])

  // Fetch version history from API
  const fetchVersionHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await promptService.getVersionHistory(prompt.id)
      setVersions(response.versions)
    } catch (err: unknown) {
      console.error('Failed to fetch version history:', err)
      const error = err as { response?: { status?: number } }
      const message = error.response?.status === 404
        ? 'Prompt not found'
        : error.response?.status && error.response.status >= 500
        ? 'Server error. Please try again later.'
        : 'Failed to load version history'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  // Handle version selection
  const handleSelectVersion = (version: number) => {
    if (version === prompt.version) {
      // Don't allow selecting current version for restore
      setSelectedVersion(null)
      return
    }

    if (selectedVersion === version) {
      // Deselect if already selected
      setSelectedVersion(null)
    } else {
      setSelectedVersion(version)
    }
  }

  // Handle restore button click
  const handleRestoreClick = () => {
    if (selectedVersion === null) return
    setShowRestoreConfirm(true)
  }

  // Handle restore confirmation
  const handleRestoreConfirm = async () => {
    if (selectedVersion === null) return

    try {
      setRestoring(true)
      await promptService.restoreVersion(
        prompt.id,
        selectedVersion,
        `Restored version ${selectedVersion}`
      )

      toast.success(`Version ${selectedVersion} restored successfully`)
      setShowRestoreConfirm(false)
      onRestore()
    } catch (err: unknown) {
      console.error('Failed to restore version:', err)
      const error = err as { response?: { data?: { detail?: string } } }
      const message = error.response?.data?.detail || 'Failed to restore version'
      setError(message)
      toast.error(message)
    } finally {
      setRestoring(false)
    }
  }

  // Handle restore cancel
  const handleRestoreCancel = () => {
    setShowRestoreConfirm(false)
  }

  // Handle overlay click
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !showRestoreConfirm && !restoring) {
      onClose()
    }
  }

  // Handle panel click (prevent closing)
  const handlePanelClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation()
  }

  return (
    <div
      className="prompt-version-history-modal"
      onClick={handleOverlayClick}
    >
      <div className="prompt-version-history-overlay" aria-hidden="true" />

      <div
        className="prompt-version-history-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="version-history-title"
        onClick={handlePanelClick}
      >
        {/* Header */}
        <div className="version-history-header">
          <h2 id="version-history-title">
            Version History: {prompt.name}
          </h2>
          <button
            className="close-btn"
            onClick={onClose}
            aria-label="Close"
            disabled={restoring}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="version-history-body">
          {loading && (
            <div className="version-history-loading">
              <Loader2 size={32} className="spinner-icon" />
              <p>Loading version history...</p>
            </div>
          )}

          {error && !loading && (
            <div className="version-history-error">
              <div className="error-icon">⚠️</div>
              <p>{error}</p>
              <button onClick={fetchVersionHistory} className="retry-button">
                Retry
              </button>
            </div>
          )}

          {!loading && !error && versions.length === 0 && (
            <div className="version-history-empty">
              <p>No version history available</p>
            </div>
          )}

          {!loading && !error && versions.length > 0 && (
            <VersionTimeline
              versions={versions}
              currentVersion={prompt.version}
              selectedVersions={selectedVersion ? [selectedVersion] : []}
              onSelectVersion={handleSelectVersion}
            />
          )}
        </div>

        {/* Footer */}
        <div className="version-history-footer">
          <div className="footer-left">
            <span className="current-version-indicator">
              Current: v{prompt.version}
            </span>
          </div>

          <div className="footer-right">
            {selectedVersion !== null && selectedVersion !== prompt.version && (
              <button
                className="btn-primary"
                onClick={handleRestoreClick}
                disabled={restoring}
              >
                Restore Version {selectedVersion}
              </button>
            )}

            <button
              className="btn-secondary"
              onClick={onClose}
              disabled={restoring}
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Restore Confirmation Modal */}
      {showRestoreConfirm && selectedVersion !== null && (
        <div className="restore-confirm-overlay" onClick={handleRestoreCancel}>
          <div
            className="restore-confirm-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="restore-confirm-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="restore-confirm-title">Confirm Restore</h3>
            <p>
              Are you sure you want to restore version {selectedVersion}? This
              will create a new version based on the selected version's content.
            </p>

            <div className="restore-confirm-actions">
              <button
                className="btn-secondary"
                onClick={handleRestoreCancel}
                disabled={restoring}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleRestoreConfirm}
                disabled={restoring}
              >
                {restoring ? (
                  <>
                    <Loader2 size={14} className="spinner-icon" />
                    Restoring...
                  </>
                ) : (
                  'Confirm'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PromptVersionHistory
