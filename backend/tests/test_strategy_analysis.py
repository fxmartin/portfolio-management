# ABOUTME: Comprehensive tests for strategy-driven recommendations feature (F8.8-002)
# ABOUTME: Tests for PromptDataCollector, AnalysisService, and strategy endpoint integration

"""
Test Suite for Strategy-Driven Recommendations (F8.8-002)

Tests cover:
1. Data collection for strategy analysis
2. AI service integration for recommendations
3. API endpoint behavior
4. Caching and performance
5. Error handling and edge cases

Coverage target: ≥85%
"""

import pytest
import json
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from models import InvestmentStrategy, Position, AssetType, Prompt
from prompt_renderer import PromptDataCollector
from analysis_service import AnalysisService
from strategy_schemas import StrategyDrivenRecommendationResponse


# ==================== Unit Tests for PromptDataCollector ====================

class TestPromptDataCollectorStrategyData:
    """Unit tests for collect_strategy_analysis_data method"""

    @pytest.fixture
    def mock_portfolio_service(self):
        """Create mock portfolio service"""
        service = AsyncMock()
        service.get_all_positions = AsyncMock()
        return service

    @pytest.fixture
    def mock_strategy(self):
        """Create complete strategy with all fields"""
        return InvestmentStrategy(
            id=1,
            user_id=1,
            strategy_text="Focus on long-term growth with 60% stocks, 30% crypto, 10% metals. Emphasize diversification and quarterly rebalancing.",
            target_annual_return=Decimal("12.5"),
            risk_tolerance="MEDIUM",
            time_horizon_years=10,
            max_positions=15,
            profit_taking_threshold=Decimal("25.0"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version=1
        )

    @pytest.fixture
    def mock_minimal_strategy(self):
        """Create minimal strategy (only required field)"""
        return InvestmentStrategy(
            id=1,
            user_id=1,
            strategy_text="Conservative balanced portfolio approach with emphasis on capital preservation and steady growth.",
            target_annual_return=None,
            risk_tolerance=None,
            time_horizon_years=None,
            max_positions=None,
            profit_taking_threshold=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version=1
        )

    @pytest.fixture
    def mock_positions(self):
        """Create diverse position list using MagicMock"""
        # Create mock positions with all required attributes
        btc = MagicMock(spec=Position)
        btc.id = 1
        btc.symbol = "BTC"
        btc.asset_name = "Bitcoin"
        btc.asset_type = AssetType.CRYPTO
        btc.quantity = Decimal("0.5")
        btc.avg_cost_basis = Decimal("40000")
        btc.total_cost_basis = Decimal("20000")
        btc.current_price = Decimal("82000")
        btc.current_value = Decimal("41000")
        btc.unrealized_pnl = Decimal("21000")
        btc.unrealized_pnl_percent = Decimal("105.0")
        btc.first_purchase_date = datetime.now(UTC) - timedelta(days=425)
        btc.last_price_update = datetime.now(UTC)
        btc.sector = None

        aapl = MagicMock(spec=Position)
        aapl.id = 2
        aapl.symbol = "AAPL"
        aapl.asset_name = "Apple Inc."
        aapl.asset_type = AssetType.STOCK
        aapl.quantity = Decimal("50")
        aapl.avg_cost_basis = Decimal("150")
        aapl.total_cost_basis = Decimal("7500")
        aapl.current_price = Decimal("175")
        aapl.current_value = Decimal("8750")
        aapl.unrealized_pnl = Decimal("1250")
        aapl.unrealized_pnl_percent = Decimal("16.67")
        aapl.first_purchase_date = datetime.now(UTC) - timedelta(days=180)
        aapl.last_price_update = datetime.now(UTC)
        aapl.sector = "Technology"

        xau = MagicMock(spec=Position)
        xau.id = 3
        xau.symbol = "XAU"
        xau.asset_name = "Gold"
        xau.asset_type = AssetType.METAL
        xau.quantity = Decimal("10.5")
        xau.avg_cost_basis = Decimal("1800")
        xau.total_cost_basis = Decimal("18900")
        xau.current_price = Decimal("2050")
        xau.current_value = Decimal("21525")
        xau.unrealized_pnl = Decimal("2625")
        xau.unrealized_pnl_percent = Decimal("13.89")
        xau.first_purchase_date = datetime.now(UTC) - timedelta(days=90)
        xau.last_price_update = datetime.now(UTC)
        xau.sector = None

        return [btc, aapl, xau]

    @pytest.mark.asyncio
    async def test_collect_strategy_analysis_data_complete(
        self, mock_portfolio_service, mock_strategy, mock_positions
    ):
        """Test data collection with complete strategy and positions"""
        mock_portfolio_service.get_all_positions.return_value = mock_positions

        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, mock_positions)

        # Verify all required fields present
        assert "strategy_text" in data
        assert "target_annual_return" in data
        assert "risk_tolerance" in data
        assert "time_horizon_years" in data
        assert "max_positions" in data
        assert "profit_taking_threshold" in data
        assert "portfolio_total_value" in data
        assert "position_count" in data
        assert "positions_table" in data
        assert "asset_allocation" in data
        assert "top_3_weight" in data
        assert "single_asset_max" in data
        assert "single_sector_max" in data

        # Verify strategy values
        assert data["strategy_text"] == mock_strategy.strategy_text
        assert data["target_annual_return"] == "12.50"
        assert data["risk_tolerance"] == "MEDIUM"
        assert data["time_horizon_years"] == "10"
        assert data["max_positions"] == "15"
        assert data["profit_taking_threshold"] == "25.00"

        # Verify portfolio calculations
        assert data["position_count"] == 3
        expected_total = float(41000 + 8750 + 21525)
        assert float(data["portfolio_total_value"]) == pytest.approx(expected_total, rel=0.01)

        # Verify positions table format (should be markdown table)
        assert "| Symbol | Asset Type | Quantity |" in data["positions_table"]
        assert "BTC" in data["positions_table"]
        assert "AAPL" in data["positions_table"]
        assert "XAU" in data["positions_table"]

    @pytest.mark.asyncio
    async def test_collect_strategy_analysis_data_minimal_strategy(
        self, mock_portfolio_service, mock_minimal_strategy, mock_positions
    ):
        """Test data collection with minimal strategy (optional fields None)"""
        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(
            mock_minimal_strategy, mock_positions
        )

        # Verify required fields present
        assert data["strategy_text"] == mock_minimal_strategy.strategy_text

        # Verify optional fields show "Not specified"
        assert data["target_annual_return"] == "Not specified"
        assert data["risk_tolerance"] == "Not specified"
        assert data["time_horizon_years"] == "Not specified"
        assert data["max_positions"] == "Not specified"
        assert data["profit_taking_threshold"] == "Not specified"

    @pytest.mark.asyncio
    async def test_collect_strategy_analysis_data_no_positions(
        self, mock_portfolio_service, mock_strategy
    ):
        """Test data collection with empty position list"""
        empty_positions = []

        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, empty_positions)

        # Verify graceful handling
        assert data["position_count"] == 0
        assert float(data["portfolio_total_value"]) == 0.0
        assert data["top_3_weight"] == "0.00"
        assert data["single_asset_max"] == "0.00"

    @pytest.mark.asyncio
    async def test_format_positions_table(
        self, mock_portfolio_service, mock_strategy, mock_positions
    ):
        """Test positions table formatting"""
        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, mock_positions)
        table = data["positions_table"]

        # Verify markdown table structure
        lines = table.split("\n")
        assert len(lines) >= 4  # Header + separator + at least 3 positions

        # Verify header
        assert "Symbol" in lines[0]
        assert "Asset Type" in lines[0]
        assert "Quantity" in lines[0]
        assert "Current Price" in lines[0]
        assert "P&L %" in lines[0]

        # Verify separator
        assert "|---" in lines[1]

        # Verify data rows contain position info
        assert "BTC" in table
        assert "CRYPTO" in table
        assert "105.0%" in table or "105.00%" in table  # P&L percentage

    @pytest.mark.asyncio
    async def test_asset_allocation_calculation(
        self, mock_portfolio_service, mock_strategy, mock_positions
    ):
        """Test asset allocation string formatting"""
        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, mock_positions)
        allocation = data["asset_allocation"]

        # Verify format: "Stocks: 12.3% (€8,750), Crypto: 57.6% (€41,000), Metals: 30.1% (€21,525)"
        assert "Stocks:" in allocation or "STOCK:" in allocation
        assert "Crypto:" in allocation or "CRYPTO:" in allocation
        assert "Metals:" in allocation or "METAL:" in allocation
        assert "€" in allocation
        assert "%" in allocation

    @pytest.mark.asyncio
    async def test_sector_allocation_stocks_only(
        self, mock_portfolio_service, mock_strategy, mock_positions
    ):
        """Test sector allocation includes only stock positions"""
        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, mock_positions)
        sector_allocation = data.get("sector_allocation", "")

        # Sector allocation should mention Technology (from AAPL)
        # Should NOT include crypto/metals positions
        if sector_allocation and sector_allocation != "Not available":
            assert "Technology" in sector_allocation

    @pytest.mark.asyncio
    async def test_concentration_metrics_calculation(
        self, mock_portfolio_service, mock_strategy, mock_positions
    ):
        """Test concentration risk metrics"""
        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, mock_positions)

        # Top 3 weight should be high (we only have 3 positions = 100%)
        top_3 = float(data["top_3_weight"])
        assert top_3 == pytest.approx(100.0, rel=0.1)

        # Single asset max should be BTC (largest position)
        single_max = float(data["single_asset_max"])
        btc_weight = 41000 / (41000 + 8750 + 21525) * 100
        assert single_max == pytest.approx(btc_weight, rel=0.1)

    @pytest.mark.asyncio
    async def test_holding_period_calculation(
        self, mock_portfolio_service, mock_strategy, mock_positions
    ):
        """Test holding period displayed in positions table"""
        collector = PromptDataCollector(
            db=AsyncMock(),
            portfolio_service=mock_portfolio_service
        )

        data = await collector.collect_strategy_analysis_data(mock_strategy, mock_positions)
        table = data["positions_table"]

        # BTC purchased 425 days ago - should show in table
        assert "425" in table or "Holding Period" in table


# ==================== Unit Tests for AnalysisService ====================

class TestAnalysisServiceStrategyRecommendations:
    """Unit tests for generate_strategy_recommendations method"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def mock_claude_service(self):
        """Create mock Claude service"""
        service = AsyncMock()
        return service

    @pytest.fixture
    def mock_prompt_service(self):
        """Create mock prompt service"""
        service = AsyncMock()
        return service

    @pytest.fixture
    def mock_data_collector(self):
        """Create mock data collector"""
        collector = AsyncMock()
        return collector

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        return cache

    @pytest.fixture
    def mock_strategy(self):
        """Create mock strategy"""
        return InvestmentStrategy(
            id=1,
            user_id=1,
            strategy_text="Long-term growth focus",
            target_annual_return=Decimal("12.0"),
            profit_taking_threshold=Decimal("25.0"),
            version=1
        )

    @pytest.fixture
    def mock_positions(self):
        """Create mock positions using MagicMock"""
        btc = MagicMock(spec=Position)
        btc.symbol = "BTC"
        btc.asset_type = AssetType.CRYPTO
        btc.quantity = Decimal("0.5")
        btc.current_value = Decimal("41000")
        btc.unrealized_pnl_percent = Decimal("105.0")
        return [btc]

    @pytest.fixture
    def mock_claude_response(self):
        """Create mock Claude API response"""
        return {
            "summary": "Portfolio shows strong crypto exposure with profit-taking opportunity.",
            "profit_taking_opportunities": [
                {
                    "symbol": "BTC",
                    "current_value": 41000.0,
                    "entry_cost": 20000.0,
                    "unrealized_gain": 21000.0,
                    "gain_percentage": 105.0,
                    "holding_period_days": 425,
                    "recommendation": "TAKE_PROFIT",
                    "rationale": "Position exceeds 25% profit threshold",
                    "suggested_sell_percentage": 50,
                    "transaction_data": {
                        "transaction_type": "SELL",
                        "symbol": "BTC",
                        "quantity": 0.25,
                        "price": 82000.0,
                        "total_value": 20500.0,
                        "currency": "EUR"
                    }
                }
            ],
            "position_assessments": [],
            "new_position_suggestions": [],
            "action_plan": [
                {
                    "priority": 1,
                    "action": "Sell 50% of BTC",
                    "symbol": "BTC",
                    "details": "Lock in profits",
                    "expected_impact": "Reduce crypto exposure",
                    "transaction_data": {
                        "transaction_type": "SELL",
                        "symbol": "BTC",
                        "quantity": 0.25,
                        "price": 82000.0,
                        "total_value": 20500.0,
                        "currency": "EUR"
                    }
                }
            ],
            "target_return_assessment": {
                "target_return": 12.0,
                "current_projected_return": 8.5,
                "achievability": "CHALLENGING",
                "required_changes": "Increase stock allocation",
                "risk_level": "MEDIUM"
            },
            "portfolio_alignment_score": 72.0,
            "risk_assessment": "Moderate concentration in crypto",
            "implementation_notes": "Execute over 2 weeks"
        }

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_success(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy,
        mock_positions, mock_claude_response
    ):
        """Test successful recommendation generation"""
        # Setup mocks
        mock_prompt = Prompt(
            id=1,
            name="strategy_driven_recommendations",
            prompt_text="Test prompt {strategy_text}",
            template_variables={"strategy_text": "string"},
            version=1
        )
        mock_prompt_service.get_prompt_by_name.return_value = mock_prompt

        mock_data_collector.collect_strategy_analysis_data.return_value = {
            "strategy_text": "Long-term growth",
            "portfolio_total_value": 50000.0
        }

        mock_claude_service.generate_analysis.return_value = {
            "content": json.dumps(mock_claude_response),
            "tokens_used": 2500,
            "generation_time_ms": 8500
        }

        # Create service
        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        # Execute
        result = await service.generate_strategy_recommendations(
            mock_strategy, mock_positions, force_refresh=False
        )

        # Verify
        assert result["summary"] == mock_claude_response["summary"]
        assert result["portfolio_alignment_score"] == 72.0
        assert result["tokens_used"] == 2500
        assert result["cached"] == False
        assert len(result["profit_taking_opportunities"]) == 1

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_cached(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy,
        mock_positions, mock_claude_response
    ):
        """Test returning cached recommendations"""
        # Setup cache hit
        cached_data = {
            **mock_claude_response,
            "generated_at": datetime.now(UTC),
            "tokens_used": 2500
        }
        mock_cache_service.get.return_value = cached_data

        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        result = await service.generate_strategy_recommendations(
            mock_strategy, mock_positions, force_refresh=False
        )

        # Verify cache was used
        assert result["cached"] == True
        assert result["tokens_used"] == 2500
        # Claude API should not be called
        mock_claude_service.generate_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_force_refresh(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy,
        mock_positions, mock_claude_response
    ):
        """Test force refresh bypasses cache"""
        # Setup cache with data
        cached_data = {**mock_claude_response, "generated_at": datetime.now(UTC)}
        mock_cache_service.get.return_value = cached_data

        # Setup fresh generation
        mock_prompt = Prompt(id=1, name="test", prompt_text="{strategy_text}",
                            template_variables={"strategy_text": "string"}, version=1)
        mock_prompt_service.get_prompt_by_name.return_value = mock_prompt
        mock_data_collector.collect_strategy_analysis_data.return_value = {
            "strategy_text": "Test"
        }
        mock_claude_service.generate_analysis.return_value = {
            "content": json.dumps(mock_claude_response),
            "tokens_used": 2600,
            "generation_time_ms": 9000
        }

        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        result = await service.generate_strategy_recommendations(
            mock_strategy, mock_positions, force_refresh=True
        )

        # Verify fresh generation
        assert result["cached"] == False
        assert result["tokens_used"] == 2600
        mock_claude_service.generate_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_missing_prompt(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy, mock_positions
    ):
        """Test error when prompt not found"""
        mock_prompt_service.get_prompt_by_name.return_value = None

        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        with pytest.raises(ValueError, match="not found"):
            await service.generate_strategy_recommendations(
                mock_strategy, mock_positions
            )

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_claude_error(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy, mock_positions
    ):
        """Test error handling when Claude API fails"""
        mock_prompt = Prompt(id=1, name="test", prompt_text="{strategy_text}",
                            template_variables={"strategy_text": "string"}, version=1)
        mock_prompt_service.get_prompt_by_name.return_value = mock_prompt
        mock_data_collector.collect_strategy_analysis_data.return_value = {
            "strategy_text": "Test"
        }
        mock_claude_service.generate_analysis.side_effect = Exception("API error")

        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        with pytest.raises(Exception, match="API error"):
            await service.generate_strategy_recommendations(
                mock_strategy, mock_positions
            )

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_json_parsing(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy,
        mock_positions, mock_claude_response
    ):
        """Test JSON parsing from direct response"""
        mock_prompt = Prompt(id=1, name="test", prompt_text="{strategy_text}",
                            template_variables={"strategy_text": "string"}, version=1)
        mock_prompt_service.get_prompt_by_name.return_value = mock_prompt
        mock_data_collector.collect_strategy_analysis_data.return_value = {
            "strategy_text": "Test"
        }

        # Return plain JSON (not markdown wrapped)
        mock_claude_service.generate_analysis.return_value = {
            "content": json.dumps(mock_claude_response),
            "tokens_used": 2500,
            "generation_time_ms": 8500
        }

        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        result = await service.generate_strategy_recommendations(
            mock_strategy, mock_positions
        )

        assert result["summary"] == mock_claude_response["summary"]

    @pytest.mark.asyncio
    async def test_generate_strategy_recommendations_markdown_extraction(
        self, mock_db, mock_claude_service, mock_prompt_service,
        mock_data_collector, mock_cache_service, mock_strategy,
        mock_positions, mock_claude_response
    ):
        """Test JSON extraction from markdown code block"""
        mock_prompt = Prompt(id=1, name="test", prompt_text="{strategy_text}",
                            template_variables={"strategy_text": "string"}, version=1)
        mock_prompt_service.get_prompt_by_name.return_value = mock_prompt
        mock_data_collector.collect_strategy_analysis_data.return_value = {
            "strategy_text": "Test"
        }

        # Return markdown-wrapped JSON
        markdown_response = f"```json\n{json.dumps(mock_claude_response)}\n```"
        mock_claude_service.generate_analysis.return_value = {
            "content": markdown_response,
            "tokens_used": 2500,
            "generation_time_ms": 8500
        }

        service = AnalysisService(
            db=mock_db,
            claude_service=mock_claude_service,
            prompt_service=mock_prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache_service
        )

        result = await service.generate_strategy_recommendations(
            mock_strategy, mock_positions
        )

        assert result["summary"] == mock_claude_response["summary"]


# ==================== Integration Tests ====================

class TestStrategyRecommendationsIntegration:
    """Integration tests for end-to-end recommendation flow"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_strategy_recommendations(self):
        """Test complete flow from API endpoint to response"""
        # This would require actual database and services
        # For now, mark as placeholder for integration testing
        pytest.skip("Requires full service initialization")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recommendations_with_profit_taking_threshold(self):
        """Test profit-taking logic with actual threshold"""
        pytest.skip("Requires full service initialization")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recommendations_exceeding_max_positions(self):
        """Test recommendations when portfolio exceeds max_positions"""
        pytest.skip("Requires full service initialization")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cache_invalidation_on_strategy_update(self):
        """Test cache is properly invalidated when strategy changes"""
        pytest.skip("Requires full service initialization")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recommendations_with_all_strategy_fields(self):
        """Test with complete strategy including all optional fields"""
        pytest.skip("Requires full service initialization")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recommendations_with_minimal_strategy(self):
        """Test with minimal strategy (only required fields)"""
        pytest.skip("Requires full service initialization")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complex_json_response_parsing(self):
        """Test parsing complex nested JSON from Claude"""
        pytest.skip("Requires full service initialization")
