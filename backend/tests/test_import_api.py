# ABOUTME: Integration tests for the import API endpoints
# ABOUTME: Tests multi-file upload, validation, and processing

import pytest
import io
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


class TestImportEndpoints:
    """Integration tests for import API endpoints"""

    def test_upload_status_endpoint(self, test_client):
        """Test the /api/import/status endpoint"""
        response = test_client.get("/api/import/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert len(data["supported_formats"]) == 3

        # Check supported formats
        format_types = [f["type"] for f in data["supported_formats"]]
        assert "METALS" in format_types
        assert "STOCKS" in format_types
        assert "CRYPTO" in format_types

    def test_upload_single_metals_file(self, test_client):
        """Test uploading a single metals CSV file"""
        # Create a mock CSV file with proper Revolut metals format
        csv_content = b"Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance\nExchange,Current,2024-01-01 10:00:00,2024-01-01 10:00:00,Exchanged to XAU,0.5,0.001,XAU,COMPLETED,0.499"
        file = io.BytesIO(csv_content)

        files = [
            ("files", ("account-statement_2024-01-01_2024-12-31_en_123456.csv", file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check summary
        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 1
        assert data["summary"]["failed"] == 0

        # Check file results
        assert len(data["files"]) == 1
        file_result = data["files"][0]
        assert file_result["filename"] == "account-statement_2024-01-01_2024-12-31_en_123456.csv"
        assert file_result["file_type"] == "METALS"
        assert file_result["status"] == "success"

    def test_upload_single_stocks_file(self, test_client):
        """Test uploading a single stocks CSV file"""
        csv_content = b"Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate\n2024-01-01,10:00:00,BUY,Apple Inc,AAPL,10,150.00,1500.00,USD,1.0"
        file = io.BytesIO(csv_content)

        files = [
            ("files", ("B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv", file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 1
        assert data["files"][0]["file_type"] == "STOCKS"

    def test_upload_single_crypto_file(self, test_client):
        """Test uploading a single crypto CSV file"""
        csv_content = b"Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash\n2024-01-01 10:00:00,Buy,0.5,BTC,20000,USD,10,USD,19990,,,0x123"
        file = io.BytesIO(csv_content)

        files = [
            ("files", ("Koinly Transactions.csv", file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 1
        assert data["files"][0]["file_type"] == "CRYPTO"

    def test_upload_multiple_files(self, test_client):
        """Test uploading multiple CSV files of different types"""
        # Create mock files with proper headers (metals with correct format, others as stubs)
        metals_csv = io.BytesIO(b"Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance\nExchange,Current,2024-01-01 10:00:00,2024-01-01 10:00:00,Exchanged to XAU,0.5,0.001,XAU,COMPLETED,0.499")
        stocks_csv = io.BytesIO(b"Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate\n2024-01-01,10:00:00,BUY,Apple Inc,AAPL,10,150.00,1500.00,USD,1.0")
        crypto_csv = io.BytesIO(b"Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash\n2024-01-01 10:00:00,Buy,0.5,BTC,20000,USD,10,USD,19990,,,0x123")

        files = [
            ("files", ("account-statement_2024-01-01_2024-12-31_en_123456.csv", metals_csv, "text/csv")),
            ("files", ("B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv", stocks_csv, "text/csv")),
            ("files", ("Koinly Transactions.csv", crypto_csv, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Check summary
        assert data["summary"]["total_files"] == 3
        assert data["summary"]["successful"] == 3
        assert data["summary"]["failed"] == 0

        # Check individual file results
        assert len(data["files"]) == 3

        file_types = [f["file_type"] for f in data["files"]]
        assert "METALS" in file_types
        assert "STOCKS" in file_types
        assert "CRYPTO" in file_types

    def test_upload_invalid_file_type(self, test_client):
        """Test uploading a file with unknown format"""
        csv_content = b"Date,Data\n2024-01-01,Test"
        file = io.BytesIO(csv_content)

        files = [
            ("files", ("random_data.csv", file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_files"] == 1
        assert data["summary"]["successful"] == 0
        assert data["summary"]["failed"] == 1

        file_result = data["files"][0]
        assert file_result["status"] == "error"
        assert file_result["file_type"] is None
        assert "Unknown CSV format" in file_result["errors"][0]

    def test_upload_non_csv_file(self, test_client):
        """Test uploading a non-CSV file"""
        file_content = b"This is a text file, not CSV"
        file = io.BytesIO(file_content)

        files = [
            ("files", ("document.txt", file, "text/plain"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["failed"] == 1
        assert "must be a CSV file" in data["files"][0]["errors"][0]

    def test_upload_mixed_valid_invalid_files(self, test_client):
        """Test uploading a mix of valid and invalid files"""
        valid_csv = io.BytesIO(b"Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance\nExchange,Current,2024-01-01 10:00:00,2024-01-01 10:00:00,Exchanged to XAU,0.5,0.001,XAU,COMPLETED,0.499")
        invalid_csv = io.BytesIO(b"Random content")

        files = [
            ("files", ("account-statement_2024-01-01_2024-12-31_en_123456.csv", valid_csv, "text/csv")),
            ("files", ("invalid.txt", invalid_csv, "text/plain"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_files"] == 2
        assert data["summary"]["successful"] == 1
        assert data["summary"]["failed"] == 1

    def test_upload_empty_file(self, test_client):
        """Test uploading an empty CSV file"""
        empty_file = io.BytesIO(b"")

        files = [
            ("files", ("Koinly Transactions.csv", empty_file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Empty file should still be processed (validation passes, parser handles empty content)
        assert data["summary"]["total_files"] == 1
        assert data["files"][0]["file_type"] == "CRYPTO"

    def test_upload_no_files(self, test_client):
        """Test calling upload endpoint with no files"""
        response = test_client.post("/api/import/upload", files=[])

        # FastAPI returns 422 for validation errors when required fields are missing
        assert response.status_code == 422

    def test_upload_large_filename(self, test_client):
        """Test uploading a file with a very long filename"""
        long_filename = "account-statement_" + "2024-01-01_" * 20 + "en_123456.csv"
        csv_content = b"Date,Type,Product\n2024-01-01,BUY,Gold"
        file = io.BytesIO(csv_content)

        files = [
            ("files", (long_filename, file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["files"][0]["file_type"] == "METALS"

class TestConcurrentUploads:
    """Test concurrent file upload scenarios"""

    def test_upload_duplicate_filenames(self, test_client):
        """Test uploading files with identical names"""
        csv1 = io.BytesIO(b"Date,Type,Asset\n2024-01-01,BUY,BTC")
        csv2 = io.BytesIO(b"Date,Type,Asset\n2024-01-02,SELL,BTC")

        files = [
            ("files", ("Koinly Transactions.csv", csv1, "text/csv")),
            ("files", ("Koinly Transactions.csv", csv2, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        # Both files should be processed
        assert data["summary"]["total_files"] == 2
        assert all(f["file_type"] == "CRYPTO" for f in data["files"])

    def test_upload_all_file_types_together(self, test_client):
        """Test uploading one file of each type simultaneously"""
        # Create sample files for each type
        metals_samples = [
            ("account-statement_2024-01-01_2024-01-31_en_aaa111.csv", b"metals1"),
            ("account-statement_2024-02-01_2024-02-29_en_bbb222.csv", b"metals2"),
        ]

        stocks_samples = [
            ("11111111-1111-1111-1111-111111111111.csv", b"stocks1"),
            ("22222222-2222-2222-2222-222222222222.csv", b"stocks2"),
        ]

        crypto_samples = [
            ("Koinly Transactions.csv", b"crypto1"),
            ("koinly_export_2024.csv", b"crypto2"),
        ]

        files = []
        for filename, content in metals_samples + stocks_samples + crypto_samples:
            files.append(("files", (filename, io.BytesIO(content), "text/csv")))

        response = test_client.post("/api/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["total_files"] == 6

        # Count file types
        file_types = [f["file_type"] for f in data["files"]]
        assert file_types.count("METALS") == 2
        assert file_types.count("STOCKS") == 2
        assert file_types.count("CRYPTO") == 2

class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_malformed_request(self, test_client):
        """Test handling of malformed requests"""
        # Send data instead of files
        response = test_client.post("/api/import/upload", json={"data": "test"})

        # FastAPI should return 422 for validation error
        assert response.status_code == 422

    def test_upload_file_exceeds_size_limit(self, test_client):
        """Test uploading a file that exceeds the 10MB limit"""
        # Create a file larger than 10MB (simulated with small content for testing)
        # In real scenario, the validation would check actual file size
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        file = io.BytesIO(large_content)

        files = [
            ("files", ("Koinly Transactions.csv", file, "text/csv"))
        ]

        response = test_client.post("/api/import/upload", files=files)

        # Note: The current implementation reads the entire file to check size,
        # which happens after FastAPI receives it. In production, you might want
        # to use streaming or check Content-Length header.
        assert response.status_code == 200
        data = response.json()

        # The file should be rejected due to size
        if len(large_content) > 10 * 1024 * 1024:
            assert data["summary"]["failed"] == 1
            assert "exceeds 10MB limit" in str(data["files"][0]["errors"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])