# ABOUTME: FastAPI router for AI Analysis API endpoints (Epic 8 - F8.3-001)
# ABOUTME: RESTful API for generating and retrieving AI-powered market analysis

"""
Analysis API Router

Endpoints:
- GET /api/analysis/global - Generate global market analysis
- GET /api/analysis/position/{symbol} - Generate position-specific analysis
- GET /api/analysis/forecast/{symbol} - Generate two-quarter forecast
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import asyncio

from database import get_async_db
from analysis_service import AnalysisService
from claude_service import ClaudeService
from prompt_service import PromptService
from prompt_renderer import PromptDataCollector
from portfolio_service import PortfolioService
from yahoo_finance_service import YahooFinanceService
from cache_service import CacheService
from config import get_settings
from analysis_schemas import (
    GlobalAnalysisResponse,
    PositionAnalysisResponse,
    ForecastResponse,
    BulkAnalysisRequest,
    BulkAnalysisResponse,
    BulkForecastRequest,
    BulkForecastResponse
)


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


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

    # Initialize market data services with fallback chain
    # Priority: Twelve Data (paid, best European coverage) -> Yahoo -> Alpha Vantage
    twelve_data_service = None
    if settings.TWELVE_DATA_API_KEY:
        from twelve_data_service import TwelveDataService
        twelve_data_service = TwelveDataService(
            settings.TWELVE_DATA_API_KEY,
            redis_client=cache_service.client
        )
        print("[Analysis Router] ✓ Twelve Data service initialized (primary) with Redis caching")

    alpha_vantage_service = None
    if settings.ALPHA_VANTAGE_API_KEY:
        from alpha_vantage_service import AlphaVantageService
        alpha_vantage_service = AlphaVantageService(settings.ALPHA_VANTAGE_API_KEY)
        print("[Analysis Router] ✓ Alpha Vantage service initialized (fallback)")

    # Initialize CoinGecko service for crypto fundamentals
    coingecko_service = None
    try:
        from coingecko_service import CoinGeckoService
        coingecko_service = CoinGeckoService(
            api_key=settings.COINGECKO_API_KEY,
            redis_client=cache_service.client,
            calls_per_minute=settings.COINGECKO_RATE_LIMIT_PER_MINUTE
        )
        tier = 'Demo tier' if settings.COINGECKO_API_KEY else 'free tier'
        print(f"[Analysis Router] ✓ CoinGecko service initialized ({tier}, {settings.COINGECKO_RATE_LIMIT_PER_MINUTE} calls/min)")
    except Exception as e:
        print(f"[Analysis Router] ⚠ CoinGecko service failed to initialize: {e}")

    # Initialize data collector with all available market data sources
    data_collector = PromptDataCollector(
        db,
        portfolio_service,
        yahoo_service,
        twelve_data_service,
        alpha_vantage_service,
        coingecko_service
    )

    # Create and return analysis service
    return AnalysisService(
        db=db,
        claude_service=claude_service,
        prompt_service=prompt_service,
        data_collector=data_collector,
        cache_service=cache_service
    )


@router.get("/global", response_model=GlobalAnalysisResponse)
async def get_global_analysis(
    force_refresh: bool = Query(
        False,
        description="Force new analysis generation, bypassing cache"
    ),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Generate global market analysis for entire portfolio.

    Returns cached analysis if available and recent (< 24 hours),
    otherwise generates fresh analysis using Claude API.

    **Performance**:
    - Fresh analysis: ~5-10 seconds
    - Cached analysis: <100ms

    **Cache Duration**: 24 hours (reduces API calls by 96%)

    **Parameters**:
    - **force_refresh**: Set to `true` to bypass cache and generate new analysis

    **Response includes**:
    - Market sentiment analysis
    - Macro-economic factors
    - Sector insights relevant to holdings
    - Key risks to monitor
    - Portfolio-level P&L context
    """
    try:
        result = await analysis_service.generate_global_analysis(force_refresh)
        return GlobalAnalysisResponse(**result)
    except ValueError as e:
        # Prompt not found or data collection failed
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Claude API error or other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@router.get("/position/{symbol}", response_model=PositionAnalysisResponse)
async def get_position_analysis(
    symbol: str = Path(..., description="Asset symbol (e.g., BTC, AAPL)"),
    force_refresh: bool = Query(False, description="Force new analysis generation"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Generate analysis for specific position.

    Returns cached analysis if available and recent (< 24 hours),
    otherwise generates fresh analysis.

    **Performance**:
    - Fresh analysis: ~3-5 seconds
    - Cached analysis: <100ms

    **Cache Duration**: 24 hours (reduces API calls by 96%)
    """
    try:
        result = await analysis_service.generate_position_analysis(symbol, force_refresh)
        return PositionAnalysisResponse(**result)
    except ValueError as e:
        # Position not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@router.get("/forecast/{symbol}", response_model=ForecastResponse)
async def get_forecast(
    symbol: str = Path(..., description="Asset symbol (e.g., BTC, AAPL)"),
    force_refresh: bool = Query(False, description="Force new forecast generation"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Generate two-quarter forecast with three scenarios.

    Returns cached forecast if available and recent (< 24 hours),
    otherwise generates fresh forecast.

    **Performance**:
    - Fresh forecast: ~8-15 seconds
    - Cached forecast: <100ms

    **Forecast includes**:
    - Q1 & Q2 predictions with pessimistic/realistic/optimistic scenarios
    - Confidence levels for each scenario
    - Reasoning for each prediction
    - Overall market outlook
    """
    try:
        result = await analysis_service.generate_forecast(symbol, force_refresh)
        return ForecastResponse(**result)
    except ValueError as e:
        # Position not found or forecast invalid
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )


@router.post("/positions/bulk", response_model=BulkAnalysisResponse)
async def get_bulk_position_analysis(
    request: BulkAnalysisRequest,
    force_refresh: bool = Query(False, description="Force new analysis generation"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Generate analysis for multiple positions in parallel.

    Useful for analyzing entire portfolio in one request.
    Maximum 10 positions per request.

    **Performance**:
    - Fresh analysis: ~15-30 seconds (parallel execution)
    - Cached analysis: <500ms

    **Request body**:
    ```json
    {
        "symbols": ["BTC", "ETH", "SOL", "AAPL", "MSTR"]
    }
    ```

    **Response includes**:
    - Individual analysis for each symbol
    - Recommendations per position
    - Total tokens consumed across all analyses
    """
    try:
        # Generate all analyses in parallel
        results = await asyncio.gather(*[
            analysis_service.generate_position_analysis(symbol, force_refresh)
            for symbol in request.symbols
        ])

        # Build response
        analyses = {
            symbol: PositionAnalysisResponse(**result)
            for symbol, result in zip(request.symbols, results)
        }

        total_tokens = sum(r['tokens_used'] for r in results)

        return BulkAnalysisResponse(
            analyses=analyses,
            total_tokens_used=total_tokens
        )
    except ValueError as e:
        # Position not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk analysis: {str(e)}"
        )


@router.post("/forecasts/bulk", response_model=BulkForecastResponse)
async def get_bulk_forecasts(
    request: BulkForecastRequest,
    force_refresh: bool = Query(False, description="Force new forecast generation"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Generate forecasts for multiple positions in parallel.

    Maximum 5 positions per request to manage token consumption.
    Each forecast takes ~2000-3000 tokens.

    **Performance**:
    - Fresh forecasts: ~30-60 seconds (parallel execution)
    - Cached forecasts: <500ms

    **Request body**:
    ```json
    {
        "symbols": ["BTC", "ETH", "AAPL"]
    }
    ```

    **Response includes**:
    - Individual forecasts for each symbol with Q1/Q2 scenarios
    - Total tokens consumed across all forecasts
    """
    try:
        # Generate all forecasts in parallel
        results = await asyncio.gather(*[
            analysis_service.generate_forecast(symbol, force_refresh)
            for symbol in request.symbols
        ])

        # Build response
        forecasts = {
            symbol: ForecastResponse(**result)
            for symbol, result in zip(request.symbols, results)
        }

        total_tokens = sum(r['tokens_used'] for r in results)

        return BulkForecastResponse(
            forecasts=forecasts,
            total_tokens_used=total_tokens
        )
    except ValueError as e:
        # Position not found or forecast generation failed
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk forecasts: {str(e)}"
        )
