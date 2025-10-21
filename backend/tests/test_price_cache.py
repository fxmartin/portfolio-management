# ABOUTME: Tests for Redis price caching service
# ABOUTME: Tests cache operations, TTL management, and bulk operations

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime

try:
    from ..price_cache import PriceCache
    from ..yahoo_finance_service import PriceData
except ImportError:
    from price_cache import PriceCache
    from yahoo_finance_service import PriceData


class TestPriceCache:
    """Test price caching with Redis"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis = Mock()
        redis.setex = Mock()
        redis.get = Mock(return_value=None)
        redis.mget = Mock(return_value=[])
        redis.pipeline = Mock(return_value=Mock())
        redis.ping = Mock(return_value=True)
        return redis

    @pytest.fixture
    def cache(self, mock_redis):
        """Create PriceCache instance with mock Redis"""
        return PriceCache(mock_redis)

    @pytest.fixture
    def sample_price_data(self):
        """Create sample PriceData for testing"""
        return PriceData(
            ticker="AAPL",
            current_price=Decimal("150.25"),
            previous_close=Decimal("148.75"),
            day_change=Decimal("1.50"),
            day_change_percent=Decimal("1.01"),
            volume=1000000,
            bid=Decimal("150.20"),
            ask=Decimal("150.30"),
            last_updated=datetime(2024, 1, 15, 10, 30, 0),
            market_state="open"
        )

    def test_cache_creation(self, cache):
        """Test creating cache instance"""
        assert cache is not None
        assert cache.namespace == "price"
        assert cache.default_ttl == 60

    def test_set_price(self, cache, mock_redis, sample_price_data):
        """Test setting price in cache"""
        cache.set_price("AAPL", sample_price_data)

        # Verify setex was called
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]

        # Check key format
        assert args[0] == "price:AAPL"
        # Check TTL is set
        assert args[1] > 0
        # Check data is JSON
        data = json.loads(args[2])
        assert data['ticker'] == "AAPL"

    def test_get_price(self, cache, mock_redis, sample_price_data):
        """Test getting price from cache"""
        # Set up mock to return data
        price_dict = {
            'ticker': 'AAPL',
            'current_price': '150.25',
            'previous_close': '148.75',
            'day_change': '1.50',
            'day_change_percent': '1.01',
            'volume': 1000000,
            'bid': '150.20',
            'ask': '150.30',
            'last_updated': '2024-01-15T10:30:00',
            'market_state': 'open'
        }
        mock_redis.get.return_value = json.dumps(price_dict)

        result = cache.get_price("AAPL")

        assert result is not None
        assert result.ticker == "AAPL"
        assert result.current_price == Decimal("150.25")
        mock_redis.get.assert_called_once_with("price:AAPL")

    def test_get_price_cache_miss(self, cache, mock_redis):
        """Test get_price returns None on cache miss"""
        mock_redis.get.return_value = None

        result = cache.get_price("AAPL")

        assert result is None

    def test_calculate_ttl_market_open(self, cache):
        """Test TTL calculation for open market"""
        ttl = cache._calculate_ttl("open")
        assert ttl == 60  # 1 minute for active markets

    def test_calculate_ttl_market_closed(self, cache):
        """Test TTL calculation for closed market"""
        ttl = cache._calculate_ttl("closed")
        assert ttl == 300  # 5 minutes for closed markets

    def test_calculate_ttl_premarket(self, cache):
        """Test TTL calculation for premarket"""
        ttl = cache._calculate_ttl("pre")
        assert ttl == 60

    def test_calculate_ttl_afterhours(self, cache):
        """Test TTL calculation for after hours"""
        ttl = cache._calculate_ttl("post")
        assert ttl == 120  # 2 minutes for after hours

    def test_mget_prices(self, cache, mock_redis):
        """Test bulk get operation"""
        # Set up mock pipeline
        pipeline = Mock()
        pipeline.get = Mock()
        pipeline.execute = Mock(return_value=[
            json.dumps({
                'ticker': 'AAPL',
                'current_price': '150.25',
                'previous_close': '148.75',
                'day_change': '1.50',
                'day_change_percent': '1.01',
                'volume': 1000000,
                'bid': '150.20',
                'ask': '150.30',
                'last_updated': '2024-01-15T10:30:00',
                'market_state': 'open'
            }),
            json.dumps({
                'ticker': 'TSLA',
                'current_price': '245.60',
                'previous_close': '248.00',
                'day_change': '-2.40',
                'day_change_percent': '-0.97',
                'volume': 2000000,
                'bid': '245.50',
                'ask': '245.70',
                'last_updated': '2024-01-15T10:30:00',
                'market_state': 'open'
            })
        ])
        mock_redis.pipeline.return_value = pipeline

        result = cache.mget_prices(["AAPL", "TSLA"])

        assert len(result) == 2
        assert "AAPL" in result
        assert "TSLA" in result
        assert result["AAPL"].current_price == Decimal("150.25")
        assert result["TSLA"].current_price == Decimal("245.60")

    def test_mget_prices_partial_miss(self, cache, mock_redis):
        """Test bulk get with some cache misses"""
        pipeline = Mock()
        pipeline.get = Mock()
        pipeline.execute = Mock(return_value=[
            json.dumps({
                'ticker': 'AAPL',
                'current_price': '150.25',
                'previous_close': '148.75',
                'day_change': '1.50',
                'day_change_percent': '1.01',
                'volume': 1000000,
                'bid': '150.20',
                'ask': '150.30',
                'last_updated': '2024-01-15T10:30:00',
                'market_state': 'open'
            }),
            None  # Cache miss for TSLA
        ])
        mock_redis.pipeline.return_value = pipeline

        result = cache.mget_prices(["AAPL", "TSLA"])

        assert len(result) == 1
        assert "AAPL" in result
        assert "TSLA" not in result

    def test_mset_prices(self, cache, mock_redis, sample_price_data):
        """Test bulk set operation"""
        pipeline = Mock()
        pipeline.setex = Mock()
        pipeline.execute = Mock()
        mock_redis.pipeline.return_value = pipeline

        prices = {
            "AAPL": sample_price_data,
            "TSLA": PriceData(
                ticker="TSLA",
                current_price=Decimal("245.60"),
                previous_close=Decimal("248.00"),
                day_change=Decimal("-2.40"),
                day_change_percent=Decimal("-0.97"),
                volume=2000000,
                bid=Decimal("245.50"),
                ask=Decimal("245.70"),
                last_updated=datetime(2024, 1, 15, 10, 30, 0),
                market_state="open"
            )
        }

        cache.mset_prices(prices)

        # Pipeline should be created and executed
        mock_redis.pipeline.assert_called_once()
        pipeline.execute.assert_called_once()

    def test_invalidate_price(self, cache, mock_redis):
        """Test cache invalidation"""
        cache.invalidate_price("AAPL")

        mock_redis.delete.assert_called_once_with("price:AAPL")

    def test_invalidate_all(self, cache, mock_redis):
        """Test invalidating all price data"""
        mock_redis.keys.return_value = [b"price:AAPL", b"price:TSLA"]

        cache.invalidate_all()

        mock_redis.keys.assert_called_once_with("price:*")
        # Should delete all keys
        assert mock_redis.delete.call_count == 2

    def test_ping(self, cache, mock_redis):
        """Test Redis connection check"""
        result = cache.ping()

        assert result is True
        mock_redis.ping.assert_called_once()

    def test_price_data_serialization(self, cache, sample_price_data):
        """Test PriceData to JSON serialization"""
        json_str = cache._serialize_price_data(sample_price_data)
        data = json.loads(json_str)

        assert data['ticker'] == 'AAPL'
        assert data['current_price'] == '150.25'
        assert data['market_state'] == 'open'

    def test_price_data_deserialization(self, cache):
        """Test JSON to PriceData deserialization"""
        json_data = {
            'ticker': 'AAPL',
            'current_price': '150.25',
            'previous_close': '148.75',
            'day_change': '1.50',
            'day_change_percent': '1.01',
            'volume': 1000000,
            'bid': '150.20',
            'ask': '150.30',
            'last_updated': '2024-01-15T10:30:00',
            'market_state': 'open'
        }

        price_data = cache._deserialize_price_data(json.dumps(json_data))

        assert price_data.ticker == 'AAPL'
        assert price_data.current_price == Decimal('150.25')
        assert price_data.market_state == 'open'

    def test_price_data_deserialization_with_none_bid_ask(self, cache):
        """Test deserialization when bid/ask are null"""
        json_data = {
            'ticker': 'AAPL',
            'current_price': '150.25',
            'previous_close': '148.75',
            'day_change': '1.50',
            'day_change_percent': '1.01',
            'volume': 1000000,
            'bid': None,
            'ask': None,
            'last_updated': '2024-01-15T10:30:00',
            'market_state': 'closed'
        }

        price_data = cache._deserialize_price_data(json.dumps(json_data))

        assert price_data.bid is None
        assert price_data.ask is None
