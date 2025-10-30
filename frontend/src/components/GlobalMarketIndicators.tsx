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

  const getCategoryIcon = (category: 'equities' | 'risk' | 'commodities' | 'crypto') => {
    switch (category) {
      case 'risk':
        return <Zap size={12} />
      case 'equities':
        return <BarChart3 size={12} />
      case 'commodities':
        return <DollarSign size={12} />
      case 'crypto':
        return <TrendingUp size={12} />
    }
  }

  const getCategoryClass = (category: string) => {
    return `category-${category}`
  }

  const renderIndicator = (indicator: MarketIndicator, category: 'equities' | 'risk' | 'commodities' | 'crypto') => {
    const tooltipText = INDICATOR_TOOLTIPS[indicator.symbol]
    const content = (
      <div className="indicator-content">
        <span className={`category-badge ${getCategoryClass(category)}`}>
          {getCategoryIcon(category)}
        </span>
        <span className="indicator-label">{indicator.name}</span>
        <span className="indicator-separator">•</span>
        <span className="indicator-price">{formatPrice(indicator.price, indicator.symbol)}</span>
        <span className={`indicator-change ${getChangeClass(indicator.change_percent)}`}>
          {formatChange(indicator.change_percent)}
        </span>
      </div>
    )

    return (
      <div key={indicator.symbol} className="indicator-item">
        {tooltipText ? (
          <Tooltip content={tooltipText}>{content}</Tooltip>
        ) : (
          content
        )}
        {indicator.interpretation && (
          <span className="indicator-interpretation">{indicator.interpretation}</span>
        )}
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
        <Activity size={16} />
        <h3>Global Market Snapshot</h3>
        <span className="source-badge">Live</span>
      </div>

      <div className="indicators-grid">
        {/* Flatten all indicators into a single horizontal grid */}
        {/* Risk Indicators (show first) */}
        {data.risk.map((indicator) => renderIndicator(indicator, 'risk'))}

        {/* Equities */}
        {data.equities.map((indicator) => renderIndicator(indicator, 'equities'))}

        {/* Commodities */}
        {data.commodities.map((indicator) => renderIndicator(indicator, 'commodities'))}

        {/* Crypto */}
        {data.crypto.map((indicator) => renderIndicator(indicator, 'crypto'))}
      </div>
    </div>
  )
}

export default GlobalMarketIndicators
