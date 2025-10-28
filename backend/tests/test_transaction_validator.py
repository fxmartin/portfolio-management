# ABOUTME: Tests for transaction validator service - business rules and validation
# ABOUTME: Covers all validation scenarios including negative holdings, duplicates, and date validation

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from transaction_validator import TransactionValidator, ValidationLevel
from models import Transaction, AssetType, TransactionType, Base


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
async def validator(db_session):
    """Create a TransactionValidator instance"""
    return TransactionValidator(db_session)


@pytest_asyncio.fixture
async def existing_transactions(db_session):
    """Create some existing transactions for testing"""
    transactions = [
        Transaction(
            id=1,
            transaction_date=datetime(2024, 1, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            quantity=Decimal("100"),
            price_per_unit=Decimal("150.00"),
            fee=Decimal("1.99"),
            currency="USD",
            source="CSV"
        ),
        Transaction(
            id=2,
            transaction_date=datetime(2024, 1, 15),
            asset_type=AssetType.CRYPTO,
            transaction_type=TransactionType.BUY,
            symbol="BTC",
            quantity=Decimal("0.5"),
            price_per_unit=Decimal("50000"),
            fee=Decimal("10.00"),
            currency="USD",
            source="CSV"
        ),
        Transaction(
            id=3,
            transaction_date=datetime(2024, 2, 1),
            asset_type=AssetType.STOCK,
            transaction_type=TransactionType.SELL,
            symbol="AAPL",
            quantity=Decimal("30"),
            price_per_unit=Decimal("160.00"),
            fee=Decimal("1.99"),
            currency="USD",
            source="CSV"
        )
    ]

    for txn in transactions:
        db_session.add(txn)
    await db_session.commit()

    return transactions


# ============================================================================
# Test validate_create
# ============================================================================

@pytest.mark.asyncio
async def test_validate_create_valid_buy(validator):
    """Test validation of a valid BUY transaction"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is True
    assert len([m for m in result.messages if m.level == ValidationLevel.ERROR]) == 0


@pytest.mark.asyncio
async def test_validate_create_missing_symbol(validator):
    """Test validation fails when symbol is missing"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="",
        quantity=Decimal("10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("symbol" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_zero_quantity(validator):
    """Test validation fails for zero quantity"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("0"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("quantity" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_negative_quantity(validator):
    """Test validation fails for negative quantity"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("-10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("quantity" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_buy_requires_price(validator):
    """Test BUY transaction requires price"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=None,
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("price" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_sell_requires_price(validator):
    """Test SELL transaction requires price"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.SELL,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=None,
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("price" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_negative_price(validator):
    """Test validation fails for negative price"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=Decimal("-150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("price" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_negative_fee(validator):
    """Test validation fails for negative fee"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("-1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("fee" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_fee_exceeds_value(validator):
    """Test warning when fee exceeds transaction value"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("1"),
        price_per_unit=Decimal("10.00"),
        fee=Decimal("20.00"),
        currency="USD"
    )

    # Should still be valid but with warning
    assert result.valid is True
    assert any("fee" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.WARNING)


@pytest.mark.asyncio
async def test_validate_create_future_date(validator):
    """Test validation fails for future date"""
    future_date = datetime.now() + timedelta(days=1)

    result = await validator.validate_create(
        transaction_date=future_date,
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("future" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_notes_too_long(validator):
    """Test validation fails for notes exceeding 500 characters"""
    long_notes = "x" * 501

    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD",
        notes=long_notes
    )

    assert result.valid is False
    assert any("notes" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_sell_exceeds_holdings(validator, existing_transactions):
    """Test validation fails when selling more than owned"""
    # existing_transactions has 100 AAPL bought and 30 sold = 70 remaining

    result = await validator.validate_create(
        transaction_date=datetime(2024, 3, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.SELL,
        symbol="AAPL",
        quantity=Decimal("100"),  # More than the 70 available
        price_per_unit=Decimal("160.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is False
    assert any("cannot sell" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_create_sell_within_holdings(validator, existing_transactions):
    """Test validation passes when selling within available holdings"""
    # existing_transactions has 100 AAPL bought and 30 sold = 70 remaining

    result = await validator.validate_create(
        transaction_date=datetime(2024, 3, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.SELL,
        symbol="AAPL",
        quantity=Decimal("50"),  # Within the 70 available
        price_per_unit=Decimal("160.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    assert result.valid is True


@pytest.mark.asyncio
async def test_validate_create_duplicate_warning(validator, existing_transactions):
    """Test warning for potential duplicate transaction"""
    # Create transaction similar to existing one
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 1, 0, 0, 30),  # Within same minute
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("100"),  # Same quantity
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD"
    )

    # Should be valid but with duplicate warning
    assert result.valid is True
    assert any("duplicate" in msg.message.lower() or "similar" in msg.message.lower()
               for msg in result.messages if msg.level == ValidationLevel.WARNING)


@pytest.mark.asyncio
async def test_validate_create_currency_consistency_warning(validator, existing_transactions):
    """Test warning when using different currency for same symbol"""
    result = await validator.validate_create(
        transaction_date=datetime(2024, 1, 5),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",  # Existing AAPL is in USD
        quantity=Decimal("10"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="EUR"  # Different currency
    )

    # Should be valid but with currency warning
    assert result.valid is True
    assert any("currency" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.WARNING)


# ============================================================================
# Test validate_update
# ============================================================================

@pytest.mark.asyncio
async def test_validate_update_valid(validator, existing_transactions):
    """Test validation of valid update"""
    result = await validator.validate_update(
        transaction_id=1,
        new_values={"quantity": Decimal("110")}
    )

    assert result.valid is True


@pytest.mark.asyncio
async def test_validate_update_nonexistent_transaction(validator):
    """Test validation fails for non-existent transaction"""
    result = await validator.validate_update(
        transaction_id=9999,
        new_values={"quantity": Decimal("10")}
    )

    assert result.valid is False
    assert any("not found" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_update_zero_quantity(validator, existing_transactions):
    """Test validation fails when updating to zero quantity"""
    result = await validator.validate_update(
        transaction_id=1,
        new_values={"quantity": Decimal("0")}
    )

    assert result.valid is False
    assert any("quantity" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_update_negative_price(validator, existing_transactions):
    """Test validation fails when updating to negative price"""
    result = await validator.validate_update(
        transaction_id=1,
        new_values={"price_per_unit": Decimal("-100")}
    )

    assert result.valid is False
    assert any("price" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_update_future_date(validator, existing_transactions):
    """Test validation fails when updating to future date"""
    future_date = datetime.now() + timedelta(days=1)

    result = await validator.validate_update(
        transaction_id=1,
        new_values={"transaction_date": future_date}
    )

    assert result.valid is False
    assert any("future" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_update_csv_import_warning(validator, existing_transactions):
    """Test warning when updating CSV imported transaction"""
    result = await validator.validate_update(
        transaction_id=1,  # This is a CSV import
        new_values={"quantity": Decimal("110")}
    )

    # Should have warning about CSV import
    assert any("imported" in msg.message.lower() or "csv" in msg.message.lower()
               for msg in result.messages if msg.level == ValidationLevel.WARNING)


# ============================================================================
# Test validate_delete
# ============================================================================

@pytest.mark.asyncio
async def test_validate_delete_valid(validator, existing_transactions):
    """Test validation of valid deletion"""
    result = await validator.validate_delete(transaction_id=3)  # SELL transaction

    assert result.valid is True


@pytest.mark.asyncio
async def test_validate_delete_nonexistent(validator):
    """Test validation fails for non-existent transaction"""
    result = await validator.validate_delete(transaction_id=9999)

    assert result.valid is False
    assert any("not found" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


@pytest.mark.asyncio
async def test_validate_delete_sell_warning(validator, existing_transactions):
    """Test warning when deleting SELL transaction (affects realized P&L)"""
    result = await validator.validate_delete(transaction_id=3)  # SELL transaction

    # Should have warning about realized P&L
    assert any("realized" in msg.message.lower() or "p&l" in msg.message.lower()
               for msg in result.messages if msg.level == ValidationLevel.WARNING)


@pytest.mark.asyncio
async def test_validate_delete_would_create_negative_holdings(validator, db_session):
    """Test validation fails when deletion would create negative holdings"""
    # Create a scenario: BUY 50, SELL 40, then try to delete the BUY
    buy_txn = Transaction(
        id=10,
        transaction_date=datetime(2024, 1, 1),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="TEST",
        quantity=Decimal("50"),
        price_per_unit=Decimal("100"),
        fee=Decimal("1"),
        currency="USD",
        source="MANUAL"
    )
    sell_txn = Transaction(
        id=11,
        transaction_date=datetime(2024, 1, 15),
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.SELL,
        symbol="TEST",
        quantity=Decimal("40"),
        price_per_unit=Decimal("110"),
        fee=Decimal("1"),
        currency="USD",
        source="MANUAL"
    )

    db_session.add(buy_txn)
    db_session.add(sell_txn)
    await db_session.commit()

    # Try to delete the BUY - should fail
    result = await validator.validate_delete(transaction_id=10)

    assert result.valid is False
    assert any("negative" in msg.message.lower() for msg in result.messages if msg.level == ValidationLevel.ERROR)


# ============================================================================
# Test helper methods
# ============================================================================

@pytest.mark.asyncio
async def test_get_holdings_at_date(validator, existing_transactions):
    """Test calculating holdings at a specific date"""
    # At 2024-02-15, should have: 100 bought - 30 sold = 70 AAPL
    holdings = await validator._get_holdings_at_date(
        symbol="AAPL",
        date=datetime(2024, 2, 15)
    )

    assert holdings == Decimal("70")


@pytest.mark.asyncio
async def test_get_holdings_at_date_no_transactions(validator):
    """Test holdings returns zero when no transactions"""
    holdings = await validator._get_holdings_at_date(
        symbol="UNKNOWN",
        date=datetime(2024, 1, 1)
    )

    assert holdings == Decimal("0")


@pytest.mark.asyncio
async def test_detect_duplicates(validator, existing_transactions):
    """Test duplicate detection finds potential duplicates"""
    # Add a duplicate-like transaction
    dup_txn = Transaction(
        id=4,
        transaction_date=datetime(2024, 1, 1, 0, 0, 30),  # Same minute as ID 1
        asset_type=AssetType.STOCK,
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        quantity=Decimal("100"),
        price_per_unit=Decimal("150.00"),
        fee=Decimal("1.99"),
        currency="USD",
        source="CSV"
    )
    validator.db.add(dup_txn)
    await validator.db.commit()

    duplicate_groups = await validator.detect_duplicates(symbol="AAPL")

    # Should find at least one group with multiple transactions
    assert len(duplicate_groups) > 0
    assert any(len(group) > 1 for group in duplicate_groups)


@pytest.mark.asyncio
async def test_detect_duplicates_no_duplicates(validator, existing_transactions):
    """Test duplicate detection returns empty when no duplicates"""
    duplicate_groups = await validator.detect_duplicates(symbol="UNIQUE")

    assert len(duplicate_groups) == 0
