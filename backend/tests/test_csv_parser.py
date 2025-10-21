# ABOUTME: Unit tests for CSV parser module
# ABOUTME: Tests file type detection, validation, and parser selection

import pytest
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from csv_parser import CSVDetector, FileType, get_parser, MetalsParser, StocksParser, CryptoParser

class TestCSVDetector:
    """Test suite for CSV file type detection"""

    def test_detect_metals_file(self):
        """Test detection of Revolut metals account statement files"""
        filenames = [
            "account-statement_2025-06-15_2025-10-21_en_4cab86.csv",
            "account-statement_2024-01-01_2024-12-31_de_123456.csv",
            "account-statement_2023-07-01_2023-07-31_fr_abcdef.csv"
        ]

        for filename in filenames:
            result = CSVDetector.detect_file_type(filename)
            assert result == FileType.METALS, f"Failed to detect metals file: {filename}"

    def test_detect_stocks_file(self):
        """Test detection of Revolut stocks export files (UUID format)"""
        filenames = [
            "B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv",
            "12345678-1234-1234-1234-123456789ABC.csv",
            "ABCDEF12-3456-7890-ABCD-EF1234567890.csv"
        ]

        for filename in filenames:
            result = CSVDetector.detect_file_type(filename)
            assert result == FileType.STOCKS, f"Failed to detect stocks file: {filename}"

    def test_detect_crypto_file(self):
        """Test detection of Koinly crypto export files"""
        filenames = [
            "Koinly Transactions.csv",
            "koinly_export_2024.csv",
            "my_KOINLY_data.csv",
            "Koinly-tax-report.csv"
        ]

        for filename in filenames:
            result = CSVDetector.detect_file_type(filename)
            assert result == FileType.CRYPTO, f"Failed to detect crypto file: {filename}"

    def test_detect_unknown_file(self):
        """Test detection returns UNKNOWN for unrecognized file formats"""
        filenames = [
            "random_file.csv",
            "data.csv",
            "export.csv",
            "transactions.csv",
            "portfolio.csv"
        ]

        for filename in filenames:
            result = CSVDetector.detect_file_type(filename)
            assert result == FileType.UNKNOWN, f"Incorrectly detected file: {filename}"

    def test_case_insensitive_detection(self):
        """Test that detection works regardless of case"""
        # Stocks - UUID should be case-insensitive
        assert CSVDetector.detect_file_type("b5a12617-2b56-4a79-b83d-13c6715dc0ba.csv") == FileType.STOCKS
        assert CSVDetector.detect_file_type("B5A12617-2B56-4A79-B83D-13C6715DC0BA.CSV") == FileType.STOCKS

        # Crypto - Koinly should be case-insensitive
        assert CSVDetector.detect_file_type("KOINLY Transactions.csv") == FileType.CRYPTO
        assert CSVDetector.detect_file_type("koinly transactions.CSV") == FileType.CRYPTO

class TestFileValidation:
    """Test suite for file validation"""

    def test_validate_valid_metals_file(self):
        """Test validation of valid metals file"""
        filename = "account-statement_2025-01-01_2025-12-31_en_123456.csv"
        file_size = 1024 * 500  # 500KB

        result = CSVDetector.validate_file(filename, file_size)

        assert result["is_valid"] == True
        assert result["file_type"] == FileType.METALS
        assert len(result["errors"]) == 0

    def test_validate_valid_stocks_file(self):
        """Test validation of valid stocks file"""
        filename = "B5A12617-2B56-4A79-B83D-13C6715DC0BA.csv"
        file_size = 1024 * 1024 * 2  # 2MB

        result = CSVDetector.validate_file(filename, file_size)

        assert result["is_valid"] == True
        assert result["file_type"] == FileType.STOCKS
        assert len(result["errors"]) == 0

    def test_validate_valid_crypto_file(self):
        """Test validation of valid crypto file"""
        filename = "Koinly Transactions.csv"
        file_size = 1024 * 1024 * 5  # 5MB

        result = CSVDetector.validate_file(filename, file_size)

        assert result["is_valid"] == True
        assert result["file_type"] == FileType.CRYPTO
        assert len(result["errors"]) == 0

    def test_validate_non_csv_file(self):
        """Test validation rejects non-CSV files"""
        filenames = [
            "document.pdf",
            "image.png",
            "data.xlsx",
            "script.js",
            "account-statement_2025-01-01_2025-12-31_en_123456.txt"
        ]

        for filename in filenames:
            result = CSVDetector.validate_file(filename, 1024)
            assert result["is_valid"] == False
            assert "must be a CSV file" in result["errors"][0]

    def test_validate_oversized_file(self):
        """Test validation rejects files over 10MB"""
        filename = "account-statement_2025-01-01_2025-12-31_en_123456.csv"
        file_size = 11 * 1024 * 1024  # 11MB

        result = CSVDetector.validate_file(filename, file_size)

        assert result["is_valid"] == False
        assert "exceeds 10MB limit" in result["errors"][0]

    def test_validate_unknown_csv_format(self):
        """Test validation rejects unknown CSV formats"""
        filename = "random_data.csv"
        file_size = 1024

        result = CSVDetector.validate_file(filename, file_size)

        assert result["is_valid"] == False
        assert result["file_type"] == FileType.UNKNOWN
        assert "Unknown CSV format" in result["errors"][0]

    def test_validate_exact_10mb_file(self):
        """Test validation accepts files exactly 10MB"""
        filename = "Koinly Transactions.csv"
        file_size = 10 * 1024 * 1024  # Exactly 10MB

        result = CSVDetector.validate_file(filename, file_size)

        assert result["is_valid"] == True
        assert len(result["errors"]) == 0

class TestParserFactory:
    """Test suite for parser factory function"""

    def test_get_parser_for_metals(self):
        """Test getting parser for METALS file type"""
        parser = get_parser(FileType.METALS)
        assert isinstance(parser, MetalsParser)

    def test_get_parser_for_stocks(self):
        """Test getting parser for STOCKS file type"""
        parser = get_parser(FileType.STOCKS)
        assert isinstance(parser, StocksParser)

    def test_get_parser_for_crypto(self):
        """Test getting parser for CRYPTO file type"""
        parser = get_parser(FileType.CRYPTO)
        assert isinstance(parser, CryptoParser)

    def test_get_parser_for_unknown(self):
        """Test getting parser for UNKNOWN file type returns None"""
        parser = get_parser(FileType.UNKNOWN)
        assert parser is None

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""

    def test_empty_filename(self):
        """Test handling of empty filename"""
        result = CSVDetector.detect_file_type("")
        assert result == FileType.UNKNOWN

    def test_malformed_uuid(self):
        """Test detection of files with almost-UUID names"""
        # Missing a character
        assert CSVDetector.detect_file_type("B5A12617-2B56-4A79-B83D-13C6715DC0B.csv") == FileType.UNKNOWN

        # Extra character
        assert CSVDetector.detect_file_type("B5A12617-2B56-4A79-B83D-13C6715DC0BAA.csv") == FileType.UNKNOWN

        # Wrong format
        assert CSVDetector.detect_file_type("B5A12617-2B564A79-B83D-13C6715DC0BA.csv") == FileType.UNKNOWN

    def test_partial_matches(self):
        """Test that partial matches don't trigger false positives"""
        # Contains "account" but not "account-statement"
        assert CSVDetector.detect_file_type("account_export.csv") == FileType.UNKNOWN

        # Contains "statement" but not "account-statement"
        assert CSVDetector.detect_file_type("statement_2024.csv") == FileType.UNKNOWN

    def test_special_characters_in_filename(self):
        """Test handling of special characters"""
        # Should still detect if core pattern matches
        assert CSVDetector.detect_file_type("account-statement_2024-01-01_2024-12-31_en_123456_backup.csv") == FileType.METALS

        # Koinly with special characters
        assert CSVDetector.detect_file_type("Koinly_Transactions_(2024).csv") == FileType.CRYPTO

    def test_file_size_edge_cases(self):
        """Test file size validation edge cases"""
        filename = "Koinly Transactions.csv"

        # Zero size
        result = CSVDetector.validate_file(filename, 0)
        assert result["is_valid"] == True  # Zero size is technically valid

        # Negative size (shouldn't happen but test defensive programming)
        result = CSVDetector.validate_file(filename, -1)
        assert result["is_valid"] == True  # Should handle gracefully

if __name__ == "__main__":
    pytest.main([__file__, "-v"])