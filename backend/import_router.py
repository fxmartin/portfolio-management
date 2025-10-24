# ABOUTME: FastAPI router for handling CSV file imports
# ABOUTME: Supports multi-file upload with automatic format detection

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
try:
    from .csv_parser import CSVDetector, FileType, get_parser
    from .database import get_async_db
    from .transaction_service import TransactionService, DuplicateHandler
    from .portfolio_service import PortfolioService
except ImportError:
    from csv_parser import CSVDetector, FileType, get_parser
    from database import get_async_db
    from transaction_service import TransactionService, DuplicateHandler
    from portfolio_service import PortfolioService

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/upload")
async def upload_csv_files(
    files: List[UploadFile] = File(...),
    allow_duplicates: bool = Query(False, description="Allow duplicate transactions to be skipped"),
    duplicate_strategy: str = Query("skip", description="How to handle duplicates: skip, update, or force"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload and process multiple CSV files

    Accepts:
    - Revolut metals account statements (account-statement_*.csv)
    - Revolut stocks exports (UUID.csv)
    - Koinly crypto exports (Koinly*.csv)

    Args:
        files: List of uploaded CSV files
        allow_duplicates: If True, skip duplicates without error
        duplicate_strategy: How to handle duplicates (skip, update, force)
        db: Database session

    Returns:
        Processing results for each file with database storage status
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if duplicate_strategy not in ["skip", "update", "force"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid duplicate_strategy. Must be 'skip', 'update', or 'force'"
        )

    results = []

    for file in files:
        # Validate each file
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer

        validation = CSVDetector.validate_file(file.filename, file_size)

        if not validation["is_valid"]:
            results.append({
                "filename": file.filename,
                "status": "error",
                "file_type": None,
                "errors": validation["errors"],
                "transactions_count": 0
            })
            continue

        # Process valid file
        file_type = validation["file_type"]
        parser = get_parser(file_type)

        if parser:
            try:
                # Parse the CSV content
                transactions = parser.parse(content)

                # Store transactions in database
                service = TransactionService(db)

                # Check for duplicates first if strategy is not skip
                duplicates = []
                if duplicate_strategy != "skip":
                    duplicates = await service.check_duplicates(transactions)

                # Handle duplicates based on strategy
                if duplicates and duplicate_strategy != "skip":
                    resolved = await DuplicateHandler.resolve_duplicates(
                        db, duplicates, duplicate_strategy
                    )
                    # Update transactions list based on resolution
                    duplicate_tx_ids = {id(dup["transaction"]) for dup in duplicates}
                    transactions = [
                        tx for tx in transactions
                        if id(tx) not in duplicate_tx_ids
                    ]
                    # Add resolved transactions
                    for res in resolved:
                        if res["action"] == "forced":
                            transactions.append(res["transaction"])

                # Store the transactions
                saved, skipped, failed = await service.store_transactions(
                    transactions,
                    file.filename,
                    allow_duplicates=allow_duplicates
                )

                # Calculate detailed statistics
                total_processed = len(saved) + len(skipped) + len(failed)

                results.append({
                    "filename": file.filename,
                    "status": "success" if not failed else "partial",
                    "file_type": file_type.value,
                    "errors": [f["error"] for f in failed],
                    "transactions_count": len(transactions),
                    "saved_count": len(saved),
                    "skipped_count": len(skipped),
                    "failed_count": len(failed),
                    "message": f"Saved {len(saved)} transactions, skipped {len(skipped)} duplicates, {len(failed)} failed",
                    "details": {
                        "saved": [{"id": t.id, "symbol": t.symbol, "date": t.transaction_date.isoformat()}
                                 for t in saved[:5]],  # First 5 for preview
                        "skipped_reasons": [s["reason"] for s in skipped[:5]],
                        "failed_errors": [f["error"] for f in failed[:5]]
                    }
                })
            except Exception as e:
                await db.rollback()
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "file_type": file_type.value,
                    "errors": [str(e)],
                    "transactions_count": 0,
                    "saved_count": 0,
                    "skipped_count": 0,
                    "failed_count": 0
                })
        else:
            results.append({
                "filename": file.filename,
                "status": "error",
                "file_type": file_type.value,
                "errors": ["No parser available for this file type"],
                "transactions_count": 0,
                "saved_count": 0,
                "skipped_count": 0,
                "failed_count": 0
            })

    # Calculate summary
    total_files = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    partial = sum(1 for r in results if r["status"] == "partial")
    failed = sum(1 for r in results if r["status"] == "error")
    total_transactions = sum(r.get("transactions_count", 0) for r in results)
    total_saved = sum(r.get("saved_count", 0) for r in results)
    total_skipped = sum(r.get("skipped_count", 0) for r in results)
    total_failed = sum(r.get("failed_count", 0) for r in results)

    # Recalculate positions if any transactions were saved
    positions_recalculated = 0
    if total_saved > 0:
        try:
            portfolio_service = PortfolioService(db)
            positions = await portfolio_service.recalculate_all_positions()
            positions_recalculated = len(positions)
        except Exception as e:
            print(f"Warning: Failed to recalculate positions after import: {e}")
            # Don't fail the import if position calculation fails

    return {
        "summary": {
            "total_files": total_files,
            "successful": successful,
            "partial": partial,
            "failed": failed,
            "total_transactions": total_transactions,
            "total_saved": total_saved,
            "total_skipped": total_skipped,
            "total_failed": total_failed,
            "duplicate_strategy": duplicate_strategy,
            "positions_recalculated": positions_recalculated
        },
        "files": results
    }

@router.get("/status")
async def get_import_status():
    """Get the current import status"""
    return {
        "status": "ready",
        "supported_formats": [
            {
                "type": "METALS",
                "description": "Revolut metals account statement",
                "pattern": "account-statement_*.csv"
            },
            {
                "type": "STOCKS",
                "description": "Revolut stocks export",
                "pattern": "[UUID].csv"
            },
            {
                "type": "CRYPTO",
                "description": "Koinly crypto transactions",
                "pattern": "*Koinly*.csv"
            }
        ]
    }

@router.get("/summary")
async def get_import_summary(
    source_file: Optional[str] = Query(None, description="Filter by source file"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get summary of imported transactions from database

    Args:
        source_file: Optional filter by source file name
        db: Database session

    Returns:
        Summary statistics of imported transactions
    """
    service = TransactionService(db)
    summary = await service.get_import_summary(source_file)
    return summary

@router.post("/check-duplicates")
async def check_duplicates(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Check for potential duplicate transactions before importing

    Args:
        file: CSV file to check
        db: Database session

    Returns:
        List of potential duplicates found
    """
    # Validate file
    content = await file.read()
    file_size = len(content)

    validation = CSVDetector.validate_file(file.filename, file_size)
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file: {', '.join(validation['errors'])}"
        )

    # Parse file
    file_type = validation["file_type"]
    parser = get_parser(file_type)

    if not parser:
        raise HTTPException(
            status_code=400,
            detail="No parser available for this file type"
        )

    try:
        # Parse transactions
        transactions = parser.parse(content)

        # Check for duplicates
        service = TransactionService(db)
        duplicates = await service.check_duplicates(transactions)

        return {
            "filename": file.filename,
            "file_type": file_type.value,
            "total_transactions": len(transactions),
            "duplicate_count": len(duplicates),
            "duplicates": [
                {
                    "symbol": dup["transaction"]["symbol"],
                    "date": dup["transaction"]["transaction_date"].isoformat(),
                    "quantity": dup["transaction"].get("quantity"),
                    "type": dup["transaction"]["transaction_type"].value,
                    "existing_id": dup["existing_id"],
                    "existing_source": dup["existing_source"]
                }
                for dup in duplicates[:20]  # Limit to first 20 for response size
            ],
            "has_more": len(duplicates) > 20
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking duplicates: {str(e)}"
        )