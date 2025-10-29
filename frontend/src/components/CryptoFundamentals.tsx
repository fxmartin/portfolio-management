// ABOUTME: Display cryptocurrency fundamental data from CoinGecko
// ABOUTME: Shows ATH/ATL, market cap, supply metrics, and performance indicators

import { TrendingUp, TrendingDown, Coins, BarChart3 } from 'lucide-react'
import type { CryptoFundamentals as CryptoFundamentalsType } from '../api/analysis'
import './CryptoFundamentals.css'

interface CryptoFundamentalsProps {
  data: CryptoFundamentalsType
}

export const CryptoFundamentals: React.FC<CryptoFundamentalsProps> = ({ data }) => {
  const formatNumber = (num: number | undefined, decimals: number = 0): string => {
    if (num === undefined || num === null) return 'N/A'

    if (num >= 1_000_000_000) {
      return `€${(num / 1_000_000_000).toFixed(decimals)}B`
    } else if (num >= 1_000_000) {
      return `€${(num / 1_000_000).toFixed(decimals)}M`
    } else if (num >= 1_000) {
      return `€${(num / 1_000).toFixed(decimals)}K`
    }
    return `€${num.toFixed(decimals)}`
  }

  const formatSupply = (num: number | undefined): string => {
    if (num === undefined || num === null) return 'N/A'
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(2)}B`
    } else if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(2)}M`
    }
    return num.toLocaleString()
  }

  const formatPercentage = (num: number | undefined): string => {
    if (num === undefined || num === null) return 'N/A'
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getDaysAgo = (dateStr: string): number => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    return Math.floor(diffTime / (1000 * 60 * 60 * 24))
  }

  return (
    <div className="crypto-fundamentals">
      <div className="fundamentals-header">
        <Coins size={18} />
        <h3>Cryptocurrency Fundamentals</h3>
        <span className="source-badge">CoinGecko</span>
      </div>

      <div className="fundamentals-grid">
        {/* Market Cap & Rank */}
        <div className="fundamental-item">
          <div className="item-icon">
            <BarChart3 size={16} />
          </div>
          <div className="item-content">
            <span className="item-label">Market Cap</span>
            <span className="item-value">{formatNumber(data.market_cap, 1)}</span>
            <span className="item-detail">
              <span className="rank-badge">Rank #{data.market_cap_rank}</span>
            </span>
          </div>
        </div>

        {/* 24h Volume (if available) */}
        {data.total_volume_24h !== undefined && data.total_volume_24h > 0 && (
          <div className="fundamental-item">
            <div className="item-icon">
              <BarChart3 size={16} />
            </div>
            <div className="item-content">
              <span className="item-label">24h Volume</span>
              <span className="item-value">{formatNumber(data.total_volume_24h, 1)}</span>
              <span className="item-detail">Trading activity</span>
            </div>
          </div>
        )}

        {/* Supply */}
        <div className="fundamental-item">
          <div className="item-icon">
            <Coins size={16} />
          </div>
          <div className="item-content">
            <span className="item-label">Supply</span>
            <span className="item-value">{formatSupply(data.circulating_supply)}</span>
            <span className="item-detail">
              {data.max_supply ? `Max: ${formatSupply(data.max_supply)}` : 'No max supply'}
            </span>
          </div>
        </div>

        {/* ATH */}
        <div className="fundamental-item ath">
          <div className="item-icon">
            <TrendingUp size={16} color="#059669" />
          </div>
          <div className="item-content">
            <span className="item-label">All-Time High</span>
            <span className="item-value">{formatNumber(data.ath, 2)}</span>
            <span className="item-detail ath-detail">
              {formatDate(data.ath_date)} ({getDaysAgo(data.ath_date)}d ago)
              <span className={data.ath_change_percentage < 0 ? 'negative' : 'positive'}>
                {formatPercentage(data.ath_change_percentage)}
              </span>
            </span>
          </div>
        </div>

        {/* ATL */}
        <div className="fundamental-item atl">
          <div className="item-icon">
            <TrendingDown size={16} color="#dc2626" />
          </div>
          <div className="item-content">
            <span className="item-label">All-Time Low</span>
            <span className="item-value">{formatNumber(data.atl, 4)}</span>
            <span className="item-detail atl-detail">
              {formatDate(data.atl_date)}
              <span className="positive">{formatPercentage(data.atl_change_percentage)}</span>
            </span>
          </div>
        </div>

        {/* Performance */}
        {(data.price_change_percentage_7d !== undefined ||
          data.price_change_percentage_30d !== undefined ||
          data.price_change_percentage_1y !== undefined) && (
          <div className="fundamental-item performance">
            <div className="item-content">
              <span className="item-label">Performance</span>
              <div className="performance-grid">
                {data.price_change_percentage_7d !== undefined && (
                  <div className="perf-item">
                    <span className="perf-period">7d</span>
                    <span
                      className={`perf-value ${
                        data.price_change_percentage_7d >= 0 ? 'positive' : 'negative'
                      }`}
                    >
                      {formatPercentage(data.price_change_percentage_7d)}
                    </span>
                  </div>
                )}
                {data.price_change_percentage_30d !== undefined && (
                  <div className="perf-item">
                    <span className="perf-period">30d</span>
                    <span
                      className={`perf-value ${
                        data.price_change_percentage_30d >= 0 ? 'positive' : 'negative'
                      }`}
                    >
                      {formatPercentage(data.price_change_percentage_30d)}
                    </span>
                  </div>
                )}
                {data.price_change_percentage_1y !== undefined && (
                  <div className="perf-item">
                    <span className="perf-period">1y</span>
                    <span
                      className={`perf-value ${
                        data.price_change_percentage_1y >= 0 ? 'positive' : 'negative'
                      }`}
                    >
                      {formatPercentage(data.price_change_percentage_1y)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* All-Time ROI */}
        {data.all_time_roi !== undefined && (
          <div className="fundamental-item roi">
            <div className="item-content">
              <span className="item-label">All-Time ROI</span>
              <span className="item-value roi-value">
                {formatPercentage(data.all_time_roi)}
              </span>
              <span className="item-detail">ATL → ATH</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CryptoFundamentals
