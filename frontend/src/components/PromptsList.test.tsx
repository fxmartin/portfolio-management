// ABOUTME: Unit tests for PromptsList component
// ABOUTME: Tests list rendering, search, filter, and empty states

import { describe, it, expect, vi } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PromptsList } from './PromptsList'
import type { PromptResponse } from '../types/prompt.types'

describe('PromptsList', () => {
  const mockPrompts: PromptResponse[] = [
    {
      id: 1,
      name: 'global_market_analysis',
      category: 'global',
      prompt_text: 'Analyze global market trends for {{symbol}}',
      template_variables: { symbol: 'string' },
      version: 1,
      is_active: true,
      created_at: '2025-11-05T10:00:00Z',
      updated_at: '2025-11-05T10:00:00Z'
    },
    {
      id: 2,
      name: 'position_analysis',
      category: 'position',
      prompt_text: 'Analyze position for {{symbol}} with {{quantity}} shares',
      template_variables: { symbol: 'string', quantity: 'number' },
      version: 2,
      is_active: true,
      created_at: '2025-11-05T11:00:00Z',
      updated_at: '2025-11-05T11:00:00Z'
    },
    {
      id: 3,
      name: 'forecast_prediction',
      category: 'forecast',
      prompt_text: 'Forecast {{symbol}} over {{timeframe}}',
      template_variables: { symbol: 'string', timeframe: 'string' },
      version: 1,
      is_active: true,
      created_at: '2025-11-05T12:00:00Z',
      updated_at: '2025-11-05T12:00:00Z'
    }
  ]

  const mockHandlers = {
    onCreatePrompt: vi.fn(),
    onEditPrompt: vi.fn(),
    onDeletePrompt: vi.fn(),
    onViewHistory: vi.fn()
  }

  describe('Rendering', () => {
    it('should render prompts list with all prompts', () => {
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      expect(screen.getByText('global_market_analysis')).toBeInTheDocument()
      expect(screen.getByText('position_analysis')).toBeInTheDocument()
      expect(screen.getByText('forecast_prediction')).toBeInTheDocument()
    })

    it('should render search input', () => {
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      expect(screen.getByRole('textbox', { name: /Search/i })).toBeInTheDocument()
    })

    it('should render category filter', () => {
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      expect(screen.getByRole('combobox', { name: /Category/i })).toBeInTheDocument()
    })

    it('should render Create Prompt button', () => {
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      expect(
        screen.getByRole('button', { name: /Create Prompt/i })
      ).toBeInTheDocument()
    })
  })

  describe('Empty States', () => {
    it('should show empty state when no prompts exist', () => {
      render(
        <PromptsList
          prompts={[]}
          loading={false}
          {...mockHandlers}
        />
      )

      expect(screen.getByText(/No Prompts Yet/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /Create.*Prompt/i })
      ).toBeInTheDocument()
    })

    it('should call onCreatePrompt when Create button clicked in empty state', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={[]}
          loading={false}
          {...mockHandlers}
        />
      )

      const createButton = screen.getByRole('button', { name: /Create.*Prompt/i })
      await user.click(createButton)

      expect(mockHandlers.onCreatePrompt).toHaveBeenCalled()
    })
  })

  describe('Search Functionality', () => {
    it('should filter prompts by name when searching', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'position')

      // Wait for debounce (300ms)
      await waitFor(() => {
        expect(screen.getByText('position_analysis')).toBeInTheDocument()
        expect(screen.queryByText('global_market_analysis')).not.toBeInTheDocument()
        expect(screen.queryByText('forecast_prediction')).not.toBeInTheDocument()
      }, { timeout: 500 })
    })

    it('should filter prompts by prompt text content', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'global market')

      // Wait for debounce (300ms)
      await waitFor(() => {
        expect(screen.getByText('global_market_analysis')).toBeInTheDocument()
        expect(screen.queryByText('position_analysis')).not.toBeInTheDocument()
      }, { timeout: 500 })
    })

    it('should show "no results" when search returns nothing', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'nonexistent')

      // Wait for debounce (300ms)
      await waitFor(() => {
        expect(screen.getByText(/No results found/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Clear/i })).toBeInTheDocument()
      }, { timeout: 500 })
    })

    it('should clear filters when Clear button clicked', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'nonexistent')

      // Wait for debounce to show no results
      await waitFor(() => {
        expect(screen.getByText(/No results found/i)).toBeInTheDocument()
      }, { timeout: 500 })

      const clearButton = screen.getByRole('button', { name: /Clear/i })
      await user.click(clearButton)

      // Wait for debounce to clear and show all prompts again
      await waitFor(() => {
        expect(screen.getByText('global_market_analysis')).toBeInTheDocument()
        expect(screen.getByText('position_analysis')).toBeInTheDocument()
      }, { timeout: 500 })
    })

    it('should be case-insensitive when searching', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'POSITION')

      expect(screen.getByText('position_analysis')).toBeInTheDocument()
    })
  })

  describe('Category Filter', () => {
    it('should filter prompts by category', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const categorySelect = screen.getByRole('combobox', { name: /Category/i })
      await user.selectOptions(categorySelect, 'global')

      expect(screen.getByText('global_market_analysis')).toBeInTheDocument()
      expect(screen.queryByText('position_analysis')).not.toBeInTheDocument()
      expect(screen.queryByText('forecast_prediction')).not.toBeInTheDocument()
    })

    it('should show all prompts when "all" category selected', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const categorySelect = screen.getByRole('combobox', { name: /Category/i })

      // First filter to one category
      await user.selectOptions(categorySelect, 'position')
      expect(screen.queryByText('global_market_analysis')).not.toBeInTheDocument()

      // Then select "all"
      await user.selectOptions(categorySelect, 'all')
      expect(screen.getByText('global_market_analysis')).toBeInTheDocument()
      expect(screen.getByText('position_analysis')).toBeInTheDocument()
      expect(screen.getByText('forecast_prediction')).toBeInTheDocument()
    })

    it('should combine search and category filters', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      // Filter by category
      const categorySelect = screen.getByRole('combobox', { name: /Category/i })
      await user.selectOptions(categorySelect, 'position')

      // Then search
      const searchInput = screen.getByRole('textbox', { name: /Search/i })
      await user.type(searchInput, 'analysis')

      // Should show only position_analysis
      expect(screen.getByText('position_analysis')).toBeInTheDocument()
      expect(screen.queryByText('global_market_analysis')).not.toBeInTheDocument()
    })
  })

  describe('Create Prompt Button', () => {
    it('should call onCreatePrompt when Create Prompt button clicked', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={mockPrompts}
          loading={false}
          {...mockHandlers}
        />
      )

      const createButton = screen.getByRole('button', { name: /Create Prompt/i })
      await user.click(createButton)

      expect(mockHandlers.onCreatePrompt).toHaveBeenCalled()
    })
  })

  describe('Prompt Card Actions', () => {
    it('should call onEditPrompt when Edit button clicked', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={[mockPrompts[0]]}
          loading={false}
          {...mockHandlers}
        />
      )

      const editButton = screen.getByRole('button', { name: /Edit/i })
      await user.click(editButton)

      expect(mockHandlers.onEditPrompt).toHaveBeenCalledWith(mockPrompts[0])
    })

    it('should call onDeletePrompt when Delete button clicked', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={[mockPrompts[0]]}
          loading={false}
          {...mockHandlers}
        />
      )

      const deleteButton = screen.getByRole('button', { name: /Delete/i })
      await user.click(deleteButton)

      expect(mockHandlers.onDeletePrompt).toHaveBeenCalledWith(mockPrompts[0].id)
    })

    it('should call onViewHistory when History button clicked', async () => {
      const user = userEvent.setup()
      render(
        <PromptsList
          prompts={[mockPrompts[0]]}
          loading={false}
          {...mockHandlers}
        />
      )

      const historyButton = screen.getByRole('button', { name: /History/i })
      await user.click(historyButton)

      expect(mockHandlers.onViewHistory).toHaveBeenCalledWith(mockPrompts[0])
    })
  })
})
