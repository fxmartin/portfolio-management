# ABOUTME: Tests for realized P&L calculation from closed positions
# ABOUTME: Validates FIFO methodology, fee aggregation, and asset type breakdown

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from portfolio_service import PortfolioService
from models import Transaction, Position, AssetType, TransactionType, Base


# Use SQLite for testing (in-memory database)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with TestSessionLocal() as session:
        yield session

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestRealizedPnL:
    """Test realized P&L calculation for closed positions"""

    @pytest.mark.asyncio
    async def test_no_closed_positions(self, db_session):
        """Test with only open positions (no sells)"""
        # Add only BUY transactions
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("15000.00"),
                currency="USD",
                fee=Decimal("2.50"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Get realized P&L summary
        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # Should have no realized P&L
        assert summary["total_realized_pnl"] == 0
        assert summary["total_fees"] == Decimal("2.50")
        assert summary["net_pnl"] == Decimal("-2.50")  # Only fees
        assert summary["closed_positions_count"] == 0
        assert summary["breakdown"]["stocks"]["closed_count"] == 0
        assert summary["breakdown"]["crypto"]["closed_count"] == 0
        assert summary["breakdown"]["metals"]["closed_count"] == 0

    @pytest.mark.asyncio
    async def test_single_closed_position_with_profit(self, db_session):
        """Test closed position with realized profit"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("15000.00"),
                currency="USD",
                fee=Decimal("1.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("17000.00"),
                currency="USD",
                fee=Decimal("1.50"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Calculate realized P&L
        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # FIFO: Bought 100 @ 150, Sold 100 @ 170
        # Realized gain: (170 - 150) * 100 = 2000
        # Total fees: 1.00 + 1.50 = 2.50
        # Net P&L: 2000 - 2.50 = 1997.50
        assert summary["total_realized_pnl"] == Decimal("2000.00")
        assert summary["total_fees"] == Decimal("2.50")
        assert summary["net_pnl"] == Decimal("1997.50")
        assert summary["closed_positions_count"] == 1

        # Check breakdown
        assert summary["breakdown"]["stocks"]["realized_pnl"] == Decimal("2000.00")
        assert summary["breakdown"]["stocks"]["fees"] == Decimal("2.50")
        assert summary["breakdown"]["stocks"]["net_pnl"] == Decimal("1997.50")
        assert summary["breakdown"]["stocks"]["closed_count"] == 1
        assert summary["breakdown"]["crypto"]["closed_count"] == 0
        assert summary["breakdown"]["metals"]["closed_count"] == 0

    @pytest.mark.asyncio
    async def test_single_closed_position_with_loss(self, db_session):
        """Test closed position with realized loss"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="TSLA",
                quantity=Decimal("50"),
                price_per_unit=Decimal("250.00"),
                total_amount=Decimal("12500.00"),
                currency="USD",
                fee=Decimal("5.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="TSLA",
                quantity=Decimal("50"),
                price_per_unit=Decimal("220.00"),
                total_amount=Decimal("11000.00"),
                currency="USD",
                fee=Decimal("3.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # FIFO: Bought 50 @ 250, Sold 50 @ 220
        # Realized loss: (220 - 250) * 50 = -1500
        # Total fees: 5.00 + 3.00 = 8.00
        # Net P&L: -1500 - 8.00 = -1508.00
        assert summary["total_realized_pnl"] == Decimal("-1500.00")
        assert summary["total_fees"] == Decimal("8.00")
        assert summary["net_pnl"] == Decimal("-1508.00")
        assert summary["closed_positions_count"] == 1

    @pytest.mark.asyncio
    async def test_multiple_lots_fifo_calculation(self, db_session):
        """Test FIFO with multiple purchase lots - fully closed position"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("30000.00"),
                total_amount=Decimal("30000.00"),
                currency="USD",
                fee=Decimal("10.00"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("35000.00"),
                total_amount=Decimal("17500.00"),
                currency="USD",
                fee=Decimal("5.00"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="BTC",
                quantity=Decimal("1.5"),  # Changed to 1.5 to fully close position
                price_per_unit=Decimal("40000.00"),
                total_amount=Decimal("60000.00"),  # Updated total
                currency="USD",
                fee=Decimal("15.00"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # FIFO calculation:
        # Lot 1: 1.0 BTC @ 30000
        # Lot 2: 0.5 BTC @ 35000
        # Sell 1.5 BTC @ 40000 (fully closes position)
        # - First 1.0 from Lot 1: gain = (40000 - 30000) * 1.0 = 10000
        # - Next 0.5 from Lot 2: gain = (40000 - 35000) * 0.5 = 2500
        # Total realized gain: 12500
        # Total fees: 10 + 5 + 15 = 30
        # Net P&L: 12500 - 30 = 12470
        assert summary["total_realized_pnl"] == Decimal("12500.00")
        assert summary["total_fees"] == Decimal("30.00")
        assert summary["net_pnl"] == Decimal("12470.00")
        assert summary["closed_positions_count"] == 1
        assert summary["breakdown"]["crypto"]["closed_count"] == 1

    @pytest.mark.asyncio
    async def test_mixed_asset_types(self, db_session):
        """Test with closed positions across different asset types"""
        transactions = [
            # Closed stock position
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("15000.00"),
                currency="USD",
                fee=Decimal("2.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("17000.00"),
                currency="USD",
                fee=Decimal("3.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            # Closed crypto position
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="ETH",
                quantity=Decimal("10.0"),
                price_per_unit=Decimal("2000.00"),
                total_amount=Decimal("20000.00"),
                currency="USD",
                fee=Decimal("10.00"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="ETH",
                quantity=Decimal("10.0"),
                price_per_unit=Decimal("2500.00"),
                total_amount=Decimal("25000.00"),
                currency="USD",
                fee=Decimal("12.50"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
            # Closed metal position
            Transaction(
                transaction_date=datetime(2024, 1, 10),
                asset_type=AssetType.METAL,
                transaction_type=TransactionType.BUY,
                symbol="XAU",
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("2000.00"),
                total_amount=Decimal("2000.00"),
                currency="USD",
                fee=Decimal("5.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 10),
                asset_type=AssetType.METAL,
                transaction_type=TransactionType.SELL,
                symbol="XAU",
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("2100.00"),
                total_amount=Decimal("2100.00"),
                currency="USD",
                fee=Decimal("5.50"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # Stocks: (170-150)*100 = 2000, fees = 5
        # Crypto: (2500-2000)*10 = 5000, fees = 22.50
        # Metals: (2100-2000)*1 = 100, fees = 10.50
        # Total realized: 2000 + 5000 + 100 = 7100
        # Total fees: 5 + 22.50 + 10.50 = 38
        # Net P&L: 7100 - 38 = 7062
        assert summary["total_realized_pnl"] == Decimal("7100.00")
        assert summary["total_fees"] == Decimal("38.00")
        assert summary["net_pnl"] == Decimal("7062.00")
        assert summary["closed_positions_count"] == 3

        # Check asset type breakdown
        assert summary["breakdown"]["stocks"]["realized_pnl"] == Decimal("2000.00")
        assert summary["breakdown"]["stocks"]["fees"] == Decimal("5.00")
        assert summary["breakdown"]["stocks"]["net_pnl"] == Decimal("1995.00")
        assert summary["breakdown"]["stocks"]["closed_count"] == 1

        assert summary["breakdown"]["crypto"]["realized_pnl"] == Decimal("5000.00")
        assert summary["breakdown"]["crypto"]["fees"] == Decimal("22.50")
        assert summary["breakdown"]["crypto"]["net_pnl"] == Decimal("4977.50")
        assert summary["breakdown"]["crypto"]["closed_count"] == 1

        assert summary["breakdown"]["metals"]["realized_pnl"] == Decimal("100.00")
        assert summary["breakdown"]["metals"]["fees"] == Decimal("10.50")
        assert summary["breakdown"]["metals"]["net_pnl"] == Decimal("89.50")
        assert summary["breakdown"]["metals"]["closed_count"] == 1

    @pytest.mark.asyncio
    async def test_partially_closed_position(self, db_session):
        """Test position where sell < buy (not fully closed, should not count)"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="GOOGL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("140.00"),
                total_amount=Decimal("14000.00"),
                currency="USD",
                fee=Decimal("2.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="GOOGL",
                quantity=Decimal("30"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("4500.00"),
                currency="USD",
                fee=Decimal("1.50"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # Position is not fully closed (70 shares remaining)
        # Should not be counted as closed position
        assert summary["closed_positions_count"] == 0
        # But fees should still be tracked
        assert summary["total_fees"] == Decimal("3.50")

    @pytest.mark.asyncio
    async def test_multiple_closed_positions_same_asset_type(self, db_session):
        """Test multiple closed positions within the same asset type"""
        transactions = [
            # Closed AAPL
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("50"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("7500.00"),
                currency="USD",
                fee=Decimal("1.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("50"),
                price_per_unit=Decimal("160.00"),
                total_amount=Decimal("8000.00"),
                currency="USD",
                fee=Decimal("1.50"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            # Closed TSLA
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="TSLA",
                quantity=Decimal("25"),
                price_per_unit=Decimal("200.00"),
                total_amount=Decimal("5000.00"),
                currency="USD",
                fee=Decimal("2.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 15),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="TSLA",
                quantity=Decimal("25"),
                price_per_unit=Decimal("180.00"),
                total_amount=Decimal("4500.00"),
                currency="USD",
                fee=Decimal("1.25"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # AAPL: (160-150)*50 = 500
        # TSLA: (180-200)*25 = -500
        # Total realized: 500 - 500 = 0
        # Total fees: 1 + 1.50 + 2 + 1.25 = 5.75
        # Net P&L: 0 - 5.75 = -5.75
        assert summary["total_realized_pnl"] == Decimal("0.00")
        assert summary["total_fees"] == Decimal("5.75")
        assert summary["net_pnl"] == Decimal("-5.75")
        assert summary["closed_positions_count"] == 2
        assert summary["breakdown"]["stocks"]["closed_count"] == 2

    @pytest.mark.asyncio
    async def test_zero_fees(self, db_session):
        """Test closed position with no fees"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="ADA",
                quantity=Decimal("1000"),
                price_per_unit=Decimal("0.50"),
                total_amount=Decimal("500.00"),
                currency="USD",
                fee=Decimal("0"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="ADA",
                quantity=Decimal("1000"),
                price_per_unit=Decimal("0.60"),
                total_amount=Decimal("600.00"),
                currency="USD",
                fee=Decimal("0"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        summary = await service.get_realized_pnl_summary()

        # Realized: (0.60-0.50)*1000 = 100
        # Fees: 0
        # Net: 100
        assert summary["total_realized_pnl"] == Decimal("100.00")
        assert summary["total_fees"] == Decimal("0")
        assert summary["net_pnl"] == Decimal("100.00")
        assert summary["closed_positions_count"] == 1
