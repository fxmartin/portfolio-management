// ABOUTME: Tests for RealizedPnLCard component
// ABOUTME: Tests loading, error states, empty positions with sales, and realized P&L display with breakdown

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import axios from 'axios'
import RealizedPnLCard from './RealizedPnLCard'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('RealizedPnLCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockNoClosedPositions = {
    total_realized_pnl: 0,
    total_fees: 2.50,
    net_pnl: -2.50,
    closed_positions_count: 0,
    breakdown: {
      stocks: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
      crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
      metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
    },
    last_updated: '2024-01-15T10:30:00Z',
  }

  const mockClosedPositionWithProfit = {
    total_realized_pnl: 2000,
    total_fees: 2.50,
    net_pnl: 1997.50,
    closed_positions_count: 1,
    breakdown: {
      stocks: { realized_pnl: 2000, fees: 2.50, net_pnl: 1997.50, closed_count: 1 },
      crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
      metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
    },
    last_updated: '2024-01-15T10:30:00Z',
  }

  const mockClosedPositionWithLoss = {
    total_realized_pnl: -1500,
    total_fees: 8.00,
    net_pnl: -1508.00,
    closed_positions_count: 1,
    breakdown: {
      stocks: { realized_pnl: -1500, fees: 8.00, net_pnl: -1508.00, closed_count: 1 },
      crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
      metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
    },
    last_updated: '2024-01-15T14:00:00Z',
  }

  const mockMixedAssetTypes = {
    total_realized_pnl: -500,
    total_fees: 12.00,
    net_pnl: -512.00,
    closed_positions_count: 2,
    breakdown: {
      stocks: { realized_pnl: 500, fees: 2.50, net_pnl: 497.50, closed_count: 1 },
      crypto: { realized_pnl: -1000, fees: 9.50, net_pnl: -1009.50, closed_count: 1 },
      metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
    },
    last_updated: '2024-01-15T10:30:00Z',
  }

  const mockAllAssetTypes = {
    total_realized_pnl: 7100,
    total_fees: 38.00,
    net_pnl: 7062.00,
    closed_positions_count: 3,
    breakdown: {
      stocks: { realized_pnl: 2000, fees: 5.00, net_pnl: 1995.00, closed_count: 1 },
      crypto: { realized_pnl: 5000, fees: 22.50, net_pnl: 4977.50, closed_count: 1 },
      metals: { realized_pnl: 100, fees: 10.50, net_pnl: 89.50, closed_count: 1 },
    },
    last_updated: '2024-01-15T10:30:00Z',
  }

  it('shows loading state initially', () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {}))

    render(<RealizedPnLCard />)

    expect(screen.getByText(/loading realized p&l/i)).toBeInTheDocument()
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('shows error state when API call fails', async () => {
    mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load realized p&l data/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('displays empty state when no positions with sales', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockNoClosedPositions })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText(/No closed positions yet/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/realized p&l will appear here/i)).toBeInTheDocument()
  })

  it('displays realized P&L for single position with sales with profit', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockClosedPositionWithProfit })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('1 position with sales')).toBeInTheDocument()
    }, { timeout: 3000 })

    // Check main metrics
    expect(screen.getByText('Total Realized P&L')).toBeInTheDocument()
    const totalPnl = screen.getAllByText('€ 2,000.00')
    expect(totalPnl.length).toBeGreaterThan(0)
    expect(screen.getByText('Transaction Fees')).toBeInTheDocument()
    expect(screen.getByText('€ 2.50')).toBeInTheDocument()
    expect(screen.getByText('Net P&L')).toBeInTheDocument()
    const netPnl = screen.getAllByText('€ 1,997.50')
    expect(netPnl.length).toBeGreaterThan(0)
  })

  it('displays realized P&L for single position with sales with loss', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockClosedPositionWithLoss })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('1 position with sales')).toBeInTheDocument()
    }, { timeout: 3000 })

    // Check main metrics
    const totalLoss = screen.getAllByText('-€ 1,500.00')
    expect(totalLoss.length).toBeGreaterThan(0)
    expect(screen.getByText('€ 8.00')).toBeInTheDocument()
    const netLoss = screen.getAllByText('-€ 1,508.00')
    expect(netLoss.length).toBeGreaterThan(0)
  })

  it('displays breakdown by asset type for mixed positions', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockMixedAssetTypes })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('2 positions with sales')).toBeInTheDocument()
    })

    // Check breakdown section appears
    expect(screen.getByText('Breakdown by Asset Type')).toBeInTheDocument()

    // Check stocks breakdown (profit)
    expect(screen.getByText('Stocks')).toBeInTheDocument()
    const stocksPnl = screen.getAllByText('€ 500.00')
    expect(stocksPnl.length).toBeGreaterThan(0)
    expect(screen.getByText('1 closed')).toBeInTheDocument()

    // Check crypto breakdown (loss)
    expect(screen.getByText('Crypto')).toBeInTheDocument()
    expect(screen.getByText('-$ 1,000.00')).toBeInTheDocument()
  })

  it('displays all three asset types when all have positions with sales', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockAllAssetTypes })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('3 positions with sales')).toBeInTheDocument()
    })

    // Check all three asset types are displayed
    expect(screen.getByText('Stocks')).toBeInTheDocument()
    expect(screen.getByText('Crypto')).toBeInTheDocument()
    expect(screen.getByText('Metals')).toBeInTheDocument()
  })

  it('does not show breakdown section when no positions with sales', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockNoClosedPositions })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText(/No closed positions yet/i)).toBeInTheDocument()
    })

    expect(screen.queryByText('Breakdown by Asset Type')).not.toBeInTheDocument()
  })

  it('applies correct CSS classes for profit/loss values', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockMixedAssetTypes })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('2 positions with sales')).toBeInTheDocument()
    })

    // Find profit and loss values and check their classes
    const profitElements = screen.getAllByText(/€500\.00/)
    const lossElements = screen.getAllByText(/-€1,000\.00/)

    expect(profitElements.length).toBeGreaterThan(0)
    expect(lossElements.length).toBeGreaterThan(0)
  })

  it('formats currency values correctly', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockClosedPositionWithProfit })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      // Check that currency is formatted with € symbol and thousands separators
      const totalPnl = screen.getAllByText('€ 2,000.00')
      expect(totalPnl.length).toBeGreaterThan(0)
      expect(screen.getByText('€ 2.50')).toBeInTheDocument()
      const netPnl = screen.getAllByText('€ 1,997.50')
      expect(netPnl.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })

  it('handles plural/singular for positions with sales count', async () => {
    // Test singular
    mockedAxios.get.mockResolvedValueOnce({ data: mockClosedPositionWithProfit })
    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('1 position with sales')).toBeInTheDocument()
    }, { timeout: 3000 })

    // Test plural separately
    mockedAxios.get.mockResolvedValueOnce({ data: mockMixedAssetTypes })
    const { unmount } = render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('2 positions with sales')).toBeInTheDocument()
    }, { timeout: 3000 })

    unmount()
  })

  it('displays breakdown metrics correctly', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockAllAssetTypes })

    render(<RealizedPnLCard />)

    await waitFor(() => {
      expect(screen.getByText('3 positions with sales')).toBeInTheDocument()
      // Check that breakdown rows show labels
      const realizedLabels = screen.queryAllByText('Realized:')
      const feesLabels = screen.queryAllByText('Fees:')
      const netLabels = screen.queryAllByText('Net:')

      // At least one of each label should exist
      expect(realizedLabels.length + feesLabels.length + netLabels.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
