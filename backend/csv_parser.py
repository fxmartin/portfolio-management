# ABOUTME: CSV parser module for detecting and parsing different CSV formats
# ABOUTME: Handles Revolut metals, stocks, and Koinly crypto transaction files

import re
from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path

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

    def parse(self, content: bytes) -> List[Dict]:
        """Parse Koinly crypto CSV"""
        # TODO: Implement crypto parsing logic
        return []

def get_parser(file_type: FileType) -> Optional[CSVParser]:
    """Get appropriate parser for file type"""
    parsers = {
        FileType.METALS: MetalsParser(),
        FileType.STOCKS: StocksParser(),
        FileType.CRYPTO: CryptoParser()
    }
    return parsers.get(file_type)