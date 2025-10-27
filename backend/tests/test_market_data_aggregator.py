# ABOUTME: Test suite for MarketDataAggregator with intelligent fallback logic
# ABOUTME: Tests provider selection, circuit breaker, and caching strategies

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from enum import Enum

# Import the aggregator we'll be creating
import sys
sys.path.append('..')


class DataProvider(Enum):
    """Mock of DataProvider enum"""
    YAHOO_FINANCE = "yahoo"
    ALPHA_VANTAGE = "alphavantage"
    CACHE = "cache"


@pytest.fixture
def mock_yahoo_service():
    """Mock Yahoo Finance service"""
    service = Mock()
    service.get_quote = AsyncMock()
    service.get_historical_prices = AsyncMock()
    return service


@pytest.fixture
def mock_alpha_vantage_service():
    """Mock Alpha Vantage service"""
    service = Mock()
    service.get_quote = AsyncMock()
    service.get_historical_daily = AsyncMock()
    return service


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def aggregator(mock_yahoo_service, mock_alpha_vantage_service, mock_redis):
    """Create MarketDataAggregator instance"""
    from market_data_aggregator import MarketDataAggregator
    return MarketDataAggregator(
        yahoo_service=mock_yahoo_service,
        alpha_vantage_service=mock_alpha_vantage_service,
        redis_client=mock_redis
    )


class TestProviderSelection:
    """Test intelligent provider selection logic"""

    def test_is_european_etf_detects_brussels_exchange(self, aggregator):
        """Test detection of Brussels exchange ETFs"""
        assert aggregator._is_european_etf('AMEM.BE') is True
        assert aggregator._is_european_etf('MWOQ.BE') is True

    def test_is_european_etf_detects_other_european_exchanges(self, aggregator):
        """Test detection of other European exchange suffixes"""
        assert aggregator._is_european_etf('ABC.PA') is True  # Paris
        assert aggregator._is_european_etf('DEF.DE') is True  # Germany
        assert aggregator._is_european_etf('GHI.MI') is True  # Milan
        assert aggregator._is_european_etf('JKL.MC') is True  # Madrid

    def test_is_european_etf_returns_false_for_us_stocks(self, aggregator):
        """Test that US stock tickers are not detected as European ETFs"""
        assert aggregator._is_european_etf('AAPL') is False
        assert aggregator._is_european_etf('MSTR') is False
        assert aggregator._is_european_etf('BTC-USD') is False

    @pytest.mark.asyncio
    async def test_us_stock_tries_yahoo_first(self, aggregator, mock_yahoo_service):
        """Test that US stocks try Yahoo Finance first"""
        # Mock successful Yahoo response
        mock_price = Mock()
        mock_price.symbol = "AAPL"
        mock_price.current_price = Decimal("150.00")
        mock_yahoo_service.get_quote.return_value = mock_price

        price, provider = await aggregator.get_quote("AAPL")

        assert provider.value == "yahoo"
        mock_yahoo_service.get_quote.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_european_etf_tries_alpha_vantage_first(self, aggregator, mock_alpha_vantage_service):
        """Test that European ETFs try Alpha Vantage first"""
        # Mock successful Alpha Vantage response
        mock_price = Mock()
        mock_price.symbol = "AMEM.BE"
        mock_price.current_price = Decimal("100.00")
        mock_alpha_vantage_service.get_quote.return_value = mock_price

        price, provider = await aggregator.get_quote("AMEM.BE")

        assert provider.value == "alphavantage"
        mock_alpha_vantage_service.get_quote.assert_called_once_with("AMEM.BE")


class TestFallbackLogic:
    """Test fallback behavior when providers fail"""

    @pytest.mark.asyncio
    async def test_falls_back_to_alpha_vantage_when_yahoo_fails(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service
    ):
        """Test fallback from Yahoo Finance to Alpha Vantage"""
        # Yahoo fails
        mock_yahoo_service.get_quote.side_effect = Exception("Yahoo API error")

        # Alpha Vantage succeeds
        mock_price = Mock()
        mock_price.symbol = "IBM"
        mock_price.current_price = Decimal("145.50")
        mock_alpha_vantage_service.get_quote.return_value = mock_price

        price, provider = await aggregator.get_quote("IBM")

        assert price.symbol == "IBM"
        assert price.current_price == Decimal("145.50")
        assert provider.value == "alphavantage"

        # Verify both were tried
        mock_yahoo_service.get_quote.assert_called_once()
        mock_alpha_vantage_service.get_quote.assert_called_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_cache_when_all_providers_fail(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service, mock_redis
    ):
        """Test fallback to cache when all providers fail"""
        # Both providers fail
        mock_yahoo_service.get_quote.side_effect = Exception("Yahoo API error")
        mock_alpha_vantage_service.get_quote.side_effect = Exception("Alpha Vantage API error")

        # Cache has data
        import json
        cached_data = json.dumps({
            "ticker": "IBM",
            "current_price": "145.50",
            "previous_close": "144.00",
            "change": "1.50",
            "change_percent": "1.04",
            "volume": 5234567,
            "last_updated": datetime.now().isoformat()
        })
        mock_redis.get.return_value = cached_data

        price, provider = await aggregator.get_quote("IBM")

        assert price.ticker == "IBM"  # PriceData uses 'ticker' not 'symbol'
        assert provider.value == "cache"

        # Verify cache was checked
        mock_redis.get.assert_called_once_with("market:quote:IBM")

    @pytest.mark.asyncio
    async def test_returns_none_when_all_fail_including_cache(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service, mock_redis
    ):
        """Test that aggregator returns None when everything fails"""
        # All providers fail
        mock_yahoo_service.get_quote.side_effect = Exception("Yahoo API error")
        mock_alpha_vantage_service.get_quote.side_effect = Exception("Alpha Vantage API error")
        mock_redis.get.return_value = None  # No cached data

        price, provider = await aggregator.get_quote("INVALID")

        assert price is None
        assert provider is None


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation"""

    def test_circuit_breaker_initialization(self, aggregator):
        """Test that circuit breakers are initialized for each provider"""
        from market_data_aggregator import DataProvider

        assert DataProvider.YAHOO_FINANCE in aggregator.circuit_breaker
        assert DataProvider.ALPHA_VANTAGE in aggregator.circuit_breaker
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['failures'] == 0
        assert aggregator.circuit_breaker[DataProvider.ALPHA_VANTAGE]['failures'] == 0

    def test_record_failure_increments_counter(self, aggregator):
        """Test that failures are recorded"""
        from market_data_aggregator import DataProvider

        aggregator._record_failure(DataProvider.YAHOO_FINANCE)
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['failures'] == 1

        aggregator._record_failure(DataProvider.YAHOO_FINANCE)
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['failures'] == 2

    def test_circuit_opens_after_threshold_failures(self, aggregator):
        """Test that circuit opens after reaching failure threshold"""
        from market_data_aggregator import DataProvider

        # Record failures up to threshold (default: 5)
        for _ in range(aggregator.circuit_breaker_threshold):
            aggregator._record_failure(DataProvider.YAHOO_FINANCE)

        # Circuit should now be open
        assert aggregator._is_circuit_open(DataProvider.YAHOO_FINANCE) is True
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['open_until'] is not None

    def test_circuit_stays_closed_below_threshold(self, aggregator):
        """Test that circuit stays closed below threshold"""
        from market_data_aggregator import DataProvider

        # Record fewer failures than threshold
        for _ in range(aggregator.circuit_breaker_threshold - 1):
            aggregator._record_failure(DataProvider.YAHOO_FINANCE)

        # Circuit should still be closed
        assert aggregator._is_circuit_open(DataProvider.YAHOO_FINANCE) is False

    def test_circuit_resets_after_timeout(self, aggregator):
        """Test that circuit closes after timeout expires"""
        from market_data_aggregator import DataProvider

        # Open the circuit
        for _ in range(aggregator.circuit_breaker_threshold):
            aggregator._record_failure(DataProvider.YAHOO_FINANCE)

        assert aggregator._is_circuit_open(DataProvider.YAHOO_FINANCE) is True

        # Simulate timeout passage
        aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['open_until'] = (
            datetime.now() - timedelta(seconds=1)  # Expired 1 second ago
        )

        # Circuit should now be closed
        assert aggregator._is_circuit_open(DataProvider.YAHOO_FINANCE) is False
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['failures'] == 0

    def test_record_success_resets_circuit(self, aggregator):
        """Test that successful call resets circuit breaker"""
        from market_data_aggregator import DataProvider

        # Record some failures
        for _ in range(3):
            aggregator._record_failure(DataProvider.YAHOO_FINANCE)

        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['failures'] == 3

        # Record success
        aggregator._record_success(DataProvider.YAHOO_FINANCE)

        # Circuit should be reset
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['failures'] == 0
        assert aggregator.circuit_breaker[DataProvider.YAHOO_FINANCE]['open_until'] is None

    @pytest.mark.asyncio
    async def test_open_circuit_skips_provider(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service
    ):
        """Test that open circuit causes provider to be skipped"""
        from market_data_aggregator import DataProvider

        # Open Yahoo circuit
        for _ in range(aggregator.circuit_breaker_threshold):
            aggregator._record_failure(DataProvider.YAHOO_FINANCE)

        # Alpha Vantage succeeds
        mock_price = Mock()
        mock_price.symbol = "IBM"
        mock_price.current_price = Decimal("145.50")
        mock_alpha_vantage_service.get_quote.return_value = mock_price

        price, provider = await aggregator.get_quote("IBM")

        # Yahoo should NOT have been called (circuit open)
        mock_yahoo_service.get_quote.assert_not_called()

        # Alpha Vantage should have been called
        mock_alpha_vantage_service.get_quote.assert_called_once()
        assert provider.value == "alphavantage"


class TestProviderStatistics:
    """Test provider metrics tracking"""

    def test_statistics_initialization(self, aggregator):
        """Test that provider statistics are initialized"""
        from market_data_aggregator import DataProvider

        stats = aggregator.provider_stats

        assert DataProvider.YAHOO_FINANCE in stats
        assert DataProvider.ALPHA_VANTAGE in stats
        assert DataProvider.CACHE in stats

        assert stats[DataProvider.YAHOO_FINANCE]['success'] == 0
        assert stats[DataProvider.YAHOO_FINANCE]['failure'] == 0

    @pytest.mark.asyncio
    async def test_success_increments_stat(self, aggregator, mock_yahoo_service):
        """Test that successful calls increment success counter"""
        from market_data_aggregator import DataProvider

        # Mock successful Yahoo response
        mock_price = Mock()
        mock_price.symbol = "AAPL"
        mock_price.current_price = Decimal("150.00")
        mock_yahoo_service.get_quote.return_value = mock_price

        await aggregator.get_quote("AAPL")

        assert aggregator.provider_stats[DataProvider.YAHOO_FINANCE]['success'] == 1
        assert aggregator.provider_stats[DataProvider.YAHOO_FINANCE]['failure'] == 0

    @pytest.mark.asyncio
    async def test_failure_increments_stat(self, aggregator, mock_yahoo_service, mock_alpha_vantage_service):
        """Test that failed calls increment failure counter"""
        from market_data_aggregator import DataProvider

        # Both providers fail
        mock_yahoo_service.get_quote.side_effect = Exception("Yahoo API error")
        mock_alpha_vantage_service.get_quote.side_effect = Exception("Alpha Vantage API error")

        await aggregator.get_quote("INVALID")

        assert aggregator.provider_stats[DataProvider.YAHOO_FINANCE]['failure'] >= 1
        assert aggregator.provider_stats[DataProvider.ALPHA_VANTAGE]['failure'] >= 1

    def test_get_provider_stats_returns_metrics(self, aggregator):
        """Test that get_provider_stats returns comprehensive metrics"""
        from market_data_aggregator import DataProvider

        # Record some activity
        aggregator._record_success(DataProvider.YAHOO_FINANCE)
        aggregator._record_success(DataProvider.YAHOO_FINANCE)
        aggregator._record_failure(DataProvider.ALPHA_VANTAGE)

        stats = aggregator.get_provider_stats()

        assert 'stats' in stats
        assert 'circuit_breakers' in stats

        assert stats['stats'][DataProvider.YAHOO_FINANCE]['success'] == 2
        assert stats['stats'][DataProvider.ALPHA_VANTAGE]['failure'] == 1

        # Check circuit breaker status
        assert 'yahoo' in stats['circuit_breakers']
        assert stats['circuit_breakers']['yahoo']['failures'] == 0  # Reset by success
        assert stats['circuit_breakers']['yahoo']['open'] is False


class TestHistoricalPriceFallback:
    """Test historical price fetching with fallback"""

    @pytest.mark.asyncio
    async def test_historical_prices_from_yahoo_success(
        self, aggregator, mock_yahoo_service
    ):
        """Test successful historical price fetch from Yahoo"""
        mock_yahoo_service.get_historical_prices.return_value = {
            'IBM': {
                datetime(2025, 1, 15): Decimal("146.25"),
                datetime(2025, 1, 14): Decimal("144.80")
            }
        }

        start_date = datetime(2025, 1, 14)
        end_date = datetime(2025, 1, 15)

        prices, provider = await aggregator.get_historical_prices("IBM", start_date, end_date)

        assert len(prices) == 2
        assert prices[datetime(2025, 1, 15)] == Decimal("146.25")
        assert provider.value == "yahoo"

    @pytest.mark.asyncio
    async def test_historical_prices_falls_back_to_alpha_vantage(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service
    ):
        """Test fallback to Alpha Vantage for historical prices"""
        # Yahoo fails
        mock_yahoo_service.get_historical_prices.return_value = {'IBM': {}}

        # Alpha Vantage succeeds
        mock_alpha_vantage_service.get_historical_daily.return_value = {
            datetime(2025, 1, 15): Decimal("146.25"),
            datetime(2025, 1, 14): Decimal("144.80")
        }

        start_date = datetime(2025, 1, 14)
        end_date = datetime(2025, 1, 15)

        prices, provider = await aggregator.get_historical_prices("IBM", start_date, end_date)

        assert len(prices) == 2
        assert provider.value == "alphavantage"
        mock_alpha_vantage_service.get_historical_daily.assert_called_once()

    @pytest.mark.asyncio
    async def test_historical_prices_returns_empty_when_all_fail(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service
    ):
        """Test that empty dict returned when all providers fail"""
        # Both fail
        mock_yahoo_service.get_historical_prices.return_value = {'IBM': {}}
        mock_alpha_vantage_service.get_historical_daily.side_effect = Exception("API error")

        start_date = datetime(2025, 1, 14)
        end_date = datetime(2025, 1, 15)

        prices, provider = await aggregator.get_historical_prices("IBM", start_date, end_date)

        assert prices == {}
        assert provider is None


class TestCacheIntegration:
    """Test caching behavior"""

    @pytest.mark.asyncio
    async def test_cache_fallback_uses_correct_key(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service, mock_redis
    ):
        """Test that cache fallback uses correct Redis key"""
        import json

        # Both providers fail
        mock_yahoo_service.get_quote.side_effect = Exception("Yahoo API error")
        mock_alpha_vantage_service.get_quote.side_effect = Exception("Alpha Vantage API error")

        # Cache has data
        cached_data = json.dumps({
            "symbol": "IBM",
            "current_price": "145.50",
            "previous_close": "144.00",
            "change": "1.50",
            "change_percent": "1.04",
            "volume": 5234567,
            "last_updated": datetime.now().isoformat()
        })
        mock_redis.get.return_value = cached_data

        await aggregator.get_quote("IBM")

        # Verify correct cache key was used
        mock_redis.get.assert_called_once_with("market:quote:IBM")

    @pytest.mark.asyncio
    async def test_cache_increments_success_stat(
        self, aggregator, mock_yahoo_service, mock_alpha_vantage_service, mock_redis
    ):
        """Test that cache hits increment cache success counter"""
        import json
        from market_data_aggregator import DataProvider

        # Both providers fail
        mock_yahoo_service.get_quote.side_effect = Exception("Yahoo API error")
        mock_alpha_vantage_service.get_quote.side_effect = Exception("Alpha Vantage API error")

        # Cache succeeds
        cached_data = json.dumps({
            "symbol": "IBM",
            "current_price": "145.50",
            "previous_close": "144.00",
            "change": "1.50",
            "change_percent": "1.04",
            "volume": 5234567,
            "last_updated": datetime.now().isoformat()
        })
        mock_redis.get.return_value = cached_data

        await aggregator.get_quote("IBM")

        assert aggregator.provider_stats[DataProvider.CACHE]['success'] == 1
