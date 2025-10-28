// ABOUTME: Expandable row component showing transaction history for a position
// ABOUTME: Displays nested table with transaction details (date, type, quantity, price, fee, total)

import { useEffect, useState } from 'react'
import axios from 'axios'
import { formatCurrency } from '../utils/formatters'
import { API_CONFIG } from '../config/app.config'
import './TransactionDetailsRow.css'

const API_URL = API_CONFIG.BASE_URL

export interface Transaction {
  id: number
  date: string
  type: string
  quantity: number
  price: number
  fee: number
  total_amount: number
  currency: string
  asset_type: string
}

interface TransactionDetailsRowProps {
  symbol: string
  onClose: () => void
}

export default function TransactionDetailsRow({ symbol, onClose }: TransactionDetailsRowProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setError(null)
        const response = await axios.get<Transaction[]>(
          `${API_URL}/api/portfolio/positions/${symbol}/transactions`
        )
        setTransactions(response.data)
      } catch (err) {
        console.error('Failed to fetch transactions:', err)
        setError('Failed to load transaction history')
      } finally {
        setLoading(false)
      }
    }

    fetchTransactions()
  }, [symbol])

  const getTransactionTypeClass = (type: string): string => {
    const lowerType = type.toLowerCase()
    if (lowerType === 'buy') return 'buy'
    if (lowerType === 'sell') return 'sell'
    if (['staking', 'airdrop', 'mining'].includes(lowerType)) return 'reward'
    return 'other'
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <tr className="transaction-details-row">
        <td colSpan={8}>
          <div className="loading-transactions">
            <div className="loading-spinner"></div>
            <p>Loading transaction history...</p>
          </div>
        </td>
      </tr>
    )
  }

  if (error) {
    return (
      <tr className="transaction-details-row">
        <td colSpan={8}>
          <div className="transaction-error">
            <p>{error}</p>
            <button onClick={onClose} className="close-button-text">
              Close
            </button>
          </div>
        </td>
      </tr>
    )
  }

  return (
    <tr className="transaction-details-row">
      <td colSpan={8}>
        <div className="transaction-details-container">
          <div className="transaction-details-header">
            <h4>Transaction History for {symbol}</h4>
            <button
              onClick={onClose}
              className="close-button"
              aria-label="Close transaction details"
            >
              ✕
            </button>
          </div>
          <div className="transaction-details-body">
            <table className="transaction-details-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Type</th>
                  <th className="align-right">Quantity</th>
                  <th className="align-right">Price</th>
                  <th className="align-right">Fee</th>
                  <th className="align-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn) => (
                  <tr key={txn.id}>
                    <td>{formatDate(txn.date)}</td>
                    <td className="time-cell">{formatTime(txn.date)}</td>
                    <td>
                      <span
                        className={`transaction-type ${getTransactionTypeClass(txn.type)}`}
                      >
                        {txn.type}
                      </span>
                    </td>
                    <td className="align-right">
                      {txn.asset_type === 'CRYPTO'
                        ? txn.quantity.toFixed(8)
                        : txn.quantity.toFixed(2)}
                    </td>
                    <td className="align-right">
                      {formatCurrency(txn.price, txn.currency)}
                    </td>
                    <td className="align-right">
                      {formatCurrency(txn.fee, txn.currency)}
                    </td>
                    <td className="align-right total-cell">
                      {formatCurrency(txn.total_amount, txn.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="transaction-details-footer">
            <p>
              {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </td>
    </tr>
  )
}
