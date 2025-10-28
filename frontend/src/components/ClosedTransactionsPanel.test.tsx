// ABOUTME: Tests for ClosedTransactionsPanel component
// ABOUTME: Tests closed transaction display, loading states, and error handling

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import axios from 'axios'
import ClosedTransactionsPanel from './ClosedTransactionsPanel'

vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('ClosedTransactionsPanel', () => {
  const mockOnClose = vi.fn()

  const mockClosedTransactions = [
    {
      id: 1,
      symbol: 'XAU',
      sell_date: '2024-09-15T00:00:00',
      quantity: 0.5,
      buy_price: 1952.0,
      sell_price: 2148.0,
      gross_pnl: 98.0,
      sell_fee: 1.0,
      net_pnl: 97.0,
      currency: 'EUR',
    },
    {
      id: 2,
      symbol: 'XAG',
      sell_date: '2024-09-10T00:00:00',
      quantity: 15.0,
      buy_price: 26.7,
      sell_price: 37.19,
      gross_pnl: 157.35,
      sell_fee: 0.5,
      net_pnl: 156.85,
      currency: 'EUR',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {}))

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    expect(screen.getByText(/loading closed transactions/i)).toBeInTheDocument()
  })

  it('fetches and displays closed transactions', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockClosedTransactions })

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Metals Transactions')).toBeInTheDocument()
    })

    expect(mockedAxios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/portfolio/realized-pnl/metals/transactions')
    )

    expect(screen.getByText('XAU')).toBeInTheDocument()
    expect(screen.getByText('XAG')).toBeInTheDocument()
    expect(screen.getByText('2 closed transactions')).toBeInTheDocument()
  })

  it('displays correct quantity decimals for crypto', async () => {
    const cryptoTransactions = [
      {
        id: 1,
        symbol: 'BTC',
        sell_date: '2024-06-01T00:00:00',
        quantity: 0.3,
        buy_price: 40100.0,
        sell_price: 50000.0,
        gross_pnl: 2970.0,
        sell_fee: 5.0,
        net_pnl: 2965.0,
        currency: 'EUR',
      },
    ]

    mockedAxios.get.mockResolvedValue({ data: cryptoTransactions })

    render(<ClosedTransactionsPanel assetType="crypto" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Crypto Transactions')).toBeInTheDocument()
    })

    // Crypto should show 8 decimals
    expect(screen.getByText('0.30000000')).toBeInTheDocument()
  })

  it('displays correct quantity decimals for stocks', async () => {
    const stockTransactions = [
      {
        id: 1,
        symbol: 'AAPL',
        sell_date: '2024-03-01T00:00:00',
        quantity: 15.5,
        buy_price: 150.0,
        sell_price: 175.0,
        gross_pnl: 387.5,
        sell_fee: 2.0,
        net_pnl: 385.5,
        currency: 'USD',
      },
    ]

    mockedAxios.get.mockResolvedValue({ data: stockTransactions })

    render(<ClosedTransactionsPanel assetType="stocks" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Stocks Transactions')).toBeInTheDocument()
    })

    // Stocks should show 2 decimals
    expect(screen.getByText('15.50')).toBeInTheDocument()
  })

  it('handles error state correctly', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'))

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load closed transactions/i)).toBeInTheDocument()
    })

    const closeButton = screen.getByText('Close')
    expect(closeButton).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockClosedTransactions })

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Metals Transactions')).toBeInTheDocument()
    })

    const closeButton = screen.getByRole('button', { name: /close transaction details/i })
    closeButton.click()

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('displays single transaction with correct pluralization', async () => {
    mockedAxios.get.mockResolvedValue({ data: [mockClosedTransactions[0]] })

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Metals Transactions')).toBeInTheDocument()
    })

    expect(screen.getByText('1 closed transaction')).toBeInTheDocument()
  })

  it('formats dates correctly', async () => {
    mockedAxios.get.mockResolvedValue({ data: [mockClosedTransactions[0]] })

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Metals Transactions')).toBeInTheDocument()
    })

    // Date should be formatted as "Sep 15, 2024" or similar
    expect(screen.getByText(/Sep.*15.*2024/i)).toBeInTheDocument()
  })

  it('displays P&L with correct formatting and color', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockClosedTransactions })

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Metals Transactions')).toBeInTheDocument()
    })

    // Should show formatted currency values
    expect(screen.getByText('€ 98.00')).toBeInTheDocument()
    expect(screen.getByText('€ 97.00')).toBeInTheDocument()

    // Positive P&L should have profit class
    const netPnlCells = screen.getAllByText(/€ \d+\.\d+/)
    const profitCells = netPnlCells.filter((cell) => cell.classList.contains('profit'))
    expect(profitCells.length).toBeGreaterThan(0)
  })

  it('has proper accessibility attributes', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockClosedTransactions })

    render(<ClosedTransactionsPanel assetType="metals" onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Closed Metals Transactions')).toBeInTheDocument()
    })

    const closeButton = screen.getByRole('button', { name: /close transaction details/i })
    expect(closeButton).toHaveAttribute('aria-label', 'Close transaction details')
  })
})
