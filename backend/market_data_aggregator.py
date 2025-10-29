# ABOUTME: Intelligent market data aggregator with fallback logic and circuit breaker
# ABOUTME: Routes requests between Twelve Data, Yahoo Finance, and Alpha Vantage based on availability and performance

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import json


class DataProvider(Enum):
    """Available market data providers"""
    TWELVE_DATA = "twelvedata"
    YAHOO_FINANCE = "yahoo"
    ALPHA_VANTAGE = "alphavantage"
    CACHE = "cache"


class MarketDataAggregator:
    """
    Intelligent market data aggregator with fallback logic.

    Features:
    - Automatic fallback: Twelve Data → Yahoo Finance → Alpha Vantage → Cache
    - Circuit breaker pattern to avoid hammering failed providers
    - Twelve Data prioritized for European ETFs (best coverage)
    - Provider statistics tracking for monitoring
    """

    def __init__(
        self,
        yahoo_service,
        alpha_vantage_service,
        twelve_data_service=None,
        redis_client=None
    ):
        """
        Initialize market data aggregator

        Args:
            yahoo_service: YahooFinanceService instance
            alpha_vantage_service: AlphaVantageService instance
            twelve_data_service: Optional TwelveDataService instance (primary for European stocks)
            redis_client: Optional Redis client for caching
        """
        self.twelve_data = twelve_data_service
        self.yahoo = yahoo_service
        self.alpha_vantage = alpha_vantage_service
        self.redis = redis_client

        # Provider metrics tracking
        self.provider_stats = {
            DataProvider.TWELVE_DATA: {'success': 0, 'failure': 0},
            DataProvider.YAHOO_FINANCE: {'success': 0, 'failure': 0},
            DataProvider.ALPHA_VANTAGE: {'success': 0, 'failure': 0},
            DataProvider.CACHE: {'success': 0, 'failure': 0}
        }

        # Circuit breaker: Track consecutive failures
        self.circuit_breaker = {
            DataProvider.TWELVE_DATA: {'failures': 0, 'open_until': None},
            DataProvider.YAHOO_FINANCE: {'failures': 0, 'open_until': None},
            DataProvider.ALPHA_VANTAGE: {'failures': 0, 'open_until': None}
        }

        self.circuit_breaker_threshold = 5  # Open circuit after 5 consecutive failures
        self.circuit_breaker_timeout = 300  # 5 minutes in seconds

    def _is_european_etf(self, symbol: str) -> bool:
        """
        Check if symbol is a European ETF based on exchange suffix

        Args:
            symbol: Stock ticker symbol

        Returns:
            True if symbol has European exchange suffix
        """
        european_suffixes = ['.BE', '.PA', '.DE', '.MI', '.MC']
        return any(symbol.endswith(suffix) for suffix in european_suffixes)

    def _is_circuit_open(self, provider: DataProvider) -> bool:
        """
        Check if circuit breaker is open for provider

        Args:
            provider: The data provider to check

        Returns:
            True if circuit is open (provider should be skipped)
        """
        if provider not in self.circuit_breaker:
            return False

        breaker = self.circuit_breaker[provider]

        # Check if circuit is currently open
        if breaker['open_until'] and datetime.now() < breaker['open_until']:
            return True

        # Reset circuit if timeout expired
        if breaker['open_until'] and datetime.now() >= breaker['open_until']:
            breaker['failures'] = 0
            breaker['open_until'] = None

        return False

    def _record_failure(self, provider: DataProvider):
        """
        Record provider failure and potentially open circuit

        Args:
            provider: The provider that failed
        """
        self.provider_stats[provider]['failure'] += 1

        breaker = self.circuit_breaker.get(provider)
        if breaker is not None:
            breaker['failures'] += 1

            # Open circuit if threshold reached
            if breaker['failures'] >= self.circuit_breaker_threshold:
                breaker['open_until'] = datetime.now() + timedelta(seconds=self.circuit_breaker_timeout)
                print(
                    f"[Circuit Breaker] {provider.value} circuit opened for "
                    f"{self.circuit_breaker_timeout}s"
                )

    def _record_success(self, provider: DataProvider):
        """
        Record provider success and reset circuit

        Args:
            provider: The provider that succeeded
        """
        self.provider_stats[provider]['success'] += 1

        breaker = self.circuit_breaker.get(provider)
        if breaker is not None:
            breaker['failures'] = 0
            breaker['open_until'] = None

    async def get_quote(self, symbol: str) -> Tuple[Optional[object], Optional[DataProvider]]:
        """
        Get quote with intelligent fallback logic

        Tries providers in order with Twelve Data prioritized:
        - All symbols: Twelve Data → Yahoo → Alpha Vantage → Cache

        Args:
            symbol: Stock/crypto ticker symbol

        Returns:
            Tuple of (price_data, provider_used) or (None, None) if all fail
        """
        # Build provider list with Twelve Data first (if available)
        providers = []
        if self.twelve_data:
            providers.append(DataProvider.TWELVE_DATA)
        providers.extend([DataProvider.YAHOO_FINANCE, DataProvider.ALPHA_VANTAGE])

        # Try each provider in order
        for provider in providers:
            # Skip if circuit breaker is open
            if self._is_circuit_open(provider):
                print(f"[Fallback] Skipping {provider.value} (circuit breaker open)")
                continue

            try:
                if provider == DataProvider.TWELVE_DATA:
                    price_data = await self.twelve_data.get_quote(symbol)
                elif provider == DataProvider.YAHOO_FINANCE:
                    price_data = await self.yahoo.get_quote(symbol)
                elif provider == DataProvider.ALPHA_VANTAGE:
                    price_data = await self.alpha_vantage.get_quote(symbol)

                if price_data:
                    self._record_success(provider)
                    print(f"[Fallback] {symbol} fetched from {provider.value}")
                    return price_data, provider

            except Exception as e:
                self._record_failure(provider)
                print(f"[Fallback] {provider.value} failed for {symbol}: {e}")
                continue

        # All providers failed - try cache
        if self.redis:
            try:
                cached = await self.redis.get(f"market:quote:{symbol}")
                if cached:
                    self._record_success(DataProvider.CACHE)
                    print(f"[Fallback] {symbol} loaded from cache")
                    price_data = self._deserialize_price_data(cached)
                    return price_data, DataProvider.CACHE
            except Exception as e:
                print(f"[Fallback] Cache failed for {symbol}: {e}")

        # Complete failure
        print(f"[Fallback] All providers failed for {symbol}")
        return None, None

    async def get_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[Dict[datetime, Decimal], Optional[DataProvider]]:
        """
        Get historical prices with fallback logic

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            Tuple of (price_dict, provider_used) or ({}, None) if all fail
        """
        # Build provider list with Twelve Data first (if available)
        providers = []
        if self.twelve_data:
            providers.append(DataProvider.TWELVE_DATA)
        providers.extend([DataProvider.YAHOO_FINANCE, DataProvider.ALPHA_VANTAGE])

        for provider in providers:
            # Skip if circuit breaker is open
            if self._is_circuit_open(provider):
                print(f"[Fallback] Skipping {provider.value} for historical (circuit breaker open)")
                continue

            try:
                if provider == DataProvider.TWELVE_DATA:
                    prices = await self.twelve_data.get_historical_daily(symbol, start_date, end_date)
                    if prices:
                        self._record_success(provider)
                        print(f"[Fallback] {symbol} historical from {provider.value}")
                        return prices, provider

                elif provider == DataProvider.YAHOO_FINANCE:
                    prices = await self.yahoo.get_historical_prices([symbol], start_date, end_date)
                    if symbol in prices and prices[symbol]:
                        self._record_success(provider)
                        print(f"[Fallback] {symbol} historical from {provider.value}")
                        return prices[symbol], provider

                elif provider == DataProvider.ALPHA_VANTAGE:
                    prices = await self.alpha_vantage.get_historical_daily(symbol, start_date, end_date)
                    if prices:
                        self._record_success(provider)
                        print(f"[Fallback] {symbol} historical from {provider.value}")
                        return prices, provider

            except Exception as e:
                self._record_failure(provider)
                print(f"[Fallback] {provider.value} historical failed for {symbol}: {e}")
                continue

        # All failed
        print(f"[Fallback] All providers failed for {symbol} historical data")
        return {}, None

    def get_provider_stats(self) -> Dict:
        """
        Get comprehensive provider statistics for monitoring

        Returns:
            Dictionary with provider stats and circuit breaker status
        """
        return {
            'stats': self.provider_stats,
            'circuit_breakers': {
                provider.value: {
                    'failures': breaker['failures'],
                    'open': breaker['open_until'] is not None,
                    'open_until': breaker['open_until'].isoformat() if breaker['open_until'] else None
                }
                for provider, breaker in self.circuit_breaker.items()
            }
        }

    def _deserialize_price_data(self, data: str) -> object:
        """
        Deserialize price data from JSON cache

        Args:
            data: JSON string from cache

        Returns:
            PriceData object
        """
        from yahoo_finance_service import PriceData

        obj = json.loads(data)
        return PriceData(
            ticker=obj.get('ticker', obj.get('symbol')),  # Support both ticker and symbol keys
            current_price=Decimal(obj['current_price']),
            previous_close=Decimal(obj['previous_close']),
            day_change=Decimal(obj.get('change', obj.get('day_change', '0'))),
            day_change_percent=Decimal(obj.get('change_percent', obj.get('day_change_percent', '0'))),
            volume=obj['volume'],
            bid=None,
            ask=None,
            last_updated=datetime.fromisoformat(obj['last_updated']),
            market_state='unknown',
            asset_name=obj.get('asset_name'),
            price_currency=obj.get('price_currency', 'USD')
        )
