// ABOUTME: Configuration file containing tooltip texts for all market indicators
// ABOUTME: Used by GlobalMarketIndicators and GlobalCryptoMarket components

/**
 * Tooltip explanations for all market indicators
 *
 * Each tooltip is 1-2 sentences explaining:
 * - What the indicator measures
 * - How to interpret rising/falling values
 * - Why it matters for investment decisions
 */
export const INDICATOR_TOOLTIPS: Record<string, string> = {
  // Global Market Indicators (12 indicators)
  '^GSPC': "Tracks 500 largest US companies. Rising indicates economic growth; falling signals recession concerns.",
  '^DJI': "30 major US 'blue-chip' companies. Conservative benchmark for large-cap stability.",
  '^IXIC': "Tech-heavy index with 2,500+ stocks. Measures investor appetite for growth and innovation.",
  '^STOXX50E': "50 largest Eurozone companies. Benchmark for European economic health.",
  '^GDAXI': "Germany's top 30 companies. Leading indicator for European market strength.",
  '^VIX': "Market 'fear gauge' measuring expected volatility. <20 = calm, 20-30 = moderate fear, >30 = high uncertainty.",
  '^TNX': "US government 10-year bond rate. Rising = growth expectations, falling = recession fears or flight to safety.",
  'DX-Y.NYB': "USD strength vs 6 major currencies. Rising dollar helps imports but hurts exports and commodities.",
  'GC=F': "Safe-haven asset rising during uncertainty and inflation. Use as portfolio stabilizer and inflation hedge.",
  'CL=F': "Benchmark crude oil price. Rising indicates inflation risk and economic growth; falling signals slowdown.",
  'HG=F': "'Dr. Copper' industrial metal sensitive to economic activity. Best leading indicator of manufacturing and construction demand.",
  'BTC-USD': "Original cryptocurrency tracking overall crypto sentiment. Rising signals risk-on appetite; falling indicates risk-off.",

  // Crypto Market Indicators (7 indicators, by field name)
  'total_market_cap': "Combined value of all cryptocurrencies. Measures overall crypto sector health and bull/bear market status.",
  'fear_greed': "Crypto sentiment score 0-100. <25 = Extreme Fear (buy opportunity), >75 = Extreme Greed (consider selling).",
  '24h_volume': "Total crypto traded in last 24 hours. High volume confirms price trends; low volume signals weak momentum.",
  'btc_dominance': "Bitcoin's market share of total crypto. >60% = caution, <40% = 'altseason' risk-on sentiment.",
  'eth_dominance': "ETH's market share. Rising = capital flowing to smart contracts; falling = rotation to BTC or altcoins.",
  'active_cryptos': "Number of traded cryptocurrencies. Expanding ecosystem indicator but less actionable than dominance metrics.",
  'defi_market_cap': "Value of decentralized finance protocols. Tracks adoption of non-custodial finance and higher-growth crypto sector."
}

/**
 * Get tooltip text for a given indicator symbol
 * @param symbol - Market indicator symbol (e.g., '^GSPC', 'total_market_cap')
 * @returns Tooltip text or undefined if not found
 */
export function getTooltip(symbol: string): string | undefined {
  return INDICATOR_TOOLTIPS[symbol]
}
