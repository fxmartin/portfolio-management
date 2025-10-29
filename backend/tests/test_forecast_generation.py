# ABOUTME: Tests for forecast generation including data collection and API endpoints
# ABOUTME: Covers historical data fetching, performance metrics, and bulk forecasts

"""
Forecast Generation Tests

Tests for F8.5-001 (Forecast API) and F8.5-002 (Forecast Data Collection):
- Historical price fetching
- Performance metrics calculation (30d, 90d, 180d, 365d)
- Volatility calculation
- Market context building
- Forecast data collection integration
- Single forecast endpoint
- Bulk forecast endpoint
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from prompt_renderer import PromptDataCollector
from models import AssetType


# =====================================================================
# Test F8.5-002: Historical Data Fetching
# =====================================================================

class TestHistoricalPriceFetching:
    """Tests for _get_historical_prices() method"""

    @pytest.mark.asyncio
    async def test_get_historical_prices_success(self):
        """Test successful historical price fetching"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        # Mock yfinance ticker
        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.__getitem__.return_value.tolist.return_value = [
            100.0, 105.0, 103.0, 107.0, 110.0
        ]
        mock_ticker.history.return_value = mock_hist

        with patch('prompt_renderer.yf.Ticker', return_value=mock_ticker):
            prices = await collector._get_historical_prices('AAPL', days=5)

        assert len(prices) == 5
        assert prices == [100.0, 105.0, 103.0, 107.0, 110.0]
        mock_ticker.history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_historical_prices_with_etf_mapping(self):
        """Test ETF symbol transformation for Yahoo Finance"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.__getitem__.return_value.tolist.return_value = [50.0, 51.0]
        mock_ticker.history.return_value = mock_hist

        with patch('prompt_renderer.yf.Ticker', return_value=mock_ticker) as mock_yf:
            prices = await collector._get_historical_prices('AMEM', days=2)

        # Verify ETF mapping applied (AMEM -> AMEM.BE)
        mock_yf.assert_called_once_with('AMEM.BE')
        assert len(prices) == 2

    @pytest.mark.asyncio
    async def test_get_historical_prices_empty_result(self):
        """Test handling of empty price history"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = True
        mock_ticker.history.return_value = mock_hist

        with patch('prompt_renderer.yf.Ticker', return_value=mock_ticker):
            prices = await collector._get_historical_prices('INVALID', days=30)

        assert prices == []

    @pytest.mark.asyncio
    async def test_get_historical_prices_exception_handling(self):
        """Test graceful degradation on API errors"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        with patch('prompt_renderer.yf.Ticker', side_effect=Exception("API Error")):
            prices = await collector._get_historical_prices('AAPL', days=30)

        assert prices == []  # Graceful degradation


# =====================================================================
# Test F8.5-002: Performance Metrics Calculation
# =====================================================================

class TestPerformanceMetrics:
    """Tests for _calculate_performance_metrics() method"""

    def test_calculate_performance_metrics_full_year(self):
        """Test performance calculation with 365 days of data"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        # Generate 365 days of synthetic prices (starting at 100, ending at 120)
        prices = [100 + (20 * i / 365) for i in range(365)]

        metrics = collector._calculate_performance_metrics(prices)

        assert '30d' in metrics
        assert '90d' in metrics
        assert '180d' in metrics
        assert '365d' in metrics
        assert 'volatility' in metrics

        # 365-day return should be ~20%
        assert metrics['365d'] == pytest.approx(20.0, abs=0.1)

    def test_calculate_performance_metrics_partial_data(self):
        """Test performance calculation with limited data"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        # Only 50 days of data
        prices = [100 + (10 * i / 50) for i in range(50)]

        metrics = collector._calculate_performance_metrics(prices)

        # Should still calculate all metrics with available data
        assert metrics['365d'] == pytest.approx(10.0, abs=0.5)  # More tolerance for partial data
        assert metrics['30d'] >= 0
        assert metrics['volatility'] >= 0

    def test_calculate_performance_metrics_high_volatility(self):
        """Test volatility calculation with volatile prices"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        # Highly volatile prices (oscillating)
        prices = [100 + (10 if i % 2 == 0 else -10) for i in range(60)]

        metrics = collector._calculate_performance_metrics(prices)

        # High volatility should be detected
        assert metrics['volatility'] > 50  # Annualized volatility should be high

    def test_calculate_performance_metrics_empty_data(self):
        """Test handling of empty price list"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        metrics = collector._calculate_performance_metrics([])

        # Should return zeros for all metrics
        assert metrics == {
            '30d': 0.0,
            '90d': 0.0,
            '180d': 0.0,
            '365d': 0.0,
            'volatility': 0.0
        }

    def test_calculate_performance_metrics_insufficient_data(self):
        """Test handling of insufficient data (< 2 prices)"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        metrics = collector._calculate_performance_metrics([100.0])

        # Should return zeros
        assert metrics['365d'] == 0.0


# =====================================================================
# Test F8.5-002: Market Context Building
# =====================================================================

class TestMarketContext:
    """Tests for _build_market_context() method"""

    @pytest.mark.asyncio
    async def test_build_market_context_stocks(self):
        """Test market context for stocks"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        # Mock S&P 500 price
        mock_price = Mock()
        mock_price.day_change_percent = 1.23
        yahoo_service.get_price = AsyncMock(return_value=mock_price)

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        context = await collector._build_market_context(AssetType.STOCK)

        assert "S&P 500" in context
        assert "+1.23%" in context
        assert "mixed signals" in context.lower()

    @pytest.mark.asyncio
    async def test_build_market_context_crypto(self):
        """Test market context for crypto"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        # Mock Bitcoin price
        mock_price = Mock()
        mock_price.day_change_percent = -2.45
        yahoo_service.get_price = AsyncMock(return_value=mock_price)

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        context = await collector._build_market_context(AssetType.CRYPTO)

        assert "Bitcoin" in context
        assert "-2.45%" in context
        assert "market leader" in context.lower()

    @pytest.mark.asyncio
    async def test_build_market_context_metals(self):
        """Test market context for metals"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        # Mock Gold price
        mock_price = Mock()
        mock_price.day_change_percent = 0.75
        yahoo_service.get_price = AsyncMock(return_value=mock_price)

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        context = await collector._build_market_context(AssetType.METAL)

        assert "Gold" in context
        assert "+0.75%" in context

    @pytest.mark.asyncio
    async def test_build_market_context_error_handling(self):
        """Test graceful degradation when indices unavailable"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()
        yahoo_service.get_price = AsyncMock(side_effect=Exception("API Error"))

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        context = await collector._build_market_context(AssetType.STOCK)

        assert context == "Market context unavailable"


# =====================================================================
# Test F8.5-002: Integrated Forecast Data Collection
# =====================================================================

class TestForecastDataCollection:
    """Tests for collect_forecast_data() integration"""

    @pytest.mark.asyncio
    async def test_collect_forecast_data_complete(self):
        """Test complete forecast data collection with all fields"""
        db = Mock()
        portfolio_service = Mock()
        yahoo_service = Mock()

        # Mock position
        mock_position = Mock()
        mock_position.symbol = 'AAPL'
        mock_position.current_price = Decimal('150.00')
        mock_position.asset_type = AssetType.STOCK
        portfolio_service.get_position = AsyncMock(return_value=mock_position)

        # Mock Yahoo service
        mock_sp500 = Mock()
        mock_sp500.day_change_percent = 0.5
        yahoo_service.get_price = AsyncMock(return_value=mock_sp500)

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        # Mock historical prices
        historical_prices = [140 + i * 0.5 for i in range(365)]
        with patch.object(collector, '_get_historical_prices', return_value=historical_prices):
            data = await collector.collect_forecast_data('AAPL')

        # Verify all required fields present
        assert data['symbol'] == 'AAPL'
        assert data['current_price'] == 150.0
        assert 'week_52_low' in data
        assert 'week_52_high' in data
        assert data['week_52_low'] == 140.0
        assert data['week_52_high'] == pytest.approx(322.0, abs=1.0)
        assert 'performance_30d' in data
        assert 'performance_90d' in data
        assert 'performance_180d' in data
        assert 'performance_365d' in data
        assert 'volatility_30d' in data
        assert 'market_context' in data
        assert "S&P 500" in data['market_context']

    @pytest.mark.asyncio
    async def test_collect_forecast_data_position_not_found(self):
        """Test error handling when position doesn't exist"""
        db = Mock()
        portfolio_service = Mock()
        portfolio_service.get_position = AsyncMock(return_value=None)
        yahoo_service = Mock()

        collector = PromptDataCollector(db, portfolio_service, yahoo_service)

        with pytest.raises(ValueError, match="Position not found: INVALID"):
            await collector.collect_forecast_data('INVALID')


# =====================================================================
# Test F8.5-001: Forecast API Endpoints (Integration Tests)
# =====================================================================

# Note: Full integration tests for the forecast endpoint would require
# a running database and Claude API mock. These would be added to
# test_analysis_router.py with appropriate fixtures.
