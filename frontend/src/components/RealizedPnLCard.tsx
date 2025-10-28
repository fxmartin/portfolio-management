// ABOUTME: Realized P&L summary card showing closed positions with fee breakdown
// ABOUTME: Displays gross realized P&L, total fees, and net P&L by asset type

import { useEffect, useState } from 'react'
import axios from 'axios'
import { formatCurrency, getPnLClassName } from '../utils/formatters'
import { API_CONFIG, PORTFOLIO_CONFIG } from '../config/app.config'
import ClosedTransactionsPanel from './ClosedTransactionsPanel'
import './RealizedPnLCard.css'

const API_URL = API_CONFIG.BASE_URL
const BASE_CURRENCY = PORTFOLIO_CONFIG.BASE_CURRENCY

interface AssetTypeBreakdown {
  realized_pnl: number
  fees: number
  net_pnl: number
  closed_count: number
}

interface RealizedPnLData {
  total_realized_pnl: number
  total_fees: number
  net_pnl: number
  closed_positions_count: number
  breakdown: {
    stocks: AssetTypeBreakdown
    crypto: AssetTypeBreakdown
    metals: AssetTypeBreakdown
  }
  last_updated: string
}

const RealizedPnLCard = () => {
  const [data, setData] = useState<RealizedPnLData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedAssetTypes, setExpandedAssetTypes] = useState<Set<string>>(new Set())

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.get(`${API_URL}/api/portfolio/realized-pnl`)
        setData(response.data)
      } catch (err) {
        console.error('Failed to fetch realized P&L:', err)
        setError('Failed to load realized P&L data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="realized-pnl-card loading">
        <div className="spinner" />
        <p>Loading realized P&L...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="realized-pnl-card error">
        <p className="error-message">{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const toggleAssetTypeExpansion = (assetType: string) => {
    const newExpanded = new Set(expandedAssetTypes)
    if (newExpanded.has(assetType)) {
      newExpanded.delete(assetType)
    } else {
      newExpanded.add(assetType)
    }
    setExpandedAssetTypes(newExpanded)
  }

  // Filter out asset types with no closed positions
  const activeAssetTypes = Object.entries(data.breakdown)
    .filter(([_, breakdown]) => breakdown.closed_count > 0)
    .map(([type]) => type)

  return (
    <div className="realized-pnl-card">
      <div className="card-header">
        <h2>Realized P&L</h2>
        {data.closed_positions_count > 0 && (
          <span className="closed-count">
            {data.closed_positions_count} position{data.closed_positions_count !== 1 ? 's' : ''} with sales
          </span>
        )}
      </div>

      {data.closed_positions_count === 0 ? (
        <div className="empty-state">
          <p>No closed positions yet</p>
          <p className="empty-state-hint">Realized P&L will appear here when you fully close a position by selling all shares</p>
        </div>
      ) : (
        <>
          <div className="main-metrics">
            <div className="metric-card">
              <div className="metric-label">Total Realized P&L</div>
              <div className={`metric-value ${getPnLClassName(data.total_realized_pnl)}`}>
                {formatCurrency(data.total_realized_pnl, BASE_CURRENCY)}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Transaction Fees</div>
              <div className="metric-value fees">
                {formatCurrency(data.total_fees, BASE_CURRENCY)}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Net P&L</div>
              <div className={`metric-value ${getPnLClassName(data.net_pnl)}`}>
                {formatCurrency(data.net_pnl, BASE_CURRENCY)}
              </div>
            </div>
          </div>

          {activeAssetTypes.length > 0 && (
            <div className="breakdown-section">
              <h3>Breakdown by Asset Type</h3>
              <div className="breakdown-grid">
                {activeAssetTypes.includes('stocks') && (
                  <AssetBreakdownItem
                    icon="📈"
                    label="Stocks"
                    data={data.breakdown.stocks}
                    onClick={() => toggleAssetTypeExpansion('stocks')}
                    isExpanded={expandedAssetTypes.has('stocks')}
                  />
                )}
                {activeAssetTypes.includes('crypto') && (
                  <AssetBreakdownItem
                    icon="💰"
                    label="Crypto"
                    data={data.breakdown.crypto}
                    onClick={() => toggleAssetTypeExpansion('crypto')}
                    isExpanded={expandedAssetTypes.has('crypto')}
                  />
                )}
                {activeAssetTypes.includes('metals') && (
                  <AssetBreakdownItem
                    icon="🥇"
                    label="Metals"
                    data={data.breakdown.metals}
                    onClick={() => toggleAssetTypeExpansion('metals')}
                    isExpanded={expandedAssetTypes.has('metals')}
                  />
                )}
              </div>
              {expandedAssetTypes.has('stocks') && (
                <ClosedTransactionsPanel
                  assetType="stocks"
                  onClose={() => toggleAssetTypeExpansion('stocks')}
                />
              )}
              {expandedAssetTypes.has('crypto') && (
                <ClosedTransactionsPanel
                  assetType="crypto"
                  onClose={() => toggleAssetTypeExpansion('crypto')}
                />
              )}
              {expandedAssetTypes.has('metals') && (
                <ClosedTransactionsPanel
                  assetType="metals"
                  onClose={() => toggleAssetTypeExpansion('metals')}
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

interface AssetBreakdownItemProps {
  icon: string
  label: string
  data: AssetTypeBreakdown
  onClick: () => void
  isExpanded: boolean
}

const AssetBreakdownItem = ({ icon, label, data, onClick, isExpanded }: AssetBreakdownItemProps) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <div
      className={`breakdown-item ${isExpanded ? 'expanded' : ''}`}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-expanded={isExpanded}
      aria-label={`${label} - Click to ${isExpanded ? 'collapse' : 'expand'} transaction details`}
    >
      <div className="breakdown-header">
        <span className={`expand-indicator ${isExpanded ? 'expanded' : ''}`}>▶</span>
        <span className="icon">{icon}</span>
        <span className="label">{label}</span>
      </div>
      <div className="breakdown-metrics">
        <div className="breakdown-row">
          <span className={`row-value ${getPnLClassName(data.net_pnl)}`}>
            {formatCurrency(data.net_pnl, BASE_CURRENCY)}
          </span>
        </div>
      </div>
    </div>
  )
}

export default RealizedPnLCard
