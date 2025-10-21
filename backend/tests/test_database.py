# ABOUTME: Unit tests for database models and operations
# ABOUTME: Tests database connection, model creation, and basic CRUD operations

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, Transaction, Position, PriceHistory, PortfolioSnapshot, AssetType, TransactionType

# Test database URL (using SQLite for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_session(test_engine):
    """Create test database session"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


class TestDatabaseModels:
    """Test database models"""

    def test_create_transaction(self, test_session):
        """Test creating a transaction"""
        transaction = Transaction(
            transaction_date=datetime.now(),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10.5"),
            price_per_unit=Decimal("150.25"),
            total_amount=Decimal("1577.625"),
            currency="USD",
            fee=Decimal("5.0"),
            source_file="test.csv",
            source_type="REVOLUT"
        )

        test_session.add(transaction)
        test_session.commit()

        # Retrieve and verify
        result = test_session.query(Transaction).filter_by(symbol="AAPL").first()
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.quantity == Decimal("10.5")
        assert result.asset_type == AssetType.STOCK

    def test_create_position(self, test_session):
        """Test creating a position"""
        position = Position(
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            quantity=Decimal("0.5"),
            avg_cost_basis=Decimal("30000"),
            total_cost_basis=Decimal("15000"),
            currency="USD",
            cost_lots=[{"quantity": 0.5, "cost": 30000, "date": "2024-01-01"}]
        )

        test_session.add(position)
        test_session.commit()

        # Retrieve and verify
        result = test_session.query(Position).filter_by(symbol="BTC").first()
        assert result is not None
        assert result.symbol == "BTC"
        assert result.quantity == Decimal("0.5")
        assert result.asset_type == AssetType.CRYPTO

    def test_create_price_history(self, test_session):
        """Test creating price history"""
        price = PriceHistory(
            symbol="TSLA",
            asset_type=AssetType.STOCK,
            price_date=datetime.now(),
            open_price=Decimal("250.50"),
            high_price=Decimal("255.00"),
            low_price=Decimal("248.00"),
            close_price=Decimal("252.75"),
            volume=Decimal("10000000"),
            currency="USD",
            source="YAHOO"
        )

        test_session.add(price)
        test_session.commit()

        # Retrieve and verify
        result = test_session.query(PriceHistory).filter_by(symbol="TSLA").first()
        assert result is not None
        assert result.symbol == "TSLA"
        assert result.close_price == Decimal("252.75")
        assert result.source == "YAHOO"

    def test_create_portfolio_snapshot(self, test_session):
        """Test creating portfolio snapshot"""
        snapshot = PortfolioSnapshot(
            snapshot_date=datetime.now(),
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("10000.00"),
            invested_value=Decimal("90000.00"),
            total_cost_basis=Decimal("85000.00"),
            total_unrealized_pnl=Decimal("5000.00"),
            total_unrealized_pnl_percent=Decimal("5.88"),
            positions_snapshot=[
                {"symbol": "AAPL", "quantity": 100, "value": 15000, "pnl": 500},
                {"symbol": "BTC", "quantity": 0.5, "value": 20000, "pnl": 2000}
            ],
            metals_percent=Decimal("10.00"),
            stocks_percent=Decimal("50.00"),
            crypto_percent=Decimal("30.00"),
            cash_percent=Decimal("10.00"),
            currency="USD"
        )

        test_session.add(snapshot)
        test_session.commit()

        # Retrieve and verify
        result = test_session.query(PortfolioSnapshot).first()
        assert result is not None
        assert result.total_value == Decimal("100000.00")
        assert result.cash_balance == Decimal("10000.00")
        assert len(result.positions_snapshot) == 2

    def test_transaction_unique_constraint(self, test_session):
        """Test transaction unique constraint"""
        trans_date = datetime.now()

        # Create first transaction
        trans1 = Transaction(
            transaction_date=trans_date,
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.BUY,
            symbol="XAU",
            quantity=Decimal("1.0"),
            price_per_unit=Decimal("1800"),
            total_amount=Decimal("1800")
        )

        test_session.add(trans1)
        test_session.commit()

        # Try to create duplicate (should fail)
        trans2 = Transaction(
            transaction_date=trans_date,
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.BUY,
            symbol="XAU",
            quantity=Decimal("1.0"),
            price_per_unit=Decimal("1850"),
            total_amount=Decimal("1850")
        )

        test_session.add(trans2)
        with pytest.raises(Exception):  # Should raise integrity error
            test_session.commit()

    def test_position_unique_symbol(self, test_session):
        """Test position unique symbol constraint"""
        # Create first position
        pos1 = Position(
            symbol="MSFT",
            asset_type=AssetType.STOCK,
            quantity=Decimal("50")
        )

        test_session.add(pos1)
        test_session.commit()

        # Try to create duplicate symbol (should fail)
        pos2 = Position(
            symbol="MSFT",
            asset_type=AssetType.STOCK,
            quantity=Decimal("100")
        )

        test_session.add(pos2)
        with pytest.raises(Exception):  # Should raise integrity error
            test_session.commit()

    def test_transaction_position_relationship(self, test_session):
        """Test relationship between transaction and position"""
        # Create transaction
        transaction = Transaction(
            transaction_date=datetime.now(),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="GOOGL",
            quantity=Decimal("5"),
            price_per_unit=Decimal("100"),
            total_amount=Decimal("500")
        )
        test_session.add(transaction)
        test_session.commit()

        # Create position linked to transaction
        position = Position(
            symbol="GOOGL",
            asset_type=AssetType.STOCK,
            quantity=Decimal("5"),
            transaction_id=transaction.id
        )
        test_session.add(position)
        test_session.commit()

        # Verify relationship
        result = test_session.query(Position).filter_by(symbol="GOOGL").first()
        assert result.transaction_id == transaction.id
        assert result.transaction.symbol == "GOOGL"


class TestAssetTypes:
    """Test asset type enumerations"""

    def test_asset_types(self):
        """Test asset type values"""
        assert AssetType.METAL.value == "METAL"
        assert AssetType.STOCK.value == "STOCK"
        assert AssetType.CRYPTO.value == "CRYPTO"

    def test_transaction_types(self):
        """Test transaction type values"""
        assert TransactionType.BUY.value == "BUY"
        assert TransactionType.SELL.value == "SELL"
        assert TransactionType.DIVIDEND.value == "DIVIDEND"
        assert TransactionType.STAKING.value == "STAKING"
        assert TransactionType.FEE.value == "FEE"