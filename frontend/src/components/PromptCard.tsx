// ABOUTME: Individual prompt card component showing metadata and actions
// ABOUTME: Displays name, category, preview, version, and action buttons

import { Edit2, History, Trash2 } from 'lucide-react'
import type { PromptResponse } from '../types/prompt.types'
import './PromptCard.css'

export interface PromptCardProps {
  prompt: PromptResponse
  onEdit: () => void
  onDelete: () => void
  onViewHistory: () => void
}

export const PromptCard: React.FC<PromptCardProps> = ({
  prompt,
  onEdit,
  onDelete,
  onViewHistory
}) => {
  // Truncate text to max length
  const truncateText = (text: string, maxLength: number = 150): string => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  // Format relative time
  const formatRelativeTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      return date.toLocaleDateString()
    } catch {
      return 'Unknown'
    }
  }

  const isLongText = prompt.prompt_text.length > 150

  return (
    <div className="prompt-card">
      <div className="prompt-card-header">
        <h3 className="prompt-name">{prompt.name}</h3>
        <span className={`prompt-category badge-${prompt.category}`}>
          {prompt.category}
        </span>
      </div>

      <div className="prompt-preview">
        <p>{truncateText(prompt.prompt_text, 150)}</p>
        {isLongText && (
          <span className="char-count">
            ({prompt.prompt_text.length} characters)
          </span>
        )}
      </div>

      <div className="prompt-metadata">
        <span className="prompt-version">v{prompt.version}</span>
        <span className="prompt-updated">
          Updated {formatRelativeTime(prompt.updated_at)}
        </span>
        {!prompt.is_active && (
          <span className="prompt-inactive">Inactive</span>
        )}
      </div>

      <div className="prompt-actions">
        <button
          className="prompt-action-btn edit"
          onClick={onEdit}
          title="Edit Prompt"
          aria-label="Edit Prompt"
        >
          <Edit2 size={16} />
          Edit
        </button>
        <button
          className="prompt-action-btn history"
          onClick={onViewHistory}
          title="View History"
          aria-label="View History"
        >
          <History size={16} />
          History
        </button>
        <button
          className="prompt-action-btn delete"
          onClick={onDelete}
          title="Delete Prompt"
          aria-label="Delete Prompt"
        >
          <Trash2 size={16} />
          Delete
        </button>
      </div>
    </div>
  )
}

export default PromptCard
