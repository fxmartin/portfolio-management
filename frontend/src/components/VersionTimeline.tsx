// ABOUTME: Timeline component displaying prompt version history
// ABOUTME: Shows versions chronologically with metadata, selection, and current indicator

import type { PromptVersionResponse } from '../types/prompt.types'
import './VersionTimeline.css'

export interface VersionTimelineProps {
  versions: PromptVersionResponse[]
  currentVersion: number
  selectedVersions: number[]
  onSelectVersion: (version: number) => void
}

export const VersionTimeline: React.FC<VersionTimelineProps> = ({
  versions,
  currentVersion,
  selectedVersions,
  onSelectVersion
}) => {
  // Format date for display
  const formatDate = (timestamp: string): string => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      // Relative time for recent changes
      if (diffMins < 1) return 'just now'
      if (diffMins < 60) return `${diffMins} minutes ago`
      if (diffHours < 24) return `${diffHours} hours ago`
      if (diffDays < 7) return `${diffDays} days ago`

      // Absolute date for older changes
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Unknown date'
    }
  }

  // Truncate prompt text preview
  const truncateText = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  // Handle version selection
  const handleVersionClick = (version: number) => {
    onSelectVersion(version)
  }

  // Handle keyboard navigation
  const handleKeyPress = (e: React.KeyboardEvent, version: number) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onSelectVersion(version)
    }
  }

  // Empty state
  if (versions.length === 0) {
    return (
      <div className="version-timeline-empty">
        <p>No version history available</p>
      </div>
    )
  }

  return (
    <div className="version-timeline" role="list" aria-label="Version history timeline">
      {versions.map((version) => {
        const isCurrent = version.version === currentVersion
        const isSelected = selectedVersions.includes(version.version)

        return (
          <div
            key={version.id}
            className={`version-card ${isCurrent ? 'current' : ''} ${isSelected ? 'selected' : ''}`}
            onClick={() => handleVersionClick(version.version)}
            onKeyDown={(e) => handleKeyPress(e, version.version)}
            role="listitem"
            tabIndex={0}
            aria-selected={isSelected}
            aria-current={isCurrent ? 'true' : undefined}
          >
            <div className="version-header">
              <div className="version-title">
                <h4>Version {version.version}</h4>
                {isCurrent && <span className="current-badge">Current</span>}
              </div>
              <span className="version-date">{formatDate(version.changed_at)}</span>
            </div>

            <div className="version-preview">
              <p>{truncateText(version.prompt_text, 100)}</p>
            </div>

            <div className="version-metadata">
              <div className="metadata-row">
                <span className="metadata-label">Changed by:</span>
                <span className="metadata-value">
                  {version.changed_by || 'Unknown'}
                </span>
              </div>
              {version.change_reason && (
                <div className="metadata-row">
                  <span className="metadata-label">Reason:</span>
                  <span className="metadata-value">{version.change_reason}</span>
                </div>
              )}
              {!version.change_reason && version.version === 1 && (
                <div className="metadata-row">
                  <span className="metadata-label">Reason:</span>
                  <span className="metadata-value">Initial version</span>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default VersionTimeline
