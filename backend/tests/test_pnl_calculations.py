# ABOUTME: Tests for P&L calculations (realized and unrealized)
# ABOUTME: Verifies profit/loss calculations with live prices

import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import AsyncMock, patch

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
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestUnrealizedPNL:
    """Test unrealized P&L calculations"""

    @pytest.mark.asyncio
    async def test_calculate_unrealized_pnl_single_lot(self, db_session):
        """Test unrealized P&L with single lot"""
        # Create a buy transaction
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("100"),
            price_per_unit=Decimal("150.00"),
            total_amount=Decimal("15000.00"),
            currency="USD",
            source_type="REVOLUT",
            source_file="test.csv"
        )
        db_session.add(transaction)
        await db_session.commit()

        # Calculate position
        service = PortfolioService(db_session)
        await service.update_position("AAPL")

        # Update with current price
        current_price = Decimal("170.00")
        await service.update_position_price("AAPL", current_price)

        # Get position with P&L
        position = await service.get_position("AAPL")

        # Unrealized P&L = (170 - 150) * 100 = 2000
        assert position.unrealized_pnl == Decimal("2000.00")
        # Percentage = ((170 / 150) - 1) * 100 = 13.33%
        expected_pct = Decimal("13.33")
        assert abs(position.unrealized_pnl_percent - expected_pct) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_calculate_unrealized_pnl_multiple_lots(self, db_session):
        """Test unrealized P&L with multiple lots at different costs"""
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
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("50"),
                price_per_unit=Decimal("160.00"),
                total_amount=Decimal("8000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.update_position("AAPL")

        # Update with current price
        current_price = Decimal("180.00")
        await service.update_position_price("AAPL", current_price)

        position = await service.get_position("AAPL")

        # Total cost: 100*150 + 50*160 = 23000
        # Current value: 150*180 = 27000
        # Unrealized P&L: 27000 - 23000 = 4000
        assert abs(position.unrealized_pnl - Decimal("4000.00")) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_unrealized_pnl_after_partial_sell(self, db_session):
        """Test unrealized P&L after selling part of position"""
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
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("30"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("5100.00"),
                currency="USD",
                fee=Decimal("5.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.update_position("AAPL")

        # Update with current price
        current_price = Decimal("180.00")
        await service.update_position_price("AAPL", current_price)

        position = await service.get_position("AAPL")

        # Remaining: 70 shares @ 150 cost
        # Current value: 70 * 180 = 12600
        # Cost basis: 70 * 150 = 10500
        # Unrealized P&L: 12600 - 10500 = 2100
        assert position.quantity == Decimal("70")
        assert position.unrealized_pnl == Decimal("2100.00")

    @pytest.mark.asyncio
    async def test_negative_unrealized_pnl(self, db_session):
        """Test unrealized P&L when position is underwater"""
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("100"),
            price_per_unit=Decimal("200.00"),
            total_amount=Decimal("20000.00"),
            currency="USD",
            source_type="REVOLUT",
            source_file="test.csv"
        )
        db_session.add(transaction)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.update_position("AAPL")

        # Price has dropped
        current_price = Decimal("150.00")
        await service.update_position_price("AAPL", current_price)

        position = await service.get_position("AAPL")

        # Loss = (150 - 200) * 100 = -5000
        assert position.unrealized_pnl == Decimal("-5000.00")
        # Percentage = ((150 / 200) - 1) * 100 = -25%
        assert position.unrealized_pnl_percent == Decimal("-25.00")


class TestRealizedPNL:
    """Test realized P&L tracking"""

    @pytest.mark.asyncio
    async def test_get_realized_pnl_for_ticker(self, db_session):
        """Test retrieving realized P&L for a specific ticker"""
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
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("50"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("8500.00"),
                currency="USD",
                fee=Decimal("10.00"),
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        # Get realized P&L
        realized = await service.get_realized_pnl("AAPL")

        # Profit = (170 - 150) * 50 = 1000
        # Net after fee = 1000 - 10 = 990
        assert realized["total_realized_pnl"] == Decimal("1000.00")
        assert realized["total_fees"] == Decimal("10.00")
        assert realized["net_realized_pnl"] == Decimal("990.00")

    @pytest.mark.asyncio
    async def test_realized_pnl_multiple_sales(self, db_session):
        """Test realized P&L with multiple sale transactions"""
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
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("30"),
                price_per_unit=Decimal("160.00"),
                total_amount=Decimal("4800.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("30"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("5100.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        realized = await service.get_realized_pnl("AAPL")

        # Sale 1: (160 - 150) * 30 = 300
        # Sale 2: (170 - 150) * 30 = 600
        # Total = 900
        assert realized["total_realized_pnl"] == Decimal("900.00")

    @pytest.mark.asyncio
    async def test_portfolio_wide_pnl_summary(self, db_session):
        """Test getting P&L summary for entire portfolio"""
        transactions = [
            # AAPL - profit
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("100"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("15000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                quantity=Decimal("50"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("8500.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            # TSLA - loss
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="TSLA",
                quantity=Decimal("50"),
                price_per_unit=Decimal("250.00"),
                total_amount=Decimal("12500.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="TSLA",
                quantity=Decimal("25"),
                price_per_unit=Decimal("200.00"),
                total_amount=Decimal("5000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        summary = await service.get_portfolio_pnl_summary()

        # AAPL realized: (170-150)*50 = 1000
        # TSLA realized: (200-250)*25 = -1250
        # Total realized: 1000 - 1250 = -250
        assert summary["total_realized_pnl"] == Decimal("-250.00")
