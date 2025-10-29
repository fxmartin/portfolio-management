# ABOUTME: Integration tests for PromptRenderer with real database prompts
# ABOUTME: Tests end-to-end rendering flow with seeded prompts and portfolio data

import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from models import Prompt, Base
from prompt_renderer import PromptRenderer, PromptDataCollector
from seed_prompts import seed_default_prompts_async


# Use SQLite for testing (in-memory database)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with TestSessionLocal() as session:
        # Seed default prompts
        await seed_default_prompts_async(session)
        yield session

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def renderer():
    """Create a PromptRenderer instance."""
    return PromptRenderer()


class TestRealPromptRendering:
    """Integration tests with real prompts from database."""

    @pytest.mark.asyncio
    async def test_render_global_analysis_prompt(self, db_session: AsyncSession, renderer: PromptRenderer):
        """Test rendering the global_market_analysis prompt with real data."""
        # Fetch the global analysis prompt from database
        result = await db_session.execute(select(Prompt).filter_by(name="global_market_analysis"))
        prompt = result.scalar_one_or_none()
        assert prompt is not None, "global_market_analysis prompt not found in database"

        # Prepare realistic portfolio data
        data = {
            "portfolio_value": Decimal("50000.00"),
            "asset_allocation": {
                "stocks": 30000,
                "crypto": 15000,
                "metals": 5000
            },
            "position_count": 15,
            "top_holdings": ["AAPL (€10000.00)", "BTC (€7000.00)", "TSLA (€6000.00)"]
        }

        # Render the prompt
        result = renderer.render(prompt.prompt_text, prompt.template_variables, data)

        # Verify the rendered prompt contains expected data
        assert "50000.00" in result
        assert "15" in result
        assert "AAPL" in result or "BTC" in result or "TSLA" in result
        assert "stocks: 30000" in result
        assert "crypto: 15000" in result

        # Verify prompt structure is intact
        assert "Portfolio Context" in result or "Total Value" in result
        assert len(result) > 200  # Should be a substantial prompt

    @pytest.mark.asyncio
    async def test_render_position_analysis_prompt(self, db_session: AsyncSession, renderer: PromptRenderer):
        """Test rendering the position_analysis prompt with real data."""
        result = await db_session.execute(select(Prompt).filter_by(name="position_analysis"))
        prompt = result.scalar_one_or_none()
        assert prompt is not None, "position_analysis prompt not found in database"

        # Prepare position data
        data = {
            "symbol": "BTC",
            "name": "Bitcoin",
            "quantity": Decimal("1.5"),
            "current_price": Decimal("50000.00"),
            "cost_basis": Decimal("60000.00"),
            "unrealized_pnl": Decimal("-10000.00"),
            "pnl_percentage": Decimal("-16.67"),
            "position_percentage": Decimal("30.00"),
            "day_change": Decimal("2.50"),
            "sector": "Cryptocurrency",
            "asset_type": "CRYPTO"
        }

        result = renderer.render(prompt.prompt_text, prompt.template_variables, data)

        # Verify position details are included
        assert "BTC" in result
        assert "1.50" in result  # Quantity formatted as decimal
        assert "50000.00" in result  # Current price
        assert "-10000.00" in result  # Unrealized P&L
        assert "-16.67" in result  # P&L percentage

        # Verify prompt asks for analysis
        assert "Position" in result or "Asset" in result
        assert len(result) > 150

    @pytest.mark.asyncio
    async def test_render_forecast_prompt(self, db_session: AsyncSession, renderer: PromptRenderer):
        """Test rendering the forecast_two_quarters prompt with real data."""
        result = await db_session.execute(select(Prompt).filter_by(name="forecast_two_quarters"))
        prompt = result.scalar_one_or_none()
        assert prompt is not None, "forecast_two_quarters prompt not found in database"

        # Prepare forecast data
        data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "current_price": Decimal("180.00"),
            "week_52_low": Decimal("140.00"),
            "week_52_high": Decimal("200.00"),
            "performance_30d": Decimal("5.50"),
            "performance_90d": Decimal("12.30"),
            "sector": "Technology",
            "asset_type": "STOCK",
            "market_context": "Strong earnings beat, new product launches expected Q2"
        }

        result = renderer.render(prompt.prompt_text, prompt.template_variables, data)

        # Verify forecast parameters
        assert "AAPL" in result
        assert "180.00" in result  # Current price
        assert "140.00" in result  # 52-week low
        assert "200.00" in result  # 52-week high
        assert "5.50" in result  # 30-day performance
        assert "Strong earnings beat" in result  # Market context

        # Verify prompt structure for forecast
        assert "Pessimistic" in result or "Realistic" in result or "Optimistic" in result
        assert "Q1" in result or "Q2" in result
        assert len(result) > 300  # Forecast prompts should be detailed

    @pytest.mark.asyncio
    async def test_all_prompts_have_valid_template_variables(self, db_session: AsyncSession):
        """Test that all seeded prompts have valid template variable schemas."""
        result = await db_session.execute(select(Prompt).filter_by(is_active=True))
        prompts = result.scalars().all()
        assert len(prompts) == 3, "Should have 3 default prompts"

        valid_types = ['string', 'integer', 'decimal', 'boolean', 'array', 'object']

        for prompt in prompts:
            # Verify template_variables is a dict
            assert isinstance(prompt.template_variables, dict)

            # Verify all types are valid
            for var_name, var_type in prompt.template_variables.items():
                assert var_type in valid_types, \
                    f"Invalid type '{var_type}' in prompt '{prompt.name}' for variable '{var_name}'"

    @pytest.mark.asyncio
    async def test_prompt_variables_match_placeholders(self, db_session: AsyncSession):
        """Test that template variables match placeholders in prompt text."""
        import re

        result = await db_session.execute(select(Prompt).filter_by(is_active=True))
        prompts = result.scalars().all()

        for prompt in prompts:
            # Extract {variable} placeholders from prompt text
            placeholders = set(re.findall(r'\{(\w+)\}', prompt.prompt_text))

            # Get declared template variables
            declared_vars = set(prompt.template_variables.keys())

            # All placeholders should have corresponding template variables
            # (Note: Some template variables might not be used, which is okay)
            undeclared = placeholders - declared_vars
            assert len(undeclared) == 0, \
                f"Prompt '{prompt.name}' has undeclared placeholders: {undeclared}"


class TestPromptDataCollectorIntegration:
    """Integration tests for PromptDataCollector with portfolio service."""

    @pytest.mark.skip(reason="Requires full portfolio service setup with test data")
    @pytest.mark.asyncio
    async def test_collect_and_render_global_data(self, db_session: AsyncSession):
        """Test collecting real portfolio data and rendering global prompt."""
        # This test would require:
        # 1. Portfolio service with test transactions
        # 2. Positions calculated
        # 3. Data collection
        # 4. Prompt rendering
        #
        # Skip for now - would be part of full system integration tests
        pass

    @pytest.mark.skip(reason="Requires full portfolio service setup with test data")
    @pytest.mark.asyncio
    async def test_collect_and_render_position_data(self, db_session: AsyncSession):
        """Test collecting real position data and rendering position prompt."""
        # Similar to above - requires full test data setup
        pass


class TestPromptPerformance:
    """Performance tests for prompt rendering."""

    @pytest.mark.asyncio
    async def test_render_performance_under_50ms(self, db_session: AsyncSession, renderer: PromptRenderer):
        """Test that prompt rendering completes in <50ms as required."""
        import time

        result = await db_session.execute(select(Prompt).filter_by(name="position_analysis"))
        prompt = result.scalar_one_or_none()
        data = {
            "symbol": "BTC",
            "name": "Bitcoin",
            "quantity": Decimal("1.0"),
            "current_price": Decimal("50000.00"),
            "cost_basis": Decimal("45000.00"),
            "unrealized_pnl": Decimal("5000.00"),
            "pnl_percentage": Decimal("11.11"),
            "position_percentage": Decimal("25.00"),
            "day_change": Decimal("1.50"),
            "sector": "Crypto",
            "asset_type": "CRYPTO"
        }

        # Measure rendering time
        start = time.perf_counter()
        result = renderer.render(prompt.prompt_text, prompt.template_variables, data)
        duration_ms = (time.perf_counter() - start) * 1000

        assert len(result) > 0
        assert duration_ms < 50, f"Rendering took {duration_ms:.2f}ms (requirement: <50ms)"

    @pytest.mark.asyncio
    async def test_render_multiple_prompts_performance(self, db_session: AsyncSession, renderer: PromptRenderer):
        """Test rendering multiple prompts sequentially."""
        import time

        result = await db_session.execute(select(Prompt).filter_by(is_active=True))
        prompts = result.scalars().all()
        assert len(prompts) > 0

        start = time.perf_counter()

        for _ in range(10):  # Render each prompt 10 times
            for prompt in prompts:
                # Use dummy data that matches template variables
                data = {var: "test_value" if var_type == "string" else 0
                       for var, var_type in prompt.template_variables.items()}
                try:
                    renderer.render(prompt.prompt_text, prompt.template_variables, data)
                except (ValueError, TypeError):
                    # Some data might not be valid for certain types, skip
                    pass

        duration_ms = (time.perf_counter() - start) * 1000
        avg_render_time = duration_ms / (10 * len(prompts))

        # Average render time should be well under 50ms
        assert avg_render_time < 25, \
            f"Average render time {avg_render_time:.2f}ms exceeds 25ms threshold"
