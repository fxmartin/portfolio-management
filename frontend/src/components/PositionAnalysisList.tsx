// ABOUTME: List of portfolio positions for AI analysis selection
// ABOUTME: Shows all positions with current value and P&L, clickable for detailed analysis

import { useState, useEffect } from 'react'
import axios from 'axios'
import './PositionAnalysisList.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Position {
  symbol: string
  asset_type: string
  quantity: number
  current_price: number
  current_value: number
  total_cost_basis: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
}

interface PositionAnalysisListProps {
  onSelectPosition: (symbol: string) => void
  selectedSymbol: string | null
}

export const PositionAnalysisList: React.FC<PositionAnalysisListProps> = ({
  onSelectPosition,
  selectedSymbol,
}) => {
  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const response = await axios.get<Position[]>(`${API_URL}/api/portfolio/positions`)
        setPositions(response.data)
      } catch (err: any) {
        console.error('Failed to fetch positions:', err)
        setError('Failed to load positions')
      } finally {
        setLoading(false)
      }
    }

    fetchPositions()
  }, [])

  if (loading) {
    return (
      <div className="position-list loading">
        <div className="spinner"></div>
        <p>Loading positions...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="position-list error">
        <p>{error}</p>
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <div className="position-list empty">
        <p>No positions to analyze</p>
        <span>Import transactions to get started</span>
      </div>
    )
  }

  return (
    <div className="position-list">
      <h3>Your Positions</h3>
      <p className="subtitle">Select a position for AI-powered analysis</p>

      <div className="position-items">
        {positions.map((position) => (
          <div
            key={position.symbol}
            className={`position-item ${
              selectedSymbol === position.symbol ? 'selected' : ''
            }`}
            onClick={() => onSelectPosition(position.symbol)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onSelectPosition(position.symbol)
              }
            }}
            aria-pressed={selectedSymbol === position.symbol}
          >
            <div className="position-header">
              <div className="position-symbol">{position.symbol}</div>
              <div className="asset-badge">{position.asset_type}</div>
            </div>

            <div className="position-value">
              €{position.current_value?.toFixed(2) ?? '0.00'}
            </div>

            <div className="position-stats">
              <div className="stat">
                <span className="stat-label">Quantity</span>
                <span className="stat-value">{position.quantity?.toFixed(4) ?? 'N/A'}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Avg Price</span>
                <span className="stat-value">€{position.current_price?.toFixed(2) ?? 'N/A'}</span>
              </div>
            </div>

            <div
              className={`position-pnl ${
                (position.unrealized_pnl ?? 0) >= 0 ? 'positive' : 'negative'
              }`}
            >
              <span className="pnl-amount">
                {(position.unrealized_pnl ?? 0) >= 0 ? '+' : ''}
                €{position.unrealized_pnl?.toFixed(2) ?? '0.00'}
              </span>
              <span className="pnl-percentage">
                ({(position.unrealized_pnl ?? 0) >= 0 ? '+' : ''}
                {position.unrealized_pnl_percent?.toFixed(2) ?? '0.00'}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default PositionAnalysisList
