# ABOUTME: Yahoo Finance integration for fetching live stock and crypto prices
# ABOUTME: Includes rate limiting, retry logic, and market hours detection

import asyncio
import time
from datetime import datetime, time as dt_time
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque

import yfinance as yf


# Cryptocurrency ticker mappings
CRYPTO_MAPPINGS = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'ADA': 'ADA-USD',
    'DOT': 'DOT-USD',
    'LINK': 'LINK-USD',
    'UNI': 'UNI-USD',
    'AAVE': 'AAVE-USD',
    'SOL': 'SOL-USD',
    'MATIC': 'MATIC-USD',
    'AVAX': 'AVAX-USD',
    'ATOM': 'ATOM-USD',
    'XRP': 'XRP-USD',
    'LTC': 'LTC-USD',
    'BCH': 'BCH-USD',
    'XLM': 'XLM-USD',
    'DOGE': 'DOGE-USD',
    'SHIB': 'SHIB-USD',
    'ALGO': 'ALGO-USD',
    'VET': 'VET-USD',
    'FTM': 'FTM-USD',
}

# ETF ticker mappings (European exchanges)
ETF_MAPPINGS = {
    'AMEM': 'AMEM.BE',  # Amundi MSCI Emerging Markets - Brussels
    'MWOQ': 'MWOQ.BE',  # Amundi MSCI World - Brussels
}


@dataclass
class PriceData:
    """Live price data from Yahoo Finance"""
    ticker: str
    current_price: Decimal
    previous_close: Decimal
    day_change: Decimal
    day_change_percent: Decimal
    volume: int
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    last_updated: datetime
    market_state: str  # 'open', 'closed', 'pre', 'post'
    asset_name: Optional[str] = None  # Full name (e.g., "MicroStrategy", "Bitcoin")


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, max_calls: int, period: int):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    async def acquire(self):
        """Acquire permission to make an API call"""
        now = time.time()

        # Remove calls outside the current period
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.period - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                # Recursively try again
                return await self.acquire()

        # Record this call
        self.calls.append(now)


class ExponentialBackoff:
    """Exponential backoff retry policy"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize backoff policy

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        return self.base_delay * (2 ** attempt)

    async def execute(self, func):
        """
        Execute function with retry logic

        Args:
            func: Async function to execute

        Returns:
            Result of function call

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                break

        # All retries exhausted
        raise last_exception


class YahooFinanceService:
    """Service for fetching live prices from Yahoo Finance"""

    def __init__(self):
        """Initialize Yahoo Finance service"""
        self.rate_limiter = RateLimiter(max_calls=100, period=60)
        self.retry_policy = ExponentialBackoff(max_retries=3)

    def _transform_ticker(self, ticker: str) -> str:
        """
        Transform ticker symbol to Yahoo Finance format

        Applies crypto and ETF mappings to convert internal symbols
        to Yahoo Finance-compatible ticker symbols.

        Args:
            ticker: Internal ticker symbol

        Returns:
            Yahoo Finance ticker symbol
        """
        # Check crypto mappings first
        if ticker in CRYPTO_MAPPINGS:
            return CRYPTO_MAPPINGS[ticker]

        # Check ETF mappings
        if ticker in ETF_MAPPINGS:
            return ETF_MAPPINGS[ticker]

        # Return as-is for standard stock tickers
        return ticker

    async def get_stock_prices(self, tickers: List[str]) -> Dict[str, PriceData]:
        """
        Fetch prices for multiple tickers

        Args:
            tickers: List of stock ticker symbols

        Returns:
            Dictionary mapping ticker to PriceData
        """
        result = {}

        # Batch process for efficiency
        if len(tickers) > 10:
            # Use batch API for large requests
            try:
                await self.rate_limiter.acquire()
                result = await self._batch_fetch_prices(tickers)
            except Exception as e:
                print(f"Batch fetch failed: {e}")
                # Fall back to individual fetches
                for ticker in tickers:
                    try:
                        price_data = await self.get_quote(ticker)
                        result[ticker] = price_data
                    except Exception as ticker_error:
                        print(f"Failed to fetch {ticker}: {ticker_error}")
                        continue
        else:
            # Individual fetches for small lists
            for ticker in tickers:
                try:
                    await self.rate_limiter.acquire()
                    price_data = await self.get_quote(ticker)
                    result[ticker] = price_data
                except Exception as e:
                    print(f"Failed to fetch {ticker}: {e}")
                    continue

        return result

    async def _batch_fetch_prices(self, tickers: List[str]) -> Dict[str, PriceData]:
        """
        Batch fetch prices using yfinance download

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary of ticker to PriceData
        """
        # Transform tickers to Yahoo Finance format
        ticker_mapping = {ticker: self._transform_ticker(ticker) for ticker in tickers}
        yf_tickers = list(ticker_mapping.values())

        async def fetch():
            # yfinance.download is synchronous, run in executor
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                lambda: yf.download(yf_tickers, period="1d", interval="1m", progress=False)
            )
            return data

        try:
            data = await self.retry_policy.execute(fetch)
        except Exception as e:
            print(f"Batch download failed: {e}")
            return {}

        # Parse batch results
        result = {}
        for original_ticker, yf_ticker in ticker_mapping.items():
            try:
                # Get detailed info for each ticker using transformed symbol
                ticker_obj = yf.Ticker(yf_ticker)
                info = ticker_obj.info

                if not info or 'regularMarketPrice' not in info:
                    continue

                # Use original ticker in response
                price_data = self._parse_ticker_info(original_ticker, info)
                result[original_ticker] = price_data
            except Exception as e:
                print(f"Failed to parse {original_ticker}: {e}")
                continue

        return result

    async def get_quote(self, ticker: str) -> PriceData:
        """
        Get detailed quote for a single ticker

        Args:
            ticker: Stock ticker symbol (will be transformed if needed)

        Returns:
            PriceData object

        Raises:
            Exception: If ticker is invalid or API fails
        """
        # Transform ticker to Yahoo Finance format
        yf_ticker = self._transform_ticker(ticker)

        async def fetch():
            # Run synchronous yfinance call in executor
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(
                None,
                yf.Ticker,
                yf_ticker
            )
            info = ticker_obj.info
            return info

        info = await self.retry_policy.execute(fetch)

        if not info or 'regularMarketPrice' not in info:
            raise ValueError(f"Invalid ticker or no data available: {ticker}")

        # Use original ticker in response, not transformed one
        return self._parse_ticker_info(ticker, info)

    def _parse_ticker_info(self, ticker: str, info: dict) -> PriceData:
        """
        Parse ticker info into PriceData

        Args:
            ticker: Ticker symbol
            info: Info dictionary from yfinance

        Returns:
            PriceData object
        """
        current_price = Decimal(str(info.get('regularMarketPrice', 0)))
        previous_close = Decimal(str(info.get('previousClose', 0)))
        day_change = current_price - previous_close
        day_change_percent = (day_change / previous_close * 100) if previous_close > 0 else Decimal(0)

        # Bid/Ask may not be available when market is closed
        bid = None
        ask = None
        if 'bid' in info and info['bid']:
            bid = Decimal(str(info['bid']))
        if 'ask' in info and info['ask']:
            ask = Decimal(str(info['ask']))

        # Normalize market state
        market_state_raw = info.get('marketState', 'CLOSED')
        market_state = self._normalize_market_state(market_state_raw)

        # Extract asset name - try shortName first, fallback to longName
        asset_name = info.get('shortName') or info.get('longName')

        return PriceData(
            ticker=ticker,
            current_price=current_price,
            previous_close=previous_close,
            day_change=day_change,
            day_change_percent=day_change_percent,
            volume=info.get('regularMarketVolume', 0),
            bid=bid,
            ask=ask,
            last_updated=datetime.now(),
            market_state=market_state,
            asset_name=asset_name
        )

    def _normalize_market_state(self, state: str) -> str:
        """
        Normalize market state string

        Args:
            state: Raw market state from Yahoo Finance

        Returns:
            Normalized state: 'open', 'closed', 'pre', 'post'
        """
        state_upper = state.upper()
        if state_upper == 'REGULAR':
            return 'open'
        elif state_upper == 'PRE':
            return 'pre'
        elif state_upper == 'POST':
            return 'post'
        else:
            return 'closed'

    def is_market_open(self) -> bool:
        """
        Check if US stock market is currently open

        Returns:
            True if market is open, False otherwise
        """
        now = datetime.now()

        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Market hours: 9:30 AM - 4:00 PM ET
        # TODO: This is a simplified check, real implementation should handle:
        # - Timezone conversion to ET
        # - Market holidays
        # - Half days
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)

        current_time = now.time()
        return market_open <= current_time <= market_close

    def normalize_crypto_ticker(self, symbol: str, currency: str = 'USD') -> str:
        """
        Normalize cryptocurrency ticker to Yahoo Finance format

        Args:
            symbol: Crypto symbol (e.g. 'BTC', 'ETH', or 'BTC-USD')
            currency: Target currency (e.g. 'USD', 'EUR', 'GBP')

        Returns:
            Yahoo Finance ticker format (e.g. 'BTC-USD' or 'BTC-EUR')
        """
        # If already in correct format with currency suffix, check if it matches
        if '-' in symbol:
            return symbol

        # Build ticker with specified currency
        return f"{symbol}-{currency}"

    async def get_crypto_prices(self, symbols: List[str], currency: str = 'USD') -> Dict[str, PriceData]:
        """
        Fetch prices for cryptocurrencies

        Args:
            symbols: List of crypto symbols (e.g. ['BTC', 'ETH'])
            currency: Target currency for prices (e.g. 'USD', 'EUR', 'GBP')

        Returns:
            Dictionary mapping symbol to PriceData
        """
        result = {}

        for symbol in symbols:
            try:
                await self.rate_limiter.acquire()

                # Normalize ticker with specified currency
                ticker = self.normalize_crypto_ticker(symbol, currency)

                # Fetch price data
                price_data = await self.get_quote(ticker)

                # Store with original symbol as key
                result[symbol] = price_data
            except Exception as e:
                print(f"Failed to fetch crypto {symbol}-{currency}: {e}")
                continue

        return result
