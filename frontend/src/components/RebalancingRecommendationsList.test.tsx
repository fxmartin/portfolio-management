// ABOUTME: Test suite for RebalancingRecommendationsList component
// ABOUTME: Tests expand/collapse, copy, navigation, planned/completed state tracking

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RebalancingRecommendationsList from './RebalancingRecommendationsList'
import type { RebalancingAnalysis, RebalancingRecommendationResponse } from '../api/rebalancing'
import * as rebalancingApi from '../api/rebalancing'

vi.mock('../api/rebalancing')

const mockBalancedAnalysis: RebalancingAnalysis = {
  total_portfolio_value: 10000,
  current_allocation: [],
  target_model: 'moderate',
  rebalancing_required: false,
  total_trades_needed: 0,
  estimated_transaction_costs: 0,
  largest_deviation: 0,
  most_overweight: null,
  most_underweight: null,
  generated_at: '2025-01-01T12:00:00Z'
}

const mockRebalancingAnalysis: RebalancingAnalysis = {
  ...mockBalancedAnalysis,
  rebalancing_required: true,
  total_trades_needed: 3,
  estimated_transaction_costs: 150,
  largest_deviation: 10
}

const mockRecommendations: RebalancingRecommendationResponse = {
  summary: 'Your portfolio requires rebalancing to align with moderate allocation targets.',
  priority: 'HIGH',
  recommendations: [
    {
      action: 'SELL',
      symbol: 'BTC',
      asset_type: 'CRYPTO',
      quantity: 0.05,
      current_price: 20000,
      estimated_value: 1000,
      rationale: 'Reduce crypto exposure from 35% to 25% to meet target allocation. This will help balance risk and align with moderate strategy.',
      priority: 1,
      timing: 'Within 1 week',
      transaction_data: {
        transaction_type: 'SELL',
        symbol: 'BTC',
        quantity: 0.05,
        price: 20000,
        total_value: 1000,
        currency: 'EUR',
        notes: 'Rebalancing: Reduce crypto from 35% to 25%'
      }
    },
    {
      action: 'BUY',
      symbol: 'MSTR',
      asset_type: 'STOCK',
      quantity: 10,
      current_price: 248.50,
      estimated_value: 2485,
      rationale: 'Increase stock exposure from 50% to 60% to meet target allocation. Focus on high-growth tech stocks.',
      priority: 2,
      timing: 'Within 2 weeks',
      transaction_data: {
        transaction_type: 'BUY',
        symbol: 'MSTR',
        quantity: 10,
        price: 248.50,
        total_value: 2485,
        currency: 'EUR',
        notes: 'Rebalancing: Increase stocks from 50% to 60%'
      }
    }
  ],
  expected_outcome: {
    stocks_percentage: 60,
    crypto_percentage: 25,
    metals_percentage: 15,
    total_trades: 3,
    estimated_costs: 150,
    net_allocation_improvement: '10% reduction in deviation from target'
  },
  risk_assessment: 'Low risk rebalancing plan with gradual execution recommended.',
  implementation_notes: 'Execute trades during market hours. Consider tax implications of crypto sale.',
  generated_at: '2025-01-01T12:00:00Z',
  tokens_used: 1500,
  cached: false
}

describe('RebalancingRecommendationsList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset localStorage/sessionStorage mocks
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
    vi.mocked(sessionStorage.getItem).mockReturnValue(null)
    vi.mocked(sessionStorage.setItem).mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should show message when no rebalancing required', () => {
    render(<RebalancingRecommendationsList analysis={mockBalancedAnalysis} recommendations={null} />)

    expect(screen.getByText('No rebalancing recommendations needed.')).toBeInTheDocument()
    expect(screen.getByText('Your portfolio is well-balanced!')).toBeInTheDocument()
  })

  it('should show loading state when recommendations are null but rebalancing required', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={null} />)

    expect(screen.getByText('Generating AI recommendations...')).toBeInTheDocument()
  })

  it('should render recommendations header', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('AI Recommendations')).toBeInTheDocument()
  })

  it('should display priority badge', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('should display summary text', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText(/Your portfolio requires rebalancing/i)).toBeInTheDocument()
  })

  it('should display all recommendations', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('BTC')).toBeInTheDocument()
    expect(screen.getByText('MSTR')).toBeInTheDocument()
  })

  it('should display SELL action badge for sell recommendations', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('SELL')).toBeInTheDocument()
  })

  it('should display BUY action badge for buy recommendations', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('BUY')).toBeInTheDocument()
  })

  it('should display priority numbers', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('#1')).toBeInTheDocument()
    expect(screen.getByText('#2')).toBeInTheDocument()
  })

  it('should display trade details (quantity, price, total)', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getAllByText(/Quantity:/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Price:/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Total:/i).length).toBeGreaterThan(0)
  })

  it('should format quantity with locale string', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('0.05')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('should format price with EUR symbol and decimals', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('€20,000.00')).toBeInTheDocument()
    expect(screen.getByText('€248.50')).toBeInTheDocument()
  })

  it('should show rationale preview when collapsed', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const preview = screen.getByText(/Reduce crypto exposure from 35% to 25%/i)
    expect(preview).toBeInTheDocument()
  })

  it('should expand recommendation when expand button clicked', async () => {
    const user = userEvent.setup()
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const expandButtons = screen.getAllByLabelText('Expand')
    await user.click(expandButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Rationale')).toBeInTheDocument()
    })
  })

  it('should show full rationale when expanded', async () => {
    const user = userEvent.setup()
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const expandButtons = screen.getAllByLabelText('Expand')
    await user.click(expandButtons[0])

    await waitFor(() => {
      expect(screen.getByText(/This will help balance risk and align with moderate strategy/i)).toBeInTheDocument()
    })
  })

  it('should show timing when expanded', async () => {
    const user = userEvent.setup()
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const expandButtons = screen.getAllByLabelText('Expand')
    await user.click(expandButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Timing')).toBeInTheDocument()
      expect(screen.getByText('Within 1 week')).toBeInTheDocument()
    })
  })

  it('should show transaction data when expanded', async () => {
    const user = userEvent.setup()
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const expandButtons = screen.getAllByLabelText('Expand')
    await user.click(expandButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Transaction Data')).toBeInTheDocument()
    })
  })

  it('should collapse recommendation when collapse button clicked', async () => {
    const user = userEvent.setup()
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const expandButtons = screen.getAllByLabelText('Expand')
    await user.click(expandButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Rationale')).toBeInTheDocument()
    })

    const collapseButton = screen.getByLabelText('Collapse')
    await user.click(collapseButton)

    await waitFor(() => {
      expect(screen.queryByText('Rationale')).not.toBeInTheDocument()
    })
  })

  it('should display Copy Data button', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const copyButtons = screen.getAllByText('Copy Data')
    expect(copyButtons.length).toBe(2)
  })

  it('should call copyTransactionDataToClipboard when copy button clicked', async () => {
    const copySpy = vi.spyOn(rebalancingApi, 'copyTransactionDataToClipboard')
    const user = userEvent.setup()

    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const copyButtons = screen.getAllByText('Copy Data')
    await user.click(copyButtons[0])

    expect(copySpy).toHaveBeenCalledWith(mockRecommendations.recommendations[0].transaction_data)
  })

  it('should show Copied! message after copy button clicked', async () => {
    const user = userEvent.setup()
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const copyButtons = screen.getAllByText('Copy Data')
    await user.click(copyButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Copied!')).toBeInTheDocument()
    })
  })

  it('should reset copy state after 2 seconds', async () => {
    vi.useFakeTimers()

    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const copyButtons = screen.getAllByText('Copy Data')

    await act(async () => {
      fireEvent.click(copyButtons[0])
    })

    expect(screen.getByText('Copied!')).toBeInTheDocument()

    await act(async () => {
      vi.advanceTimersByTime(2000)
    })

    expect(screen.queryByText('Copied!')).not.toBeInTheDocument()

    vi.useRealTimers()
  })

  it('should display Create Transaction button', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const createButtons = screen.getAllByText('Create Transaction')
    expect(createButtons.length).toBe(2)
  })

  it('should store transaction data in sessionStorage when Create Transaction clicked', async () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const createButtons = screen.getAllByText('Create Transaction')
    fireEvent.click(createButtons[0])

    expect(sessionStorage.setItem).toHaveBeenCalledWith('transaction_prefill', expect.stringContaining('BTC'))
  })

  it('should call onCreateTransaction callback when provided', async () => {
    const onCreateTransaction = vi.fn()

    render(
      <RebalancingRecommendationsList
        analysis={mockRebalancingAnalysis}
        recommendations={mockRecommendations}
        onCreateTransaction={onCreateTransaction}
      />
    )

    const createButtons = screen.getAllByText('Create Transaction')
    fireEvent.click(createButtons[0])

    expect(onCreateTransaction).toHaveBeenCalledWith(expect.objectContaining({
      symbol: 'BTC',
      transaction_type: 'SELL'
    }))
  })

  it('should display Mark Planned button', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const plannedButtons = screen.getAllByText('Mark Planned')
    expect(plannedButtons.length).toBe(2)
  })

  it('should toggle planned state when Mark Planned clicked', async () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    // Get first Mark Planned button and click it
    const plannedButton = screen.getAllByText('Mark Planned')[0]

    await act(async () => {
      fireEvent.click(plannedButton)
    })

    // Should show "Planned ✓" text immediately
    expect(screen.getByText('Planned ✓')).toBeInTheDocument()
  })

  it('should save planned state to localStorage', async () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const plannedButtons = screen.getAllByText('Mark Planned')

    await act(async () => {
      fireEvent.click(plannedButtons[0])
    })

    expect(screen.getByText('Planned ✓')).toBeInTheDocument()
    expect(localStorage.setItem).toHaveBeenCalledWith('rebalancing_planned', expect.stringContaining('0'))
  })

  it('should display Mark Completed button', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const completedButtons = screen.getAllByText('Mark Completed')
    expect(completedButtons.length).toBe(2)
  })

  it('should toggle completed state when Mark Completed clicked', async () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const completedButtons = screen.getAllByText('Mark Completed')

    await act(async () => {
      fireEvent.click(completedButtons[0])
    })

    expect(screen.getByText('Completed ✓')).toBeInTheDocument()
  })

  it('should save completed state to localStorage', async () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const completedButtons = screen.getAllByText('Mark Completed')

    await act(async () => {
      fireEvent.click(completedButtons[0])
    })

    expect(screen.getByText('Completed ✓')).toBeInTheDocument()
    expect(localStorage.setItem).toHaveBeenCalledWith('rebalancing_completed', expect.stringContaining('0'))
  })

  it('should automatically mark as planned when marked as completed', async () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const completedButtons = screen.getAllByText('Mark Completed')

    await act(async () => {
      fireEvent.click(completedButtons[0])
    })

    expect(screen.getByText('Completed ✓')).toBeInTheDocument()
    expect(localStorage.setItem).toHaveBeenCalledWith('rebalancing_planned', expect.stringContaining('0'))
  })

  it('should restore planned state from localStorage on mount', () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => {
      if (key === 'rebalancing_planned') return JSON.stringify([0])
      return null
    })

    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('Planned ✓')).toBeInTheDocument()
  })

  it('should restore completed state from localStorage on mount', () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => {
      if (key === 'rebalancing_completed') return JSON.stringify([1])
      return null
    })

    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('Completed ✓')).toBeInTheDocument()
  })

  it('should display expected outcome section', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('Expected Outcome')).toBeInTheDocument()
  })

  it('should display expected allocation percentages', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('Stocks:')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
    expect(screen.getByText('Crypto:')).toBeInTheDocument()
    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText('Metals:')).toBeInTheDocument()
    expect(screen.getByText('15%')).toBeInTheDocument()
  })

  it('should display net allocation improvement', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText(/10% reduction in deviation/i)).toBeInTheDocument()
  })

  it('should display risk assessment section', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('Risk Assessment')).toBeInTheDocument()
    expect(screen.getByText(/Low risk rebalancing plan/i)).toBeInTheDocument()
  })

  it('should display implementation notes section', () => {
    render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    expect(screen.getByText('Implementation Notes')).toBeInTheDocument()
    expect(screen.getByText(/Execute trades during market hours/i)).toBeInTheDocument()
  })

  it('should apply correct CSS class for sell action', () => {
    const { container } = render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const sellItem = container.querySelector('.recommendation-item.sell')
    expect(sellItem).toBeInTheDocument()
  })

  it('should apply correct CSS class for buy action', () => {
    const { container } = render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const buyItem = container.querySelector('.recommendation-item.buy')
    expect(buyItem).toBeInTheDocument()
  })

  it('should apply planned CSS class when marked as planned', async () => {
    const { container } = render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const plannedButtons = screen.getAllByText('Mark Planned')

    await act(async () => {
      fireEvent.click(plannedButtons[0])
    })

    expect(screen.getByText('Planned ✓')).toBeInTheDocument()

    const plannedItem = container.querySelector('.recommendation-item.planned')
    expect(plannedItem).toBeInTheDocument()
  })

  it('should apply completed CSS class when marked as completed', async () => {
    const { container } = render(<RebalancingRecommendationsList analysis={mockRebalancingAnalysis} recommendations={mockRecommendations} />)

    const completedButtons = screen.getAllByText('Mark Completed')

    await act(async () => {
      fireEvent.click(completedButtons[0])
    })

    expect(screen.getByText('Completed ✓')).toBeInTheDocument()

    const completedItem = container.querySelector('.recommendation-item.completed')
    expect(completedItem).toBeInTheDocument()
  })
})
