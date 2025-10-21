# ABOUTME: Currency conversion service for multi-currency portfolio support
# ABOUTME: Fetches exchange rates from Yahoo Finance with caching

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import yfinance as yf


# Major currency pairs supported
SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
    "CNY", "HKD", "SGD", "SEK", "NOK", "DKK", "PLN", "CZK"
]


@dataclass
class ExchangeRate:
    """Exchange rate data"""
    from_currency: str
    to_currency: str
    rate: Decimal
    timestamp: datetime
    source: str = "Yahoo Finance"


class CurrencyConverter:
    """
    Currency conversion service with caching.

    Fetches exchange rates from Yahoo Finance and caches them
    for performance. Supports conversion between any two currencies
    via base currency triangulation.
    """

    def __init__(self, base_currency: str = "USD", cache_duration: int = 3600):
        """
        Initialize currency converter.

        Args:
            base_currency: Base currency for conversions (default: USD)
            cache_duration: Cache duration in seconds (default: 1 hour)
        """
        self.base_currency = base_currency.upper()
        self.cache_duration = cache_duration
        self._cache: Dict[str, tuple[Decimal, float]] = {}

    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: Optional[str] = None
    ) -> Decimal:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., EUR)
            to_currency: Target currency code (defaults to base_currency)

        Returns:
            Converted amount in target currency
        """
        if to_currency is None:
            to_currency = self.base_currency

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # No conversion needed for same currency
        if from_currency == to_currency:
            return amount

        # Get exchange rate
        rate = await self.get_exchange_rate(from_currency, to_currency)

        # Convert
        converted = amount * rate

        return converted

    async def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Get exchange rate between two currencies.

        Uses triangulation via base currency if direct rate unavailable.

        Args:
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Exchange rate
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return Decimal("1.0")

        # Try direct conversion first
        try:
            rate = await self.fetch_exchange_rate(from_currency, to_currency)
            return rate
        except ValueError:
            # If direct conversion fails, try triangulation via base currency
            if from_currency != self.base_currency and to_currency != self.base_currency:
                try:
                    # Convert from_currency -> base -> to_currency
                    rate_to_base = await self.fetch_exchange_rate(from_currency, self.base_currency)
                    rate_from_base = await self.fetch_exchange_rate(self.base_currency, to_currency)
                    return rate_to_base * rate_from_base
                except ValueError:
                    raise ValueError(
                        f"Could not convert {from_currency} to {to_currency} "
                        f"(neither direct nor via {self.base_currency})"
                    )
            raise

    async def fetch_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Fetch exchange rate from Yahoo Finance (with caching).

        Args:
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Exchange rate

        Raises:
            ValueError: If rate cannot be fetched
        """
        cache_key = f"{from_currency}_{to_currency}"

        # Check cache
        if cache_key in self._cache:
            rate, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return rate

        # Fetch from Yahoo Finance
        # Yahoo uses format like "EURUSD=X" for currency pairs
        ticker_symbol = f"{from_currency}{to_currency}=X"

        try:
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, ticker_symbol)

            # Get current price
            info = await loop.run_in_executor(None, lambda: ticker.info)

            # Try multiple price fields
            price = None
            for field in ['regularMarketPrice', 'ask', 'bid', 'previousClose']:
                if field in info and info[field]:
                    price = info[field]
                    break

            if price is None or price == 0:
                raise ValueError(f"Could not fetch exchange rate for {from_currency}/{to_currency}")

            rate = Decimal(str(price))

            # Cache the rate
            self._cache[cache_key] = (rate, time.time())

            return rate

        except Exception as e:
            # If direct fetch fails, try inverse
            try:
                inverse_key = f"{to_currency}_{from_currency}"
                if inverse_key in self._cache:
                    inverse_rate, timestamp = self._cache[inverse_key]
                    if time.time() - timestamp < self.cache_duration:
                        return Decimal("1.0") / inverse_rate

                raise ValueError(f"Could not fetch exchange rate for {from_currency}/{to_currency}: {e}")
            except:
                raise ValueError(f"Could not fetch exchange rate for {from_currency}/{to_currency}: {e}")

    def get_supported_currencies(self) -> List[str]:
        """
        Get list of supported currency codes.

        Returns:
            List of currency codes
        """
        return SUPPORTED_CURRENCIES.copy()

    def clear_cache(self):
        """Clear exchange rate cache"""
        self._cache.clear()

    def get_cache_info(self) -> Dict:
        """
        Get information about cached rates.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_pairs": len(self._cache),
            "cache_duration": self.cache_duration,
            "pairs": list(self._cache.keys())
        }


class PortfolioCurrencyConverter:
    """
    Portfolio-specific currency converter.

    Extends base converter with portfolio-specific functionality
    like converting entire positions and calculating totals.
    """

    def __init__(self, base_currency: str = "USD"):
        """
        Initialize portfolio currency converter.

        Args:
            base_currency: Base currency for portfolio
        """
        self.converter = CurrencyConverter(base_currency=base_currency)
        self.base_currency = base_currency

    async def convert_position(
        self,
        position_value: Decimal,
        position_currency: str
    ) -> Decimal:
        """
        Convert a position value to base currency.

        Args:
            position_value: Position value in original currency
            position_currency: Currency of the position

        Returns:
            Position value in base currency
        """
        return await self.converter.convert(
            position_value,
            position_currency,
            self.base_currency
        )

    async def convert_portfolio(
        self,
        positions: List[Dict]
    ) -> Dict:
        """
        Convert all positions to base currency and calculate totals.

        Args:
            positions: List of position dictionaries with 'value' and 'currency'

        Returns:
            Dictionary with converted values and totals
        """
        converted_positions = []
        total_value = Decimal("0")

        for position in positions:
            symbol = position.get("symbol")
            value = Decimal(str(position.get("value", 0)))
            currency = position.get("currency", self.base_currency)

            # Convert to base currency
            converted_value = await self.convert_position(value, currency)

            converted_positions.append({
                "symbol": symbol,
                "original_value": float(value),
                "original_currency": currency,
                "converted_value": float(converted_value),
                "base_currency": self.base_currency
            })

            total_value += converted_value

        return {
            "positions": converted_positions,
            "total_value": float(total_value),
            "base_currency": self.base_currency
        }

    async def get_rates_for_portfolio(
        self,
        currencies: List[str]
    ) -> Dict[str, Decimal]:
        """
        Get exchange rates for all currencies in portfolio.

        Args:
            currencies: List of currency codes

        Returns:
            Dictionary mapping currency to exchange rate vs base
        """
        rates = {}

        for currency in set(currencies):
            if currency == self.base_currency:
                rates[currency] = Decimal("1.0")
            else:
                try:
                    rate = await self.converter.get_exchange_rate(
                        currency,
                        self.base_currency
                    )
                    rates[currency] = rate
                except ValueError:
                    # If rate unavailable, use 1.0 as fallback
                    rates[currency] = Decimal("1.0")

        return rates
