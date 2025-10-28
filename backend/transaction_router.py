# ABOUTME: FastAPI router for transaction CRUD operations
# ABOUTME: Handles manual transaction management with validation and audit trail

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from database import get_async_db
from models import Transaction, TransactionAudit, TransactionType, AssetType
from transaction_validator import TransactionValidator, ValidationResult
from portfolio_service import PortfolioService


router = APIRouter(prefix="/api/transactions", tags=["transactions"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TransactionCreate(BaseModel):
    """Request model for creating a transaction"""
    transaction_date: datetime
    asset_type: AssetType
    transaction_type: TransactionType
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: Decimal = Field(..., gt=0)
    price_per_unit: Optional[Decimal] = Field(None, ge=0)
    fee: Optional[Decimal] = Field(default=0, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('currency')
    def currency_uppercase(cls, v):
        return v.upper() if v else v


class TransactionUpdate(BaseModel):
    """Request model for updating a transaction"""
    transaction_date: Optional[datetime] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    price_per_unit: Optional[Decimal] = Field(None, ge=0)
    fee: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    notes: Optional[str] = Field(None, max_length=500)
    change_reason: Optional[str] = Field(None, max_length=500)

    @validator('currency')
    def currency_uppercase(cls, v):
        return v.upper() if v else v


class TransactionResponse(BaseModel):
    """Response model for a transaction"""
    id: int
    transaction_date: datetime
    asset_type: AssetType
    transaction_type: TransactionType
    symbol: str
    quantity: Decimal
    price_per_unit: Optional[Decimal]
    total_amount: Optional[Decimal]
    fee: Decimal
    currency: str
    notes: Optional[str]
    source: str
    source_file: Optional[str]
    deleted_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationResponse(BaseModel):
    """Response model for validation results"""
    valid: bool
    messages: List[Dict[str, Any]]


class DeletionImpact(BaseModel):
    """Impact analysis for transaction deletion"""
    transaction_id: int
    affected_positions: List[str]
    warnings: List[str]
    can_delete: bool


class BulkCreateRequest(BaseModel):
    """Request model for bulk transaction creation"""
    transactions: List[TransactionCreate]


class BulkCreateResponse(BaseModel):
    """Response model for bulk creation"""
    total: int
    successful: int
    failed: int
    created_ids: List[int]
    errors: List[Dict[str, Any]]


class TransactionAuditResponse(BaseModel):
    """Response model for audit trail entry"""
    id: int
    transaction_id: int
    changed_at: datetime
    changed_by: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    change_reason: Optional[str]
    action: str

    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

async def log_audit(
    db: AsyncSession,
    transaction_id: int,
    action: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    change_reason: Optional[str] = None,
    changed_by: str = "system"
):
    """Log transaction change to audit trail"""
    audit_entry = TransactionAudit(
        transaction_id=transaction_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        change_reason=change_reason,
        changed_by=changed_by,
        changed_at=datetime.now()  # Timezone-naive
    )
    db.add(audit_entry)
    await db.commit()


def transaction_to_dict(txn: Transaction) -> Dict[str, Any]:
    """Convert transaction to dictionary for audit logging"""
    return {
        "transaction_date": txn.transaction_date.isoformat() if txn.transaction_date else None,
        "asset_type": txn.asset_type.value if txn.asset_type else None,
        "transaction_type": txn.transaction_type.value if txn.transaction_type else None,
        "symbol": txn.symbol,
        "quantity": str(txn.quantity) if txn.quantity else None,
        "price_per_unit": str(txn.price_per_unit) if txn.price_per_unit else None,
        "fee": str(txn.fee) if txn.fee else None,
        "currency": txn.currency,
        "notes": txn.notes
    }


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new manual transaction"""

    # Validate transaction
    validator = TransactionValidator(db)
    validation = await validator.validate_create(
        transaction_date=data.transaction_date,
        asset_type=data.asset_type,
        transaction_type=data.transaction_type,
        symbol=data.symbol,
        quantity=data.quantity,
        price_per_unit=data.price_per_unit,
        fee=data.fee,
        currency=data.currency,
        notes=data.notes
    )

    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Validation failed",
                "errors": [msg.dict() for msg in validation.messages if msg.level.value == "error"]
            }
        )

    # Calculate total amount
    total_amount = None
    if data.price_per_unit and data.quantity:
        total_amount = data.price_per_unit * data.quantity

    # Make transaction_date timezone-naive for database storage
    transaction_date = data.transaction_date
    if transaction_date.tzinfo is not None:
        transaction_date = transaction_date.replace(tzinfo=None)

    # Create transaction
    transaction = Transaction(
        transaction_date=transaction_date,
        asset_type=data.asset_type,
        transaction_type=data.transaction_type,
        symbol=data.symbol,
        quantity=data.quantity,
        price_per_unit=data.price_per_unit,
        total_amount=total_amount,
        fee=data.fee or Decimal('0'),
        currency=data.currency,
        notes=data.notes,
        source="MANUAL",
        created_at=datetime.now()  # Timezone-naive for database
    )

    db.add(transaction)
    await db.flush()  # Flush to get the ID

    # Log audit trail
    await log_audit(
        db=db,
        transaction_id=transaction.id,
        action="CREATE",
        new_values=transaction_to_dict(transaction),
        changed_by="user"
    )

    await db.commit()
    await db.refresh(transaction)

    # Recalculate positions
    portfolio_service = PortfolioService(db)
    await portfolio_service.recalculate_all_positions()

    return transaction


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    source: Optional[str] = Query(None, description="Filter by source (CSV or MANUAL)"),
    include_deleted: bool = Query(False, description="Include soft-deleted transactions"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """List transactions with optional filters"""

    stmt = select(Transaction)

    # Apply filters
    if symbol:
        stmt = stmt.where(Transaction.symbol.ilike(f"%{symbol}%"))
    if asset_type:
        stmt = stmt.where(Transaction.asset_type == asset_type)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if source:
        stmt = stmt.where(Transaction.source == source.upper())
    if not include_deleted:
        stmt = stmt.where(Transaction.deleted_at.is_(None))

    # Order by date descending (newest first)
    stmt = stmt.order_by(desc(Transaction.transaction_date))

    # Pagination
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a single transaction by ID"""

    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update an existing transaction"""

    # Get existing transaction
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.deleted_at:
        raise HTTPException(status_code=400, detail="Cannot update deleted transaction")

    # Store old values for audit
    old_values = transaction_to_dict(transaction)

    # Prepare update values
    update_values = data.dict(exclude_unset=True, exclude={'change_reason'})

    # Validate update
    if update_values:
        validator = TransactionValidator(db)
        validation = await validator.validate_update(transaction_id, update_values)

        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Validation failed",
                    "errors": [msg.dict() for msg in validation.messages if msg.level.value == "error"]
                }
            )

    # Apply updates
    for field, value in update_values.items():
        setattr(transaction, field, value)

    # Recalculate total amount if price or quantity changed
    if 'price_per_unit' in update_values or 'quantity' in update_values:
        if transaction.price_per_unit and transaction.quantity:
            transaction.total_amount = transaction.price_per_unit * transaction.quantity

    await db.flush()

    # Log audit trail
    await log_audit(
        db=db,
        transaction_id=transaction_id,
        action="UPDATE",
        old_values=old_values,
        new_values=transaction_to_dict(transaction),
        change_reason=data.change_reason,
        changed_by="user"
    )

    await db.commit()
    await db.refresh(transaction)

    # Recalculate positions
    portfolio_service = PortfolioService(db)
    await portfolio_service.recalculate_all_positions()

    return transaction


@router.delete("/{transaction_id}", response_model=Dict[str, Any])
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Soft delete a transaction"""

    # Get transaction
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.deleted_at:
        raise HTTPException(status_code=400, detail="Transaction already deleted")

    # Validate deletion
    validator = TransactionValidator(db)
    validation = await validator.validate_delete(transaction_id)

    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot delete transaction",
                "errors": [msg.dict() for msg in validation.messages if msg.level.value == "error"]
            }
        )

    # Soft delete
    old_values = transaction_to_dict(transaction)
    transaction.deleted_at = datetime.now()  # Timezone-naive

    # Log audit trail
    await log_audit(
        db=db,
        transaction_id=transaction_id,
        action="DELETE",
        old_values=old_values,
        changed_by="user"
    )

    await db.commit()

    # Recalculate positions
    portfolio_service = PortfolioService(db)
    await portfolio_service.recalculate_all_positions()

    return {
        "message": "Transaction deleted successfully",
        "transaction_id": transaction_id,
        "deleted_at": transaction.deleted_at,
        "can_undo": True,
        "undo_deadline": "24 hours from deletion"
    }


@router.post("/{transaction_id}/restore", response_model=TransactionResponse)
async def restore_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Restore a soft-deleted transaction"""

    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if not transaction.deleted_at:
        raise HTTPException(status_code=400, detail="Transaction is not deleted")

    # Restore
    transaction.deleted_at = None

    # Log audit trail
    await log_audit(
        db=db,
        transaction_id=transaction_id,
        action="RESTORE",
        new_values=transaction_to_dict(transaction),
        changed_by="user"
    )

    await db.commit()
    await db.refresh(transaction)

    # Recalculate positions
    portfolio_service = PortfolioService(db)
    await portfolio_service.recalculate_all_positions()

    return transaction


@router.get("/{transaction_id}/history", response_model=List[TransactionAuditResponse])
async def get_transaction_history(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get audit history for a transaction"""

    # Verify transaction exists
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Get audit trail
    stmt = select(TransactionAudit).where(
        TransactionAudit.transaction_id == transaction_id
    ).order_by(desc(TransactionAudit.changed_at))

    result = await db.execute(stmt)
    audit_entries = result.scalars().all()

    return audit_entries


@router.post("/bulk", response_model=BulkCreateResponse)
async def bulk_create_transactions(
    request: BulkCreateRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Create multiple transactions at once"""

    total = len(request.transactions)
    successful = 0
    failed = 0
    created_ids = []
    errors = []

    validator = TransactionValidator(db)

    for idx, txn_data in enumerate(request.transactions):
        try:
            # Validate
            validation = await validator.validate_create(
                transaction_date=txn_data.transaction_date,
                asset_type=txn_data.asset_type,
                transaction_type=txn_data.transaction_type,
                symbol=txn_data.symbol,
                quantity=txn_data.quantity,
                price_per_unit=txn_data.price_per_unit,
                fee=txn_data.fee,
                currency=txn_data.currency,
                notes=txn_data.notes
            )

            if not validation.valid:
                failed += 1
                errors.append({
                    "index": idx,
                    "symbol": txn_data.symbol,
                    "errors": [msg.dict() for msg in validation.messages if msg.level.value == "error"]
                })
                continue

            # Create transaction
            total_amount = None
            if txn_data.price_per_unit and txn_data.quantity:
                total_amount = txn_data.price_per_unit * txn_data.quantity

            # Make timezone-naive
            transaction_date = txn_data.transaction_date
            if transaction_date.tzinfo is not None:
                transaction_date = transaction_date.replace(tzinfo=None)

            transaction = Transaction(
                transaction_date=transaction_date,
                asset_type=txn_data.asset_type,
                transaction_type=txn_data.transaction_type,
                symbol=txn_data.symbol,
                quantity=txn_data.quantity,
                price_per_unit=txn_data.price_per_unit,
                total_amount=total_amount,
                fee=txn_data.fee or Decimal('0'),
                currency=txn_data.currency,
                notes=txn_data.notes,
                source="MANUAL",
                created_at=datetime.now()  # Timezone-naive
            )

            db.add(transaction)
            await db.flush()

            # Log audit
            await log_audit(
                db=db,
                transaction_id=transaction.id,
                action="CREATE",
                new_values=transaction_to_dict(transaction),
                changed_by="user"
            )

            created_ids.append(transaction.id)
            successful += 1

        except Exception as e:
            failed += 1
            errors.append({
                "index": idx,
                "symbol": txn_data.symbol,
                "error": str(e)
            })

    await db.commit()

    # Recalculate positions once after all transactions
    if successful > 0:
        portfolio_service = PortfolioService(db)
        await portfolio_service.recalculate_all_positions()

    return BulkCreateResponse(
        total=total,
        successful=successful,
        failed=failed,
        created_ids=created_ids,
        errors=errors
    )


@router.post("/validate", response_model=ValidationResponse)
async def validate_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Validate a transaction without creating it"""

    validator = TransactionValidator(db)
    validation = await validator.validate_create(
        transaction_date=data.transaction_date,
        asset_type=data.asset_type,
        transaction_type=data.transaction_type,
        symbol=data.symbol,
        quantity=data.quantity,
        price_per_unit=data.price_per_unit,
        fee=data.fee,
        currency=data.currency,
        notes=data.notes
    )

    return ValidationResponse(
        valid=validation.valid,
        messages=[msg.dict() for msg in validation.messages]
    )


@router.get("/duplicates", response_model=List[List[TransactionResponse]])
async def find_duplicates(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of groups to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Find potential duplicate transactions"""

    validator = TransactionValidator(db)
    duplicate_groups = await validator.detect_duplicates(symbol=symbol, limit=limit)

    return duplicate_groups


@router.delete("/{transaction_id}/impact", response_model=DeletionImpact)
async def analyze_deletion_impact(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Analyze the impact of deleting a transaction without actually deleting it"""

    # Get transaction
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Validate deletion
    validator = TransactionValidator(db)
    validation = await validator.validate_delete(transaction_id)

    warnings = [msg.message for msg in validation.messages]

    return DeletionImpact(
        transaction_id=transaction_id,
        affected_positions=[transaction.symbol],
        warnings=warnings,
        can_delete=validation.valid
    )
