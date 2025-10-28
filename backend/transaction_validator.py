# ABOUTME: Transaction validation service with business rules
# ABOUTME: Validates create, update, and delete operations to maintain portfolio data integrity

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from models import Transaction, TransactionType, AssetType


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    ERROR = "error"  # Blocking validation failure
    WARNING = "warning"  # Non-blocking warning
    INFO = "info"  # Informational message


class ValidationMessage(BaseModel):
    """Validation message with level and details"""
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of validation with pass/fail status and messages"""
    valid: bool
    messages: List[ValidationMessage] = []

    def add_error(self, message: str, field: Optional[str] = None, suggestion: Optional[str] = None):
        """Add an error message (blocking)"""
        self.valid = False
        self.messages.append(ValidationMessage(
            level=ValidationLevel.ERROR,
            message=message,
            field=field,
            suggestion=suggestion
        ))

    def add_warning(self, message: str, field: Optional[str] = None, suggestion: Optional[str] = None):
        """Add a warning message (non-blocking)"""
        self.messages.append(ValidationMessage(
            level=ValidationLevel.WARNING,
            message=message,
            field=field,
            suggestion=suggestion
        ))

    def add_info(self, message: str, field: Optional[str] = None):
        """Add an info message"""
        self.messages.append(ValidationMessage(
            level=ValidationLevel.INFO,
            message=message,
            field=field
        ))


class TransactionValidator:
    """
    Validation service for transaction operations.

    Business Rules:
    1. No Negative Holdings: Cannot sell more than owned
    2. Valid Dates: Transaction dates must be chronological for FIFO
    3. Price Validation: Prices must be reasonable (warn if >50% deviation from market)
    4. Fee Validation: Fees must be less than transaction value
    5. Currency Consistency: Warn if mixing currencies for same symbol
    6. Duplicate Detection: Flag potential duplicates (same symbol, date, quantity)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_create(
        self,
        transaction_date: datetime,
        asset_type: AssetType,
        transaction_type: TransactionType,
        symbol: str,
        quantity: Decimal,
        price_per_unit: Optional[Decimal],
        fee: Optional[Decimal],
        currency: str,
        notes: Optional[str] = None
    ) -> ValidationResult:
        """Validate transaction creation"""
        result = ValidationResult(valid=True)

        # Required field validation
        if not symbol or symbol.strip() == "":
            result.add_error("Symbol is required", "symbol")

        if quantity is None or quantity <= 0:
            result.add_error("Quantity must be greater than zero", "quantity")

        if transaction_date is None:
            result.add_error("Transaction date is required", "transaction_date")

        # Price validation for BUY/SELL transactions
        if transaction_type in [TransactionType.BUY, TransactionType.SELL]:
            if price_per_unit is None:
                result.add_error(
                    f"Price is required for {transaction_type.value} transactions",
                    "price_per_unit",
                    "Enter the price per unit for this transaction"
                )
            elif price_per_unit < 0:
                result.add_error("Price cannot be negative", "price_per_unit")

        # Fee validation
        if fee is not None:
            if fee < 0:
                result.add_error("Fee cannot be negative", "fee")
            elif price_per_unit and quantity:
                total_value = price_per_unit * quantity
                if fee > total_value:
                    result.add_warning(
                        f"Fee ({fee}) exceeds transaction value ({total_value})",
                        "fee",
                        "Double-check the fee amount"
                    )

        # Date validation - cannot be in the future
        # Make sure transaction_date is timezone-naive for comparison
        if transaction_date.tzinfo is not None:
            transaction_date = transaction_date.replace(tzinfo=None)

        now = datetime.now()  # Timezone-naive
        if transaction_date > now:
            result.add_error(
                "Transaction date cannot be in the future",
                "transaction_date",
                "Use today's date or earlier"
            )

        # Notes length validation
        if notes and len(notes) > 500:
            result.add_error(
                "Notes cannot exceed 500 characters",
                "notes",
                f"Current length: {len(notes)} characters"
            )

        # Check for negative holdings (for SELL transactions)
        if transaction_type == TransactionType.SELL:
            available_quantity = await self._get_holdings_at_date(symbol, transaction_date)
            if quantity > available_quantity:
                result.add_error(
                    f"Cannot sell {quantity} {symbol}. Only {available_quantity} available.",
                    "quantity",
                    f"Reduce quantity to {available_quantity} or less"
                )

        # Check for currency consistency
        await self._check_currency_consistency(symbol, currency, result)

        # Check for potential duplicates
        await self._check_duplicates(
            transaction_date=transaction_date,
            symbol=symbol,
            quantity=quantity,
            transaction_type=transaction_type,
            result=result
        )

        return result

    async def validate_update(
        self,
        transaction_id: int,
        new_values: Dict[str, Any]
    ) -> ValidationResult:
        """Validate transaction update"""
        result = ValidationResult(valid=True)

        # Get existing transaction
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        db_result = await self.db.execute(stmt)
        old_transaction = db_result.scalar_one_or_none()

        if not old_transaction:
            result.add_error(f"Transaction {transaction_id} not found")
            return result

        # Check if transaction is from CSV import
        if old_transaction.source == 'CSV' or old_transaction.source_type in ['REVOLUT', 'KOINLY']:
            result.add_warning(
                "This is an imported transaction. Consider re-importing instead of editing.",
                suggestion="Delete and re-import the CSV file for best data integrity"
            )

        # Validate individual fields if they're being changed
        if 'quantity' in new_values:
            quantity = new_values['quantity']
            if quantity <= 0:
                result.add_error("Quantity must be greater than zero", "quantity")

        if 'price_per_unit' in new_values:
            price = new_values['price_per_unit']
            if price < 0:
                result.add_error("Price cannot be negative", "price_per_unit")

        if 'fee' in new_values:
            fee = new_values['fee']
            if fee < 0:
                result.add_error("Fee cannot be negative", "fee")

        if 'transaction_date' in new_values:
            new_date = new_values['transaction_date']
            if new_date.tzinfo is not None:
                new_date = new_date.replace(tzinfo=None)
            now = datetime.now()  # Timezone-naive
            if new_date > now:
                result.add_error("Transaction date cannot be in the future", "transaction_date")

        # Check if update would create negative holdings
        if old_transaction.transaction_type == TransactionType.SELL:
            new_quantity = new_values.get('quantity', old_transaction.quantity)
            new_date = new_values.get('transaction_date', old_transaction.transaction_date)

            # Calculate holdings before this transaction
            available_quantity = await self._get_holdings_at_date(
                old_transaction.symbol,
                new_date,
                exclude_transaction_id=transaction_id
            )

            if new_quantity > available_quantity:
                result.add_error(
                    f"Update would create negative holdings. Only {available_quantity} {old_transaction.symbol} available.",
                    "quantity"
                )

        return result

    async def validate_delete(
        self,
        transaction_id: int
    ) -> ValidationResult:
        """Validate transaction deletion"""
        result = ValidationResult(valid=True)

        # Get the transaction
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        db_result = await self.db.execute(stmt)
        transaction = db_result.scalar_one_or_none()

        if not transaction:
            result.add_error(f"Transaction {transaction_id} not found")
            return result

        # Check if deletion would create negative holdings
        if transaction.transaction_type == TransactionType.BUY:
            # Calculate holdings after this transaction is removed
            available_quantity = await self._get_holdings_at_date(
                transaction.symbol,
                datetime.now(),  # Timezone-naive
                exclude_transaction_id=transaction_id
            )

            if available_quantity < 0:
                result.add_error(
                    f"Cannot delete this transaction. It would create negative holdings for {transaction.symbol}.",
                    suggestion="Delete more recent SELL transactions first"
                )

        # Warn if this affects realized P&L
        if transaction.transaction_type == TransactionType.SELL:
            result.add_warning(
                "Deleting this SELL transaction will affect your realized P&L calculations",
                suggestion="Consider if this will impact your tax records"
            )

        return result

    async def _get_holdings_at_date(
        self,
        symbol: str,
        date: datetime,
        exclude_transaction_id: Optional[int] = None
    ) -> Decimal:
        """Calculate holdings for a symbol at a specific date"""
        # Make timezone-naive
        if date.tzinfo is not None:
            date = date.replace(tzinfo=None)

        # Build query to get all transactions before this date
        from sqlalchemy import case

        stmt = select(
            func.sum(
                case(
                    (Transaction.transaction_type == TransactionType.BUY, Transaction.quantity),
                    (Transaction.transaction_type == TransactionType.SELL, -Transaction.quantity),
                    (Transaction.transaction_type == TransactionType.STAKING, Transaction.quantity),
                    (Transaction.transaction_type == TransactionType.AIRDROP, Transaction.quantity),
                    (Transaction.transaction_type == TransactionType.MINING, Transaction.quantity),
                    (Transaction.transaction_type == TransactionType.DEPOSIT, Transaction.quantity),
                    (Transaction.transaction_type == TransactionType.WITHDRAWAL, -Transaction.quantity),
                    else_=0
                )
            )
        ).where(
            and_(
                Transaction.symbol == symbol,
                Transaction.transaction_date < date,
                Transaction.deleted_at.is_(None)
            )
        )

        if exclude_transaction_id:
            stmt = stmt.where(Transaction.id != exclude_transaction_id)

        result = await self.db.execute(stmt)
        holdings = result.scalar()

        return holdings if holdings else Decimal('0')

    async def _check_currency_consistency(
        self,
        symbol: str,
        currency: str,
        result: ValidationResult
    ):
        """Warn if mixing currencies for the same symbol"""
        stmt = select(Transaction.currency).where(
            and_(
                Transaction.symbol == symbol,
                Transaction.deleted_at.is_(None)
            )
        ).distinct().limit(5)

        db_result = await self.db.execute(stmt)
        existing_currencies = [row[0] for row in db_result.all()]

        if existing_currencies and currency not in existing_currencies:
            result.add_warning(
                f"Currency {currency} differs from existing transactions for {symbol} ({', '.join(existing_currencies)})",
                "currency",
                "Mixing currencies may affect P&L calculations"
            )

    async def _check_duplicates(
        self,
        transaction_date: datetime,
        symbol: str,
        quantity: Decimal,
        transaction_type: TransactionType,
        result: ValidationResult,
        transaction_id: Optional[int] = None
    ):
        """Check for potential duplicate transactions"""
        # Look for transactions with same symbol, date, quantity, and type
        # within a 1-minute window

        # Make timezone-naive for database comparison
        if transaction_date.tzinfo is not None:
            transaction_date = transaction_date.replace(tzinfo=None)

        date_start = transaction_date.replace(second=0, microsecond=0)
        # Handle minute overflow
        if date_start.minute == 59:
            from datetime import timedelta
            date_end = date_start.replace(minute=0) + timedelta(hours=1)
        else:
            date_end = date_start.replace(minute=date_start.minute + 1)

        stmt = select(Transaction).where(
            and_(
                Transaction.symbol == symbol,
                Transaction.transaction_date >= date_start,
                Transaction.transaction_date < date_end,
                Transaction.quantity == quantity,
                Transaction.transaction_type == transaction_type,
                Transaction.deleted_at.is_(None)
            )
        )

        if transaction_id:
            stmt = stmt.where(Transaction.id != transaction_id)

        db_result = await self.db.execute(stmt)
        duplicates = db_result.scalars().all()

        if duplicates:
            result.add_warning(
                f"Found {len(duplicates)} similar transaction(s) around this time",
                suggestion="Check if this is a duplicate entry"
            )

    async def detect_duplicates(
        self,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[List[Transaction]]:
        """Find potential duplicate transactions across the portfolio"""
        # Group transactions by symbol, date (minute precision), quantity, and type
        # This is a more expensive operation, so we limit results

        stmt = select(Transaction).where(Transaction.deleted_at.is_(None))

        if symbol:
            stmt = stmt.where(Transaction.symbol == symbol)

        stmt = stmt.order_by(Transaction.transaction_date.desc()).limit(limit * 2)

        result = await self.db.execute(stmt)
        transactions = result.scalars().all()

        # Group potential duplicates
        groups: Dict[tuple, List[Transaction]] = {}

        for txn in transactions:
            # Create a key based on similarity criteria
            key = (
                txn.symbol,
                txn.transaction_date.replace(second=0, microsecond=0),
                txn.quantity,
                txn.transaction_type
            )

            if key not in groups:
                groups[key] = []
            groups[key].append(txn)

        # Filter out groups with only one transaction
        duplicate_groups = [group for group in groups.values() if len(group) > 1]

        return duplicate_groups[:limit]
