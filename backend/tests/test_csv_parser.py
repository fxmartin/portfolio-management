# ABOUTME: Unit tests for CSV parser module
# ABOUTME: Tests file type detection, validation, and parser selection

import pytest
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from csv_parser import CSVDetector, FileType, get_parser, MetalsParser, StocksParser, CryptoParser
from models import TransactionType, AssetType
from datetime import datetime

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

class TestMetalsParser:
    """Test suite for Revolut metals CSV parser"""

    @pytest.fixture
    def parser(self):
        """Get a MetalsParser instance"""
        return MetalsParser()

    @pytest.fixture
    def sample_buy_csv(self):
        """Sample CSV with buy transactions"""
        return b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Current,2025-06-15 10:01:28,2025-06-15 10:01:28,Exchanged to XPD,0.164922,0.001099,XPD,COMPLETED,0.163823
Exchange,Current,2025-07-06 12:15:45,2025-07-06 12:15:45,Exchanged to XPD,0.153299,0.001022,XPD,COMPLETED,0.316100"""

    @pytest.fixture
    def sample_sell_csv(self):
        """Sample CSV with sell transaction"""
        return b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Current,2025-10-15 15:45:54,2025-10-15 15:45:54,Exchanged to EUR,-0.316100,0.000000,XPD,COMPLETED,0.000000"""

    @pytest.fixture
    def sample_mixed_metals_csv(self):
        """Sample CSV with multiple metal types"""
        return b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Current,2025-06-15 10:00:42,2025-06-15 10:00:42,Exchanged to XAU,0.082971,0.000405,XAU,COMPLETED,0.082566
Exchange,Current,2025-06-15 10:00:59,2025-06-15 10:00:59,Exchanged to XAG,12.552019,0.061505,XAG,COMPLETED,12.490514
Exchange,Current,2025-06-15 10:01:13,2025-06-15 10:01:13,Exchanged to XPT,0.185163,0.000926,XPT,COMPLETED,0.184237
Exchange,Current,2025-06-15 10:01:28,2025-06-15 10:01:28,Exchanged to XPD,0.164922,0.001099,XPD,COMPLETED,0.163823"""

    @pytest.fixture
    def sample_invalid_header_csv(self):
        """Sample CSV with invalid headers"""
        return b"""Wrong,Headers,Here
Exchange,Current,2025-06-15 10:01:28"""

    @pytest.fixture
    def sample_empty_csv(self):
        """Empty CSV content"""
        return b""

    @pytest.fixture
    def sample_non_exchange_csv(self):
        """Sample CSV with non-exchange transaction types"""
        return b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
CARD_PAYMENT,Current,2025-06-15 10:00:00,2025-06-15 10:00:00,Payment to store,-50.00,0.00,EUR,COMPLETED,450.00
TOPUP,Current,2025-06-16 10:00:00,2025-06-16 10:00:00,Top up from card,100.00,0.00,EUR,COMPLETED,550.00"""

    def test_parse_buy_transaction(self, parser, sample_buy_csv):
        """Test parsing of buy transactions (positive amount)"""
        transactions = parser.parse(sample_buy_csv)

        assert len(transactions) == 2

        # First transaction
        tx1 = transactions[0]
        assert tx1["transaction_type"] == TransactionType.BUY
        assert tx1["asset_type"] == AssetType.METAL
        assert tx1["symbol"] == "XPD"
        assert tx1["quantity"] == 0.163823  # Amount minus fee
        assert tx1["gross_quantity"] == 0.164922
        assert tx1["fee"] == 0.001099
        assert tx1["transaction_date"] == datetime(2025, 6, 15, 10, 1, 28)
        assert tx1["source_type"] == "REVOLUT"
        assert tx1["balance_after"] == 0.163823

        # Second transaction
        tx2 = transactions[1]
        assert abs(tx2["quantity"] - 0.152277) < 0.0000001  # 0.153299 - 0.001022
        assert tx2["balance_after"] == 0.316100

    def test_parse_sell_transaction(self, parser, sample_sell_csv):
        """Test parsing of sell transactions (negative amount)"""
        transactions = parser.parse(sample_sell_csv)

        assert len(transactions) == 1

        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.SELL
        assert tx["symbol"] == "XPD"
        assert tx["quantity"] == 0.316100  # Absolute value
        assert tx["fee"] == 0.000000
        assert tx["balance_after"] == 0.000000

    def test_parse_multiple_metal_types(self, parser, sample_mixed_metals_csv):
        """Test parsing different metal symbols"""
        transactions = parser.parse(sample_mixed_metals_csv)

        assert len(transactions) == 4

        symbols = [tx["symbol"] for tx in transactions]
        assert "XAU" in symbols  # Gold
        assert "XAG" in symbols  # Silver
        assert "XPT" in symbols  # Platinum
        assert "XPD" in symbols  # Palladium

        # Check all are marked as METAL asset type
        for tx in transactions:
            assert tx["asset_type"] == AssetType.METAL

    def test_parse_date_handling(self, parser, sample_buy_csv):
        """Test proper date parsing"""
        transactions = parser.parse(sample_buy_csv)

        # Check date parsing is correct
        tx1_date = transactions[0]["transaction_date"]
        assert isinstance(tx1_date, datetime)
        assert tx1_date.year == 2025
        assert tx1_date.month == 6
        assert tx1_date.day == 15
        assert tx1_date.hour == 10
        assert tx1_date.minute == 1
        assert tx1_date.second == 28

    def test_parse_fee_calculation(self, parser, sample_buy_csv):
        """Test fee extraction and net quantity calculation"""
        transactions = parser.parse(sample_buy_csv)

        tx1 = transactions[0]
        # Verify fee is extracted
        assert tx1["fee"] == 0.001099
        # Verify net quantity is gross minus fee (with float precision tolerance)
        assert abs(tx1["quantity"] - (tx1["gross_quantity"] - tx1["fee"])) < 0.0000001
        assert abs(tx1["quantity"] - 0.163823) < 0.0000001  # Float precision

    def test_parse_balance_tracking(self, parser, sample_mixed_metals_csv):
        """Test balance tracking for each metal type"""
        transactions = parser.parse(sample_mixed_metals_csv)

        # Group by symbol and check balances
        xau_txs = [tx for tx in transactions if tx["symbol"] == "XAU"]
        assert len(xau_txs) == 1
        assert xau_txs[0]["balance_after"] == 0.082566

        xag_txs = [tx for tx in transactions if tx["symbol"] == "XAG"]
        assert len(xag_txs) == 1
        assert xag_txs[0]["balance_after"] == 12.490514

    def test_parse_raw_data_preservation(self, parser, sample_buy_csv):
        """Test that raw CSV row data is preserved"""
        transactions = parser.parse(sample_buy_csv)

        tx1 = transactions[0]
        assert "raw_data" in tx1
        assert tx1["raw_data"]["Type"] == "Exchange"
        assert tx1["raw_data"]["Product"] == "Current"
        assert tx1["raw_data"]["State"] == "COMPLETED"
        assert tx1["raw_data"]["Description"] == "Exchanged to XPD"

    def test_parse_invalid_header_error(self, parser, sample_invalid_header_csv):
        """Test error handling for invalid CSV headers"""
        with pytest.raises(ValueError, match="Invalid CSV format.*missing required headers"):
            parser.parse(sample_invalid_header_csv)

    def test_parse_empty_csv(self, parser, sample_empty_csv):
        """Test handling of empty CSV file"""
        with pytest.raises(ValueError, match="Empty CSV file"):
            parser.parse(sample_empty_csv)

    def test_parse_non_exchange_transactions(self, parser, sample_non_exchange_csv):
        """Test handling of non-exchange transaction types"""
        transactions = parser.parse(sample_non_exchange_csv)

        # Should skip non-exchange transactions for metals
        assert len(transactions) == 0

    def test_parse_completed_state_only(self, parser):
        """Test that only COMPLETED transactions are processed"""
        csv_content = b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Current,2025-06-15 10:01:28,2025-06-15 10:01:28,Exchanged to XPD,0.164922,0.001099,XPD,COMPLETED,0.163823
Exchange,Current,2025-06-15 10:02:00,2025-06-15 10:02:00,Exchanged to XPD,0.100000,0.001000,XPD,PENDING,0.099000
Exchange,Current,2025-06-15 10:03:00,2025-06-15 10:03:00,Exchanged to XPD,0.200000,0.002000,XPD,FAILED,0.000000"""

        transactions = parser.parse(csv_content)

        # Should only include COMPLETED transaction
        assert len(transactions) == 1
        assert transactions[0]["gross_quantity"] == 0.164922

    def test_parse_currency_validation(self, parser):
        """Test that only valid metal currencies are processed"""
        csv_content = b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Current,2025-06-15 10:01:28,2025-06-15 10:01:28,Exchanged to XPD,0.164922,0.001099,XPD,COMPLETED,0.163823
Exchange,Current,2025-06-15 10:02:00,2025-06-15 10:02:00,Exchanged to EUR,100.00,0.00,EUR,COMPLETED,100.00
Exchange,Current,2025-06-15 10:03:00,2025-06-15 10:03:00,Exchanged to USD,50.00,0.00,USD,COMPLETED,50.00"""

        transactions = parser.parse(csv_content)

        # Should only include metal transactions (XPD, not EUR/USD)
        assert len(transactions) == 1
        assert transactions[0]["symbol"] == "XPD"

    def test_parse_decimal_precision(self, parser):
        """Test handling of high-precision decimal values"""
        csv_content = b"""Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Exchange,Current,2025-06-15 10:01:28,2025-06-15 10:01:28,Exchanged to XAU,0.12345678,0.00012345,XAU,COMPLETED,0.12333333"""

        transactions = parser.parse(csv_content)

        tx = transactions[0]
        # Check precision is maintained
        assert tx["gross_quantity"] == 0.12345678
        assert tx["fee"] == 0.00012345
        assert abs(tx["quantity"] - 0.12333333) < 0.0000001

    def test_parse_zero_fee_handling(self, parser, sample_sell_csv):
        """Test handling of zero fees (common in sell transactions)"""
        transactions = parser.parse(sample_sell_csv)

        tx = transactions[0]
        assert tx["fee"] == 0.0
        # When fee is zero, quantity should equal gross quantity
        assert tx["quantity"] == abs(tx["gross_quantity"])

class TestStocksParser:
    """Test suite for Revolut stocks CSV parser"""

    @pytest.fixture
    def parser(self):
        """Get a StocksParser instance"""
        return StocksParser()

    @pytest.fixture
    def sample_buy_csv(self):
        """Sample CSV with stock buy transactions"""
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-15,14:30:00,BUY,Tesla Inc,TSLA,10,250.50,2505.00,USD,1.0
2024-10-14,10:15:00,BUY,Apple Inc,AAPL,5,175.25,876.25,USD,1.0"""

    @pytest.fixture
    def sample_sell_csv(self):
        """Sample CSV with stock sell transactions"""
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-20,09:45:00,SELL,Tesla Inc,TSLA,5,260.00,1300.00,USD,1.0
2024-10-21,11:30:00,SELL,Apple Inc,AAPL,2,180.00,360.00,USD,1.0"""

    @pytest.fixture
    def sample_dividend_csv(self):
        """Sample CSV with dividend transactions"""
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-14,00:00:00,DIVIDEND,Apple Inc,AAPL,,0.24,24.00,USD,1.0
2024-10-15,00:00:00,DIVIDEND,Microsoft Corp,MSFT,,0.75,37.50,USD,1.0"""

    @pytest.fixture
    def sample_mixed_csv(self):
        """Sample CSV with mixed transaction types"""
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-10,10:00:00,BUY,Tesla Inc,TSLA,10,250.00,2500.00,USD,1.0
2024-10-14,00:00:00,DIVIDEND,Apple Inc,AAPL,,0.24,24.00,USD,1.0
2024-10-15,15:00:00,SELL,Tesla Inc,TSLA,5,255.00,1275.00,USD,1.0
2024-10-16,09:30:00,BUY,Nvidia Corp,NVDA,3,450.50,1351.50,USD,1.0"""

    @pytest.fixture
    def sample_fractional_csv(self):
        """Sample CSV with fractional shares"""
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-15,14:30:00,BUY,Amazon.com Inc,AMZN,0.5,3250.00,1625.00,USD,1.0
2024-10-16,10:15:00,BUY,Alphabet Inc Class A,GOOGL,0.25,2800.00,700.00,USD,1.0
2024-10-17,11:00:00,SELL,Amazon.com Inc,AMZN,0.25,3300.00,825.00,USD,1.0"""

    @pytest.fixture
    def sample_eur_csv(self):
        """Sample CSV with EUR currency transactions"""
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-15,14:30:00,BUY,BMW AG,BMW,10,85.50,855.00,EUR,1.06
2024-10-16,10:15:00,BUY,Volkswagen AG,VOW3,5,110.25,551.25,EUR,1.06"""

    @pytest.fixture
    def sample_empty_csv(self):
        """Empty CSV content"""
        return b""

    @pytest.fixture
    def sample_invalid_header_csv(self):
        """Sample CSV with invalid headers"""
        return b"""Symbol,Date,Shares,Price
TSLA,2024-10-15,10,250.50"""

    @pytest.fixture
    def sample_fee_csv(self):
        """Sample CSV with transactions including fees (custom format for testing)"""
        # Note: Actual Revolut format may vary
        return b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate,Fee
2024-10-15,14:30:00,BUY,Tesla Inc,TSLA,10,250.50,2505.00,USD,1.0,2.50
2024-10-16,10:00:00,SELL,Tesla Inc,TSLA,5,255.00,1275.00,USD,1.0,1.25"""

    def test_parse_buy_transactions(self, parser, sample_buy_csv):
        """Test parsing of stock buy transactions"""
        transactions = parser.parse(sample_buy_csv)

        assert len(transactions) == 2

        # First transaction - TSLA
        tx1 = transactions[0]
        assert tx1["transaction_type"] == TransactionType.BUY
        assert tx1["asset_type"] == AssetType.STOCK
        assert tx1["symbol"] == "TSLA"
        assert tx1["quantity"] == 10.0
        assert tx1["price_per_unit"] == 250.50
        assert tx1["total_amount"] == 2505.00
        assert tx1["currency"] == "USD"
        assert tx1["transaction_date"] == datetime(2024, 10, 15, 14, 30, 0)
        assert tx1["source_type"] == "REVOLUT"

        # Second transaction - AAPL
        tx2 = transactions[1]
        assert tx2["symbol"] == "AAPL"
        assert tx2["quantity"] == 5.0
        assert tx2["price_per_unit"] == 175.25

    def test_parse_sell_transactions(self, parser, sample_sell_csv):
        """Test parsing of stock sell transactions"""
        transactions = parser.parse(sample_sell_csv)

        assert len(transactions) == 2

        tx1 = transactions[0]
        assert tx1["transaction_type"] == TransactionType.SELL
        assert tx1["symbol"] == "TSLA"
        assert tx1["quantity"] == 5.0
        assert tx1["price_per_unit"] == 260.00
        assert tx1["total_amount"] == 1300.00

    def test_parse_dividend_transactions(self, parser, sample_dividend_csv):
        """Test parsing of dividend transactions"""
        transactions = parser.parse(sample_dividend_csv)

        assert len(transactions) == 2

        tx1 = transactions[0]
        assert tx1["transaction_type"] == TransactionType.DIVIDEND
        assert tx1["symbol"] == "AAPL"
        assert tx1["quantity"] is None or tx1["quantity"] == 0  # Dividends may not have quantity
        assert tx1["price_per_unit"] == 0.24
        assert tx1["total_amount"] == 24.00

        tx2 = transactions[1]
        assert tx2["symbol"] == "MSFT"
        assert tx2["total_amount"] == 37.50

    def test_parse_mixed_transactions(self, parser, sample_mixed_csv):
        """Test parsing of mixed transaction types"""
        transactions = parser.parse(sample_mixed_csv)

        assert len(transactions) == 4

        # Verify we have all transaction types
        types = [tx["transaction_type"] for tx in transactions]
        assert TransactionType.BUY in types
        assert TransactionType.SELL in types
        assert TransactionType.DIVIDEND in types

        # Verify tickers are correct
        symbols = [tx["symbol"] for tx in transactions]
        assert "TSLA" in symbols
        assert "AAPL" in symbols
        assert "NVDA" in symbols

    def test_parse_fractional_shares(self, parser, sample_fractional_csv):
        """Test handling of fractional share quantities"""
        transactions = parser.parse(sample_fractional_csv)

        assert len(transactions) == 3

        # Check fractional quantities
        tx1 = transactions[0]
        assert tx1["symbol"] == "AMZN"
        assert tx1["quantity"] == 0.5

        tx2 = transactions[1]
        assert tx2["symbol"] == "GOOGL"
        assert tx2["quantity"] == 0.25

        tx3 = transactions[2]
        assert tx3["quantity"] == 0.25

    def test_parse_date_time_handling(self, parser, sample_buy_csv):
        """Test proper date and time parsing"""
        transactions = parser.parse(sample_buy_csv)

        tx1 = transactions[0]
        date = tx1["transaction_date"]
        assert isinstance(date, datetime)
        assert date.year == 2024
        assert date.month == 10
        assert date.day == 15
        assert date.hour == 14
        assert date.minute == 30
        assert date.second == 0

    def test_parse_currency_handling(self, parser, sample_eur_csv):
        """Test handling of different currencies"""
        transactions = parser.parse(sample_eur_csv)

        assert len(transactions) == 2

        # Check EUR currency
        tx1 = transactions[0]
        assert tx1["currency"] == "EUR"
        assert tx1["fx_rate"] == 1.06

        tx2 = transactions[1]
        assert tx2["currency"] == "EUR"

    def test_parse_ticker_extraction(self, parser, sample_mixed_csv):
        """Test ticker symbol extraction and cleaning"""
        transactions = parser.parse(sample_mixed_csv)

        # Check tickers are properly extracted
        tickers = {tx["symbol"] for tx in transactions}
        expected_tickers = {"TSLA", "AAPL", "NVDA"}
        assert tickers == expected_tickers

    def test_parse_raw_data_preservation(self, parser, sample_buy_csv):
        """Test that raw CSV row data is preserved"""
        transactions = parser.parse(sample_buy_csv)

        tx1 = transactions[0]
        assert "raw_data" in tx1
        assert tx1["raw_data"]["Date"] == "2024-10-15"
        assert tx1["raw_data"]["Time"] == "14:30:00"
        assert tx1["raw_data"]["Type"] == "BUY"
        assert tx1["raw_data"]["Product"] == "Tesla Inc"
        assert tx1["raw_data"]["Ticker"] == "TSLA"

    def test_parse_fee_handling(self, parser, sample_fee_csv):
        """Test handling of transaction fees if present"""
        transactions = parser.parse(sample_fee_csv)

        assert len(transactions) == 2

        tx1 = transactions[0]
        assert tx1["fee"] == 2.50

        tx2 = transactions[1]
        assert tx2["fee"] == 1.25

    def test_parse_empty_csv(self, parser, sample_empty_csv):
        """Test handling of empty CSV file"""
        with pytest.raises(ValueError, match="Empty CSV file"):
            parser.parse(sample_empty_csv)

    def test_parse_invalid_header(self, parser, sample_invalid_header_csv):
        """Test error handling for invalid CSV headers"""
        with pytest.raises(ValueError, match="Invalid CSV format.*missing required headers"):
            parser.parse(sample_invalid_header_csv)

    def test_parse_total_amount_validation(self, parser, sample_buy_csv):
        """Test validation of total amount calculation"""
        transactions = parser.parse(sample_buy_csv)

        for tx in transactions:
            if tx["quantity"] and tx["price_per_unit"]:
                # Allow for small floating point differences
                calculated_total = tx["quantity"] * tx["price_per_unit"]
                assert abs(calculated_total - tx["total_amount"]) < 0.01

    def test_parse_product_name_handling(self, parser, sample_mixed_csv):
        """Test handling of product names"""
        transactions = parser.parse(sample_mixed_csv)

        # Check product names are preserved in raw data
        product_names = {tx["raw_data"]["Product"] for tx in transactions}
        expected_names = {"Tesla Inc", "Apple Inc", "Nvidia Corp"}
        assert expected_names.issubset(product_names)

    def test_parse_with_missing_quantity_dividend(self, parser, sample_dividend_csv):
        """Test handling of missing quantity for dividend transactions"""
        transactions = parser.parse(sample_dividend_csv)

        # Dividends typically don't have quantity
        for tx in transactions:
            if tx["transaction_type"] == TransactionType.DIVIDEND:
                assert tx["quantity"] is None or tx["quantity"] == 0

    def test_parse_fx_rate_handling(self, parser):
        """Test handling of FX rate for currency conversions"""
        csv_content = b"""Date,Time,Type,Product,Ticker,Quantity,Price per share,Total Amount,Currency,FX Rate
2024-10-15,14:30:00,BUY,BMW AG,BMW,10,85.50,855.00,EUR,1.06
2024-10-16,10:15:00,BUY,Apple Inc,AAPL,5,175.25,876.25,USD,1.0"""

        transactions = parser.parse(csv_content)

        # EUR transaction with FX rate
        tx1 = transactions[0]
        assert tx1["fx_rate"] == 1.06
        assert tx1["currency"] == "EUR"

        # USD transaction with FX rate 1.0
        tx2 = transactions[1]
        assert tx2["fx_rate"] == 1.0
        assert tx2["currency"] == "USD"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])