# ABOUTME: Tests for database reset functionality
# ABOUTME: Verifies safety checks, atomic deletion, and audit logging

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import text
from database_reset_service import DatabaseResetService
from datetime import datetime


class TestDatabaseResetService:
    """Test suite for DatabaseResetService"""

    def test_reset_requires_correct_confirmation_code(self):
        """Test that reset requires exact confirmation code"""
        # Arrange
        mock_db = Mock(spec=Session)
        service = DatabaseResetService(mock_db)

        # Act & Assert - Test with wrong confirmation
        with pytest.raises(ValueError, match="Invalid confirmation code"):
            service.reset_database("WRONG_CODE")

        # Verify no database operations occurred
        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_reset_with_valid_confirmation_executes_deletion(self):
        """Test that reset executes with valid confirmation"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.begin.return_value.__enter__ = Mock()
        mock_db.begin.return_value.__exit__ = Mock()

        service = DatabaseResetService(mock_db)

        # Act
        with patch.object(service, '_get_table_counts') as mock_counts:
            mock_counts.side_effect = [
                {"transactions": 100, "positions": 50, "price_history": 200, "portfolio_snapshots": 30},  # Before
                {"transactions": 0, "positions": 0, "price_history": 0, "portfolio_snapshots": 0}  # After
            ]
            result = service.reset_database("DELETE_ALL_TRANSACTIONS", "test_user")

        # Assert
        assert result["status"] == "success"
        assert "Database reset complete" in result["message"]
        assert result["deleted_records"]["transactions"] == 100
        mock_db.commit.assert_called()

    def test_reset_deletes_tables_in_correct_order(self):
        """Test that tables are deleted in order respecting foreign keys"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.begin.return_value.__enter__ = Mock()
        mock_db.begin.return_value.__exit__ = Mock()

        executed_queries = []

        def track_query(query):
            executed_queries.append(str(query))
            return Mock(scalar=Mock(return_value=0))

        mock_db.execute.side_effect = track_query
        service = DatabaseResetService(mock_db)

        # Act
        with patch.object(service, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {"transactions": 0, "positions": 0, "price_history": 0, "portfolio_snapshots": 0}
            service.reset_database("DELETE_ALL_TRANSACTIONS")

        # Assert - Check deletion order (dependent tables first)
        delete_queries = [q for q in executed_queries if 'DELETE FROM' in q]
        assert len(delete_queries) == 4
        assert 'DELETE FROM price_history' in delete_queries[0]
        assert 'DELETE FROM portfolio_snapshots' in delete_queries[1]
        assert 'DELETE FROM positions' in delete_queries[2]
        assert 'DELETE FROM transactions' in delete_queries[3]

    def test_reset_resets_sequences(self):
        """Test that primary key sequences are reset"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.begin.return_value.__enter__ = Mock()
        mock_db.begin.return_value.__exit__ = Mock()

        executed_queries = []

        def track_query(query):
            executed_queries.append(str(query))
            return Mock(scalar=Mock(return_value=0))

        mock_db.execute.side_effect = track_query
        service = DatabaseResetService(mock_db)

        # Act
        with patch.object(service, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {"transactions": 0, "positions": 0, "price_history": 0, "portfolio_snapshots": 0}
            service.reset_database("DELETE_ALL_TRANSACTIONS")

        # Assert - Check sequence reset commands
        sequence_queries = [q for q in executed_queries if 'ALTER SEQUENCE' in q]
        assert len(sequence_queries) == 4
        assert any('transactions_id_seq' in q for q in sequence_queries)
        assert any('positions_id_seq' in q for q in sequence_queries)
        assert any('price_history_id_seq' in q for q in sequence_queries)
        assert any('portfolio_snapshots_id_seq' in q for q in sequence_queries)

    def test_reset_rolls_back_on_error(self):
        """Test that reset rolls back on database error"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.begin.return_value.__enter__ = Mock()
        mock_db.begin.return_value.__exit__ = Mock(side_effect=Exception("Database error"))

        service = DatabaseResetService(mock_db)

        # Act & Assert
        with patch.object(service, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {"transactions": 10, "positions": 5, "price_history": 20, "portfolio_snapshots": 3}

            with pytest.raises(Exception, match="Database reset failed"):
                service.reset_database("DELETE_ALL_TRANSACTIONS")

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    def test_get_table_counts_returns_correct_counts(self):
        """Test that _get_table_counts returns accurate record counts"""
        # Arrange
        mock_db = Mock(spec=Session)

        # Mock scalar results for each table count
        mock_db.execute.return_value.scalar.side_effect = [100, 50, 200, 30]

        service = DatabaseResetService(mock_db)

        # Act
        counts = service._get_table_counts()

        # Assert
        assert counts["transactions"] == 100
        assert counts["positions"] == 50
        assert counts["price_history"] == 200
        assert counts["portfolio_snapshots"] == 30

    def test_get_table_counts_handles_missing_tables(self):
        """Test that _get_table_counts handles missing tables gracefully"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.execute.side_effect = Exception("Table does not exist")

        service = DatabaseResetService(mock_db)

        # Act
        counts = service._get_table_counts()

        # Assert - Should return zeros for missing tables
        assert counts["transactions"] == 0
        assert counts["positions"] == 0
        assert counts["price_history"] == 0
        assert counts["portfolio_snapshots"] == 0

    def test_get_database_stats_returns_complete_info(self):
        """Test that get_database_stats returns comprehensive database information"""
        # Arrange
        mock_db = Mock(spec=Session)

        # Mock table counts
        with patch.object(DatabaseResetService, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {
                "transactions": 150,
                "positions": 25,
                "price_history": 500,
                "portfolio_snapshots": 60
            }

            # Mock date range query
            mock_date_result = Mock()
            mock_date_result.earliest = datetime(2024, 1, 1)
            mock_date_result.latest = datetime(2024, 10, 21)
            mock_db.execute.return_value.first.return_value = mock_date_result

            service = DatabaseResetService(mock_db)

            # Act
            stats = service.get_database_stats()

        # Assert
        assert stats["table_counts"]["transactions"] == 150
        assert stats["total_records"] == 735  # 150 + 25 + 500 + 60
        assert stats["database_ready"] == True
        assert "transaction_date_range" in stats
        assert stats["transaction_date_range"]["earliest"] == "2024-01-01T00:00:00"
        assert stats["transaction_date_range"]["latest"] == "2024-10-21T00:00:00"

    def test_get_database_stats_handles_empty_database(self):
        """Test that get_database_stats handles empty database correctly"""
        # Arrange
        mock_db = Mock(spec=Session)

        with patch.object(DatabaseResetService, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {
                "transactions": 0,
                "positions": 0,
                "price_history": 0,
                "portfolio_snapshots": 0
            }

            service = DatabaseResetService(mock_db)

            # Act
            stats = service.get_database_stats()

        # Assert
        assert stats["total_records"] == 0
        assert stats["database_ready"] == True
        assert "transaction_date_range" not in stats  # No date range for empty DB

    def test_get_database_stats_handles_errors(self):
        """Test that get_database_stats handles errors gracefully"""
        # Arrange
        mock_db = Mock(spec=Session)

        with patch.object(DatabaseResetService, '_get_table_counts') as mock_counts:
            mock_counts.side_effect = Exception("Database connection failed")

            service = DatabaseResetService(mock_db)

            # Act
            stats = service.get_database_stats()

        # Assert
        assert "error" in stats
        assert stats["total_records"] == 0
        assert stats["database_ready"] == False

    def test_reset_includes_audit_information(self):
        """Test that reset response includes audit information"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.begin.return_value.__enter__ = Mock()
        mock_db.begin.return_value.__exit__ = Mock()

        service = DatabaseResetService(mock_db)

        # Act
        with patch.object(service, '_get_table_counts') as mock_counts:
            mock_counts.side_effect = [
                {"transactions": 50, "positions": 10, "price_history": 100, "portfolio_snapshots": 5},  # Before
                {"transactions": 0, "positions": 0, "price_history": 0, "portfolio_snapshots": 0}  # After
            ]
            result = service.reset_database("DELETE_ALL_TRANSACTIONS", "test_admin")

        # Assert
        assert result["status"] == "success"
        assert "deleted_records" in result
        assert result["deleted_records"]["transactions"] == 50
        assert "timestamp" in result
        # Verify timestamp is in ISO format
        datetime.fromisoformat(result["timestamp"])

    @patch('database_reset_service.logger')
    def test_reset_logs_operations(self, mock_logger):
        """Test that reset operations are properly logged"""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.execute.return_value.scalar.return_value = 0
        mock_db.begin.return_value.__enter__ = Mock()
        mock_db.begin.return_value.__exit__ = Mock()

        service = DatabaseResetService(mock_db)

        # Act
        with patch.object(service, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {"transactions": 0, "positions": 0, "price_history": 0, "portfolio_snapshots": 0}
            service.reset_database("DELETE_ALL_TRANSACTIONS", "test_user")

        # Assert - Check logging calls
        assert mock_logger.info.call_count >= 3
        # Check that user info is logged
        assert any("test_user" in str(call) for call in mock_logger.info.call_args_list)
        # Check that completion is logged
        assert any("completed successfully" in str(call) for call in mock_logger.info.call_args_list)