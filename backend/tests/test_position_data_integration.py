# ABOUTME: Integration tests for position data collection with real database
# ABOUTME: Uses SQLite in-memory database to verify actual database queries work correctly

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timedelta

from prompt_renderer import PromptDataCollector
from portfolio_service import PortfolioService
from yahoo_finance_service import YahooFinanceService
from models import Position, Transaction, AssetType, TransactionType
from sqlalchemy import select


@pytest_asyncio.fixture
async def sample_transactions(test_session):
    """Create sample transactions in the test database."""
    transactions = [
        Transaction(
            symbol="AAPL",
            transaction_date=datetime.utcnow() - timedelta(days=365),
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5.0"),
            price_per_unit=Decimal("140.00"),
            total_amount=Decimal("700.00"),
            currency="USD",
            asset_type=AssetType.STOCK
        ),
        Transaction(
            symbol="AAPL",
            transaction_date=datetime.utcnow() - timedelta(days=180),
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5.0"),
            price_per_unit=Decimal("160.00"),
            total_amount=Decimal("800.00"),
            currency="USD",
            asset_type=AssetType.STOCK
        ),
        Transaction(
            symbol="BTC",
            transaction_date=datetime.utcnow() - timedelta(days=200),
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("50000.00"),
            total_amount=Decimal("25000.00"),
            currency="USD",
            asset_type=AssetType.CRYPTO
        ),
    ]

    for tx in transactions:
        test_session.add(tx)

    await test_session.commit()
    return transactions


@pytest_asyncio.fixture
async def sample_positions(test_session):
    """Create sample positions in the test database."""
    positions = [
        Position(
            symbol="AAPL",
            asset_name="Apple Inc.",
            asset_type=AssetType.STOCK,
            quantity=Decimal("10.0"),
            avg_cost_basis=Decimal("150.00"),
            total_cost_basis=Decimal("1500.00"),
            current_price=Decimal("180.00"),
            current_value=Decimal("1800.00"),
            unrealized_pnl=Decimal("300.00"),
            unrealized_pnl_percent=Decimal("20.00")
        ),
        Position(
            symbol="BTC",
            asset_name="Bitcoin",
            asset_type=AssetType.CRYPTO,
            quantity=Decimal("0.5"),
            avg_cost_basis=Decimal("50000.00"),
            total_cost_basis=Decimal("25000.00"),
            current_price=Decimal("65000.00"),
            current_value=Decimal("32500.00"),
            unrealized_pnl=Decimal("7500.00"),
            unrealized_pnl_percent=Decimal("30.00")
        )
    ]

    for pos in positions:
        test_session.add(pos)

    await test_session.commit()
    return positions


class TestPositionDataIntegration:
    """Integration tests with real database for position data collection."""

    @pytest.mark.asyncio
    async def test_transaction_count_with_real_database(
        self,
        test_session,
        sample_transactions
    ):
        """Test getting transaction count from real database."""
        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Test AAPL with 2 transactions
        count = await collector._get_transaction_count("AAPL")
        assert count == 2

        # Test BTC with 1 transaction
        count = await collector._get_transaction_count("BTC")
        assert count == 1

        # Test non-existent symbol
        count = await collector._get_transaction_count("NONEXISTENT")
        assert count == 0

    @pytest.mark.asyncio
    async def test_first_purchase_date_with_real_database(
        self,
        test_session,
        sample_transactions
    ):
        """Test getting first purchase date from real database."""
        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Test AAPL - should return earliest date (365 days ago)
        first_date = await collector._get_first_purchase_date("AAPL")
        assert first_date is not None

        # Should be approximately 365 days ago
        days_ago = (datetime.utcnow() - first_date).days
        assert 364 <= days_ago <= 366  # Allow 1 day buffer for timing

        # Test non-existent symbol
        first_date = await collector._get_first_purchase_date("NONEXISTENT")
        assert first_date is None

    @pytest.mark.asyncio
    async def test_holding_period_with_real_database(
        self,
        test_session,
        sample_transactions
    ):
        """Test calculating holding period from real database."""
        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Test AAPL - held for ~365 days
        holding_period = await collector._get_holding_period("AAPL")
        assert 364 <= holding_period <= 366

        # Test BTC - held for ~200 days
        holding_period = await collector._get_holding_period("BTC")
        assert 199 <= holding_period <= 201

        # Test non-existent symbol
        holding_period = await collector._get_holding_period("NONEXISTENT")
        assert holding_period == 0

    @pytest.mark.asyncio
    async def test_collect_position_data_integration(
        self,
        test_session,
        sample_positions,
        sample_transactions
    ):
        """Test full position data collection with real database."""
        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Mock get_position to return from database
        aapl_position = sample_positions[0]

        # Manually set up the mock since we're testing integration
        from unittest.mock import AsyncMock, Mock, patch

        # Create a mock that returns the position
        mock_portfolio_service = Mock()
        mock_portfolio_service.get_position = AsyncMock(return_value=aapl_position)

        collector.portfolio_service = mock_portfolio_service

        # Mock Yahoo Finance fundamentals
        mock_fundamentals = {
            'name': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'fiftyTwoWeekLow': 150.0,
            'fiftyTwoWeekHigh': 200.0,
            'volume': 50000000,
            'averageVolume': 45000000,
            'marketCap': 3000000000000,
            'peRatio': 28.5
        }

        with patch.object(
            collector,
            '_get_stock_fundamentals',
            new_callable=AsyncMock,
            return_value=mock_fundamentals
        ):
            result = await collector.collect_position_data("AAPL")

        # Verify basic data
        assert result['symbol'] == 'AAPL'
        assert result['name'] == 'Apple Inc.'
        assert result['quantity'] == Decimal("10.0")
        assert result['current_price'] == Decimal("180.00")

        # Verify transaction context from real database
        assert result['transaction_count'] == 2
        assert 364 <= result['holding_period_days'] <= 366

        # Verify Yahoo Finance fundamentals
        assert result['sector'] == 'Technology'
        assert result['industry'] == 'Consumer Electronics'

    @pytest.mark.asyncio
    async def test_database_query_performance(
        self,
        test_session,
        sample_positions,
        sample_transactions
    ):
        """Test that database queries complete quickly."""
        import time

        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Test transaction count query performance
        start = time.perf_counter()
        count = await collector._get_transaction_count("AAPL")
        duration = time.perf_counter() - start

        assert count == 2
        assert duration < 0.1, f"Query took {duration:.3f}s (expected <0.1s)"

        # Test first purchase date query performance
        start = time.perf_counter()
        first_date = await collector._get_first_purchase_date("AAPL")
        duration = time.perf_counter() - start

        assert first_date is not None
        assert duration < 0.1, f"Query took {duration:.3f}s (expected <0.1s)"

    @pytest.mark.asyncio
    async def test_multiple_transactions_ordering(
        self,
        test_session
    ):
        """Test that first purchase date returns the earliest transaction."""
        # Create transactions in non-chronological order
        transactions = [
            Transaction(
                symbol="TEST",
                transaction_date=datetime(2024, 6, 1),  # Middle
                transaction_type=TransactionType.BUY,
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("100.00"),
                total_amount=Decimal("100.00"),
                currency="USD",
                asset_type=AssetType.STOCK
            ),
            Transaction(
                symbol="TEST",
                transaction_date=datetime(2024, 1, 1),  # Earliest
                transaction_type=TransactionType.BUY,
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("90.00"),
                total_amount=Decimal("90.00"),
                currency="USD",
                asset_type=AssetType.STOCK
            ),
            Transaction(
                symbol="TEST",
                transaction_date=datetime(2024, 12, 1),  # Latest
                transaction_type=TransactionType.BUY,
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("110.00"),
                total_amount=Decimal("110.00"),
                currency="USD",
                asset_type=AssetType.STOCK
            ),
        ]

        for tx in transactions:
            test_session.add(tx)
        await test_session.commit()

        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Should return the earliest date (2024-01-01)
        first_date = await collector._get_first_purchase_date("TEST")
        assert first_date is not None
        assert first_date.year == 2024
        assert first_date.month == 1
        assert first_date.day == 1


class TestDatabaseQueryAccuracy:
    """Test accuracy and correctness of database queries."""

    @pytest.mark.asyncio
    async def test_transaction_type_filtering(
        self,
        test_session
    ):
        """Test that only BUY transactions are counted for first purchase."""
        # Create mixed transaction types
        transactions = [
            Transaction(
                symbol="MIX",
                transaction_date=datetime(2024, 1, 1),
                transaction_type=TransactionType.SELL,  # Should be ignored
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("100.00"),
                total_amount=Decimal("100.00"),
                currency="USD",
                asset_type=AssetType.STOCK
            ),
            Transaction(
                symbol="MIX",
                transaction_date=datetime(2024, 2, 1),
                transaction_type=TransactionType.BUY,  # This should be the first
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("100.00"),
                total_amount=Decimal("100.00"),
                currency="USD",
                asset_type=AssetType.STOCK
            ),
        ]

        for tx in transactions:
            test_session.add(tx)
        await test_session.commit()

        portfolio_service = PortfolioService(test_session)
        yahoo_service = YahooFinanceService()
        collector = PromptDataCollector(
            db=test_session,
            portfolio_service=portfolio_service,
            yahoo_service=yahoo_service
        )

        # Should return February (the first BUY), not January (SELL)
        first_date = await collector._get_first_purchase_date("MIX")
        assert first_date is not None
        assert first_date.month == 2

        # Transaction count should include all types
        count = await collector._get_transaction_count("MIX")
        assert count == 2
