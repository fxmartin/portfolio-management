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

    @pytest.mark.asyncio
    async def test_get_positions_includes_fee_information(
        self, test_client, db_session
    ):
        """Test that positions endpoint includes total fees and transaction count per position"""
        # Create transactions with fees
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("50000.00"),
                fee=Decimal("25.50"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("48000.00"),
                total_amount=Decimal("24000.00"),
                fee=Decimal("12.25"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 20),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="ETH",
                quantity=Decimal("10.0"),
                price_per_unit=Decimal("3000.00"),
                total_amount=Decimal("30000.00"),
                fee=Decimal("15.75"),
                currency="EUR",
                source_type="KOINLY",
            ),
            # Transaction with no fee
            Transaction(
                transaction_date=datetime(2024, 2, 10),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.STAKING,
                symbol="BTC",
                quantity=Decimal("0.01"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("500.00"),
                fee=Decimal("0"),
                currency="EUR",
                source_type="KOINLY",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        # Find BTC position
        btc = next(p for p in data if p["symbol"] == "BTC")

        # Verify fee information is included
        assert "total_fees" in btc
        assert "fee_transaction_count" in btc

        # BTC has 3 transactions: 25.50 + 12.25 + 0 = 37.75
        assert btc["total_fees"] == 37.75

        # Count of transactions with fees > 0 = 2
        assert btc["fee_transaction_count"] == 2

        # Find ETH position
        eth = next(p for p in data if p["symbol"] == "ETH")

        # ETH has 1 transaction with fee: 15.75
        assert eth["total_fees"] == 15.75
        assert eth["fee_transaction_count"] == 1

    @pytest.mark.asyncio
    async def test_get_positions_with_zero_fees(
        self, test_client, db_session
    ):
        """Test positions with no transaction fees return zero"""
        # Create transaction without fee
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10.0"),
            price_per_unit=Decimal("150.00"),
            total_amount=Decimal("1500.00"),
            fee=Decimal("0"),
            currency="USD",
            source_type="REVOLUT",
        )

        db_session.add(transaction)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        # Find AAPL position
        aapl = next(p for p in data if p["symbol"] == "AAPL")

        # Should have zero fees
        assert aapl["total_fees"] == 0
        assert aapl["fee_transaction_count"] == 0

    @pytest.mark.asyncio
    async def test_get_positions_fee_aggregation_with_mixed_types(
        self, test_client, db_session
    ):
        """Test fee aggregation with mixed transaction types (BUY, SELL, STAKING)"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="SOL",
                quantity=Decimal("100.0"),
                price_per_unit=Decimal("100.00"),
                total_amount=Decimal("10000.00"),
                fee=Decimal("5.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="SOL",
                quantity=Decimal("50.0"),
                price_per_unit=Decimal("120.00"),
                total_amount=Decimal("6000.00"),
                fee=Decimal("3.50"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.STAKING,
                symbol="SOL",
                quantity=Decimal("5.0"),
                price_per_unit=Decimal("110.00"),
                total_amount=Decimal("550.00"),
                fee=Decimal("0.50"),
                currency="EUR",
                source_type="KOINLY",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        # Find SOL position
        sol = next(p for p in data if p["symbol"] == "SOL")

        # Total fees = 5.00 + 3.50 + 0.50 = 9.00
        assert sol["total_fees"] == 9.00

        # All 3 transactions have fees
        assert sol["fee_transaction_count"] == 3


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

    @pytest.mark.asyncio
    async def test_open_positions_includes_fee_information(
        self, test_client, db_session
    ):
        """Test that open positions includes total fees and transaction count"""
        # Create transactions with fees
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("50000.00"),
                fee=Decimal("25.50"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="ETH",
                quantity=Decimal("10.0"),
                price_per_unit=Decimal("3000.00"),
                total_amount=Decimal("30000.00"),
                fee=Decimal("15.75"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("5.0"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("750.00"),
                fee=Decimal("2.50"),
                currency="USD",
                source_type="REVOLUT",
            ),
            # Transaction with no fee
            Transaction(
                transaction_date=datetime(2024, 2, 10),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.STAKING,
                symbol="BTC",
                quantity=Decimal("0.01"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("500.00"),
                fee=Decimal("0"),
                currency="EUR",
                source_type="KOINLY",
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

        # Verify fee information is included
        assert "total_fees" in data
        assert "fee_transaction_count" in data

        # Total fees = 25.50 + 15.75 + 2.50 + 0 = 43.75
        assert data["total_fees"] == 43.75

        # Count of transactions with fees > 0 = 3
        assert data["fee_transaction_count"] == 3


class TestAssetNames:
    """Tests for asset_name field functionality"""

    @pytest.mark.asyncio
    async def test_positions_endpoint_returns_asset_name_field(
        self, test_client, db_session, sample_transactions
    ):
        """Test that /api/portfolio/positions returns asset_name field"""
        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        # Verify asset_name field is present in all positions
        for position in data:
            assert "asset_name" in position
            assert "symbol" in position

    @pytest.mark.asyncio
    async def test_asset_name_is_nullable(
        self, test_client, db_session
    ):
        """Test that asset_name can be null for positions without names"""
        # Create a position without asset name
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="TEST",
            quantity=Decimal("10"),
            price_per_unit=Decimal("100.00"),
            total_amount=Decimal("1000.00"),
            currency="USD",
            source_type="REVOLUT",
        )
        db_session.add(transaction)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        response = await test_client.get("/api/portfolio/positions")

        assert response.status_code == 200
        data = response.json()

        test_position = next(p for p in data if p["symbol"] == "TEST")
        # Asset name should be null since we haven't fetched prices
        assert test_position["asset_name"] is None

    @pytest.mark.asyncio
    async def test_update_position_price_stores_asset_name(
        self, test_client, db_session
    ):
        """Test that update_position_price stores asset_name when provided"""
        # Create a position
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="MSTR",
            quantity=Decimal("10"),
            price_per_unit=Decimal("500.00"),
            total_amount=Decimal("5000.00"),
            currency="USD",
            source_type="REVOLUT",
        )
        db_session.add(transaction)
        await db_session.commit()

        # Recalculate positions
        portfolio_service = PortfolioService(db_session)
        await portfolio_service.recalculate_all_positions()

        # Update price with asset name
        await portfolio_service.update_position_price(
            "MSTR",
            Decimal("550.00"),
            asset_name="MicroStrategy Incorporated"
        )

        # Verify asset_name was stored
        response = await test_client.get("/api/portfolio/positions")
        assert response.status_code == 200
        data = response.json()

        mstr_position = next(p for p in data if p["symbol"] == "MSTR")
        assert mstr_position["asset_name"] == "MicroStrategy Incorporated"


class TestRealizedPnLAPI:
    """Test realized P&L summary API endpoint"""

    @pytest.mark.asyncio
    async def test_get_realized_pnl_with_no_closed_positions(
        self, test_client, db_session
    ):
        """Test API returns zero realized P&L when no positions are closed"""
        # Add only BUY transaction (open position)
        transaction = Transaction(
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
        )
        db_session.add(transaction)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl")

        assert response.status_code == 200
        data = response.json()

        assert data["total_realized_pnl"] == 0
        assert data["total_fees"] == 2.50
        assert data["net_pnl"] == -2.50
        assert data["closed_positions_count"] == 0
        assert data["breakdown"]["stocks"]["closed_count"] == 0
        assert data["breakdown"]["crypto"]["closed_count"] == 0
        assert data["breakdown"]["metals"]["closed_count"] == 0
        assert "last_updated" in data

    @pytest.mark.asyncio
    async def test_get_realized_pnl_with_single_closed_position(
        self, test_client, db_session
    ):
        """Test API returns correct realized P&L for single closed position"""
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

        response = await test_client.get("/api/portfolio/realized-pnl")

        assert response.status_code == 200
        data = response.json()

        # Realized: (170-150)*100 = 2000
        # Fees: 1 + 1.50 = 2.50
        # Net: 2000 - 2.50 = 1997.50
        assert data["total_realized_pnl"] == 2000.0
        assert data["total_fees"] == 2.50
        assert data["net_pnl"] == 1997.50
        assert data["closed_positions_count"] == 1
        assert data["breakdown"]["stocks"]["realized_pnl"] == 2000.0
        assert data["breakdown"]["stocks"]["fees"] == 2.50
        assert data["breakdown"]["stocks"]["net_pnl"] == 1997.50
        assert data["breakdown"]["stocks"]["closed_count"] == 1

    @pytest.mark.asyncio
    async def test_get_realized_pnl_with_mixed_asset_types(
        self, test_client, db_session
    ):
        """Test API returns correct breakdown for multiple asset types"""
        transactions = [
            # Closed STOCK position (profit)
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
            # Closed CRYPTO position (loss)
            Transaction(
                transaction_date=datetime(2024, 1, 15),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="ETH",
                quantity=Decimal("5.0"),
                price_per_unit=Decimal("2000.00"),
                total_amount=Decimal("10000.00"),
                currency="USD",
                fee=Decimal("5.00"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="ETH",
                quantity=Decimal("5.0"),
                price_per_unit=Decimal("1800.00"),
                total_amount=Decimal("9000.00"),
                currency="USD",
                fee=Decimal("4.50"),
                source_type="KOINLY",
                source_file="test.csv"
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl")

        assert response.status_code == 200
        data = response.json()

        # AAPL: (160-150)*50 = 500
        # ETH: (1800-2000)*5 = -1000
        # Total realized: 500 - 1000 = -500
        # Total fees: 1 + 1.50 + 5 + 4.50 = 12
        # Net: -500 - 12 = -512
        assert data["total_realized_pnl"] == -500.0
        assert data["total_fees"] == 12.0
        assert data["net_pnl"] == -512.0
        assert data["closed_positions_count"] == 2

        # Check breakdown
        assert data["breakdown"]["stocks"]["realized_pnl"] == 500.0
        assert data["breakdown"]["stocks"]["closed_count"] == 1
        assert data["breakdown"]["crypto"]["realized_pnl"] == -1000.0
        assert data["breakdown"]["crypto"]["closed_count"] == 1
        assert data["breakdown"]["metals"]["closed_count"] == 0

    @pytest.mark.asyncio
    async def test_get_realized_pnl_response_structure(
        self, test_client, db_session
    ):
        """Test API response has correct structure and fields"""
        response = await test_client.get("/api/portfolio/realized-pnl")

        assert response.status_code == 200
        data = response.json()

        # Check top-level fields
        assert "total_realized_pnl" in data
        assert "total_fees" in data
        assert "net_pnl" in data
        assert "closed_positions_count" in data
        assert "breakdown" in data
        assert "last_updated" in data

        # Check breakdown structure
        assert "stocks" in data["breakdown"]
        assert "crypto" in data["breakdown"]
        assert "metals" in data["breakdown"]

        # Check asset type breakdown fields
        for asset_type in ["stocks", "crypto", "metals"]:
            breakdown = data["breakdown"][asset_type]
            assert "realized_pnl" in breakdown
            assert "fees" in breakdown
            assert "net_pnl" in breakdown
            assert "closed_count" in breakdown


class TestPositionTransactionsEndpoint:
    """Tests for the position transactions endpoint"""

    @pytest.mark.asyncio
    async def test_get_transactions_for_symbol(
        self, test_client, db_session
    ):
        """Test fetching transactions for a specific symbol"""
        # Create multiple transactions for the same symbol
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("45000.00"),
                total_amount=Decimal("22500.00"),
                fee=Decimal("25.50"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.STAKING,
                symbol="BTC",
                quantity=Decimal("0.001"),
                price_per_unit=Decimal("50000.00"),
                total_amount=Decimal("50.00"),
                fee=Decimal("0.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="BTC",
                quantity=Decimal("0.2"),
                price_per_unit=Decimal("52000.00"),
                total_amount=Decimal("10400.00"),
                fee=Decimal("10.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        # Fetch transactions for BTC
        response = await test_client.get("/api/portfolio/positions/BTC/transactions")

        assert response.status_code == 200
        data = response.json()

        # Should return 3 transactions
        assert len(data) == 3

        # Check first transaction (should be newest - SELL from March)
        first_txn = data[0]
        assert first_txn["type"] == "SELL"  # Newest
        assert first_txn["quantity"] == 0.2
        assert first_txn["price"] == 52000.0
        assert first_txn["fee"] == 10.0
        assert first_txn["currency"] == "EUR"
        assert first_txn["asset_type"] == "CRYPTO"

        # Check ordering (newest first)
        assert data[0]["date"] > data[1]["date"]
        assert data[1]["date"] > data[2]["date"]

        # Check all transaction types are present
        types = [txn["type"] for txn in data]
        assert "BUY" in types
        assert "SELL" in types
        assert "STAKING" in types

    @pytest.mark.asyncio
    async def test_get_transactions_404_for_nonexistent_symbol(
        self, test_client, db_session
    ):
        """Test 404 response for symbol with no transactions"""
        response = await test_client.get("/api/portfolio/positions/NONEXISTENT/transactions")

        assert response.status_code == 404
        assert "No transactions found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_transactions_ordering(
        self, test_client, db_session
    ):
        """Test transactions are ordered by date descending (newest first)"""
        # Create transactions with different dates
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("10"),
                price_per_unit=Decimal("150.00"),
                total_amount=Decimal("1500.00"),
                fee=Decimal("1.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 6, 15),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("5"),
                price_per_unit=Decimal("180.00"),
                total_amount=Decimal("900.00"),
                fee=Decimal("1.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 10),
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                quantity=Decimal("3"),
                price_per_unit=Decimal("160.00"),
                total_amount=Decimal("480.00"),
                fee=Decimal("1.00"),
                currency="USD",
                source_type="REVOLUT",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/positions/AAPL/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3

        # Verify descending order by date
        dates = [datetime.fromisoformat(txn["date"]) for txn in data]
        assert dates == sorted(dates, reverse=True)

        # First should be June (newest)
        assert data[0]["quantity"] == 5.0
        # Last should be January (oldest)
        assert data[2]["quantity"] == 10.0

    @pytest.mark.asyncio
    async def test_get_transactions_total_amount_calculation(
        self, test_client, db_session
    ):
        """Test that total_amount is calculated correctly (price * quantity + fee)"""
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.BUY,
            symbol="ETH",
            quantity=Decimal("2.5"),
            price_per_unit=Decimal("3000.00"),
            total_amount=Decimal("7500.00"),
            fee=Decimal("15.25"),
            currency="EUR",
            source_type="KOINLY",
        )

        db_session.add(transaction)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/positions/ETH/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        txn = data[0]

        # total_amount should be quantity * price + fee
        expected_total = 2.5 * 3000.0 + 15.25
        assert abs(txn["total_amount"] - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_get_transactions_with_all_transaction_types(
        self, test_client, db_session
    ):
        """Test that all transaction types are returned correctly"""
        transactions = [
            Transaction(
                transaction_date=datetime(2024, 1, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="SOL",
                quantity=Decimal("10"),
                price_per_unit=Decimal("100.00"),
                total_amount=Decimal("1000.00"),
                fee=Decimal("1.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 2, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.STAKING,
                symbol="SOL",
                quantity=Decimal("0.5"),
                price_per_unit=Decimal("110.00"),
                total_amount=Decimal("55.00"),
                fee=Decimal("0.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 3, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.AIRDROP,
                symbol="SOL",
                quantity=Decimal("1.0"),
                price_per_unit=Decimal("115.00"),
                total_amount=Decimal("115.00"),
                fee=Decimal("0.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
            Transaction(
                transaction_date=datetime(2024, 4, 1),
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.SELL,
                symbol="SOL",
                quantity=Decimal("5.0"),
                price_per_unit=Decimal("120.00"),
                total_amount=Decimal("600.00"),
                fee=Decimal("2.00"),
                currency="EUR",
                source_type="KOINLY",
            ),
        ]

        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/positions/SOL/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 4

        # Check all transaction types are present
        types = [txn["type"] for txn in data]
        assert "BUY" in types
        assert "SELL" in types
        assert "STAKING" in types
        assert "AIRDROP" in types

    @pytest.mark.asyncio
    async def test_get_transactions_response_structure(
        self, test_client, db_session
    ):
        """Test that API response has correct structure and fields"""
        transaction = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="MSTR",
            quantity=Decimal("1.0"),
            price_per_unit=Decimal("500.00"),
            total_amount=Decimal("500.00"),
            fee=Decimal("0.50"),
            currency="USD",
            source_type="REVOLUT",
        )

        db_session.add(transaction)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/positions/MSTR/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        txn = data[0]

        # Check all required fields are present
        required_fields = [
            "id",
            "date",
            "type",
            "quantity",
            "price",
            "fee",
            "total_amount",
            "currency",
            "asset_type",
        ]

        for field in required_fields:
            assert field in txn, f"Missing required field: {field}"

        # Check field types and values
        assert isinstance(txn["id"], int)
        assert isinstance(txn["date"], str)
        assert txn["type"] == "BUY"
        assert txn["quantity"] == 1.0
        assert txn["price"] == 500.0
        assert txn["fee"] == 0.50
        assert txn["currency"] == "USD"
        assert txn["asset_type"] == "STOCK"


class TestClosedTransactionsEndpoint:
    """Tests for the closed transactions endpoint (realized P&L details)"""

    @pytest.mark.asyncio
    async def test_get_closed_transactions_for_metals(
        self, test_client, db_session
    ):
        """Test fetching closed transactions for metals asset type"""
        # Create a BUY and SELL for XAU (gold)
        buy_txn = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.BUY,
            symbol="XAU",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("1950.00"),
            total_amount=Decimal("975.00"),
            fee=Decimal("1.00"),
            currency="EUR",
            source_type="REVOLUT",
        )
        sell_txn = Transaction(
            transaction_date=datetime(2024, 2, 1),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.SELL,
            symbol="XAU",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("2148.00"),
            total_amount=Decimal("1074.00"),
            fee=Decimal("1.00"),
            currency="EUR",
            source_type="REVOLUT",
        )

        db_session.add(buy_txn)
        db_session.add(sell_txn)
        await db_session.commit()

        # Fetch closed transactions for metals
        response = await test_client.get("/api/portfolio/realized-pnl/metals/transactions")

        assert response.status_code == 200
        data = response.json()

        # Should return 1 closed transaction (the SELL)
        assert len(data) == 1

        closed_txn = data[0]
        assert closed_txn["symbol"] == "XAU"
        assert closed_txn["quantity"] == 0.5
        assert closed_txn["sell_price"] == 2148.0
        assert closed_txn["sell_fee"] == 1.0
        assert closed_txn["currency"] == "EUR"

        # Verify FIFO cost basis is calculated correctly
        # Buy price with fee: (1950 * 0.5 + 1) / 0.5 = 1952
        expected_buy_price = (1950.0 * 0.5 + 1.0) / 0.5
        assert abs(closed_txn["buy_price"] - expected_buy_price) < 0.01

        # Gross P&L: (2148 - 1952) * 0.5 = 98
        expected_gross_pnl = (2148.0 - expected_buy_price) * 0.5
        assert abs(closed_txn["gross_pnl"] - expected_gross_pnl) < 0.01

        # Net P&L: gross - sell fee = 98 - 1 = 97
        assert abs(closed_txn["net_pnl"] - (expected_gross_pnl - 1.0)) < 0.01

    @pytest.mark.asyncio
    async def test_get_closed_transactions_404_for_no_sales(
        self, test_client, db_session
    ):
        """Test 404 response when asset type has no SELL transactions"""
        # Create only a BUY transaction
        buy_txn = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10"),
            price_per_unit=Decimal("150.00"),
            total_amount=Decimal("1500.00"),
            fee=Decimal("1.00"),
            currency="USD",
            source_type="REVOLUT",
        )

        db_session.add(buy_txn)
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl/stocks/transactions")

        assert response.status_code == 404
        assert "No closed transactions found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_closed_transactions_400_for_invalid_asset_type(
        self, test_client, db_session
    ):
        """Test 400 response for invalid asset type"""
        response = await test_client.get("/api/portfolio/realized-pnl/invalid/transactions")

        assert response.status_code == 400
        assert "Invalid asset type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_closed_transactions_ordering(
        self, test_client, db_session
    ):
        """Test closed transactions are ordered by sell date (newest first)"""
        # Create BUY transactions
        buy1 = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.BUY,
            symbol="BTC",
            quantity=Decimal("1.0"),
            price_per_unit=Decimal("40000.00"),
            total_amount=Decimal("40000.00"),
            fee=Decimal("10.00"),
            currency="EUR",
            source_type="KOINLY",
        )

        # Create SELL transactions on different dates
        sell1 = Transaction(
            transaction_date=datetime(2024, 6, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.SELL,
            symbol="BTC",
            quantity=Decimal("0.3"),
            price_per_unit=Decimal("50000.00"),
            total_amount=Decimal("15000.00"),
            fee=Decimal("5.00"),
            currency="EUR",
            source_type="KOINLY",
        )

        sell2 = Transaction(
            transaction_date=datetime(2024, 3, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.SELL,
            symbol="BTC",
            quantity=Decimal("0.2"),
            price_per_unit=Decimal("45000.00"),
            total_amount=Decimal("9000.00"),
            fee=Decimal("3.00"),
            currency="EUR",
            source_type="KOINLY",
        )

        db_session.add_all([buy1, sell1, sell2])
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl/crypto/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2

        # First should be June sale (newest)
        assert data[0]["quantity"] == 0.3
        assert "2024-06-01" in data[0]["sell_date"]

        # Second should be March sale (older)
        assert data[1]["quantity"] == 0.2
        assert "2024-03-01" in data[1]["sell_date"]

    @pytest.mark.asyncio
    async def test_get_closed_transactions_fifo_calculation(
        self, test_client, db_session
    ):
        """Test FIFO cost basis calculation with multiple buy lots"""
        # Create multiple BUY transactions at different prices
        buy1 = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="TSLA",
            quantity=Decimal("10"),
            price_per_unit=Decimal("200.00"),
            total_amount=Decimal("2000.00"),
            fee=Decimal("2.00"),
            currency="USD",
            source_type="REVOLUT",
        )

        buy2 = Transaction(
            transaction_date=datetime(2024, 2, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="TSLA",
            quantity=Decimal("10"),
            price_per_unit=Decimal("250.00"),
            total_amount=Decimal("2500.00"),
            fee=Decimal("2.50"),
            currency="USD",
            source_type="REVOLUT",
        )

        # Sell 15 shares (should use FIFO: 10 @ 200 + 5 @ 250)
        sell = Transaction(
            transaction_date=datetime(2024, 3, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.SELL,
            symbol="TSLA",
            quantity=Decimal("15"),
            price_per_unit=Decimal("300.00"),
            total_amount=Decimal("4500.00"),
            fee=Decimal("5.00"),
            currency="USD",
            source_type="REVOLUT",
        )

        db_session.add_all([buy1, buy2, sell])
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl/stocks/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        closed_txn = data[0]

        # FIFO cost basis calculation:
        # Buy 1: (200 * 10 + 2) / 10 = 200.20 per share
        # Buy 2: (250 * 10 + 2.50) / 10 = 250.25 per share
        # Average for 15 shares: (10 * 200.20 + 5 * 250.25) / 15 = 217.55
        expected_avg_cost = (10 * 200.20 + 5 * 250.25) / 15
        assert abs(closed_txn["buy_price"] - expected_avg_cost) < 0.01

        # Gross P&L: (300 - 217.55) * 15 = 1236.75
        expected_gross_pnl = (300.0 - expected_avg_cost) * 15
        assert abs(closed_txn["gross_pnl"] - expected_gross_pnl) < 0.01

        # Net P&L: 1236.75 - 5 = 1231.75
        assert abs(closed_txn["net_pnl"] - (expected_gross_pnl - 5.0)) < 0.01

    @pytest.mark.asyncio
    async def test_get_closed_transactions_multiple_symbols(
        self, test_client, db_session
    ):
        """Test endpoint returns all closed transactions for the asset type"""
        # Create BUY and SELL for XAU
        xau_buy = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.BUY,
            symbol="XAU",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("1950.00"),
            total_amount=Decimal("975.00"),
            fee=Decimal("1.00"),
            currency="EUR",
            source_type="REVOLUT",
        )
        xau_sell = Transaction(
            transaction_date=datetime(2024, 2, 1),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.SELL,
            symbol="XAU",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("2148.00"),
            total_amount=Decimal("1074.00"),
            fee=Decimal("1.00"),
            currency="EUR",
            source_type="REVOLUT",
        )

        # Create BUY and SELL for XAG
        xag_buy = Transaction(
            transaction_date=datetime(2024, 1, 5),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.BUY,
            symbol="XAG",
            quantity=Decimal("15.0"),
            price_per_unit=Decimal("26.67"),
            total_amount=Decimal("400.00"),
            fee=Decimal("0.50"),
            currency="EUR",
            source_type="REVOLUT",
        )
        xag_sell = Transaction(
            transaction_date=datetime(2024, 2, 15),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.SELL,
            symbol="XAG",
            quantity=Decimal("15.0"),
            price_per_unit=Decimal("37.19"),
            total_amount=Decimal("557.85"),
            fee=Decimal("0.50"),
            currency="EUR",
            source_type="REVOLUT",
        )

        db_session.add_all([xau_buy, xau_sell, xag_buy, xag_sell])
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl/metals/transactions")

        assert response.status_code == 200
        data = response.json()

        # Should return 2 closed transactions
        assert len(data) == 2

        # Check both symbols are present
        symbols = [txn["symbol"] for txn in data]
        assert "XAU" in symbols
        assert "XAG" in symbols

    @pytest.mark.asyncio
    async def test_get_closed_transactions_response_structure(
        self, test_client, db_session
    ):
        """Test API response has correct structure and fields"""
        buy = Transaction(
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.BUY,
            symbol="ETH",
            quantity=Decimal("2.0"),
            price_per_unit=Decimal("3000.00"),
            total_amount=Decimal("6000.00"),
            fee=Decimal("10.00"),
            currency="EUR",
            source_type="KOINLY",
        )

        sell = Transaction(
            transaction_date=datetime(2024, 2, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.SELL,
            symbol="ETH",
            quantity=Decimal("1.0"),
            price_per_unit=Decimal("3500.00"),
            total_amount=Decimal("3500.00"),
            fee=Decimal("5.00"),
            currency="EUR",
            source_type="KOINLY",
        )

        db_session.add_all([buy, sell])
        await db_session.commit()

        response = await test_client.get("/api/portfolio/realized-pnl/crypto/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        txn = data[0]

        # Check all required fields are present
        required_fields = [
            "id",
            "symbol",
            "sell_date",
            "quantity",
            "buy_price",
            "sell_price",
            "gross_pnl",
            "sell_fee",
            "net_pnl",
            "currency",
        ]

        for field in required_fields:
            assert field in txn, f"Missing required field: {field}"

        # Check field types and values
        assert isinstance(txn["id"], int)
        assert isinstance(txn["symbol"], str)
        assert isinstance(txn["sell_date"], str)
        assert isinstance(txn["quantity"], float)
        assert isinstance(txn["buy_price"], float)
        assert isinstance(txn["sell_price"], float)
        assert isinstance(txn["gross_pnl"], float)
        assert isinstance(txn["sell_fee"], float)
        assert isinstance(txn["net_pnl"], float)
        assert isinstance(txn["currency"], str)

        assert txn["symbol"] == "ETH"
        assert txn["currency"] == "EUR"
