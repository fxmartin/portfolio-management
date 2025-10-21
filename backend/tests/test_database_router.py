# ABOUTME: Tests for database router API endpoints
# ABOUTME: Verifies reset endpoint, stats endpoint, and health check

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app
from database_reset_service import DatabaseResetService
from database import get_db

client = TestClient(app)


class TestDatabaseRouter:
    """Test suite for database management API endpoints"""

    @patch('database_router.get_db')
    @patch('database_router.DatabaseResetService')
    def test_reset_endpoint_with_valid_confirmation(self, mock_service_class, mock_get_db):
        """Test /api/database/reset with valid confirmation code"""
        # Arrange
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.reset_database.return_value = {
            "status": "success",
            "message": "Database reset complete",
            "deleted_records": {"transactions": 100},
            "timestamp": "2024-10-21T12:00:00"
        }
        mock_service_class.return_value = mock_service_instance

        # Act
        response = client.post(
            "/api/database/reset",
            json={"confirmation": "DELETE_ALL_TRANSACTIONS"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Database reset complete" in data["message"]
        mock_service_instance.reset_database.assert_called_once_with(
            confirmation_code="DELETE_ALL_TRANSACTIONS",
            user_info="API User"
        )

    @patch('database_router.get_db')
    @patch('database_router.DatabaseResetService')
    def test_reset_endpoint_with_invalid_confirmation(self, mock_service_class, mock_get_db):
        """Test /api/database/reset with invalid confirmation code"""
        # Arrange
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.reset_database.side_effect = ValueError("Invalid confirmation code")
        mock_service_class.return_value = mock_service_instance

        # Act
        response = client.post(
            "/api/database/reset",
            json={"confirmation": "WRONG_CODE"}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid confirmation code" in data["detail"]

    @patch('database_router.get_db')
    @patch('database_router.DatabaseResetService')
    def test_reset_endpoint_handles_database_error(self, mock_service_class, mock_get_db):
        """Test /api/database/reset handles database errors"""
        # Arrange
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.reset_database.side_effect = Exception("Database connection failed")
        mock_service_class.return_value = mock_service_instance

        # Act
        response = client.post(
            "/api/database/reset",
            json={"confirmation": "DELETE_ALL_TRANSACTIONS"}
        )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Database reset failed" in data["detail"]

    def test_reset_endpoint_requires_confirmation_field(self):
        """Test /api/database/reset requires confirmation field"""
        # Act
        response = client.post(
            "/api/database/reset",
            json={}  # Missing confirmation field
        )

        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "field required" in str(data).lower()

    @patch('database_router.get_db')
    @patch('database_router.DatabaseResetService')
    def test_stats_endpoint_returns_database_statistics(self, mock_service_class, mock_get_db):
        """Test /api/database/stats returns current statistics"""
        # Arrange
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_database_stats.return_value = {
            "table_counts": {
                "transactions": 150,
                "positions": 25,
                "price_history": 500,
                "portfolio_snapshots": 60
            },
            "total_records": 735,
            "database_ready": True,
            "transaction_date_range": {
                "earliest": "2024-01-01T00:00:00",
                "latest": "2024-10-21T00:00:00"
            }
        }
        mock_service_class.return_value = mock_service_instance

        # Act
        response = client.get("/api/database/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 735
        assert data["table_counts"]["transactions"] == 150
        assert data["database_ready"] == True
        assert "transaction_date_range" in data

    @patch('database_router.get_db')
    @patch('database_router.DatabaseResetService')
    def test_stats_endpoint_handles_empty_database(self, mock_service_class, mock_get_db):
        """Test /api/database/stats with empty database"""
        # Arrange
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_database_stats.return_value = {
            "table_counts": {
                "transactions": 0,
                "positions": 0,
                "price_history": 0,
                "portfolio_snapshots": 0
            },
            "total_records": 0,
            "database_ready": True
        }
        mock_service_class.return_value = mock_service_instance

        # Act
        response = client.get("/api/database/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 0
        assert all(count == 0 for count in data["table_counts"].values())

    @patch('database_router.get_db')
    @patch('database_router.DatabaseResetService')
    def test_stats_endpoint_handles_errors(self, mock_service_class, mock_get_db):
        """Test /api/database/stats handles errors gracefully"""
        # Arrange
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        mock_service_instance = Mock()
        mock_service_instance.get_database_stats.side_effect = Exception("Database error")
        mock_service_class.return_value = mock_service_instance

        # Act
        response = client.get("/api/database/stats")

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get database statistics" in data["detail"]

    def test_health_endpoint_when_database_is_healthy(self):
        """Test /api/database/health when database is healthy"""
        # Arrange
        mock_db = Mock()
        mock_db.execute.return_value = Mock()  # Successful query

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        with patch('database_router.DatabaseResetService') as mock_service_class:
            mock_service_instance = Mock()
            mock_service_instance.get_database_stats.return_value = {
                "database_ready": True
            }
            mock_service_class.return_value = mock_service_instance

            # Act
            response = client.get("/api/database/health")

        # Clean up override
        app.dependency_overrides.clear()

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_ready"] == True
        assert data["tables_exist"] == True

    def test_health_endpoint_when_database_is_unhealthy(self):
        """Test /api/database/health when database is unhealthy"""
        # Arrange
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Connection refused")

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        # Act
        response = client.get("/api/database/health")

        # Clean up override
        app.dependency_overrides.clear()

        # Assert
        assert response.status_code == 200  # Still returns 200 but with unhealthy status
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database_ready"] == False
        assert "Connection refused" in data["error"]

    def test_health_endpoint_when_tables_dont_exist(self):
        """Test /api/database/health when tables don't exist"""
        # Arrange
        mock_db = Mock()
        mock_db.execute.return_value = Mock()  # Connection works

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        with patch('database_router.DatabaseResetService') as mock_service_class:
            mock_service_instance = Mock()
            mock_service_instance.get_database_stats.return_value = {
                "database_ready": False  # Tables not created
            }
            mock_service_class.return_value = mock_service_instance

            # Act
            response = client.get("/api/database/health")

        # Clean up override
        app.dependency_overrides.clear()

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"  # Connection works
        assert data["database_ready"] == False  # But tables don't exist
        assert data["tables_exist"] == False