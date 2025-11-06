// ABOUTME: Tests for PortfolioSummary component
// ABOUTME: Tests loading, error states, empty portfolio, and portfolio data display

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import axios from 'axios'
import PortfolioSummary, { PortfolioSummaryData } from './PortfolioSummary'
import { SettingsProvider } from '../contexts/SettingsContext'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

// Test wrapper with SettingsProvider
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <SettingsProvider>{children}</SettingsProvider>
}

// Custom render function with TestWrapper
const renderWithProviders = (ui: React.ReactElement) => {
  return render(ui, { wrapper: TestWrapper })
}

describe('PortfolioSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock settings API calls by default
    mockedAxios.get.mockImplementation((url: string) => {
      if (url.includes('/api/settings/category/display')) {
        return Promise.resolve({
          data: [
            { key: 'base_currency', value: 'EUR', category: 'display' },
            { key: 'date_format', value: 'YYYY-MM-DD', category: 'display' },
            { key: 'number_format', value: 'en-US', category: 'display' },
          ],
        })
      }
      if (url.includes('/api/settings/category/system')) {
        return Promise.resolve({
          data: [
            { key: 'crypto_price_refresh_seconds', value: '60', category: 'system' },
            { key: 'stock_price_refresh_seconds', value: '120', category: 'system' },
            { key: 'cache_ttl_hours', value: '1', category: 'system' },
          ],
        })
      }
      // Let other calls be handled by test-specific mocks
      return Promise.reject(new Error('Unmocked URL: ' + url))
    })
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  const mockEmptyPortfolio: PortfolioSummaryData = {
    total_value: 0,
    cash_balances: {},
    total_cash: 0,
    total_investment_value: 0,
    total_cost_basis: 0,
    total_pnl: 0,
    total_pnl_percent: 0,
    unrealized_pnl: 0,
    realized_pnl: 0,
    day_change: 0,
    day_change_percent: 0,
    positions_count: 0,
    last_updated: null,
  }

  const mockPortfolioWithData: PortfolioSummaryData = {
    total_value: 50000,
    cash_balances: {
      USD: 10000,
      EUR: 5000,
    },
    total_cash: 15000,
    total_investment_value: 35000,
    total_cost_basis: 30000,
    total_pnl: 5000,
    total_pnl_percent: 16.67,
    unrealized_pnl: 3500,
    realized_pnl: 1500,
    day_change: 250,
    day_change_percent: 0.5,
    positions_count: 5,
    last_updated: '2024-01-15T10:30:00Z',
  }

  const mockPortfolioWithLoss: PortfolioSummaryData = {
    total_value: 25000,
    cash_balances: {
      USD: 5000,
    },
    total_cash: 5000,
    total_investment_value: 20000,
    total_cost_basis: 25000,
    total_pnl: -5000,
    total_pnl_percent: -20.0,
    unrealized_pnl: -5000,
    realized_pnl: 0,
    day_change: -500,
    day_change_percent: -1.96,
    positions_count: 3,
    last_updated: '2024-01-15T14:00:00Z',
  }

  describe('Loading State', () => {
    it('should show loading spinner while fetching data', () => {
      mockedAxios.get.mockImplementation(() => new Promise(() => {})) // Never resolves

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      expect(screen.getByText(/loading portfolio/i)).toBeInTheDocument()
      expect(document.querySelector('.loading-spinner')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should show error message when API call fails', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/failed to load portfolio data/i)).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    it('should retry fetching data when retry button is clicked', async () => {
      mockedAxios.get
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/failed to load portfolio data/i)).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /retry/i })
      retryButton.click()

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty Portfolio', () => {
    it('should display zero values for empty portfolio', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Check total value - use getAllByText since there might be multiple zero values
      const zeroElements = screen.getAllByText('€ 0.00')
      expect(zeroElements.length).toBeGreaterThan(0)

      // Check positions count
      expect(screen.getByText(/no positions/i)).toBeInTheDocument()

      // Cash balances section should not be visible for empty portfolio
      expect(screen.queryByText(/cash balances/i)).not.toBeInTheDocument()
    })

    it('should not show day change for zero change', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      })

      // Day change should not be displayed when it's 0
      expect(screen.queryByText(/today/i)).not.toBeInTheDocument()
    })
  })

  describe('Portfolio with Data', () => {
    it('should display total portfolio value correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        const values = screen.getAllByText('€ 50,000.00')
        expect(values.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('should display total P&L with correct styling for profit', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        const pnlElements = screen.getAllByText('€ 5,000.00')
        expect(pnlElements.length).toBeGreaterThan(0)
      }, { timeout: 3000 })

      // Check that profit class is applied
      const pnlElements = screen.getAllByText('€ 5,000.00')
      expect(pnlElements.some(el => el.className.includes('profit'))).toBe(true)
    })

    it('should display unrealized and realized P&L separately', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        const unrealizedLabels = screen.getAllByText(/unrealized p&l/i)
        const realizedLabels = screen.getAllByText(/realized p&l/i)
        expect(unrealizedLabels.length).toBeGreaterThan(0)
        expect(realizedLabels.length).toBeGreaterThan(0)
      }, { timeout: 3000 })

      const unrealizedValues = screen.getAllByText('€ 3,500.00')
      const realizedValues = screen.getAllByText('€ 1,500.00')
      expect(unrealizedValues.length).toBeGreaterThan(0) // Unrealized
      expect(realizedValues.length).toBeGreaterThan(0) // Realized
    })

    it('should display positions count correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/5 positions/i)).toBeInTheDocument()
      })
    })

    it('should display single position count without plural', async () => {
      const singlePositionData = {
        ...mockPortfolioWithData,
        positions_count: 1,
      }
      mockedAxios.get.mockResolvedValueOnce({ data: singlePositionData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/1 position$/i)).toBeInTheDocument()
      })
    })

    it('should display day change when non-zero', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/today/i)).toBeInTheDocument()
      })

      // Day change should include + sign, amount and percentage
      expect(screen.getByText(/\+€ 250\.00/)).toBeInTheDocument()
      expect(screen.getByText(/\+0\.50%/)).toBeInTheDocument()
    })

    it('should display last updated time', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/updated/i)).toBeInTheDocument()
      })
    })
  })

  describe('Cash Balances', () => {
    it('should display cash balances section with multiple currencies', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/cash balances/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Check currency codes
      expect(screen.getByText('USD')).toBeInTheDocument()
      expect(screen.getByText('EUR')).toBeInTheDocument()

      // Check amounts - these might appear multiple times, so just verify they exist
      const amounts = screen.getAllByText(/€ 10,000\.00|€ 5,000\.00/)
      expect(amounts.length).toBeGreaterThan(0)
    })

    it('should display total cash amount', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/total cash/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      const cashValues = screen.getAllByText(/€ 15,000\.00/)
      expect(cashValues.length).toBeGreaterThan(0)
    })

    it('should not display cash balances section when no cash', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      })

      expect(screen.queryByText(/cash balances/i)).not.toBeInTheDocument()
    })
  })

  describe('Investment Breakdown', () => {
    it('should display investment breakdown with all values', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/investment value/i)).toBeInTheDocument()
        expect(screen.getByText(/cost basis/i)).toBeInTheDocument()
        expect(screen.getByText(/total portfolio/i)).toBeInTheDocument()
      })

      // Check values in breakdown
      expect(screen.getByText('€ 35,000.00')).toBeInTheDocument() // Investment value
      expect(screen.getByText('€ 30,000.00')).toBeInTheDocument() // Cost basis
    })
  })

  describe('Loss Scenarios', () => {
    it('should display negative P&L with loss styling', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithLoss })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      })

      // Check for negative values
      const lossElements = screen.getAllByText(/-€ 5,000\.00/)
      expect(lossElements.length).toBeGreaterThan(0)

      // Check that loss class is applied
      expect(lossElements.some(el => el.className.includes('loss'))).toBe(true)
    })

    it('should display negative day change correctly', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithLoss })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/today/i)).toBeInTheDocument()
      })

      // Day change should show negative sign
      expect(screen.getByText(/-€ 500\.00/)).toBeInTheDocument()
      expect(screen.getByText(/-1\.96%/)).toBeInTheDocument()
    })
  })

  describe('API Integration', () => {
    it('should call correct API endpoint', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/portfolio/summary')
        )
      })
    })

    it('should respect custom API URL from environment', async () => {
      const originalEnv = import.meta.env.VITE_API_URL
      import.meta.env.VITE_API_URL = 'http://custom-api:9000'

      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          'http://custom-api:9000/api/portfolio/summary'
        )
      }, { timeout: 3000 })

      import.meta.env.VITE_API_URL = originalEnv
    })
  })

  describe('Refresh Functionality', () => {
    it('should call onRefresh callback after successful data fetch', async () => {
      const onRefresh = vi.fn()
      mockedAxios.get.mockResolvedValueOnce({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary onRefresh={onRefresh} />)

      await waitFor(() => {
        expect(onRefresh).toHaveBeenCalledTimes(1)
      })
    })

    it('should not call onRefresh when API call fails', async () => {
      const onRefresh = vi.fn()
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<PortfolioSummary onRefresh={onRefresh} />)

      await waitFor(() => {
        expect(screen.getByText(/failed to load portfolio data/i)).toBeInTheDocument()
      })

      expect(onRefresh).not.toHaveBeenCalled()
    })

    it('should auto-refresh when autoRefresh is enabled', async () => {
      vi.useFakeTimers()
      mockedAxios.get.mockResolvedValue({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={true} refreshInterval={5000} />)

      // Initial fetch
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1)
      })

      // Fast-forward time
      vi.advanceTimersByTime(5000)

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(2)
      })

      vi.useRealTimers()
    })

    it('should not auto-refresh when autoRefresh is disabled', async () => {
      vi.useFakeTimers()
      mockedAxios.get.mockResolvedValue({ data: mockEmptyPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      // Initial fetch
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(1)
      })

      // Fast-forward time
      vi.advanceTimersByTime(60000)

      // Should still only have 1 call
      expect(mockedAxios.get).toHaveBeenCalledTimes(1)

      vi.useRealTimers()
    })
  })

  describe('Edge Cases', () => {
    it('should handle null last_updated gracefully', async () => {
      const dataWithNullUpdate = {
        ...mockPortfolioWithData,
        last_updated: null,
      }
      mockedAxios.get.mockResolvedValueOnce({ data: dataWithNullUpdate })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Should not crash, and "Updated" text should not appear
      expect(screen.queryByText(/updated/i)).not.toBeInTheDocument()
    })

    it('should handle very large numbers correctly', async () => {
      const largePortfolio = {
        ...mockPortfolioWithData,
        total_value: 1234567.89,
        total_pnl: 987654.32,
      }
      mockedAxios.get.mockResolvedValueOnce({ data: largePortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        const largeValues = screen.getAllByText('€ 1,234,567.89')
        expect(largeValues.length).toBeGreaterThan(0)
      }, { timeout: 3000 })
    })

    it('should handle zero P&L as neutral', async () => {
      const neutralPortfolio = {
        ...mockPortfolioWithData,
        total_pnl: 0,
        total_pnl_percent: 0,
        unrealized_pnl: 0,
        realized_pnl: 0,
      }
      mockedAxios.get.mockResolvedValueOnce({ data: neutralPortfolio })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Should display $0.00 for P&L values
      const zeroElements = screen.getAllByText('€ 0.00')
      expect(zeroElements.length).toBeGreaterThan(0)
    })

    it('should handle missing cash_balances object', async () => {
      const dataWithoutCash = {
        ...mockPortfolioWithData,
        cash_balances: {},
      }
      mockedAxios.get.mockResolvedValueOnce({ data: dataWithoutCash })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      }, { timeout: 3000 })

      // Should not show cash balances section
      expect(screen.queryByText(/cash balances/i)).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading structure', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockPortfolioWithData })

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        const headings = screen.getAllByRole('heading')
        expect(headings.length).toBeGreaterThan(0)
      }, { timeout: 3000 })

      expect(screen.getByRole('heading', { name: /portfolio summary/i })).toBeInTheDocument()
    })

    it('should render retry button with proper role', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<PortfolioSummary autoRefresh={false} />)

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /retry/i })
        expect(retryButton).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('Component Lifecycle', () => {
    it('should clean up interval on unmount when autoRefresh is enabled', async () => {
      const clearIntervalSpy = vi.spyOn(global, 'clearInterval')

      mockedAxios.get.mockResolvedValue({ data: mockEmptyPortfolio })

      const { unmount } = renderWithProviders(<PortfolioSummary autoRefresh={true} />)

      await waitFor(() => {
        expect(screen.getByText(/portfolio summary/i)).toBeInTheDocument()
      })

      unmount()

      expect(clearIntervalSpy).toHaveBeenCalled()

      clearIntervalSpy.mockRestore()
    })
  })
})
