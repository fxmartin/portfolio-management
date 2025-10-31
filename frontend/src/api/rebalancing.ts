// ABOUTME: API client for portfolio rebalancing endpoints
// ABOUTME: Handles allocation analysis and AI-powered rebalancing recommendations

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface AssetTypeAllocation {
  asset_type: 'STOCK' | 'CRYPTO' | 'METAL'
  current_value: number
  current_percentage: number
  target_percentage: number
  deviation: number
  status: 'OVERWEIGHT' | 'UNDERWEIGHT' | 'SLIGHTLY_OVERWEIGHT' | 'SLIGHTLY_UNDERWEIGHT' | 'BALANCED'
  rebalancing_needed: boolean
  delta_value: number
  delta_percentage: number
}

export interface RebalancingAnalysis {
  total_portfolio_value: number
  current_allocation: AssetTypeAllocation[]
  target_model: string
  rebalancing_required: boolean
  total_trades_needed: number
  estimated_transaction_costs: number
  largest_deviation: number
  most_overweight: string | null
  most_underweight: string | null
  generated_at: string
}

export interface TransactionData {
  transaction_type: 'BUY' | 'SELL'
  symbol: string
  quantity: number
  price: number
  total_value: number
  currency: string
  notes: string
}

export interface RebalancingRecommendation {
  action: 'BUY' | 'SELL'
  symbol: string
  asset_type: 'STOCK' | 'CRYPTO' | 'METAL'
  quantity: number
  current_price: number
  estimated_value: number
  rationale: string
  priority: number
  timing: string | null
  transaction_data: TransactionData
}

export interface ExpectedOutcome {
  stocks_percentage: number
  crypto_percentage: number
  metals_percentage: number
  total_trades: number
  estimated_costs: number
  net_allocation_improvement: string
}

export interface RebalancingRecommendationResponse {
  summary: string
  priority: 'HIGH' | 'MEDIUM' | 'LOW'
  recommendations: RebalancingRecommendation[]
  expected_outcome: ExpectedOutcome
  risk_assessment: string
  implementation_notes: string
  generated_at: string
  tokens_used: number
  cached: boolean
}

export interface AllocationModel {
  name: string
  description: string
  stocks: number
  crypto: number
  metals: number
}

export interface AllocationModelsResponse {
  models: {
    moderate: AllocationModel
    aggressive: AllocationModel
    conservative: AllocationModel
  }
  custom: {
    description: string
    constraints: string
    example: { stocks: number; crypto: number; metals: number }
  }
  thresholds: {
    trigger: string
    tolerance: string
    minimum_trade: string
  }
}

/**
 * Get rebalancing analysis comparing current allocation vs target model
 */
export const getRebalancingAnalysis = async (
  targetModel: string = 'moderate',
  customStocks?: number,
  customCrypto?: number,
  customMetals?: number
): Promise<RebalancingAnalysis> => {
  const params: any = { target_model: targetModel }

  if (targetModel === 'custom') {
    params.custom_stocks = customStocks
    params.custom_crypto = customCrypto
    params.custom_metals = customMetals
  }

  const response = await axios.get(`${API_URL}/api/rebalancing/analysis`, { params })
  return response.data
}

/**
 * Get AI-powered rebalancing recommendations from Claude
 */
export const getRebalancingRecommendations = async (
  targetModel: string = 'moderate',
  customStocks?: number,
  customCrypto?: number,
  customMetals?: number,
  forceRefresh: boolean = false
): Promise<RebalancingRecommendationResponse> => {
  const params: any = {
    target_model: targetModel,
    force_refresh: forceRefresh
  }

  if (targetModel === 'custom') {
    params.custom_stocks = customStocks
    params.custom_crypto = customCrypto
    params.custom_metals = customMetals
  }

  const response = await axios.get(`${API_URL}/api/rebalancing/recommendations`, { params })
  return response.data
}

/**
 * Get available allocation models
 */
export const getAllocationModels = async (): Promise<AllocationModelsResponse> => {
  const response = await axios.get(`${API_URL}/api/rebalancing/models`)
  return response.data
}

/**
 * Copy transaction data to clipboard as CSV
 */
export const copyTransactionDataToClipboard = (transactionData: TransactionData): void => {
  const csv = `Type,Symbol,Quantity,Price,Total,Currency,Notes
${transactionData.transaction_type},${transactionData.symbol},${transactionData.quantity},${transactionData.price},${transactionData.total_value},${transactionData.currency},"${transactionData.notes}"`

  navigator.clipboard.writeText(csv)
}
