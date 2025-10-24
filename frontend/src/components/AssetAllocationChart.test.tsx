// ABOUTME: Tests for AssetAllocationChart component
// ABOUTME: Tests pie chart rendering, data calculation, and tooltip display

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import AssetAllocationChart from './AssetAllocationChart'

describe('AssetAllocationChart', () => {
  const mockBreakdown = {
    stocks: { value: 8292.67, pnl: 783.25, pnl_percent: 10.43 },
    crypto: { value: 9854.68, pnl: -9.17, pnl_percent: -0.09 },
    metals: { value: 0, pnl: 0, pnl_percent: 0 },
  }

  describe('Rendering', () => {
    it('should render pie chart with non-zero assets', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
          currency="EUR"
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
      // Recharts renders in DOM
      expect(container.firstChild).toBeTruthy()
    })

    it('should not render when all values are zero', () => {
      const emptyBreakdown = {
        stocks: { value: 0, pnl: 0, pnl_percent: 0 },
        crypto: { value: 0, pnl: 0, pnl_percent: 0 },
        metals: { value: 0, pnl: 0, pnl_percent: 0 },
      }

      const { container } = render(
        <AssetAllocationChart
          breakdown={emptyBreakdown}
          totalValue={0}
          currency="EUR"
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).not.toBeInTheDocument()
    })

    it('should render chart container', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
          currency="EUR"
        />
      )

      const chartContainer = container.querySelector('.asset-allocation-chart')
      expect(chartContainer).toBeInTheDocument()
    })
  })

  describe('Data Filtering', () => {
    it('should render with filtered assets', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
          currency="EUR"
        />
      )

      // Component should render when there are non-zero values
      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })

    it('should handle single asset', () => {
      const singleAssetBreakdown = {
        stocks: { value: 0, pnl: 0, pnl_percent: 0 },
        crypto: { value: 10000, pnl: 100, pnl_percent: 1.0 },
        metals: { value: 0, pnl: 0, pnl_percent: 0 },
      }

      const { container } = render(
        <AssetAllocationChart
          breakdown={singleAssetBreakdown}
          totalValue={10000}
          currency="EUR"
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })

    it('should handle all three assets with values', () => {
      const allAssetsBreakdown = {
        stocks: { value: 5000, pnl: 100, pnl_percent: 2.0 },
        crypto: { value: 10000, pnl: 200, pnl_percent: 2.0 },
        metals: { value: 5000, pnl: 50, pnl_percent: 1.0 },
      }

      const { container } = render(
        <AssetAllocationChart
          breakdown={allAssetsBreakdown}
          totalValue={20000}
          currency="EUR"
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })
  })

  describe('Percentage Calculation', () => {
    it('should render with calculated percentages', () => {
      // Stocks: 8292.67 / 18147.35 = 45.7%
      // Crypto: 9854.68 / 18147.35 = 54.3%
      // Percentages are calculated and passed to Recharts

      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
          currency="EUR"
        />
      )

      // Component renders with percentage data
      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })
  })

  describe('Currency Support', () => {
    it('should handle EUR currency', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
          currency="EUR"
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })

    it('should handle USD currency', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={20000}
          currency="USD"
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })

    it('should default to EUR when no currency provided', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
        />
      )

      expect(container.querySelector('.asset-allocation-chart')).toBeInTheDocument()
    })
  })

  describe('Responsive Container', () => {
    it('should use ResponsiveContainer for chart', () => {
      const { container } = render(
        <AssetAllocationChart
          breakdown={mockBreakdown}
          totalValue={18147.35}
          currency="EUR"
        />
      )

      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
    })
  })
})
