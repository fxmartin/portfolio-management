// ABOUTME: List of AI-powered rebalancing recommendations with action buttons
// ABOUTME: Displays prioritized buy/sell recommendations with copy and expand functionality

import { useState, useEffect } from 'react'
import type { RebalancingAnalysis, RebalancingRecommendationResponse } from '../api/rebalancing'
import { copyTransactionDataToClipboard } from '../api/rebalancing'
import { TrendingUp, TrendingDown, Copy, ChevronDown, ChevronUp, AlertCircle, Plus, Check } from 'lucide-react'
import './RebalancingRecommendationsList.css'

interface RebalancingRecommendationsListProps {
  analysis: RebalancingAnalysis
  recommendations: RebalancingRecommendationResponse | null
  onCreateTransaction?: (transactionData: any) => void
}

const RebalancingRecommendationsList: React.FC<RebalancingRecommendationsListProps> = ({
  analysis,
  recommendations,
  onCreateTransaction
}) => {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [plannedActions, setPlannedActions] = useState<Set<number>>(new Set())
  const [completedActions, setCompletedActions] = useState<Set<number>>(new Set())

  // Load state from localStorage on mount
  useEffect(() => {
    const savedPlanned = localStorage.getItem('rebalancing_planned')
    const savedCompleted = localStorage.getItem('rebalancing_completed')

    if (savedPlanned) {
      setPlannedActions(new Set(JSON.parse(savedPlanned)))
    }
    if (savedCompleted) {
      setCompletedActions(new Set(JSON.parse(savedCompleted)))
    }
  }, [])

  // Save state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('rebalancing_planned', JSON.stringify(Array.from(plannedActions)))
  }, [plannedActions])

  useEffect(() => {
    localStorage.setItem('rebalancing_completed', JSON.stringify(Array.from(completedActions)))
  }, [completedActions])

  const toggleExpand = (id: number) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const handleCopy = (id: number, transactionData: any) => {
    copyTransactionDataToClipboard(transactionData)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleCreateTransaction = (rec: any) => {
    const prefillData = {
      transaction_type: rec.transaction_data.transaction_type,
      symbol: rec.transaction_data.symbol,
      quantity: rec.transaction_data.quantity,
      price_per_unit: rec.transaction_data.price,
      currency: rec.transaction_data.currency,
      notes: rec.transaction_data.notes,
      source: 'REBALANCING_RECOMMENDATION'
    }

    // Store in sessionStorage for the transaction form to pick up
    sessionStorage.setItem('transaction_prefill', JSON.stringify(prefillData))

    // Call the callback if provided (to trigger tab navigation)
    if (onCreateTransaction) {
      onCreateTransaction(prefillData)
    }
  }

  const togglePlanned = (id: number) => {
    const newPlanned = new Set(plannedActions)
    if (newPlanned.has(id)) {
      newPlanned.delete(id)
    } else {
      newPlanned.add(id)
    }
    setPlannedActions(newPlanned)
  }

  const toggleCompleted = (id: number) => {
    const newCompleted = new Set(completedActions)
    if (newCompleted.has(id)) {
      newCompleted.delete(id)
    } else {
      newCompleted.add(id)
      // Also mark as planned if not already
      if (!plannedActions.has(id)) {
        const newPlanned = new Set(plannedActions)
        newPlanned.add(id)
        setPlannedActions(newPlanned)
      }
    }
    setCompletedActions(newCompleted)
  }

  if (!analysis.rebalancing_required) {
    return (
      <div className="recommendations-list">
        <h3>Recommendations</h3>
        <div className="no-recommendations">
          <AlertCircle size={48} />
          <p>No rebalancing recommendations needed.</p>
          <p className="subtext">Your portfolio is well-balanced!</p>
        </div>
      </div>
    )
  }

  if (!recommendations) {
    return (
      <div className="recommendations-list">
        <h3>Recommendations</h3>
        <div className="loading-recommendations">
          <div className="spinner"></div>
          <p>Generating AI recommendations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="recommendations-list">
      <div className="list-header">
        <h3>AI Recommendations</h3>
        <span className={`priority-badge ${recommendations.priority.toLowerCase()}`}>
          {recommendations.priority}
        </span>
      </div>

      {/* Summary */}
      <div className="recommendations-summary">
        <p>{recommendations.summary}</p>
      </div>

      {/* Recommendations */}
      <div className="recommendations-items">
        {recommendations.recommendations.map((rec, index) => {
          const isExpanded = expandedIds.has(index)
          const isCopied = copiedId === index
          const isPlanned = plannedActions.has(index)
          const isCompleted = completedActions.has(index)

          return (
            <div key={index} className={`recommendation-item ${rec.action.toLowerCase()} ${isCompleted ? 'completed' : ''} ${isPlanned ? 'planned' : ''}`}>
              {/* Header */}
              <div className="item-header">
                <div className="item-priority">#{rec.priority}</div>
                <div className="item-action">
                  {rec.action === 'SELL' ? (
                    <TrendingDown size={20} />
                  ) : (
                    <TrendingUp size={20} />
                  )}
                  <span className="action-label">{rec.action}</span>
                </div>
                <div className="item-symbol">{rec.symbol}</div>
                <button
                  className="expand-button"
                  onClick={() => toggleExpand(index)}
                  aria-label={isExpanded ? 'Collapse' : 'Expand'}
                >
                  {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>
              </div>

              {/* Trade Details */}
              <div className="item-details">
                <div className="detail-row">
                  <span className="detail-label">Quantity:</span>
                  <span className="detail-value">{rec.quantity.toLocaleString()}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Price:</span>
                  <span className="detail-value">€{rec.current_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Total:</span>
                  <span className="detail-value total">€{rec.estimated_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
              </div>

              {/* Rationale (Collapsed) */}
              {!isExpanded && (
                <div className="item-rationale-preview">
                  {rec.rationale.substring(0, 100)}...
                </div>
              )}

              {/* Expanded Content */}
              {isExpanded && (
                <div className="item-expanded">
                  <div className="expanded-section">
                    <h4>Rationale</h4>
                    <p>{rec.rationale}</p>
                  </div>

                  {rec.timing && (
                    <div className="expanded-section">
                      <h4>Timing</h4>
                      <p>{rec.timing}</p>
                    </div>
                  )}

                  <div className="expanded-section">
                    <h4>Transaction Data</h4>
                    <div className="transaction-data">
                      <div className="data-row">
                        <span>Type:</span>
                        <span>{rec.transaction_data.transaction_type}</span>
                      </div>
                      <div className="data-row">
                        <span>Symbol:</span>
                        <span>{rec.transaction_data.symbol}</span>
                      </div>
                      <div className="data-row">
                        <span>Quantity:</span>
                        <span>{rec.transaction_data.quantity}</span>
                      </div>
                      <div className="data-row">
                        <span>Price:</span>
                        <span>€{rec.transaction_data.price.toFixed(2)}</span>
                      </div>
                      <div className="data-row">
                        <span>Total:</span>
                        <span>€{rec.transaction_data.total_value.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="item-actions">
                <button
                  className="copy-button"
                  onClick={() => handleCopy(index, rec.transaction_data)}
                  disabled={isCopied}
                  title="Copy transaction data to clipboard as CSV"
                >
                  <Copy size={16} />
                  {isCopied ? 'Copied!' : 'Copy Data'}
                </button>
                <button
                  className="create-button"
                  onClick={() => handleCreateTransaction(rec)}
                  title="Create transaction from this recommendation"
                >
                  <Plus size={16} />
                  Create Transaction
                </button>
                <button
                  className={`planned-button ${isPlanned ? 'active' : ''}`}
                  onClick={() => togglePlanned(index)}
                  title={isPlanned ? 'Unmark as planned' : 'Mark as planned'}
                >
                  <Check size={16} />
                  {isPlanned ? 'Planned ✓' : 'Mark Planned'}
                </button>
                <button
                  className={`completed-button ${isCompleted ? 'active' : ''}`}
                  onClick={() => toggleCompleted(index)}
                  title={isCompleted ? 'Unmark as completed' : 'Mark as completed'}
                >
                  <Check size={16} />
                  {isCompleted ? 'Completed ✓' : 'Mark Completed'}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Expected Outcome */}
      <div className="expected-outcome">
        <h4>Expected Outcome</h4>
        <div className="outcome-grid">
          <div className="outcome-item">
            <span className="outcome-label">Stocks:</span>
            <span className="outcome-value">{recommendations.expected_outcome.stocks_percentage}%</span>
          </div>
          <div className="outcome-item">
            <span className="outcome-label">Crypto:</span>
            <span className="outcome-value">{recommendations.expected_outcome.crypto_percentage}%</span>
          </div>
          <div className="outcome-item">
            <span className="outcome-label">Metals:</span>
            <span className="outcome-value">{recommendations.expected_outcome.metals_percentage}%</span>
          </div>
        </div>
        <p className="outcome-improvement">{recommendations.expected_outcome.net_allocation_improvement}</p>
      </div>

      {/* Risk Assessment */}
      <div className="risk-assessment">
        <h4>Risk Assessment</h4>
        <p>{recommendations.risk_assessment}</p>
      </div>

      {/* Implementation Notes */}
      <div className="implementation-notes">
        <h4>Implementation Notes</h4>
        <p>{recommendations.implementation_notes}</p>
      </div>
    </div>
  )
}

export default RebalancingRecommendationsList
