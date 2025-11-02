// ABOUTME: Component for displaying strategy-driven portfolio recommendations
// ABOUTME: Includes profit-taking opportunities, position assessments, and action plans

import { useState, useEffect } from 'react';
import { Copy, Plus, Check, Download, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { AlignmentScoreGauge } from './AlignmentScoreGauge';
import type { StrategyDrivenRecommendationResponse, TransactionData } from '../types/strategy';
import './StrategyRecommendationsCard.css';

interface StrategyRecommendationsCardProps {
  recommendations: StrategyDrivenRecommendationResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onNavigateToTransactions?: () => void;
}

export default function StrategyRecommendationsCard({
  recommendations,
  loading,
  error,
  onRefresh,
  onNavigateToTransactions
}: StrategyRecommendationsCardProps) {
  const [plannedTransactions, setPlannedTransactions] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('planned_strategy_transactions');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });

  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['immediate']));

  useEffect(() => {
    localStorage.setItem('planned_strategy_transactions', JSON.stringify([...plannedTransactions]));
  }, [plannedTransactions]);

  const copyTransactionData = async (txData: TransactionData) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(txData, null, 2));
      // Could add toast notification here
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const createTransaction = (txData: TransactionData) => {
    // Store transaction data in localStorage for the transaction form to pick up
    localStorage.setItem('transaction_prefill_data', JSON.stringify(txData));

    if (onNavigateToTransactions) {
      onNavigateToTransactions();
    }
  };

  const togglePlanned = (txKey: string) => {
    const newSet = new Set(plannedTransactions);
    if (newSet.has(txKey)) {
      newSet.delete(txKey);
    } else {
      newSet.add(txKey);
    }
    setPlannedTransactions(newSet);
  };

  const exportAllActions = () => {
    if (!recommendations) return;

    const rows: string[][] = [
      ['Type', 'Symbol', 'Action', 'Details', 'Rationale']
    ];

    // Add profit-taking opportunities
    recommendations.profit_taking_opportunities.forEach(opp => {
      rows.push([
        'Profit Taking',
        opp.symbol,
        opp.recommendation,
        `${opp.transaction_details.quantity} × $${opp.transaction_details.price.toFixed(2)} = $${opp.transaction_details.total.toFixed(2)}`,
        opp.rationale
      ]);
    });

    // Add immediate actions
    recommendations.action_plan.immediate_actions.forEach(action => {
      rows.push(['Immediate Action', '-', '-', action, '-']);
    });

    // Add redeployment options
    recommendations.action_plan.redeployment_options.forEach(option => {
      rows.push(['Redeployment', '-', '-', option, '-']);
    });

    const csvContent = rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `strategy_actions_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleSection = (section: string) => {
    const newSet = new Set(expandedSections);
    if (newSet.has(section)) {
      newSet.delete(section);
    } else {
      newSet.add(section);
    }
    setExpandedSections(newSet);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'HOLD':
        return 'action-hold';
      case 'REDUCE':
        return 'action-reduce';
      case 'CLOSE':
        return 'action-close';
      default:
        return '';
    }
  };

  if (loading) {
    return (
      <div className="strategy-recommendations-card loading">
        <p>Loading recommendations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="strategy-recommendations-card error">
        <p>{error}</p>
        <button onClick={onRefresh} className="refresh-button">
          <RefreshCw size={16} />
          Retry
        </button>
      </div>
    );
  }

  if (!recommendations) {
    return (
      <div className="strategy-recommendations-card empty">
        <p>No recommendations available</p>
        <button onClick={onRefresh} className="refresh-button">
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="strategy-recommendations-card">
      <div className="card-header">
        <h2>Strategy Recommendations</h2>
        <button onClick={onRefresh} className="refresh-button" title="Refresh recommendations">
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Alignment Score */}
      <div className="alignment-section">
        <h3>Portfolio Alignment Score</h3>
        <AlignmentScoreGauge score={recommendations.alignment_score} size={120} />
      </div>

      {/* Key Insights */}
      <div className="insights-section">
        <h3>Key Insights</h3>
        <ul className="insights-list">
          {recommendations.key_insights.map((insight, idx) => (
            <li key={idx}>{insight}</li>
          ))}
        </ul>
      </div>

      {/* Profit-Taking Opportunities */}
      {recommendations.profit_taking_opportunities.length > 0 && (
        <div className="opportunities-section">
          <h3>Profit-Taking Opportunities</h3>
          <table className="opportunities-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>P&L %</th>
                <th>Threshold</th>
                <th>Recommendation</th>
                <th>Transaction</th>
                <th>Rationale</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recommendations.profit_taking_opportunities.map((opp, idx) => {
                const txKey = `${opp.symbol}-${opp.transaction_details.transaction_type}-${opp.transaction_details.quantity}`;
                const isPlanned = plannedTransactions.has(txKey);

                return (
                  <tr key={idx}>
                    <td className="symbol">{opp.symbol}</td>
                    <td className="pnl-pct">{opp.current_pnl_pct.toFixed(1)}%</td>
                    <td>{opp.threshold.toFixed(1)}%</td>
                    <td className="recommendation">{opp.recommendation}</td>
                    <td className="transaction-details">
                      <div>
                        {opp.transaction_details.quantity} × ${opp.transaction_details.price.toFixed(2)}
                      </div>
                      <div className="total">
                        ${opp.transaction_details.total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </td>
                    <td className="rationale">{opp.rationale}</td>
                    <td className="action-buttons">
                      <button
                        onClick={() => copyTransactionData(opp.transaction_details)}
                        className="icon-button"
                        title="Copy transaction data"
                      >
                        <Copy size={16} />
                      </button>
                      <button
                        onClick={() => createTransaction(opp.transaction_details)}
                        className="icon-button"
                        title="Create transaction"
                      >
                        <Plus size={16} />
                      </button>
                      <button
                        onClick={() => togglePlanned(txKey)}
                        className={`icon-button ${isPlanned ? 'planned' : ''}`}
                        title={isPlanned ? 'Mark as not planned' : 'Mark as planned'}
                      >
                        <Check size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Position Assessments */}
      {recommendations.position_assessments.length > 0 && (
        <div className="assessments-section">
          <h3>Position Assessments</h3>
          <table className="assessments-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Action</th>
                <th>Fits Strategy?</th>
                <th>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {recommendations.position_assessments.map((assessment, idx) => (
                <tr key={idx}>
                  <td className="symbol">{assessment.symbol}</td>
                  <td>
                    <span className={`action-badge ${getActionColor(assessment.action)}`}>
                      {assessment.action}
                    </span>
                  </td>
                  <td className="fits-strategy">
                    {assessment.fits_strategy ? '✓ Yes' : '✗ No'}
                  </td>
                  <td className="rationale">{assessment.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* New Position Suggestions */}
      {recommendations.new_position_suggestions.length > 0 && (
        <div className="suggestions-section">
          <h3>New Position Suggestions</h3>
          <div className="suggestions-list">
            {recommendations.new_position_suggestions.map((suggestion, idx) => (
              <div key={idx} className="suggestion-item">
                <strong>{suggestion.symbol}</strong> ({suggestion.asset_type})
                <div className="suggestion-rationale">{suggestion.rationale}</div>
                <div className="suggestion-details">
                  Allocation: {suggestion.suggested_allocation} | {suggestion.entry_strategy}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Plan */}
      <div className="action-plan-section">
        <h3>Action Plan</h3>

        <div className="accordion">
          <div className="accordion-item">
            <button
              className="accordion-header"
              onClick={() => toggleSection('immediate')}
            >
              <span>Immediate Actions ({recommendations.action_plan.immediate_actions.length})</span>
              {expandedSections.has('immediate') ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
            {expandedSections.has('immediate') && (
              <div className="accordion-content">
                <ul>
                  {recommendations.action_plan.immediate_actions.map((action, idx) => (
                    <li key={idx}>
                      <strong>Priority {action.priority}:</strong> {action.action}
                      <div className="action-details">{action.details}</div>
                      {action.expected_impact && <div className="expected-impact">Impact: {action.expected_impact}</div>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="accordion-item">
            <button
              className="accordion-header"
              onClick={() => toggleSection('redeployment')}
            >
              <span>Redeployment Options ({recommendations.action_plan.redeployment?.length || 0})</span>
              {expandedSections.has('redeployment') ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
            {expandedSections.has('redeployment') && recommendations.action_plan.redeployment && (
              <div className="accordion-content">
                <ul>
                  {recommendations.action_plan.redeployment.map((option, idx) => (
                    <li key={idx}>
                      <strong>{option.source || 'Redeployment option'}</strong>
                      {option.allocation && Array.isArray(option.allocation) ? (
                        <ul className="allocation-list">
                          {option.allocation.map((item, itemIdx) => (
                            <li key={itemIdx}>→ {item}</li>
                          ))}
                        </ul>
                      ) : (
                        <>
                          {option.target && <div>→ {option.target}</div>}
                          {option.rationale && <div className="rationale">{option.rationale}</div>}
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="accordion-item">
            <button
              className="accordion-header"
              onClick={() => toggleSection('gradual')}
            >
              <span>Gradual Adjustments ({recommendations.action_plan.gradual_adjustments?.length || 0})</span>
              {expandedSections.has('gradual') ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
            {expandedSections.has('gradual') && recommendations.action_plan.gradual_adjustments && (
              <div className="accordion-content">
                <ul>
                  {recommendations.action_plan.gradual_adjustments.map((adjustment, idx) => (
                    <li key={idx}>
                      <strong>{adjustment.action}</strong>
                      {adjustment.timeframe && <div className="adjustment-timeframe">Timeframe: {adjustment.timeframe}</div>}
                      <div className="adjustment-details">{adjustment.details}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="card-footer">
        <div className="next-review">
          Next Review: {formatDate(recommendations.next_review_date)}
        </div>
        <button onClick={exportAllActions} className="export-button">
          <Download size={16} />
          Export All Actions
        </button>
      </div>
    </div>
  );
}
