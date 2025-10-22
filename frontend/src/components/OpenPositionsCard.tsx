// ABOUTME: Open positions overview card showing total value and unrealized P&L
// ABOUTME: Displays breakdown by asset type with clickable filters for holdings table

import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { formatCurrency, formatPnLChange, formatDateTime, getPnLClassName } from '../utils/formatters'
import { API_CONFIG, PORTFOLIO_CONFIG, REFRESH_INTERVALS, formatRefreshInterval } from '../config/app.config'
import './OpenPositionsCard.css'

const API_URL = API_CONFIG.BASE_URL
const BASE_CURRENCY = PORTFOLIO_CONFIG.BASE_CURRENCY
const DEFAULT_REFRESH_INTERVAL = REFRESH_INTERVALS.PORTFOLIO_SUMMARY

interface AssetTypeMetrics {
  value: number
  pnl: number
  pnl_percent: number
}

interface OpenPositionsData {
  total_value: number
  total_cost_basis: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
  breakdown: {
    stocks: AssetTypeMetrics
    crypto: AssetTypeMetrics
    metals: AssetTypeMetrics
  }
  last_updated: string | null
}

interface OpenPositionsCardProps {
  onAssetTypeFilter?: (assetType: string | null) => void
  autoRefresh?: boolean
  refreshInterval?: number
}

export default function OpenPositionsCard({
  onAssetTypeFilter,
  autoRefresh = true,
  refreshInterval = DEFAULT_REFRESH_INTERVAL,
}: OpenPositionsCardProps) {
  const [data, setData] = useState<OpenPositionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedType, setSelectedType] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setError(null)
      const response = await axios.get<OpenPositionsData>(`${API_URL}/api/portfolio/open-positions`)
      setData(response.data)
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch open positions overview:', err)
      setError('Failed to load open positions data')
      setLoading(false)
    }
  }, [])

  const refreshPrices = useCallback(async () => {
    try {
      await axios.post(`${API_URL}/api/portfolio/refresh-prices`)
      await fetchData()
    } catch (err) {
      console.error('[OpenPositionsCard] Failed to refresh prices:', err)
    }
  }, [fetchData])

  useEffect(() => {
    // Initial load
    fetchData()

    if (autoRefresh) {
      console.log(`[OpenPositionsCard] Setting up auto-refresh with interval: ${refreshInterval}ms`)
      const interval = setInterval(() => {
        console.log('[OpenPositionsCard] Auto-refresh triggered')
        refreshPrices()
      }, refreshInterval)
      return () => {
        console.log('[OpenPositionsCard] Clearing auto-refresh interval')
        clearInterval(interval)
      }
    }
  }, [autoRefresh, refreshInterval, fetchData, refreshPrices])

  const handleTypeClick = (type: string) => {
    const newSelectedType = selectedType === type ? null : type
    setSelectedType(newSelectedType)

    if (onAssetTypeFilter) {
      onAssetTypeFilter(newSelectedType)
    }
  }

  if (loading) {
    return (
      <div className="open-positions-card loading">
        <div className="loading-spinner"></div>
        <p>Loading open positions...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="open-positions-card error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button onClick={fetchData} className="retry-button">
          Retry
        </button>
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="open-positions-card">
      <div className="card-header">
        <h2>Open Positions</h2>
        {data.last_updated && (
          <div className="last-updated">
            Last updated: {formatDateTime(data.last_updated)}
            {autoRefresh && (
              <span className="auto-refresh-badge">
                • Auto-refresh: {formatRefreshInterval(refreshInterval)}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="main-metrics">
        <div className="metric-card primary">
          <div className="metric-label">Total Value</div>
          <div className="metric-value">{formatCurrency(data.total_value, BASE_CURRENCY)}</div>
          <div className="metric-subtitle">
            Cost basis: {formatCurrency(data.total_cost_basis, BASE_CURRENCY)}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Unrealized P&L</div>
          <div className={`metric-value ${getPnLClassName(data.unrealized_pnl)}`}>
            {formatPnLChange(data.unrealized_pnl, data.unrealized_pnl_percent, BASE_CURRENCY)}
          </div>
          <div className="metric-subtitle">From open positions only</div>
        </div>
      </div>

      <div className="breakdown-section">
        <h3>Asset Breakdown</h3>
        <div className="breakdown-grid">
          <div
            className={`breakdown-item ${selectedType === 'stock' ? 'selected' : ''}`}
            onClick={() => handleTypeClick('stock')}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleTypeClick('stock')
              }
            }}
          >
            <div className="breakdown-header">
              <div className="asset-icon">📊</div>
              <div className="asset-label">Stocks</div>
            </div>
            <div className="breakdown-value">
              {formatCurrency(data.breakdown.stocks.value, BASE_CURRENCY)}
            </div>
            <div className={`breakdown-pnl ${getPnLClassName(data.breakdown.stocks.pnl)}`}>
              {formatPnLChange(data.breakdown.stocks.pnl, data.breakdown.stocks.pnl_percent, BASE_CURRENCY)}
            </div>
          </div>

          <div
            className={`breakdown-item ${selectedType === 'crypto' ? 'selected' : ''}`}
            onClick={() => handleTypeClick('crypto')}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleTypeClick('crypto')
              }
            }}
          >
            <div className="breakdown-header">
              <div className="asset-icon">₿</div>
              <div className="asset-label">Crypto</div>
            </div>
            <div className="breakdown-value">
              {formatCurrency(data.breakdown.crypto.value, BASE_CURRENCY)}
            </div>
            <div className={`breakdown-pnl ${getPnLClassName(data.breakdown.crypto.pnl)}`}>
              {formatPnLChange(data.breakdown.crypto.pnl, data.breakdown.crypto.pnl_percent, BASE_CURRENCY)}
            </div>
          </div>

          <div
            className={`breakdown-item ${selectedType === 'metal' ? 'selected' : ''}`}
            onClick={() => handleTypeClick('metal')}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleTypeClick('metal')
              }
            }}
          >
            <div className="breakdown-header">
              <div className="asset-icon">🥇</div>
              <div className="asset-label">Metals</div>
            </div>
            <div className="breakdown-value">
              {formatCurrency(data.breakdown.metals.value, BASE_CURRENCY)}
            </div>
            <div className={`breakdown-pnl ${getPnLClassName(data.breakdown.metals.pnl)}`}>
              {formatPnLChange(data.breakdown.metals.pnl, data.breakdown.metals.pnl_percent, BASE_CURRENCY)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
