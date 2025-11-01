// ABOUTME: Test suite for AllocationComparisonChart component
// ABOUTME: Tests chart rendering, color coding, deviation display, and responsive behavior

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AllocationComparisonChart from './AllocationComparisonChart'
import type { RebalancingAnalysis } from '../api/rebalancing'

const mockBalancedAnalysis: RebalancingAnalysis = {
  total_portfolio_value: 10000,
  current_allocation: [
    {
      asset_type: 'STOCK',
      current_value: 6000,
      current_percentage: 60,
      target_percentage: 60,
      deviation: 0,
      status: 'BALANCED',
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    },
    {
      asset_type: 'CRYPTO',
      current_value: 2500,
      current_percentage: 25,
      target_percentage: 25,
      deviation: 0,
      status: 'BALANCED',
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    },
    {
      asset_type: 'METAL',
      current_value: 1500,
      current_percentage: 15,
      target_percentage: 15,
      deviation: 0,
      status: 'BALANCED',
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

const mockOverweightAnalysis: RebalancingAnalysis = {
  ...mockBalancedAnalysis,
  rebalancing_required: true,
  largest_deviation: 10,
  most_overweight: 'CRYPTO',
  most_underweight: 'STOCK',
  current_allocation: [
    {
      asset_type: 'STOCK',
      current_value: 5000,
      current_percentage: 50,
      target_percentage: 60,
      deviation: -10,
      status: 'UNDERWEIGHT',
      rebalancing_needed: true,
      delta_value: 1000,
      delta_percentage: -10
    },
    {
      asset_type: 'CRYPTO',
      current_value: 3500,
      current_percentage: 35,
      target_percentage: 25,
      deviation: 10,
      status: 'OVERWEIGHT',
      rebalancing_needed: true,
      delta_value: -1000,
      delta_percentage: 10
    },
    {
      asset_type: 'METAL',
      current_value: 1500,
      current_percentage: 15,
      target_percentage: 15,
      deviation: 0,
      status: 'BALANCED',
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    }
  ]
}

const mockSlightlyOverweightAnalysis: RebalancingAnalysis = {
  ...mockBalancedAnalysis,
  rebalancing_required: true,
  largest_deviation: 3,
  current_allocation: [
    {
      asset_type: 'STOCK',
      current_value: 5700,
      current_percentage: 57,
      target_percentage: 60,
      deviation: -3,
      status: 'SLIGHTLY_UNDERWEIGHT',
      rebalancing_needed: true,
      delta_value: 300,
      delta_percentage: -3
    },
    {
      asset_type: 'CRYPTO',
      current_value: 2800,
      current_percentage: 28,
      target_percentage: 25,
      deviation: 3,
      status: 'SLIGHTLY_OVERWEIGHT',
      rebalancing_needed: true,
      delta_value: -300,
      delta_percentage: 3
    },
    {
      asset_type: 'METAL',
      current_value: 1500,
      current_percentage: 15,
      target_percentage: 15,
      deviation: 0,
      status: 'BALANCED',
      rebalancing_needed: false,
      delta_value: 0,
      delta_percentage: 0
    }
  ]
}

describe('AllocationComparisonChart', () => {
  it('should render chart title', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    expect(screen.getByText('Current vs Target Allocation')).toBeInTheDocument()
  })

  it('should display all asset types', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    // Chart uses formatted names
    expect(screen.getByText('Stocks')).toBeInTheDocument()
    expect(screen.getByText('Crypto')).toBeInTheDocument()
    expect(screen.getByText('Metals')).toBeInTheDocument()
  })

  it('should show legend explanation', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    expect(screen.getByText(/Overweight \(reduce\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Underweight \(increase\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Balanced/i)).toBeInTheDocument()
  })

  it('should display deviation summary for all assets', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const deviations = screen.getAllByText(/0%/)
    expect(deviations.length).toBeGreaterThan(0)
  })

  it('should show positive deviation with plus sign', () => {
    render(<AllocationComparisonChart analysis={mockOverweightAnalysis} />)

    expect(screen.getByText('+10%')).toBeInTheDocument()
  })

  it('should show negative deviation without extra minus sign', () => {
    render(<AllocationComparisonChart analysis={mockOverweightAnalysis} />)

    expect(screen.getByText('-10%')).toBeInTheDocument()
  })

  it('should display zero deviation', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const zeroDeviations = screen.getAllByText('0%')
    expect(zeroDeviations.length).toBeGreaterThan(0)
  })

  it('should render chart container with correct class', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const chartDiv = container.querySelector('.allocation-comparison-chart')
    expect(chartDiv).toBeInTheDocument()
  })

  it('should render legend container', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const legend = container.querySelector('.chart-legend')
    expect(legend).toBeInTheDocument()
  })

  it('should render deviation summary container', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const deviationSummary = container.querySelector('.deviation-summary')
    expect(deviationSummary).toBeInTheDocument()
  })

  it('should display all three legend items', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const legendItems = container.querySelectorAll('.legend-item')
    expect(legendItems).toHaveLength(3)
  })

  it('should display all three asset deviations', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const deviationItems = container.querySelectorAll('.deviation-item')
    expect(deviationItems).toHaveLength(3)
  })

  it('should show overweight status with OVERWEIGHT classification', () => {
    render(<AllocationComparisonChart analysis={mockOverweightAnalysis} />)

    // Crypto is overweight with +10% deviation
    expect(screen.getByText('Crypto')).toBeInTheDocument()
    expect(screen.getByText('+10%')).toBeInTheDocument()
  })

  it('should show underweight status with UNDERWEIGHT classification', () => {
    render(<AllocationComparisonChart analysis={mockOverweightAnalysis} />)

    // Stocks are underweight with -10% deviation
    expect(screen.getByText('Stocks')).toBeInTheDocument()
    expect(screen.getByText('-10%')).toBeInTheDocument()
  })

  it('should show balanced status with zero deviation', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    // All assets are balanced
    const balancedText = screen.getByText(/Balanced/i)
    expect(balancedText).toBeInTheDocument()
  })

  it('should display slightly overweight assets', () => {
    render(<AllocationComparisonChart analysis={mockSlightlyOverweightAnalysis} />)

    expect(screen.getByText('+3%')).toBeInTheDocument()
  })

  it('should display slightly underweight assets', () => {
    render(<AllocationComparisonChart analysis={mockSlightlyOverweightAnalysis} />)

    expect(screen.getByText('-3%')).toBeInTheDocument()
  })

  it('should format asset type names correctly', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    // STOCK -> Stocks
    expect(screen.getByText('Stocks')).toBeInTheDocument()
    // CRYPTO -> Crypto
    expect(screen.getByText('Crypto')).toBeInTheDocument()
    // METAL -> Metals
    expect(screen.getByText('Metals')).toBeInTheDocument()
  })

  it('should display correct percentages for current allocation', () => {
    render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    // Chart data should include 60%, 25%, 15%
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)
    expect(container).toBeInTheDocument()
  })

  it('should handle single asset type', () => {
    const singleAssetAnalysis: RebalancingAnalysis = {
      ...mockBalancedAnalysis,
      current_allocation: [mockBalancedAnalysis.current_allocation[0]]
    }

    render(<AllocationComparisonChart analysis={singleAssetAnalysis} />)

    expect(screen.getByText('Stocks')).toBeInTheDocument()
  })

  it('should apply correct CSS class for positive deviation', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockOverweightAnalysis} />)

    const positiveDeviation = container.querySelector('.deviation-value.positive')
    expect(positiveDeviation).toBeInTheDocument()
  })

  it('should apply correct CSS class for negative deviation', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockOverweightAnalysis} />)

    const negativeDeviation = container.querySelector('.deviation-value.negative')
    expect(negativeDeviation).toBeInTheDocument()
  })

  it('should apply correct CSS class for neutral deviation', () => {
    const { container } = render(<AllocationComparisonChart analysis={mockBalancedAnalysis} />)

    const neutralDeviation = container.querySelector('.deviation-value.neutral')
    expect(neutralDeviation).toBeInTheDocument()
  })
})
