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
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, conlist


class Recommendation(str, Enum):
    """Position recommendation extracted from AI analysis"""
    HOLD = "HOLD"
    BUY_MORE = "BUY_MORE"
    REDUCE = "REDUCE"
    SELL = "SELL"


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
    recommendation: Optional[Recommendation] = Field(
        None,
        description="Investment recommendation: HOLD, BUY_MORE, REDUCE, or SELL"
    )
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


class BulkAnalysisRequest(BaseModel):
    """Request schema for bulk position analysis"""
    symbols: conlist(str, min_length=1, max_length=10) = Field(..., description="List of asset symbols (1-10)")

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["BTC", "ETH", "SOL", "AAPL", "MSTR"]
            }
        }


class BulkAnalysisResponse(BaseModel):
    """Response schema for bulk position analysis"""
    analyses: Dict[str, PositionAnalysisResponse] = Field(
        ...,
        description="Map of symbol to analysis response"
    )
    total_tokens_used: int = Field(..., ge=0, description="Total tokens across all analyses")

    class Config:
        json_schema_extra = {
            "example": {
                "analyses": {
                    "BTC": {
                        "analysis": "## Bitcoin Analysis\n\nStrong momentum...",
                        "recommendation": "HOLD",
                        "generated_at": "2025-10-29T10:35:00Z",
                        "tokens_used": 892,
                        "cached": False
                    },
                    "ETH": {
                        "analysis": "## Ethereum Analysis\n\nConsolidating...",
                        "recommendation": "BUY_MORE",
                        "generated_at": "2025-10-29T10:35:15Z",
                        "tokens_used": 847,
                        "cached": False
                    }
                },
                "total_tokens_used": 1739
            }
        }


class QuarterScenario(BaseModel):
    """Scenario data for a single quarter"""
    price: float = Field(..., description="Predicted price in this scenario")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level (0-100%)")
    assumptions: str = Field(..., description="Key assumptions driving this scenario")
    risks: str = Field(..., description="Main risk factors for this scenario")


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
                    "pessimistic": {"price": 45000, "confidence": 25, "assumptions": "Market downturn scenario", "risks": "Regulatory pressure"},
                    "realistic": {"price": 55000, "confidence": 50, "assumptions": "Steady growth continues", "risks": "Market volatility"},
                    "optimistic": {"price": 70000, "confidence": 25, "assumptions": "Bull market catalyst", "risks": "Overextension"}
                },
                "q2_forecast": {
                    "pessimistic": {"price": 40000, "confidence": 20, "assumptions": "Extended bear market", "risks": "Economic recession"},
                    "realistic": {"price": 60000, "confidence": 60, "assumptions": "Recovery phase begins", "risks": "Rate uncertainty"},
                    "optimistic": {"price": 85000, "confidence": 20, "assumptions": "Major rally continues", "risks": "Correction risk"}
                },
                "overall_outlook": "Moderately bullish with volatility expected",
                "generated_at": "2025-10-29T10:40:00Z",
                "tokens_used": 2156,
                "cached": False
            }
        }


class BulkForecastRequest(BaseModel):
    """Request schema for bulk forecast generation"""
    symbols: conlist(str, min_length=1, max_length=5) = Field(
        ...,
        description="List of asset symbols (1-5 max for token management)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["BTC", "ETH", "AAPL"]
            }
        }


class BulkForecastResponse(BaseModel):
    """Response schema for bulk forecast generation"""
    forecasts: Dict[str, ForecastResponse] = Field(
        ...,
        description="Map of symbol to forecast response"
    )
    total_tokens_used: int = Field(..., ge=0, description="Total tokens across all forecasts")

    class Config:
        json_schema_extra = {
            "example": {
                "forecasts": {
                    "BTC": {
                        "q1_forecast": {
                            "pessimistic": {"price": 45000, "confidence": 25, "assumptions": "Market downturn scenario", "risks": "Regulatory pressure"},
                            "realistic": {"price": 55000, "confidence": 50, "assumptions": "Steady growth continues", "risks": "Market volatility"},
                            "optimistic": {"price": 70000, "confidence": 25, "assumptions": "Bull market catalyst", "risks": "Overextension"}
                        },
                        "q2_forecast": {
                            "pessimistic": {"price": 40000, "confidence": 20, "assumptions": "Extended bear market", "risks": "Economic recession"},
                            "realistic": {"price": 60000, "confidence": 60, "assumptions": "Recovery phase begins", "risks": "Rate uncertainty"},
                            "optimistic": {"price": 85000, "confidence": 20, "assumptions": "Major rally continues", "risks": "Correction risk"}
                        },
                        "overall_outlook": "Moderately bullish",
                        "generated_at": "2025-10-29T10:40:00Z",
                        "tokens_used": 2156,
                        "cached": False
                    }
                },
                "total_tokens_used": 2156
            }
        }
