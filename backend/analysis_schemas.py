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


class GlobalCryptoMarketData(BaseModel):
    """Global cryptocurrency market data from CoinGecko"""
    total_market_cap_eur: int = Field(..., description="Total crypto market cap in EUR")
    total_volume_24h_eur: int = Field(..., description="24h trading volume across all cryptos in EUR")
    btc_dominance: float = Field(..., description="Bitcoin dominance as percentage")
    eth_dominance: float = Field(..., description="Ethereum dominance as percentage")
    active_cryptocurrencies: int = Field(..., description="Number of active cryptocurrencies")
    markets: int = Field(..., description="Number of exchanges/markets")
    market_cap_change_24h: float = Field(..., description="24h market cap change percentage")
    defi_market_cap_eur: Optional[int] = Field(None, description="DeFi total value locked in EUR")
    defi_dominance: Optional[float] = Field(None, description="DeFi as % of total market cap")
    defi_24h_volume_eur: Optional[int] = Field(None, description="DeFi 24h trading volume in EUR")
    fear_greed_value: Optional[int] = Field(None, description="Fear & Greed Index value (0-100)")
    fear_greed_classification: Optional[str] = Field(None, description="Fear & Greed classification (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)")


class MarketIndicator(BaseModel):
    """Individual market indicator data"""
    symbol: str = Field(..., description="Market symbol (e.g., ^GSPC, ^VIX)")
    name: str = Field(..., description="Display name (e.g., S&P 500, VIX)")
    price: float = Field(..., description="Current price/value")
    change_percent: float = Field(..., description="24h change percentage")
    category: str = Field(..., description="Category: equities, risk, commodities, crypto")
    interpretation: Optional[str] = Field(None, description="Human-readable interpretation (e.g., VIX levels)")


class GlobalMarketIndicators(BaseModel):
    """Global market indicators grouped by category"""
    equities: List[MarketIndicator] = Field(default_factory=list, description="Equity index indicators")
    risk: List[MarketIndicator] = Field(default_factory=list, description="Risk indicators (VIX, yields, dollar)")
    commodities: List[MarketIndicator] = Field(default_factory=list, description="Commodity indicators")
    crypto: List[MarketIndicator] = Field(default_factory=list, description="Crypto indicators")


class GlobalAnalysisResponse(BaseModel):
    """Response schema for global market analysis"""
    analysis: str = Field(..., description="Markdown-formatted analysis text")
    global_crypto_market: Optional[GlobalCryptoMarketData] = Field(
        None,
        description="Global cryptocurrency market metrics (only when portfolio has crypto exposure)"
    )
    market_indicators: Optional[GlobalMarketIndicators] = Field(
        None,
        description="Global market indicators (equities, risk, commodities, crypto)"
    )
    generated_at: datetime = Field(..., description="Timestamp when analysis was generated")
    tokens_used: int = Field(..., ge=0, description="Total tokens consumed by Claude API")
    cached: bool = Field(..., description="Whether this was served from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "## Market Sentiment\n\nCurrent markets showing...",
                "global_crypto_market": {
                    "total_market_cap_eur": 2567000000000,
                    "total_volume_24h_eur": 98000000000,
                    "btc_dominance": 54.2,
                    "eth_dominance": 17.1,
                    "active_cryptocurrencies": 12543,
                    "markets": 1127,
                    "market_cap_change_24h": 1.8,
                    "defi_market_cap_eur": 87000000000,
                    "defi_dominance": 3.4,
                    "defi_24h_volume_eur": 4200000000
                },
                "generated_at": "2025-10-29T10:30:00Z",
                "tokens_used": 1523,
                "cached": False
            }
        }


class CryptoFundamentals(BaseModel):
    """Cryptocurrency fundamental data from CoinGecko"""
    market_cap: float = Field(..., description="Market capitalization in EUR")
    market_cap_rank: int = Field(..., description="Global market cap ranking")
    total_volume_24h: Optional[float] = Field(None, description="24-hour trading volume in EUR")
    circulating_supply: Optional[float] = Field(None, description="Circulating supply")
    max_supply: Optional[float] = Field(None, description="Maximum supply (if applicable)")
    ath: float = Field(..., description="All-time high price in EUR")
    ath_date: str = Field(..., description="Date when ATH was reached")
    ath_change_percentage: float = Field(..., description="% change from ATH")
    atl: float = Field(..., description="All-time low price in EUR")
    atl_date: str = Field(..., description="Date when ATL was reached")
    atl_change_percentage: float = Field(..., description="% change from ATL")
    price_change_percentage_7d: Optional[float] = Field(None, description="7-day price change %")
    price_change_percentage_30d: Optional[float] = Field(None, description="30-day price change %")
    price_change_percentage_1y: Optional[float] = Field(None, description="1-year price change %")
    all_time_roi: Optional[float] = Field(None, description="All-time ROI from ATL to ATH")


class PositionAnalysisResponse(BaseModel):
    """Response schema for position-level analysis"""
    analysis: str = Field(..., description="Markdown-formatted analysis text")
    recommendation: Optional[Recommendation] = Field(
        None,
        description="Investment recommendation: HOLD, BUY_MORE, REDUCE, or SELL"
    )
    crypto_fundamentals: Optional[CryptoFundamentals] = Field(
        None,
        description="Cryptocurrency fundamentals (only for crypto positions)"
    )
    generated_at: datetime
    tokens_used: int = Field(..., ge=0)
    cached: bool

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "## Bitcoin Analysis\n\nCurrent price action suggests...",
                "recommendation": "HOLD",
                "crypto_fundamentals": {
                    "market_cap": 1904377621119,
                    "market_cap_rank": 1,
                    "ath": 107662.0,
                    "ath_date": "2025-10-06",
                    "ath_change_percentage": -11.3
                },
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
