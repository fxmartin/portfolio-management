# ABOUTME: Unit tests for Koinly crypto CSV parser
# ABOUTME: Tests crypto transaction parsing from Koinly export format

import pytest
from pathlib import Path
import sys
from datetime import datetime
from io import BytesIO

sys.path.append(str(Path(__file__).parent.parent))

from csv_parser import CryptoParser, CSVDetector, FileType
from models import TransactionType, AssetType

class TestCryptoParser:
    """Test suite for Koinly crypto CSV parser"""

    def test_parse_crypto_buy_transaction(self):
        """Test parsing of crypto BUY transaction"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Buy,0.5,BTC,25000,USD,10,USD,24990,,,0x123abc"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.BUY
        assert tx["asset_type"] == AssetType.CRYPTO
        assert tx["symbol"] == "BTC"
        assert tx["quantity"] == 0.5
        assert tx["price_per_unit"] == 50000.0  # 25000 / 0.5
        assert tx["total_amount"] == 25000.0
        assert tx["fee"] == 10.0
        assert tx["currency"] == "USD"
        assert tx["net_value_usd"] == 24990.0
        assert tx["transaction_date"] == datetime(2024, 1, 15, 10, 30, 0)
        assert tx["tx_hash"] == "0x123abc"

    def test_parse_crypto_sell_transaction(self):
        """Test parsing of crypto SELL transaction"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-02-20 14:45:00,Sell,30000,USD,0.75,BTC,15,USD,29985,,,0x456def"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.SELL
        assert tx["asset_type"] == AssetType.CRYPTO
        assert tx["symbol"] == "BTC"
        assert tx["quantity"] == 0.75
        assert tx["price_per_unit"] == 40000.0  # 30000 / 0.75
        assert tx["total_amount"] == 30000.0
        assert tx["fee"] == 15.0
        assert tx["currency"] == "USD"
        assert tx["net_value_usd"] == 29985.0
        assert tx["transaction_date"] == datetime(2024, 2, 20, 14, 45, 0)

    def test_parse_staking_reward(self):
        """Test parsing of staking reward transaction"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-03-01 00:00:00,Staking,0.001,ETH,,,,,2.50,reward,Staking reward,0x789ghi"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.STAKING
        assert tx["asset_type"] == AssetType.CRYPTO
        assert tx["symbol"] == "ETH"
        assert tx["quantity"] == 0.001
        assert tx["price_per_unit"] == 2500.0  # 2.50 / 0.001
        assert tx["total_amount"] == 2.50
        assert tx["fee"] == 0.0
        assert tx["net_value_usd"] == 2.50
        assert tx["label"] == "reward"

    def test_parse_crypto_swap_transaction(self):
        """Test parsing of crypto swap (exchange) transaction"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-04-10 12:00:00,Exchange,2000,USDT,0.05,BTC,1,USDT,1999,,,0xabcdef"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        # Should create two transactions: SELL of BTC and BUY of USDT
        assert len(transactions) == 2

        # First transaction: SELL BTC
        sell_tx = transactions[0]
        assert sell_tx["transaction_type"] == TransactionType.SELL
        assert sell_tx["symbol"] == "BTC"
        assert sell_tx["quantity"] == 0.05

        # Second transaction: BUY USDT
        buy_tx = transactions[1]
        assert buy_tx["transaction_type"] == TransactionType.BUY
        assert buy_tx["symbol"] == "USDT"
        assert buy_tx["quantity"] == 2000

    def test_parse_multiple_transactions(self):
        """Test parsing multiple transactions in one file"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Buy,0.5,BTC,25000,USD,10,USD,24990,,,0x123
2024-01-16 11:00:00,Buy,10,ETH,25000,USD,10,USD,24990,,,0x456
2024-01-17 12:00:00,Sell,5000,USD,2,ETH,5,USD,4995,,,0x789"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 3
        assert transactions[0]["symbol"] == "BTC"
        assert transactions[1]["symbol"] == "ETH"
        assert transactions[2]["symbol"] == "ETH"

    def test_parse_with_empty_fee(self):
        """Test parsing transaction with no fee"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Buy,1,BTC,50000,USD,,,50000,,,0x123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0]["fee"] == 0.0

    def test_parse_airdrop_transaction(self):
        """Test parsing of airdrop/free crypto receipt"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-05-01 00:00:00,Airdrop,100,TOKEN,,,,,50.00,airdrop,Airdrop received,"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.AIRDROP
        assert tx["symbol"] == "TOKEN"
        assert tx["quantity"] == 100
        assert tx["net_value_usd"] == 50.00

    def test_parse_mining_reward(self):
        """Test parsing of mining reward transaction"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-06-01 00:00:00,Mining,0.00001,BTC,,,,,0.50,mining,Mining reward,0xmining123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.MINING
        assert tx["symbol"] == "BTC"
        assert tx["quantity"] == 0.00001
        assert tx["label"] == "mining"

    def test_parse_transfer_in(self):
        """Test parsing of crypto transfer in (deposit)"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-07-01 09:00:00,Deposit,1.5,ETH,,,0.001,ETH,3750,,,0xdeposit123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.DEPOSIT
        assert tx["symbol"] == "ETH"
        assert tx["quantity"] == 1.5
        assert tx["fee"] == 0.001

    def test_parse_transfer_out(self):
        """Test parsing of crypto transfer out (withdrawal)"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-07-02 10:00:00,Withdrawal,,,1.5,ETH,0.001,ETH,3750,,,0xwithdraw123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx["transaction_type"] == TransactionType.WITHDRAWAL
        assert tx["symbol"] == "ETH"
        assert tx["quantity"] == 1.5
        assert tx["fee"] == 0.001

    def test_handle_various_date_formats(self):
        """Test parsing with different date formats Koinly might use"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15T10:30:00Z,Buy,0.1,BTC,5000,USD,5,USD,4995,,,0x123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        # Should handle ISO format with timezone
        assert transactions[0]["transaction_date"].year == 2024

    def test_empty_csv_raises_error(self):
        """Test that empty CSV content raises an error"""
        csv_content = b""

        parser = CryptoParser()
        with pytest.raises(ValueError, match="Empty CSV file"):
            parser.parse(csv_content)

    def test_missing_headers_raises_error(self):
        """Test that missing required headers raises an error"""
        csv_content = b"""Date,Type,Amount
2024-01-15,Buy,0.5"""

        parser = CryptoParser()
        with pytest.raises(ValueError, match="missing required headers"):
            parser.parse(csv_content)

    def test_preserve_raw_data(self):
        """Test that raw CSV row data is preserved"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Buy,0.5,BTC,25000,USD,10,USD,24990,custom_label,Custom description,0x123abc"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        raw = transactions[0]["raw_data"]
        assert raw["Type"] == "Buy"
        assert raw["In Amount"] == "0.5"
        assert raw["In Currency"] == "BTC"
        assert raw["Description"] == "Custom description"

    def test_handle_decimal_precision(self):
        """Test handling of high precision decimal values"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Buy,0.123456789,BTC,6172.83945,USD,0.00123,USD,6172.83822,,,0x123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0]["quantity"] == 0.123456789
        assert transactions[0]["total_amount"] == 6172.83945
        assert transactions[0]["fee"] == 0.00123

    def test_skip_non_crypto_transactions(self):
        """Test that non-crypto transactions (like fiat deposits) are skipped"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Deposit,1000,USD,,,,,1000,,,
2024-01-16 11:00:00,Buy,0.02,BTC,1000,USD,1,USD,999,,,0x123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        # Should only have the BTC buy transaction, not the USD deposit
        assert len(transactions) == 1
        assert transactions[0]["symbol"] == "BTC"

    def test_handle_cost_basis_field(self):
        """Test preservation of cost basis information from Koinly"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash,Cost Basis
2024-01-15 10:30:00,Sell,10000,USD,0.2,BTC,10,USD,9990,,,0x123,8000"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0]["cost_basis"] == 8000.0

    def test_crypto_fee_in_crypto_currency(self):
        """Test handling fees paid in cryptocurrency"""
        csv_content = b"""Date,Type,In Amount,In Currency,Out Amount,Out Currency,Fee Amount,Fee Currency,Net Value(USD),Label,Description,TxHash
2024-01-15 10:30:00,Buy,0.5,BTC,25000,USD,0.0001,BTC,24990,,,0x123"""

        parser = CryptoParser()
        transactions = parser.parse(csv_content)

        assert len(transactions) == 1
        assert transactions[0]["fee"] == 0.0001
        assert transactions[0]["fee_currency"] == "BTC"

    def test_integration_with_csv_detector(self):
        """Test that CryptoParser integrates correctly with CSVDetector"""
        # Test detection
        filename = "Koinly Transactions.csv"
        file_type = CSVDetector.detect_file_type(filename)
        assert file_type == FileType.CRYPTO

        # Test validation
        validation = CSVDetector.validate_file(filename, 1024)
        assert validation["is_valid"] == True
        assert validation["file_type"] == FileType.CRYPTO