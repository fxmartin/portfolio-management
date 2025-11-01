# ABOUTME: Pydantic schemas for Investment Strategy API (Epic 8 - F8.8-001)
# ABOUTME: Request/response models for strategy CRUD operations with validation

"""
Pydantic Schemas for Investment Strategy Management

Provides request and response models for:
- Creating investment strategies
- Updating investment strategies
- Retrieving investment strategies
- Strategy-driven recommendations (F8.8-002)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class RiskTolerance(str, Enum):
    """Risk tolerance levels for investment strategy"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CUSTOM = "CUSTOM"


class InvestmentStrategyCreate(BaseModel):
    """Request schema for creating an investment strategy"""
    strategy_text: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Investment strategy description (50-5000 chars, minimum 20 words)"
    )
    target_annual_return: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Target annual return percentage (0-100%)"
    )
    risk_tolerance: Optional[RiskTolerance] = Field(
        None,
        description="Risk tolerance level"
    )
    time_horizon_years: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Investment time horizon in years (1-50)"
    )
    max_positions: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Maximum number of positions (1-100)"
    )
    profit_taking_threshold: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Profit taking threshold percentage (0-100%)"
    )

    @field_validator('strategy_text')
    @classmethod
    def validate_minimum_words(cls, v: str) -> str:
        """Validate strategy has at least 20 words"""
        words = v.split()
        if len(words) < 20:
            raise ValueError(f"Strategy must contain at least 20 words (found {len(words)})")
        return v


class InvestmentStrategyUpdate(BaseModel):
    """Request schema for updating an investment strategy (all fields optional)"""
    strategy_text: Optional[str] = Field(
        None,
        min_length=50,
        max_length=5000,
        description="Investment strategy description"
    )
    target_annual_return: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Target annual return percentage"
    )
    risk_tolerance: Optional[RiskTolerance] = Field(
        None,
        description="Risk tolerance level"
    )
    time_horizon_years: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Investment time horizon in years"
    )
    max_positions: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Maximum number of positions"
    )
    profit_taking_threshold: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Profit taking threshold percentage"
    )

    @field_validator('strategy_text')
    @classmethod
    def validate_minimum_words(cls, v: Optional[str]) -> Optional[str]:
        """Validate strategy has at least 20 words if provided"""
        if v is not None:
            words = v.split()
            if len(words) < 20:
                raise ValueError(f"Strategy must contain at least 20 words (found {len(words)})")
        return v


class InvestmentStrategyResponse(BaseModel):
    """Response schema for investment strategy"""
    id: int
    user_id: int
    strategy_text: str
    target_annual_return: Optional[float]
    risk_tolerance: Optional[str]
    time_horizon_years: Optional[int]
    max_positions: Optional[int]
    profit_taking_threshold: Optional[float]
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True  # Pydantic v2


# ==================== F8.8-002: Strategy-Driven Recommendations ====================

class TransactionData(BaseModel):
    """Transaction data for recommended actions"""
    transaction_type: str = Field(..., description="BUY or SELL")
    symbol: str = Field(..., description="Asset symbol")
    quantity: float = Field(..., description="Quantity to buy/sell")
    price: float = Field(..., description="Recommended execution price")
    total_value: float = Field(..., description="Total EUR value")
    currency: str = Field(default="EUR", description="Currency")
    notes: Optional[str] = Field(None, description="Additional notes")


class ProfitTakingOpportunity(BaseModel):
    """Profit taking opportunity assessment"""
    symbol: str
    current_value: float
    entry_cost: float
    unrealized_gain: float
    gain_percentage: float
    holding_period_days: int
    recommendation: str  # TAKE_PROFIT, HOLD_FOR_MORE, PARTIAL_SELL
    rationale: str
    suggested_sell_percentage: Optional[float] = None
    transaction_data: Optional[TransactionData] = None


class PositionAssessment(BaseModel):
    """Individual position assessment against strategy"""
    symbol: str
    current_allocation: float
    strategic_fit: str  # ALIGNED, OVERWEIGHT, UNDERWEIGHT, MISALIGNED
    action_needed: str  # HOLD, REDUCE, INCREASE, SELL
    rationale: str


class NewPositionSuggestion(BaseModel):
    """Suggestion for new position to add"""
    symbol: str
    asset_type: str
    rationale: str
    suggested_allocation: float
    entry_strategy: str


class ActionPlanItem(BaseModel):
    """Single item in recommended action plan"""
    priority: int
    action: str
    symbol: str
    details: str
    expected_impact: str
    transaction_data: Optional[TransactionData] = None


class TargetReturnAssessment(BaseModel):
    """Assessment of target return achievability"""
    target_return: float
    current_projected_return: float
    achievability: str  # ACHIEVABLE, CHALLENGING, UNREALISTIC
    required_changes: str
    risk_level: str


class StrategyDrivenRecommendationResponse(BaseModel):
    """
    Complete response for strategy-driven portfolio recommendations.

    This is the main response model for GET /api/strategy/recommendations.
    Contains comprehensive analysis of portfolio alignment with investment strategy.
    """
    summary: str = Field(..., description="Executive summary of recommendations")

    alignment_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Overall portfolio alignment score (0-10 scale)"
    )

    key_insights: List[str] = Field(
        default_factory=list,
        description="3-5 key insights about portfolio alignment"
    )

    profit_taking_opportunities: List[ProfitTakingOpportunity] = Field(
        default_factory=list,
        description="Positions that have reached profit-taking thresholds"
    )

    position_assessments: List[PositionAssessment] = Field(
        default_factory=list,
        description="Assessment of each position against strategy"
    )

    new_position_suggestions: List[NewPositionSuggestion] = Field(
        default_factory=list,
        description="Suggested new positions to align with strategy"
    )

    action_plan: Dict[str, List[ActionPlanItem]] = Field(
        default_factory=dict,
        description="Action plan with immediate_actions, redeployment, gradual_adjustments"
    )

    target_annual_return_assessment: Optional[TargetReturnAssessment] = Field(
        None,
        description="Assessment of target return achievability"
    )

    risk_assessment: str = Field(
        ...,
        description="Overall risk assessment"
    )

    next_review_date: str = Field(
        ...,
        description="Recommended next review date (YYYY-MM-DD format)"
    )

    generated_at: datetime = Field(..., description="Timestamp of generation")
    tokens_used: int = Field(..., description="Claude API tokens used")
    cached: bool = Field(default=False, description="Whether result was cached")
