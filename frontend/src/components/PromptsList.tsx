// ABOUTME: List view component for displaying all prompts with search and filter
// ABOUTME: Renders grid of PromptCards with filtering and empty states

import { useState, useMemo } from 'react'
import { Search, Plus } from 'lucide-react'
import { PromptCard } from './PromptCard'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import type { PromptResponse } from '../types/prompt.types'
import './PromptsList.css'

export interface PromptsListProps {
  prompts: PromptResponse[]
  loading: boolean
  onCreatePrompt: () => void
  onEditPrompt: (prompt: PromptResponse) => void
  onDeletePrompt: (id: number) => void
  onViewHistory: (prompt: PromptResponse) => void
}

export const PromptsList: React.FC<PromptsListProps> = ({
  prompts,
  loading,
  onCreatePrompt,
  onEditPrompt,
  onDeletePrompt,
  onViewHistory
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const debouncedSearchQuery = useDebouncedValue(searchQuery, 300)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  // Filter prompts based on search and category
  const filteredPrompts = useMemo(() => {
    return prompts.filter(prompt => {
      // Category filter
      if (categoryFilter !== 'all' && prompt.category !== categoryFilter) {
        return false
      }

      // Search filter (name or prompt_text)
      if (debouncedSearchQuery) {
        const query = debouncedSearchQuery.toLowerCase()
        return (
          prompt.name.toLowerCase().includes(query) ||
          prompt.prompt_text.toLowerCase().includes(query)
        )
      }

      return true
    })
  }, [prompts, debouncedSearchQuery, categoryFilter])

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('')
    setCategoryFilter('all')
  }

  // Has active filters
  const hasFilters = searchQuery !== '' || categoryFilter !== 'all'

  // Empty state when no prompts at all
  if (prompts.length === 0 && !loading) {
    return (
      <div className="prompts-list">
        <div className="prompts-empty">
          <div className="empty-icon">📝</div>
          <h3>No Prompts Yet</h3>
          <p>Create your first prompt to customize AI analysis output</p>
          <button onClick={onCreatePrompt} className="btn-primary">
            <Plus size={16} />
            Create First Prompt
          </button>
        </div>
      </div>
    )
  }

  // Empty state when search/filter returns no results
  if (filteredPrompts.length === 0 && hasFilters) {
    return (
      <div className="prompts-list">
        <div className="prompts-list-header">
          <div className="header-left">
            <h2>AI Prompts</h2>
          </div>
          <div className="header-right">
            <div className="search-box">
              <Search size={16} className="search-icon" />
              <input
                type="text"
                placeholder="Search prompts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
                aria-label="Search prompts"
              />
            </div>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="category-filter"
              aria-label="Category filter"
            >
              <option value="all">All Categories</option>
              <option value="global">Global Analysis</option>
              <option value="position">Position Analysis</option>
              <option value="forecast">Forecast Analysis</option>
            </select>

            <button onClick={onCreatePrompt} className="btn-primary">
              <Plus size={16} />
              Create Prompt
            </button>
          </div>
        </div>

        <div className="prompts-empty">
          <div className="empty-icon">🔍</div>
          <h3>No Results Found</h3>
          <p>Try a different search or filter</p>
          <button onClick={clearFilters} className="btn-secondary">
            Clear Filters
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="prompts-list">
      <div className="prompts-list-header">
        <div className="header-left">
          <h2>AI Prompts</h2>
          <span className="prompts-count">
            {filteredPrompts.length} {filteredPrompts.length === 1 ? 'prompt' : 'prompts'}
          </span>
        </div>

        <div className="header-right">
          <div className="search-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search prompts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
              aria-label="Search prompts"
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="category-filter"
            aria-label="Category filter"
          >
            <option value="all">All Categories</option>
            <option value="global">Global Analysis</option>
            <option value="position">Position Analysis</option>
            <option value="forecast">Forecast Analysis</option>
          </select>

          <button onClick={onCreatePrompt} className="btn-primary">
            <Plus size={16} />
            Create Prompt
          </button>
        </div>
      </div>

      <div className="prompts-grid">
        {filteredPrompts.map(prompt => (
          <PromptCard
            key={prompt.id}
            prompt={prompt}
            onEdit={() => onEditPrompt(prompt)}
            onDelete={() => onDeletePrompt(prompt.id)}
            onViewHistory={() => onViewHistory(prompt)}
          />
        ))}
      </div>
    </div>
  )
}

export default PromptsList
