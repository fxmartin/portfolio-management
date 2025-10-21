# ABOUTME: Tests for portfolio service - position aggregation and P&L calculations
# ABOUTME: Integration tests combining FIFO calculator with database operations

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


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing"""
    return [
        Transaction(
            id=1,
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("100"),
            price_per_unit=Decimal("150.00"),
            total_amount=Decimal("15000.00"),
            currency="USD",
            fee=Decimal("0"),
            source_type="REVOLUT",
            source_file="test.csv"
        ),
        Transaction(
            id=2,
            transaction_date=datetime(2024, 2, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("50"),
            price_per_unit=Decimal("160.00"),
            total_amount=Decimal("8000.00"),
            currency="USD",
            fee=Decimal("0"),
            source_type="REVOLUT",
            source_file="test.csv"
        ),
        Transaction(
            id=3,
            transaction_date=datetime(2024, 3, 1),
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


class TestPortfolioService:
    """Test portfolio position aggregation and calculations"""

    @pytest.mark.asyncio
    async def test_calculate_positions_from_scratch(self, db_session, sample_transactions):
        """Test calculating positions from transactions"""
        # Add transactions to database
        for txn in sample_transactions:
            db_session.add(txn)
        await db_session.commit()

        # Calculate positions
        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        # Check position
        position = await service.get_position("AAPL")
        assert position is not None
        assert position.symbol == "AAPL"
        assert position.quantity == Decimal("120")  # 100 + 50 - 30
        assert position.asset_type == AssetType.STOCK

        # Cost basis should be weighted average of remaining lots
        # Sold 30 from first lot (100 @ 150)
        # Remaining: 70 @ 150 + 50 @ 160
        # Total cost: 70*150 + 50*160 = 10500 + 8000 = 18500
        # Avg cost: 18500 / 120 = 154.1666...
        assert position.total_cost_basis == Decimal("18500.00")
        avg_expected = Decimal("18500.00") / Decimal("120")
        assert abs(position.avg_cost_basis - avg_expected) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_get_all_positions(self, db_session):
        """Test retrieving all positions"""
        # Create multiple positions
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
                transaction_date=datetime(2024, 1, 2),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="TSLA",
                quantity=Decimal("50"),
                price_per_unit=Decimal("200.00"),
                total_amount=Decimal("10000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 3),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("25000.00"),
                currency="USD",
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        positions = await service.get_all_positions()
        assert len(positions) == 3

        symbols = [p.symbol for p in positions]
        assert "AAPL" in symbols
        assert "TSLA" in symbols
        assert "BTC" in symbols

    @pytest.mark.asyncio
    async def test_position_with_complete_sell(self, db_session):
        """Test position after selling entire holding"""
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
                quantity=Decimal("100"),
                price_per_unit=Decimal("170.00"),
                total_amount=Decimal("17000.00"),
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

        position = await service.get_position("AAPL")
        assert position is not None
        assert position.quantity == Decimal("0")
        assert position.total_cost_basis == Decimal("0")

    @pytest.mark.asyncio
    async def test_cost_lots_stored_correctly(self, db_session):
        """Test that FIFO cost lots are stored in position"""
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
        await service.recalculate_all_positions()

        position = await service.get_position("AAPL")
        assert position.cost_lots is not None
        assert len(position.cost_lots) == 2
        assert position.cost_lots[0]["quantity"] == "100"
        assert position.cost_lots[0]["price"] == "150.00"
        assert position.cost_lots[1]["quantity"] == "50"
        assert position.cost_lots[1]["price"] == "160.00"

    @pytest.mark.asyncio
    async def test_multiple_asset_types(self, db_session):
        """Test positions across different asset types"""
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
                transaction_date=datetime(2024, 1, 2),
                asset_type=AssetType.METAL,
                transaction_type=TransactionType.BUY,
                symbol="XAU",
                quantity=Decimal("10"),
                price_per_unit=Decimal("2000.00"),
                total_amount=Decimal("20000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 3),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("25000.00"),
                currency="USD",
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        aapl = await service.get_position("AAPL")
        assert aapl.asset_type == AssetType.STOCK

        xau = await service.get_position("XAU")
        assert xau.asset_type == AssetType.METAL

        btc = await service.get_position("BTC")
        assert btc.asset_type == AssetType.CRYPTO

    @pytest.mark.asyncio
    async def test_first_and_last_transaction_dates(self, db_session):
        """Test that position tracks first purchase and last transaction dates"""
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
                transaction_date=datetime(2024, 3, 15),
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
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        position = await service.get_position("AAPL")
        assert position.first_purchase_date == datetime(2024, 1, 1)
        assert position.last_transaction_date == datetime(2024, 3, 15)

    @pytest.mark.asyncio
    async def test_update_single_position(self, db_session):
        """Test updating a single position without recalculating all"""
        # Create transactions for multiple symbols
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
                transaction_date=datetime(2024, 1, 2),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="TSLA",
                quantity=Decimal("50"),
                price_per_unit=Decimal("200.00"),
                total_amount=Decimal("10000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)

        # Update only AAPL position
        await service.update_position("AAPL")

        aapl = await service.get_position("AAPL")
        assert aapl is not None
        assert aapl.quantity == Decimal("100")

        # TSLA shouldn't exist yet
        tsla = await service.get_position("TSLA")
        assert tsla is None

        # Now update TSLA
        await service.update_position("TSLA")
        tsla = await service.get_position("TSLA")
        assert tsla is not None
        assert tsla.quantity == Decimal("50")

    @pytest.mark.asyncio
    async def test_get_positions_by_asset_type(self, db_session):
        """Test filtering positions by asset type"""
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
                transaction_date=datetime(2024, 1, 2),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("25000.00"),
                currency="USD",
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        # Get only stocks
        stocks = await service.get_all_positions(asset_type=AssetType.STOCK)
        assert len(stocks) == 1
        assert stocks[0].symbol == "AAPL"

        # Get only crypto
        crypto = await service.get_all_positions(asset_type=AssetType.CRYPTO)
        assert len(crypto) == 1
        assert crypto[0].symbol == "BTC"

    @pytest.mark.asyncio
    async def test_update_position_no_transactions(self, db_session):
        """Test updating position when no transactions exist"""
        service = PortfolioService(db_session)
        result = await service.update_position("NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_portfolio_summary(self, db_session):
        """Test getting portfolio summary"""
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
                transaction_date=datetime(2024, 1, 2),
                asset_type=AssetType.METAL,
                transaction_type=TransactionType.BUY,
                symbol="XAU",
                quantity=Decimal("10"),
                price_per_unit=Decimal("2000.00"),
                total_amount=Decimal("20000.00"),
                currency="USD",
                source_type="REVOLUT",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 3),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("25000.00"),
                currency="USD",
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        summary = await service.get_portfolio_summary()
        assert summary["total_positions"] == 3
        assert summary["total_cost_basis"] == 60000.00  # 15000 + 20000 + 25000
        assert summary["positions_by_type"]["stocks"] == 1
        assert summary["positions_by_type"]["metals"] == 1
        assert summary["positions_by_type"]["crypto"] == 1
        assert "AAPL" in summary["symbols"]
        assert "XAU" in summary["symbols"]
        assert "BTC" in summary["symbols"]

    @pytest.mark.asyncio
    async def test_delete_all_positions(self, db_session):
        """Test deleting all positions"""
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
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        service = PortfolioService(db_session)
        await service.recalculate_all_positions()

        # Verify position exists
        positions = await service.get_all_positions()
        assert len(positions) == 1

        # Delete all
        count = await service.delete_all_positions()
        assert count == 1

        # Verify empty
        positions = await service.get_all_positions()
        assert len(positions) == 0
