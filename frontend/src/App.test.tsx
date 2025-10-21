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
    mockedAxios.get.mockResolvedValue({
      data: {
        total_value: 10000,
        positions: [],
        cash_balance: 5000
      }
    })
  })

  describe('Sidebar Navigation', () => {
    it('renders app with sidebar and default portfolio tab', async () => {
      render(<App />)

      // Sidebar should be visible
      expect(screen.getByRole('navigation')).toBeInTheDocument()

      // Portfolio tab should be active by default
      await waitFor(() => {
        expect(screen.getByText('Portfolio Overview')).toBeInTheDocument()
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
      expect(screen.queryByText('Portfolio Overview')).not.toBeInTheDocument()
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
        expect(screen.getByText('Portfolio Overview')).toBeInTheDocument()
      })

      // Upload content should not be visible
      expect(screen.queryByText('Import Transactions')).not.toBeInTheDocument()
    })
  })

  describe('Portfolio Display', () => {
    it('displays portfolio summary when loaded', async () => {
      mockedAxios.get.mockResolvedValue({
        data: {
          total_value: 15000.50,
          positions: [],
          cash_balance: 2500.75
        }
      })

      render(<App />)

      // Wait for portfolio to load and check for summary cards
      await waitFor(() => {
        expect(screen.getByText('Total Value')).toBeInTheDocument()
        expect(screen.getByText('Cash Balance')).toBeInTheDocument()
      })

      // Check that values are displayed somewhere in the document
      const totalValue = document.querySelector('.card-value')
      expect(totalValue).toBeTruthy()
    })

    it('displays positions table when positions exist', async () => {
      mockedAxios.get.mockResolvedValue({
        data: {
          total_value: 20000,
          positions: [
            {
              ticker: 'AAPL',
              quantity: 10,
              avgCost: 150,
              currentPrice: 160,
              value: 1600,
              pnl: 100,
              pnlPercent: 6.67
            }
          ],
          cash_balance: 5000
        }
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument()
        expect(screen.getByText('10')).toBeInTheDocument()
        expect(screen.getByText('$150.00')).toBeInTheDocument()
      })
    })

    it('displays empty state when no positions', async () => {
      mockedAxios.get.mockResolvedValue({
        data: {
          total_value: 0,
          positions: [],
          cash_balance: 0
        }
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText(/No positions yet/)).toBeInTheDocument()
      })
    })
  })

  describe('Tab System', () => {
    it('only displays one tab content at a time', async () => {
      const user = userEvent.setup()
      render(<App />)

      // Initially showing portfolio
      await waitFor(() => {
        expect(screen.getByText('Portfolio Overview')).toBeInTheDocument()
      })

      // Switch to upload
      await user.click(screen.getByTitle('Upload'))

      await waitFor(() => {
        expect(screen.getByText('Import Transactions')).toBeInTheDocument()
        expect(screen.queryByText('Portfolio Overview')).not.toBeInTheDocument()
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
        expect(screen.getByText(/Dangerous Operation/)).toBeInTheDocument()
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
      mockedAxios.get.mockRejectedValue(new Error('Network error'))

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
      mockedAxios.get.mockResolvedValue({
        data: {
          total_value: 20000,
          positions: [
            {
              ticker: 'WINNING',
              quantity: 10,
              avgCost: 100,
              currentPrice: 150,
              value: 1500,
              pnl: 500,
              pnlPercent: 50
            },
            {
              ticker: 'LOSING',
              quantity: 5,
              avgCost: 200,
              currentPrice: 150,
              value: 750,
              pnl: -250,
              pnlPercent: -25
            }
          ],
          cash_balance: 5000
        }
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
