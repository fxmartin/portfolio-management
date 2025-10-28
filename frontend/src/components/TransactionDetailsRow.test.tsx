// ABOUTME: Tests for TransactionDetailsRow component
// ABOUTME: Tests transaction history display, loading states, and error handling

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import axios from 'axios'
import TransactionDetailsRow from './TransactionDetailsRow'

vi.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('TransactionDetailsRow', () => {
  const mockOnClose = vi.fn()
  const mockTransactions = [
    {
      id: 1,
      date: '2024-03-01T00:00:00',
      type: 'SELL',
      quantity: 0.2,
      price: 52000.0,
      fee: 10.0,
      total_amount: 10410.0,
      currency: 'EUR',
      asset_type: 'CRYPTO',
    },
    {
      id: 2,
      date: '2024-02-01T00:00:00',
      type: 'STAKING',
      quantity: 0.001,
      price: 50000.0,
      fee: 0.0,
      total_amount: 50.0,
      currency: 'EUR',
      asset_type: 'CRYPTO',
    },
    {
      id: 3,
      date: '2024-01-01T00:00:00',
      type: 'BUY',
      quantity: 0.5,
      price: 45000.0,
      fee: 25.5,
      total_amount: 22525.5,
      currency: 'EUR',
      asset_type: 'CRYPTO',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    expect(screen.getByText(/loading transaction history/i)).toBeInTheDocument()
  })

  it('fetches and displays transactions for a symbol', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockTransactions })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Check API was called correctly
    expect(mockedAxios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/portfolio/positions/BTC/transactions')
    )

    // Check all transactions are displayed
    expect(screen.getByText('SELL')).toBeInTheDocument()
    expect(screen.getByText('STAKING')).toBeInTheDocument()
    expect(screen.getByText('BUY')).toBeInTheDocument()

    // Check transaction count
    expect(screen.getByText('3 transactions')).toBeInTheDocument()
  })

  it('displays transaction details correctly', async () => {
    mockedAxios.get.mockResolvedValue({ data: [mockTransactions[0]] })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Check quantities (crypto should show 8 decimals)
    expect(screen.getByText('0.20000000')).toBeInTheDocument()

    // Check currency amounts are formatted (with space after symbol)
    expect(screen.getByText('€ 52,000.00')).toBeInTheDocument()
    expect(screen.getByText('€ 10.00')).toBeInTheDocument()
    expect(screen.getByText('€ 10,410.00')).toBeInTheDocument()
  })

  it('applies correct styling to transaction types', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockTransactions })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Check transaction type badges have correct classes
    const buyBadge = screen.getByText('BUY')
    const sellBadge = screen.getByText('SELL')
    const stakingBadge = screen.getByText('STAKING')

    expect(buyBadge).toHaveClass('transaction-type', 'buy')
    expect(sellBadge).toHaveClass('transaction-type', 'sell')
    expect(stakingBadge).toHaveClass('transaction-type', 'reward')
  })

  it('displays dates and times correctly', async () => {
    mockedAxios.get.mockResolvedValue({ data: [mockTransactions[0]] })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Date should be formatted as "Mar 1, 2024" or similar
    expect(screen.getByText(/Mar.*1.*2024/i)).toBeInTheDocument()

    // Time should be formatted as "12:00 AM" or similar
    expect(screen.getByText(/12:00/i)).toBeInTheDocument()
  })

  it('handles different asset types for quantity precision', async () => {
    const stockTransaction = {
      id: 1,
      date: '2024-01-01T00:00:00',
      type: 'BUY',
      quantity: 10.5,
      price: 150.0,
      fee: 1.0,
      total_amount: 1576.0,
      currency: 'USD',
      asset_type: 'STOCK',
    }

    mockedAxios.get.mockResolvedValue({ data: [stockTransaction] })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="AAPL" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for AAPL')).toBeInTheDocument()
    })

    // Stock should show 2 decimals
    expect(screen.getByText('10.50')).toBeInTheDocument()
  })

  it('handles error state correctly', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'))

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText(/failed to load transaction history/i)).toBeInTheDocument()
    })

    // Close button should be available in error state
    const closeButton = screen.getByRole('button', { name: /close/i })
    expect(closeButton).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockTransactions })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    const closeButton = screen.getByRole('button', { name: /close transaction details/i })
    closeButton.click()

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('displays single transaction with correct pluralization', async () => {
    mockedAxios.get.mockResolvedValue({ data: [mockTransactions[0]] })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Should say "1 transaction" not "1 transactions"
    expect(screen.getByText('1 transaction')).toBeInTheDocument()
  })

  it('displays multiple transactions with correct pluralization', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockTransactions })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Should say "3 transactions"
    expect(screen.getByText('3 transactions')).toBeInTheDocument()
  })

  it('handles all transaction types correctly', async () => {
    const allTypes = [
      { ...mockTransactions[0], type: 'BUY' },
      { ...mockTransactions[0], id: 2, type: 'SELL' },
      { ...mockTransactions[0], id: 3, type: 'STAKING' },
      { ...mockTransactions[0], id: 4, type: 'AIRDROP' },
      { ...mockTransactions[0], id: 5, type: 'MINING' },
      { ...mockTransactions[0], id: 6, type: 'DIVIDEND' },
    ]

    mockedAxios.get.mockResolvedValue({ data: allTypes })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Check all transaction types are displayed
    expect(screen.getByText('BUY')).toBeInTheDocument()
    expect(screen.getByText('SELL')).toBeInTheDocument()
    expect(screen.getByText('STAKING')).toBeInTheDocument()
    expect(screen.getByText('AIRDROP')).toBeInTheDocument()
    expect(screen.getByText('MINING')).toBeInTheDocument()
    expect(screen.getByText('DIVIDEND')).toBeInTheDocument()
  })

  it('spans correct number of columns', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockTransactions })

    const { container } = render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Should span 8 columns (matching HoldingsTable)
    const expandedRow = container.querySelector('.transaction-details-row td')
    expect(expandedRow).toHaveAttribute('colSpan', '8')
  })

  it('has proper accessibility attributes', async () => {
    mockedAxios.get.mockResolvedValue({ data: mockTransactions })

    render(
      <table>
        <tbody>
          <TransactionDetailsRow symbol="BTC" onClose={mockOnClose} />
        </tbody>
      </table>
    )

    await waitFor(() => {
      expect(screen.getByText('Transaction History for BTC')).toBeInTheDocument()
    })

    // Close button should have proper aria-label
    const closeButton = screen.getByRole('button', { name: /close transaction details/i })
    expect(closeButton).toHaveAttribute('aria-label', 'Close transaction details')
  })
})
