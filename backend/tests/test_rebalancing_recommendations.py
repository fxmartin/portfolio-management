# ABOUTME: Unit and integration tests for AI-powered rebalancing recommendations (F8.7-002)
# ABOUTME: Tests prompt rendering, JSON parsing, Claude integration, caching, and end-to-end workflow

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta, UTC
from decimal import Decimal
import json

from sqlalchemy.ext.asyncio import AsyncSession

from analysis_service import AnalysisService
from claude_service import ClaudeService
from prompt_service import PromptService
from rebalancing_service import RebalancingService
from rebalancing_schemas import (
    RebalancingAnalysis,
    AssetTypeAllocation,
    AllocationStatus,
    RebalancingRecommendationResponse,
    RebalancingRecommendation,
    RebalancingAction,
    ExpectedOutcome,
    TransactionData
)
from models import Prompt, AssetType, Position


class TestRebalancingPromptRendering:
    """Test prompt template rendering for rebalancing recommendations."""

    @pytest.mark.asyncio
    async def test_render_rebalancing_prompt_success(self, test_session):
        """Test successful rendering of rebalancing prompt template."""
        from prompt_renderer import PromptRenderer

        # Create rebalancing prompt
        prompt_text = """# Portfolio Rebalancing

Total Value: €{portfolio_total_value}
Target Model: {target_model}

## Allocation
{allocation_table}

## Positions
{positions_table}

## Market Context
{market_indices}"""

        template_vars = {
            "portfolio_total_value": {"type": "decimal"},
            "target_model": {"type": "string"},
            "allocation_table": {"type": "string"},
            "positions_table": {"type": "string"},
            "market_indices": {"type": "string"}
        }

        data = {
            "portfolio_total_value": Decimal("50000.00"),
            "target_model": "moderate",
            "allocation_table": "| Stocks | 55% | 60% |",
            "positions_table": "| BTC | 0.5 |",
            "market_indices": "S&P 500: 5000"
        }

        renderer = PromptRenderer()
        result = renderer.render(prompt_text, template_vars, data)

        assert "€50000.00" in result
        assert "moderate" in result
        assert "Stocks" in result
        assert "BTC" in result
        assert "S&P 500" in result

    @pytest.mark.asyncio
    async def test_render_rebalancing_prompt_missing_variable_raises(self, test_session):
        """Test that missing template variables raise ValueError."""
        from prompt_renderer import PromptRenderer

        prompt_text = "Total: {portfolio_total_value}"
        template_vars = {"portfolio_total_value": {"type": "decimal"}}
        data = {}  # Missing required variable

        renderer = PromptRenderer()

        with pytest.raises(ValueError, match="Missing template variables"):
            renderer.render(prompt_text, template_vars, data)


class TestRebalancingJSONParsing:
    """Test JSON response parsing from Claude."""

    def test_parse_rebalancing_json_direct(self):
        """Test parsing direct JSON response."""
        service = self._create_mock_service()

        json_response = json.dumps({
            "summary": "Test summary",
            "priority": "HIGH",
            "recommendations": [],
            "expected_outcome": {
                "stocks_percentage": 60.0,
                "crypto_percentage": 25.0,
                "metals_percentage": 15.0,
                "total_trades": 0,
                "estimated_costs": 0,
                "net_allocation_improvement": "Balanced"
            },
            "risk_assessment": "Low",
            "implementation_notes": "None needed"
        })

        result = service._extract_json_from_response(json_response)

        assert result["summary"] == "Test summary"
        assert result["priority"] == "HIGH"
        assert len(result["recommendations"]) == 0

    def test_parse_rebalancing_json_with_markdown_block(self):
        """Test parsing JSON from markdown code block."""
        service = self._create_mock_service()

        response = """Here are the recommendations:

```json
{
  "summary": "Rebalance crypto",
  "priority": "MEDIUM",
  "recommendations": [
    {
      "action": "SELL",
      "symbol": "BTC",
      "asset_type": "CRYPTO",
      "quantity": 0.1,
      "current_price": 80000.00,
      "estimated_value": 8000.00,
      "rationale": "Reduce exposure",
      "priority": 1,
      "timing": "Within 1 week",
      "transaction_data": {
        "transaction_type": "SELL",
        "symbol": "BTC",
        "quantity": 0.1,
        "price": 80000.00,
        "total_value": 8000.00,
        "currency": "EUR",
        "notes": "Rebalancing"
      }
    }
  ],
  "expected_outcome": {
    "stocks_percentage": 60.0,
    "crypto_percentage": 25.0,
    "metals_percentage": 15.0,
    "total_trades": 1,
    "estimated_costs": 40.00,
    "net_allocation_improvement": "+10% closer"
  },
  "risk_assessment": "Low",
  "implementation_notes": "Execute quickly"
}
```

That's my analysis."""

        result = service._extract_json_from_response(response)

        assert result["summary"] == "Rebalance crypto"
        assert result["priority"] == "MEDIUM"
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["symbol"] == "BTC"
        assert result["recommendations"][0]["action"] == "SELL"

    def test_parse_rebalancing_json_invalid_raises(self):
        """Test that invalid JSON raises ValueError."""
        service = self._create_mock_service()

        response = "This is not JSON at all!"

        with pytest.raises(ValueError, match="Could not parse JSON"):
            service._extract_json_from_response(response)

    def _create_mock_service(self):
        """Helper to create AnalysisService with mocked dependencies."""
        mock_db = AsyncMock()
        mock_claude = AsyncMock()
        mock_prompts = AsyncMock()
        mock_data = AsyncMock()
        mock_cache = AsyncMock()

        return AnalysisService(
            db=mock_db,
            claude_service=mock_claude,
            prompt_service=mock_prompts,
            data_collector=mock_data,
            cache_service=mock_cache
        )


class TestRebalancingRecommendationValidation:
    """Test validation of recommendation quantities and priorities."""

    def test_validate_recommendation_quantities_positive(self):
        """Test that recommendation quantities must be positive."""
        rec = RebalancingRecommendation(
            action=RebalancingAction.BUY,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            quantity=Decimal("0.5"),
            current_price=Decimal("80000.00"),
            estimated_value=Decimal("40000.00"),
            rationale="Test",
            priority=1,
            transaction_data=TransactionData(
                transaction_type="BUY",
                symbol="BTC",
                quantity=Decimal("0.5"),
                price=Decimal("80000.00"),
                total_value=Decimal("40000.00"),
                notes="Test"
            )
        )

        assert rec.quantity > 0
        assert rec.estimated_value > 0

    def test_validate_recommendation_priorities_sequential(self):
        """Test that recommendation priorities are properly ordered."""
        recs = [
            RebalancingRecommendation(
                action=RebalancingAction.SELL,
                symbol="BTC",
                asset_type=AssetType.CRYPTO,
                quantity=Decimal("0.1"),
                current_price=Decimal("80000.00"),
                estimated_value=Decimal("8000.00"),
                rationale="Highest priority",
                priority=1,
                transaction_data=TransactionData(
                    transaction_type="SELL",
                    symbol="BTC",
                    quantity=Decimal("0.1"),
                    price=Decimal("80000.00"),
                    total_value=Decimal("8000.00"),
                    notes="Test"
                )
            ),
            RebalancingRecommendation(
                action=RebalancingAction.BUY,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                quantity=Decimal("10"),
                current_price=Decimal("150.00"),
                estimated_value=Decimal("1500.00"),
                rationale="Second priority",
                priority=2,
                transaction_data=TransactionData(
                    transaction_type="BUY",
                    symbol="AAPL",
                    quantity=Decimal("10"),
                    price=Decimal("150.00"),
                    total_value=Decimal("1500.00"),
                    notes="Test"
                )
            )
        ]

        # Verify priorities are in order
        assert recs[0].priority == 1
        assert recs[1].priority == 2
        assert recs[0].priority < recs[1].priority


class TestBalancedPortfolioHandling:
    """Test handling of already-balanced portfolios."""

    @pytest.mark.asyncio
    async def test_balanced_portfolio_no_recommendations(self, test_session):
        """Test that balanced portfolios return empty recommendations."""
        service = self._create_service_with_mocks(test_session)

        # Create balanced portfolio analysis
        analysis = RebalancingAnalysis(
            total_portfolio_value=Decimal("50000.00"),
            current_allocation=[
                AssetTypeAllocation(
                    asset_type=AssetType.STOCK,
                    current_value=Decimal("30000.00"),
                    current_percentage=Decimal("60.0"),
                    target_percentage=Decimal("60.0"),
                    deviation=Decimal("0.0"),
                    status=AllocationStatus.BALANCED,
                    rebalancing_needed=False,
                    delta_value=Decimal("0.00"),
                    delta_percentage=Decimal("0.0")
                )
            ],
            target_model="moderate",
            rebalancing_required=False,
            total_trades_needed=0,
            estimated_transaction_costs=Decimal("0.00"),
            largest_deviation=Decimal("0.0"),
            most_overweight=None,
            most_underweight=None
        )

        result = await service.generate_rebalancing_recommendations(analysis)

        assert result['summary'] == "Your portfolio is well-balanced. No rebalancing needed."
        assert result['priority'] == 'LOW'
        assert len(result['recommendations']) == 0
        assert result['tokens_used'] == 0
        assert result['cached'] is False

    def _create_service_with_mocks(self, test_session):
        """Helper to create service with mocked dependencies."""
        from config import get_settings

        config = get_settings()
        mock_claude = AsyncMock()
        mock_data = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        prompt_service = PromptService(test_session)

        return AnalysisService(
            db=test_session,
            claude_service=mock_claude,
            prompt_service=prompt_service,
            data_collector=mock_data,
            cache_service=mock_cache
        )


class TestExtremeDeviationHandling:
    """Test handling of extreme allocation deviations."""

    @pytest.mark.asyncio
    async def test_extreme_deviation_high_priority(self, test_session):
        """Test that extreme deviations generate HIGH priority recommendations."""
        service = self._create_service_with_mocks(test_session)

        # Create prompt in database
        await self._create_rebalancing_prompt(test_session)

        # Create analysis with extreme deviation
        analysis = RebalancingAnalysis(
            total_portfolio_value=Decimal("50000.00"),
            current_allocation=[
                AssetTypeAllocation(
                    asset_type=AssetType.CRYPTO,
                    current_value=Decimal("20000.00"),
                    current_percentage=Decimal("40.0"),
                    target_percentage=Decimal("25.0"),
                    deviation=Decimal("15.0"),  # Extreme overweight
                    status=AllocationStatus.OVERWEIGHT,
                    rebalancing_needed=True,
                    delta_value=Decimal("-7500.00"),
                    delta_percentage=Decimal("-15.0")
                )
            ],
            target_model="moderate",
            rebalancing_required=True,
            total_trades_needed=5,
            estimated_transaction_costs=Decimal("125.50"),
            largest_deviation=Decimal("15.0"),
            most_overweight="crypto",
            most_underweight="stocks"
        )

        # Mock Claude response
        mock_response = {
            "summary": "Urgent rebalancing needed - crypto 15% overweight",
            "priority": "HIGH",
            "recommendations": [
                {
                    "action": "SELL",
                    "symbol": "BTC",
                    "asset_type": "CRYPTO",
                    "quantity": 0.09,
                    "current_price": 81234.56,
                    "estimated_value": 7311.11,
                    "rationale": "Critical overweight reduction needed",
                    "priority": 1,
                    "timing": "Immediate",
                    "transaction_data": {
                        "transaction_type": "SELL",
                        "symbol": "BTC",
                        "quantity": 0.09,
                        "price": 81234.56,
                        "total_value": 7311.11,
                        "currency": "EUR",
                        "notes": "Rebalancing: Reduce crypto from 40% to 25%"
                    }
                }
            ],
            "expected_outcome": {
                "stocks_percentage": 60.0,
                "crypto_percentage": 25.0,
                "metals_percentage": 15.0,
                "total_trades": 5,
                "estimated_costs": 125.50,
                "net_allocation_improvement": "+15% closer to target"
            },
            "risk_assessment": "Medium - Large trades may impact prices",
            "implementation_notes": "Execute quickly due to high deviation"
        }

        service.claude.generate_analysis = AsyncMock(return_value={
            'content': json.dumps(mock_response),
            'tokens_used': 1850,
            'generation_time_ms': 8500,
            'model': 'claude-sonnet-4-5-20250929',
            'stop_reason': 'end_turn'
        })

        # Mock data collector
        service.data.collect_global_data = AsyncMock(return_value={
            'market_indicators': {
                'sp500': {'price': 5000, 'change_percent': '+0.5%'},
                'bitcoin': {'price': 81234.56, 'change_percent': '+2.3%'},
                'gold': {'price': 2500, 'change_percent': '-0.1%'}
            }
        })

        result = await service.generate_rebalancing_recommendations(analysis)

        assert result['priority'] == 'HIGH'
        assert len(result['recommendations']) > 0
        assert result['recommendations'][0]['symbol'] == 'BTC'
        assert result['recommendations'][0]['action'] == 'SELL'
        assert result['tokens_used'] > 0

    def _create_service_with_mocks(self, test_session):
        """Helper to create service with mocked dependencies."""
        from config import get_settings

        config = get_settings()
        mock_claude = ClaudeService(config)
        mock_data = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        prompt_service = PromptService(test_session)

        return AnalysisService(
            db=test_session,
            claude_service=mock_claude,
            prompt_service=prompt_service,
            data_collector=mock_data,
            cache_service=mock_cache
        )

    async def _create_rebalancing_prompt(self, test_session):
        """Helper to create rebalancing prompt in database."""
        prompt = Prompt(
            name="portfolio_rebalancing",
            category="rebalancing",
            prompt_text="Generate rebalancing recommendations for {target_model} model",
            template_variables={
                "portfolio_total_value": {"type": "decimal"},
                "target_model": {"type": "string"},
                "allocation_table": {"type": "string"},
                "positions_table": {"type": "string"},
                "market_indices": {"type": "string"}
            },
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()


class TestRebalancingCaching:
    """Test caching behavior for rebalancing recommendations."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self, test_session):
        """Test that cache hit returns cached recommendations."""
        service = self._create_service_with_mocks(test_session)

        # Mock cached result
        cached_data = {
            'summary': 'Cached recommendations',
            'priority': 'MEDIUM',
            'recommendations': [],
            'expected_outcome': {
                'stocks_percentage': 60.0,
                'crypto_percentage': 25.0,
                'metals_percentage': 15.0,
                'total_trades': 0,
                'estimated_costs': 0,
                'net_allocation_improvement': 'Balanced'
            },
            'risk_assessment': 'Low',
            'implementation_notes': 'None',
            'generated_at': datetime.now(UTC) - timedelta(hours=3),
            'tokens_used': 1500
        }
        service.cache.get.return_value = cached_data

        analysis = self._create_test_analysis()

        result = await service.generate_rebalancing_recommendations(analysis)

        assert result['cached'] is True
        assert result['summary'] == 'Cached recommendations'
        assert result['tokens_used'] == 1500

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, test_session):
        """Test that force_refresh bypasses cache."""
        service = self._create_service_with_mocks(test_session)

        # Create prompt
        await self._create_rebalancing_prompt(test_session)

        # Mock cached result (should be ignored)
        cached_data = {
            'summary': 'Old cached data',
            'generated_at': datetime.now(UTC) - timedelta(hours=1),
            'tokens_used': 1000
        }
        service.cache.get.return_value = cached_data

        # Mock Claude response
        mock_response = {
            "summary": "Fresh recommendations",
            "priority": "HIGH",
            "recommendations": [],
            "expected_outcome": {
                "stocks_percentage": 60.0,
                "crypto_percentage": 25.0,
                "metals_percentage": 15.0,
                "total_trades": 0,
                "estimated_costs": 0,
                "net_allocation_improvement": "Balanced"
            },
            "risk_assessment": "Low",
            "implementation_notes": "None"
        }

        service.claude.generate_analysis = AsyncMock(return_value={
            'content': json.dumps(mock_response),
            'tokens_used': 2000,
            'generation_time_ms': 9000,
            'model': 'claude-sonnet-4-5-20250929',
            'stop_reason': 'end_turn'
        })

        service.data.collect_global_data = AsyncMock(return_value={
            'market_indicators': {}
        })

        analysis = self._create_test_analysis()

        result = await service.generate_rebalancing_recommendations(
            analysis, force_refresh=True
        )

        assert result['cached'] is False
        assert result['summary'] == 'Fresh recommendations'
        assert result['tokens_used'] == 2000

    def _create_service_with_mocks(self, test_session):
        """Helper to create service with mocked dependencies."""
        from config import get_settings

        config = get_settings()
        mock_claude = ClaudeService(config)
        mock_data = AsyncMock()
        mock_cache = AsyncMock()

        prompt_service = PromptService(test_session)

        return AnalysisService(
            db=test_session,
            claude_service=mock_claude,
            prompt_service=prompt_service,
            data_collector=mock_data,
            cache_service=mock_cache
        )

    def _create_test_analysis(self):
        """Helper to create test analysis."""
        return RebalancingAnalysis(
            total_portfolio_value=Decimal("50000.00"),
            current_allocation=[
                AssetTypeAllocation(
                    asset_type=AssetType.STOCK,
                    current_value=Decimal("27500.00"),
                    current_percentage=Decimal("55.0"),
                    target_percentage=Decimal("60.0"),
                    deviation=Decimal("-5.0"),
                    status=AllocationStatus.UNDERWEIGHT,
                    rebalancing_needed=True,
                    delta_value=Decimal("2500.00"),
                    delta_percentage=Decimal("5.0")
                )
            ],
            target_model="moderate",
            rebalancing_required=True,
            total_trades_needed=3,
            estimated_transaction_costs=Decimal("75.00"),
            largest_deviation=Decimal("5.0"),
            most_overweight=None,
            most_underweight="stocks"
        )

    async def _create_rebalancing_prompt(self, test_session):
        """Helper to create rebalancing prompt in database."""
        prompt = Prompt(
            name="portfolio_rebalancing",
            category="rebalancing",
            prompt_text="Generate recommendations",
            template_variables={
                "portfolio_total_value": {"type": "decimal"},
                "target_model": {"type": "string"},
                "allocation_table": {"type": "string"},
                "positions_table": {"type": "string"},
                "market_indices": {"type": "string"}
            },
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()


class TestJSONParsingErrorHandling:
    """Test error handling for JSON parsing failures."""

    def test_json_parsing_error_handling(self):
        """Test that JSON parsing errors are caught and raised properly."""
        service = self._create_mock_service()

        # Invalid JSON response
        response = "This is plain text, not JSON!"

        with pytest.raises(ValueError, match="Could not parse JSON"):
            service._extract_json_from_response(response)

    def _create_mock_service(self):
        """Helper to create AnalysisService with mocked dependencies."""
        mock_db = AsyncMock()
        mock_claude = AsyncMock()
        mock_prompts = AsyncMock()
        mock_data = AsyncMock()
        mock_cache = AsyncMock()

        return AnalysisService(
            db=mock_db,
            claude_service=mock_claude,
            prompt_service=mock_prompts,
            data_collector=mock_data,
            cache_service=mock_cache
        )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEndToEndRebalancingRecommendations:
    """Integration tests for complete rebalancing recommendation workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_rebalancing_recommendations(self, test_session):
        """Test complete workflow from analysis to recommendations."""
        # This test requires real services and database
        # Create positions, run analysis, generate recommendations

        # Setup: Create test positions
        positions = [
            Position(
                symbol="BTC",
                asset_type=AssetType.CRYPTO,
                quantity=Decimal("0.5"),
                avg_cost_basis=Decimal("70000.00"),
                total_cost_basis=Decimal("35000.00"),
                current_price=Decimal("80000.00"),
                current_value=Decimal("40000.00"),
                unrealized_pnl=Decimal("5000.00"),
                unrealized_pnl_percent=Decimal("14.29")
            ),
            Position(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                quantity=Decimal("50"),
                avg_cost_basis=Decimal("150.00"),
                total_cost_basis=Decimal("7500.00"),
                current_price=Decimal("160.00"),
                current_value=Decimal("8000.00"),
                unrealized_pnl=Decimal("500.00"),
                unrealized_pnl_percent=Decimal("6.67")
            )
        ]

        for pos in positions:
            test_session.add(pos)
        await test_session.commit()

        # Create rebalancing service
        rebalancing_service = RebalancingService(test_session)

        # Run allocation analysis
        analysis = await rebalancing_service.analyze_rebalancing(
            target_model="moderate"
        )

        assert analysis.total_portfolio_value > 0
        assert len(analysis.current_allocation) > 0

    @pytest.mark.asyncio
    async def test_moderate_model_recommendations(self, test_session):
        """Test recommendations for moderate allocation model."""
        # Test specific to moderate model (60/25/15)
        pass  # Implement with real data

    @pytest.mark.asyncio
    async def test_aggressive_model_recommendations(self, test_session):
        """Test recommendations for aggressive allocation model."""
        # Test specific to aggressive model (50/40/10)
        pass  # Implement with real data

    @pytest.mark.asyncio
    async def test_custom_model_recommendations(self, test_session):
        """Test recommendations for custom allocation model."""
        # Test with custom percentages
        pass  # Implement with real data

    @pytest.mark.asyncio
    async def test_recommendation_response_structure(self, test_session):
        """Test that recommendation response has correct structure."""
        # Verify all required fields are present
        pass  # Implement with real data
