// ABOUTME: API client for AI-powered portfolio analysis endpoints
// ABOUTME: Handles communication with Claude-powered analysis, position insights, and forecasts

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface GlobalCryptoMarketData {
  total_market_cap_eur: number
  total_volume_24h_eur: number
  btc_dominance: number
  eth_dominance: number
  active_cryptocurrencies: number
  markets: number
  market_cap_change_24h: number
  defi_market_cap_eur?: number
  defi_dominance?: number
  defi_24h_volume_eur?: number
  fear_greed_value?: number
  fear_greed_classification?: string
}

export interface MarketIndicator {
  symbol: string
  name: string
  price: number
  change_percent: number
  category: 'equities' | 'risk' | 'commodities' | 'crypto'
  interpretation?: string
}

export interface GlobalMarketIndicators {
  equities: MarketIndicator[]
  risk: MarketIndicator[]
  commodities: MarketIndicator[]
  crypto: MarketIndicator[]
}

export interface GlobalAnalysisResponse {
  analysis: string
  global_crypto_market?: GlobalCryptoMarketData
  market_indicators?: GlobalMarketIndicators
  generated_at: string
  tokens_used: number
  cached?: boolean
}

export interface CryptoFundamentals {
  market_cap: number
  market_cap_rank: number
  total_volume_24h?: number
  circulating_supply?: number
  max_supply?: number
  ath: number
  ath_date: string
  ath_change_percentage: number
  atl: number
  atl_date: string
  atl_change_percentage: number
  price_change_percentage_7d?: number
  price_change_percentage_30d?: number
  price_change_percentage_1y?: number
  all_time_roi?: number
}

export interface PositionAnalysisResponse {
  symbol: string
  analysis: string
  recommendation: 'HOLD' | 'BUY_MORE' | 'REDUCE' | 'SELL'
  crypto_fundamentals?: CryptoFundamentals
  generated_at: string
  tokens_used: number
  cached?: boolean
}

export interface ForecastScenario {
  price: number
  confidence: number
  assumptions: string
  risks: string
}

export interface QuarterForecast {
  pessimistic: ForecastScenario
  realistic: ForecastScenario
  optimistic: ForecastScenario
}

export interface ForecastResponse {
  overall_outlook: string
  q1_forecast: QuarterForecast
  q2_forecast: QuarterForecast
  generated_at: string
  tokens_used: number
  cached?: boolean
}

export interface BulkAnalysisRequest {
  symbols: string[]
}

export interface BulkAnalysisResponse {
  analyses: PositionAnalysisResponse[]
  total_tokens: number
  generated_at: string
}

export interface BulkForecastRequest {
  symbols: string[]
}

export interface BulkForecastResponse {
  forecasts: ForecastResponse[]
  total_tokens: number
  generated_at: string
}

/**
 * Get global portfolio market analysis
 */
export async function getGlobalAnalysis(forceRefresh = false): Promise<GlobalAnalysisResponse> {
  const params = forceRefresh ? { force_refresh: 'true' } : {}
  const response = await axios.get<GlobalAnalysisResponse>(
    `${API_URL}/api/analysis/global`,
    { params }
  )
  return response.data
}

/**
 * Get analysis for a specific position
 */
export async function getPositionAnalysis(
  symbol: string,
  forceRefresh = false
): Promise<PositionAnalysisResponse> {
  const params = forceRefresh ? { force_refresh: 'true' } : {}
  const response = await axios.get<PositionAnalysisResponse>(
    `${API_URL}/api/analysis/position/${symbol}`,
    { params }
  )
  return response.data
}

/**
 * Get forecast for a specific position
 */
export async function getForecast(
  symbol: string,
  forceRefresh = false
): Promise<ForecastResponse> {
  const params = forceRefresh ? { force_refresh: 'true' } : {}
  const response = await axios.get<ForecastResponse>(
    `${API_URL}/api/analysis/forecast/${symbol}`,
    { params }
  )
  return response.data
}

/**
 * Get bulk analysis for multiple positions
 */
export async function getBulkAnalysis(
  request: BulkAnalysisRequest
): Promise<BulkAnalysisResponse> {
  const response = await axios.post<BulkAnalysisResponse>(
    `${API_URL}/api/analysis/positions/bulk`,
    request
  )
  return response.data
}

/**
 * Get bulk forecasts for multiple positions
 */
export async function getBulkForecasts(
  request: BulkForecastRequest
): Promise<BulkForecastResponse> {
  const response = await axios.post<BulkForecastResponse>(
    `${API_URL}/api/analysis/forecasts/bulk`,
    request
  )
  return response.data
}
