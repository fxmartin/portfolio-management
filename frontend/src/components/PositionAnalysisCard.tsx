// ABOUTME: Display AI-powered analysis for a specific position
// ABOUTME: Shows Claude's insights, recommendations, and markdown-formatted analysis

import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { RefreshCw, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react'
import { getPositionAnalysis } from '../api/analysis'
import type { PositionAnalysisResponse } from '../api/analysis'
import './PositionAnalysisCard.css'

interface PositionAnalysisCardProps {
  symbol: string
}

const RECOMMENDATION_CONFIG = {
  BUY_MORE: {
    icon: TrendingUp,
    color: '#059669',
    label: 'Buy More',
    bgColor: '#d1fae5',
  },
  HOLD: {
    icon: Minus,
    color: '#3b82f6',
    label: 'Hold',
    bgColor: '#dbeafe',
  },
  REDUCE: {
    icon: TrendingDown,
    color: '#f59e0b',
    label: 'Reduce',
    bgColor: '#fef3c7',
  },
  SELL: {
    icon: AlertCircle,
    color: '#dc2626',
    label: 'Sell',
    bgColor: '#fee2e2',
  },
}

export const PositionAnalysisCard: React.FC<PositionAnalysisCardProps> = ({ symbol }) => {
  const [analysis, setAnalysis] = useState<PositionAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    loadAnalysis()
  }, [symbol])

  const loadAnalysis = async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    setError(null)

    try {
      const result = await getPositionAnalysis(symbol, forceRefresh)
      setAnalysis(result)
    } catch (err: any) {
      console.error(`Failed to load analysis for ${symbol}:`, err)
      setError(err.response?.data?.detail || 'Failed to load analysis. Please try again.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    loadAnalysis(true)
  }

  if (loading) {
    return (
      <div className="position-analysis-card loading">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Analyzing {symbol}...</p>
          <span className="loading-hint">Generating insights with Claude AI</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="position-analysis-card error">
        <div className="error-content">
          <h3>Unable to Load Analysis</h3>
          <p>{error}</p>
          <button onClick={() => loadAnalysis()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!analysis) {
    return null
  }

  const recConfig = RECOMMENDATION_CONFIG[analysis.recommendation]
  const RecommendationIcon = recConfig.icon

  return (
    <div className="position-analysis-card">
      <div className="card-header">
        <div className="header-left">
          <h2>Analysis: {analysis.symbol}</h2>
          {analysis.cached && (
            <span className="cache-badge" title="Analysis loaded from cache">
              Cached
            </span>
          )}
        </div>
        <div className="header-right">
          <span className="timestamp">
            {new Date(analysis.generated_at).toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })}
          </span>
          <button
            onClick={handleRefresh}
            className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
            disabled={refreshing}
            title="Generate new analysis"
            aria-label="Refresh analysis"
          >
            <RefreshCw size={18} />
            {refreshing && <span>Refreshing...</span>}
          </button>
        </div>
      </div>

      {/* Recommendation Badge */}
      <div
        className="recommendation-badge"
        style={{
          background: recConfig.bgColor,
          borderLeft: `4px solid ${recConfig.color}`,
        }}
      >
        <RecommendationIcon size={24} color={recConfig.color} />
        <div className="recommendation-content">
          <span className="recommendation-label">Recommendation</span>
          <span className="recommendation-value" style={{ color: recConfig.color }}>
            {recConfig.label}
          </span>
        </div>
      </div>

      {/* Analysis Content */}
      <div className="card-body">
        <ReactMarkdown>{analysis.analysis}</ReactMarkdown>
      </div>

      {/* Footer */}
      <div className="card-footer">
        <span className="token-count" title="Tokens used for this analysis">
          {analysis.tokens_used.toLocaleString()} tokens
        </span>
      </div>
    </div>
  )
}

export default PositionAnalysisCard
