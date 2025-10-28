# ABOUTME: Integration tests for complete CSV import to database flow
# ABOUTME: Tests end-to-end transaction import with real parsers and database

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImportIntegration:
    """Integration tests for the complete import flow"""

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
        return b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:00:00,Buy,0.5,BTC,20000,USD,10,USD,19990,,,0x123
2024-01-16 10:00:00,Sell,1500,USD,0.05,BTC,5,USD,1495,,,0x456
2024-01-17 10:00:00,Staking,0.001,BTC,,,,,,reward,Staking Reward,0x789"""

    @pytest.mark.asyncio
    async def test_upload_metals_csv_to_database(self, test_client, metals_csv):
        """Test uploading and storing metals CSV to database"""
        files = [
            ('files', ('account-statement_2024-01-01_2024-01-31_en_123456.csv', metals_csv, 'text/csv'))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Verify summary
        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 1
        assert data["summary"]["total_saved"] == 3

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
    async def test_upload_stocks_csv_to_database(self, test_client, stocks_csv):
        """Test uploading and storing stocks CSV to database"""
        files = [
            ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Verify summary
        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 1
        assert data["summary"]["total_saved"] == 4

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
    async def test_upload_crypto_csv_to_database(self, test_client, crypto_csv):
        """Test uploading and storing crypto CSV to database"""
        # Prepare file
        files = [
            ('files', ('Koinly Transactions.csv', crypto_csv, 'text/csv'))
        ]

        # Upload file
        response = test_client.post("/api/import/upload", files=files)

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Check if there were errors
        if data["summary"]["successful"] == 0:
            print(f"Upload failed. Response: {data}")
            # Check file-level errors
            if data["files"]:
                print(f"File errors: {data['files'][0].get('errors', [])}")

        # Verify crypto transactions were processed
        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 1, f"Expected 1 successful file, got {data['summary']['successful']}. Errors: {data['files'][0].get('errors', []) if data['files'] else 'N/A'}"
        # Should have multiple transactions from the crypto CSV
        assert data["summary"]["total_saved"] >= 3

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self, test_client, metals_csv, stocks_csv):
        """Test uploading multiple CSV files at once"""
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
    async def test_duplicate_detection(self, test_client, stocks_csv):
        """Test duplicate transaction detection"""
        files = [
            ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
        ]

        # First upload - all transactions should be saved
        response1 = test_client.post("/api/import/upload", files=files)
        assert response1.status_code == 200
        data1 = response1.json()
        first_upload_count = data1["summary"]["total_saved"]
        assert first_upload_count == 4  # 4 stocks transactions

        # Second upload - same file, should detect all as duplicates
        response2 = test_client.post("/api/import/upload", files=files)
        assert response2.status_code == 200
        data2 = response2.json()

        # All transactions should be skipped as duplicates
        assert data2["summary"]["total_saved"] == 0
        assert data2["summary"]["total_skipped"] == 4

        file_result = data2["files"][0]
        assert file_result["skipped_count"] == 4
        assert len(file_result["details"]["skipped_reasons"]) > 0

    @pytest.mark.asyncio
    async def test_duplicate_strategies(self, test_client, stocks_csv):
        """Test different duplicate handling strategies"""
        files = [
            ('files', ('stocks.csv', stocks_csv, 'text/csv'))
        ]

        # Test skip strategy (default)
        response = test_client.post(
            "/api/import/upload?duplicate_strategy=skip",
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["duplicate_strategy"] == "skip"

        # Test invalid strategy
        response = test_client.post(
            "/api/import/upload?duplicate_strategy=invalid",
            files=files
        )
        assert response.status_code == 400
        assert "Invalid duplicate_strategy" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_check_duplicates_endpoint(self, test_client, stocks_csv):
        """Test the check-duplicates endpoint"""
        # First upload some data
        upload_files = [
            ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
        ]
        test_client.post("/api/import/upload", files=upload_files)

        # Now check for duplicates with same file
        check_files = [
            ('file', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
        ]
        response = test_client.post("/api/import/check-duplicates", files=check_files)

        assert response.status_code == 200
        data = response.json()

        assert data["file_type"] == "STOCKS"
        assert data["total_transactions"] == 4
        assert data["duplicate_count"] == 4  # All should be duplicates now
        assert len(data["duplicates"]) == 4

    @pytest.mark.asyncio
    async def test_get_import_summary(self, test_client, stocks_csv):
        """Test getting import summary"""
        # Upload some data first
        files = [
            ('files', ('B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv', stocks_csv, 'text/csv'))
        ]
        test_client.post("/api/import/upload", files=files)

        # Get import summary
        response = test_client.get("/api/import/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_transactions"] >= 4
        assert "STOCK" in data["by_asset_type"]
        assert "BUY" in data["by_transaction_type"]

    @pytest.mark.asyncio
    async def test_error_handling(self, test_client):
        """Test error handling in import process"""
        # Test with invalid CSV
        invalid_csv = b"This is not a valid CSV"

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
    async def test_large_batch_import(self, test_client):
        """Test importing large CSV file"""

        # Generate large CSV with 100 transactions
        large_csv_lines = ["Date,Ticker,Type,Quantity,Price per share,Total Amount,Currency,FX Rate"]
        for i in range(100):
            date = f"2024-01-{(i % 28) + 1:02d}T10:00:00Z"
            ticker = f"STOCK{i % 10}"
            line = f"{date},{ticker},BUY,{i % 100 + 1},{100 + i % 50},{(i % 100 + 1) * (100 + i % 50)},USD,1.0"
            large_csv_lines.append(line)

        large_csv = "\n".join(large_csv_lines).encode()

        files = [
            ('files', ('12345678-1234-1234-1234-123456789ABC.csv', large_csv, 'text/csv'))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Should handle all 100 transactions
        assert data["summary"]["total_transactions"] == 100
        assert data["summary"]["total_saved"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])