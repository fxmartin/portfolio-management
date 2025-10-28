// ABOUTME: Expandable panel showing closed transaction history for an asset type
// ABOUTME: Displays FIFO-calculated P&L for each closed (sold) transaction

import { useEffect, useState } from 'react'
import axios from 'axios'
import { formatCurrency, getPnLClassName } from '../utils/formatters'
import { API_CONFIG, PORTFOLIO_CONFIG } from '../config/app.config'
import './ClosedTransactionsPanel.css'

const API_URL = API_CONFIG.BASE_URL
const BASE_CURRENCY = PORTFOLIO_CONFIG.BASE_CURRENCY

export interface ClosedTransaction {
  id: number
  symbol: string
  sell_date: string
  quantity: number
  buy_price: number
  sell_price: number
  gross_pnl: number
  sell_fee: number
  net_pnl: number
  currency: string
}

interface ClosedTransactionsPanelProps {
  assetType: string
  onClose: () => void
}

export default function ClosedTransactionsPanel({
  assetType,
  onClose
}: ClosedTransactionsPanelProps) {
  const [transactions, setTransactions] = useState<ClosedTransaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setError(null)
        const response = await axios.get<ClosedTransaction[]>(
          `${API_URL}/api/portfolio/realized-pnl/${assetType}/transactions`
        )
        setTransactions(response.data)
      } catch (err) {
        console.error('Failed to fetch closed transactions:', err)
        setError('Failed to load closed transactions')
      } finally {
        setLoading(false)
      }
    }

    fetchTransactions()
  }, [assetType])

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getAssetTypeName = (): string => {
    return assetType.charAt(0).toUpperCase() + assetType.slice(1)
  }

  const getQuantityDecimals = (): number => {
    return assetType === 'crypto' ? 8 : 2
  }

  if (loading) {
    return (
      <div className="closed-transactions-panel">
        <div className="loading-transactions">
          <div className="loading-spinner"></div>
          <p>Loading closed transactions...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="closed-transactions-panel">
        <div className="transaction-error">
          <p>{error}</p>
          <button onClick={onClose} className="close-button-text">
            Close
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="closed-transactions-panel">
      <div className="panel-header">
        <h4>Closed {getAssetTypeName()} Transactions</h4>
        <button
          onClick={onClose}
          className="close-button"
          aria-label="Close transaction details"
        >
          ✕
        </button>
      </div>
      <div className="panel-body">
        <table className="closed-transactions-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Date Sold</th>
              <th className="align-right">Quantity</th>
              <th className="align-right">Buy Price</th>
              <th className="align-right">Sell Price</th>
              <th className="align-right">Gross P&L</th>
              <th className="align-right">Fees</th>
              <th className="align-right">Net P&L</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => (
              <tr key={txn.id}>
                <td className="symbol-cell">{txn.symbol}</td>
                <td>{formatDate(txn.sell_date)}</td>
                <td className="align-right">
                  {txn.quantity.toFixed(getQuantityDecimals())}
                </td>
                <td className="align-right">
                  {formatCurrency(txn.buy_price, txn.currency)}
                </td>
                <td className="align-right">
                  {formatCurrency(txn.sell_price, txn.currency)}
                </td>
                <td className={`align-right ${getPnLClassName(txn.gross_pnl)}`}>
                  {formatCurrency(txn.gross_pnl, BASE_CURRENCY)}
                </td>
                <td className="align-right fees-cell">
                  {formatCurrency(txn.sell_fee, txn.currency)}
                </td>
                <td className={`align-right net-pnl-cell ${getPnLClassName(txn.net_pnl)}`}>
                  {formatCurrency(txn.net_pnl, BASE_CURRENCY)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="panel-footer">
        <p>
          {transactions.length} closed transaction{transactions.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  )
}
