# ABOUTME: FastAPI router for database management endpoints
# ABOUTME: Provides endpoints for database reset and statistics

from fastapi import APIRouter, HTTPException, Depends, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from database_reset_service import DatabaseResetService
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/database",
    tags=["database"]
)


@router.post("/reset", response_model=Dict)
def reset_database(
    confirmation: str = Body(..., embed=True, description="Confirmation code for reset"),
    db: Session = Depends(get_db)
):
    """
    Reset the database and clear all transactions.

    This is a destructive operation that will permanently delete:
    - All imported transactions
    - All positions
    - All price history
    - All portfolio snapshots

    Requires confirmation code: DELETE_ALL_TRANSACTIONS
    """
    try:
        # Create service instance
        service = DatabaseResetService(db)

        # Perform reset with audit logging
        result = service.reset_database(
            confirmation_code=confirmation,
            user_info="API User"  # In production, this would come from auth
        )

        return result

    except ValueError as e:
        # Invalid confirmation code
        logger.warning(f"Invalid reset confirmation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Other errors
        logger.error(f"Database reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {str(e)}"
        )


@router.get("/stats", response_model=Dict)
def get_database_stats(db: Session = Depends(get_db)):
    """
    Get current database statistics including record counts.

    Returns information about:
    - Number of transactions
    - Number of positions
    - Number of price history records
    - Number of portfolio snapshots
    - Transaction date range (if applicable)
    """
    try:
        service = DatabaseResetService(db)
        stats = service.get_database_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database statistics: {str(e)}"
        )


@router.get("/health", response_model=Dict)
def check_database_health(db: Session = Depends(get_db)):
    """
    Check if database connection is healthy and tables exist.
    """
    try:
        # Try to execute a simple query
        db.execute(text("SELECT 1"))

        # Check if main tables exist
        service = DatabaseResetService(db)
        stats = service.get_database_stats()

        return {
            "status": "healthy",
            "database_ready": stats.get("database_ready", False),
            "tables_exist": stats.get("database_ready", False)
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_ready": False,
            "tables_exist": False
        }