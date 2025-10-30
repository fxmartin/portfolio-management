// ABOUTME: Display global market indicators from Yahoo Finance and market data sources
// ABOUTME: Shows equities, risk indicators, commodities, and crypto with live prices and 24h changes

import { TrendingUp, TrendingDown, Activity, BarChart3, DollarSign, Zap } from 'lucide-react'
import type { GlobalMarketIndicators, MarketIndicator } from '../api/analysis'
import { Tooltip } from './Tooltip'
import { INDICATOR_TOOLTIPS } from '../config/indicatorTooltips'
import './GlobalMarketIndicators.css'

interface GlobalMarketIndicatorsProps {
  data: GlobalMarketIndicators
}

export const GlobalMarketIndicators: React.FC<GlobalMarketIndicatorsProps> = ({ data }) => {
  const formatPrice = (price: number, symbol: string): string => {
    // Treasury yield is a percentage
    if (symbol === '^TNX') {
      return `${price.toFixed(2)}%`
    }
    // Format as currency with appropriate decimals
    if (price >= 1000) {
      return price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    } else if (price >= 100) {
      return price.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
    }
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  const formatChange = (change: number): string => {
    const sign = change >= 0 ? '+' : ''
    return `${sign}${change.toFixed(2)}%`
  }

  const getChangeClass = (change: number): string => {
    return change >= 0 ? 'positive' : 'negative'
  }

  const renderIndicator = (indicator: MarketIndicator) => {
    const tooltipText = INDICATOR_TOOLTIPS[indicator.symbol]

    return (
      <div key={indicator.symbol} className="indicator-item">
        <div className="indicator-content">
          {tooltipText ? (
            <Tooltip content={tooltipText}>
              <span className="indicator-label">{indicator.name}</span>
            </Tooltip>
          ) : (
            <span className="indicator-label">{indicator.name}</span>
          )}
          <div className="indicator-values">
            <span className="indicator-price">{formatPrice(indicator.price, indicator.symbol)}</span>
            <span className={`indicator-change ${getChangeClass(indicator.change_percent)}`}>
              {formatChange(indicator.change_percent)}
            </span>
          </div>
          {indicator.interpretation && (
            <span className="indicator-interpretation">{indicator.interpretation}</span>
          )}
        </div>
      </div>
    )
  }

  // Check if we have any data to display
  const hasData =
    data.equities.length > 0 ||
    data.risk.length > 0 ||
    data.commodities.length > 0 ||
    data.crypto.length > 0

  if (!hasData) {
    return null
  }

  return (
    <div className="global-market-indicators">
      <div className="market-header">
        <Activity size={18} />
        <h3>Global Market Snapshot</h3>
        <span className="source-badge">Live Data</span>
      </div>

      <div className="indicators-grid">
        {/* Risk Indicators (CRITICAL - show first) */}
        {data.risk.length > 0 && (
          <div className="indicator-section risk-section">
            <div className="section-header">
              <Zap size={14} />
              <span>Risk Indicators</span>
            </div>
            <div className="section-items">
              {data.risk.map(renderIndicator)}
            </div>
          </div>
        )}

        {/* Equities */}
        {data.equities.length > 0 && (
          <div className="indicator-section equities-section">
            <div className="section-header">
              <BarChart3 size={14} />
              <span>Equities</span>
            </div>
            <div className="section-items">
              {data.equities.map(renderIndicator)}
            </div>
          </div>
        )}

        {/* Commodities */}
        {data.commodities.length > 0 && (
          <div className="indicator-section commodities-section">
            <div className="section-header">
              <DollarSign size={14} />
              <span>Commodities</span>
            </div>
            <div className="section-items">
              {data.commodities.map(renderIndicator)}
            </div>
          </div>
        )}

        {/* Crypto */}
        {data.crypto.length > 0 && (
          <div className="indicator-section crypto-section">
            <div className="section-header">
              <TrendingUp size={14} />
              <span>Crypto</span>
            </div>
            <div className="section-items">
              {data.crypto.map(renderIndicator)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default GlobalMarketIndicators
