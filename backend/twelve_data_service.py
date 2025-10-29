# ABOUTME: Twelve Data API integration for European stock coverage and historical data
# ABOUTME: Provides fallback when Yahoo Finance/Alpha Vantage fail, supports 60+ markets

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass
import aiohttp
import json


@dataclass
class TwelveDataPriceData:
    """Price data from Twelve Data API"""
    symbol: str
    current_price: Decimal
    previous_close: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int
    last_updated: datetime
    asset_name: Optional[str] = None
    price_currency: str = 'USD'
    exchange: Optional[str] = None


class TwelveDataRateLimiter:
    """Token bucket rate limiter for Twelve Data API"""

    def __init__(self, calls_per_minute: int = 8, calls_per_day: int = 800):
        """
        Initialize rate limiter with token buckets

        Args:
            calls_per_minute: Maximum API calls per minute (default: 8 for Grow tier)
            calls_per_day: Maximum API calls per day (default: 800 for Grow tier)
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
                print(f"[Twelve Data] Rate limit: waiting {wait_seconds:.1f}s for minute bucket refill")
                await asyncio.sleep(wait_seconds)
                # Recursively try again after waiting
                return await self.acquire()

        if self.day_tokens <= 0:
            raise Exception("Twelve Data daily rate limit exceeded (800 calls/day)")

        # Consume tokens from both buckets
        self.minute_tokens -= 1
        self.day_tokens -= 1


class TwelveDataService:
    """Service for fetching market data from Twelve Data API"""

    BASE_URL = "https://api.twelvedata.com"

    # ETF exchange mappings (symbol -> exchange MIC code)
    # For European ETFs that need explicit exchange specification
    ETF_EXCHANGE_MAPPINGS = {
        'AMEM': 'XETR',  # Amundi MSCI Emerging Markets - Frankfurt
        'MWOQ': 'XETR',  # Amundi MSCI World - Frankfurt (if available)
    }

    def __init__(self, api_key: str, redis_client=None):
        """
        Initialize Twelve Data service

        Args:
            api_key: Twelve Data API key
            redis_client: Optional Redis client for caching
        """
        self.api_key = api_key
        self.rate_limiter = TwelveDataRateLimiter()
        self.redis_client = redis_client

        # Cache TTLs in seconds
        self.cache_ttl = {
            'quote': 60,      # 1 minute for live quotes
            'daily': 3600,    # 1 hour for daily historical
        }

    def _get_symbol_with_exchange(self, symbol: str) -> str:
        """
        Get symbol with exchange specification for API calls.

        Twelve Data uses colon notation: SYMBOL:EXCHANGE

        Args:
            symbol: Base symbol (e.g., "AMEM", "AAPL")

        Returns:
            Formatted symbol (e.g., "AMEM:XETR", "AAPL")
        """
        # Check if symbol needs exchange mapping
        if symbol in self.ETF_EXCHANGE_MAPPINGS:
            exchange = self.ETF_EXCHANGE_MAPPINGS[symbol]
            return f"{symbol}:{exchange}"

        # For US stocks, no exchange needed
        return symbol

    async def get_historical_daily(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[datetime, Decimal]:
        """
        Get historical daily closing prices using time_series endpoint

        Args:
            symbol: Stock ticker symbol (will add exchange if needed)
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            Dictionary mapping datetime -> closing price

        Raises:
            Exception: When API returns no data or an error
        """
        # Calculate number of days for outputsize
        days_requested = (end_date - start_date).days + 1
        output_size = min(days_requested, 5000)  # API max is 5000

        cache_key = f"td:daily:{symbol}:{start_date.date()}:{end_date.date()}"

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                print(f"[Twelve Data] Cache HIT for {symbol} ({days_requested} days)")
                return self._deserialize_historical_data(cached)

        # Get symbol with exchange if needed
        api_symbol = self._get_symbol_with_exchange(symbol)

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        print(f"[Twelve Data] Cache MISS - Fetching from API for {symbol}")
        # Fetch from API
        params = {
            'symbol': api_symbol,
            'interval': '1day',
            'outputsize': output_size,
            'apikey': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/time_series", params=params) as response:
                data = await response.json()

        # Check for errors
        if data.get('status') == 'error':
            raise Exception(f"Twelve Data error: {data.get('message', 'Unknown error')}")

        if 'values' not in data or not data['values']:
            raise Exception(f"No daily data for {symbol}")

        # Parse response
        prices = {}
        for value in data['values']:
            date = datetime.strptime(value['datetime'], '%Y-%m-%d')
            if start_date <= date <= end_date:
                prices[date] = Decimal(value['close'])

        # Cache result
        if self.redis_client and prices:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl['daily'],
                self._serialize_historical_data(prices)
            )

        return prices

    async def get_quote(self, symbol: str) -> TwelveDataPriceData:
        """
        Get real-time quote for a symbol using quote endpoint

        Args:
            symbol: Stock ticker symbol (will add exchange if needed)

        Returns:
            TwelveDataPriceData with current price and metadata

        Raises:
            Exception: When API returns no data or an error
        """
        cache_key = f"td:quote:{symbol}"

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return self._deserialize_price_data(cached)

        # Get symbol with exchange if needed
        api_symbol = self._get_symbol_with_exchange(symbol)

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        # Fetch from API
        params = {
            'symbol': api_symbol,
            'apikey': self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/quote", params=params) as response:
                data = await response.json()

        # Check for errors
        if data.get('status') == 'error':
            raise Exception(f"Twelve Data error: {data.get('message', 'Unknown error')}")

        if 'close' not in data:
            raise Exception(f"No quote data for {symbol}")

        # Calculate change from previous close
        current_price = Decimal(data['close'])
        previous_close = Decimal(data.get('previous_close', data['close']))
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close > 0 else Decimal(0)

        price_data = TwelveDataPriceData(
            symbol=symbol,
            current_price=current_price,
            previous_close=previous_close,
            change=change,
            change_percent=change_percent,
            volume=int(data.get('volume', 0)),
            last_updated=datetime.now(),
            asset_name=data.get('name'),
            price_currency=data.get('currency', 'USD'),
            exchange=data.get('exchange')
        )

        # Cache result
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl['quote'],
                self._serialize_price_data(price_data)
            )

        return price_data

    def _serialize_price_data(self, price_data: TwelveDataPriceData) -> str:
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
            'price_currency': price_data.price_currency,
            'exchange': price_data.exchange
        })

    def _deserialize_price_data(self, data: str) -> TwelveDataPriceData:
        """Deserialize price data from JSON cache"""
        obj = json.loads(data)
        return TwelveDataPriceData(
            symbol=obj['symbol'],
            current_price=Decimal(obj['current_price']),
            previous_close=Decimal(obj['previous_close']),
            change=Decimal(obj['change']),
            change_percent=Decimal(obj['change_percent']),
            volume=obj['volume'],
            last_updated=datetime.fromisoformat(obj['last_updated']),
            asset_name=obj.get('asset_name'),
            price_currency=obj.get('price_currency', 'USD'),
            exchange=obj.get('exchange')
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
