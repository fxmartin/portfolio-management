# ABOUTME: Pydantic schemas for portfolio rebalancing recommendations
# ABOUTME: Defines request/response models for rebalancing analysis and AI recommendations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator

from models import AssetType


class AllocationStatus(str, Enum):
    """Asset allocation status relative to target"""
    OVERWEIGHT = "OVERWEIGHT"  # > target + 5%
    UNDERWEIGHT = "UNDERWEIGHT"  # < target - 5%
    SLIGHTLY_OVERWEIGHT = "SLIGHTLY_OVERWEIGHT"  # target + 2% to target + 5%
    SLIGHTLY_UNDERWEIGHT = "SLIGHTLY_UNDERWEIGHT"  # target - 5% to target - 2%
    BALANCED = "BALANCED"  # within ±2%


class AssetTypeAllocation(BaseModel):
    """Allocation data for a single asset type"""
    asset_type: AssetType
    current_value: Decimal = Field(..., description="Current EUR value of this asset type")
    current_percentage: Decimal = Field(..., description="Current allocation percentage (0-100)")
    target_percentage: Decimal = Field(..., description="Target allocation percentage (0-100)")
    deviation: Decimal = Field(..., description="Deviation from target (current - target)")
    status: AllocationStatus
    rebalancing_needed: bool = Field(..., description="True if deviation exceeds threshold")
    delta_value: Decimal = Field(..., description="EUR amount to buy (+) or sell (-)")
    delta_percentage: Decimal = Field(..., description="Percentage points to adjust")

    class Config:
        json_schema_extra = {
            "example": {
                "asset_type": "STOCK",
                "current_value": 27500.00,
                "current_percentage": 55.0,
                "target_percentage": 60.0,
                "deviation": -5.0,
                "status": "UNDERWEIGHT",
                "rebalancing_needed": True,
                "delta_value": 2500.00,
                "delta_percentage": 5.0
            }
        }


class RebalancingAnalysis(BaseModel):
    """Complete rebalancing analysis with allocation breakdown"""
    total_portfolio_value: Decimal = Field(..., description="Total portfolio value in EUR")
    current_allocation: List[AssetTypeAllocation]
    target_model: str = Field(..., description="moderate, aggressive, conservative, or custom")
    rebalancing_required: bool = Field(..., description="True if any asset exceeds threshold")
    total_trades_needed: int = Field(..., description="Number of trades required")
    estimated_transaction_costs: Decimal = Field(..., description="Estimated fees in EUR")

    # Summary metrics
    largest_deviation: Decimal = Field(..., description="Largest deviation in percentage points")
    most_overweight: Optional[str] = Field(None, description="Asset type most overweight")
    most_underweight: Optional[str] = Field(None, description="Asset type most underweight")

    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "total_portfolio_value": 50000.00,
                "target_model": "moderate",
                "rebalancing_required": True,
                "total_trades_needed": 5,
                "estimated_transaction_costs": 125.50,
                "largest_deviation": -15.0,
                "most_overweight": "crypto",
                "most_underweight": "stocks"
            }
        }


class RebalancingAction(str, Enum):
    """Type of rebalancing action"""
    BUY = "BUY"
    SELL = "SELL"


class TransactionData(BaseModel):
    """Ready-to-execute transaction data for manual input"""
    transaction_type: str = Field(..., description="BUY or SELL")
    symbol: str
    quantity: Decimal
    price: Decimal
    total_value: Decimal
    currency: str = "EUR"
    notes: str

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_type": "BUY",
                "symbol": "MSTR",
                "quantity": 10,
                "price": 248.50,
                "total_value": 2485.00,
                "currency": "EUR",
                "notes": "Rebalancing: Increase stocks to 60% target"
            }
        }


class RebalancingRecommendation(BaseModel):
    """Single buy/sell recommendation from AI"""
    action: RebalancingAction
    symbol: str
    asset_type: AssetType
    quantity: Decimal
    current_price: Decimal
    estimated_value: Decimal
    rationale: str = Field(..., description="AI explanation for this recommendation")
    priority: int = Field(..., ge=1, description="Priority rank (1 = highest)")
    timing: Optional[str] = Field(None, description="Suggested timing for execution")
    transaction_data: TransactionData = Field(..., description="Ready for transaction input")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "SELL",
                "symbol": "BTC",
                "asset_type": "CRYPTO",
                "quantity": 0.05,
                "current_price": 81234.56,
                "estimated_value": 4061.73,
                "rationale": "Reduce crypto exposure from 35% to 25%. BTC showing strength - good exit.",
                "priority": 1,
                "timing": "Consider selling into current strength (+2.3% today)"
            }
        }


class ExpectedOutcome(BaseModel):
    """Expected portfolio state after rebalancing"""
    stocks_percentage: Decimal
    crypto_percentage: Decimal
    metals_percentage: Decimal
    total_trades: int
    estimated_costs: Decimal
    net_allocation_improvement: str = Field(..., description="Human-readable improvement description")

    class Config:
        json_schema_extra = {
            "example": {
                "stocks_percentage": 60.0,
                "crypto_percentage": 25.0,
                "metals_percentage": 15.0,
                "total_trades": 5,
                "estimated_costs": 125.50,
                "net_allocation_improvement": "+15% closer to target"
            }
        }


class RebalancingRecommendationResponse(BaseModel):
    """Complete AI-generated rebalancing recommendations"""
    summary: str = Field(..., description="Overall strategy summary")
    priority: str = Field(..., description="HIGH, MEDIUM, or LOW")
    recommendations: List[RebalancingRecommendation]
    expected_outcome: ExpectedOutcome
    risk_assessment: str = Field(..., description="AI risk evaluation")
    implementation_notes: str = Field(..., description="Practical execution guidance")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: int = Field(0, description="Claude API tokens consumed")
    cached: bool = Field(False, description="Whether result was cached")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Reduce crypto exposure, increase stocks allocation",
                "priority": "HIGH",
                "risk_assessment": "Low - Recommendations diversified across asset types",
                "implementation_notes": "Execute in 2-3 tranches over 1 week",
                "tokens_used": 1850,
                "cached": False
            }
        }


class CustomAllocationRequest(BaseModel):
    """Request model for custom allocation percentages"""
    stocks: int = Field(..., ge=0, le=100, description="Target stocks percentage")
    crypto: int = Field(..., ge=0, le=100, description="Target crypto percentage")
    metals: int = Field(..., ge=0, le=100, description="Target metals percentage")

    @field_validator('stocks', 'crypto', 'metals')
    @classmethod
    def validate_percentage(cls, v):
        """Ensure percentages are valid"""
        if v < 0 or v > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

    def validate_sum(self):
        """Validate that percentages sum to 100"""
        total = self.stocks + self.crypto + self.metals
        if total != 100:
            raise ValueError(f"Allocations must sum to 100%, got {total}%")
        return True

    class Config:
        json_schema_extra = {
            "example": {
                "stocks": 50,
                "crypto": 30,
                "metals": 20
            }
        }
