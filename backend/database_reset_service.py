# ABOUTME: Database reset service for safely clearing all transaction data
# ABOUTME: Provides atomic deletion with audit logging and safety confirmations

from datetime import datetime
from typing import Dict
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

logger = logging.getLogger(__name__)


class DatabaseResetService:
    """Service for safely resetting the database and clearing all transactions"""

    CONFIRMATION_CODE = "DELETE_ALL_TRANSACTIONS"

    def __init__(self, db_session: Session):
        self.db = db_session

    def reset_database(self, confirmation_code: str, user_info: str = "system") -> Dict:
        """
        Reset the database by clearing all transaction-related data.

        Args:
            confirmation_code: Must match CONFIRMATION_CODE for safety
            user_info: Identifier for who initiated the reset (for audit logging)

        Returns:
            Dictionary with status and message

        Raises:
            ValueError: If confirmation code is invalid
        """
        # Validate confirmation code
        if confirmation_code != self.CONFIRMATION_CODE:
            logger.warning(f"Failed reset attempt with invalid code: {confirmation_code}")
            raise ValueError(f"Invalid confirmation code. Must be exactly: {self.CONFIRMATION_CODE}")

        # Log the reset operation
        logger.info(f"Database reset initiated by {user_info} at {datetime.utcnow()}")

        try:
            # Get table counts before deletion for audit
            counts_before = self._get_table_counts()
            logger.info(f"Table counts before reset: {counts_before}")

            # Perform atomic deletion using raw SQL for better control
            # Order matters due to foreign key constraints
            # Clear dependent tables first
            self.db.execute(text("DELETE FROM price_history"))
            self.db.execute(text("DELETE FROM portfolio_snapshots"))
            self.db.execute(text("DELETE FROM positions"))
            self.db.execute(text("DELETE FROM transactions"))

            # Reset sequences for primary keys
            self.db.execute(text("ALTER SEQUENCE IF EXISTS transactions_id_seq RESTART WITH 1"))
            self.db.execute(text("ALTER SEQUENCE IF EXISTS positions_id_seq RESTART WITH 1"))
            self.db.execute(text("ALTER SEQUENCE IF EXISTS price_history_id_seq RESTART WITH 1"))
            self.db.execute(text("ALTER SEQUENCE IF EXISTS portfolio_snapshots_id_seq RESTART WITH 1"))

            # Commit the transaction
            self.db.commit()

            # Verify deletion
            counts_after = self._get_table_counts()
            logger.info(f"Table counts after reset: {counts_after}")

            # Check all counts are zero
            if all(count == 0 for count in counts_after.values()):
                logger.info("Database reset completed successfully")
                return {
                    "status": "success",
                    "message": "Database reset complete. All transactions and related data have been deleted.",
                    "deleted_records": counts_before,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Database reset incomplete. Remaining records: {counts_after}")
                raise Exception("Database reset failed - some records remain")

        except Exception as e:
            logger.error(f"Database reset failed: {str(e)}")
            self.db.rollback()
            raise Exception(f"Database reset failed: {str(e)}")

    def _get_table_counts(self) -> Dict[str, int]:
        """Get record counts for all transaction-related tables"""
        counts = {}

        try:
            # Get counts for each table
            result = self.db.execute(text("SELECT COUNT(*) FROM transactions")).scalar()
            counts["transactions"] = result or 0

            result = self.db.execute(text("SELECT COUNT(*) FROM positions")).scalar()
            counts["positions"] = result or 0

            result = self.db.execute(text("SELECT COUNT(*) FROM price_history")).scalar()
            counts["price_history"] = result or 0

            result = self.db.execute(text("SELECT COUNT(*) FROM portfolio_snapshots")).scalar()
            counts["portfolio_snapshots"] = result or 0

        except Exception as e:
            logger.warning(f"Error getting table counts: {e}")
            # Return zeros if tables don't exist yet
            counts = {
                "transactions": 0,
                "positions": 0,
                "price_history": 0,
                "portfolio_snapshots": 0
            }

        return counts

    def get_database_stats(self) -> Dict:
        """Get current database statistics without modifying data"""
        try:
            counts = self._get_table_counts()

            # Get additional statistics
            stats = {
                "table_counts": counts,
                "total_records": sum(counts.values()),
                "database_ready": all(table in counts for table in
                                     ["transactions", "positions", "price_history", "portfolio_snapshots"])
            }

            # Get date range of transactions if any exist
            if counts.get("transactions", 0) > 0:
                result = self.db.execute(text("""
                    SELECT MIN(transaction_date) as earliest, MAX(transaction_date) as latest
                    FROM transactions
                """)).first()

                if result and result.earliest and result.latest:
                    stats["transaction_date_range"] = {
                        "earliest": result.earliest.isoformat() if hasattr(result.earliest, 'isoformat') else str(result.earliest),
                        "latest": result.latest.isoformat() if hasattr(result.latest, 'isoformat') else str(result.latest)
                    }

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "error": str(e),
                "table_counts": {},
                "total_records": 0,
                "database_ready": False
            }

    def get_detailed_stats(self) -> Dict:
        """Get detailed database statistics including breakdowns by type"""
        try:
            basic_stats = self.get_database_stats()

            # Initialize detailed stats structure
            detailed_stats = {
                "transactions": {
                    "total": basic_stats["table_counts"].get("transactions", 0),
                    "byAssetType": {},
                    "byTransactionType": {},
                    "dateRange": {}
                },
                "symbols": {
                    "total": 0,
                    "topSymbols": []
                },
                "database": {
                    "tablesCount": basic_stats["table_counts"],
                    "totalRecords": basic_stats["total_records"],
                    "isHealthy": basic_stats["database_ready"],
                    "lastImport": None
                }
            }

            # Only query if we have transactions
            if basic_stats["table_counts"].get("transactions", 0) > 0:
                # Get breakdown by asset type
                result = self.db.execute(text("""
                    SELECT asset_type, COUNT(*) as count
                    FROM transactions
                    GROUP BY asset_type
                """))
                for row in result:
                    detailed_stats["transactions"]["byAssetType"][row.asset_type] = row.count

                # Get breakdown by transaction type
                result = self.db.execute(text("""
                    SELECT transaction_type, COUNT(*) as count
                    FROM transactions
                    GROUP BY transaction_type
                """))
                for row in result:
                    detailed_stats["transactions"]["byTransactionType"][row.transaction_type] = row.count

                # Get date range
                result = self.db.execute(text("""
                    SELECT MIN(transaction_date) as earliest,
                           MAX(transaction_date) as latest
                    FROM transactions
                """)).first()
                if result and result.earliest and result.latest:
                    detailed_stats["transactions"]["dateRange"] = {
                        "earliest": result.earliest.isoformat() if hasattr(result.earliest, 'isoformat') else str(result.earliest),
                        "latest": result.latest.isoformat() if hasattr(result.latest, 'isoformat') else str(result.latest)
                    }

                # Get unique symbols count
                result = self.db.execute(text("""
                    SELECT COUNT(DISTINCT symbol) as count
                    FROM transactions
                """)).scalar()
                detailed_stats["symbols"]["total"] = result or 0

                # Get top symbols by transaction count
                result = self.db.execute(text("""
                    SELECT symbol, COUNT(*) as count
                    FROM transactions
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT 10
                """))
                detailed_stats["symbols"]["topSymbols"] = [
                    {"symbol": row.symbol, "count": row.count}
                    for row in result
                ]

                # Get last import timestamp
                result = self.db.execute(text("""
                    SELECT MAX(import_timestamp) as last_import
                    FROM transactions
                """)).scalar()
                if result:
                    detailed_stats["database"]["lastImport"] = result.isoformat() if hasattr(result, 'isoformat') else str(result)

            return detailed_stats

        except Exception as e:
            logger.error(f"Error getting detailed database stats: {e}")
            return {
                "error": str(e),
                "transactions": {
                    "total": 0,
                    "byAssetType": {},
                    "byTransactionType": {},
                    "dateRange": {}
                },
                "symbols": {
                    "total": 0,
                    "topSymbols": []
                },
                "database": {
                    "tablesCount": {},
                    "totalRecords": 0,
                    "isHealthy": False,
                    "lastImport": None
                }
            }