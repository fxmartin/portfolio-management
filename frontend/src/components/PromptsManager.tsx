// ABOUTME: Container component for prompt management within Settings
// ABOUTME: Manages state, API calls, and routing between list/edit/history views

import { useState, useEffect, useCallback } from 'react'
import { toast } from 'react-toastify'
import { promptService } from '../services/promptService'
import { PromptsList } from './PromptsList'
import { PromptEditor } from './PromptEditor'
import { PromptVersionHistory } from './PromptVersionHistory'
import type { PromptResponse, PromptCreate, PromptUpdate } from '../types/prompt.types'
import './PromptsManager.css'

type View = 'list' | 'edit' | 'history'

export const PromptsManager: React.FC = () => {
  // Data state
  const [prompts, setPrompts] = useState<PromptResponse[]>([])
  const [selectedPrompt, setSelectedPrompt] = useState<PromptResponse | null>(null)

  // UI state
  const [view, setView] = useState<View>('list')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch prompts from API
  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await promptService.listPrompts(undefined, true, 0, 100)
      setPrompts(response.prompts)
    } catch (err: any) {
      console.error('Failed to fetch prompts:', err)
      const message = err.response?.status === 401
        ? 'Authentication required. Please log in again.'
        : err.response?.status === 403
        ? 'You don\'t have permission to view prompts.'
        : err.response?.status >= 500
        ? 'Server error. Please try again later.'
        : err.message || 'Failed to load prompts. Check your connection.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch on mount
  useEffect(() => {
    fetchPrompts()
  }, [fetchPrompts])

  // Handle create prompt
  const handleCreatePrompt = () => {
    setSelectedPrompt(null)
    setView('edit')
  }

  // Handle edit prompt
  const handleEditPrompt = (prompt: PromptResponse) => {
    setSelectedPrompt(prompt)
    setView('edit')
  }

  // Handle delete prompt
  const handleDeletePrompt = async (id: number) => {
    if (!window.confirm('Deactivate this prompt? It can be restored later.')) {
      return
    }

    const backup = prompts

    try {
      await promptService.deletePrompt(id)
      toast.success('Prompt deactivated successfully')
      await fetchPrompts()
    } catch (err: any) {
      console.error('Failed to delete prompt:', err)
      const message = err.response?.status === 404
        ? 'Prompt not found. It may have been deleted.'
        : err.response?.status === 403
        ? 'You don\'t have permission to delete this prompt.'
        : err.response?.status >= 500
        ? 'Server error. Please try again later.'
        : err.message || 'Failed to delete prompt. Check your connection.'
      setError(message)
      setPrompts(backup) // Restore on error
      toast.error(message)
    }
  }

  // Handle view history
  const handleViewHistory = (prompt: PromptResponse) => {
    setSelectedPrompt(prompt)
    setView('history')
  }

  // Handle save prompt (create or update)
  const handleSavePrompt = async (data: PromptCreate | PromptUpdate) => {
    try {
      if (selectedPrompt) {
        // Update existing prompt
        await promptService.updatePrompt(selectedPrompt.id, data as PromptUpdate)
        toast.success('Prompt updated successfully')
      } else {
        // Create new prompt
        await promptService.createPrompt(data as PromptCreate)
        toast.success('Prompt created successfully')
      }

      setView('list')
      await fetchPrompts()
    } catch (err: any) {
      console.error('Failed to save prompt:', err)
      const message = err.response?.data?.detail || 'Failed to save prompt'
      toast.error(message)
      throw err // Re-throw so editor can handle it
    }
  }

  // Handle cancel editor
  const handleCancelEditor = () => {
    setView('list')
    setSelectedPrompt(null)
  }

  // Handle close history
  const handleCloseHistory = () => {
    setView('list')
    setSelectedPrompt(null)
  }

  // Handle restore version
  const handleRestoreVersion = async () => {
    setView('list')
    setSelectedPrompt(null)
    await fetchPrompts() // Refresh list to show updated version
  }

  // Loading state
  if (loading && view === 'list') {
    return (
      <div className="prompts-manager">
        <div className="prompts-loading">
          <div className="loading-spinner"></div>
          <p>Loading prompts...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error && view === 'list') {
    return (
      <div className="prompts-manager">
        <div className="prompts-error">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button onClick={fetchPrompts} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="prompts-manager">
      {view === 'list' && (
        <PromptsList
          prompts={prompts}
          loading={loading}
          onCreatePrompt={handleCreatePrompt}
          onEditPrompt={handleEditPrompt}
          onDeletePrompt={handleDeletePrompt}
          onViewHistory={handleViewHistory}
        />
      )}

      {view === 'edit' && (
        <PromptEditor
          prompt={selectedPrompt}
          onSave={handleSavePrompt}
          onCancel={handleCancelEditor}
        />
      )}

      {view === 'history' && selectedPrompt && (
        <PromptVersionHistory
          prompt={selectedPrompt}
          onClose={handleCloseHistory}
          onRestore={handleRestoreVersion}
        />
      )}
    </div>
  )
}

export default PromptsManager
