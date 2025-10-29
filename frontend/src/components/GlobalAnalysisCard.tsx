// ABOUTME: Display AI-powered global portfolio market analysis from Claude
// ABOUTME: Shows market overview with markdown rendering, cache indicators, and refresh functionality

import { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { RefreshCw } from 'lucide-react'
import { getGlobalAnalysis } from '../api/analysis'
import type { GlobalAnalysisResponse } from '../api/analysis'
import { GlobalCryptoMarket } from './GlobalCryptoMarket'
import { GlobalMarketIndicators } from './GlobalMarketIndicators'
import './GlobalAnalysisCard.css'

export const GlobalAnalysisCard: React.FC = () => {
  const [analysis, setAnalysis] = useState<GlobalAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const loadAnalysis = useCallback(async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    setError(null)

    try {
      const result = await getGlobalAnalysis(forceRefresh)
      setAnalysis(result)
    } catch (err: any) {
      console.error('Failed to load global analysis:', err)
      setError(err.response?.data?.detail || 'Failed to load analysis. Please try again.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadAnalysis()
  }, [loadAnalysis])

  const handleRefresh = () => {
    loadAnalysis(true)
  }

  if (loading) {
    return (
      <div className="global-analysis-card loading">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Generating market analysis with Claude AI...</p>
          <span className="loading-hint">This may take 10-30 seconds</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="global-analysis-card error">
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

  return (
    <div className="global-analysis-card">
      <div className="card-header">
        <div className="header-left">
          <h2>Market Overview</h2>
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

      {/* Global Market Indicators (if available) */}
      {analysis.market_indicators && (
        <GlobalMarketIndicators data={analysis.market_indicators} />
      )}

      {/* Global Crypto Market Data (if available) */}
      {analysis.global_crypto_market && (
        <GlobalCryptoMarket data={analysis.global_crypto_market} />
      )}

      <div className="card-body">
        <ReactMarkdown>{analysis.analysis}</ReactMarkdown>
      </div>

      <div className="card-footer">
        <span className="token-count" title="Tokens used for this analysis">
          {analysis.tokens_used.toLocaleString()} tokens
        </span>
      </div>
    </div>
  )
}

export default GlobalAnalysisCard
