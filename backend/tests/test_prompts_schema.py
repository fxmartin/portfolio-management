"""
Tests for Epic 8 Prompt Management Schema (F8.1-001)

Tests database schema, models, and seed data functionality for:
- Prompt model
- PromptVersion model
- AnalysisResult model
- Seed data script
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from models import Prompt, PromptVersion, AnalysisResult, Base
from seed_prompts import seed_default_prompts_async, DEFAULT_PROMPTS


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
    """Create a test database session"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with TestSessionLocal() as session:
        yield session

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestPromptModel:
    """Test Prompt model creation and constraints"""

    @pytest.mark.asyncio
    async def test_create_prompt(self, db_session):
        """Test creating a basic prompt"""
        prompt = Prompt(
            name="test_prompt",
            category="global",
            prompt_text="Test prompt text with {variable}",
            template_variables={"variable": "string"},
            is_active=1,
            version=1
        )
        db_session.add(prompt)
        await db_session.commit()

        assert prompt.id is not None
        assert prompt.name == "test_prompt"
        assert prompt.category == "global"
        assert prompt.is_active == 1
        assert prompt.version == 1
        assert prompt.created_at is not None
        assert prompt.updated_at is not None

    @pytest.mark.asyncio
    async def test_prompt_unique_name_constraint(self, db_session):
        """Test that prompt names must be unique"""
        prompt1 = Prompt(name="duplicate", category="global", prompt_text="Text 1")
        db_session.add(prompt1)
        await db_session.commit()

        prompt2 = Prompt(name="duplicate", category="position", prompt_text="Text 2")
        db_session.add(prompt2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_prompt_template_variables_json(self, db_session):
        """Test storing template variables as JSON"""
        variables = {
            "portfolio_value": "decimal",
            "position_count": "integer",
            "symbols": "array"
        }
        prompt = Prompt(
            name="json_test",
            category="global",
            prompt_text="Test",
            template_variables=variables
        )
        db_session.add(prompt)
        await db_session.commit()

        result = await db_session.execute(select(Prompt).filter_by(name="json_test"))
        retrieved = result.scalar_one()
        assert retrieved.template_variables == variables
        assert retrieved.template_variables["portfolio_value"] == "decimal"

    @pytest.mark.asyncio
    async def test_prompt_default_values(self, db_session):
        """Test default values for optional fields"""
        prompt = Prompt(
            name="defaults_test",
            category="position",
            prompt_text="Test text"
        )
        db_session.add(prompt)
        await db_session.commit()

        assert prompt.is_active == 1  # Default true
        assert prompt.version == 1  # Default 1
        assert prompt.template_variables is None  # Can be null
        assert prompt.created_at is not None
        assert prompt.updated_at is not None

    @pytest.mark.asyncio
    async def test_prompt_repr(self, db_session):
        """Test string representation"""
        prompt = Prompt(name="repr_test", category="global", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        repr_str = repr(prompt)
        assert "repr_test" in repr_str
        assert "v1" in repr_str
        assert "active=True" in repr_str


class TestPromptVersionModel:
    """Test PromptVersion model and version tracking"""

    @pytest.mark.asyncio
    async def test_create_prompt_version(self, db_session):
        """Test creating a prompt version record"""
        # Create parent prompt
        prompt = Prompt(name="versioned", category="global", prompt_text="Original text")
        db_session.add(prompt)
        await db_session.commit()

        # Create version record
        version = PromptVersion(
            prompt_id=prompt.id,
            version=1,
            prompt_text="Original text",
            changed_by="system",
            change_reason="Initial version"
        )
        db_session.add(version)
        await db_session.commit()

        assert version.id is not None
        assert version.prompt_id == prompt.id
        assert version.version == 1
        assert version.changed_by == "system"
        assert version.changed_at is not None

    @pytest.mark.asyncio
    async def test_prompt_version_relationship(self, db_session):
        """Test relationship between Prompt and PromptVersion"""
        prompt = Prompt(name="related", category="position", prompt_text="V1")
        db_session.add(prompt)
        await db_session.commit()

        # Add multiple versions
        for v in range(1, 4):
            version = PromptVersion(
                prompt_id=prompt.id,
                version=v,
                prompt_text=f"Version {v}",
                changed_by="test_user"
            )
            db_session.add(version)
        await db_session.commit()

        # Test relationship - need to refresh to get relationships
        await db_session.refresh(prompt, ['versions'])
        assert len(prompt.versions) == 3
        assert prompt.versions[0].version == 1
        assert prompt.versions[2].prompt_text == "Version 3"


class TestAnalysisResultModel:
    """Test AnalysisResult model for storing AI responses"""

    @pytest.mark.asyncio
    async def test_create_analysis_result(self, db_session):
        """Test creating an analysis result"""
        prompt = Prompt(name="analysis_test", category="global", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        result = AnalysisResult(
            analysis_type="global",
            symbol=None,
            prompt_id=prompt.id,
            prompt_version=1,
            raw_response="AI generated analysis text",
            tokens_used=1500,
            generation_time_ms=8500
        )
        db_session.add(result)
        await db_session.commit()

        assert result.id is not None
        assert result.analysis_type == "global"
        assert result.symbol is None
        assert result.tokens_used == 1500
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_analysis_result_with_symbol(self, db_session):
        """Test analysis result for specific position"""
        prompt = Prompt(name="position_test", category="position", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        result = AnalysisResult(
            analysis_type="position",
            symbol="AAPL",
            prompt_id=prompt.id,
            prompt_version=1,
            raw_response="Apple analysis",
            tokens_used=800,
            generation_time_ms=4200
        )
        db_session.add(result)
        await db_session.commit()

        query = await db_session.execute(select(AnalysisResult).filter_by(symbol="AAPL"))
        retrieved = query.scalar_one()
        assert retrieved.symbol == "AAPL"
        assert retrieved.analysis_type == "position"

    @pytest.mark.asyncio
    async def test_analysis_result_parsed_data_json(self, db_session):
        """Test storing structured forecast data as JSON"""
        prompt = Prompt(name="forecast_test", category="forecast", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        forecast_data = {
            "q1_forecast": {
                "pessimistic": {"price": 100, "confidence": 70},
                "realistic": {"price": 120, "confidence": 65},
                "optimistic": {"price": 150, "confidence": 45}
            },
            "overall_outlook": "Positive trend expected"
        }

        result = AnalysisResult(
            analysis_type="forecast",
            symbol="BTC-USD",
            prompt_id=prompt.id,
            prompt_version=1,
            raw_response="Forecast JSON",
            parsed_data=forecast_data,
            tokens_used=2000,
            generation_time_ms=12000
        )
        db_session.add(result)
        await db_session.commit()

        query = await db_session.execute(select(AnalysisResult).filter_by(symbol="BTC-USD"))
        retrieved = query.scalar_one()
        assert retrieved.parsed_data["q1_forecast"]["realistic"]["price"] == 120
        assert retrieved.parsed_data["overall_outlook"] == "Positive trend expected"

    @pytest.mark.asyncio
    async def test_analysis_result_expires_at(self, db_session):
        """Test expiration timestamp for cache cleanup"""
        prompt = Prompt(name="expire_test", category="global", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        expires_at = datetime.utcnow() + timedelta(hours=1)
        result = AnalysisResult(
            analysis_type="global",
            prompt_id=prompt.id,
            prompt_version=1,
            raw_response="Cached analysis",
            tokens_used=1200,
            generation_time_ms=7000,
            expires_at=expires_at
        )
        db_session.add(result)
        await db_session.commit()

        query = await db_session.execute(select(AnalysisResult).filter_by(id=result.id))
        retrieved = query.scalar_one()
        assert retrieved.expires_at is not None
        assert (retrieved.expires_at - expires_at).total_seconds() < 1  # Within 1 second

    @pytest.mark.asyncio
    async def test_analysis_result_relationship(self, db_session):
        """Test relationship between AnalysisResult and Prompt"""
        prompt = Prompt(name="rel_test", category="position", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        # Create multiple analyses with same prompt
        for i in range(3):
            result = AnalysisResult(
                analysis_type="position",
                symbol=f"SYM{i}",
                prompt_id=prompt.id,
                prompt_version=1,
                raw_response=f"Analysis {i}",
                tokens_used=800
            )
            db_session.add(result)
        await db_session.commit()

        await db_session.refresh(prompt, ['analysis_results'])
        assert len(prompt.analysis_results) == 3


class TestSeedPrompts:
    """Test seed data functionality"""

    @pytest.mark.asyncio
    async def test_seed_default_prompts_creates_all(self, db_session):
        """Test seeding creates all 4 default prompts"""
        result = await seed_default_prompts_async(db_session)

        assert result["created"] == 4
        assert result["skipped"] == 0
        assert result["updated"] == 0
        assert result["total"] == 4

        # Verify all prompts exist
        query = await db_session.execute(select(Prompt))
        prompts = query.scalars().all()
        assert len(prompts) == 4

        prompt_names = [p.name for p in prompts]
        assert "portfolio_rebalancing" in prompt_names
        assert "global_market_analysis" in prompt_names
        assert "position_analysis" in prompt_names
        assert "forecast_two_quarters" in prompt_names

    @pytest.mark.asyncio
    async def test_seed_prompts_content_correct(self, db_session):
        """Test seed prompts have correct content"""
        await seed_default_prompts_async(db_session)

        query = await db_session.execute(select(Prompt).filter_by(name="global_market_analysis"))
        global_prompt = query.scalar_one()
        assert global_prompt is not None
        assert global_prompt.category == "global"
        assert "{portfolio_value}" in global_prompt.prompt_text
        assert "{asset_allocation}" in global_prompt.prompt_text
        assert global_prompt.template_variables["portfolio_value"] == "decimal"

        query = await db_session.execute(select(Prompt).filter_by(name="position_analysis"))
        position_prompt = query.scalar_one()
        assert position_prompt.category == "position"
        assert "{symbol}" in position_prompt.prompt_text
        assert "HOLD, BUY_MORE, REDUCE, or SELL" in position_prompt.prompt_text

        query = await db_session.execute(select(Prompt).filter_by(name="forecast_two_quarters"))
        forecast_prompt = query.scalar_one()
        assert forecast_prompt.category == "forecast"
        assert "Pessimistic Scenario" in forecast_prompt.prompt_text
        assert "q1_forecast" in forecast_prompt.prompt_text

    @pytest.mark.asyncio
    async def test_seed_prompts_idempotent(self, db_session):
        """Test seed script is idempotent (can run multiple times)"""
        # First run
        result1 = await seed_default_prompts_async(db_session)
        assert result1["created"] == 4

        # Second run
        result2 = await seed_default_prompts_async(db_session)
        assert result2["created"] == 0
        assert result2["skipped"] == 4

        # Should still have exactly 4 prompts
        query = await db_session.execute(select(Prompt))
        prompts = query.scalars().all()
        assert len(prompts) == 4

    @pytest.mark.asyncio
    async def test_seed_prompts_updates_changed_text(self, db_session):
        """Test seed updates prompts when text changes"""
        # Create initial prompts
        await seed_default_prompts_async(db_session)

        # Manually modify a prompt
        query = await db_session.execute(select(Prompt).filter_by(name="global_market_analysis"))
        prompt = query.scalar_one()
        original_version = prompt.version
        prompt.prompt_text = "Modified text"
        await db_session.commit()

        # Re-seed (this will restore original text)
        result = await seed_default_prompts_async(db_session)
        assert result["updated"] == 1

        # Verify text was restored and version incremented
        query = await db_session.execute(select(Prompt).filter_by(name="global_market_analysis"))
        updated_prompt = query.scalar_one()
        assert "Modified text" not in updated_prompt.prompt_text
        assert updated_prompt.version == original_version + 1


class TestSchemaIndexes:
    """Test database indexes exist and work"""

    @pytest.mark.asyncio
    async def test_analysis_type_symbol_index(self, db_session):
        """Test composite index on analysis_results"""
        prompt = Prompt(name="index_test", category="position", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        # Create multiple analysis results
        for symbol in ["AAPL", "GOOGL", "MSFT"]:
            result = AnalysisResult(
                analysis_type="position",
                symbol=symbol,
                prompt_id=prompt.id,
                prompt_version=1,
                raw_response=f"Analysis for {symbol}",
                tokens_used=800
            )
            db_session.add(result)
        await db_session.commit()

        # Query using indexed columns
        query = await db_session.execute(
            select(AnalysisResult).filter(
                AnalysisResult.analysis_type == "position",
                AnalysisResult.symbol == "AAPL"
            )
        )
        results = query.scalars().all()

        assert len(results) == 1
        assert results[0].symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_analysis_created_at_index(self, db_session):
        """Test created_at index for time-based queries"""
        prompt = Prompt(name="time_test", category="global", prompt_text="Test")
        db_session.add(prompt)
        await db_session.commit()

        # Create results at different times
        for i in range(3):
            result = AnalysisResult(
                analysis_type="global",
                prompt_id=prompt.id,
                prompt_version=1,
                raw_response=f"Analysis {i}",
                tokens_used=1000
            )
            db_session.add(result)
            await db_session.commit()  # Ensure different timestamps

        # Query recent results (DESC order)
        query = await db_session.execute(
            select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(2)
        )
        recent = query.scalars().all()

        assert len(recent) == 2
        assert recent[0].created_at >= recent[1].created_at
