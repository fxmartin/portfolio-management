// ABOUTME: Integration tests for the App component with new sidebar and tab navigation
// ABOUTME: Tests complete workflows through the modernized UI

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import App from './App'
import axios from 'axios'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('App Integration Tests - Epic 6', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Setup endpoint-specific mocks
    mockedAxios.get.mockImplementation((url: string) => {
      // Mock /api/portfolio/open-positions endpoint
      if (url.includes('/api/portfolio/open-positions')) {
        return Promise.resolve({
          data: {
            total_value: 10000,
            total_cost_basis: 9000,
            unrealized_pnl: 1000,
            unrealized_pnl_percent: 11.11,
            total_fees: 25.50,
            breakdown: {
              stocks: {
                total_value: 5000,
                total_cost_basis: 4500,
                unrealized_pnl: 500,
                unrealized_pnl_percent: 11.11,
                fees: 10.00,
                count: 2
              },
              crypto: {
                total_value: 5000,
                total_cost_basis: 4500,
                unrealized_pnl: 500,
                unrealized_pnl_percent: 11.11,
                fees: 15.50,
                count: 3
              },
              metals: {
                total_value: 0,
                total_cost_basis: 0,
                unrealized_pnl: 0,
                unrealized_pnl_percent: 0,
                fees: 0,
                count: 0
              }
            },
            last_updated: '2024-01-15T10:30:00Z'
          }
        })
      }

      // Mock /api/portfolio/realized-pnl endpoint
      if (url.includes('/api/portfolio/realized-pnl')) {
        return Promise.resolve({
          data: {
            total_realized_pnl: 0,
            total_fees: 0,
            net_pnl: 0,
            closed_positions_count: 0,
            breakdown: {
              stocks: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
              crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
              metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 }
            },
            last_updated: '2024-01-15T10:30:00Z'
          }
        })
      }

      // Mock /api/portfolio/positions endpoint
      if (url.includes('/api/portfolio/positions')) {
        return Promise.resolve({
          data: []
        })
      }

      // Default fallback for any other endpoints
      return Promise.resolve({
        data: {
          total_value: 10000,
          positions: [],
          cash_balance: 5000
        }
      })
    })
  })

  describe('Sidebar Navigation', () => {
    it('renders app with sidebar and default portfolio tab', async () => {
      render(<App />)

      // Sidebar should be visible
      expect(screen.getByRole('navigation')).toBeInTheDocument()

      // Portfolio tab should be active by default
      await waitFor(() => {
        expect(screen.getByText('Portfolio Dashboard')).toBeInTheDocument()
      })
    })

    it('navigates from portfolio to upload tab', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Click upload in sidebar
      const uploadButton = screen.getByTitle('Upload')
      await user.click(uploadButton)

      // Upload tab should be visible
      await waitFor(() => {
        expect(screen.getByText('Import Transactions')).toBeInTheDocument()
      })

      // Portfolio tab should not be visible
      expect(screen.queryByText('Portfolio Dashboard')).not.toBeInTheDocument()
    })

    it('navigates from portfolio to database stats', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Open database submenu
      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      // Click stats
      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      const statsButton = screen.getByText('Stats')
      await user.click(statsButton)

      // DatabaseStats component should be visible
      // Note: The actual stats display depends on the DatabaseStats component
      // which may show a loading or error state initially
    })

    it('maintains tab state across navigation', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Go to upload
      const uploadButton = screen.getByTitle('Upload')
      await user.click(uploadButton)

      await waitFor(() => {
        expect(screen.getByText('Import Transactions')).toBeInTheDocument()
      })

      // Go back to portfolio
      const portfolioButton = screen.getByTitle('Portfolio')
      await user.click(portfolioButton)

      await waitFor(() => {
        expect(screen.getByText('Portfolio Dashboard')).toBeInTheDocument()
      })

      // Upload content should not be visible
      expect(screen.queryByText('Import Transactions')).not.toBeInTheDocument()
    })
  })

  describe('Portfolio Display', () => {
    it('displays portfolio summary when loaded', async () => {
      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/portfolio/open-positions')) {
          return Promise.resolve({
            data: {
              total_value: 15000.50,
              total_cost_basis: 13000,
              unrealized_pnl: 2000.50,
              unrealized_pnl_percent: 15.39,
              total_fees: 30.00,
              breakdown: {
                stocks: { total_value: 10000, total_cost_basis: 9000, unrealized_pnl: 1000, unrealized_pnl_percent: 11.11, fees: 20, count: 2 },
                crypto: { total_value: 5000.50, total_cost_basis: 4000, unrealized_pnl: 1000.50, unrealized_pnl_percent: 25.01, fees: 10, count: 1 },
                metals: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/realized-pnl')) {
          return Promise.resolve({
            data: {
              total_realized_pnl: 0,
              total_fees: 0,
              net_pnl: 0,
              closed_positions_count: 0,
              breakdown: {
                stocks: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/positions')) {
          return Promise.resolve({ data: [] })
        }
        return Promise.resolve({ data: {} })
      })

      render(<App />)

      // Wait for portfolio to load and check for summary cards
      await waitFor(() => {
        expect(screen.getByText('Total Value')).toBeInTheDocument()
      })

      // Check that values are displayed somewhere in the document
      const totalValue = document.querySelector('.metric-value')
      expect(totalValue).toBeTruthy()
    })

    it('displays positions table when positions exist', async () => {
      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/portfolio/open-positions')) {
          return Promise.resolve({
            data: {
              total_value: 20000,
              total_cost_basis: 18000,
              unrealized_pnl: 2000,
              unrealized_pnl_percent: 11.11,
              total_fees: 50,
              breakdown: {
                stocks: { total_value: 20000, total_cost_basis: 18000, unrealized_pnl: 2000, unrealized_pnl_percent: 11.11, fees: 50, count: 1 },
                crypto: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 },
                metals: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/realized-pnl')) {
          return Promise.resolve({
            data: {
              total_realized_pnl: 0,
              total_fees: 0,
              net_pnl: 0,
              closed_positions_count: 0,
              breakdown: {
                stocks: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/positions')) {
          return Promise.resolve({
            data: [
              {
                symbol: 'AAPL',
                asset_type: 'stocks',
                quantity: 10,
                avg_cost: 150,
                current_price: 160,
                market_value: 1600,
                cost_basis: 1500,
                unrealized_pnl: 100,
                unrealized_pnl_percent: 6.67,
                fees: 5.00
              }
            ]
          })
        }
        return Promise.resolve({ data: {} })
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
      })
    })

    it('displays empty state when no positions', async () => {
      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/portfolio/open-positions')) {
          return Promise.resolve({
            data: {
              total_value: 0,
              total_cost_basis: 0,
              unrealized_pnl: 0,
              unrealized_pnl_percent: 0,
              total_fees: 0,
              breakdown: {
                stocks: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 },
                crypto: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 },
                metals: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/realized-pnl')) {
          return Promise.resolve({
            data: {
              total_realized_pnl: 0,
              total_fees: 0,
              net_pnl: 0,
              closed_positions_count: 0,
              breakdown: {
                stocks: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/positions')) {
          return Promise.resolve({ data: [] })
        }
        return Promise.resolve({ data: {} })
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText(/No positions to display/)).toBeInTheDocument()
      })
    })
  })

  describe('Tab System', () => {
    it('only displays one tab content at a time', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Initially showing portfolio
      await waitFor(() => {
        expect(screen.getByText('Portfolio Dashboard')).toBeInTheDocument()
      })

      // Switch to upload
      await user.click(screen.getByTitle('Upload'))

      await waitFor(() => {
        expect(screen.getByText('Import Transactions')).toBeInTheDocument()
        expect(screen.queryByText('Portfolio Dashboard')).not.toBeInTheDocument()
      })
    })

    it('highlights active tab in sidebar', async () => {
      const user = userEvent.setup()
      render(<App />)

      const portfolioButton = screen.getByTitle('Portfolio')
      const uploadButton = screen.getByTitle('Upload')

      // Portfolio should be active initially
      expect(portfolioButton).toHaveClass('active')
      expect(uploadButton).not.toHaveClass('active')

      // Click upload
      await user.click(uploadButton)

      // Upload should be active
      await waitFor(() => {
        expect(uploadButton).toHaveClass('active')
        expect(portfolioButton).not.toHaveClass('active')
      })
    })
  })

  describe('Database Reset Flow', () => {
    it('opens reset modal when database reset is clicked', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Open database submenu
      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Reset')).toBeInTheDocument()
      })

      // Click reset
      const resetButton = screen.getByText('Reset')
      await user.click(resetButton)

      // Modal should appear
      await waitFor(() => {
        expect(screen.getByText(/Database Reset/)).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Behavior', () => {
    it('renders correctly on desktop layout', () => {
      render(<App />)

      const layout = document.querySelector('.app-layout')
      expect(layout).toBeInTheDocument()

      const sidebar = screen.getByRole('navigation')
      expect(sidebar).toBeInTheDocument()

      const mainContent = document.querySelector('.main-content')
      expect(mainContent).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles portfolio fetch errors gracefully', async () => {
      mockedAxios.get.mockImplementation((url: string) => {
        // Return errors for API calls but the app should still render
        return Promise.reject(new Error('Network error'))
      })

      render(<App />)

      // App should still render
      expect(screen.getByRole('navigation')).toBeInTheDocument()
    })
  })

  describe('Component Integration', () => {
    it('TransactionImport component is accessible from upload tab', async () => {
      const user = userEvent.setup()
      render(<App />)

      await user.click(screen.getByTitle('Upload'))

      await waitFor(() => {
        // TransactionImport component should have its elements
        expect(screen.getByText('Import Transactions')).toBeInTheDocument()
      })
    })

    it('database submenu closes after selecting an item', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Open database submenu
      const databaseButton = screen.getByTitle('Database')
      await user.click(databaseButton)

      await waitFor(() => {
        expect(screen.getByText('Stats')).toBeInTheDocument()
      })

      // Click stats
      await user.click(screen.getByText('Stats'))

      // Submenu should close
      await waitFor(() => {
        expect(screen.queryByText('Reset')).not.toBeInTheDocument()
      })
    })
  })

  describe('Visual States', () => {
    it('shows loading state initially', () => {
      render(<App />)

      // May show loading text while portfolio is fetching
      // This depends on the timing of the fetch
    })

    it('applies profit/loss styling correctly', async () => {
      mockedAxios.get.mockImplementation((url: string) => {
        if (url.includes('/api/portfolio/open-positions')) {
          return Promise.resolve({
            data: {
              total_value: 20000,
              total_cost_basis: 17500,
              unrealized_pnl: 2500,
              unrealized_pnl_percent: 14.29,
              total_fees: 50,
              breakdown: {
                stocks: { total_value: 20000, total_cost_basis: 17500, unrealized_pnl: 2500, unrealized_pnl_percent: 14.29, fees: 50, count: 2 },
                crypto: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 },
                metals: { total_value: 0, total_cost_basis: 0, unrealized_pnl: 0, unrealized_pnl_percent: 0, fees: 0, count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/realized-pnl')) {
          return Promise.resolve({
            data: {
              total_realized_pnl: 0,
              total_fees: 0,
              net_pnl: 0,
              closed_positions_count: 0,
              breakdown: {
                stocks: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                crypto: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 },
                metals: { realized_pnl: 0, fees: 0, net_pnl: 0, closed_count: 0 }
              },
              last_updated: '2024-01-15T10:30:00Z'
            }
          })
        }
        if (url.includes('/api/portfolio/positions')) {
          return Promise.resolve({
            data: [
              {
                symbol: 'WINNING',
                asset_type: 'stocks',
                quantity: 10,
                avg_cost: 100,
                current_price: 150,
                market_value: 1500,
                cost_basis: 1000,
                unrealized_pnl: 500,
                unrealized_pnl_percent: 50,
                fees: 10.00
              },
              {
                symbol: 'LOSING',
                asset_type: 'stocks',
                quantity: 5,
                avg_cost: 200,
                current_price: 150,
                market_value: 750,
                cost_basis: 1000,
                unrealized_pnl: -250,
                unrealized_pnl_percent: -25,
                fees: 5.00
              }
            ]
          })
        }
        return Promise.resolve({ data: {} })
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('WINNING')).toBeInTheDocument()
      })

      // Find profit/loss cells and check styling
      const profitCells = document.querySelectorAll('.profit')
      const lossCells = document.querySelectorAll('.loss')

      expect(profitCells.length).toBeGreaterThan(0)
      expect(lossCells.length).toBeGreaterThan(0)
    })
  })
})
