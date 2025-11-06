// ABOUTME: Unit tests for PromptCard component
// ABOUTME: Tests rendering, badges, preview truncation, and action buttons

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PromptCard } from './PromptCard'
import type { PromptResponse } from '../types/prompt.types'

describe('PromptCard', () => {
  const mockPrompt: PromptResponse = {
    id: 1,
    name: 'global_market_analysis',
    category: 'global',
    prompt_text: 'Analyze the global market trends for {{symbol}} over the past {{timeframe}}. Consider key metrics and provide insights.',
    template_variables: { symbol: 'string', timeframe: 'string' },
    version: 3,
    is_active: true,
    created_at: '2025-11-05T10:00:00Z',
    updated_at: '2025-11-05T14:30:00Z'
  }

  const mockHandlers = {
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onViewHistory: vi.fn()
  }

  describe('Rendering', () => {
    it('should render prompt name', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.getByText('global_market_analysis')).toBeInTheDocument()
    })

    it('should render category badge', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      const badge = screen.getByText('global')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('prompt-category')
    })

    it('should apply correct badge class for category', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      const badge = screen.getByText('global')
      expect(badge).toHaveClass('badge-global')
    })

    it('should render version number', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.getByText(/v3/i)).toBeInTheDocument()
    })

    it('should render prompt preview', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      expect(
        screen.getByText(/Analyze the global market trends/i)
      ).toBeInTheDocument()
    })

    it('should render all action buttons', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.getByRole('button', { name: /Edit/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /History/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Delete/i })).toBeInTheDocument()
    })
  })

  describe('Category Badges', () => {
    it('should render global category badge', () => {
      const globalPrompt = { ...mockPrompt, category: 'global' as const }
      render(<PromptCard prompt={globalPrompt} {...mockHandlers} />)

      const badge = screen.getByText('global')
      expect(badge).toHaveClass('badge-global')
    })

    it('should render position category badge', () => {
      const positionPrompt = { ...mockPrompt, category: 'position' as const }
      render(<PromptCard prompt={positionPrompt} {...mockHandlers} />)

      const badge = screen.getByText('position')
      expect(badge).toHaveClass('badge-position')
    })

    it('should render forecast category badge', () => {
      const forecastPrompt = { ...mockPrompt, category: 'forecast' as const }
      render(<PromptCard prompt={forecastPrompt} {...mockHandlers} />)

      const badge = screen.getByText('forecast')
      expect(badge).toHaveClass('badge-forecast')
    })
  })

  describe('Text Truncation', () => {
    it('should truncate long prompt text', () => {
      const longText = 'A'.repeat(200)
      const longPrompt = { ...mockPrompt, prompt_text: longText }

      render(<PromptCard prompt={longPrompt} {...mockHandlers} />)

      const preview = screen.getByText(/A{3,}\.\.\./)
      expect(preview.textContent!.length).toBeLessThan(155)
    })

    it('should not truncate short prompt text', () => {
      const shortPrompt = {
        ...mockPrompt,
        prompt_text: 'Short prompt'
      }

      render(<PromptCard prompt={shortPrompt} {...mockHandlers} />)

      const preview = screen.getByText('Short prompt')
      expect(preview.textContent).not.toContain('...')
    })

    it('should show character count for long text', () => {
      const longText = 'A'.repeat(200)
      const longPrompt = { ...mockPrompt, prompt_text: longText }

      render(<PromptCard prompt={longPrompt} {...mockHandlers} />)

      expect(screen.getByText(/200 characters/i)).toBeInTheDocument()
    })
  })

  describe('Inactive State', () => {
    it('should show inactive badge when prompt is not active', () => {
      const inactivePrompt = { ...mockPrompt, is_active: false }

      render(<PromptCard prompt={inactivePrompt} {...mockHandlers} />)

      expect(screen.getByText(/Inactive/i)).toBeInTheDocument()
    })

    it('should not show inactive badge when prompt is active', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      expect(screen.queryByText(/Inactive/i)).not.toBeInTheDocument()
    })
  })

  describe('Action Buttons', () => {
    it('should call onEdit when Edit button clicked', async () => {
      const user = userEvent.setup()
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      const editButton = screen.getByRole('button', { name: /Edit/i })
      await user.click(editButton)

      expect(mockHandlers.onEdit).toHaveBeenCalledTimes(1)
    })

    it('should call onViewHistory when History button clicked', async () => {
      const user = userEvent.setup()
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      const historyButton = screen.getByRole('button', { name: /History/i })
      await user.click(historyButton)

      expect(mockHandlers.onViewHistory).toHaveBeenCalledTimes(1)
    })

    it('should call onDelete when Delete button clicked', async () => {
      const user = userEvent.setup()
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      const deleteButton = screen.getByRole('button', { name: /Delete/i })
      await user.click(deleteButton)

      expect(mockHandlers.onDelete).toHaveBeenCalledTimes(1)
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels for action buttons', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      expect(
        screen.getByRole('button', { name: /Edit Prompt/i })
      ).toHaveAttribute('aria-label')
    })

    it('should have accessible button text', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      const editButton = screen.getByRole('button', { name: /Edit/i })
      expect(editButton).toBeVisible()
    })
  })

  describe('Updated Timestamp', () => {
    it('should display relative time for recent updates', () => {
      render(<PromptCard prompt={mockPrompt} {...mockHandlers} />)

      // Should show some form of timestamp
      expect(screen.getByText(/ago|just now|updated/i)).toBeInTheDocument()
    })
  })
})
