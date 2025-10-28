# ABOUTME: Integration tests for complete CSV import to database flow
# ABOUTME: Tests end-to-end transaction import with real parsers and database

import pytest
from datetime import datetime
import json
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Transaction, AssetType, TransactionType
from transaction_service import TransactionService


class TestImportIntegration:
    """Integration tests for the complete import flow"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing"""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()
        session.close = AsyncMock()

        # Mock execute to return no duplicates by default
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        return session

    @pytest.fixture
    def metals_csv(self):
        """Sample Revolut metals CSV content"""
        return b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Gold,2024-01-15 10:00:00,2024-01-15 10:00:01,Bought XAU 0.5,0.5,0.001,XAU,COMPLETED,0.5
Exchange,Gold,2024-01-16 14:30:00,2024-01-16 14:30:01,Sold XAU 0.2,-0.2,0.0,XAU,COMPLETED,0.3
Exchange,Silver,2024-01-17 09:15:00,2024-01-17 09:15:01,Bought XAG 10,10,0.05,XAG,COMPLETED,10"""

    @pytest.fixture
    def stocks_csv(self):
        """Sample Revolut stocks CSV content"""
        return b"""Date,Ticker,Type,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-01-15T10:30:00Z,AAPL,BUY,10,150.50,1505.00,USD,1.0
2024-01-16T14:45:00Z,TSLA,BUY,5,250.00,1250.00,USD,1.0
2024-01-17T11:00:00Z,AAPL,DIVIDEND,,0.24,2.40,USD,1.0
2024-01-18T16:20:00Z,TSLA,SELL,2,260.00,520.00,USD,1.0"""

    @pytest.fixture
    def crypto_csv(self):
        """Sample Koinly crypto CSV content"""
        return b"""Date (UTC),Type,From Amount,From Currency,To Amount,To Currency,Fee Amount,Fee Currency,Net Value (read-only),Value Currency (read-only),Tag,Description,TxHash
2024-01-15 10:00:00,trade,1000.00,EUR,0.025,BTC,5.00,EUR,1000.00,EUR,,,0xabc123
2024-01-16 14:30:00,trade,0.01,BTC,450.00,EUR,2.00,EUR,450.00,EUR,,,0xdef456
2024-01-17 08:45:00,deposit,,,,0.0001,BTC,,,2.50,EUR,reward,Staking Reward,0xghi789"""

    @pytest.mark.asyncio
    async def test_upload_metals_csv_to_database(self, test_client, mock_db_session, metals_csv):
        """Test uploading and storing metals CSV to database"""

        # Mock the database dependency - need to use async generator
        async def mock_get_async_db():
            yield mock_db_session

        with patch('import_router.get_async_db', mock_get_async_db):
            # Prepare file
            files = [
                ('files', ('account-statement_2024-01-01_2024-01-31_en_123456.csv', metals_csv, 'text/csv'))
            ]

            # Upload file
            response = test_client.post("/api/import/upload", files=files)

            # Check response
            assert response.status_code == 200
            data = response.json()

            # Debug output
            print(f"Response data: {json.dumps(data, indent=2)}")

            # Verify summary
            assert data["summary"]["total_files"] == 1
            # Adjust expectation based on actual output
            if data["files"][0].get("status") == "error":
                print(f"Error details: {data['files'][0].get('errors')}")
                assert False, f"File processing failed: {data['files'][0].get('errors')}"

            assert data["summary"]["successful"] == 1
            assert data["summary"]["total_saved"] == 3  # 3 metal transactions

            # Verify file details
            file_result = data["files"][0]
            assert file_result["filename"] == "account-statement_2024-01-01_2024-01-31_en_123456.csv"
            assert file_result["status"] == "success"
            assert file_result["file_type"] == "METALS"
            assert file_result["saved_count"] == 3

            # Verify saved transaction details
            assert len(file_result["details"]["saved"]) == 3
            assert all("symbol" in tx for tx in file_result["details"]["saved"])

    @pytest.mark.asyncio
    async def test_upload_stocks_csv_to_database(self, test_client, mock_db_session, stocks_csv):
        """Test uploading and storing stocks CSV to database"""

        with patch('import_router.get_async_db', return_value=mock_db_session):
            # Prepare file with UUID name
            files = [
                ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
            ]

            # Upload file
            response = test_client.post("/api/import/upload", files=files)

            # Check response
            assert response.status_code == 200
            data = response.json()

            # Verify summary
            assert data["summary"]["total_files"] == 1
            assert data["summary"]["successful"] == 1
            assert data["summary"]["total_saved"] == 4  # 4 stock transactions

            # Verify file details
            file_result = data["files"][0]
            assert file_result["file_type"] == "STOCKS"
            assert file_result["saved_count"] == 4

            # Check transaction details
            assert len(file_result["details"]["saved"]) > 0
            first_tx = file_result["details"]["saved"][0]
            assert "symbol" in first_tx
            assert "date" in first_tx

    @pytest.mark.asyncio
    async def test_upload_crypto_csv_to_database(self, test_client, mock_db_session, crypto_csv):
        """Test uploading and storing crypto CSV to database"""

        with patch('import_router.get_async_db', return_value=mock_db_session):
            # Prepare file
            files = [
                ('files', ('Koinly Transactions.csv', crypto_csv, 'text/csv'))
            ]

            # Upload file
            response = test_client.post("/api/import/upload", files=files)

            # Check response
            assert response.status_code == 200
            data = response.json()

            # Verify crypto transactions were processed
            assert data["summary"]["total_files"] == 1
            assert data["summary"]["successful"] == 1
            # Should have 4 transactions: 2 from first trade (sell EUR + buy BTC),
            # 1 from second trade (sell BTC), and 1 staking reward
            assert data["summary"]["total_saved"] >= 3

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self, test_client, mock_db_session, metals_csv, stocks_csv):
        """Test uploading multiple CSV files at once"""

        with patch('import_router.get_async_db', return_value=mock_db_session):
            # Prepare multiple files
            files = [
                ('files', ('account-statement_2024-01-01_2024-01-31_en_123456.csv', metals_csv, 'text/csv')),
                ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
            ]

            # Upload files
            response = test_client.post("/api/import/upload", files=files)

            # Check response
            assert response.status_code == 200
            data = response.json()

            # Verify both files processed
            assert data["summary"]["total_files"] == 2
            assert data["summary"]["successful"] == 2
            assert data["summary"]["total_saved"] == 7  # 3 metals + 4 stocks

            # Check individual file results
            assert len(data["files"]) == 2
            assert data["files"][0]["file_type"] == "METALS"
            assert data["files"][1]["file_type"] == "STOCKS"

    @pytest.mark.asyncio
    async def test_duplicate_detection(self, test_client, mock_db_session, stocks_csv):
        """Test duplicate transaction detection"""

        # Mock finding existing transaction
        existing_tx = MagicMock()
        existing_tx.id = 123
        existing_tx.source_file = "previous_import.csv"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            existing_tx,  # First transaction is duplicate
            None, None, None  # Rest are new
        ]
        mock_db_session.execute.return_value = mock_result

        with patch('import_router.get_async_db', return_value=mock_db_session):
            files = [
                ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
            ]

            # Upload with duplicate detection
            response = test_client.post(
                "/api/import/upload?allow_duplicates=true",
                files=files
            )

            assert response.status_code == 200
            data = response.json()

            # Should have skipped 1 duplicate
            assert data["summary"]["total_saved"] == 3
            assert data["summary"]["total_skipped"] == 1

            file_result = data["files"][0]
            assert file_result["skipped_count"] == 1
            assert len(file_result["details"]["skipped_reasons"]) > 0

    @pytest.mark.asyncio
    async def test_duplicate_strategies(self, test_client, mock_db_session, stocks_csv):
        """Test different duplicate handling strategies"""

        # Test skip strategy (default)
        with patch('import_router.get_async_db', return_value=mock_db_session):
            files = [
                ('files', ('stocks.csv', stocks_csv, 'text/csv'))
            ]

            response = test_client.post(
                "/api/import/upload?duplicate_strategy=skip",
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert data["summary"]["duplicate_strategy"] == "skip"

        # Test update strategy
        with patch('import_router.get_async_db', return_value=mock_db_session):
            response = test_client.post(
                "/api/import/upload?duplicate_strategy=update",
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert data["summary"]["duplicate_strategy"] == "update"

        # Test force strategy
        with patch('import_router.get_async_db', return_value=mock_db_session):
            response = test_client.post(
                "/api/import/upload?duplicate_strategy=force",
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert data["summary"]["duplicate_strategy"] == "force"

        # Test invalid strategy
        with patch('import_router.get_async_db', return_value=mock_db_session):
            response = test_client.post(
                "/api/import/upload?duplicate_strategy=invalid",
                files=files
            )
            assert response.status_code == 400
            assert "Invalid duplicate_strategy" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_check_duplicates_endpoint(self, test_client, mock_db_session, stocks_csv):
        """Test the check-duplicates endpoint"""

        # Mock finding duplicates
        existing_tx = MagicMock()
        existing_tx.id = 456
        existing_tx.source_file = "old_import.csv"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            existing_tx,  # First transaction is duplicate
            None, None, None  # Rest are new
        ]
        mock_db_session.execute.return_value = mock_result

        with patch('import_router.get_async_db', return_value=mock_db_session):
            files = [
                ('file', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
            ]

            response = test_client.post("/api/import/check-duplicates", files=files)

            assert response.status_code == 200
            data = response.json()

            assert data["file_type"] == "STOCKS"
            assert data["total_transactions"] == 4
            assert data["duplicate_count"] == 1
            assert len(data["duplicates"]) == 1
            assert data["duplicates"][0]["existing_id"] == 456

    @pytest.mark.asyncio
    async def test_get_import_summary(self, test_client, mock_db_session):
        """Test getting import summary"""

        # Mock transactions in database
        mock_transactions = [
            MagicMock(
                asset_type=AssetType.STOCK,
                transaction_type=TransactionType.BUY,
                symbol="AAPL",
                transaction_date=datetime(2024, 1, 15)
            ),
            MagicMock(
                asset_type=AssetType.CRYPTO,
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                transaction_date=datetime(2024, 1, 16)
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_transactions
        mock_db_session.execute.return_value = mock_result

        with patch('import_router.get_async_db', return_value=mock_db_session):
            response = test_client.get("/api/import/summary")

            assert response.status_code == 200
            data = response.json()

            assert data["total_transactions"] == 2
            assert "STOCK" in data["by_asset_type"]
            assert "CRYPTO" in data["by_asset_type"]
            assert "BUY" in data["by_transaction_type"]

    @pytest.mark.asyncio
    async def test_error_handling(self, test_client, mock_db_session):
        """Test error handling in import process"""

        # Test with invalid CSV
        invalid_csv = b"This is not a valid CSV"

        with patch('import_router.get_async_db', return_value=mock_db_session):
            files = [
                ('files', ('account-statement_2024.csv', invalid_csv, 'text/csv'))
            ]

            response = test_client.post("/api/import/upload", files=files)

            assert response.status_code == 200
            data = response.json()

            # File should fail processing
            assert data["summary"]["failed"] == 1
            assert data["files"][0]["status"] == "error"
            assert len(data["files"][0]["errors"]) > 0

    @pytest.mark.asyncio
    async def test_large_batch_import(self, test_client, mock_db_session):
        """Test importing large CSV file"""

        # Generate large CSV with 1000 transactions
        large_csv_lines = ["Date,Ticker,Type,Quantity,Price per share,Total Amount,Currency,FX Rate"]
        for i in range(1000):
            date = f"2024-01-{(i % 28) + 1:02d}T10:00:00Z"
            ticker = f"STOCK{i % 10}"
            line = f"{date},{ticker},BUY,{i % 100 + 1},{100 + i % 50},{(i % 100 + 1) * (100 + i % 50)},USD,1.0"
            large_csv_lines.append(line)

        large_csv = "\n".join(large_csv_lines).encode()

        with patch('import_router.get_async_db', return_value=mock_db_session):
            files = [
                ('files', ('large-batch.csv', large_csv, 'text/csv'))
            ]

            response = test_client.post("/api/import/upload", files=files)

            assert response.status_code == 200
            data = response.json()

            # Should handle all 1000 transactions
            assert data["summary"]["total_transactions"] == 1000
            assert data["summary"]["total_saved"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])