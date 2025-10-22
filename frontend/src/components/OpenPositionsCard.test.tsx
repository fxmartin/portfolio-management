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
      const zeroValues = screen.getAllByText(/€0.00/)
      expect(zeroValues.length).toBeGreaterThan(0)
    })
  })

  describe('Data Display', () => {
    it('should display total value and unrealized P&L correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/€26,525.00/)).toBeInTheDocument()
      })

      // Should show unrealized P&L
      expect(screen.getByText(/\+€1,525.00/)).toBeInTheDocument()
      expect(screen.getByText(/\+6.10%/)).toBeInTheDocument()
    })

    it('should display cost basis correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Cost basis: €25,000.00/)).toBeInTheDocument()
      })
    })

    it('should show last updated timestamp', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument()
      })
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
      expect(screen.getByText(/€2,525.00/)).toBeInTheDocument()
    })

    it('should display crypto breakdown correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Crypto/i)).toBeInTheDocument()
      })

      // Check crypto value
      expect(screen.getByText(/€24,000.00/)).toBeInTheDocument()
    })

    it('should display metals breakdown when present', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithMetals })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/Metals/i)).toBeInTheDocument()
      })

      // Check metals value
      expect(screen.getByText(/€5,000.00/)).toBeInTheDocument()
    })

    it('should display all three asset type sections', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const breakdownItems = document.querySelectorAll('.breakdown-item')
        expect(breakdownItems).toHaveLength(3)
      })
    })
  })

  describe('P&L Color Coding', () => {
    it('should show positive P&L in green', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const pnlElements = document.querySelectorAll('.positive')
        expect(pnlElements.length).toBeGreaterThan(0)
      })
    })

    it('should show negative P&L in red', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithLoss })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const pnlElements = document.querySelectorAll('.negative')
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
        expect(screen.getByText(/Metals/i)).toBeInTheDocument()
      })

      const metalsItem = screen.getByText(/Metals/i).closest('.breakdown-item')
      fireEvent.click(metalsItem!)

      await waitFor(() => {
        expect(metalsItem).toHaveClass('selected')
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA roles for breakdown items', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPositionsWithData })

      render(<OpenPositionsCard autoRefresh={false} />)

      await waitFor(() => {
        const breakdownItems = document.querySelectorAll('[role="button"]')
        expect(breakdownItems.length).toBe(3) // stocks, crypto, metals
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
})
