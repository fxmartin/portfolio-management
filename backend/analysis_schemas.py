# ABOUTME: Pydantic schemas for Analysis API (Epic 8 - F8.3-001)
# ABOUTME: Request/response models for AI-powered market analysis endpoints

"""
Pydantic Schemas for Analysis API

Provides response models for:
- Global market analysis
- Position-level analysis
- Two-quarter forecasts
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class GlobalAnalysisResponse(BaseModel):
    """Response schema for global market analysis"""
    analysis: str = Field(..., description="Markdown-formatted analysis text")
    generated_at: datetime = Field(..., description="Timestamp when analysis was generated")
    tokens_used: int = Field(..., ge=0, description="Total tokens consumed by Claude API")
    cached: bool = Field(..., description="Whether this was served from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "## Market Sentiment\n\nCurrent markets showing...",
                "generated_at": "2025-10-29T10:30:00Z",
                "tokens_used": 1523,
                "cached": False
            }
        }


class PositionAnalysisResponse(BaseModel):
    """Response schema for position-level analysis"""
    analysis: str = Field(..., description="Markdown-formatted analysis text")
    recommendation: Optional[str] = Field(None, description="HOLD, BUY_MORE, REDUCE, or SELL")
    generated_at: datetime
    tokens_used: int = Field(..., ge=0)
    cached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "## Bitcoin Analysis\n\nCurrent price action suggests...",
                "recommendation": "HOLD",
                "generated_at": "2025-10-29T10:35:00Z",
                "tokens_used": 892,
                "cached": False
            }
        }


class QuarterScenario(BaseModel):
    """Scenario data for a single quarter"""
    price: float = Field(..., description="Predicted price in this scenario")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level (0-100%)")
    reasoning: str = Field(..., description="Explanation for this scenario")


class QuarterForecast(BaseModel):
    """Forecast data for one quarter with three scenarios"""
    pessimistic: QuarterScenario
    realistic: QuarterScenario
    optimistic: QuarterScenario


class ForecastResponse(BaseModel):
    """Response schema for two-quarter forecast"""
    q1_forecast: QuarterForecast = Field(..., description="First quarter forecast")
    q2_forecast: QuarterForecast = Field(..., description="Second quarter forecast")
    overall_outlook: str = Field(..., description="Summary of overall forecast")
    generated_at: datetime
    tokens_used: int = Field(..., ge=0)
    cached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "q1_forecast": {
                    "pessimistic": {"price": 45000, "confidence": 25, "reasoning": "Market downturn..."},
                    "realistic": {"price": 55000, "confidence": 50, "reasoning": "Steady growth..."},
                    "optimistic": {"price": 70000, "confidence": 25, "reasoning": "Bull market..."}
                },
                "q2_forecast": {
                    "pessimistic": {"price": 40000, "confidence": 20, "reasoning": "Extended bear..."},
                    "realistic": {"price": 60000, "confidence": 60, "reasoning": "Recovery phase..."},
                    "optimistic": {"price": 85000, "confidence": 20, "reasoning": "Major rally..."}
                },
                "overall_outlook": "Moderately bullish with volatility expected",
                "generated_at": "2025-10-29T10:40:00Z",
                "tokens_used": 2156,
                "cached": False
            }
        }
