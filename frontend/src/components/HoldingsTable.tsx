// ABOUTME: Holdings table component displaying active portfolio positions
// ABOUTME: Shows positions with sortable columns, filtering, and search functionality

import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { formatCurrency, formatPercentage, getPnLClassName } from '../utils/formatters'
import { API_CONFIG, PORTFOLIO_CONFIG, REFRESH_INTERVALS } from '../config/app.config'
import './HoldingsTable.css'

const API_URL = API_CONFIG.BASE_URL
const BASE_CURRENCY = PORTFOLIO_CONFIG.BASE_CURRENCY
const DEFAULT_REFRESH_INTERVAL = REFRESH_INTERVALS.HOLDINGS_TABLE

export interface Position {
  symbol: string
  asset_type: string
  quantity: number
  avg_cost_basis: number
  total_cost_basis: number
  current_price: number
  current_value: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
  currency: string
  first_purchase_date: string | null
  last_transaction_date: string | null
  last_price_update: string | null
}

// Asset name mapping for display
const ASSET_NAMES: Record<string, string> = {
  'BTC': 'Bitcoin',
  'ETH': 'Ethereum',
  'SOL': 'Solana',
  'LINK': 'Chainlink',
  'XRP': 'Ripple',
  'USDT': 'Tether',
  'BNB': 'Binance Coin',
  'ADA': 'Cardano',
  'DOGE': 'Dogecoin',
  'MATIC': 'Polygon',
  'DOT': 'Polkadot',
  'UNI': 'Uniswap',
  'AVAX': 'Avalanche',
  'ATOM': 'Cosmos',
  'ALGO': 'Algorand',
}

type SortKey = 'symbol' | 'quantity' | 'avg_cost_basis' | 'current_price' | 'current_value' | 'unrealized_pnl' | 'unrealized_pnl_percent'
type SortDirection = 'asc' | 'desc'

interface HoldingsTableProps {
  onRefresh?: () => void
  autoRefresh?: boolean
  refreshInterval?: number
}

export default function HoldingsTable({
  onRefresh,
  autoRefresh = true,
  refreshInterval = DEFAULT_REFRESH_INTERVAL,
}: HoldingsTableProps) {
  const [positions, setPositions] = useState<Position[]>([])
  const [filteredPositions, setFilteredPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('current_value')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [assetTypeFilter, setAssetTypeFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const fetchPositions = useCallback(async () => {
    try {
      setError(null)
      const response = await axios.get<Position[]>(`${API_URL}/api/portfolio/positions`)
      setPositions(response.data)
      setLoading(false)

      if (onRefresh) {
        onRefresh()
      }
    } catch (err) {
      console.error('Failed to fetch positions:', err)
      setError('Failed to load positions')
      setLoading(false)
    }
  }, [onRefresh])

  useEffect(() => {
    fetchPositions()

    if (autoRefresh) {
      console.log(`[HoldingsTable] Setting up auto-refresh with interval: ${refreshInterval}ms`)
      const interval = setInterval(() => {
        console.log('[HoldingsTable] Auto-refresh triggered')
        fetchPositions()
      }, refreshInterval)
      return () => {
        console.log('[HoldingsTable] Clearing auto-refresh interval')
        clearInterval(interval)
      }
    }
  }, [autoRefresh, refreshInterval, fetchPositions])

  // Filter and sort positions whenever dependencies change
  useEffect(() => {
    let result = [...positions]

    // Apply asset type filter
    if (assetTypeFilter !== 'all') {
      result = result.filter(p => p.asset_type.toLowerCase() === assetTypeFilter.toLowerCase())
    }

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter(p => {
        const name = ASSET_NAMES[p.symbol] || ''
        return (
          p.symbol.toLowerCase().includes(term) ||
          name.toLowerCase().includes(term)
        )
      })
    }

    // Apply sorting
    result.sort((a, b) => {
      let aValue = a[sortKey]
      let bValue = b[sortKey]

      // Handle string comparison for symbol
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      // Handle number comparison
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }

      return 0
    })

    setFilteredPositions(result)
  }, [positions, assetTypeFilter, searchTerm, sortKey, sortDirection])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      // Toggle direction if clicking the same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      // Set new sort key with default descending
      setSortKey(key)
      setSortDirection('desc')
    }
  }

  const getSortIcon = (key: SortKey): string => {
    if (sortKey !== key) return '↕'
    return sortDirection === 'asc' ? '↑' : '↓'
  }

  if (loading) {
    return (
      <div className="holdings-table-container loading">
        <div className="loading-spinner"></div>
        <p>Loading positions...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="holdings-table-container error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button onClick={fetchPositions} className="retry-button">
          Retry
        </button>
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <div className="holdings-table-container empty">
        <p>No positions to display. Import transactions to see your holdings.</p>
      </div>
    )
  }

  return (
    <div className="holdings-table-container">
      <div className="holdings-header">
        <h2>Holdings</h2>
        <div className="holdings-controls">
          {/* Search Input */}
          <input
            type="text"
            placeholder="Search by symbol or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />

          {/* Asset Type Filter */}
          <select
            value={assetTypeFilter}
            onChange={(e) => setAssetTypeFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Assets</option>
            <option value="stock">Stocks</option>
            <option value="crypto">Crypto</option>
            <option value="metal">Metals</option>
          </select>
        </div>
      </div>

      {filteredPositions.length === 0 ? (
        <div className="no-results">
          <p>No positions match your filters.</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="holdings-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('symbol')} className="sortable">
                  Symbol {getSortIcon('symbol')}
                </th>
                <th onClick={() => handleSort('quantity')} className="sortable align-right">
                  Quantity {getSortIcon('quantity')}
                </th>
                <th onClick={() => handleSort('avg_cost_basis')} className="sortable align-right">
                  Avg Cost {getSortIcon('avg_cost_basis')}
                </th>
                <th onClick={() => handleSort('current_price')} className="sortable align-right">
                  Market Price {getSortIcon('current_price')}
                </th>
                <th onClick={() => handleSort('current_value')} className="sortable align-right">
                  Value {getSortIcon('current_value')}
                </th>
                <th onClick={() => handleSort('unrealized_pnl')} className="sortable align-right">
                  P&L {getSortIcon('unrealized_pnl')}
                </th>
                <th onClick={() => handleSort('unrealized_pnl_percent')} className="sortable align-right">
                  P&L % {getSortIcon('unrealized_pnl_percent')}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredPositions.map((position) => (
                <tr key={position.symbol}>
                  <td className="symbol-cell">
                    <div className="symbol-name">{position.symbol}</div>
                    <div className="asset-name">{ASSET_NAMES[position.symbol] || ''}</div>
                  </td>
                  <td className="align-right">
                    {position.quantity.toFixed(position.asset_type === 'CRYPTO' ? 8 : 2)} {position.symbol}
                  </td>
                  <td className="align-right">
                    {formatCurrency(position.avg_cost_basis, position.currency)}
                  </td>
                  <td className="align-right">
                    {formatCurrency(position.current_price, position.currency)}
                  </td>
                  <td className="align-right">
                    {formatCurrency(position.current_value, BASE_CURRENCY)}
                  </td>
                  <td className={`align-right ${getPnLClassName(position.unrealized_pnl)}`}>
                    {formatCurrency(position.unrealized_pnl, BASE_CURRENCY)}
                  </td>
                  <td className={`align-right ${getPnLClassName(position.unrealized_pnl)}`}>
                    {formatPercentage(position.unrealized_pnl_percent)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="holdings-footer">
        <p>
          Showing {filteredPositions.length} of {positions.length} position{positions.length === 1 ? '' : 's'}
        </p>
      </div>
    </div>
  )
}
