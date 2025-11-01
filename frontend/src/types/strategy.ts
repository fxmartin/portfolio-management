// ABOUTME: TypeScript interfaces for investment strategy management and AI-driven recommendations
// ABOUTME: Defines data structures for strategy CRUD, profit-taking, position assessment, and action planning

export interface InvestmentStrategy {
  id: number;
  user_id: number;
  strategy_text: string;
  target_annual_return?: number;
  risk_tolerance?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CUSTOM';
  time_horizon_years?: number;
  max_positions?: number;
  profit_taking_threshold?: number;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface TransactionData {
  transaction_type: string;
  symbol: string;
  quantity: number;
  price: number;
  total_value: number;
  currency: string;
  notes: string;
}

export interface ProfitTakingOpportunity {
  symbol: string;
  current_pnl_percentage: number;
  threshold: number;
  recommendation: string;
  expected_proceeds: number;
  rationale: string;
  transaction_data: TransactionData;
}

export interface PositionAssessment {
  symbol: string;
  fits_strategy: boolean;
  action: string;
  target_reduction?: number;
  rationale: string;
}

export interface NewPositionSuggestion {
  asset_type: string;
  region: string;
  sector: string;
  rationale: string;
  example_symbols: string[];
}

export interface ActionPlanItem {
  action: string;
  symbol?: string;
  percentage?: number;
  target_region?: string;
  target_sector?: string;
  allocation?: number;
  expected_proceeds?: number;
  timing?: string;
  rationale?: string;
  reason?: string;
  approach?: string;
  suggested_symbols?: string[];
  transaction_data?: TransactionData;
}

export interface StrategyDrivenRecommendationResponse {
  summary: string;
  alignment_score: number;
  key_insights: string[];
  profit_taking_opportunities: ProfitTakingOpportunity[];
  position_assessments: PositionAssessment[];
  new_position_suggestions: NewPositionSuggestion[];
  action_plan: {
    immediate_actions: ActionPlanItem[];
    redeployment: ActionPlanItem[];
    gradual_adjustments: ActionPlanItem[];
  };
  target_annual_return_assessment: {
    current_ytd_return: number;
    target_return: number;
    on_track: boolean;
    commentary: string;
  };
  risk_assessment: string;
  next_review_date: string;
  generated_at: string;
  tokens_used: number;
  cached: boolean;
}

export interface StrategyTemplate {
  id: string;
  title: string;
  description: string;
  strategy_text: string;
  target_annual_return: number;
  risk_tolerance: 'LOW' | 'MEDIUM' | 'HIGH';
  time_horizon_years: number;
  max_positions: number;
  profit_taking_threshold: number;
}
