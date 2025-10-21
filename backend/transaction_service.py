# ABOUTME: Service layer for transaction operations and database persistence
# ABOUTME: Handles transaction storage, duplicate detection, and batch imports

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from models import Transaction, AssetType, TransactionType


class TransactionService:
    """Service for handling transaction database operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def store_transactions(
        self,
        transactions: List[Dict],
        source_file: str,
        allow_duplicates: bool = False
    ) -> Tuple[List[Transaction], List[Dict], List[Dict]]:
        """
        Store parsed transactions to the database

        Args:
            transactions: List of parsed transaction dictionaries
            source_file: Name of the source CSV file
            allow_duplicates: If True, skip duplicates; if False, raise error on duplicates

        Returns:
            Tuple of (saved_transactions, skipped_duplicates, failed_transactions)
        """
        saved = []
        skipped = []
        failed = []

        for tx_data in transactions:
            try:
                # Create Transaction object from parsed data
                transaction = await self._create_transaction_model(tx_data, source_file)

                # Check for duplicates
                if not allow_duplicates:
                    existing = await self._find_duplicate(transaction)
                    if existing:
                        skipped.append({
                            "transaction": tx_data,
                            "reason": f"Duplicate transaction found (ID: {existing.id})"
                        })
                        continue

                # Add to session
                self.session.add(transaction)

                # Try to flush to detect constraint violations
                try:
                    await self.session.flush()
                    saved.append(transaction)
                except IntegrityError as e:
                    # Duplicate based on unique constraint
                    await self.session.rollback()
                    if "uix_transaction_unique" in str(e):
                        skipped.append({
                            "transaction": tx_data,
                            "reason": "Duplicate based on unique constraint"
                        })
                    else:
                        failed.append({
                            "transaction": tx_data,
                            "error": str(e)
                        })

            except Exception as e:
                failed.append({
                    "transaction": tx_data,
                    "error": str(e)
                })
                await self.session.rollback()

        # Commit all successful transactions
        if saved:
            try:
                await self.session.commit()
            except Exception as e:
                await self.session.rollback()
                # Move all saved to failed if commit fails
                for tx in saved:
                    failed.append({
                        "transaction": self._transaction_to_dict(tx),
                        "error": f"Commit failed: {str(e)}"
                    })
                saved = []

        return saved, skipped, failed

    async def _create_transaction_model(self, tx_data: Dict, source_file: str) -> Transaction:
        """Create a Transaction model instance from parsed data"""

        # Handle optional fields with defaults
        quantity = tx_data.get('quantity')
        if quantity is not None:
            quantity = Decimal(str(quantity))

        price_per_unit = tx_data.get('price_per_unit', 0)
        if price_per_unit is not None:
            price_per_unit = Decimal(str(price_per_unit))

        total_amount = tx_data.get('total_amount', 0)
        if total_amount is not None:
            total_amount = Decimal(str(total_amount))

        fee = tx_data.get('fee', 0)
        if fee is not None:
            fee = Decimal(str(fee))

        cost_basis = tx_data.get('cost_basis')
        if cost_basis is not None:
            cost_basis = Decimal(str(cost_basis))

        # Create transaction
        transaction = Transaction(
            transaction_date=tx_data['transaction_date'],
            asset_type=tx_data['asset_type'],
            transaction_type=tx_data['transaction_type'],
            symbol=tx_data['symbol'],
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_amount=total_amount,
            currency=tx_data.get('currency', 'USD'),
            fee=fee,
            cost_basis=cost_basis,
            tax_lot_id=tx_data.get('tax_lot_id'),
            raw_data=tx_data.get('raw_data', {}),
            source_file=source_file,
            source_type=tx_data.get('source_type', 'UNKNOWN')
        )

        return transaction

    async def _find_duplicate(self, transaction: Transaction) -> Optional[Transaction]:
        """
        Find duplicate transaction based on unique constraint fields

        Returns existing transaction if found, None otherwise
        """
        stmt = select(Transaction).where(
            and_(
                Transaction.transaction_date == transaction.transaction_date,
                Transaction.symbol == transaction.symbol,
                Transaction.quantity == transaction.quantity,
                Transaction.transaction_type == transaction.transaction_type,
                Transaction.asset_type == transaction.asset_type
            )
        )

        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        # Handle if scalar_one_or_none is async
        if hasattr(existing, '__await__'):
            existing = await existing
        return existing

    async def check_duplicates(self, transactions: List[Dict]) -> List[Dict]:
        """
        Check which transactions would be duplicates before inserting

        Args:
            transactions: List of parsed transaction dictionaries

        Returns:
            List of transactions that would be duplicates
        """
        duplicates = []

        for tx_data in transactions:
            # Extract key fields for duplicate check
            try:
                # Handle quantity conversion
                quantity = tx_data.get('quantity')
                if quantity is not None:
                    quantity = Decimal(str(quantity))

                stmt = select(Transaction).where(
                    and_(
                        Transaction.transaction_date == tx_data['transaction_date'],
                        Transaction.symbol == tx_data['symbol'],
                        Transaction.quantity == quantity,
                        Transaction.transaction_type == tx_data['transaction_type'],
                        Transaction.asset_type == tx_data['asset_type']
                    )
                )

                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()
                # Handle if scalar_one_or_none is async
                if hasattr(existing, '__await__'):
                    existing = await existing

                if existing:
                    duplicates.append({
                        "transaction": tx_data,
                        "existing_id": existing.id,
                        "existing_source": existing.source_file
                    })
            except Exception as e:
                # If we can't check, assume not duplicate
                continue

        return duplicates

    async def get_import_summary(self, source_file: Optional[str] = None) -> Dict:
        """
        Get summary of imported transactions

        Args:
            source_file: Optional filter by source file

        Returns:
            Summary statistics
        """
        stmt = select(Transaction)
        if source_file:
            stmt = stmt.where(Transaction.source_file == source_file)

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        # Calculate summaries
        summary = {
            "total_transactions": len(transactions),
            "by_asset_type": {},
            "by_transaction_type": {},
            "by_symbol": {},
            "date_range": {}
        }

        if transactions:
            # Group by asset type
            for asset_type in AssetType:
                count = sum(1 for t in transactions if t.asset_type == asset_type)
                if count > 0:
                    summary["by_asset_type"][asset_type.value] = count

            # Group by transaction type
            for tx_type in TransactionType:
                count = sum(1 for t in transactions if t.transaction_type == tx_type)
                if count > 0:
                    summary["by_transaction_type"][tx_type.value] = count

            # Group by symbol (top 10)
            symbol_counts = {}
            for t in transactions:
                symbol_counts[t.symbol] = symbol_counts.get(t.symbol, 0) + 1

            top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            summary["by_symbol"] = dict(top_symbols)

            # Date range
            dates = [t.transaction_date for t in transactions]
            summary["date_range"] = {
                "earliest": min(dates).isoformat() if dates else None,
                "latest": max(dates).isoformat() if dates else None
            }

        return summary

    def _transaction_to_dict(self, transaction: Transaction) -> Dict:
        """Convert Transaction model to dictionary"""
        return {
            "id": transaction.id,
            "transaction_date": transaction.transaction_date.isoformat(),
            "asset_type": transaction.asset_type.value,
            "transaction_type": transaction.transaction_type.value,
            "symbol": transaction.symbol,
            "quantity": float(transaction.quantity) if transaction.quantity else None,
            "price_per_unit": float(transaction.price_per_unit) if transaction.price_per_unit else None,
            "total_amount": float(transaction.total_amount) if transaction.total_amount else None,
            "currency": transaction.currency,
            "fee": float(transaction.fee) if transaction.fee else None,
            "source_file": transaction.source_file,
            "source_type": transaction.source_type
        }


class DuplicateHandler:
    """Handle duplicate transaction detection and resolution"""

    @staticmethod
    async def resolve_duplicates(
        session: AsyncSession,
        duplicates: List[Dict],
        strategy: str = "skip"
    ) -> List[Dict]:
        """
        Resolve duplicate transactions based on strategy

        Args:
            session: Database session
            duplicates: List of duplicate transaction info
            strategy: How to handle duplicates - "skip", "update", or "force"

        Returns:
            List of resolved transactions
        """
        resolved = []

        for dup in duplicates:
            if strategy == "skip":
                # Skip the duplicate
                resolved.append({
                    "action": "skipped",
                    "transaction": dup["transaction"],
                    "reason": f"Duplicate of transaction ID {dup['existing_id']}"
                })
            elif strategy == "update":
                # Update the existing transaction
                stmt = select(Transaction).where(Transaction.id == dup["existing_id"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update fields that might have changed
                    tx_data = dup["transaction"]
                    existing.price_per_unit = Decimal(str(tx_data.get('price_per_unit', 0)))
                    existing.total_amount = Decimal(str(tx_data.get('total_amount', 0)))
                    existing.fee = Decimal(str(tx_data.get('fee', 0)))
                    existing.raw_data = tx_data.get('raw_data', {})

                    resolved.append({
                        "action": "updated",
                        "transaction": dup["transaction"],
                        "transaction_id": existing.id
                    })
            elif strategy == "force":
                # Force insert by slightly modifying the timestamp
                tx_data = dup["transaction"].copy()
                # Add 1 microsecond to make it unique
                from datetime import timedelta
                tx_data["transaction_date"] = tx_data["transaction_date"] + timedelta(microseconds=1)

                resolved.append({
                    "action": "forced",
                    "transaction": tx_data,
                    "note": "Timestamp modified to allow insertion"
                })

        if strategy in ["update", "force"]:
            await session.commit()

        return resolved