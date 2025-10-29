// ABOUTME: Display global cryptocurrency market metrics from CoinGecko
// ABOUTME: Shows total market cap, BTC/ETH dominance, trading volume, and DeFi metrics

import { TrendingUp, Globe, BarChart3, Coins, Activity } from 'lucide-react'
import type { GlobalCryptoMarketData } from '../api/analysis'
import './GlobalCryptoMarket.css'

interface GlobalCryptoMarketProps {
  data: GlobalCryptoMarketData
}

export const GlobalCryptoMarket: React.FC<GlobalCryptoMarketProps> = ({ data }) => {
  const formatNumber = (num: number | undefined, decimals: number = 0): string => {
    if (num === undefined || num === null) return 'N/A'

    if (num >= 1_000_000_000_000) {
      return `€${(num / 1_000_000_000_000).toFixed(decimals)}T`
    } else if (num >= 1_000_000_000) {
      return `€${(num / 1_000_000_000).toFixed(decimals)}B`
    } else if (num >= 1_000_000) {
      return `€${(num / 1_000_000).toFixed(decimals)}M`
    }
    return `€${num.toFixed(decimals)}`
  }

  const formatPercentage = (num: number | undefined): string => {
    if (num === undefined || num === null) return 'N/A'
    return `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`
  }

  const formatCount = (num: number | undefined): string => {
    if (num === undefined || num === null) return 'N/A'
    return num.toLocaleString()
  }

  return (
    <div className="global-crypto-market">
      <div className="market-header">
        <Globe size={18} />
        <h3>Global Crypto Market</h3>
        <span className="source-badge">CoinGecko</span>
      </div>

      <div className="market-grid">
        {/* Total Market Cap */}
        <div className="market-item highlight">
          <div className="item-icon">
            <BarChart3 size={16} />
          </div>
          <div className="item-content">
            <span className="item-label">Total Market Cap</span>
            <span className="item-value">{formatNumber(data.total_market_cap_eur, 1)}</span>
            <span className={`item-detail ${data.market_cap_change_24h >= 0 ? 'positive' : 'negative'}`}>
              {formatPercentage(data.market_cap_change_24h)} 24h
            </span>
          </div>
        </div>

        {/* Fear & Greed Index (if available) */}
        {data.fear_greed_value !== undefined && data.fear_greed_classification && (
          <div className="market-item fear-greed highlight">
            <div className="item-icon">
              <Activity size={16} />
            </div>
            <div className="item-content">
              <span className="item-label">Fear & Greed Index</span>
              <span className="item-value fear-greed-value">{data.fear_greed_value}/100</span>
              <span className="item-detail">{data.fear_greed_classification}</span>
            </div>
          </div>
        )}

        {/* 24h Volume */}
        <div className="market-item">
          <div className="item-icon">
            <TrendingUp size={16} />
          </div>
          <div className="item-content">
            <span className="item-label">24h Volume</span>
            <span className="item-value">{formatNumber(data.total_volume_24h_eur, 1)}</span>
            <span className="item-detail">Trading activity</span>
          </div>
        </div>

        {/* BTC Dominance */}
        <div className="market-item btc">
          <div className="item-content">
            <span className="item-label">Bitcoin Dominance</span>
            <span className="item-value">{data.btc_dominance.toFixed(1)}%</span>
            <span className="item-detail">BTC market share</span>
          </div>
        </div>

        {/* ETH Dominance */}
        <div className="market-item eth">
          <div className="item-content">
            <span className="item-label">Ethereum Dominance</span>
            <span className="item-value">{data.eth_dominance.toFixed(1)}%</span>
            <span className="item-detail">ETH market share</span>
          </div>
        </div>

        {/* Active Cryptocurrencies */}
        <div className="market-item">
          <div className="item-icon">
            <Coins size={16} />
          </div>
          <div className="item-content">
            <span className="item-label">Active Cryptos</span>
            <span className="item-value">{formatCount(data.active_cryptocurrencies)}</span>
            <span className="item-detail">{formatCount(data.markets)} markets</span>
          </div>
        </div>

        {/* DeFi Metrics (if available) */}
        {data.defi_market_cap_eur && data.defi_market_cap_eur > 0 && (
          <div className="market-item defi">
            <div className="item-content">
              <span className="item-label">DeFi Market Cap</span>
              <span className="item-value">{formatNumber(data.defi_market_cap_eur, 1)}</span>
              <span className="item-detail">{data.defi_dominance?.toFixed(1)}% of total</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default GlobalCryptoMarket
