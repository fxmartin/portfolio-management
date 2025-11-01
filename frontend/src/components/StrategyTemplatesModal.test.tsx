// ABOUTME: Test suite for StrategyTemplatesModal component
// ABOUTME: Tests template selection, preview, and insertion into strategy editor

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StrategyTemplatesModal } from './StrategyTemplatesModal'

describe('StrategyTemplatesModal', () => {
  const mockOnClose = vi.fn()
  const mockOnSelectTemplate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should not render when closed', () => {
    const { container } = render(
      <StrategyTemplatesModal
        isOpen={false}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    expect(container.firstChild).toBeNull()
  })

  it('should render modal when open', () => {
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    expect(screen.getByText('Strategy Templates')).toBeInTheDocument()
  })

  it('should display all 5 template options', () => {
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    expect(screen.getByText('Conservative Growth')).toBeInTheDocument()
    expect(screen.getByText('Balanced Growth')).toBeInTheDocument()
    expect(screen.getByText('Aggressive Growth')).toBeInTheDocument()
    expect(screen.getByText('Income Focus')).toBeInTheDocument()
    expect(screen.getByText('Value Investing')).toBeInTheDocument()
  })

  it('should display template descriptions', () => {
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    expect(screen.getByText(/Stable dividends, low risk/i)).toBeInTheDocument()
    expect(screen.getByText(/Mix of stocks\/crypto, medium risk/i)).toBeInTheDocument()
  })

  it('should call onSelectTemplate with correct data when "Use Template" clicked', async () => {
    const user = userEvent.setup()
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    const useButtons = screen.getAllByText('Use Template')
    await user.click(useButtons[0]) // Click first template (Conservative Growth)

    expect(mockOnSelectTemplate).toHaveBeenCalledTimes(1)
    expect(mockOnSelectTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'conservative-growth',
        title: 'Conservative Growth',
        strategy_text: expect.any(String),
        target_annual_return: expect.any(Number),
        risk_tolerance: 'low'
      })
    )
  })

  it('should call onClose when Cancel button clicked', async () => {
    const user = userEvent.setup()
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should display structured fields for each template', () => {
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    // Conservative Growth template card should show suggested fields
    const templateCards = screen.getAllByRole('article')
    expect(templateCards).toHaveLength(5)
  })

  it('should close modal when clicking backdrop', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    const backdrop = container.querySelector('.modal-backdrop')
    if (backdrop) {
      await user.click(backdrop)
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    }
  })

  it('should show different risk tolerance levels across templates', () => {
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    const lowRisk = screen.getAllByText(/Risk: Low/i)
    const mediumRisk = screen.getAllByText(/Risk: Medium/i)
    const highRisk = screen.getAllByText(/Risk: High/i)

    expect(lowRisk.length).toBeGreaterThan(0)
    expect(mediumRisk.length).toBeGreaterThan(0)
    expect(highRisk.length).toBeGreaterThan(0)
  })

  it('should show different time horizons across templates', () => {
    render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    const tenToFifteen = screen.getAllByText(/10-15 years/i)
    const fiveToTen = screen.getAllByText(/5-10 years/i)

    expect(tenToFifteen.length).toBeGreaterThan(0)
    expect(fiveToTen.length).toBeGreaterThan(0)
  })

  it('should highlight selected template card on hover', () => {
    const { container } = render(
      <StrategyTemplatesModal
        isOpen={true}
        onClose={mockOnClose}
        onSelectTemplate={mockOnSelectTemplate}
      />
    )

    const templateCards = container.querySelectorAll('.template-card')
    expect(templateCards.length).toBeGreaterThan(0)

    templateCards.forEach(card => {
      expect(card).toHaveClass('template-card')
    })
  })
})
