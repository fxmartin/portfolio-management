// ABOUTME: Open positions overview card showing total value and unrealized P&L
// ABOUTME: Displays breakdown by asset type with clickable filters for holdings table

import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { formatCurrency, formatPnLChange, formatDateTime, getPnLClassName } from '../utils/formatters'
import { API_CONFIG, PORTFOLIO_CONFIG, REFRESH_INTERVALS, formatRefreshInterval } from '../config/app.config'
import { getMarketStatus, getStatusIndicator, type MarketStatus } from '../utils/marketStatus'
import AssetAllocationChart from './AssetAllocationChart'
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
  total_fees: number
  fee_transaction_count: number
}

interface OpenPositionsCardProps {
  onAssetTypeFilter?: (assetType: string | null) => void
  autoRefresh?: boolean
  refreshInterval?: number
}

type TrendDirection = 'up' | 'down' | 'neutral'

interface PnLSnapshot {
  timestamp: number
  stocks: number
  crypto: number
  metals: number
}

// Trend tracking utilities
const TREND_THRESHOLD = 0.01 // €0.01
const SNAPSHOT_MAX_AGE = 25 * 60 * 60 * 1000 // 25 hours in milliseconds

const storePnLSnapshot = (breakdown: OpenPositionsData['breakdown']): void => {
  const snapshot: PnLSnapshot = {
    timestamp: Date.now(),
    stocks: breakdown.stocks.pnl,
    crypto: breakdown.crypto.pnl,
    metals: breakdown.metals.pnl,
  }
  localStorage.setItem('pnl_snapshot', JSON.stringify(snapshot))
}

const calculateTrend = (currentPnL: number, assetType: 'stocks' | 'crypto' | 'metals'): TrendDirection => {
  try {
    const stored = localStorage.getItem('pnl_snapshot')
    if (!stored) return 'neutral'

    const snapshot: PnLSnapshot = JSON.parse(stored)
    const timeDiff = Date.now() - snapshot.timestamp

    // Ignore stale snapshots (> 25 hours)
    if (timeDiff > SNAPSHOT_MAX_AGE) return 'neutral'

    const previousPnL = snapshot[assetType] || 0
    const diff = currentPnL - previousPnL

    // Apply threshold to avoid noise
    if (Math.abs(diff) < TREND_THRESHOLD) return 'neutral'

    return diff > 0 ? 'up' : 'down'
  } catch (error) {
    console.error('Error calculating trend:', error)
    return 'neutral'
  }
}

const getTrendArrow = (trend: TrendDirection): string => {
  switch (trend) {
    case 'up':
      return '↑'
    case 'down':
      return '↓'
    default:
      return '→'
  }
}

const getTrendClassName = (trend: TrendDirection): string => {
  return `trend-${trend}`
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
  const [marketStatuses, setMarketStatuses] = useState<{
    stocks: MarketStatus
    crypto: MarketStatus
    metals: MarketStatus
  }>({
    stocks: getMarketStatus('stocks'),
    crypto: getMarketStatus('crypto'),
    metals: getMarketStatus('metals'),
  })

  const fetchData = useCallback(async () => {
    try {
      setError(null)
      const response = await axios.get<OpenPositionsData>(`${API_URL}/api/portfolio/open-positions`)
      setData(response.data)

      // Store P&L snapshot for trend tracking
      if (response.data.breakdown) {
        storePnLSnapshot(response.data.breakdown)
      }

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

  const updateMarketStatuses = useCallback(() => {
    setMarketStatuses({
      stocks: getMarketStatus('stocks'),
      crypto: getMarketStatus('crypto'),
      metals: getMarketStatus('metals'),
    })
  }, [])

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

  // Update market statuses every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      updateMarketStatuses()
    }, 60000) // 60 seconds

    return () => clearInterval(interval)
  }, [updateMarketStatuses])

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

  if (!data || !data.breakdown) {
    return null
  }

  // Helper to determine which asset types have non-zero values
  const assetTypes = [
    { key: 'stocks' as const, label: 'Stocks', icon: '📊', filterType: 'stock', data: data.breakdown.stocks },
    { key: 'crypto' as const, label: 'Crypto', icon: '₿', filterType: 'crypto', data: data.breakdown.crypto },
    { key: 'metals' as const, label: 'Metals', icon: '🥇', filterType: 'metal', data: data.breakdown.metals },
  ].filter(asset => asset.data.value > 0) // Only show assets with non-zero values

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
        <div className="metric-card">
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
          <div className="metric-subtitle">
            Current Holdings Fees {formatCurrency(data.total_fees, BASE_CURRENCY)} ({data.fee_transaction_count} trade{data.fee_transaction_count === 1 ? '' : 's'})
          </div>
        </div>
      </div>

      <div className="breakdown-section">
        <h3>Asset Breakdown</h3>
        <div className="breakdown-container">
          <div className="breakdown-grid">
            {assetTypes.map((asset) => (
              <div
                key={asset.key}
                className={`breakdown-item ${selectedType === asset.filterType ? 'selected' : ''}`}
                onClick={() => handleTypeClick(asset.filterType)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleTypeClick(asset.filterType)
                  }
                }}
              >
                <div className="breakdown-first-line">
                  <div className="breakdown-header">
                    <div className="asset-icon">{asset.icon}</div>
                    <div className="asset-label">{asset.label}</div>
                    <span className={`market-status-badge market-status-${marketStatuses[asset.key].session}`}>
                      <span className="status-indicator">{getStatusIndicator(marketStatuses[asset.key].session)}</span>
                      <span className="status-text">{marketStatuses[asset.key].statusText}</span>
                    </span>
                  </div>
                  <div className="breakdown-value">
                    {formatCurrency(asset.data.value, BASE_CURRENCY)}
                  </div>
                </div>
                <div className="breakdown-pnl-line">
                  <span className={`pnl-value ${getPnLClassName(asset.data.pnl)}`}>
                    {formatCurrency(asset.data.pnl, BASE_CURRENCY)}
                  </span>
                  <span className={`trend-arrow ${getTrendClassName(calculateTrend(asset.data.pnl, asset.key))}`}>
                    {getTrendArrow(calculateTrend(asset.data.pnl, asset.key))}
                  </span>
                  <span className={`pnl-percent ${getPnLClassName(asset.data.pnl)}`}>
                    {asset.data.pnl >= 0 ? '+' : ''}{asset.data.pnl_percent.toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div className="breakdown-chart">
            <AssetAllocationChart
              breakdown={data.breakdown}
              totalValue={data.total_value}
              currency={BASE_CURRENCY}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
