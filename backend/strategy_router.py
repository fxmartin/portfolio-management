# ABOUTME: FastAPI router for Investment Strategy API endpoints (Epic 8 - F8.8-001)
# ABOUTME: RESTful API for CRUD operations on user investment strategies

"""
Investment Strategy API Router

Endpoints:
- GET /api/strategy/ - Get current strategy (404 if none)
- POST /api/strategy/ - Create strategy (409 if exists)
- PUT /api/strategy/ - Update strategy (404 if none, auto-increments version)
- DELETE /api/strategy/ - Delete strategy (204 response)
- GET /api/strategy/recommendations - Get AI-powered recommendations (F8.8-002)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional

from database import get_async_db
from models import InvestmentStrategy
from strategy_schemas import (
    InvestmentStrategyCreate,
    InvestmentStrategyUpdate,
    InvestmentStrategyResponse,
    StrategyDrivenRecommendationResponse
)


router = APIRouter(prefix="/api/strategy", tags=["strategy"])

# Default user_id (single-user system for MVP)
DEFAULT_USER_ID = 1


@router.get("/", response_model=InvestmentStrategyResponse)
async def get_strategy(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current investment strategy.

    Returns the user's current investment strategy with all fields.
    Returns 404 if no strategy exists yet.

    **Response**: InvestmentStrategyResponse with strategy details
    """
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment strategy not found. Create one first using POST /api/strategy/"
        )

    return strategy


@router.post("/", response_model=InvestmentStrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: InvestmentStrategyCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new investment strategy.

    Creates an investment strategy for the user. Only one strategy allowed per user.
    Returns 409 if strategy already exists.

    **Validation**:
    - strategy_text: 50-5000 chars, minimum 20 words
    - target_annual_return: 0-100% (optional)
    - risk_tolerance: LOW/MEDIUM/HIGH/CUSTOM (optional)
    - time_horizon_years: 1-50 (optional)
    - max_positions: 1-100 (optional)
    - profit_taking_threshold: 0-100% (optional)

    **Response**: Created strategy with version=1
    """
    # Check if strategy already exists
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Investment strategy already exists (id={existing.id}). Use PUT to update."
        )

    # Create new strategy
    strategy = InvestmentStrategy(
        user_id=DEFAULT_USER_ID,
        strategy_text=strategy_data.strategy_text,
        target_annual_return=strategy_data.target_annual_return,
        risk_tolerance=strategy_data.risk_tolerance.value if strategy_data.risk_tolerance else None,
        time_horizon_years=strategy_data.time_horizon_years,
        max_positions=strategy_data.max_positions,
        profit_taking_threshold=strategy_data.profit_taking_threshold
    )

    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)

    return strategy


@router.put("/", response_model=InvestmentStrategyResponse)
async def update_strategy(
    update_data: InvestmentStrategyUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update existing investment strategy.

    Updates the user's strategy with provided fields. Version auto-increments
    via database trigger. Returns 404 if no strategy exists.

    **All fields are optional** - only provide fields you want to update.

    **Response**: Updated strategy with incremented version
    """
    # Get existing strategy
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment strategy not found. Create one first using POST /api/strategy/"
        )

    # Update provided fields
    if update_data.strategy_text is not None:
        strategy.strategy_text = update_data.strategy_text
    if update_data.target_annual_return is not None:
        strategy.target_annual_return = update_data.target_annual_return
    if update_data.risk_tolerance is not None:
        strategy.risk_tolerance = update_data.risk_tolerance.value
    if update_data.time_horizon_years is not None:
        strategy.time_horizon_years = update_data.time_horizon_years
    if update_data.max_positions is not None:
        strategy.max_positions = update_data.max_positions
    if update_data.profit_taking_threshold is not None:
        strategy.profit_taking_threshold = update_data.profit_taking_threshold

    # Commit (trigger will auto-increment version and update updated_at)
    await db.commit()
    await db.refresh(strategy)

    return strategy


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete investment strategy.

    Permanently deletes the user's investment strategy.
    Returns 404 if no strategy exists.

    **Response**: 204 No Content on success
    """
    # Check if strategy exists
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment strategy not found"
        )

    # Delete strategy
    await db.execute(
        delete(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
    )
    await db.commit()

    return None  # 204 response has no body


@router.get("/recommendations", response_model=StrategyDrivenRecommendationResponse)
async def get_strategy_recommendations(
    force_refresh: bool = Query(False, description="Bypass cache and generate fresh recommendations"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get AI-powered strategy-driven portfolio recommendations (F8.8-002).

    Analyzes current portfolio against investment strategy and generates
    personalized recommendations including:
    - Profit-taking opportunities based on thresholds
    - Position assessments (aligned/overweight/underweight)
    - New position suggestions to align with strategy
    - Prioritized action plan with transaction data
    - Target return achievability assessment

    **Requirements**:
    - Investment strategy must exist (404 if none)
    - Portfolio must have positions

    **Caching**: Results cached for 12 hours (use force_refresh=true to bypass)

    **Performance**: <20s generation time

    **Response**: Comprehensive recommendations with action plan
    """
    # Import here to avoid circular dependency
    from analysis_service import AnalysisService
    from claude_service import ClaudeService
    from prompt_service import PromptService
    from prompt_renderer import PromptDataCollector
    from portfolio_service import PortfolioService
    from yahoo_finance_service import YahooFinanceService
    from cache_service import CacheService
    from config import get_settings

    # Get strategy
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.user_id == DEFAULT_USER_ID)
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment strategy not found. Create one first using POST /api/strategy/"
        )

    # Initialize services
    settings = get_settings()
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

    # Initialize analysis service
    analysis_service = AnalysisService(
        db,
        claude_service,
        prompt_service,
        data_collector,
        cache_service
    )

    # Get all positions
    positions = await portfolio_service.get_all_positions()

    if not positions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio has no positions. Import transactions first."
        )

    # Generate recommendations
    try:
        recommendations = await analysis_service.generate_strategy_recommendations(
            strategy,
            positions,
            force_refresh=force_refresh
        )
        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )
