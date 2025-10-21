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

    # Precious metals symbols
    METAL_SYMBOLS = {"XAU", "XAG", "XPT", "XPD"}  # Gold, Silver, Platinum, Palladium

    def parse(self, content: bytes) -> List[Dict]:
        """Parse Revolut metals CSV and return list of transactions"""

        # Handle empty content
        if not content or len(content.strip()) == 0:
            raise ValueError("Empty CSV file")

        # Decode content
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = content.decode('utf-8-sig')  # Handle BOM

        # Parse CSV using csv.DictReader
        csv_file = StringIO(text_content)
        reader = csv.DictReader(csv_file)

        # Validate required headers
        if not reader.fieldnames:
            raise ValueError("Invalid CSV format: missing headers")

        required_headers = {"Type", "Product", "Started Date", "Completed Date",
                           "Description", "Amount", "Fee", "Currency", "State", "Balance"}
        if not required_headers.issubset(set(reader.fieldnames)):
            missing = required_headers - set(reader.fieldnames)
            raise ValueError(f"Invalid CSV format: missing required headers: {missing}")

        transactions = []

        for row in reader:
            # Skip non-exchange transactions (only process metal exchanges)
            if row["Type"] != "Exchange":
                continue

            # Skip non-completed transactions
            if row["State"] != "COMPLETED":
                continue

            # Check if currency is a metal symbol
            currency = row["Currency"].strip()
            if currency not in self.METAL_SYMBOLS and currency not in {"EUR", "USD", "GBP"}:
                # If not a known metal or fiat currency, skip
                continue

            # Parse amount to determine transaction type using Decimal for precision
            amount = Decimal(row["Amount"])
            fee = Decimal(row["Fee"])
            balance = Decimal(row["Balance"])

            # Negative amount means selling metals for fiat
            # Positive amount means buying metals with fiat
            if amount < 0:
                # Selling metal (negative amount, metal currency)
                if currency in self.METAL_SYMBOLS:
                    tx_type = TransactionType.SELL
                    symbol = currency
                    quantity = abs(amount)  # Make positive
                else:
                    # This shouldn't happen for metals in the current format
                    continue
            else:
                # Buying metal (positive amount, metal currency)
                if currency in self.METAL_SYMBOLS:
                    tx_type = TransactionType.BUY
                    symbol = currency
                    quantity = amount - fee  # Net quantity after fee
                else:
                    # Fiat currency with positive amount - skip
                    continue

            # Parse transaction date
            date_str = row["Completed Date"]
            transaction_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

            # Build transaction - convert Decimals to float for JSON serialization
            transaction = {
                "transaction_type": tx_type,
                "asset_type": AssetType.METAL,
                "symbol": symbol,
                "quantity": float(quantity),
                "gross_quantity": float(abs(amount)),
                "fee": float(fee),
                "fee_currency": currency,
                "transaction_date": transaction_date,
                "balance_after": float(balance),
                "description": row["Description"],
                "source_type": "REVOLUT",
                "raw_data": dict(row)
            }

            # For metals, we don't have price per unit in the CSV
            # This would need to be calculated from exchange rate if needed
            transaction["price_per_unit"] = 0.0
            transaction["total_amount"] = 0.0
            transaction["currency"] = "EUR"  # Default base currency

            transactions.append(transaction)

        return transactions

class StocksParser(CSVParser):
    """Parser for Revolut stocks export"""

    def parse(self, content: bytes) -> List[Dict]:
        """Parse Revolut stocks CSV and return list of transactions"""

        # Handle empty content
        if not content or len(content.strip()) == 0:
            raise ValueError("Empty CSV file")

        # Decode content
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

        # Check for required headers in at least one format
        actual_format_headers = {'Date', 'Ticker', 'Type', 'Quantity', 'Price per share', 'Total Amount'}
        test_format_headers = {'Date', 'Time', 'Type', 'Product', 'Ticker'}

        has_actual_headers = actual_format_headers.issubset(set(reader.fieldnames))
        has_test_headers = test_format_headers.issubset(set(reader.fieldnames))

        if not has_actual_headers and not has_test_headers:
            raise ValueError(f"Invalid CSV format: missing required headers")

        # Detect format version
        has_time_field = 'Time' in reader.fieldnames
        has_product_field = 'Product' in reader.fieldnames

        transactions = []

        for row in reader:
            try:
                # Skip CASH TOP-UP transactions
                if 'CASH TOP-UP' in row.get('Type', ''):
                    continue

                # Parse based on format
                if has_time_field and has_product_field:
                    # Old test format with separate Date and Time
                    tx = self._parse_test_format_row(row)
                else:
                    # New actual Revolut format
                    tx = self._parse_actual_format_row(row)

                if tx:
                    transactions.append(tx)

            except (ValueError, KeyError) as e:
                # Skip rows that can't be parsed
                continue

        return transactions

    def _parse_actual_format_row(self, row: Dict) -> Optional[Dict]:
        """Parse a row from the actual Revolut stocks CSV format"""

        # Skip if no ticker (cash transactions)
        if not row.get('Ticker'):
            return None

        # Parse transaction type
        type_str = row.get('Type', '').upper()
        if 'BUY' in type_str:
            tx_type = TransactionType.BUY
        elif 'SELL' in type_str:
            tx_type = TransactionType.SELL
        elif 'DIVIDEND' in type_str:
            tx_type = TransactionType.DIVIDEND
        else:
            return None

        # Parse date from ISO format
        date_str = row['Date']
        if 'T' in date_str:
            # ISO format with timezone
            date_str = date_str.replace('Z', '+00:00')
            transaction_date = datetime.fromisoformat(date_str.split('.')[0])
        else:
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d')

        # Parse numeric values
        quantity = float(row['Quantity']) if row.get('Quantity') else None

        # Clean price and total amount (remove currency symbols)
        price_str = row.get('Price per share', '').replace('€', '').replace('$', '').replace('£', '').strip()
        total_str = row.get('Total Amount', '').replace('€', '').replace('$', '').replace('£', '').strip()

        price_per_unit = float(price_str) if price_str else 0.0
        total_amount = float(total_str) if total_str else 0.0

        # Determine currency
        currency = row.get('Currency', 'EUR')

        return {
            "transaction_type": tx_type,
            "asset_type": AssetType.STOCK,
            "symbol": row['Ticker'],
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "total_amount": total_amount,
            "currency": currency,
            "fee": 0.0,  # Revolut doesn't show fees in this export
            "transaction_date": transaction_date,
            "fx_rate": float(row.get('FX Rate', 1.0)),
            "source_type": "REVOLUT",
            "raw_data": dict(row)
        }

    def _parse_test_format_row(self, row: Dict) -> Optional[Dict]:
        """Parse a row from the test fixture format"""

        # Parse transaction type
        type_str = row.get('Type', '').upper()
        if type_str == 'BUY':
            tx_type = TransactionType.BUY
        elif type_str == 'SELL':
            tx_type = TransactionType.SELL
        elif type_str == 'DIVIDEND':
            tx_type = TransactionType.DIVIDEND
        else:
            return None

        # Parse date and time
        date_str = row['Date']
        time_str = row.get('Time', '00:00:00')
        datetime_str = f"{date_str} {time_str}"
        transaction_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

        # Parse numeric values
        quantity_str = row.get('Quantity', '').strip()
        quantity = float(quantity_str) if quantity_str else None

        price_per_unit = float(row.get('Price per share', 0))
        total_amount = float(row.get('Total Amount', 0))

        # Get fee if present
        fee = float(row.get('Fee', 0))

        return {
            "transaction_type": tx_type,
            "asset_type": AssetType.STOCK,
            "symbol": row.get('Ticker', ''),
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "total_amount": total_amount,
            "currency": row.get('Currency', 'USD'),
            "fee": fee,
            "transaction_date": transaction_date,
            "fx_rate": float(row.get('FX Rate', 1.0)),
            "product": row.get('Product', ''),  # Company name
            "source_type": "REVOLUT",
            "raw_data": dict(row)
        }

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