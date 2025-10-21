# ABOUTME: Tests for currency conversion service
# ABOUTME: Verifies exchange rate fetching and multi-currency portfolio calculations

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from currency_converter import CurrencyConverter, ExchangeRate, PortfolioCurrencyConverter


class TestCurrencyConverter:
    """Test currency conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_same_currency(self):
        """Test converting amount in same currency returns unchanged"""
        converter = CurrencyConverter(base_currency="USD")

        result = await converter.convert(Decimal("100.00"), "USD", "USD")
        assert result == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_convert_to_base_currency(self):
        """Test converting to base currency"""
        converter = CurrencyConverter(base_currency="USD")

        # Mock exchange rate EUR -> USD = 1.10
        with patch.object(converter, 'get_exchange_rate', return_value=Decimal("1.10")):
            result = await converter.convert(Decimal("100.00"), "EUR", "USD")
            assert result == Decimal("110.00")

    @pytest.mark.asyncio
    async def test_convert_from_base_currency(self):
        """Test converting from base currency"""
        converter = CurrencyConverter(base_currency="USD")

        # Mock exchange rate USD -> EUR = 0.91 (inverse of 1.10)
        with patch.object(converter, 'get_exchange_rate', return_value=Decimal("0.91")):
            result = await converter.convert(Decimal("110.00"), "USD", "EUR")
            expected = Decimal("100.10")
            assert abs(result - expected) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_convert_between_non_base_currencies(self):
        """Test converting between two non-base currencies via base"""
        converter = CurrencyConverter(base_currency="USD")

        # EUR -> GBP via USD (triangulation)
        # EUR -> USD = 1.10, USD -> GBP = 0.79
        # So EUR -> GBP = 1.10 * 0.79 = 0.869
        async def mock_fetch_rate(from_curr, to_curr):
            # Direct EUR->GBP not available, will trigger triangulation
            if from_curr == "EUR" and to_curr == "GBP":
                raise ValueError("Direct rate not available")
            elif from_curr == "EUR" and to_curr == "USD":
                return Decimal("1.10")
            elif from_curr == "USD" and to_curr == "GBP":
                return Decimal("0.79")
            return Decimal("1.0")

        with patch.object(converter, 'fetch_exchange_rate', side_effect=mock_fetch_rate):
            result = await converter.convert(Decimal("100.00"), "EUR", "GBP")
            expected = Decimal("86.90")
            assert abs(result - expected) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_convert_defaults_to_base_currency(self):
        """Test that convert uses base currency as default target"""
        converter = CurrencyConverter(base_currency="USD")

        with patch.object(converter, 'get_exchange_rate', return_value=Decimal("1.10")):
            result = await converter.convert(Decimal("100.00"), "EUR")
            assert result == Decimal("110.00")

    @pytest.mark.asyncio
    async def test_fetch_exchange_rate_from_yahoo(self):
        """Test fetching real exchange rate from Yahoo Finance"""
        converter = CurrencyConverter(base_currency="USD")

        # This tests real API - may be slow or fail if Yahoo is down
        # Mock it for CI/CD stability
        mock_ticker = Mock()
        mock_ticker.info = {
            'regularMarketPrice': 1.10,
            'ask': 1.11,
            'bid': 1.09
        }

        with patch('currency_converter.yf.Ticker', return_value=mock_ticker):
            rate = await converter.fetch_exchange_rate("EUR", "USD")
            assert rate > Decimal("0")
            assert rate == Decimal("1.10")

    @pytest.mark.asyncio
    async def test_cache_exchange_rates(self):
        """Test that exchange rates are cached"""
        converter = CurrencyConverter(base_currency="USD", cache_duration=60)

        mock_ticker = Mock()
        mock_ticker.info = {'regularMarketPrice': 1.10}

        with patch('currency_converter.yf.Ticker', return_value=mock_ticker) as mock_yf:
            # First call - should fetch
            rate1 = await converter.fetch_exchange_rate("EUR", "USD")
            assert mock_yf.call_count == 1

            # Second call - should use cache
            rate2 = await converter.fetch_exchange_rate("EUR", "USD")
            assert mock_yf.call_count == 1  # No additional call
            assert rate1 == rate2

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test that cache expires after duration"""
        converter = CurrencyConverter(base_currency="USD", cache_duration=0.1)

        mock_ticker = Mock()
        mock_ticker.info = {'regularMarketPrice': 1.10}

        with patch('currency_converter.yf.Ticker', return_value=mock_ticker) as mock_yf:
            # First call
            await converter.fetch_exchange_rate("EUR", "USD")
            assert mock_yf.call_count == 1

            # Wait for cache to expire
            import asyncio
            await asyncio.sleep(0.2)

            # Second call - should fetch again
            await converter.fetch_exchange_rate("EUR", "USD")
            assert mock_yf.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_missing_exchange_rate(self):
        """Test handling when exchange rate is unavailable"""
        converter = CurrencyConverter(base_currency="USD")

        mock_ticker = Mock()
        mock_ticker.info = {}  # No price data

        with patch('currency_converter.yf.Ticker', return_value=mock_ticker):
            with pytest.raises(ValueError, match="Could not fetch exchange rate"):
                await converter.fetch_exchange_rate("XXX", "USD")

    @pytest.mark.asyncio
    async def test_convert_with_precision(self):
        """Test that conversions maintain decimal precision"""
        converter = CurrencyConverter(base_currency="USD")

        # Test with fractional amounts and rates
        with patch.object(converter, 'get_exchange_rate', return_value=Decimal("1.23456789")):
            result = await converter.convert(Decimal("123.456789"), "EUR", "USD")
            # Should maintain precision
            expected = Decimal("123.456789") * Decimal("1.23456789")
            assert abs(result - expected) < Decimal("0.00000001")

    @pytest.mark.asyncio
    async def test_get_supported_currencies(self):
        """Test getting list of supported currencies"""
        converter = CurrencyConverter(base_currency="USD")

        currencies = converter.get_supported_currencies()
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "GBP" in currencies
        assert len(currencies) > 5

    @pytest.mark.asyncio
    async def test_convert_zero_amount(self):
        """Test converting zero amount"""
        converter = CurrencyConverter(base_currency="USD")

        with patch.object(converter, 'get_exchange_rate', return_value=Decimal("1.10")):
            result = await converter.convert(Decimal("0"), "EUR", "USD")
            assert result == Decimal("0")

    @pytest.mark.asyncio
    async def test_convert_negative_amount(self):
        """Test converting negative amount (for losses)"""
        converter = CurrencyConverter(base_currency="USD")

        with patch.object(converter, 'get_exchange_rate', return_value=Decimal("1.10")):
            result = await converter.convert(Decimal("-50.00"), "EUR", "USD")
            assert result == Decimal("-55.00")

    @pytest.mark.asyncio
    async def test_exchange_rate_model(self):
        """Test ExchangeRate dataclass"""
        rate = ExchangeRate(
            from_currency="EUR",
            to_currency="USD",
            rate=Decimal("1.10"),
            timestamp=datetime.now(),
            source="Yahoo Finance"
        )

        assert rate.from_currency == "EUR"
        assert rate.to_currency == "USD"
        assert rate.rate == Decimal("1.10")
        assert rate.source == "Yahoo Finance"

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing exchange rate cache"""
        converter = CurrencyConverter(base_currency="USD")

        mock_ticker = Mock()
        mock_ticker.info = {'regularMarketPrice': 1.10}

        with patch('currency_converter.yf.Ticker', return_value=mock_ticker) as mock_yf:
            # Fetch and cache
            await converter.fetch_exchange_rate("EUR", "USD")
            assert mock_yf.call_count == 1

            # Clear cache
            converter.clear_cache()

            # Should fetch again
            await converter.fetch_exchange_rate("EUR", "USD")
            assert mock_yf.call_count == 2


class TestPortfolioCurrencyConverter:
    """Test portfolio-specific currency conversion"""

    @pytest.mark.asyncio
    async def test_convert_position(self):
        """Test converting a single position"""
        converter = PortfolioCurrencyConverter(base_currency="USD")

        with patch.object(converter.converter, 'fetch_exchange_rate', return_value=Decimal("1.10")):
            result = await converter.convert_position(Decimal("1000.00"), "EUR")
            assert result == Decimal("1100.00")

    @pytest.mark.asyncio
    async def test_convert_portfolio(self):
        """Test converting entire portfolio"""
        converter = PortfolioCurrencyConverter(base_currency="USD")

        positions = [
            {"symbol": "AAPL", "value": 1000, "currency": "USD"},
            {"symbol": "VOD", "value": 500, "currency": "GBP"},
            {"symbol": "SAP", "value": 750, "currency": "EUR"},
        ]

        # Mock exchange rates
        async def mock_fetch_rate(from_curr, to_curr):
            rates = {
                ("GBP", "USD"): Decimal("1.27"),
                ("EUR", "USD"): Decimal("1.10"),
            }
            return rates.get((from_curr, to_curr), Decimal("1.0"))

        with patch.object(converter.converter, 'fetch_exchange_rate', side_effect=mock_fetch_rate):
            result = await converter.convert_portfolio(positions)

            # AAPL: 1000 USD
            # VOD: 500 * 1.27 = 635 USD
            # SAP: 750 * 1.10 = 825 USD
            # Total: 2460 USD
            assert result["total_value"] == 2460.0
            assert result["base_currency"] == "USD"
            assert len(result["positions"]) == 3

    @pytest.mark.asyncio
    async def test_get_rates_for_portfolio(self):
        """Test getting exchange rates for all currencies"""
        converter = PortfolioCurrencyConverter(base_currency="USD")

        currencies = ["USD", "EUR", "GBP"]

        async def mock_fetch_rate(from_curr, to_curr):
            rates = {
                ("EUR", "USD"): Decimal("1.10"),
                ("GBP", "USD"): Decimal("1.27"),
            }
            return rates.get((from_curr, to_curr), Decimal("1.0"))

        with patch.object(converter.converter, 'fetch_exchange_rate', side_effect=mock_fetch_rate):
            rates = await converter.get_rates_for_portfolio(currencies)

            assert rates["USD"] == Decimal("1.0")
            assert rates["EUR"] == Decimal("1.10")
            assert rates["GBP"] == Decimal("1.27")

    @pytest.mark.asyncio
    async def test_get_rates_handles_missing(self):
        """Test that missing rates use fallback"""
        converter = PortfolioCurrencyConverter(base_currency="USD")

        currencies = ["USD", "XXX"]  # XXX is not a real currency

        async def mock_fetch_rate(from_curr, to_curr):
            if from_curr == "XXX":
                raise ValueError("Unknown currency")
            return Decimal("1.0")

        with patch.object(converter.converter, 'fetch_exchange_rate', side_effect=mock_fetch_rate):
            rates = await converter.get_rates_for_portfolio(currencies)

            assert rates["USD"] == Decimal("1.0")
            assert rates["XXX"] == Decimal("1.0")  # Fallback
