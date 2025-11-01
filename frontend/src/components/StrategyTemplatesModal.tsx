// ABOUTME: Modal component displaying pre-written investment strategy templates
// ABOUTME: Provides 5 template options (conservative, balanced, aggressive, income, value) for quick strategy setup

import React from 'react'
import { Modal } from './Modal'
import type { StrategyTemplate } from '../types/strategy'
import './StrategyTemplatesModal.css'

interface StrategyTemplatesModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectTemplate: (template: StrategyTemplate) => void
}

const STRATEGY_TEMPLATES: StrategyTemplate[] = [
  {
    id: 'conservative-growth',
    title: 'Conservative Growth',
    description: 'Stable dividends, low risk, focus on established companies',
    risk_tolerance: 'low',
    target_annual_return: 8,
    time_horizon_years: 15,
    max_positions: 20,
    profit_taking_threshold: 25,
    strategy_text: `My investment strategy focuses on long-term wealth preservation and steady growth through conservative asset allocation. I prioritize capital protection over aggressive returns.

Core principles:
- Invest primarily in established companies with proven track records and consistent dividend payments
- Maintain a diversified portfolio across sectors to minimize risk
- Focus on blue-chip stocks with strong fundamentals and stable earnings
- Allocate a small portion to precious metals (gold, silver) as a hedge against market volatility
- Avoid highly speculative assets and cryptocurrencies
- Target 70% stocks, 15% metals, 15% cash reserves
- Take profits when positions reach 25% gains to lock in returns
- Review portfolio quarterly and rebalance to maintain target allocation
- Prioritize companies with low debt-to-equity ratios and strong cash flows
- Time horizon: 10-15 years for retirement planning`
  },
  {
    id: 'balanced-growth',
    title: 'Balanced Growth',
    description: 'Mix of stocks/crypto, medium risk, diversified approach',
    risk_tolerance: 'medium',
    target_annual_return: 15,
    time_horizon_years: 10,
    max_positions: 30,
    profit_taking_threshold: 50,
    strategy_text: `My investment strategy seeks balanced growth through diversification across traditional and emerging asset classes. I aim for moderate returns with controlled risk exposure.

Core principles:
- Maintain a diversified portfolio: 60% stocks, 25% crypto, 15% metals
- Invest in a mix of growth stocks and established blue-chips
- Allocate 25% to cryptocurrencies (Bitcoin, Ethereum) for higher growth potential
- Use precious metals as portfolio stabilizers during market downturns
- Target companies with strong competitive advantages and growth prospects
- Take profits at 50% gains to rebalance and capture returns
- Rebalance quarterly to maintain target allocation percentages
- Accept moderate volatility for potential higher returns
- Dollar-cost average into crypto positions to reduce timing risk
- Monitor market trends and adjust sector exposure accordingly
- Time horizon: 5-10 years for wealth accumulation`
  },
  {
    id: 'aggressive-growth',
    title: 'Aggressive Growth',
    description: 'High-growth tech, high volatility, maximum returns focus',
    risk_tolerance: 'high',
    target_annual_return: 25,
    time_horizon_years: 7,
    max_positions: 40,
    profit_taking_threshold: 100,
    strategy_text: `My investment strategy pursues aggressive capital appreciation through high-growth opportunities and emerging technologies. I accept high volatility for potential outsized returns.

Core principles:
- Allocate 50% stocks (tech-heavy), 40% crypto, 10% metals
- Focus on disruptive technology companies with exponential growth potential
- Invest heavily in cryptocurrency ecosystem (DeFi, NFTs, emerging chains)
- Hold concentrated positions in conviction plays
- Take profits at 100%+ gains to compound returns aggressively
- Actively trade volatile positions to capture momentum
- Monitor market sentiment and technical indicators for entry/exit points
- Accept 30-50% drawdowns as part of high-risk strategy
- Reinvest profits into new high-potential opportunities
- Stay informed on emerging trends: AI, blockchain, biotech, clean energy
- Use stop-losses on speculative positions to limit downside
- Time horizon: 5-7 years for wealth multiplication`
  },
  {
    id: 'income-focus',
    title: 'Income Focus',
    description: 'Dividend stocks, bonds, steady cash flow generation',
    risk_tolerance: 'low',
    target_annual_return: 6,
    time_horizon_years: 20,
    max_positions: 25,
    profit_taking_threshold: 20,
    strategy_text: `My investment strategy prioritizes consistent income generation through dividend-paying assets and stable holdings. I focus on cash flow over capital appreciation.

Core principles:
- Invest in high-dividend-yield stocks with proven payout histories
- Target dividend aristocrats with 10+ years of consecutive increases
- Allocate 80% to dividend stocks, 15% to metals, 5% to growth
- Reinvest dividends to compound returns over time
- Focus on sectors with stable cash flows: utilities, consumer staples, REITs
- Maintain low portfolio turnover to minimize taxes on income
- Take profits conservatively at 20% gains to preserve capital
- Prioritize companies with dividend payout ratios below 70%
- Build a diversified income stream across 20-25 positions
- Review holdings annually, replacing companies that cut dividends
- Target 4-6% annual yield from portfolio
- Time horizon: 15-20 years for retirement income stream`
  },
  {
    id: 'value-investing',
    title: 'Value Investing',
    description: 'Undervalued established companies, margin of safety approach',
    risk_tolerance: 'medium',
    target_annual_return: 12,
    time_horizon_years: 12,
    max_positions: 15,
    profit_taking_threshold: 75,
    strategy_text: `My investment strategy follows value investing principles, seeking undervalued companies with strong fundamentals trading below intrinsic value. I focus on margin of safety and long-term compounding.

Core principles:
- Invest only in businesses I understand with clear competitive advantages
- Buy when market price is 30-40% below calculated intrinsic value
- Focus on companies with strong balance sheets and consistent earnings
- Allocate 85% stocks, 10% metals, 5% opportunistic positions
- Hold concentrated positions (10-15 companies) for deep analysis
- Ignore short-term market fluctuations and focus on business fundamentals
- Take profits at 75% gains or when valuation becomes excessive
- Analyze financial statements quarterly to validate investment thesis
- Prefer companies with shareholder-friendly management and capital allocation
- Seek companies with durable competitive moats and pricing power
- Be patient - wait for market corrections to deploy capital
- Time horizon: 10-15 years for value realization and compounding`
  }
]

export const StrategyTemplatesModal: React.FC<StrategyTemplatesModalProps> = ({
  isOpen,
  onClose,
  onSelectTemplate
}) => {
  const handleSelectTemplate = (template: StrategyTemplate) => {
    onSelectTemplate(template)
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Strategy Templates"
      className="strategy-templates-modal"
    >
      <div className="templates-container">
        <p className="templates-description">
          Choose a pre-written strategy template to get started quickly. You can customize it after insertion.
        </p>

        <div className="templates-grid">
          {STRATEGY_TEMPLATES.map(template => (
            <article key={template.id} className="template-card">
              <div className="template-header">
                <h3 className="template-title">{template.title}</h3>
                <span className={`risk-badge risk-${template.risk_tolerance}`}>
                  Risk: {template.risk_tolerance.charAt(0).toUpperCase() + template.risk_tolerance.slice(1)}
                </span>
              </div>

              <p className="template-description">{template.description}</p>

              <div className="template-details">
                <div className="detail-item">
                  <span className="detail-label">Target Return:</span>
                  <span className="detail-value">{template.target_annual_return}% annually</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Time Horizon:</span>
                  <span className="detail-value">
                    {template.time_horizon_years < 8 ? '5-10 years' :
                     template.time_horizon_years < 13 ? '10-15 years' : '15-20 years'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Max Positions:</span>
                  <span className="detail-value">{template.max_positions} holdings</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Profit Taking:</span>
                  <span className="detail-value">+{template.profit_taking_threshold}%</span>
                </div>
              </div>

              <button
                type="button"
                className="btn btn-primary template-select-btn"
                onClick={() => handleSelectTemplate(template)}
              >
                Use Template
              </button>
            </article>
          ))}
        </div>

        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Cancel
          </button>
        </div>
      </div>
    </Modal>
  )
}
