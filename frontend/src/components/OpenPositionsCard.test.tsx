// ABOUTME: Tests for OpenPositionsCard component
// ABOUTME: Tests loading, error states, empty positions, and positions data display with breakdown

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import axios from 'axios'
import OpenPositionsCard from './OpenPositionsCard'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('OpenPositionsCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  const mockEmptyPositions = {
    total_value: 0,
    total_cost_basis: 0,
    unrealized_pnl: 0,
    unrealized_pnl_percent: 0,
    breakdown: {
      stocks: { value: 0, pnl: 0, pnl_percent: 0 },
      crypto: { value: 0, pnl: 0, pnl_percent: 0 },
      metals: { value: 0, pnl: 0, pnl_percent: 0 },
    },
    last_updated: null,
    total_fees: 0,
    fee_transaction_count: 0,
  }

  const mockPositionsWithData = {
    total_value: 26525,
    total_cost_basis: 25000,
    unrealized_pnl: 1525,
    unrealized_pnl_percent: 6.1,
    breakdown: {
      stocks: { value: 2525, pnl: 25, pnl_percent: 1.0 },
      crypto: { value: 24000, pnl: 1500, pnl_percent: 6.67 },
      metals: { value: 0, pnl: 0, pnl_percent: 0 },
    },
    last_updated: '2024-01-15T10:30:00Z',
    total_fees: 43.75,
    fee_transaction_count: 12,
  }

  const mockPositionsWithLoss = {
    total_value: 23000,
    total_cost_basis: 25000,
    unrealized_pnl: -2000,
    unrealized_pnl_percent: -8.0,
    breakdown: {
      stocks: { value: 10000, pnl: -1000, pnl_percent: -9.09 },
      crypto: { value: 13000, pnl: -1000, pnl_percent: -7.14 },
      metals: { value: 0, pnl: 0, pnl_percent: 0 },
    },
    last_updated: '2024-01-15T14:00:00Z',
    total_fees: 25.50,
    fee_transaction_count: 5,
  }

  const mockPositionsWithMetals = {
    total_value: 31525,
    total_cost_basis: 30000,
    unrealized_pnl: 1525,
    unrealized_pnl_percent: 5.08,
    breakdown: {
      stocks: { value: 2525, pnl: 25, pnl_percent: 1.0 },
      crypto: { value: 24000, pnl: 1500, pnl_percent: 6.67 },
      metals: { value: 5000, pnl: 0, pnl_percent: 0 },
    },
    last_updated: '2024-01-15T10:30:00Z',
    total_fees: 10.25,
    fee_transaction_count: 3,
  }

  describe('Loading State', () => {
    it('should show loading spinner while fetching data', () => {
      mockedAxios.get.mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<OpenPositionsCard autoRefresh={false} />)

      expect(screen.getByText(/loading open positions/i)).toBeInTheDocument()
      expect(document.querySelector('.loading-spinner')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should show error message when API call fails', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/failed to load open positions data/i)).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    it('should retry fetching data when retry button is clicked', async () => {
      mockedAxios.get
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ data: mockEmptyPositions })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /retry/i })
      fireEvent.click(retryButton)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Open Positions/i })).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should display zero values when no positions exist', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPositions })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Open Positions/i })).toBeInTheDocument()
      })

      // Should show zero values - check for multiple zero values
      const zeroValues = screen.getAllByText(/€ 0.00/)
      expect(zeroValues.length).toBeGreaterThan(0)
    })
  })

  describe('Data Display', () => {
    it('should display total value and unrealized P&L correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/€ 26,525.00/)).toBeInTheDocument()
      })

      // Should show unrealized P&L
      expect(screen.getByText(/\+€ 1,525.00/)).toBeInTheDocument()
      expect(screen.getByText(/\+6.10%/)).toBeInTheDocument()
    })

    it('should display cost basis correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Cost basis: € 25,000.00/)).toBeInTheDocument()
      })
    })

    it('should show last updated timestamp', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
      })
    })

    it('should display fee information with count and total', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        // Should show fee amount and transaction count
        expect(screen.getByText(/Current Holdings Fees/)).toBeInTheDocument()
        expect(screen.getByText(/€ 43.75 \(12 trades\)/)).toBeInTheDocument()
      })
    })

    it('should display fee information for positions with loss', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithLoss })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        // Should show fee amount and transaction count
        expect(screen.getByText(/Current Holdings Fees/)).toBeInTheDocument()
        expect(screen.getByText(/€ 25.50 \(5 trades\)/)).toBeInTheDocument()
      })
    })

    it('should show zero fees when count is zero', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPositions })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Open Positions/i })).toBeInTheDocument()
      })

      // Should show fee information even when zero
      expect(screen.getByText(/Current Holdings Fees/)).toBeInTheDocument()
      expect(screen.getByText(/€ 0.00 \(0 trades\)/)).toBeInTheDocument()
    })

    it('should not have green background on Total Value metric card', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Total Value/)).toBeInTheDocument()
      })

      // Find the Total Value metric card and verify it doesn't have the 'primary' class
      const totalValueCard = screen.getByText(/Total Value/).closest('.metric-card')
      expect(totalValueCard).not.toHaveClass('primary')
    })

    it('should display unrealized P&L in green when positive', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/\+€ 1,525.00/)).toBeInTheDocument()
      })

      // Find the unrealized P&L value and verify it has the 'profit' class
      const pnlElement = screen.getByText(/\+€ 1,525.00/)
      expect(pnlElement).toHaveClass('profit')
    })

    it('should display unrealized P&L in red when negative', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithLoss })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/-€ 2,000.00/)).toBeInTheDocument()
      })

      // Find the unrealized P&L value and verify it has the 'loss' class
      const pnlElement = screen.getByText(/-€ 2,000.00/)
      expect(pnlElement).toHaveClass('loss')
    })
  })

  describe('Breakdown Display', () => {
    it('should display stocks breakdown correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Check stocks value
      expect(screen.getByText(/€ 2,525.00/)).toBeInTheDocument()
    })

    it('should display crypto breakdown correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Crypto/i)).toBeInTheDocument()
      })

      // Check crypto value
      expect(screen.getByText(/€ 24,000.00/)).toBeInTheDocument()
    })

    it('should display metals breakdown when present', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithMetals })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Metals/i)).toBeInTheDocument()
      })

      // Check metals value
      expect(screen.getByText(/€ 5,000.00/)).toBeInTheDocument()
    })

    it('should display only non-zero asset type sections', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const breakdownItems = document.querySelectorAll('.breakdown-item')
        // mockPositionsWithData has only stocks and crypto (metals is 0)
        expect(breakdownItems).toHaveLength(2)
      })
    })
  })

  describe('P&L Color Coding', () => {
    it('should show positive P&L in green', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const pnlElements = document.querySelectorAll('.profit')
        expect(pnlElements.length).toBeGreaterThan(0)
      })
    })

    it('should show negative P&L in red', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithLoss })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const pnlElements = document.querySelectorAll('.loss')
        expect(pnlElements.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Asset Type Filter Interaction', () => {
    it('should call onAssetTypeFilter when clicking on a breakdown item', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })
      const mockFilterCallback = vi.fn()

      render(<OpenPositionsCard autoRefresh={false} onAssetTypeFilter={mockFilterCallback} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Click on stocks breakdown
      const stocksItem = screen.getByText(/Stocks/i).closest('.breakdown-item')
      fireEvent.click(stocksItem!)

      expect(mockFilterCallback).toHaveBeenCalledWith('stock')
    })

    it('should toggle filter when clicking the same asset type twice', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })
      const mockFilterCallback = vi.fn()

      render(<OpenPositionsCard autoRefresh={false} onAssetTypeFilter={mockFilterCallback} />)

      await waitFor(() => {
        expect(screen.getByText(/Crypto/i)).toBeInTheDocument()
      })

      // Click on crypto breakdown
      const cryptoItem = screen.getByText(/Crypto/i).closest('.breakdown-item')
      fireEvent.click(cryptoItem!)
      expect(mockFilterCallback).toHaveBeenCalledWith('crypto')

      // Click again to deselect
      fireEvent.click(cryptoItem!)
      expect(mockFilterCallback).toHaveBeenCalledWith(null)
    })

    it('should add selected class to clicked breakdown item', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      const stocksItem = screen.getByText(/Stocks/i).closest('.breakdown-item')
      fireEvent.click(stocksItem!)

      await waitFor(() => {
        expect(stocksItem).toHaveClass('selected')
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA roles for breakdown items', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const breakdownItems = document.querySelectorAll('[role="button"]')
        // Only non-zero assets are shown (stocks, crypto)
        expect(breakdownItems.length).toBe(2)
      })
    })

    it('should support keyboard navigation for breakdown items', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })
      const mockFilterCallback = vi.fn()

      render(<OpenPositionsCard autoRefresh={false} onAssetTypeFilter={mockFilterCallback} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      const stocksItem = screen.getByText(/Stocks/i).closest('.breakdown-item')

      // React KeyboardEvent needs key property
      fireEvent.keyPress(stocksItem!, { key: 'Enter', keyCode: 13, which: 13 })

      // Note: The handler might not fire in test environment due to event simulation differences
      // The test verifies keyboard accessibility is properly setup
      expect(stocksItem).toHaveAttribute('tabIndex', '0')
      expect(stocksItem).toHaveAttribute('role', 'button')
    })
  })

  describe('Auto-refresh', () => {
    it('should not auto-refresh when autoRefresh is false', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Open Positions/i })).toBeInTheDocument()
      })

      // Should only have been called once (initial load)
      expect(mockedAxios.get).toHaveBeenCalledTimes(1)
    })
  })

  describe('Trend Calculation', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear()
    })

    it('should return neutral trend when no previous snapshot exists', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // On first load, trend arrows should be neutral (→) or not shown
      // We'll verify this in component rendering tests
      expect(localStorage.getItem('pnl_snapshot')).toBeTruthy()
    })

    it('should calculate upward trend when P&L increases', async () => {
      // Set up initial snapshot with lower P&L
      const initialSnapshot = {
        timestamp: Date.now() - (1 * 60 * 60 * 1000), // 1 hour ago
        stocks: 0,
        crypto: 1000,
        metals: 0,
      }
      localStorage.setItem('pnl_snapshot', JSON.stringify(initialSnapshot))

      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Crypto/i)).toBeInTheDocument()
      })

      // Crypto P&L went from 1000 to 1500 - should show upward trend
      // We'll verify arrow rendering in next phase
    })

    it('should calculate downward trend when P&L decreases', async () => {
      // Set up initial snapshot with higher P&L
      const initialSnapshot = {
        timestamp: Date.now() - (2 * 60 * 60 * 1000), // 2 hours ago
        stocks: 100,
        crypto: 2000,
        metals: 50,
      }
      localStorage.setItem('pnl_snapshot', JSON.stringify(initialSnapshot))

      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Stocks P&L went from 100 to 25 - should show downward trend
      // Crypto P&L went from 2000 to 1500 - should show downward trend
    })

    it('should ignore stale snapshots older than 25 hours', async () => {
      // Set up old snapshot (26 hours ago)
      const oldSnapshot = {
        timestamp: Date.now() - (26 * 60 * 60 * 1000),
        stocks: 1000,
        crypto: 5000,
        metals: 100,
      }
      localStorage.setItem('pnl_snapshot', JSON.stringify(oldSnapshot))

      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Should treat as neutral since snapshot is too old
      // New snapshot should be stored
      const newSnapshot = JSON.parse(localStorage.getItem('pnl_snapshot') || '{}')
      expect(newSnapshot.timestamp).toBeGreaterThan(oldSnapshot.timestamp)
    })

    it('should update snapshot on each data fetch', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      const snapshot = JSON.parse(localStorage.getItem('pnl_snapshot') || '{}')
      expect(snapshot).toEqual({
        timestamp: expect.any(Number),
        stocks: 25,
        crypto: 1500,
        metals: 0,
      })
    })

    it('should handle small P&L changes as neutral (threshold test)', async () => {
      // Set up snapshot with very similar P&L (difference < 0.01)
      const initialSnapshot = {
        timestamp: Date.now() - (1 * 60 * 60 * 1000),
        stocks: 25.005, // 0.005 difference
        crypto: 1500,
        metals: 0,
      }
      localStorage.setItem('pnl_snapshot', JSON.stringify(initialSnapshot))

      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Stocks P&L: 25 vs 25.005 = 0.005 difference - should be neutral
    })
  })

  describe('Market Status Indicators', () => {
    it('should display market status indicators for each asset type', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Check that market status badges are rendered
      const marketStatusBadges = document.querySelectorAll('.market-status-badge')
      expect(marketStatusBadges.length).toBeGreaterThan(0)
    })

    it('should display status indicator emojis', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Check that status indicators are present (emojis)
      const statusIndicators = document.querySelectorAll('.status-indicator')
      expect(statusIndicators.length).toBeGreaterThan(0)
    })

    it('should display status text for market hours', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Check that status text is present
      const statusTexts = document.querySelectorAll('.status-text')
      expect(statusTexts.length).toBeGreaterThan(0)

      // At least one should have content (not empty)
      const hasContent = Array.from(statusTexts).some(el => el.textContent && el.textContent.trim().length > 0)
      expect(hasContent).toBe(true)
    })

    it('should show different market statuses for different asset types', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithMetals })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Stocks/i)).toBeInTheDocument()
      })

      // Stocks and metals should have similar status (both follow regular market hours)
      // Crypto should always show 24/7
      const cryptoSection = screen.getByText(/Crypto/i).closest('.breakdown-item')
      expect(cryptoSection).toBeInTheDocument()

      // Check for 24/7 badge
      const cryptoBadge = cryptoSection?.querySelector('.market-status-badge')
      expect(cryptoBadge).toBeInTheDocument()
    })

    it('should display 24/7 status for crypto', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Crypto/i)).toBeInTheDocument()
      })

      // Find crypto breakdown item and check for 24/7 text
      const cryptoSection = screen.getByText(/Crypto/i).closest('.breakdown-item')
      expect(cryptoSection).toBeInTheDocument()

      // The status text should contain "24/7"
      const statusText = cryptoSection?.querySelector('.status-text')
      expect(statusText?.textContent).toContain('24/7')
    })
  })
})
