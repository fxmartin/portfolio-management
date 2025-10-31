// ABOUTME: Summary card displaying key rebalancing metrics
// ABOUTME: Shows priority, trades needed, costs, and largest deviations

import type { RebalancingAnalysis } from '../api/rebalancing'
import { AlertCircle, TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react'
import './RebalancingSummaryCard.css'

interface RebalancingSummaryCardProps {
  analysis: RebalancingAnalysis
}

const RebalancingSummaryCard: React.FC<RebalancingSummaryCardProps> = ({ analysis }) => {
  const getPriorityBadge = () => {
    const deviation = Math.abs(Number(analysis.largest_deviation))

    if (deviation >= 10) {
      return { label: 'HIGH', className: 'high' }
    } else if (deviation >= 5) {
      return { label: 'MEDIUM', className: 'medium' }
    } else {
      return { label: 'LOW', className: 'low' }
    }
  }

  const priority = getPriorityBadge()

  return (
    <div className="rebalancing-summary-card">
      <div className="summary-header">
        <h3>Rebalancing Summary</h3>
        <span className={`priority-badge ${priority.className}`}>
          {priority.label} Priority
        </span>
      </div>

      {analysis.rebalancing_required ? (
        <div className="summary-grid">
          {/* Total Trades */}
          <div className="summary-item">
            <div className="item-icon">
              <Activity size={20} />
            </div>
            <div className="item-content">
              <div className="item-label">Trades Needed</div>
              <div className="item-value">{analysis.total_trades_needed}</div>
            </div>
          </div>

          {/* Transaction Costs */}
          <div className="summary-item">
            <div className="item-icon">
              <DollarSign size={20} />
            </div>
            <div className="item-content">
              <div className="item-label">Est. Costs</div>
              <div className="item-value">€{Number(analysis.estimated_transaction_costs).toFixed(2)}</div>
            </div>
          </div>

          {/* Largest Deviation */}
          <div className="summary-item">
            <div className="item-icon">
              <AlertCircle size={20} />
            </div>
            <div className="item-content">
              <div className="item-label">Largest Deviation</div>
              <div className="item-value">{Number(analysis.largest_deviation).toFixed(1)}%</div>
            </div>
          </div>

          {/* Most Overweight */}
          {analysis.most_overweight && (
            <div className="summary-item">
              <div className="item-icon">
                <TrendingUp size={20} style={{ color: '#ef4444' }} />
              </div>
              <div className="item-content">
                <div className="item-label">Most Overweight</div>
                <div className="item-value capitalize">{analysis.most_overweight}</div>
              </div>
            </div>
          )}

          {/* Most Underweight */}
          {analysis.most_underweight && (
            <div className="summary-item">
              <div className="item-icon">
                <TrendingDown size={20} style={{ color: '#3b82f6' }} />
              </div>
              <div className="item-content">
                <div className="item-label">Most Underweight</div>
                <div className="item-value capitalize">{analysis.most_underweight}</div>
              </div>
            </div>
          )}

          {/* Portfolio Value */}
          <div className="summary-item">
            <div className="item-icon">
              <DollarSign size={20} />
            </div>
            <div className="item-content">
              <div className="item-label">Total Portfolio</div>
              <div className="item-value">€{Number(analysis.total_portfolio_value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="balanced-state">
          <div className="balanced-icon">✓</div>
          <h4>Portfolio is Well-Balanced</h4>
          <p>Your current allocation is within target ranges. No rebalancing needed at this time.</p>
          <p className="next-review">Next review recommended in 3 months.</p>
        </div>
      )}
    </div>
  )
}

export default RebalancingSummaryCard
