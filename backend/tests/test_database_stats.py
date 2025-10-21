# ABOUTME: Unit tests for database statistics functionality
# ABOUTME: Tests the detailed stats endpoint and service methods

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_reset_service import DatabaseResetService
from models import Base, Transaction, AssetType, TransactionType
from database_router import router
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

# Test database setup
@pytest.fixture
def test_db():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_transactions(test_db):
    """Create sample transactions for testing"""
    transactions = [
        Transaction(
            transaction_date=datetime(2023, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10"),
            price_per_unit=Decimal("150"),
            total_amount=Decimal("1500"),
            currency="USD"
        ),
        Transaction(
            transaction_date=datetime(2023, 2, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="GOOGL",
            quantity=Decimal("5"),
            price_per_unit=Decimal("100"),
            total_amount=Decimal("500"),
            currency="USD"
        ),
        Transaction(
            transaction_date=datetime(2023, 3, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.BUY,
            symbol="BTC",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("30000"),
            total_amount=Decimal("15000"),
            currency="USD"
        ),
        Transaction(
            transaction_date=datetime(2023, 4, 1),
            asset_type=AssetType.METAL,
            transaction_type=TransactionType.BUY,
            symbol="XAU",
            quantity=Decimal("2"),
            price_per_unit=Decimal("2000"),
            total_amount=Decimal("4000"),
            currency="USD"
        ),
        Transaction(
            transaction_date=datetime(2023, 5, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.SELL,
            symbol="AAPL",
            quantity=Decimal("5"),
            price_per_unit=Decimal("160"),
            total_amount=Decimal("800"),
            currency="USD"
        ),
        Transaction(
            transaction_date=datetime(2023, 6, 1),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.STAKING,
            symbol="ETH",
            quantity=Decimal("0.1"),
            price_per_unit=Decimal("0"),
            total_amount=Decimal("0"),
            currency="USD"
        )
    ]

    for transaction in transactions:
        test_db.add(transaction)
    test_db.commit()

    return transactions


def test_get_detailed_stats_empty_database(test_db):
    """Test getting detailed stats when database is empty"""
    service = DatabaseResetService(test_db)
    stats = service.get_detailed_stats()

    assert stats["transactions"]["total"] == 0
    assert stats["transactions"]["byAssetType"] == {}
    assert stats["transactions"]["byTransactionType"] == {}
    assert stats["transactions"]["dateRange"] == {}
    assert stats["symbols"]["total"] == 0
    assert stats["symbols"]["topSymbols"] == []
    assert stats["database"]["isHealthy"] == True
    assert stats["database"]["totalRecords"] == 0


def test_get_detailed_stats_with_data(test_db, sample_transactions):
    """Test getting detailed stats with sample data"""
    service = DatabaseResetService(test_db)
    stats = service.get_detailed_stats()

    # Check total transactions
    assert stats["transactions"]["total"] == 6

    # Check asset type breakdown
    assert stats["transactions"]["byAssetType"]["STOCK"] == 3
    assert stats["transactions"]["byAssetType"]["CRYPTO"] == 2
    assert stats["transactions"]["byAssetType"]["METAL"] == 1

    # Check transaction type breakdown
    assert stats["transactions"]["byTransactionType"]["BUY"] == 4
    assert stats["transactions"]["byTransactionType"]["SELL"] == 1
    assert stats["transactions"]["byTransactionType"]["STAKING"] == 1

    # Check date range
    assert "2023-01-01" in stats["transactions"]["dateRange"]["earliest"]
    assert "2023-06-01" in stats["transactions"]["dateRange"]["latest"]

    # Check unique symbols
    assert stats["symbols"]["total"] == 5  # AAPL, GOOGL, BTC, XAU, ETH

    # Check top symbols
    top_symbols = {item["symbol"]: item["count"] for item in stats["symbols"]["topSymbols"]}
    assert top_symbols["AAPL"] == 2  # 1 buy + 1 sell
    assert top_symbols["GOOGL"] == 1
    assert top_symbols["BTC"] == 1
    assert top_symbols["XAU"] == 1
    assert top_symbols["ETH"] == 1


def test_get_detailed_stats_top_symbols_limit(test_db):
    """Test that top symbols are limited to 10"""
    # Create more than 10 different symbols
    for i in range(15):
        transaction = Transaction(
            transaction_date=datetime(2023, 1, i + 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol=f"SYM{i:02d}",
            quantity=Decimal("1"),
            price_per_unit=Decimal("100"),
            total_amount=Decimal("100"),
            currency="USD"
        )
        test_db.add(transaction)
    test_db.commit()

    service = DatabaseResetService(test_db)
    stats = service.get_detailed_stats()

    # Should only return top 10
    assert len(stats["symbols"]["topSymbols"]) == 10
    assert stats["symbols"]["total"] == 15


def test_detailed_stats_endpoint():
    """Test the /api/database/stats/detailed endpoint"""
    response = client.get("/api/database/stats/detailed")
    assert response.status_code == 200

    data = response.json()
    assert "transactions" in data
    assert "symbols" in data
    assert "database" in data
    assert "total" in data["transactions"]
    assert "byAssetType" in data["transactions"]
    assert "byTransactionType" in data["transactions"]
    assert "dateRange" in data["transactions"]
    assert "total" in data["symbols"]
    assert "topSymbols" in data["symbols"]
    assert "tablesCount" in data["database"]
    assert "isHealthy" in data["database"]


def test_detailed_stats_with_import_timestamp(test_db):
    """Test that last import timestamp is correctly retrieved"""
    transaction = Transaction(
        transaction_date=datetime(2023, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=Decimal("150"),
        total_amount=Decimal("1500"),
        currency="USD",
        import_timestamp=datetime(2023, 12, 1, 10, 30, 45)
    )
    test_db.add(transaction)
    test_db.commit()

    service = DatabaseResetService(test_db)
    stats = service.get_detailed_stats()

    assert stats["database"]["lastImport"] is not None
    assert "2023-12-01" in stats["database"]["lastImport"]


def test_detailed_stats_error_handling(test_db):
    """Test error handling in detailed stats"""
    # Close the session to simulate database error
    test_db.close()

    service = DatabaseResetService(test_db)
    stats = service.get_detailed_stats()

    # When database is closed, it should still return a valid structure (graceful degradation)
    # The method handles errors gracefully and returns empty stats
    assert stats["transactions"]["total"] == 0
    assert stats["database"]["isHealthy"] == True  # Because it gracefully handles the error
    assert stats["symbols"]["total"] == 0


def test_basic_stats_compatibility(test_db, sample_transactions):
    """Test that basic stats are still working correctly"""
    service = DatabaseResetService(test_db)
    basic_stats = service.get_database_stats()

    assert basic_stats["table_counts"]["transactions"] == 6
    assert basic_stats["total_records"] == 6
    assert basic_stats["database_ready"] == True
    assert "transaction_date_range" in basic_stats


def test_detailed_stats_multiple_same_symbols(test_db):
    """Test stats when multiple transactions have the same symbol"""
    # Create multiple transactions for the same symbol
    for i in range(5):
        transaction = Transaction(
            transaction_date=datetime(2023, 1, i + 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("10"),
            price_per_unit=Decimal("150"),
            total_amount=Decimal("1500"),
            currency="USD"
        )
        test_db.add(transaction)

    # Add one transaction for another symbol
    transaction = Transaction(
        transaction_date=datetime(2023, 2, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="GOOGL",
        quantity=Decimal("5"),
        price_per_unit=Decimal("100"),
        total_amount=Decimal("500"),
        currency="USD"
    )
    test_db.add(transaction)
    test_db.commit()

    service = DatabaseResetService(test_db)
    stats = service.get_detailed_stats()

    # Check that AAPL appears at the top with correct count
    assert stats["symbols"]["topSymbols"][0]["symbol"] == "AAPL"
    assert stats["symbols"]["topSymbols"][0]["count"] == 5
    assert stats["symbols"]["topSymbols"][1]["symbol"] == "GOOGL"
    assert stats["symbols"]["topSymbols"][1]["count"] == 1
    assert stats["symbols"]["total"] == 2  # Only 2 unique symbols