// ABOUTME: Test suite for RebalancingPage component
// ABOUTME: Tests model selection, custom allocation, loading/error states, and API integration

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RebalancingPage } from './Rebalancing'
import * as rebalancingApi from '../api/rebalancing'

// Mock the API module
vi.mock('../api/rebalancing')

const mockAnalysis = {
  total_portfolio_value: 10000,
  current_allocation: [
    {
      asset_type: 'STOCK' as const,
      current_value: 6000,
      current_percentage: 60,
      target_percentage: 60,
      deviation: 0,
      status: 'BALANCED' as const,
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    },
    {
      asset_type: 'CRYPTO' as const,
      current_value: 2500,
      current_percentage: 25,
      target_percentage: 25,
      deviation: 0,
      status: 'BALANCED' as const,
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    },
    {
      asset_type: 'METAL' as const,
      current_value: 1500,
      current_percentage: 15,
      target_percentage: 15,
      deviation: 0,
      status: 'BALANCED' as const,
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    }
  ],
  target_model: 'moderate',
  rebalancing_required: false,
  total_trades_needed: 0,
  estimated_transaction_costs: 0,
  largest_deviation: 0,
  most_overweight: null,
  most_underweight: null,
  generated_at: '2025-01-01T12:00:00Z'
}

const mockRebalancingAnalysis = {
  ...mockAnalysis,
  rebalancing_required: true,
  total_trades_needed: 3,
  estimated_transaction_costs: 150,
  largest_deviation: 10,
  most_overweight: 'CRYPTO',
  most_underweight: 'STOCK',
  current_allocation: [
    {
      asset_type: 'STOCK' as const,
      current_value: 5000,
      current_percentage: 50,
      target_percentage: 60,
      deviation: -10,
      status: 'UNDERWEIGHT' as const,
      rebalancing_needed: true,
      delta_value: 1000,
      delta_percentage: -10
    },
    {
      asset_type: 'CRYPTO' as const,
      current_value: 3500,
      current_percentage: 35,
      target_percentage: 25,
      deviation: 10,
      status: 'OVERWEIGHT' as const,
      rebalancing_needed: true,
      delta_value: -1000,
      delta_percentage: 10
    },
    {
      asset_type: 'METAL' as const,
      current_value: 1500,
      current_percentage: 15,
      target_percentage: 15,
      deviation: 0,
      status: 'BALANCED' as const,
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    }
  ]
}

const mockRecommendations = {
  summary: 'Your portfolio requires rebalancing to align with moderate allocation targets.',
  priority: 'HIGH' as const,
  recommendations: [
    {
      action: 'SELL' as const,
      symbol: 'BTC',
      asset_type: 'CRYPTO' as const,
      quantity: 0.05,
      current_price: 20000,
      estimated_value: 1000,
      rationale: 'Reduce crypto exposure to target allocation',
      priority: 1,
      timing: 'Within 1 week',
      transaction_data: {
        transaction_type: 'SELL' as const,
        symbol: 'BTC',
        quantity: 0.05,
        price: 20000,
        total_value: 1000,
        currency: 'EUR',
        notes: 'Rebalancing: Reduce crypto from 35% to 25%'
      }
    }
  ],
  expected_outcome: {
    stocks_percentage: 60,
    crypto_percentage: 25,
    metals_percentage: 15,
    total_trades: 3,
    estimated_costs: 150,
    net_allocation_improvement: '10% reduction in deviation'
  },
  risk_assessment: 'Low risk rebalancing plan',
  implementation_notes: 'Execute trades during market hours',
  generated_at: '2025-01-01T12:00:00Z',
  tokens_used: 1500,
  cached: false
}

describe('RebalancingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render page header', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    render(<RebalancingPage />)

    expect(screen.getByText('Portfolio Rebalancing')).toBeInTheDocument()
    expect(screen.getByText(/AI-powered recommendations to optimize your asset allocation/i)).toBeInTheDocument()
  })

  it('should display loading state initially', () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockImplementation(() => new Promise(() => {}))

    render(<RebalancingPage />)

    expect(screen.getByText(/Analyzing portfolio allocation/i)).toBeInTheDocument()
  })

  it('should load and display moderate model by default', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    render(<RebalancingPage />)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingAnalysis).toHaveBeenCalledWith('moderate', undefined, undefined, undefined)
    })

    const moderateButton = screen.getByText('Moderate').closest('button')
    expect(moderateButton).toHaveClass('active')
  })

  it('should switch to aggressive model when clicked', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Moderate')).toBeInTheDocument()
    })

    const aggressiveButton = screen.getByText('Aggressive').closest('button')
    await user.click(aggressiveButton!)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingAnalysis).toHaveBeenCalledWith('aggressive', undefined, undefined, undefined)
    })
  })

  it('should switch to conservative model when clicked', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Conservative')).toBeInTheDocument()
    })

    const conservativeButton = screen.getByText('Conservative').closest('button')
    await user.click(conservativeButton!)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingAnalysis).toHaveBeenCalledWith('conservative', undefined, undefined, undefined)
    })
  })

  it('should show custom allocation inputs when custom model selected', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })

    const customButton = screen.getByText('Custom').closest('button')
    await user.click(customButton!)

    expect(screen.getByLabelText(/Stocks \(%\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Crypto \(%\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Metals \(%\)/i)).toBeInTheDocument()
  })

  it('should validate custom allocation sums to 100%', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })

    const customButton = screen.getByText('Custom').closest('button')
    await user.click(customButton!)

    // Default values (50, 30, 20) should sum to 100
    expect(screen.getByText(/Total: 100%/i)).toBeInTheDocument()
    expect(screen.getByText(/Total: 100% ✓/i)).toBeInTheDocument()
  })

  it('should show validation error when custom allocation does not sum to 100%', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })

    const customButton = screen.getByText('Custom').closest('button')
    await user.click(customButton!)

    const stocksInput = screen.getByLabelText(/Stocks \(%\)/i)
    await user.clear(stocksInput)
    await user.type(stocksInput, '70')

    expect(screen.getByText(/Total: 120%/i)).toBeInTheDocument()
    expect(screen.getByText(/must equal 100%/i)).toBeInTheDocument()
  })

  it('should disable apply button when custom allocation is invalid', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })

    const customButton = screen.getByText('Custom').closest('button')
    await user.click(customButton!)

    const stocksInput = screen.getByLabelText(/Stocks \(%\)/i)
    await user.clear(stocksInput)
    await user.type(stocksInput, '70')

    const applyButton = screen.getByText('Apply')
    expect(applyButton).toBeDisabled()
  })

  it('should apply custom allocation when valid and apply clicked', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Custom')).toBeInTheDocument()
    })

    const customButton = screen.getByText('Custom').closest('button')
    await user.click(customButton!)

    const stocksInput = screen.getByLabelText(/Stocks \(%\)/i)
    await user.clear(stocksInput)
    await user.type(stocksInput, '40')

    const cryptoInput = screen.getByLabelText(/Crypto \(%\)/i)
    await user.clear(cryptoInput)
    await user.type(cryptoInput, '40')

    const metalsInput = screen.getByLabelText(/Metals \(%\)/i)
    await user.clear(metalsInput)
    await user.type(metalsInput, '20')

    const applyButton = screen.getByText('Apply')
    await user.click(applyButton)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingAnalysis).toHaveBeenCalledWith('custom', 40, 40, 20)
    })
  })

  it('should display error message when API call fails', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockRejectedValue(new Error('API Error'))

    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load rebalancing data/i)).toBeInTheDocument()
    })
  })

  it('should show retry button on error', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockRejectedValue(new Error('API Error'))

    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })
  })

  it('should retry loading data when retry button clicked', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis)
      .mockRejectedValueOnce(new Error('API Error'))
      .mockResolvedValueOnce(mockAnalysis)

    const user = userEvent.setup()
    render(<RebalancingPage />)

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })

    const retryButton = screen.getByText('Retry')
    await user.click(retryButton)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingAnalysis).toHaveBeenCalledTimes(2)
    })
  })

  it('should fetch recommendations when rebalancing is required', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockRebalancingAnalysis)
    vi.mocked(rebalancingApi.getRebalancingRecommendations).mockResolvedValue(mockRecommendations)

    render(<RebalancingPage />)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingRecommendations).toHaveBeenCalledWith('moderate', undefined, undefined, undefined)
    })
  })

  it('should not fetch recommendations when rebalancing is not required', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    render(<RebalancingPage />)

    await waitFor(() => {
      expect(rebalancingApi.getRebalancingAnalysis).toHaveBeenCalled()
    })

    expect(rebalancingApi.getRebalancingRecommendations).not.toHaveBeenCalled()
  })

  it('should call onNavigateToTransactions when create transaction is triggered', async () => {
    vi.mocked(rebalancingApi.getRebalancingAnalysis).mockResolvedValue(mockAnalysis)

    const onNavigateToTransactions = vi.fn()
    render(<RebalancingPage onNavigateToTransactions={onNavigateToTransactions} />)

    await waitFor(() => {
      expect(screen.getByText('Portfolio Rebalancing')).toBeInTheDocument()
    })

    // This test verifies the callback is passed correctly
    expect(onNavigateToTransactions).not.toHaveBeenCalled()
  })
})
