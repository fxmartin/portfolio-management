// ABOUTME: Main Rebalancing page component for portfolio rebalancing recommendations
// ABOUTME: Integrates allocation analysis, AI recommendations, and visual comparison charts

import { useState, useEffect, useCallback } from 'react'
import { Scale } from 'lucide-react'
import AllocationComparisonChart from '../components/AllocationComparisonChart'
import RebalancingSummaryCard from '../components/RebalancingSummaryCard'
import RebalancingRecommendationsList from '../components/RebalancingRecommendationsList'
import { getRebalancingAnalysis, getRebalancingRecommendations } from '../api/rebalancing'
import type { RebalancingAnalysis, RebalancingRecommendationResponse } from '../api/rebalancing'
import './Rebalancing.css'

type AllocationModel = 'moderate' | 'aggressive' | 'conservative' | 'custom'

interface RebalancingPageProps {
  onNavigateToTransactions?: () => void
}

export const RebalancingPage: React.FC<RebalancingPageProps> = ({ onNavigateToTransactions }) => {
  const [selectedModel, setSelectedModel] = useState<AllocationModel>('moderate')
  const [customStocks, setCustomStocks] = useState<number>(50)
  const [customCrypto, setCustomCrypto] = useState<number>(30)
  const [customMetals, setCustomMetals] = useState<number>(20)

  const [analysis, setAnalysis] = useState<RebalancingAnalysis | null>(null)
  const [recommendations, setRecommendations] = useState<RebalancingRecommendationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load rebalancing data
  const loadRebalancingData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const analysisData = await getRebalancingAnalysis(
        selectedModel,
        selectedModel === 'custom' ? customStocks : undefined,
        selectedModel === 'custom' ? customCrypto : undefined,
        selectedModel === 'custom' ? customMetals : undefined
      )
      setAnalysis(analysisData)

      // Only fetch recommendations if rebalancing is needed
      if (analysisData.rebalancing_required) {
        const recsData = await getRebalancingRecommendations(
          selectedModel,
          selectedModel === 'custom' ? customStocks : undefined,
          selectedModel === 'custom' ? customCrypto : undefined,
          selectedModel === 'custom' ? customMetals : undefined
        )
        setRecommendations(recsData)
      } else {
        setRecommendations(null)
      }
    } catch (err) {
      console.error('Failed to load rebalancing data:', err)
      setError('Failed to load rebalancing data. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [selectedModel, customStocks, customCrypto, customMetals])

  // Load data when model changes
  useEffect(() => {
    loadRebalancingData()
  }, [loadRebalancingData])

  // Validate custom allocation sum
  const customAllocationSum = customStocks + customCrypto + customMetals
  const isCustomValid = customAllocationSum === 100

  const handleCustomApply = () => {
    if (isCustomValid) {
      loadRebalancingData()
    }
  }

  const handleCreateTransaction = (transactionData: any) => {
    // Navigate to transactions tab
    if (onNavigateToTransactions) {
      onNavigateToTransactions()
    }
  }

  return (
    <div className="rebalancing-page">
      {/* Page Header */}
      <header className="page-header">
        <div className="header-content">
          <div className="header-icon">
            <Scale size={32} />
          </div>
          <div className="header-text">
            <h1>Portfolio Rebalancing</h1>
            <p className="subtitle">
              AI-powered recommendations to optimize your asset allocation
            </p>
          </div>
        </div>
      </header>

      {/* Model Selector */}
      <section className="model-selector-section">
        <div className="model-selector-card">
          <h3>Target Allocation Model</h3>
          <div className="model-buttons">
            <button
              className={`model-button ${selectedModel === 'moderate' ? 'active' : ''}`}
              onClick={() => setSelectedModel('moderate')}
            >
              <div className="model-name">Moderate</div>
              <div className="model-allocation">60% / 25% / 15%</div>
            </button>
            <button
              className={`model-button ${selectedModel === 'aggressive' ? 'active' : ''}`}
              onClick={() => setSelectedModel('aggressive')}
            >
              <div className="model-name">Aggressive</div>
              <div className="model-allocation">50% / 40% / 10%</div>
            </button>
            <button
              className={`model-button ${selectedModel === 'conservative' ? 'active' : ''}`}
              onClick={() => setSelectedModel('conservative')}
            >
              <div className="model-name">Conservative</div>
              <div className="model-allocation">70% / 15% / 15%</div>
            </button>
            <button
              className={`model-button ${selectedModel === 'custom' ? 'active' : ''}`}
              onClick={() => setSelectedModel('custom')}
            >
              <div className="model-name">Custom</div>
              <div className="model-allocation">Your choice</div>
            </button>
          </div>

          {/* Custom Allocation Inputs */}
          {selectedModel === 'custom' && (
            <div className="custom-allocation-inputs">
              <div className="input-group">
                <label htmlFor="custom-stocks">Stocks (%)</label>
                <input
                  id="custom-stocks"
                  type="number"
                  min="0"
                  max="100"
                  value={customStocks}
                  onChange={(e) => setCustomStocks(parseInt(e.target.value) || 0)}
                />
              </div>
              <div className="input-group">
                <label htmlFor="custom-crypto">Crypto (%)</label>
                <input
                  id="custom-crypto"
                  type="number"
                  min="0"
                  max="100"
                  value={customCrypto}
                  onChange={(e) => setCustomCrypto(parseInt(e.target.value) || 0)}
                />
              </div>
              <div className="input-group">
                <label htmlFor="custom-metals">Metals (%)</label>
                <input
                  id="custom-metals"
                  type="number"
                  min="0"
                  max="100"
                  value={customMetals}
                  onChange={(e) => setCustomMetals(parseInt(e.target.value) || 0)}
                />
              </div>
              <div className="input-validation">
                <span className={isCustomValid ? 'valid' : 'invalid'}>
                  Total: {customAllocationSum}% {isCustomValid ? '✓' : '(must equal 100%)'}
                </span>
                <button
                  className="apply-button"
                  onClick={handleCustomApply}
                  disabled={!isCustomValid}
                >
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing portfolio allocation...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="error-state">
          <p>{error}</p>
          <button onClick={loadRebalancingData}>Retry</button>
        </div>
      )}

      {/* Main Content */}
      {!loading && !error && analysis && (
        <>
          {/* Summary Card */}
          <RebalancingSummaryCard analysis={analysis} />

          {/* Two-Column Layout */}
          <div className="rebalancing-grid">
            {/* Allocation Chart - Left */}
            <section className="chart-section">
              <AllocationComparisonChart analysis={analysis} />
            </section>

            {/* Recommendations - Right */}
            <section className="recommendations-section">
              <RebalancingRecommendationsList
                analysis={analysis}
                recommendations={recommendations}
                onCreateTransaction={handleCreateTransaction}
              />
            </section>
          </div>
        </>
      )}
    </div>
  )
}

export default RebalancingPage
