// ABOUTME: Unit tests for PromptsManager container component
// ABOUTME: Tests state management, API integration, and view switching

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PromptsManager } from './PromptsManager'
import { promptService } from '../services/promptService'
import type { PromptListResponse, PromptResponse } from '../types/prompt.types'

// Mock promptService
vi.mock('../services/promptService')

// Mock toast
vi.mock('react-toastify', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('PromptsManager', () => {
  const mockPrompt: PromptResponse = {
    id: 1,
    name: 'global_market_analysis',
    category: 'global',
    prompt_text: 'Analyze the market trends for {{symbol}} over {{timeframe}}',
    template_variables: { symbol: 'string', timeframe: 'string' },
    version: 1,
    is_active: true,
    created_at: '2025-11-05T10:00:00Z',
    updated_at: '2025-11-05T10:00:00Z'
  }

  const mockListResponse: PromptListResponse = {
    prompts: [mockPrompt],
    total: 1,
    skip: 0,
    limit: 100
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial Rendering and Data Fetching', () => {
    it('should render loading state initially', () => {
      vi.mocked(promptService.listPrompts).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      render(<PromptsManager />)

      expect(screen.getByText(/Loading/i)).toBeInTheDocument()
    })

    it('should fetch and display prompts on mount', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce(mockListResponse)

      render(<PromptsManager />)

      await waitFor(() => {
        expect(promptService.listPrompts).toHaveBeenCalledWith(undefined, true, 0, 100)
      })

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })
    })

    it('should display error state when fetch fails', async () => {
      vi.mocked(promptService.listPrompts).mockRejectedValueOnce(
        new Error('Network error')
      )

      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      })

      // Should show retry button
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
    })

    it('should retry fetching prompts when retry button clicked', async () => {
      vi.mocked(promptService.listPrompts)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockListResponse)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /Retry/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })
    })

    it('should display empty state when no prompts exist', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce({
        prompts: [],
        total: 0,
        skip: 0,
        limit: 100
      })

      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(/No Prompts Yet/i)).toBeInTheDocument()
      })

      // Should show create button
      expect(
        screen.getByRole('button', { name: /Create.*Prompt/i })
      ).toBeInTheDocument()
    })
  })

  describe('View Switching', () => {
    it('should switch to edit view when Create Prompt clicked', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce({
        prompts: [],
        total: 0,
        skip: 0,
        limit: 100
      })

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(/No Prompts Yet/i)).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /Create.*Prompt/i })
      await user.click(createButton)

      // Should show editor
      await waitFor(() => {
        expect(screen.getByText(/Create Prompt/i)).toBeInTheDocument()
      })
    })

    it('should switch to edit view when Edit clicked on prompt card', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce(mockListResponse)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /Edit/i })
      await user.click(editButton)

      // Should show editor with prompt data
      await waitFor(() => {
        expect(screen.getByText(/Edit Prompt/i)).toBeInTheDocument()
      })
    })

    it('should return to list view when editor is cancelled', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce(mockListResponse)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })

      // Open editor
      const editButton = screen.getByRole('button', { name: /Edit/i })
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText(/Edit Prompt/i)).toBeInTheDocument()
      })

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /Cancel/i })
      await user.click(cancelButton)

      // Should return to list
      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })
    })
  })

  describe('CRUD Operations', () => {
    it('should delete prompt when delete button clicked and confirmed', async () => {
      vi.mocked(promptService.listPrompts)
        .mockResolvedValueOnce(mockListResponse)
        .mockResolvedValueOnce({ ...mockListResponse, prompts: [] })

      vi.mocked(promptService.deletePrompt).mockResolvedValueOnce({
        message: 'Prompt deactivated',
        success: true
      })

      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: /Delete/i })
      await user.click(deleteButton)

      // Should show confirmation
      expect(confirmSpy).toHaveBeenCalled()

      // Should call delete API
      await waitFor(() => {
        expect(promptService.deletePrompt).toHaveBeenCalledWith(mockPrompt.id)
      })

      // Should refetch prompts
      await waitFor(() => {
        expect(promptService.listPrompts).toHaveBeenCalledTimes(2)
      })

      confirmSpy.mockRestore()
    })

    it('should not delete prompt when confirmation cancelled', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce(mockListResponse)

      // Mock window.confirm to return false
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: /Delete/i })
      await user.click(deleteButton)

      // Should not call delete API
      expect(promptService.deletePrompt).not.toHaveBeenCalled()

      confirmSpy.mockRestore()
    })

    it('should handle delete errors gracefully', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce(mockListResponse)
      vi.mocked(promptService.deletePrompt).mockRejectedValueOnce(
        new Error('Server error')
      )

      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: /Delete/i })
      await user.click(deleteButton)

      // Should show error message (shows err.message when no HTTP response)
      await waitFor(() => {
        expect(screen.getByText(/Server error/i)).toBeInTheDocument()
      })

      confirmSpy.mockRestore()
    })
  })

  describe('Search and Filter', () => {
    const multiplePrompts: PromptResponse[] = [
      {
        ...mockPrompt,
        id: 1,
        name: 'global_analysis',
        category: 'global'
      },
      {
        ...mockPrompt,
        id: 2,
        name: 'position_analysis',
        category: 'position'
      },
      {
        ...mockPrompt,
        id: 3,
        name: 'forecast_analysis',
        category: 'forecast'
      }
    ]

    it('should filter prompts by category', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce({
        prompts: multiplePrompts,
        total: 3,
        skip: 0,
        limit: 100
      })

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText('global_analysis')).toBeInTheDocument()
        expect(screen.getByText('position_analysis')).toBeInTheDocument()
        expect(screen.getByText('forecast_analysis')).toBeInTheDocument()
      })

      // Find and click category filter
      const categorySelect = screen.getByRole('combobox', { name: /Category/i })
      await user.selectOptions(categorySelect, 'global')

      // Should show only global prompts
      await waitFor(() => {
        expect(screen.getByText('global_analysis')).toBeInTheDocument()
        expect(screen.queryByText('position_analysis')).not.toBeInTheDocument()
        expect(screen.queryByText('forecast_analysis')).not.toBeInTheDocument()
      })
    })

    it('should search prompts by name', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce({
        prompts: multiplePrompts,
        total: 3,
        skip: 0,
        limit: 100
      })

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText('global_analysis')).toBeInTheDocument()
      })

      // Type in search box
      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'position')

      // Should show only matching prompts
      await waitFor(() => {
        expect(screen.queryByText('global_analysis')).not.toBeInTheDocument()
        expect(screen.getByText('position_analysis')).toBeInTheDocument()
        expect(screen.queryByText('forecast_analysis')).not.toBeInTheDocument()
      })
    })

    it('should show empty state when search returns no results', async () => {
      vi.mocked(promptService.listPrompts).mockResolvedValueOnce(mockListResponse)

      const user = userEvent.setup()
      render(<PromptsManager />)

      await waitFor(() => {
        expect(screen.getByText(mockPrompt.name)).toBeInTheDocument()
      })

      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'nonexistent')

      await waitFor(() => {
        expect(screen.getByText(/No results found/i)).toBeInTheDocument()
      })
    })
  })
})
