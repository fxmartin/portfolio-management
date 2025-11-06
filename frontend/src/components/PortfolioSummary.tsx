// ABOUTME: Portfolio summary component displaying total value, P&L, and cash balances
// ABOUTME: Main dashboard card with real-time portfolio statistics

import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import { formatCurrency, formatPnLChange, formatDateTime, getPnLClassName } from '../utils/formatters'
import { API_CONFIG, PORTFOLIO_CONFIG, formatRefreshInterval } from '../config/app.config'
import { useSettings } from '../contexts/SettingsContext'
import './PortfolioSummary.css'

const API_URL = API_CONFIG.BASE_URL
const BASE_CURRENCY = PORTFOLIO_CONFIG.BASE_CURRENCY

export interface PortfolioSummaryData {
  total_value: number
  cash_balances: Record<string, number>
  total_cash: number
  total_investment_value: number
  total_cost_basis: number
  total_pnl: number
  total_pnl_percent: number
  unrealized_pnl: number
  realized_pnl: number
  day_change: number
  day_change_percent: number
  positions_count: number
  last_updated: string | null
}

interface PortfolioSummaryProps {
  onRefresh?: () => void
  autoRefresh?: boolean
  refreshInterval?: number
}

export default function PortfolioSummary({
  onRefresh,
  autoRefresh = true,
  refreshInterval,
}: PortfolioSummaryProps) {
  const { cryptoRefreshSeconds } = useSettings()
  const [summary, setSummary] = useState<PortfolioSummaryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  // Use crypto interval as baseline for portfolio summary (faster updates)
  const effectiveRefreshInterval = refreshInterval || (cryptoRefreshSeconds * 1000)

  const fetchSummary = useCallback(async () => {
    try {
      setError(null)
      const response = await axios.get<PortfolioSummaryData>(`${API_URL}/api/portfolio/summary`)
      setSummary(response.data)
      setLoading(false)

      if (onRefresh) {
        onRefresh()
      }
    } catch (err) {
      console.error('Failed to fetch portfolio summary:', err)
      setError('Failed to load portfolio data')
      setLoading(false)
    }
  }, [onRefresh])

  const refreshPrices = useCallback(async () => {
    try {
      setRefreshing(true)
      await axios.post(`${API_URL}/api/portfolio/refresh-prices`)
      await fetchSummary()
    } catch (err) {
      console.error('Failed to refresh prices:', err)
    } finally {
      setRefreshing(false)
    }
  }, [fetchSummary])

  useEffect(() => {
    // Initial load - just fetch data without refreshing prices
    fetchSummary()

    if (autoRefresh) {
      console.log(`[PortfolioSummary] Setting up auto-refresh with interval: ${effectiveRefreshInterval}ms (${cryptoRefreshSeconds}s)`)
      const interval = setInterval(() => {
        console.log('[PortfolioSummary] Auto-refresh triggered - fetching new prices from Yahoo Finance')
        refreshPrices()
      }, effectiveRefreshInterval)
      return () => {
        console.log('[PortfolioSummary] Clearing auto-refresh interval')
        clearInterval(interval)
      }
    }
  }, [autoRefresh, effectiveRefreshInterval, cryptoRefreshSeconds, fetchSummary, refreshPrices])

  if (loading) {
    return (
      <div className="portfolio-summary loading">
        <div className="loading-spinner"></div>
        <p>Loading portfolio...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="portfolio-summary error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button onClick={fetchSummary} className="retry-button">
          Retry
        </button>
      </div>
    )
  }

  if (!summary) {
    return null
  }

  const hasCashBalances = summary.cash_balances && Object.keys(summary.cash_balances).length > 0
  const hasPositions = summary.positions_count > 0

  return (
    <div className="portfolio-summary">
      <div className="summary-header">
        <div className="header-left">
          <h2>Portfolio Summary</h2>
          {summary.last_updated && (
            <div className="last-updated">
              Last updated: {formatDateTime(summary.last_updated)}
              {autoRefresh && (
                <span className="auto-refresh-badge">
                  • Auto-refresh: {formatRefreshInterval(refreshInterval)}
                </span>
              )}
            </div>
          )}
        </div>
        <button
          onClick={refreshPrices}
          disabled={refreshing}
          className="refresh-button"
          title="Refresh prices from Yahoo Finance"
        >
          {refreshing ? '↻ Refreshing...' : '↻ Refresh Prices'}
        </button>
      </div>

      <div className="summary-grid">
        {/* Total Portfolio Value */}
        <div className="summary-card primary">
          <div className="card-label">Total Value</div>
          <div className="card-value">{formatCurrency(summary.total_value, BASE_CURRENCY)}</div>
          {summary.day_change !== 0 && (
            <div className={`card-change ${getPnLClassName(summary.day_change)}`}>
              {formatPnLChange(summary.day_change, summary.day_change_percent, BASE_CURRENCY)}
              <span className="change-label"> today</span>
            </div>
          )}
        </div>

        {/* Total P&L */}
        <div className="summary-card">
          <div className="card-label">Total P&L</div>
          <div className={`card-value ${getPnLClassName(summary.total_pnl)}`}>
            {formatCurrency(summary.total_pnl, BASE_CURRENCY)}
          </div>
          <div className={`card-subtitle ${getPnLClassName(summary.total_pnl)}`}>
            {summary.total_pnl_percent.toFixed(2)}% return
          </div>
        </div>

        {/* Unrealized P&L */}
        <div className="summary-card">
          <div className="card-label">Unrealized P&L</div>
          <div className={`card-value ${getPnLClassName(summary.unrealized_pnl)}`}>
            {formatCurrency(summary.unrealized_pnl, BASE_CURRENCY)}
          </div>
          <div className="card-subtitle">
            {hasPositions ? `${summary.positions_count} position${summary.positions_count === 1 ? '' : 's'}` : 'No positions'}
          </div>
        </div>

        {/* Realized P&L */}
        <div className="summary-card">
          <div className="card-label">Realized P&L</div>
          <div className={`card-value ${getPnLClassName(summary.realized_pnl)}`}>
            {formatCurrency(summary.realized_pnl, BASE_CURRENCY)}
          </div>
          <div className="card-subtitle">From closed positions</div>
        </div>
      </div>

      {/* Cash Balances Section */}
      {hasCashBalances && (
        <div className="cash-balances-section">
          <h3>Cash Balances</h3>
          <div className="cash-balances-grid">
            {Object.entries(summary.cash_balances).map(([currency, amount]) => (
              <div key={currency} className="cash-balance-card">
                <div className="currency-code">{currency}</div>
                <div className="currency-amount">{formatCurrency(amount, currency)}</div>
              </div>
            ))}
          </div>
          <div className="cash-total">
            Total Cash: {formatCurrency(summary.total_cash, BASE_CURRENCY)}
          </div>
        </div>
      )}

      {/* Investment Breakdown */}
      <div className="investment-breakdown">
        <div className="breakdown-row">
          <span className="breakdown-label">Investment Value:</span>
          <span className="breakdown-value">{formatCurrency(summary.total_investment_value, BASE_CURRENCY)}</span>
        </div>
        <div className="breakdown-row">
          <span className="breakdown-label">Cost Basis:</span>
          <span className="breakdown-value">{formatCurrency(summary.total_cost_basis, BASE_CURRENCY)}</span>
        </div>
        <div className="breakdown-row">
          <span className="breakdown-label">Cash:</span>
          <span className="breakdown-value">{formatCurrency(summary.total_cash, BASE_CURRENCY)}</span>
        </div>
        <div className="breakdown-row total">
          <span className="breakdown-label">Total Portfolio:</span>
          <span className="breakdown-value">{formatCurrency(summary.total_value, BASE_CURRENCY)}</span>
        </div>
      </div>
    </div>
  )
}
