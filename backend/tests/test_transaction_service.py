# ABOUTME: Unit tests for transaction service database operations
# ABOUTME: Tests transaction storage, duplicate detection, and batch imports

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transaction_service import TransactionService, DuplicateHandler
from models import Transaction, AssetType, TransactionType


class TestTransactionService:
    """Test suite for TransactionService"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()

        # Properly mock execute and its chain
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        session.execute = AsyncMock(return_value=mock_result)

        return session

    @pytest.fixture
    def sample_transactions(self):
        """Sample transaction data for testing"""
        return [
            {
                "transaction_date": datetime(2024, 1, 15, 10, 30),
                "asset_type": AssetType.STOCK,
                "transaction_type": TransactionType.BUY,
                "symbol": "AAPL",
                "quantity": 10.0,
                "price_per_unit": 150.50,
                "total_amount": 1505.00,
                "currency": "USD",
                "fee": 1.00,
                "source_type": "REVOLUT",
                "raw_data": {"test": "data"}
            },
            {
                "transaction_date": datetime(2024, 1, 16, 14, 20),
                "asset_type": AssetType.CRYPTO,
                "transaction_type": TransactionType.BUY,
                "symbol": "BTC",
                "quantity": 0.01,
                "price_per_unit": 45000.00,
                "total_amount": 450.00,
                "currency": "USD",
                "fee": 2.50,
                "source_type": "KOINLY",
                "raw_data": {"test": "crypto"}
            }
        ]

    @pytest.mark.asyncio
    async def test_store_transactions_success(self, mock_session, sample_transactions):
        """Test successful transaction storage"""
        service = TransactionService(mock_session)

        # Mock no duplicates found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call store_transactions
        saved, skipped, failed = await service.store_transactions(
            sample_transactions,
            "test_file.csv"
        )

        # Verify results
        assert len(saved) == 2
        assert len(skipped) == 0
        assert len(failed) == 0

        # Verify session methods were called
        assert mock_session.add.call_count == 2
        assert mock_session.flush.call_count == 2
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_transactions_with_duplicates(self, mock_session, sample_transactions):
        """Test transaction storage with duplicate detection"""
        service = TransactionService(mock_session)

        # Mock finding a duplicate for the first transaction
        existing_tx = MagicMock()
        existing_tx.id = 123

        mock_result = AsyncMock()
        # First call finds duplicate, second finds none
        mock_result.scalar_one_or_none = AsyncMock(side_effect=[existing_tx, None])
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call store_transactions without allowing duplicates
        saved, skipped, failed = await service.store_transactions(
            sample_transactions,
            "test_file.csv",
            allow_duplicates=False
        )

        # Verify results
        assert len(saved) == 1  # Only second transaction saved
        assert len(skipped) == 1  # First transaction skipped
        assert len(failed) == 0
        assert "Duplicate transaction found" in skipped[0]["reason"]

    @pytest.mark.asyncio
    async def test_store_transactions_with_integrity_error(self, mock_session, sample_transactions):
        """Test handling of integrity constraint violations"""
        service = TransactionService(mock_session)

        # Mock no duplicates found initially
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Mock flush raising IntegrityError for unique constraint
        error = IntegrityError("", "", "uix_transaction_unique")
        mock_session.flush.side_effect = [error, None]

        # Call store_transactions
        saved, skipped, failed = await service.store_transactions(
            sample_transactions,
            "test_file.csv",
            allow_duplicates=True
        )

        # Verify results
        assert len(saved) == 1  # Second transaction saved
        assert len(skipped) == 1  # First transaction skipped due to constraint
        assert len(failed) == 0
        assert "unique constraint" in skipped[0]["reason"]

    @pytest.mark.asyncio
    async def test_store_transactions_with_general_error(self, mock_session):
        """Test handling of general errors during transaction creation"""
        service = TransactionService(mock_session)

        # Invalid transaction data - missing required fields
        invalid_transactions = [
            {
                # Missing transaction_date which is required
                "asset_type": AssetType.STOCK,
                "transaction_type": TransactionType.BUY,
                "symbol": "AAPL"
            }
        ]

        # Call store_transactions
        saved, skipped, failed = await service.store_transactions(
            invalid_transactions,
            "test_file.csv"
        )

        # Verify results
        assert len(saved) == 0
        assert len(skipped) == 0
        assert len(failed) == 1
        assert "error" in failed[0]

    @pytest.mark.asyncio
    async def test_check_duplicates(self, mock_session, sample_transactions):
        """Test duplicate checking before insertion"""
        service = TransactionService(mock_session)

        # Mock finding duplicates
        existing_tx = MagicMock()
        existing_tx.id = 456
        existing_tx.source_file = "previous_import.csv"

        mock_result = AsyncMock()
        # First call finds duplicate, second finds none
        mock_result.scalar_one_or_none = AsyncMock(side_effect=[existing_tx, None])
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Check duplicates
        duplicates = await service.check_duplicates(sample_transactions)

        # Verify results
        assert len(duplicates) == 1
        assert duplicates[0]["existing_id"] == 456
        assert duplicates[0]["existing_source"] == "previous_import.csv"

    @pytest.mark.asyncio
    async def test_get_import_summary(self, mock_session):
        """Test getting import summary statistics"""
        service = TransactionService(mock_session)

        # Mock transactions
        mock_transactions = [
            MagicMock(
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                transaction_date=datetime(2024, 1, 15)
            ),
            MagicMock(
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.SELL,
                symbol="AAPL",
                transaction_date=datetime(2024, 1, 16)
            ),
            MagicMock(
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                transaction_date=datetime(2024, 1, 17)
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_transactions
        mock_session.execute.return_value = mock_result

        # Get summary
        summary = await service.get_import_summary()

        # Verify results
        assert summary["total_transactions"] == 3
        assert summary["by_asset_type"][AssetType.STOCK.value] == 2
        assert summary["by_asset_type"][AssetType.CRYPTO.value] == 1
        assert summary["by_transaction_type"][TransactionType.BUY.value] == 2
        assert summary["by_transaction_type"][TransactionType.SELL.value] == 1
        assert summary["by_symbol"]["AAPL"] == 2
        assert summary["by_symbol"]["BTC"] == 1

    @pytest.mark.asyncio
    async def test_decimal_conversion(self, mock_session):
        """Test proper decimal conversion for financial precision"""
        service = TransactionService(mock_session)

        # Transaction with various decimal values
        tx_data = {
            "transaction_date": datetime(2024, 1, 15),
            "asset_type": AssetType.CRYPTO,
            "transaction_type": TransactionType.BUY,
            "symbol": "BTC",
            "quantity": "0.00000001",  # String representation
            "price_per_unit": 45000.123456789,  # Float with many decimals
            "total_amount": "0.00045",  # String
            "fee": 0.00001,  # Small float
            "source_type": "KOINLY"
        }

        # Create transaction model
        transaction = await service._create_transaction_model(tx_data, "test.csv")

        # Verify decimal precision is maintained
        assert isinstance(transaction.quantity, Decimal)
        assert transaction.quantity == Decimal("0.00000001")
        assert isinstance(transaction.price_per_unit, Decimal)
        assert isinstance(transaction.total_amount, Decimal)
        assert isinstance(transaction.fee, Decimal)


class TestDuplicateHandler:
    """Test suite for DuplicateHandler"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def duplicate_info(self):
        """Sample duplicate information"""
        return [
            {
                "transaction": {
                    "transaction_date": datetime(2024, 1, 15),
                    "symbol": "AAPL",
                    "quantity": 10,
                    "price_per_unit": 150.50,
                    "total_amount": 1505.00,
                    "fee": 1.00,
                    "raw_data": {"updated": "data"}
                },
                "existing_id": 123,
                "existing_source": "old_import.csv"
            }
        ]

    @pytest.mark.asyncio
    async def test_resolve_duplicates_skip_strategy(self, mock_session, duplicate_info):
        """Test skip strategy for duplicate resolution"""
        resolved = await DuplicateHandler.resolve_duplicates(
            mock_session,
            duplicate_info,
            strategy="skip"
        )

        # Verify results
        assert len(resolved) == 1
        assert resolved[0]["action"] == "skipped"
        assert "Duplicate of transaction ID 123" in resolved[0]["reason"]

        # Verify no database operations
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_duplicates_update_strategy(self, mock_session, duplicate_info):
        """Test update strategy for duplicate resolution"""
        # Mock existing transaction
        existing_tx = MagicMock()
        existing_tx.id = 123
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_tx
        mock_session.execute.return_value = mock_result

        resolved = await DuplicateHandler.resolve_duplicates(
            mock_session,
            duplicate_info,
            strategy="update"
        )

        # Verify results
        assert len(resolved) == 1
        assert resolved[0]["action"] == "updated"
        assert resolved[0]["transaction_id"] == 123

        # Verify transaction was updated
        assert existing_tx.price_per_unit == Decimal("150.50")
        assert existing_tx.total_amount == Decimal("1505.00")
        assert existing_tx.fee == Decimal("1.00")

        # Verify commit was called
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_duplicates_force_strategy(self, mock_session, duplicate_info):
        """Test force strategy for duplicate resolution"""
        resolved = await DuplicateHandler.resolve_duplicates(
            mock_session,
            duplicate_info,
            strategy="force"
        )

        # Verify results
        assert len(resolved) == 1
        assert resolved[0]["action"] == "forced"
        assert "Timestamp modified" in resolved[0]["note"]

        # Verify timestamp was modified
        original_date = duplicate_info[0]["transaction"]["transaction_date"]
        modified_date = resolved[0]["transaction"]["transaction_date"]
        assert modified_date > original_date
        assert (modified_date - original_date).total_seconds() < 0.001  # Less than 1ms

        # Verify commit was called
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_duplicates_invalid_strategy(self, mock_session, duplicate_info):
        """Test handling of invalid strategy"""
        # This should not raise an error, just return empty list for unknown strategy
        resolved = await DuplicateHandler.resolve_duplicates(
            mock_session,
            duplicate_info,
            strategy="invalid"
        )

        # Verify no action taken
        assert len(resolved) == 0
        mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_batch_transaction_performance():
    """Test performance with large batch of transactions"""
    # Create mock session
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    # Properly mock execute
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=None)
    session.execute = AsyncMock(return_value=mock_result)

    service = TransactionService(session)

    # Create 1000 transactions
    large_batch = []
    for i in range(1000):
        large_batch.append({
            "transaction_date": datetime(2024, 1, 1) + timedelta(days=i % 30),
            "asset_type": AssetType.STOCK if i % 3 == 0 else AssetType.CRYPTO,
            "transaction_type": TransactionType.BUY if i % 2 == 0 else TransactionType.SELL,
            "symbol": f"SYMBOL_{i % 20}",
            "quantity": float(i % 100 + 1),
            "price_per_unit": float(100 + i % 50),
            "total_amount": float((i % 100 + 1) * (100 + i % 50)),
            "currency": "USD",
            "fee": float(i % 10),
            "source_type": "REVOLUT",
            "raw_data": {"index": i}
        })

    # Process transactions
    import time
    start = time.time()
    saved, skipped, failed = await service.store_transactions(
        large_batch,
        "large_batch.csv",
        allow_duplicates=True
    )
    duration = time.time() - start

    # Verify all processed
    assert len(saved) == 1000
    assert len(failed) == 0

    # Performance check (should be fast even with 1000 transactions)
    assert duration < 5.0  # Should process in less than 5 seconds

    # Verify batch operations
    assert session.add.call_count == 1000
    session.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])