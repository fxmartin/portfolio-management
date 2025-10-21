# ABOUTME: CSV parser module for detecting and parsing different CSV formats
# ABOUTME: Handles Revolut metals, stocks, and Koinly crypto transaction files

import re
import csv
from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from io import StringIO
from decimal import Decimal
from models import AssetType, TransactionType

class FileType(str, Enum):
    """Supported CSV file types"""
    METALS = "METALS"
    STOCKS = "STOCKS"
    CRYPTO = "CRYPTO"
    UNKNOWN = "UNKNOWN"

class CSVDetector:
    """Detects the type of CSV file based on filename patterns"""

    @staticmethod
    def detect_file_type(filename: str) -> FileType:
        """
        Detect CSV type from filename pattern

        Args:
            filename: Name of the CSV file

        Returns:
            FileType enum indicating the detected type
        """
        # Check for Revolut metals account statement
        if filename.startswith('account-statement_'):
            return FileType.METALS

        # Check for Revolut stocks export (UUID format)
        uuid_pattern = r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\.csv$'
        if re.match(uuid_pattern, filename, re.IGNORECASE):
            return FileType.STOCKS

        # Check for Koinly crypto export
        if 'koinly' in filename.lower():
            return FileType.CRYPTO

        return FileType.UNKNOWN

    @staticmethod
    def validate_file(filename: str, file_size: int) -> Dict[str, any]:
        """
        Validate uploaded file

        Args:
            filename: Name of the file
            file_size: Size of the file in bytes

        Returns:
            Dict with validation results
        """
        result = {
            "is_valid": True,
            "file_type": FileType.UNKNOWN,
            "errors": []
        }

        # Check file extension
        if not filename.lower().endswith('.csv'):
            result["is_valid"] = False
            result["errors"].append("File must be a CSV file")
            return result

        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if file_size > max_size:
            result["is_valid"] = False
            result["errors"].append(f"File size exceeds 10MB limit (size: {file_size / 1024 / 1024:.2f}MB)")
            return result

        # Detect file type
        file_type = CSVDetector.detect_file_type(filename)
        result["file_type"] = file_type

        if file_type == FileType.UNKNOWN:
            result["is_valid"] = False
            result["errors"].append(
                "Unknown CSV format. Expected formats: "
                "account-statement_*.csv (Metals), "
                "[UUID].csv (Stocks), or "
                "*Koinly*.csv (Crypto)"
            )

        return result

class CSVParser:
    """Base class for CSV parsers"""

    def parse(self, content: bytes) -> List[Dict]:
        """Parse CSV content and return list of transactions"""
        raise NotImplementedError("Subclasses must implement parse method")

class MetalsParser(CSVParser):
    """Parser for Revolut metals account statement"""

    def parse(self, content: bytes) -> List[Dict]:
        """Parse Revolut metals CSV"""
        # TODO: Implement metals parsing logic
        return []

class StocksParser(CSVParser):
    """Parser for Revolut stocks export"""

    def parse(self, content: bytes) -> List[Dict]:
        """Parse Revolut stocks CSV"""
        # TODO: Implement stocks parsing logic
        return []

class CryptoParser(CSVParser):
    """Parser for Koinly crypto export"""

    # Fiat currencies to skip when looking for crypto
    FIAT_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY"}

    def parse(self, content: bytes) -> List[Dict]:
        """Parse Koinly crypto CSV and return list of transactions"""

        # Handle empty content
        if not content or len(content.strip()) == 0:
            raise ValueError("Empty CSV file")

        # Decode content and create CSV reader
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = content.decode('utf-8-sig')  # Handle BOM

        # Parse CSV using csv.DictReader
        csv_file = StringIO(text_content)
        reader = csv.DictReader(csv_file)

        # Validate headers
        if not reader.fieldnames:
            raise ValueError("Invalid CSV format: missing headers")

        # Detect which format we have
        is_new_format = "Date (UTC)" in reader.fieldnames
        is_old_format = "Date" in reader.fieldnames and "In Amount" in reader.fieldnames

        transactions = []

        for row in reader:
            # Skip deleted transactions
            if row.get("Deleted", "").lower() == "true":
                continue

            # Parse based on format
            if is_new_format:
                tx = self._parse_new_format_row(row)
            elif is_old_format:
                tx = self._parse_old_format_row(row)
            else:
                # Skip if format not recognized, don't fail
                continue

            if tx:
                transactions.extend(tx if isinstance(tx, list) else [tx])

        return transactions

    def _parse_new_format_row(self, row: Dict) -> List[Dict]:
        """Parse a row from the new Koinly format"""
        transactions = []

        # Get transaction type
        tx_type = row["Type"].lower()
        tag = row.get("Tag", "").lower()

        # Parse date
        date_str = row["Date (UTC)"]
        if date_str:
            transaction_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            return []

        # Get amounts and currencies
        from_amount = row.get("From Amount", "").strip()
        from_currency = self._clean_currency(row.get("From Currency", ""))
        to_amount = row.get("To Amount", "").strip()
        to_currency = self._clean_currency(row.get("To Currency", ""))
        fee_amount = row.get("Fee Amount", "").strip()
        fee_currency = self._clean_currency(row.get("Fee Currency", ""))

        # Get net value (in base currency, usually EUR or USD)
        net_value = row.get("Net Value (read-only)", "").strip()
        value_currency = self._clean_currency(row.get("Value Currency (read-only)", ""))

        # Parse transaction hash if available
        tx_hash = row.get("TxHash", "").strip()
        description = row.get("Description", "").strip()

        # Handle different transaction types
        if tx_type == "trade":
            # Trade: sell one asset, buy another
            if from_currency and not self._is_fiat(from_currency):
                # Selling crypto
                sell_tx = {
                    "transaction_type": TransactionType.SELL,
                    "asset_type": AssetType.CRYPTO,
                    "symbol": from_currency,
                    "quantity": float(from_amount) if from_amount else 0.0,
                    "price_per_unit": float(net_value) / float(from_amount) if from_amount and net_value else 0.0,
                    "total_amount": float(net_value) if net_value else 0.0,
                    "currency": value_currency if value_currency else "EUR",
                    "fee": float(fee_amount) / 2 if fee_amount else 0.0,
                    "fee_currency": fee_currency if fee_currency else value_currency,
                    "transaction_date": transaction_date,
                    "tx_hash": tx_hash,
                    "description": description,
                    "source_type": "KOINLY",
                    "raw_data": dict(row)
                }
                transactions.append(sell_tx)

            if to_currency and not self._is_fiat(to_currency):
                # Buying crypto
                buy_tx = {
                    "transaction_type": TransactionType.BUY,
                    "asset_type": AssetType.CRYPTO,
                    "symbol": to_currency,
                    "quantity": float(to_amount) if to_amount else 0.0,
                    "price_per_unit": float(net_value) / float(to_amount) if to_amount and net_value else 0.0,
                    "total_amount": float(net_value) if net_value else 0.0,
                    "currency": value_currency if value_currency else "EUR",
                    "fee": float(fee_amount) / 2 if fee_amount else 0.0,
                    "fee_currency": fee_currency if fee_currency else value_currency,
                    "transaction_date": transaction_date,
                    "tx_hash": tx_hash,
                    "description": description,
                    "source_type": "KOINLY",
                    "raw_data": dict(row)
                }
                transactions.append(buy_tx)

        elif tx_type == "deposit":
            # Check the tag to determine the type of deposit
            if tag == "reward":
                # Staking reward
                if to_currency and not self._is_fiat(to_currency):
                    tx = {
                        "transaction_type": TransactionType.STAKING,
                        "asset_type": AssetType.CRYPTO,
                        "symbol": to_currency,
                        "quantity": float(to_amount) if to_amount else 0.0,
                        "price_per_unit": float(net_value) / float(to_amount) if to_amount and net_value else 0.0,
                        "total_amount": float(net_value) if net_value else 0.0,
                        "currency": value_currency if value_currency else "EUR",
                        "fee": float(fee_amount) if fee_amount else 0.0,
                        "fee_currency": fee_currency if fee_currency else value_currency,
                        "transaction_date": transaction_date,
                        "tx_hash": tx_hash,
                        "description": description,
                        "source_type": "KOINLY",
                        "raw_data": dict(row)
                    }
                    transactions.append(tx)
            elif tag == "airdrop":
                # Airdrop
                if to_currency and not self._is_fiat(to_currency):
                    tx = {
                        "transaction_type": TransactionType.AIRDROP,
                        "asset_type": AssetType.CRYPTO,
                        "symbol": to_currency,
                        "quantity": float(to_amount) if to_amount else 0.0,
                        "price_per_unit": float(net_value) / float(to_amount) if to_amount and net_value else 0.0,
                        "total_amount": float(net_value) if net_value else 0.0,
                        "currency": value_currency if value_currency else "EUR",
                        "fee": 0.0,
                        "transaction_date": transaction_date,
                        "tx_hash": tx_hash,
                        "description": description,
                        "source_type": "KOINLY",
                        "raw_data": dict(row)
                    }
                    transactions.append(tx)
            else:
                # Regular deposit
                if to_currency and not self._is_fiat(to_currency):
                    tx = {
                        "transaction_type": TransactionType.DEPOSIT,
                        "asset_type": AssetType.CRYPTO,
                        "symbol": to_currency,
                        "quantity": float(to_amount) if to_amount else 0.0,
                        "price_per_unit": float(net_value) / float(to_amount) if to_amount and net_value else 0.0,
                        "total_amount": float(net_value) if net_value else 0.0,
                        "currency": value_currency if value_currency else "EUR",
                        "fee": float(fee_amount) if fee_amount else 0.0,
                        "fee_currency": fee_currency if fee_currency else value_currency,
                        "transaction_date": transaction_date,
                        "tx_hash": tx_hash,
                        "description": description,
                        "source_type": "KOINLY",
                        "raw_data": dict(row)
                    }
                    transactions.append(tx)

        elif tx_type == "withdrawal":
            # Withdrawal
            if from_currency and not self._is_fiat(from_currency):
                tx = {
                    "transaction_type": TransactionType.WITHDRAWAL,
                    "asset_type": AssetType.CRYPTO,
                    "symbol": from_currency,
                    "quantity": float(from_amount) if from_amount else 0.0,
                    "price_per_unit": float(net_value) / float(from_amount) if from_amount and net_value else 0.0,
                    "total_amount": float(net_value) if net_value else 0.0,
                    "currency": value_currency if value_currency else "EUR",
                    "fee": float(fee_amount) if fee_amount else 0.0,
                    "fee_currency": fee_currency if fee_currency else value_currency,
                    "transaction_date": transaction_date,
                    "tx_hash": tx_hash,
                    "description": description,
                    "source_type": "KOINLY",
                    "raw_data": dict(row)
                }
                transactions.append(tx)

        return transactions

    def _parse_old_format_row(self, row: Dict) -> Dict:
        """Parse a row from the old/simplified Koinly format"""
        # For backward compatibility with test format
        # Return None for now as we focus on real Koinly format
        return None

    def _clean_currency(self, currency: str) -> str:
        """Clean currency code by removing metadata"""
        if not currency:
            return ""

        # Remove Koinly metadata like ";6166" from "SOL;6166"
        if ";" in currency:
            currency = currency.split(";")[0]

        return currency.strip()

    def _is_fiat(self, currency: str) -> bool:
        """Check if a currency is fiat"""
        clean_currency = self._clean_currency(currency)
        return clean_currency in self.FIAT_CURRENCIES

def get_parser(file_type: FileType) -> Optional[CSVParser]:
    """Get appropriate parser for file type"""
    parsers = {
        FileType.METALS: MetalsParser(),
        FileType.STOCKS: StocksParser(),
        FileType.CRYPTO: CryptoParser()
    }
    return parsers.get(file_type)