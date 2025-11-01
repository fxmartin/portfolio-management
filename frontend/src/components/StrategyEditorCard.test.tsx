// ABOUTME: Test suite for StrategyEditorCard component
// ABOUTME: Tests strategy text editing, validation, templates, and save functionality

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StrategyEditorCard } from './StrategyEditorCard'
import type { InvestmentStrategy } from '../types/strategy'

describe('StrategyEditorCard', () => {
  const mockOnSave = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render editor card with empty form', () => {
    render(<StrategyEditorCard onSave={mockOnSave} />)

    expect(screen.getByLabelText(/Strategy Text/i)).toBeInTheDocument()
    expect(screen.getByText(/0 \/ 5000 characters/i)).toBeInTheDocument()
    expect(screen.getByText(/0 words \(minimum 20\)/i)).toBeInTheDocument()
  })

  it('should load existing strategy data', () => {
    const strategy: InvestmentStrategy = {
      id: 1,
      user_id: 1,
      strategy_text: 'My investment strategy focuses on long-term growth with diversified assets across multiple sectors.',
      target_annual_return: 12,
      risk_tolerance: 'medium',
      time_horizon_years: 10,
      max_positions: 25,
      profit_taking_threshold: 50,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
      version: 1
    }

    render(<StrategyEditorCard strategy={strategy} onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i) as HTMLTextAreaElement
    expect(textarea.value).toContain('My investment strategy focuses on long-term growth')

    const targetReturnInput = screen.getByLabelText(/Target Annual Return/i) as HTMLInputElement
    expect(targetReturnInput.value).toBe('12')

    const riskSelect = screen.getByLabelText(/Risk Tolerance/i) as HTMLSelectElement
    expect(riskSelect.value).toBe('medium')
  })

  it('should update character count as user types', async () => {
    const { container } = render(<StrategyEditorCard onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i)
    const text = 'This is my investment strategy'
    fireEvent.change(textarea, { target: { value: text } })

    await waitFor(() => {
      const counters = container.querySelector('.counters')
      expect(counters?.textContent).toContain(text.length.toString())
      expect(counters?.textContent).toContain('5000 characters')
    })
  })

  it('should update word count as user types', async () => {
    const user = userEvent.setup()
    const { container } = render(<StrategyEditorCard onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i)
    await user.type(textarea, 'One two three four five six seven eight nine ten eleven twelve')

    await waitFor(() => {
      const counters = container.querySelector('.counters')
      expect(counters?.textContent).toContain('12 words')
    })
  })

  it('should show validation error when less than 20 words', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i)
    await user.type(textarea, 'Too short strategy text')

    await waitFor(() => {
      expect(screen.getByText(/minimum 20 words required/i)).toBeInTheDocument()
    })
  })

  it('should show validation error when exceeds 5000 characters', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i) as HTMLTextAreaElement
    const longText = 'a'.repeat(5001)

    // Use fireEvent for performance with large text
    fireEvent.change(textarea, { target: { value: longText } })

    await waitFor(() => {
      expect(screen.getByText(/maximum 5000 characters/i)).toBeInTheDocument()
    })
  })

  it('should disable save button when validation fails', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const saveButton = screen.getByText('Save Strategy')
    expect(saveButton).toBeDisabled()

    const textarea = screen.getByLabelText(/Strategy Text/i)
    await user.type(textarea, 'Too short')

    await waitFor(() => {
      expect(saveButton).toBeDisabled()
    })
  })

  it('should enable save button when validation passes', async () => {
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i)
    const validText = 'My long-term investment strategy focuses on diversified growth through stocks bonds and real estate for retirement planning with proper asset allocation.'

    fireEvent.change(textarea, { target: { value: validText } })

    await waitFor(() => {
      const saveButton = screen.getByText('Save Strategy')
      expect(saveButton).not.toBeDisabled()
    })
  })

  it('should open templates modal when "Use Template" clicked', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const templateButton = screen.getByText('Use Template')
    await user.click(templateButton)

    await waitFor(() => {
      expect(screen.getByText('Strategy Templates')).toBeInTheDocument()
    })
  })

  it('should insert template text when template selected', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const templateButton = screen.getByText('Use Template')
    await user.click(templateButton)

    await waitFor(() => {
      expect(screen.getByText('Conservative Growth')).toBeInTheDocument()
    })

    const useButtons = screen.getAllByText('Use Template')
    await user.click(useButtons[1]) // Click first template's "Use Template" button

    await waitFor(() => {
      const textarea = screen.getByLabelText(/Strategy Text/i) as HTMLTextAreaElement
      expect(textarea.value).toContain('My investment strategy')
    })
  })

  it('should call onSave with correct data when save clicked', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i)
    const validText = 'My long-term investment strategy focuses on diversified growth through stocks bonds and real estate for retirement planning with proper asset allocation.'
    fireEvent.change(textarea, { target: { value: validText } })

    const targetReturnInput = screen.getByLabelText(/Target Annual Return/i)
    await user.clear(targetReturnInput)
    await user.type(targetReturnInput, '15')

    await waitFor(() => {
      const saveButton = screen.getByText('Save Strategy')
      expect(saveButton).not.toBeDisabled()
    })

    const saveButton = screen.getByText('Save Strategy')
    await user.click(saveButton)

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(
        expect.objectContaining({
          strategy_text: validText,
          target_annual_return: 15
        })
      )
    })
  })

  it('should show loading state during save', async () => {
    const user = userEvent.setup()
    const slowSave = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)))
    render(<StrategyEditorCard onSave={slowSave} />)

    const textarea = screen.getByLabelText(/Strategy Text/i)
    const validText = 'My long-term investment strategy focuses on diversified growth through stocks bonds and real estate for retirement planning with proper asset allocation.'
    fireEvent.change(textarea, { target: { value: validText } })

    await waitFor(() => {
      const saveButton = screen.getByText('Save Strategy')
      expect(saveButton).not.toBeDisabled()
    })

    const saveButton = screen.getByText('Save Strategy')
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/Saving/i)).toBeInTheDocument()
    })
  })

  it('should display last updated timestamp when strategy exists', () => {
    const strategy: InvestmentStrategy = {
      id: 1,
      user_id: 1,
      strategy_text: 'My strategy text with more than twenty words to pass validation requirements for testing purposes.',
      created_at: '2025-01-01T10:00:00Z',
      updated_at: '2025-01-15T14:30:00Z',
      version: 3,
      target_annual_return: 10,
      risk_tolerance: 'medium',
      time_horizon_years: 10,
      max_positions: 25,
      profit_taking_threshold: 50
    }

    render(<StrategyEditorCard strategy={strategy} onSave={mockOnSave} />)

    expect(screen.getByText(/Version 3/i)).toBeInTheDocument()
    expect(screen.getByText(/Last updated/i)).toBeInTheDocument()
  })

  it('should handle all structured fields', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    expect(screen.getByLabelText(/Target Annual Return/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Risk Tolerance/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Time Horizon/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Max Positions/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Profit-Taking Threshold/i)).toBeInTheDocument()
  })

  it('should validate max positions range', async () => {
    const user = userEvent.setup()
    render(<StrategyEditorCard onSave={mockOnSave} />)

    const maxPositionsInput = screen.getByLabelText(/Max Positions/i)
    await user.clear(maxPositionsInput)
    await user.type(maxPositionsInput, '150')

    const input = maxPositionsInput as HTMLInputElement
    expect(parseInt(input.value)).toBeLessThanOrEqual(100)
  })
})
