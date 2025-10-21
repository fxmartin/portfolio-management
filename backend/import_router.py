# ABOUTME: FastAPI router for handling CSV file imports
# ABOUTME: Supports multi-file upload with automatic format detection

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import asyncio
try:
    from .csv_parser import CSVDetector, FileType, get_parser
except ImportError:
    from csv_parser import CSVDetector, FileType, get_parser

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/upload")
async def upload_csv_files(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple CSV files

    Accepts:
    - Revolut metals account statements (account-statement_*.csv)
    - Revolut stocks exports (UUID.csv)
    - Koinly crypto exports (Koinly*.csv)

    Args:
        files: List of uploaded CSV files

    Returns:
        Processing results for each file
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

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

                # TODO: Store transactions in database

                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "file_type": file_type.value,
                    "errors": [],
                    "transactions_count": len(transactions),
                    "message": f"Successfully processed {len(transactions)} transactions"
                })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "file_type": file_type.value,
                    "errors": [str(e)],
                    "transactions_count": 0
                })
        else:
            results.append({
                "filename": file.filename,
                "status": "error",
                "file_type": file_type.value,
                "errors": ["No parser available for this file type"],
                "transactions_count": 0
            })

    # Calculate summary
    total_files = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total_files - successful
    total_transactions = sum(r["transactions_count"] for r in results)

    return {
        "summary": {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "total_transactions": total_transactions
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