# ABOUTME: Automated price update scheduler for stocks and cryptocurrencies
# ABOUTME: Handles scheduled updates with market hours awareness and WebSocket broadcasting

import asyncio
from datetime import datetime
from typing import Dict, Set, Optional
from apscheduler.schedulers.background import BackgroundScheduler

try:
    from .yahoo_finance_service import YahooFinanceService, PriceData
    from .price_cache import PriceCache
except ImportError:
    from yahoo_finance_service import YahooFinanceService, PriceData
    from price_cache import PriceCache


class PriceUpdateScheduler:
    """Scheduler for automatic price updates"""

    def __init__(self, price_service: YahooFinanceService, cache_service: PriceCache):
        """
        Initialize price update scheduler

        Args:
            price_service: Yahoo Finance service instance
            cache_service: Price cache instance
        """
        self.price_service = price_service
        self.cache = cache_service
        self.scheduler = None
        self.stock_tickers: Set[str] = set()
        self.crypto_symbols: Set[str] = set()
        self.last_update_times: Dict[str, datetime] = {}

        # Update intervals in seconds
        self.update_intervals = {
            'market_open': 60,      # 1 minute during market hours
            'market_closed': 300,   # 5 minutes when market closed
            'crypto': 60            # 1 minute always for crypto
        }

    def start(self):
        """Start the background scheduler"""
        if self.scheduler is not None:
            print("Scheduler already running")
            return

        self.scheduler = BackgroundScheduler()

        # Schedule stock updates
        self.scheduler.add_job(
            func=self._async_wrapper(self.update_stock_prices),
            trigger='interval',
            seconds=self._get_update_interval('stocks'),
            id='stock_update',
            replace_existing=True
        )

        # Schedule crypto updates (24/7)
        self.scheduler.add_job(
            func=self._async_wrapper(self.update_crypto_prices),
            trigger='interval',
            seconds=self.update_intervals['crypto'],
            id='crypto_update',
            replace_existing=True
        )

        self.scheduler.start()
        print("Price update scheduler started")

    def stop(self):
        """Stop the background scheduler"""
        if self.scheduler is not None:
            self.scheduler.shutdown()
            self.scheduler = None
            print("Price update scheduler stopped")

    def add_stock_tickers(self, tickers: list):
        """
        Add stock tickers to watch list

        Args:
            tickers: List of stock ticker symbols
        """
        self.stock_tickers.update(tickers)

    def remove_stock_ticker(self, ticker: str):
        """
        Remove stock ticker from watch list

        Args:
            ticker: Stock ticker symbol
        """
        self.stock_tickers.discard(ticker)

    def add_crypto_symbols(self, symbols: list):
        """
        Add crypto symbols to watch list

        Args:
            symbols: List of crypto symbols
        """
        self.crypto_symbols.update(symbols)

    def remove_crypto_symbol(self, symbol: str):
        """
        Remove crypto symbol from watch list

        Args:
            symbol: Crypto symbol
        """
        self.crypto_symbols.discard(symbol)

    async def update_stock_prices(self):
        """Update all stock prices"""
        if not self.stock_tickers:
            return

        try:
            print(f"Updating prices for {len(self.stock_tickers)} stocks...")

            # Fetch prices
            prices = await self.price_service.get_stock_prices(list(self.stock_tickers))

            if prices:
                # Store in cache
                self.cache.mset_prices(prices)
                self.last_update_times['stocks'] = datetime.now()
                print(f"Updated {len(prices)} stock prices")
            else:
                print("No stock prices fetched")

        except Exception as e:
            print(f"Error updating stock prices: {e}")

    async def update_crypto_prices(self):
        """Update all crypto prices"""
        if not self.crypto_symbols:
            return

        try:
            print(f"Updating prices for {len(self.crypto_symbols)} cryptocurrencies...")

            # Fetch prices
            prices = await self.price_service.get_crypto_prices(list(self.crypto_symbols))

            if prices:
                # Store in cache
                self.cache.mset_prices(prices)
                self.last_update_times['crypto'] = datetime.now()
                print(f"Updated {len(prices)} crypto prices")
            else:
                print("No crypto prices fetched")

        except Exception as e:
            print(f"Error updating crypto prices: {e}")

    async def force_update(self, asset_type: str):
        """
        Force immediate price update

        Args:
            asset_type: 'stocks' or 'crypto'
        """
        if asset_type == 'stocks':
            await self.update_stock_prices()
        elif asset_type == 'crypto':
            await self.update_crypto_prices()

    def get_last_update_time(self, asset_type: str) -> Optional[datetime]:
        """
        Get last update timestamp for asset type

        Args:
            asset_type: 'stocks' or 'crypto'

        Returns:
            Datetime of last update, or None if never updated
        """
        return self.last_update_times.get(asset_type)

    def _get_update_interval(self, asset_type: str) -> int:
        """
        Get update interval based on asset type and market state

        Args:
            asset_type: 'stocks' or 'crypto'

        Returns:
            Update interval in seconds
        """
        if asset_type == 'crypto':
            return self.update_intervals['crypto']

        # For stocks, check if market is open
        if self.price_service.is_market_open():
            return self.update_intervals['market_open']
        else:
            return self.update_intervals['market_closed']

    def _async_wrapper(self, coro_func):
        """
        Wrap async function for scheduler

        Args:
            coro_func: Async function to wrap

        Returns:
            Synchronous wrapper function
        """
        def wrapper():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro_func())
            finally:
                loop.close()
        return wrapper
