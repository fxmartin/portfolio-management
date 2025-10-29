# ABOUTME: Unit tests for AnalysisService - AI analysis orchestration layer
# ABOUTME: Tests prompt rendering, Claude API integration, caching, and database storage

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from sqlalchemy.ext.asyncio import AsyncSession


class TestAnalysisServiceInitialization:
    """Test AnalysisService initialization."""

    @pytest.mark.asyncio
    async def test_init_with_dependencies(self, test_session):
        """Test service initializes with all dependencies."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        from config import get_settings

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)

        # Mock data collector and cache
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        assert service.db == test_session
        assert service.claude == claude
        assert service.prompts == prompt_service
        assert service.data == mock_data_collector
        assert service.cache == mock_cache


class TestGlobalAnalysisGeneration:
    """Test global market analysis generation."""

    @pytest.mark.asyncio
    async def test_generate_global_analysis_success(self, test_session):
        """Test successful global analysis generation."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        from config import get_settings
        from models import Prompt

        # Setup
        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)

        # Mock data collector and cache
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="global_market_analysis",
            category="global",
            prompt_text="Analyze portfolio: {total_positions} positions worth {total_value}",
            template_variables={"total_positions": "integer", "total_value": "decimal"},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        # Mock dependencies
        mock_cache.get.return_value = None  # Cache miss

        with patch.object(mock_data_collector, 'collect_global_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {"total_positions": 5, "total_value": 50000.00}
                mock_claude.return_value = {
                    'content': 'Your portfolio looks strong!',
                    'tokens_used': 150,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 3000,
                    'stop_reason': 'end_turn'
                }

                result = await service.generate_global_analysis()

                # Verify result
                assert result['analysis'] == 'Your portfolio looks strong!'
                assert result['tokens_used'] == 150
                assert result['cached'] is False
                assert 'generated_at' in result

    @pytest.mark.asyncio
    async def test_generate_global_analysis_cached(self, test_session):
        """Test that cached global analysis is returned."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Mock cached result
        cached_data = {
            'analysis': 'Cached analysis',
            'generated_at': datetime.utcnow() - timedelta(minutes=30),
            'tokens_used': 100
        }
        mock_cache.get.return_value = cached_data

        result = await service.generate_global_analysis()

        # Should return cached result
        assert result['analysis'] == 'Cached analysis'
        assert result['cached'] is True
        assert result['tokens_used'] == 100

    @pytest.mark.asyncio
    async def test_generate_global_analysis_force_refresh(self, test_session):
        """Test force refresh bypasses cache."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="global_market_analysis",
            category="global",
            prompt_text="Analyze: {total_value}",
            template_variables={"total_value": "decimal"},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        # Mock cached result (should be ignored)
        mock_cache.get.return_value = {'analysis': 'Old cached'}

        with patch.object(mock_data_collector, 'collect_global_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {"total_value": 50000.00}
                mock_claude.return_value = {
                    'content': 'Fresh analysis',
                    'tokens_used': 150,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 3000,
                    'stop_reason': 'end_turn'
                }

                result = await service.generate_global_analysis(force_refresh=True)

                # Should bypass cache
                assert result['analysis'] == 'Fresh analysis'
                assert result['cached'] is False


class TestPositionAnalysisGeneration:
    """Test position-level analysis generation."""

    @pytest.mark.asyncio
    async def test_generate_position_analysis_success(self, test_session):
        """Test successful position analysis generation."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="position_analysis",
            category="position",
            prompt_text="Analyze {symbol}: {quantity} @ {current_price}",
            template_variables={"symbol": "string", "quantity": "decimal", "current_price": "decimal"},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        mock_cache.get.return_value = None

        with patch.object(mock_data_collector, 'collect_position_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {
                    "symbol": "BTC",
                    "quantity": 0.5,
                    "current_price": 65000.00
                }
                mock_claude.return_value = {
                    'content': 'BTC position looks good. HOLD',
                    'tokens_used': 100,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 2000,
                    'stop_reason': 'end_turn'
                }

                result = await service.generate_position_analysis("BTC")

                assert result['analysis'] == 'BTC position looks good. HOLD'
                assert result['recommendation'] == 'HOLD'
                assert result['tokens_used'] == 100
                assert result['cached'] is False

    @pytest.mark.asyncio
    async def test_extract_recommendation_buy_more(self, test_session):
        """Test extracting BUY_MORE recommendation from analysis."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="position_analysis",
            category="position",
            prompt_text="Test",
            template_variables={},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        mock_cache.get.return_value = None

        with patch.object(mock_data_collector, 'collect_position_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {}
                mock_claude.return_value = {
                    'content': 'Strong uptrend. BUY_MORE at current levels.',
                    'tokens_used': 80,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 2000,
                    'stop_reason': 'end_turn'
                }

                result = await service.generate_position_analysis("AAPL")

                assert result['recommendation'] == 'BUY_MORE'


class TestForecastGeneration:
    """Test forecast generation with structured JSON output."""

    @pytest.mark.asyncio
    async def test_generate_forecast_success(self, test_session):
        """Test successful forecast generation with JSON parsing."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="forecast_two_quarters",
            category="forecast",
            prompt_text="Forecast {symbol}",
            template_variables={"symbol": "string"},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        mock_cache.get.return_value = None

        forecast_json = {
            "q1_forecast": {
                "pessimistic": {"price": 60000, "confidence": 0.3},
                "realistic": {"price": 65000, "confidence": 0.5},
                "optimistic": {"price": 70000, "confidence": 0.2}
            },
            "q2_forecast": {
                "pessimistic": {"price": 58000, "confidence": 0.3},
                "realistic": {"price": 68000, "confidence": 0.5},
                "optimistic": {"price": 75000, "confidence": 0.2}
            },
            "overall_outlook": "Moderate growth expected"
        }

        with patch.object(mock_data_collector, 'collect_forecast_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {"symbol": "BTC"}
                mock_claude.return_value = {
                    'content': json.dumps(forecast_json),
                    'tokens_used': 500,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 5000,
                    'stop_reason': 'end_turn'
                }

                result = await service.generate_forecast("BTC")

                assert 'q1_forecast' in result
                assert 'q2_forecast' in result
                assert result['overall_outlook'] == "Moderate growth expected"
                assert result['tokens_used'] == 500
                assert result['cached'] is False

    @pytest.mark.asyncio
    async def test_generate_forecast_json_in_markdown(self, test_session):
        """Test forecast extraction from markdown code block."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="forecast_two_quarters",
            category="forecast",
            prompt_text="Test",
            template_variables={},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        mock_cache.get.return_value = None

        forecast_json = {
            "q1_forecast": {
                "pessimistic": {"price": 100, "confidence": 0.3},
                "realistic": {"price": 110, "confidence": 0.5},
                "optimistic": {"price": 120, "confidence": 0.2}
            },
            "q2_forecast": {
                "pessimistic": {"price": 105, "confidence": 0.3},
                "realistic": {"price": 115, "confidence": 0.5},
                "optimistic": {"price": 125, "confidence": 0.2}
            },
            "overall_outlook": "Positive trend"
        }

        markdown_response = f"Here's the forecast:\n\n```json\n{json.dumps(forecast_json)}\n```\n"

        with patch.object(mock_data_collector, 'collect_forecast_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {}
                mock_claude.return_value = {
                    'content': markdown_response,
                    'tokens_used': 500,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 5000,
                    'stop_reason': 'end_turn'
                }

                result = await service.generate_forecast("AAPL")

                # Should extract JSON from markdown code block
                assert 'q1_forecast' in result
                assert result['overall_outlook'] == "Positive trend"


class TestCacheIntegration:
    """Test Redis cache integration."""

    @pytest.mark.asyncio
    async def test_cache_stores_analysis(self, test_session):
        """Test that analysis results are stored in cache."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="global_market_analysis",
            category="global",
            prompt_text="Test",
            template_variables={},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        mock_cache.get.return_value = None

        with patch.object(mock_data_collector, 'collect_global_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {}
                mock_claude.return_value = {
                    'content': 'Test analysis',
                    'tokens_used': 100,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 2000,
                    'stop_reason': 'end_turn'
                }

                await service.generate_global_analysis()

                # Verify cache.set was called
                mock_cache.set.assert_called_once()
                call_args = mock_cache.set.call_args
                assert call_args[0][0] == "analysis:global"  # cache key
                assert call_args[1]['ttl'] == 3600  # 1 hour

    @pytest.mark.asyncio
    async def test_forecast_cache_ttl_longer(self, test_session):
        """Test that forecasts have longer cache TTL (24 hours)."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="forecast_two_quarters",
            category="forecast",
            prompt_text="Test",
            template_variables={},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()

        mock_cache.get.return_value = None

        forecast_json = {
            "q1_forecast": {
                "pessimistic": {"price": 100, "confidence": 0.3},
                "realistic": {"price": 110, "confidence": 0.5},
                "optimistic": {"price": 120, "confidence": 0.2}
            },
            "q2_forecast": {
                "pessimistic": {"price": 105, "confidence": 0.3},
                "realistic": {"price": 115, "confidence": 0.5},
                "optimistic": {"price": 125, "confidence": 0.2}
            },
            "overall_outlook": "Test"
        }

        with patch.object(mock_data_collector, 'collect_forecast_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {}
                mock_claude.return_value = {
                    'content': json.dumps(forecast_json),
                    'tokens_used': 500,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 5000,
                    'stop_reason': 'end_turn'
                }

                await service.generate_forecast("BTC")

                # Verify cache.set was called with 24 hour TTL
                call_args = mock_cache.set.call_args
                assert call_args[0][0] == "analysis:forecast:BTC"
                assert call_args[1]['ttl'] == 86400  # 24 hours


class TestDatabaseStorage:
    """Test analysis results storage in database."""

    @pytest.mark.asyncio
    async def test_stores_analysis_in_database(self, test_session):
        """Test that analysis results are stored in database."""
        from analysis_service import AnalysisService
        from claude_service import ClaudeService
        from prompt_service import PromptService
        
        from config import get_settings
        from models import Prompt, AnalysisResult
        from sqlalchemy import select

        config = get_settings()
        claude = ClaudeService(config)
        prompt_service = PromptService(test_session)
        mock_data_collector = AsyncMock()
        mock_cache = AsyncMock()

        service = AnalysisService(
            db=test_session,
            claude_service=claude,
            prompt_service=prompt_service,
            data_collector=mock_data_collector,
            cache_service=mock_cache
        )

        # Create test prompt
        prompt = Prompt(
            name="position_analysis",
            category="position",
            prompt_text="Test",
            template_variables={},
            version=1,
            is_active=True
        )
        test_session.add(prompt)
        await test_session.commit()
        await test_session.refresh(prompt)

        mock_cache.get.return_value = None

        with patch.object(mock_data_collector, 'collect_position_data', new_callable=AsyncMock) as mock_collect:
            with patch.object(claude, 'generate_analysis', new_callable=AsyncMock) as mock_claude:
                mock_collect.return_value = {}
                mock_claude.return_value = {
                    'content': 'Test analysis for BTC',
                    'tokens_used': 150,
                    'model': 'claude-sonnet-4-5-20250929',
                    'generation_time_ms': 3000,
                    'stop_reason': 'end_turn'
                }

                await service.generate_position_analysis("BTC")

                # Verify stored in database
                result = await test_session.execute(
                    select(AnalysisResult).where(AnalysisResult.symbol == "BTC")
                )
                analysis_result = result.scalar_one()

                assert analysis_result.analysis_type == 'position'
                assert analysis_result.symbol == 'BTC'
                assert analysis_result.prompt_id == prompt.id
                assert analysis_result.prompt_version == 1
                assert analysis_result.raw_response == 'Test analysis for BTC'
                assert analysis_result.tokens_used == 150
                assert analysis_result.generation_time_ms == 3000
