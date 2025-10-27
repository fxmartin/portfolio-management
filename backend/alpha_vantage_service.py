# ABOUTME: Alpha Vantage API integration for fetching market data (stocks, ETFs, crypto)
# ABOUTME: Provides fallback when Yahoo Finance fails, with rate limiting and caching

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass
import aiohttp
import json


@dataclass
class AlphaVantagePriceData:
    """Price data from Alpha Vantage API"""
    symbol: str
    current_price: Decimal
    previous_close: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int
    last_updated: datetime
    asset_name: Optional[str] = None
    price_currency: str = 'USD'


class AlphaVantageRateLimiter:
    """Token bucket rate limiter for Alpha Vantage API"""

    def __init__(self, calls_per_minute: int = 5, calls_per_day: int = 100):
        """
        Initialize rate limiter with token buckets

        Args:
            calls_per_minute: Maximum API calls per minute (default: 5 for free tier)
            calls_per_day: Maximum API calls per day (default: 100 for free tier)
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day
        self.minute_tokens = calls_per_minute
        self.day_tokens = calls_per_day
        self.last_minute_refill = datetime.now()
        self.last_day_refill = datetime.now()

    async def acquire(self):
        """
        Acquire a token from the rate limiter.
        Blocks if minute limit reached, raises exception if daily limit exceeded.

        Raises:
            Exception: When daily rate limit is exceeded
        """
        now = datetime.now()

        # Refill minute bucket if 60+ seconds have passed
        if (now - self.last_minute_refill).total_seconds() >= 60:
            self.minute_tokens = self.calls_per_minute
            self.last_minute_refill = now

        # Refill day bucket if 24+ hours have passed
        if (now - self.last_day_refill).total_seconds() >= 86400:
            self.day_tokens = self.calls_per_day
            self.last_day_refill = now

        # Check if we have tokens available
        if self.minute_tokens <= 0:
            # Wait for minute bucket to refill
            wait_seconds = 60 - (now - self.last_minute_refill).total_seconds()
            if wait_seconds > 0:
                print(f"[Alpha Vantage] Rate limit: waiting {wait_seconds:.1f}s for minute bucket refill")
                await asyncio.sleep(wait_seconds)
                # Recursively try again after waiting
                return await self.acquire()

        if self.day_tokens <= 0:
            raise Exception("Alpha Vantage daily rate limit exceeded (100 calls/day)")

        # Consume tokens from both buckets
        self.minute_tokens -= 1
        self.day_tokens -= 1


class AlphaVantageService:
    """Service for fetching market data from Alpha Vantage API"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, redis_client=None):
        """
        Initialize Alpha Vantage service

        Args:
            api_key: Alpha Vantage API key
            redis_client: Optional Redis client for caching
        """
        self.api_key = api_key
        self.rate_limiter = AlphaVantageRateLimiter()
        self.redis_client = redis_client

        # Cache TTLs in seconds
        self.cache_ttl = {
            'quote': 60,      # 1 minute for live quotes
            'daily': 3600,    # 1 hour for daily historical
            'intraday': 300,  # 5 minutes for intraday
        }

    async def get_quote(self, symbol: str) -> AlphaVantagePriceData:
        """
        Get real-time quote for a symbol using GLOBAL_QUOTE function

        Args:
            symbol: Stock ticker symbol (e.g., "IBM", "AAPL")

        Returns:
            AlphaVantagePriceData with current price and metadata

        Raises:
            Exception: When API returns no data or an error
        """
        cache_key = f"av:quote:{symbol}"

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return self._deserialize_price_data(cached)

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Fetch from API
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                data = await response.json()

        # Parse response
        if 'Global Quote' not in data or not data['Global Quote']:
            raise Exception(f"No quote data for {symbol}")

        quote = data['Global Quote']

        price_data = AlphaVantagePriceData(
            symbol=symbol,
            current_price=Decimal(quote['05. price']),
            previous_close=Decimal(quote['08. previous close']),
            change=Decimal(quote['09. change']),
            change_percent=Decimal(quote['10. change percent'].rstrip('%')),
            volume=int(quote['06. volume']),
            last_updated=datetime.now()
        )

        # Cache result
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl['quote'],
                self._serialize_price_data(price_data)
            )

        return price_data

    async def get_historical_daily(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[datetime, Decimal]:
        """
        Get historical daily closing prices using TIME_SERIES_DAILY function

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            Dictionary mapping datetime -> closing price

        Raises:
            Exception: When API returns no data or an error
        """
        cache_key = f"av:daily:{symbol}:{start_date.date()}:{end_date.date()}"

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return self._deserialize_historical_data(cached)

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Fetch from API
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': 'full',  # Get all available data
            'apikey': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                data = await response.json()

        # Parse response
        if 'Time Series (Daily)' not in data:
            raise Exception(f"No daily data for {symbol}")

        time_series = data['Time Series (Daily)']
        prices = {}

        # Filter to requested date range
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if start_date <= date <= end_date:
                prices[date] = Decimal(values['4. close'])

        # Cache result
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl['daily'],
                self._serialize_historical_data(prices)
            )

        return prices

    async def get_crypto_quote(self, symbol: str, market: str = 'USD') -> AlphaVantagePriceData:
        """
        Get real-time quote for cryptocurrency using CURRENCY_EXCHANGE_RATE function

        Args:
            symbol: Crypto symbol (e.g., "BTC", "ETH")
            market: Market currency (default: "USD", can be "EUR")

        Returns:
            AlphaVantagePriceData with current exchange rate

        Raises:
            Exception: When API returns no data or an error
        """
        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Fetch from API
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': symbol,
            'to_currency': market,
            'apikey': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                data = await response.json()

        # Parse response
        if 'Realtime Currency Exchange Rate' not in data:
            raise Exception(f"No crypto data for {symbol}/{market}")

        rate_data = data['Realtime Currency Exchange Rate']

        return AlphaVantagePriceData(
            symbol=symbol,
            current_price=Decimal(rate_data['5. Exchange Rate']),
            previous_close=Decimal('0'),  # Not provided by this endpoint
            change=Decimal('0'),
            change_percent=Decimal('0'),
            volume=0,
            last_updated=datetime.now(),
            price_currency=market
        )

    def _serialize_price_data(self, price_data: AlphaVantagePriceData) -> str:
        """Serialize price data to JSON for caching"""
        return json.dumps({
            'symbol': price_data.symbol,
            'current_price': str(price_data.current_price),
            'previous_close': str(price_data.previous_close),
            'change': str(price_data.change),
            'change_percent': str(price_data.change_percent),
            'volume': price_data.volume,
            'last_updated': price_data.last_updated.isoformat(),
            'asset_name': price_data.asset_name,
            'price_currency': price_data.price_currency
        })

    def _deserialize_price_data(self, data: str) -> AlphaVantagePriceData:
        """Deserialize price data from JSON cache"""
        obj = json.loads(data)
        return AlphaVantagePriceData(
            symbol=obj['symbol'],
            current_price=Decimal(obj['current_price']),
            previous_close=Decimal(obj['previous_close']),
            change=Decimal(obj['change']),
            change_percent=Decimal(obj['change_percent']),
            volume=obj['volume'],
            last_updated=datetime.fromisoformat(obj['last_updated']),
            asset_name=obj.get('asset_name'),
            price_currency=obj.get('price_currency', 'USD')
        )

    def _serialize_historical_data(self, prices: Dict[datetime, Decimal]) -> str:
        """Serialize historical price data to JSON for caching"""
        return json.dumps({
            date.isoformat(): str(price)
            for date, price in prices.items()
        })

    def _deserialize_historical_data(self, data: str) -> Dict[datetime, Decimal]:
        """Deserialize historical price data from JSON cache"""
        obj = json.loads(data)
        return {
            datetime.fromisoformat(date_str): Decimal(price_str)
            for date_str, price_str in obj.items()
        }
