// ABOUTME: Test suite for RebalancingSummaryCard component
// ABOUTME: Tests metrics display, priority badges, balanced state, and formatting

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import RebalancingSummaryCard from './RebalancingSummaryCard'
import type { RebalancingAnalysis } from '../api/rebalancing'

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

const mockLowPriorityAnalysis: RebalancingAnalysis = {
  ...mockBalancedAnalysis,
  rebalancing_required: true,
  total_trades_needed: 2,
  estimated_transaction_costs: 50,
  largest_deviation: 3,
  most_overweight: 'CRYPTO',
  most_underweight: 'STOCK'
}

const mockMediumPriorityAnalysis: RebalancingAnalysis = {
  ...mockBalancedAnalysis,
  rebalancing_required: true,
  total_trades_needed: 3,
  estimated_transaction_costs: 100,
  largest_deviation: 7,
  most_overweight: 'CRYPTO',
  most_underweight: 'STOCK'
}

const mockHighPriorityAnalysis: RebalancingAnalysis = {
  ...mockBalancedAnalysis,
  rebalancing_required: true,
  total_trades_needed: 5,
  estimated_transaction_costs: 150,
  largest_deviation: 12,
  most_overweight: 'CRYPTO',
  most_underweight: 'STOCK'
}

describe('RebalancingSummaryCard', () => {
  it('should render card title', () => {
    render(<RebalancingSummaryCard analysis={mockBalancedAnalysis} />)

    expect(screen.getByText('Rebalancing Summary')).toBeInTheDocument()
  })

  it('should show LOW priority badge when deviation is less than 5%', () => {
    render(<RebalancingSummaryCard analysis={mockLowPriorityAnalysis} />)

    expect(screen.getByText('LOW Priority')).toBeInTheDocument()
  })

  it('should show MEDIUM priority badge when deviation is between 5% and 10%', () => {
    render(<RebalancingSummaryCard analysis={mockMediumPriorityAnalysis} />)

    expect(screen.getByText('MEDIUM Priority')).toBeInTheDocument()
  })

  it('should show HIGH priority badge when deviation is 10% or more', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('HIGH Priority')).toBeInTheDocument()
  })

  it('should display balanced state when rebalancing not required', () => {
    render(<RebalancingSummaryCard analysis={mockBalancedAnalysis} />)

    expect(screen.getByText('Portfolio is Well-Balanced')).toBeInTheDocument()
    expect(screen.getByText(/Your current allocation is within target ranges/i)).toBeInTheDocument()
  })

  it('should show next review message when balanced', () => {
    render(<RebalancingSummaryCard analysis={mockBalancedAnalysis} />)

    expect(screen.getByText(/Next review recommended in 3 months/i)).toBeInTheDocument()
  })

  it('should display trades needed metric', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('Trades Needed')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('should display estimated costs metric', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('Est. Costs')).toBeInTheDocument()
    expect(screen.getByText('€150.00')).toBeInTheDocument()
  })

  it('should display largest deviation metric', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('Largest Deviation')).toBeInTheDocument()
    expect(screen.getByText('12.0%')).toBeInTheDocument()
  })

  it('should display most overweight asset', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('Most Overweight')).toBeInTheDocument()
    expect(screen.getByText('CRYPTO')).toBeInTheDocument()
  })

  it('should display most underweight asset', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('Most Underweight')).toBeInTheDocument()
    expect(screen.getByText('STOCK')).toBeInTheDocument()
  })

  it('should display total portfolio value', () => {
    render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    expect(screen.getByText('Total Portfolio')).toBeInTheDocument()
    expect(screen.getByText('€10,000.00')).toBeInTheDocument()
  })

  it('should not show most overweight when null', () => {
    const analysisWithNoOverweight: RebalancingAnalysis = {
      ...mockHighPriorityAnalysis,
      most_overweight: null
    }

    render(<RebalancingSummaryCard analysis={analysisWithNoOverweight} />)

    expect(screen.queryByText('Most Overweight')).not.toBeInTheDocument()
  })

  it('should not show most underweight when null', () => {
    const analysisWithNoUnderweight: RebalancingAnalysis = {
      ...mockHighPriorityAnalysis,
      most_underweight: null
    }

    render(<RebalancingSummaryCard analysis={analysisWithNoUnderweight} />)

    expect(screen.queryByText('Most Underweight')).not.toBeInTheDocument()
  })

  it('should format large portfolio values with commas', () => {
    const largePortfolio: RebalancingAnalysis = {
      ...mockHighPriorityAnalysis,
      total_portfolio_value: 1234567.89
    }

    render(<RebalancingSummaryCard analysis={largePortfolio} />)

    expect(screen.getByText('€1,234,567.89')).toBeInTheDocument()
  })

  it('should format costs with two decimal places', () => {
    const analysisWithDecimals: RebalancingAnalysis = {
      ...mockHighPriorityAnalysis,
      estimated_transaction_costs: 123.456
    }

    render(<RebalancingSummaryCard analysis={analysisWithDecimals} />)

    expect(screen.getByText('€123.46')).toBeInTheDocument()
  })

  it('should format deviation with one decimal place', () => {
    const analysisWithDecimalDeviation: RebalancingAnalysis = {
      ...mockHighPriorityAnalysis,
      largest_deviation: 12.456
    }

    render(<RebalancingSummaryCard analysis={analysisWithDecimalDeviation} />)

    expect(screen.getByText('12.5%')).toBeInTheDocument()
  })

  it('should apply low priority class to badge', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockLowPriorityAnalysis} />)

    const badge = container.querySelector('.priority-badge.low')
    expect(badge).toBeInTheDocument()
  })

  it('should apply medium priority class to badge', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockMediumPriorityAnalysis} />)

    const badge = container.querySelector('.priority-badge.medium')
    expect(badge).toBeInTheDocument()
  })

  it('should apply high priority class to badge', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    const badge = container.querySelector('.priority-badge.high')
    expect(badge).toBeInTheDocument()
  })

  it('should display summary grid when rebalancing required', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    const summaryGrid = container.querySelector('.summary-grid')
    expect(summaryGrid).toBeInTheDocument()
  })

  it('should display balanced state when rebalancing not required', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockBalancedAnalysis} />)

    const balancedState = container.querySelector('.balanced-state')
    expect(balancedState).toBeInTheDocument()
  })

  it('should display checkmark icon when balanced', () => {
    render(<RebalancingSummaryCard analysis={mockBalancedAnalysis} />)

    const checkmark = screen.getByText('✓')
    expect(checkmark).toBeInTheDocument()
  })

  it('should capitalize asset type names', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    const capitalizeElements = container.querySelectorAll('.capitalize')
    expect(capitalizeElements.length).toBeGreaterThan(0)
  })

  it('should display all summary items when rebalancing required', () => {
    const { container } = render(<RebalancingSummaryCard analysis={mockHighPriorityAnalysis} />)

    const summaryItems = container.querySelectorAll('.summary-item')
    expect(summaryItems.length).toBeGreaterThanOrEqual(4)
  })

  it('should show zero trades when not rebalancing', () => {
    render(<RebalancingSummaryCard analysis={mockBalancedAnalysis} />)

    expect(screen.queryByText('Trades Needed')).not.toBeInTheDocument()
  })

  it('should handle zero estimated costs', () => {
    const zeroCoastAnalysis: RebalancingAnalysis = {
      ...mockHighPriorityAnalysis,
      estimated_transaction_costs: 0
    }

    render(<RebalancingSummaryCard analysis={zeroCoastAnalysis} />)

    expect(screen.getByText('€0.00')).toBeInTheDocument()
  })
})
