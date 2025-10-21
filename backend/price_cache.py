# ABOUTME: Redis-based price caching service for market data
# ABOUTME: Implements TTL-based caching with bulk operations

import json
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

import redis

try:
    from .yahoo_finance_service import PriceData
except ImportError:
    from yahoo_finance_service import PriceData


class PriceCache:
    """Redis cache for price data"""

    def __init__(self, redis_client):
        """
        Initialize price cache

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.namespace = "price"
        self.default_ttl = 60  # seconds

    def set_price(self, ticker: str, price_data: PriceData):
        """
        Store price data in cache

        Args:
            ticker: Stock/crypto ticker symbol
            price_data: PriceData object to cache
        """
        key = f"{self.namespace}:{ticker}"
        ttl = self._calculate_ttl(price_data.market_state)
        data_json = self._serialize_price_data(price_data)
        self.redis.setex(key, ttl, data_json)

    def get_price(self, ticker: str) -> Optional[PriceData]:
        """
        Retrieve price data from cache

        Args:
            ticker: Stock/crypto ticker symbol

        Returns:
            PriceData if found, None otherwise
        """
        key = f"{self.namespace}:{ticker}"
        data = self.redis.get(key)

        if data is None:
            return None

        return self._deserialize_price_data(data)

    def mget_prices(self, tickers: List[str]) -> Dict[str, PriceData]:
        """
        Bulk fetch prices from cache

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to PriceData (only for cache hits)
        """
        pipeline = self.redis.pipeline()

        for ticker in tickers:
            key = f"{self.namespace}:{ticker}"
            pipeline.get(key)

        results = pipeline.execute()

        # Parse results
        price_data_dict = {}
        for ticker, data in zip(tickers, results):
            if data is not None:
                try:
                    price_data = self._deserialize_price_data(data)
                    price_data_dict[ticker] = price_data
                except Exception as e:
                    print(f"Failed to deserialize {ticker}: {e}")
                    continue

        return price_data_dict

    def mset_prices(self, prices: Dict[str, PriceData]):
        """
        Bulk store prices in cache

        Args:
            prices: Dictionary mapping ticker to PriceData
        """
        pipeline = self.redis.pipeline()

        for ticker, price_data in prices.items():
            key = f"{self.namespace}:{ticker}"
            ttl = self._calculate_ttl(price_data.market_state)
            data_json = self._serialize_price_data(price_data)
            pipeline.setex(key, ttl, data_json)

        pipeline.execute()

    def invalidate_price(self, ticker: str):
        """
        Remove price from cache

        Args:
            ticker: Ticker symbol to invalidate
        """
        key = f"{self.namespace}:{ticker}"
        self.redis.delete(key)

    def invalidate_all(self):
        """Remove all price data from cache"""
        keys = self.redis.keys(f"{self.namespace}:*")
        if keys:
            for key in keys:
                self.redis.delete(key)

    def ping(self) -> bool:
        """
        Check Redis connection

        Returns:
            True if connected, False otherwise
        """
        try:
            return self.redis.ping()
        except Exception:
            return False

    def _calculate_ttl(self, market_state: str) -> int:
        """
        Calculate TTL based on market state

        Args:
            market_state: 'open', 'closed', 'pre', 'post'

        Returns:
            TTL in seconds
        """
        if market_state == 'open':
            return 60  # 1 minute for active markets
        elif market_state == 'closed':
            return 300  # 5 minutes for closed markets
        elif market_state == 'pre':
            return 60  # 1 minute for premarket
        elif market_state == 'post':
            return 120  # 2 minutes for after hours
        else:
            return self.default_ttl

    def _serialize_price_data(self, price_data: PriceData) -> str:
        """
        Convert PriceData to JSON string

        Args:
            price_data: PriceData object

        Returns:
            JSON string
        """
        data_dict = {
            'ticker': price_data.ticker,
            'current_price': str(price_data.current_price),
            'previous_close': str(price_data.previous_close),
            'day_change': str(price_data.day_change),
            'day_change_percent': str(price_data.day_change_percent),
            'volume': price_data.volume,
            'bid': str(price_data.bid) if price_data.bid is not None else None,
            'ask': str(price_data.ask) if price_data.ask is not None else None,
            'last_updated': price_data.last_updated.isoformat(),
            'market_state': price_data.market_state
        }
        return json.dumps(data_dict)

    def _deserialize_price_data(self, json_data: str) -> PriceData:
        """
        Convert JSON string to PriceData

        Args:
            json_data: JSON string

        Returns:
            PriceData object
        """
        if isinstance(json_data, bytes):
            json_data = json_data.decode('utf-8')

        data = json.loads(json_data)

        return PriceData(
            ticker=data['ticker'],
            current_price=Decimal(data['current_price']),
            previous_close=Decimal(data['previous_close']),
            day_change=Decimal(data['day_change']),
            day_change_percent=Decimal(data['day_change_percent']),
            volume=data['volume'],
            bid=Decimal(data['bid']) if data['bid'] is not None else None,
            ask=Decimal(data['ask']) if data['ask'] is not None else None,
            last_updated=datetime.fromisoformat(data['last_updated']),
            market_state=data['market_state']
        )
