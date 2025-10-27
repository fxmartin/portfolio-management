# ABOUTME: Test suite for Alpha Vantage API service
# ABOUTME: Tests rate limiting, caching, and data fetching with mocked responses

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import json

# Import the service we'll be creating
import sys
sys.path.append('..')


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def alpha_vantage_service(mock_redis):
    """Create AlphaVantageService instance with mocked Redis"""
    from alpha_vantage_service import AlphaVantageService
    return AlphaVantageService(
        api_key="test_api_key",
        redis_client=mock_redis
    )


class TestAlphaVantageRateLimiter:
    """Test rate limiter with token bucket algorithm"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct token counts"""
        from alpha_vantage_service import AlphaVantageRateLimiter

        limiter = AlphaVantageRateLimiter(calls_per_minute=5, calls_per_day=100)
        assert limiter.calls_per_minute == 5
        assert limiter.calls_per_day == 100
        assert limiter.minute_tokens == 5
        assert limiter.day_tokens == 100

    @pytest.mark.asyncio
    async def test_rate_limiter_consumes_tokens(self):
        """Test that acquiring tokens decreases both buckets"""
        from alpha_vantage_service import AlphaVantageRateLimiter

        limiter = AlphaVantageRateLimiter(calls_per_minute=5, calls_per_day=100)

        await limiter.acquire()
        assert limiter.minute_tokens == 4
        assert limiter.day_tokens == 99

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_minute_limit_reached(self):
        """Test that rate limiter blocks when minute tokens exhausted"""
        from alpha_vantage_service import AlphaVantageRateLimiter

        limiter = AlphaVantageRateLimiter(calls_per_minute=2, calls_per_day=100)

        # Consume all tokens
        await limiter.acquire()
        await limiter.acquire()

        # This should wait ~60 seconds, but we'll mock time
        with patch('alpha_vantage_service.datetime') as mock_datetime:
            # Simulate time passage
            mock_datetime.now.side_effect = [
                datetime.now(),  # Initial check
                datetime.now() + timedelta(seconds=61),  # After refill
            ]

            # Should not raise exception, refills automatically
            await limiter.acquire()
            assert limiter.minute_tokens >= 0

    @pytest.mark.asyncio
    async def test_rate_limiter_raises_exception_when_day_limit_reached(self):
        """Test that rate limiter raises exception when daily limit exhausted"""
        from alpha_vantage_service import AlphaVantageRateLimiter

        limiter = AlphaVantageRateLimiter(calls_per_minute=5, calls_per_day=2)

        # Consume all daily tokens
        await limiter.acquire()
        await limiter.acquire()

        # Should raise exception for daily limit
        with pytest.raises(Exception, match="daily rate limit exceeded"):
            await limiter.acquire()

    @pytest.mark.asyncio
    async def test_rate_limiter_refills_minute_bucket(self):
        """Test that minute bucket refills after 60 seconds"""
        from alpha_vantage_service import AlphaVantageRateLimiter

        limiter = AlphaVantageRateLimiter(calls_per_minute=5, calls_per_day=100)
        limiter.minute_tokens = 0
        limiter.last_minute_refill = datetime.now() - timedelta(seconds=61)

        await limiter.acquire()
        assert limiter.minute_tokens == 4  # Refilled to 5, consumed 1


class TestAlphaVantageServiceQuotes:
    """Test real-time quote fetching"""

    @pytest.mark.asyncio
    async def test_get_quote_success(self, alpha_vantage_service, mock_redis):
        """Test successful quote fetch from API"""
        mock_response_data = {
            "Global Quote": {
                "01. symbol": "IBM",
                "05. price": "145.50",
                "08. previous close": "144.00",
                "09. change": "1.50",
                "10. change percent": "1.04%",
                "06. volume": "5234567"
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            price_data = await alpha_vantage_service.get_quote("IBM")

            assert price_data.symbol == "IBM"
            assert price_data.current_price == Decimal("145.50")
            assert price_data.previous_close == Decimal("144.00")
            assert price_data.change == Decimal("1.50")
            assert price_data.change_percent == Decimal("1.04")
            assert price_data.volume == 5234567

    @pytest.mark.asyncio
    async def test_get_quote_caches_result(self, alpha_vantage_service, mock_redis):
        """Test that quote results are cached in Redis"""
        mock_response_data = {
            "Global Quote": {
                "01. symbol": "IBM",
                "05. price": "145.50",
                "08. previous close": "144.00",
                "09. change": "1.50",
                "10. change percent": "1.04%",
                "06. volume": "5234567"
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            await alpha_vantage_service.get_quote("IBM")

            # Verify cache was set
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args[0]
            assert call_args[0] == "av:quote:IBM"  # Cache key
            assert call_args[1] == 60  # TTL

    @pytest.mark.asyncio
    async def test_get_quote_returns_cached_data(self, alpha_vantage_service, mock_redis):
        """Test that cached quotes are returned without API call"""
        cached_data = json.dumps({
            "symbol": "IBM",
            "current_price": "145.50",
            "previous_close": "144.00",
            "change": "1.50",
            "change_percent": "1.04",
            "volume": 5234567,
            "last_updated": datetime.now().isoformat()
        })

        mock_redis.get = AsyncMock(return_value=cached_data)

        with patch('aiohttp.ClientSession.get') as mock_get:
            price_data = await alpha_vantage_service.get_quote("IBM")

            # Verify API was NOT called
            mock_get.assert_not_called()

            # Verify data came from cache
            assert price_data.symbol == "IBM"
            assert price_data.current_price == Decimal("145.50")

    @pytest.mark.asyncio
    async def test_get_quote_handles_no_data(self, alpha_vantage_service):
        """Test handling when API returns no quote data"""
        mock_response_data = {"Note": "API limit reached"}

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            with pytest.raises(Exception, match="No quote data"):
                await alpha_vantage_service.get_quote("INVALID")

    @pytest.mark.asyncio
    async def test_get_quote_respects_rate_limit(self, alpha_vantage_service):
        """Test that quote fetching respects rate limits"""
        mock_response_data = {
            "Global Quote": {
                "01. symbol": "IBM",
                "05. price": "145.50",
                "08. previous close": "144.00",
                "09. change": "1.50",
                "10. change percent": "1.04%",
                "06. volume": "5234567"
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            # Mock rate limiter to verify it's called
            alpha_vantage_service.rate_limiter.acquire = AsyncMock()

            await alpha_vantage_service.get_quote("IBM")

            # Verify rate limiter was called
            alpha_vantage_service.rate_limiter.acquire.assert_called_once()


class TestAlphaVantageServiceHistorical:
    """Test historical daily price fetching"""

    @pytest.mark.asyncio
    async def test_get_historical_daily_success(self, alpha_vantage_service):
        """Test successful historical data fetch"""
        mock_response_data = {
            "Time Series (Daily)": {
                "2025-01-15": {
                    "1. open": "145.00",
                    "2. high": "147.50",
                    "3. low": "144.00",
                    "4. close": "146.25",
                    "5. volume": "5234567"
                },
                "2025-01-14": {
                    "1. open": "143.50",
                    "2. high": "145.00",
                    "3. low": "142.75",
                    "4. close": "144.80",
                    "5. volume": "4567890"
                },
                "2025-01-13": {
                    "1. open": "142.00",
                    "2. high": "143.75",
                    "3. low": "141.50",
                    "4. close": "143.25",
                    "5. volume": "3456789"
                }
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            start_date = datetime(2025, 1, 13)
            end_date = datetime(2025, 1, 15)

            prices = await alpha_vantage_service.get_historical_daily("IBM", start_date, end_date)

            assert len(prices) == 3
            assert prices[datetime(2025, 1, 15)] == Decimal("146.25")
            assert prices[datetime(2025, 1, 14)] == Decimal("144.80")
            assert prices[datetime(2025, 1, 13)] == Decimal("143.25")

    @pytest.mark.asyncio
    async def test_get_historical_daily_filters_dates(self, alpha_vantage_service):
        """Test that historical data is filtered to requested date range"""
        mock_response_data = {
            "Time Series (Daily)": {
                "2025-01-20": {"4. close": "150.00"},  # Outside range
                "2025-01-15": {"4. close": "146.25"},  # In range
                "2025-01-14": {"4. close": "144.80"},  # In range
                "2025-01-10": {"4. close": "140.00"}   # Outside range
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            start_date = datetime(2025, 1, 14)
            end_date = datetime(2025, 1, 15)

            prices = await alpha_vantage_service.get_historical_daily("IBM", start_date, end_date)

            # Should only include dates 1/14 and 1/15
            assert len(prices) == 2
            assert datetime(2025, 1, 20) not in prices
            assert datetime(2025, 1, 10) not in prices

    @pytest.mark.asyncio
    async def test_get_historical_daily_caches_result(self, alpha_vantage_service, mock_redis):
        """Test that historical data is cached"""
        mock_response_data = {
            "Time Series (Daily)": {
                "2025-01-15": {"4. close": "146.25"}
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            start_date = datetime(2025, 1, 15)
            end_date = datetime(2025, 1, 15)

            await alpha_vantage_service.get_historical_daily("IBM", start_date, end_date)

            # Verify cache was set
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args[0]
            assert "av:daily:IBM" in call_args[0]
            assert call_args[1] == 3600  # 1 hour TTL

    @pytest.mark.asyncio
    async def test_get_historical_daily_handles_no_data(self, alpha_vantage_service):
        """Test handling when API returns no historical data"""
        mock_response_data = {"Error Message": "Invalid API key"}

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            start_date = datetime(2025, 1, 1)
            end_date = datetime(2025, 1, 31)

            with pytest.raises(Exception, match="No daily data"):
                await alpha_vantage_service.get_historical_daily("INVALID", start_date, end_date)


class TestAlphaVantageServiceCrypto:
    """Test cryptocurrency price fetching"""

    @pytest.mark.asyncio
    async def test_get_crypto_quote_success(self, alpha_vantage_service):
        """Test successful crypto quote fetch"""
        mock_response_data = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "BTC",
                "2. From_Currency Name": "Bitcoin",
                "3. To_Currency Code": "USD",
                "4. To_Currency Name": "United States Dollar",
                "5. Exchange Rate": "45678.90",
                "6. Last Refreshed": "2025-01-15 10:30:00",
                "7. Time Zone": "UTC"
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            price_data = await alpha_vantage_service.get_crypto_quote("BTC", "USD")

            assert price_data.symbol == "BTC"
            assert price_data.current_price == Decimal("45678.90")
            assert price_data.price_currency == "USD"

    @pytest.mark.asyncio
    async def test_get_crypto_quote_eur_market(self, alpha_vantage_service):
        """Test crypto quote in EUR market"""
        mock_response_data = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "BTC",
                "3. To_Currency Code": "EUR",
                "5. Exchange Rate": "42000.50"
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            price_data = await alpha_vantage_service.get_crypto_quote("BTC", "EUR")

            assert price_data.price_currency == "EUR"
            assert price_data.current_price == Decimal("42000.50")

    @pytest.mark.asyncio
    async def test_get_crypto_quote_handles_error(self, alpha_vantage_service):
        """Test handling of crypto quote errors"""
        mock_response_data = {"Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute"}

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_resp

            with pytest.raises(Exception, match="No crypto data"):
                await alpha_vantage_service.get_crypto_quote("INVALID", "USD")


class TestAlphaVantageServiceSerialization:
    """Test data serialization/deserialization for caching"""

    def test_serialize_price_data(self, alpha_vantage_service):
        """Test price data serialization"""
        from alpha_vantage_service import AlphaVantagePriceData

        price_data = AlphaVantagePriceData(
            symbol="IBM",
            current_price=Decimal("145.50"),
            previous_close=Decimal("144.00"),
            change=Decimal("1.50"),
            change_percent=Decimal("1.04"),
            volume=5234567,
            last_updated=datetime(2025, 1, 15, 10, 30, 0)
        )

        serialized = alpha_vantage_service._serialize_price_data(price_data)

        # Should be valid JSON
        data = json.loads(serialized)
        assert data['symbol'] == "IBM"
        assert data['current_price'] == "145.50"
        assert data['volume'] == 5234567

    def test_deserialize_price_data(self, alpha_vantage_service):
        """Test price data deserialization"""
        serialized = json.dumps({
            "symbol": "IBM",
            "current_price": "145.50",
            "previous_close": "144.00",
            "change": "1.50",
            "change_percent": "1.04",
            "volume": 5234567,
            "last_updated": "2025-01-15T10:30:00"
        })

        price_data = alpha_vantage_service._deserialize_price_data(serialized)

        assert price_data.symbol == "IBM"
        assert price_data.current_price == Decimal("145.50")
        assert price_data.volume == 5234567

    def test_serialize_historical_data(self, alpha_vantage_service):
        """Test historical data serialization"""
        prices = {
            datetime(2025, 1, 15): Decimal("146.25"),
            datetime(2025, 1, 14): Decimal("144.80")
        }

        serialized = alpha_vantage_service._serialize_historical_data(prices)

        # Should be valid JSON
        data = json.loads(serialized)
        assert "2025-01-15T00:00:00" in data
        assert data["2025-01-15T00:00:00"] == "146.25"

    def test_deserialize_historical_data(self, alpha_vantage_service):
        """Test historical data deserialization"""
        serialized = json.dumps({
            "2025-01-15T00:00:00": "146.25",
            "2025-01-14T00:00:00": "144.80"
        })

        prices = alpha_vantage_service._deserialize_historical_data(serialized)

        assert len(prices) == 2
        assert prices[datetime(2025, 1, 15)] == Decimal("146.25")
        assert prices[datetime(2025, 1, 14)] == Decimal("144.80")
