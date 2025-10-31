# ABOUTME: FastAPI router for Portfolio Rebalancing API endpoints (Epic 8 - F8.7-001)
# ABOUTME: RESTful API for analyzing portfolio allocation and generating rebalancing recommendations

"""
Rebalancing API Router

Endpoints:
- GET /api/rebalancing/analysis - Analyze current portfolio allocation vs target
- GET /api/rebalancing/recommendations - Get AI-powered rebalancing recommendations (F8.7-002)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_async_db
from rebalancing_service import RebalancingService
from analysis_service import AnalysisService
from claude_service import ClaudeService
from prompt_service import PromptService
from prompt_renderer import PromptDataCollector
from portfolio_service import PortfolioService
from yahoo_finance_service import YahooFinanceService
from cache_service import CacheService
from config import get_settings
from rebalancing_schemas import (
    RebalancingAnalysis,
    CustomAllocationRequest,
    RebalancingRecommendationResponse,
)


router = APIRouter(prefix="/api/rebalancing", tags=["rebalancing"])


async def get_rebalancing_service(db: AsyncSession = Depends(get_async_db)) -> RebalancingService:
    """
    Dependency to get RebalancingService instance.

    Args:
        db: Async database session

    Returns:
        RebalancingService instance
    """
    return RebalancingService(db)


@router.get("/analysis", response_model=RebalancingAnalysis)
async def get_rebalancing_analysis(
    target_model: str = Query(
        "moderate",
        description="Target allocation model: moderate, aggressive, conservative, or custom"
    ),
    custom_stocks: Optional[int] = Query(
        None,
        ge=0,
        le=100,
        description="Custom stocks percentage (required if target_model=custom)"
    ),
    custom_crypto: Optional[int] = Query(
        None,
        ge=0,
        le=100,
        description="Custom crypto percentage (required if target_model=custom)"
    ),
    custom_metals: Optional[int] = Query(
        None,
        ge=0,
        le=100,
        description="Custom metals percentage (required if target_model=custom)"
    ),
    rebalancing_service: RebalancingService = Depends(get_rebalancing_service)
):
    """
    Analyze portfolio allocation vs target and identify rebalancing needs.

    Compares current portfolio allocation against the selected target model
    and identifies which asset types are overweight or underweight.

    **Target Models**:
    - **moderate** (default): 60% stocks, 25% crypto, 15% metals
    - **aggressive**: 50% stocks, 40% crypto, 10% metals
    - **conservative**: 70% stocks, 15% crypto, 15% metals
    - **custom**: User-defined percentages (must sum to 100%)

    **Rebalancing Thresholds**:
    - **Trigger**: ±5% deviation from target (triggers rebalancing recommendation)
    - **Tolerance**: ±2% band (positions within this are considered balanced)
    - **Minimum Trade**: €50 (won't suggest trades smaller than this)

    **Returns**:
    - Current allocation by asset type
    - Deviations from target
    - Rebalancing deltas in EUR
    - Estimated transaction costs
    - Summary metrics

    **Example**:
    ```
    GET /api/rebalancing/analysis?target_model=moderate
    GET /api/rebalancing/analysis?target_model=custom&custom_stocks=50&custom_crypto=30&custom_metals=20
    ```
    """
    try:
        # Validate custom model inputs
        if target_model == "custom":
            if custom_stocks is None or custom_crypto is None or custom_metals is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom model requires all allocation percentages (custom_stocks, custom_crypto, custom_metals)"
                )

            total = custom_stocks + custom_crypto + custom_metals
            if total != 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Custom allocations must sum to 100%, got {total}%"
                )

        # Validate model name
        if target_model not in ["moderate", "aggressive", "conservative", "custom"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_model '{target_model}'. Valid options: moderate, aggressive, conservative, custom"
            )

        # Perform analysis
        analysis = await rebalancing_service.analyze_rebalancing(
            target_model=target_model,
            custom_stocks=custom_stocks,
            custom_crypto=custom_crypto,
            custom_metals=custom_metals
        )

        return analysis

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze rebalancing: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """
    Get list of available allocation models with their target percentages.

    Returns information about predefined models (moderate, aggressive, conservative)
    to help users understand their options.

    **Returns**:
    ```json
    {
      "models": {
        "moderate": {"stocks": 60, "crypto": 25, "metals": 15},
        "aggressive": {"stocks": 50, "crypto": 40, "metals": 10},
        "conservative": {"stocks": 70, "crypto": 15, "metals": 15}
      },
      "custom": {
        "description": "User-defined allocation percentages",
        "constraints": "Must sum to 100%"
      }
    }
    ```
    """
    return {
        "models": {
            "moderate": {
                "description": "Balanced growth with moderate risk",
                "stocks": 60,
                "crypto": 25,
                "metals": 15
            },
            "aggressive": {
                "description": "High growth with higher risk tolerance",
                "stocks": 50,
                "crypto": 40,
                "metals": 10
            },
            "conservative": {
                "description": "Stable growth with lower risk",
                "stocks": 70,
                "crypto": 15,
                "metals": 15
            }
        },
        "custom": {
            "description": "User-defined allocation percentages",
            "constraints": "Must sum to 100%",
            "example": {
                "stocks": 50,
                "crypto": 30,
                "metals": 20
            }
        },
        "thresholds": {
            "trigger": "±5% deviation triggers rebalancing",
            "tolerance": "±2% tolerance band (considered balanced)",
            "minimum_trade": "€50 minimum trade size"
        }
    }


async def get_analysis_service(db: AsyncSession = Depends(get_async_db)) -> AnalysisService:
    """
    Dependency to get AnalysisService instance with all dependencies.

    Creates and wires together:
    - ClaudeService (AI generation)
    - PromptService (template management)
    - PromptDataCollector (portfolio data)
    - CacheService (Redis caching)
    """
    settings = get_settings()

    # Initialize services
    claude_service = ClaudeService(settings)
    prompt_service = PromptService(db)
    portfolio_service = PortfolioService(db)
    yahoo_service = YahooFinanceService()
    cache_service = CacheService()

    # Initialize market data services
    twelve_data_service = None
    if settings.TWELVE_DATA_API_KEY:
        from twelve_data_service import TwelveDataService
        twelve_data_service = TwelveDataService(
            settings.TWELVE_DATA_API_KEY,
            redis_client=cache_service.client
        )

    alpha_vantage_service = None
    if settings.ALPHA_VANTAGE_API_KEY:
        from alpha_vantage_service import AlphaVantageService
        alpha_vantage_service = AlphaVantageService(settings.ALPHA_VANTAGE_API_KEY)

    # Initialize CoinGecko service
    coingecko_service = None
    try:
        from coingecko_service import CoinGeckoService
        coingecko_service = CoinGeckoService(
            api_key=settings.COINGECKO_API_KEY,
            redis_client=cache_service.client,
            calls_per_minute=settings.COINGECKO_RATE_LIMIT_PER_MINUTE
        )
    except Exception:
        pass

    # Initialize data collector
    data_collector = PromptDataCollector(
        db,
        portfolio_service,
        yahoo_service,
        twelve_data_service,
        alpha_vantage_service,
        coingecko_service
    )

    return AnalysisService(
        db,
        claude_service,
        prompt_service,
        data_collector,
        cache_service
    )


@router.get("/recommendations", response_model=RebalancingRecommendationResponse)
async def get_rebalancing_recommendations(
    target_model: str = Query(
        "moderate",
        description="Target allocation model: moderate, aggressive, conservative, or custom"
    ),
    custom_stocks: Optional[int] = Query(None, ge=0, le=100),
    custom_crypto: Optional[int] = Query(None, ge=0, le=100),
    custom_metals: Optional[int] = Query(None, ge=0, le=100),
    force_refresh: bool = Query(False, description="Bypass cache and generate fresh recommendations"),
    rebalancing_service: RebalancingService = Depends(get_rebalancing_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get AI-powered rebalancing recommendations.

    Uses Claude to generate specific buy/sell actions with rationale based on
    current portfolio allocation vs target model.

    **Workflow**:
    1. Analyzes current allocation vs target
    2. If balanced → returns empty recommendations
    3. If imbalanced → generates Claude recommendations with:
       - Specific symbols to buy/sell
       - Exact quantities and EUR amounts
       - Rationale for each action
       - Transaction data ready for manual input
       - Timing suggestions
       - Risk assessment

    **Caching**: Results cached for 6 hours to reduce API costs

    **Example**:
    ```
    GET /api/rebalancing/recommendations?target_model=moderate
    GET /api/rebalancing/recommendations?target_model=custom&custom_stocks=50&custom_crypto=30&custom_metals=20&force_refresh=true
    ```

    **Returns**: Prioritized list of recommendations with:
    - Action (BUY/SELL)
    - Symbol, quantity, price
    - Rationale and timing
    - Expected outcome after rebalancing
    - Risk assessment
    """
    try:
        # Get allocation analysis
        analysis = await rebalancing_service.analyze_rebalancing(
            target_model=target_model,
            custom_stocks=custom_stocks,
            custom_crypto=custom_crypto,
            custom_metals=custom_metals
        )

        # Generate AI recommendations
        recommendations = await analysis_service.generate_rebalancing_recommendations(
            analysis,
            force_refresh=force_refresh
        )

        return recommendations

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate rebalancing recommendations: {str(e)}"
        )
