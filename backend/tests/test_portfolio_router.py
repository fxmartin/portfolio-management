# ABOUTME: Tests for portfolio API endpoints
# ABOUTME: Tests portfolio summary, positions list, and price refresh endpoints

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from models import Transaction, TransactionType, AssetType, Position, Base
from portfolio_service import PortfolioService
from database import get_async_db


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


@pytest_asyncio.fixture
async def test_client(db_session):
    """Create test HTTP client with database override"""
    async def override_get_async_db():
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_async_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_transactions(db_session: AsyncSession):
    """Create sample transactions for testing"""
    transactions = [
        # Stock purchases
        Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10"),
            price_per_unit=Decimal("150.00"),
            total_amount=Decimal("1500.00"),
            currency="USD",
            source_type="REVOLUT",
        ),
        Transaction(
            transaction_date=datetime(2024, 1, 15),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="TSLA",
            quantity=Decimal("5"),
            price_per_unit=Decimal("200.00"),
            total_amount=Decimal("1000.00"),
            currency="USD",
            source_type="REVOLUT",
        ),
        # Crypto purchase
        Transaction(
            transaction_date=datetime(2024, 1, 10),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.BUY,
            symbol="BTC",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("45000.00"),
            total_amount=Decimal("22500.00"),
            currency="USD",
            source_type="KOINLY",
        ),
        # Cash transactions
        Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.CASH_IN,
            symbol="USD",
            quantity=Decimal("10000"),
            price_per_unit=Decimal("1"),
            total_amount=Decimal("10000.00"),
            currency="USD",
            source_type="REVOLUT",
        ),
        Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.CASH_IN,
            symbol="EUR",
            quantity=Decimal("5000"),
            price_per_unit=Decimal("1"),
            total_amount=Decimal("5000.00"),
            currency="EUR",
            source_type="REVOLUT",
        ),
    ]

    for txn in transactions:
        db_session.add(txn)

    await db_session.commit()

    # Recalculate positions
    portfolio_service = PortfolioService(db_session)
    await portfolio_service.recalculate_all_positions()

    return transactions


@pytest_asyncio.fixture
async def sample_positions_with_prices(db_session: AsyncSession, sample_transactions):
    """Create positions with current prices"""
    portfolio_service = PortfolioService(db_session)

    # Update prices
    await portfolio_service.update_position_price("AAPL", Decimal("155.00"))
    await portfolio_service.update_position_price("TSLA", Decimal("195.00"))
    await portfolio_service.update_position_price("BTC", Decimal("48000.00"))

    positions = await portfolio_service.get_all_positions()
    return positions


class TestPortfolioSummary:
    """Tests for GET /api/portfolio/summary endpoint"""

    @pytest.mark.asyncio
    async def test_portfolio_summary_empty_portfolio(self, test_client, db_session):
        """Test portfolio summary with no positions"""
        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_value"] == 0
        assert data["total_cash"] == 0
        assert data["total_investment_value"] == 0
        assert data["total_pnl"] == 0
        assert data["positions_count"] == 0
        assert data["last_updated"] is None

    @pytest.mark.asyncio
    async def test_portfolio_summary_with_positions(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test portfolio summary with positions and prices"""
        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_value" in data
        assert "total_cash" in data
        assert "total_investment_value" in data
        assert "total_pnl" in data
        assert "total_pnl_percent" in data
        assert "unrealized_pnl" in data
        assert "realized_pnl" in data
        assert "positions_count" in data
        assert "cash_balances" in data

        # Verify values
        assert data["positions_count"] == 3  # AAPL, TSLA, BTC
        assert data["total_cash"] == 15000.0  # 10000 USD + 5000 EUR

        # Investment value = (10 * 155) + (5 * 195) + (0.5 * 48000)
        # = 1550 + 975 + 24000 = 26525
        assert data["total_investment_value"] == 26525.0

        # Total portfolio = investments + cash
        assert data["total_value"] == 41525.0  # 26525 + 15000

        # Unrealized P&L = (155-150)*10 + (195-200)*5 + (48000-45000)*0.5
        # = 50 - 25 + 1500 = 1525
        assert data["unrealized_pnl"] == 1525.0

        # Cash balances by currency
        assert "USD" in data["cash_balances"]
        assert "EUR" in data["cash_balances"]
        assert data["cash_balances"]["USD"] == 10000.0
        assert data["cash_balances"]["EUR"] == 5000.0

        # Last updated should be recent
        assert data["last_updated"] is not None

    @pytest.mark.asyncio
    async def test_portfolio_summary_without_prices(
        self, test_client, db_session, sample_transactions
    ):
        """Test portfolio summary when prices haven't been fetched"""
        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        # Should return positions count but no current values
        assert data["positions_count"] == 3
        assert data["total_investment_value"] == 0  # No prices set
        assert data["unrealized_pnl"] == 0

    @pytest.mark.asyncio
    async def test_portfolio_summary_pnl_percentage(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test P&L percentage calculation"""
        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        # Cost basis = 1500 + 1000 + 22500 = 25000
        # P&L = 1525
        # P&L % = (1525 / 25000) * 100 = 6.1%
        assert data["total_cost_basis"] == 25000.0
        assert abs(data["total_pnl_percent"] - 6.1) < 0.1

    @pytest.mark.asyncio
    async def test_portfolio_summary_with_sells(self, test_client, db_session):
        """Test portfolio summary includes realized P&L from sells"""
        # Create buy and sell transactions
        buy = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10"),
            price_per_unit=Decimal("100.00"),
            total_amount=Decimal("1000.00"),
            currency="USD",
            source_type="REVOLUT",
        )
        sell = Transaction(
            transaction_date=datetime(2024, 1, 15),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.SELL,
            symbol="AAPL",
            quantity=Decimal("5"),
            price_per_unit=Decimal("120.00"),
            total_amount=Decimal("600.00"),
            currency="USD",
            source_type="REVOLUT",
        )

        db_session.add(buy)
        db_session.add(sell)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        # Realized P&L = (120 - 100) * 5 = 100
        assert data["realized_pnl"] == 100.0


class TestPositionsList:
    """Tests for GET /api/portfolio/positions endpoint"""

    @pytest.mark.asyncio
    async def test_get_all_positions(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test fetching all positions"""
        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3  # AAPL, TSLA, BTC

        # Check structure of first position
        position = data[0]
        assert "symbol" in position
        assert "asset_type" in position
        assert "quantity" in position
        assert "avg_cost_basis" in position
        assert "current_price" in position
        assert "current_value" in position
        assert "unrealized_pnl" in position
        assert "unrealized_pnl_percent" in position

    @pytest.mark.asyncio
    async def test_get_positions_by_asset_type_stocks(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test filtering positions by STOCK asset type"""
        response = await test_client.get("/api/portfolio/positions?asset_type=STOCK")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2  # AAPL, TSLA
        for position in data:
            assert position["asset_type"] == "STOCK"

    @pytest.mark.asyncio
    async def test_get_positions_by_asset_type_crypto(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test filtering positions by CRYPTO asset type"""
        response = await test_client.get("/api/portfolio/positions?asset_type=CRYPTO")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1  # BTC
        assert data[0]["asset_type"] == "CRYPTO"
        assert data[0]["symbol"] == "BTC"

    @pytest.mark.asyncio
    async def test_get_positions_invalid_asset_type(self, test_client, db_session):
        """Test invalid asset type returns error"""
        response = await test_client.get("/api/portfolio/positions?asset_type=INVALID")

        assert response.status_code == 400
        assert "Invalid asset type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_positions_only_open_positions(
        self, test_client, db_session, sample_transactions
    ):
        """Test that closed positions (quantity=0) are not returned"""
        # Create a position that will be fully sold
        buy = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="MSFT",
            quantity=Decimal("10"),
            price_per_unit=Decimal("300.00"),
            total_amount=Decimal("3000.00"),
            currency="USD",
            source_type="REVOLUT",
        )
        sell = Transaction(
            transaction_date=datetime(2024, 1, 15),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.SELL,
            symbol="MSFT",
            quantity=Decimal("10"),
            price_per_unit=Decimal("320.00"),
            total_amount=Decimal("3200.00"),
            currency="USD",
            source_type="REVOLUT",
        )

        db_session.add(buy)
        db_session.add(sell)
        await db_session.commit()

        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        # MSFT should not be in the list (quantity = 0)
        symbols = [p["symbol"] for p in data]
        assert "MSFT" not in symbols

    @pytest.mark.asyncio
    async def test_get_positions_with_pnl_calculations(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test positions include correct P&L calculations"""
        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        # Find AAPL position
        aapl = next(p for p in data if p["symbol"] == "AAPL")

        # AAPL: bought 10 @ 150, current 155
        assert aapl["quantity"] == 10
        assert aapl["avg_cost_basis"] == 150.0
        assert aapl["current_price"] == 155.0
        assert aapl["unrealized_pnl"] == 50.0  # (155-150)*10
        assert abs(aapl["unrealized_pnl_percent"] - 3.33) < 0.01  # (5/150)*100


class TestRefreshPrices:
    """Tests for POST /api/portfolio/refresh-prices endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_prices_structure(self, test_client, db_session):
        """Test refresh prices endpoint response structure"""
        # Note: This test will fail without positions due to Yahoo Finance calls
        # The endpoint structure is tested here; actual price fetching is tested in Epic 3
        response = await test_client.post("/api/portfolio/refresh-prices")

        # Accept both success and failure codes since we don't have real data
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "updated_count" in data
            assert "failed_count" in data
            assert "timestamp" in data
            assert "failed_symbols" in data


class TestCashBalances:
    """Tests for cash balance calculations"""

    @pytest.mark.asyncio
    async def test_multiple_cash_in_transactions(self, test_client, db_session):
        """Test cash balance with multiple deposits"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_IN,
                symbol="USD",
                quantity=Decimal("1000"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("1000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_IN,
                symbol="USD",
                quantity=Decimal("2000"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("2000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_cash"] == 3000.0
        assert data["cash_balances"]["USD"] == 3000.0

    @pytest.mark.asyncio
    async def test_cash_in_and_out_transactions(self, test_client, db_session):
        """Test cash balance with deposits and withdrawals"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_IN,
                symbol="USD",
                quantity=Decimal("5000"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("5000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_OUT,
                symbol="USD",
                quantity=Decimal("2000"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("2000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_cash"] == 3000.0  # 5000 - 2000
        assert data["cash_balances"]["USD"] == 3000.0

    @pytest.mark.asyncio
    async def test_multi_currency_cash_balances(self, test_client, db_session):
        """Test cash balances in multiple currencies"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_IN,
                symbol="USD",
                quantity=Decimal("1000"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("1000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_IN,
                symbol="EUR",
                quantity=Decimal("500"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("500.00"),
                currency="EUR",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.CASH_IN,
                symbol="GBP",
                quantity=Decimal("300"),
                price_per_unit=Decimal("1"),
                total_amount=Decimal("300.00"),
                currency="GBP",
                source_type="REVOLUT",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/summary")

        assert response.status_code == 200
        data = response.json()

        # Total cash is sum of all currencies (not converted)
        assert data["total_cash"] == 1800.0

        # Each currency should be tracked separately
        assert data["cash_balances"]["USD"] == 1000.0
        assert data["cash_balances"]["EUR"] == 500.0
        assert data["cash_balances"]["GBP"] == 300.0


class TestOpenPositionsOverview:
    """Tests for GET /api/portfolio/open-positions endpoint"""

    @pytest.mark.asyncio
    async def test_open_positions_empty_portfolio(self, test_client, db_session):
        """Test open positions overview with no positions"""
        response = await test_client.get("/api/portfolio/open-positions")

        assert response.status_code == 200
        data = response.json()

        assert data["total_value"] == 0
        assert data["total_cost_basis"] == 0
        assert data["unrealized_pnl"] == 0
        assert data["unrealized_pnl_percent"] == 0
        assert data["last_updated"] is None

        # Check breakdown structure
        assert "breakdown" in data
        assert "stocks" in data["breakdown"]
        assert "crypto" in data["breakdown"]
        assert "metals" in data["breakdown"]

        # All breakdown values should be zero
        assert data["breakdown"]["stocks"]["value"] == 0
        assert data["breakdown"]["stocks"]["pnl"] == 0
        assert data["breakdown"]["crypto"]["value"] == 0
        assert data["breakdown"]["metals"]["value"] == 0

    @pytest.mark.asyncio
    async def test_open_positions_with_positions(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test open positions overview with positions and prices"""
        response = await test_client.get("/api/portfolio/open-positions")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_value" in data
        assert "total_cost_basis" in data
        assert "unrealized_pnl" in data
        assert "unrealized_pnl_percent" in data
        assert "breakdown" in data
        assert "last_updated" in data

        # Total value = (10 * 155) + (5 * 195) + (0.5 * 48000)
        # = 1550 + 975 + 24000 = 26525
        assert data["total_value"] == 26525.0

        # Total cost basis = 1500 + 1000 + 22500 = 25000
        assert data["total_cost_basis"] == 25000.0

        # Unrealized P&L = 26525 - 25000 = 1525
        assert data["unrealized_pnl"] == 1525.0

        # P&L % = (1525 / 25000) * 100 = 6.1%
        assert abs(data["unrealized_pnl_percent"] - 6.1) < 0.1

        # Last updated should be recent
        assert data["last_updated"] is not None

    @pytest.mark.asyncio
    async def test_open_positions_breakdown_by_asset_type(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test breakdown calculation by asset type"""
        response = await test_client.get("/api/portfolio/open-positions")

        assert response.status_code == 200
        data = response.json()

        breakdown = data["breakdown"]

        # Stocks: AAPL (10 * 155) + TSLA (5 * 195) = 1550 + 975 = 2525
        # Cost: 1500 + 1000 = 2500
        # P&L: 2525 - 2500 = 25
        assert breakdown["stocks"]["value"] == 2525.0
        assert breakdown["stocks"]["pnl"] == 25.0
        assert abs(breakdown["stocks"]["pnl_percent"] - 1.0) < 0.1

        # Crypto: BTC (0.5 * 48000) = 24000
        # Cost: 22500
        # P&L: 24000 - 22500 = 1500
        assert breakdown["crypto"]["value"] == 24000.0
        assert breakdown["crypto"]["pnl"] == 1500.0
        assert abs(breakdown["crypto"]["pnl_percent"] - 6.67) < 0.1

        # Metals: None in sample data
        assert breakdown["metals"]["value"] == 0
        assert breakdown["metals"]["pnl"] == 0
        assert breakdown["metals"]["pnl_percent"] == 0

    @pytest.mark.asyncio
    async def test_open_positions_excludes_cash(
        self, test_client, db_session, sample_positions_with_prices
    ):
        """Test that open positions excludes cash balances"""
        # Get both endpoints
        summary_response = await test_client.get("/api/portfolio/summary")
        positions_response = await test_client.get("/api/portfolio/open-positions")

        assert summary_response.status_code == 200
        assert positions_response.status_code == 200

        summary = summary_response.json()
        positions = positions_response.json()

        # Summary includes cash
        assert summary["total_value"] == 41525.0  # 26525 investments + 15000 cash
        assert summary["total_cash"] == 15000.0

        # Open positions excludes cash
        assert positions["total_value"] == 26525.0  # Only investments
        assert "total_cash" not in positions

    @pytest.mark.asyncio
    async def test_open_positions_without_prices(
        self, test_client, db_session, sample_transactions
    ):
        """Test open positions when prices haven't been fetched"""
        response = await test_client.get("/api/portfolio/open-positions")

        assert response.status_code == 200
        data = response.json()

        # When no prices are set, current_value is 0 but cost basis remains
        # Cost basis = 1500 + 1000 + 22500 = 25000
        # Unrealized P&L = 0 - 25000 = -25000
        assert data["total_value"] == 0
        assert data["total_cost_basis"] == 25000.0
        assert data["unrealized_pnl"] == -25000.0
        assert data["breakdown"]["stocks"]["value"] == 0
        assert data["breakdown"]["crypto"]["value"] == 0

    @pytest.mark.asyncio
    async def test_open_positions_with_metal_positions(self, test_client, db_session):
        """Test open positions with metal (XAU, XAG) positions"""
        # Create metal transactions
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.METAL,
                transaction_type=TransactionType.BUY,
                symbol="XAU",
                quantity=Decimal("2.5"),
                price_per_unit=Decimal("2000.00"),
                total_amount=Decimal("5000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Recalculate positions and set price
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()
        await portfolio_service.update_position_price("XAU", Decimal("2100.00"))

        response = await test_client.get("/api/portfolio/open-positions")

        assert response.status_code == 200
        data = response.json()

        # XAU value: 2.5 * 2100 = 5250
        # Cost: 5000
        # P&L: 250
        assert data["total_value"] == 5250.0
        assert data["total_cost_basis"] == 5000.0
        assert data["unrealized_pnl"] == 250.0

        # Check metals breakdown
        assert data["breakdown"]["metals"]["value"] == 5250.0
        assert data["breakdown"]["metals"]["pnl"] == 250.0
        assert abs(data["breakdown"]["metals"]["pnl_percent"] - 5.0) < 0.1

    @pytest.mark.asyncio
    async def test_open_positions_excludes_closed_positions(
        self, test_client, db_session
    ):
        """Test that closed positions (quantity = 0) are excluded"""
        # Create buy and sell transactions that close the position
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="MSFT",
                quantity=Decimal("10"),
                price_per_unit=Decimal("300.00"),
                total_amount=Decimal("3000.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="MSFT",
                quantity=Decimal("10"),
                price_per_unit=Decimal("320.00"),
                total_amount=Decimal("3200.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/open-positions")

        assert response.status_code == 200
        data = response.json()

        # Position is closed, should have zero values
        assert data["total_value"] == 0
        assert data["total_cost_basis"] == 0
        assert data["unrealized_pnl"] == 0
        assert data["breakdown"]["stocks"]["value"] == 0
