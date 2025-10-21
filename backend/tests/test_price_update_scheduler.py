# ABOUTME: Tests for automated price update scheduler
# ABOUTME: Tests scheduled updates, WebSocket broadcasting, and market hours handling

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime

try:
    from ..price_update_scheduler import PriceUpdateScheduler
    from ..yahoo_finance_service import PriceData
except ImportError:
    from price_update_scheduler import PriceUpdateScheduler
    from yahoo_finance_service import PriceData


class TestPriceUpdateScheduler:
    """Test price update scheduler"""

    @pytest.fixture
    def mock_price_service(self):
        """Create mock Yahoo Finance service"""
        service = AsyncMock()
        service.get_stock_prices = AsyncMock(return_value={})
        service.get_crypto_prices = AsyncMock(return_value={})
        service.is_market_open = Mock(return_value=True)
        return service

    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service"""
        cache = Mock()
        cache.mset_prices = Mock()
        cache.mget_prices = Mock(return_value={})
        return cache

    @pytest.fixture
    def scheduler(self, mock_price_service, mock_cache_service):
        """Create scheduler instance"""
        return PriceUpdateScheduler(mock_price_service, mock_cache_service)

    def test_scheduler_creation(self, scheduler):
        """Test creating scheduler"""
        assert scheduler is not None
        assert hasattr(scheduler, 'price_service')
        assert hasattr(scheduler, 'cache')
        assert hasattr(scheduler, 'update_intervals')

    def test_update_intervals_configuration(self, scheduler):
        """Test update intervals are properly configured"""
        assert scheduler.update_intervals['market_open'] == 60
        assert scheduler.update_intervals['market_closed'] == 300
        assert scheduler.update_intervals['crypto'] == 60

    @pytest.mark.asyncio
    async def test_update_stock_prices(self, scheduler, mock_price_service, mock_cache_service):
        """Test updating stock prices"""
        # Set up mock data
        sample_price = PriceData(
            ticker="AAPL",
            current_price=Decimal("150.25"),
            previous_close=Decimal("148.75"),
            day_change=Decimal("1.50"),
            day_change_percent=Decimal("1.01"),
            volume=1000000,
            bid=Decimal("150.20"),
            ask=Decimal("150.30"),
            last_updated=datetime.now(),
            market_state="open"
        )
        mock_price_service.get_stock_prices.return_value = {"AAPL": sample_price}

        # Add tickers to watch
        scheduler.add_stock_tickers(["AAPL"])

        # Trigger update
        await scheduler.update_stock_prices()

        # Verify service was called
        mock_price_service.get_stock_prices.assert_called_once()
        # Verify cache was updated
        mock_cache_service.mset_prices.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_crypto_prices(self, scheduler, mock_price_service, mock_cache_service):
        """Test updating crypto prices"""
        sample_price = PriceData(
            ticker="BTC-USD",
            current_price=Decimal("45000.00"),
            previous_close=Decimal("44500.00"),
            day_change=Decimal("500.00"),
            day_change_percent=Decimal("1.12"),
            volume=25000000000,
            bid=None,
            ask=None,
            last_updated=datetime.now(),
            market_state="open"
        )
        mock_price_service.get_crypto_prices.return_value = {"BTC": sample_price}

        scheduler.add_crypto_symbols(["BTC"])

        await scheduler.update_crypto_prices()

        mock_price_service.get_crypto_prices.assert_called_once()
        mock_cache_service.mset_prices.assert_called_once()

    def test_add_stock_tickers(self, scheduler):
        """Test adding stock tickers to watch list"""
        scheduler.add_stock_tickers(["AAPL", "TSLA"])

        assert "AAPL" in scheduler.stock_tickers
        assert "TSLA" in scheduler.stock_tickers

    def test_add_stock_tickers_no_duplicates(self, scheduler):
        """Test adding duplicate tickers doesn't create duplicates"""
        scheduler.add_stock_tickers(["AAPL"])
        scheduler.add_stock_tickers(["AAPL", "TSLA"])

        # Should be a set, so no duplicates
        assert len(scheduler.stock_tickers) == 2

    def test_add_crypto_symbols(self, scheduler):
        """Test adding crypto symbols to watch list"""
        scheduler.add_crypto_symbols(["BTC", "ETH"])

        assert "BTC" in scheduler.crypto_symbols
        assert "ETH" in scheduler.crypto_symbols

    def test_remove_stock_ticker(self, scheduler):
        """Test removing stock ticker"""
        scheduler.add_stock_tickers(["AAPL", "TSLA"])
        scheduler.remove_stock_ticker("AAPL")

        assert "AAPL" not in scheduler.stock_tickers
        assert "TSLA" in scheduler.stock_tickers

    def test_remove_crypto_symbol(self, scheduler):
        """Test removing crypto symbol"""
        scheduler.add_crypto_symbols(["BTC", "ETH"])
        scheduler.remove_crypto_symbol("BTC")

        assert "BTC" not in scheduler.crypto_symbols
        assert "ETH" in scheduler.crypto_symbols

    def test_get_stock_update_interval(self, scheduler, mock_price_service):
        """Test getting correct update interval based on market state"""
        mock_price_service.is_market_open.return_value = True
        interval = scheduler._get_update_interval('stocks')
        assert interval == 60

        mock_price_service.is_market_open.return_value = False
        interval = scheduler._get_update_interval('stocks')
        assert interval == 300

    def test_get_crypto_update_interval(self, scheduler):
        """Test crypto always updates at 60 seconds"""
        interval = scheduler._get_update_interval('crypto')
        assert interval == 60

    def test_start_scheduler(self, scheduler):
        """Test starting scheduler"""
        with patch('price_update_scheduler.BackgroundScheduler') as mock_sched_class:
            mock_sched = Mock()
            mock_sched.add_job = Mock()
            mock_sched.start = Mock()
            mock_sched_class.return_value = mock_sched

            scheduler.start()

            # Scheduler should be started
            mock_sched.start.assert_called_once()
            # Jobs should be added
            assert mock_sched.add_job.call_count == 2

    def test_stop_scheduler(self, scheduler):
        """Test stopping scheduler"""
        mock_sched = Mock()
        scheduler.scheduler = mock_sched

        scheduler.stop()

        mock_sched.shutdown.assert_called_once()
        # Scheduler should be set to None
        assert scheduler.scheduler is None

    @pytest.mark.asyncio
    async def test_update_with_empty_tickers(self, scheduler, mock_price_service):
        """Test update when no tickers are configured"""
        await scheduler.update_stock_prices()

        # Should not call API if no tickers
        mock_price_service.get_stock_prices.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_error_handling(self, scheduler, mock_price_service, mock_cache_service):
        """Test error handling during update"""
        mock_price_service.get_stock_prices.side_effect = Exception("API Error")
        scheduler.add_stock_tickers(["AAPL"])

        # Should not raise exception
        await scheduler.update_stock_prices()

        # Cache should not be called if fetch fails
        mock_cache_service.mset_prices.assert_not_called()

    def test_get_last_update_time(self, scheduler):
        """Test getting last update timestamp"""
        timestamp = scheduler.get_last_update_time('stocks')
        # Initially should be None or datetime
        assert timestamp is None or isinstance(timestamp, datetime)

    @pytest.mark.asyncio
    async def test_force_update(self, scheduler, mock_price_service, mock_cache_service):
        """Test forcing immediate update"""
        sample_price = PriceData(
            ticker="AAPL",
            current_price=Decimal("150.25"),
            previous_close=Decimal("148.75"),
            day_change=Decimal("1.50"),
            day_change_percent=Decimal("1.01"),
            volume=1000000,
            bid=Decimal("150.20"),
            ask=Decimal("150.30"),
            last_updated=datetime.now(),
            market_state="open"
        )
        mock_price_service.get_stock_prices.return_value = {"AAPL": sample_price}
        scheduler.add_stock_tickers(["AAPL"])

        await scheduler.force_update('stocks')

        mock_price_service.get_stock_prices.assert_called_once()
        mock_cache_service.mset_prices.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_update_crypto(self, scheduler, mock_price_service, mock_cache_service):
        """Test forcing crypto update"""
        sample_price = PriceData(
            ticker="BTC-USD",
            current_price=Decimal("45000.00"),
            previous_close=Decimal("44500.00"),
            day_change=Decimal("500.00"),
            day_change_percent=Decimal("1.12"),
            volume=25000000000,
            bid=None,
            ask=None,
            last_updated=datetime.now(),
            market_state="open"
        )
        mock_price_service.get_crypto_prices.return_value = {"BTC": sample_price}
        scheduler.add_crypto_symbols(["BTC"])

        await scheduler.force_update('crypto')

        mock_price_service.get_crypto_prices.assert_called_once()
        mock_cache_service.mset_prices.assert_called_once()

    def test_start_scheduler_already_running(self, scheduler):
        """Test starting scheduler when already running"""
        with patch('price_update_scheduler.BackgroundScheduler') as mock_sched_class:
            mock_sched = Mock()
            mock_sched.add_job = Mock()
            mock_sched.start = Mock()
            mock_sched_class.return_value = mock_sched

            # Start once
            scheduler.start()
            mock_sched.start.assert_called_once()

            # Try to start again - should not create new scheduler
            scheduler.start()
            # Still only called once
            mock_sched.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_stock_prices_empty_result(self, scheduler, mock_price_service, mock_cache_service):
        """Test update when API returns empty result"""
        mock_price_service.get_stock_prices.return_value = {}
        scheduler.add_stock_tickers(["AAPL"])

        await scheduler.update_stock_prices()

        # Cache should not be called with empty results
        mock_cache_service.mset_prices.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_crypto_prices_empty_result(self, scheduler, mock_price_service, mock_cache_service):
        """Test crypto update when API returns empty result"""
        mock_price_service.get_crypto_prices.return_value = {}
        scheduler.add_crypto_symbols(["BTC"])

        await scheduler.update_crypto_prices()

        mock_cache_service.mset_prices.assert_not_called()
