// ABOUTME: API client for AI-powered portfolio analysis endpoints
// ABOUTME: Handles communication with Claude-powered analysis, position insights, and forecasts

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface GlobalAnalysisResponse {
  analysis: string
  generated_at: string
  tokens_used: number
  cached?: boolean
}

export interface PositionAnalysisResponse {
  symbol: string
  analysis: string
  recommendation: 'HOLD' | 'BUY_MORE' | 'REDUCE' | 'SELL'
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
