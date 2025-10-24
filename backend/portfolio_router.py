# ABOUTME: API routes for portfolio dashboard and summary endpoints
# ABOUTME: Provides portfolio value, P&L, positions, and cash balance data

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

from database import get_async_db
from portfolio_service import PortfolioService
from models import Transaction, TransactionType, AssetType
from yahoo_finance_service import YahooFinanceService
import redis
import os

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary")
async def get_portfolio_summary(
    session: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Get comprehensive portfolio summary for dashboard.

    Returns:
        Dictionary with:
        - total_value: Total portfolio value in base currency
        - cash_balances: Available cash by currency
        - total_pnl: Total P&L (realized + unrealized)
        - total_pnl_percent: Total P&L percentage
        - day_change: Today's portfolio value change
        - day_change_percent: Today's change percentage
        - positions_count: Number of open positions
        - last_updated: Last price update timestamp
    """
    try:
        portfolio_service = PortfolioService(session)

        # Get P&L summary (includes unrealized and realized P&L)
        pnl_summary = await portfolio_service.get_portfolio_pnl_summary()

        # Get cash balances by currency
        cash_balances = await _get_cash_balances(session)

        # Get positions count
        positions = await portfolio_service.get_all_positions()
        open_positions = [p for p in positions if p.quantity > 0]
        positions_count = len(open_positions)

        # Calculate total portfolio value (investments + cash)
        total_investment_value = Decimal(str(pnl_summary["total_current_value"]))
        total_cash = sum(Decimal(str(v)) for v in cash_balances.values())
        total_value = total_investment_value + total_cash

        # Calculate total P&L percentage
        total_cost_basis = Decimal(str(pnl_summary["total_cost_basis"]))
        total_pnl = Decimal(str(pnl_summary["total_pnl"]))

        total_pnl_percent = Decimal("0")
        if total_cost_basis > 0:
            total_pnl_percent = (total_pnl / total_cost_basis) * Decimal("100")

        # TODO: Calculate day change (requires price history)
        # For now, return 0 - will implement in next iteration
        day_change = Decimal("0")
        day_change_percent = Decimal("0")

        # Get last price update timestamp
        last_updated = None
        for position in open_positions:
            if position.last_price_update:
                if last_updated is None or position.last_price_update > last_updated:
                    last_updated = position.last_price_update

        return {
            "total_value": float(total_value),
            "cash_balances": {k: float(v) for k, v in cash_balances.items()},
            "total_cash": float(total_cash),
            "total_investment_value": float(total_investment_value),
            "total_cost_basis": float(total_cost_basis),
            "total_pnl": float(total_pnl),
            "total_pnl_percent": float(total_pnl_percent),
            "unrealized_pnl": pnl_summary["total_unrealized_pnl"],
            "realized_pnl": pnl_summary["total_realized_pnl"],
            "day_change": float(day_change),
            "day_change_percent": float(day_change_percent),
            "positions_count": positions_count,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio summary: {str(e)}"
        )


@router.get("/positions")
async def get_positions(
    asset_type: Optional[str] = None,
    session: AsyncSession = Depends(get_async_db)
) -> List[Dict]:
    """
    Get all positions with current prices and P&L.

    Args:
        asset_type: Optional filter by STOCK, METAL, or CRYPTO

    Returns:
        List of position dictionaries with all relevant data
    """
    try:
        portfolio_service = PortfolioService(session)

        # Parse asset type filter
        asset_type_filter = None
        if asset_type:
            try:
                asset_type_filter = AssetType[asset_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid asset type: {asset_type}"
                )

        # Get positions
        positions = await portfolio_service.get_all_positions(asset_type_filter)

        # Filter out closed positions and format for frontend
        result = []
        for position in positions:
            if position.quantity > 0:
                # Calculate fee information for this position
                fee_stmt = select(
                    func.sum(Transaction.fee),
                    func.count(Transaction.id)
                ).where(
                    and_(
                        Transaction.symbol == position.symbol,
                        Transaction.fee > 0
                    )
                )
                fee_result = await session.execute(fee_stmt)
                total_fees, fee_count = fee_result.one()

                result.append({
                    "symbol": position.symbol,
                    "asset_type": position.asset_type.value,
                    "quantity": float(position.quantity),
                    "avg_cost_basis": float(position.avg_cost_basis) if position.avg_cost_basis else 0,
                    "total_cost_basis": float(position.total_cost_basis) if position.total_cost_basis else 0,
                    "current_price": float(position.current_price) if position.current_price else 0,
                    "current_value": float(position.current_value) if position.current_value else 0,
                    "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else 0,
                    "unrealized_pnl_percent": float(position.unrealized_pnl_percent) if position.unrealized_pnl_percent else 0,
                    "currency": position.currency,
                    "first_purchase_date": position.first_purchase_date.isoformat() if position.first_purchase_date else None,
                    "last_transaction_date": position.last_transaction_date.isoformat() if position.last_transaction_date else None,
                    "last_price_update": position.last_price_update.isoformat() if position.last_price_update else None,
                    "total_fees": float(total_fees or 0),
                    "fee_transaction_count": int(fee_count or 0),
                })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch positions: {str(e)}"
        )


@router.post("/refresh-prices")
async def refresh_all_prices(
    session: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Refresh prices for all positions and update P&L.

    Returns:
        Dictionary with update status and summary
    """
    try:
        portfolio_service = PortfolioService(session)
        yahoo_service = YahooFinanceService()

        # Get all positions
        positions = await portfolio_service.get_all_positions()
        open_positions = [p for p in positions if p.quantity > 0]

        # Group symbols by asset type
        stock_symbols = [p.symbol for p in open_positions if p.asset_type == AssetType.STOCK]
        metal_symbols = [p.symbol for p in open_positions if p.asset_type == AssetType.METAL]
        crypto_positions = [p for p in open_positions if p.asset_type == AssetType.CRYPTO]

        updated_count = 0
        failed_symbols = []

        # Fetch prices for stocks/metals
        if stock_symbols or metal_symbols:
            all_stock_symbols = stock_symbols + metal_symbols
            try:
                stock_prices = await yahoo_service.get_stock_prices(all_stock_symbols)
                for symbol, price_data in stock_prices.items():
                    try:
                        current_price = price_data.current_price
                        await portfolio_service.update_position_price(symbol, current_price)
                        updated_count += 1
                    except Exception as e:
                        print(f"Failed to update price for {symbol}: {e}")
                        failed_symbols.append(symbol)
            except Exception as e:
                print(f"Failed to fetch stock prices: {e}")
                failed_symbols.extend(all_stock_symbols)

        # Fetch prices for crypto - group by currency
        if crypto_positions:
            # Group crypto positions by currency
            from collections import defaultdict
            crypto_by_currency = defaultdict(list)
            for position in crypto_positions:
                crypto_by_currency[position.currency].append(position.symbol)

            # Fetch prices for each currency group
            for currency, symbols in crypto_by_currency.items():
                try:
                    crypto_prices = await yahoo_service.get_crypto_prices(symbols, currency)
                    for symbol, price_data in crypto_prices.items():
                        try:
                            current_price = price_data.current_price
                            await portfolio_service.update_position_price(symbol, current_price)
                            updated_count += 1
                        except Exception as e:
                            print(f"Failed to update price for {symbol}: {e}")
                            failed_symbols.append(symbol)
                except Exception as e:
                    print(f"Failed to fetch crypto prices for {currency}: {e}")
                    failed_symbols.extend(symbols)

        return {
            "status": "completed",
            "updated_count": updated_count,
            "failed_count": len(failed_symbols),
            "failed_symbols": failed_symbols,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh prices: {str(e)}"
        )


@router.post("/recalculate-positions")
async def recalculate_all_positions(
    session: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Recalculate all positions from transaction history.

    Returns:
        Dictionary with recalculation status and position count
    """
    try:
        portfolio_service = PortfolioService(session)
        positions = await portfolio_service.recalculate_all_positions()

        return {
            "status": "completed",
            "positions_count": len(positions),
            "symbols": [p.symbol for p in positions],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to recalculate positions: {str(e)}"
        )


@router.get("/open-positions")
async def get_open_positions_overview(
    session: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Get open positions overview showing total value and unrealized P&L.
    Excludes closed positions and cash balances.
    This is separate from the main summary which includes realized P&L and cash.

    Returns:
        Dictionary with:
        - total_value: Total market value of open positions only
        - total_cost_basis: Total cost basis of open positions
        - unrealized_pnl: Total unrealized P&L (market value - cost basis)
        - unrealized_pnl_percent: Unrealized P&L percentage
        - breakdown: P&L breakdown by asset type (stocks, crypto, metals)
        - last_updated: Last price update timestamp
    """
    try:
        portfolio_service = PortfolioService(session)

        # Get all positions
        positions = await portfolio_service.get_all_positions()

        # Filter to only open positions (quantity > 0)
        open_positions = [p for p in positions if p.quantity > 0]

        if not open_positions:
            return {
                "total_value": 0,
                "total_cost_basis": 0,
                "unrealized_pnl": 0,
                "unrealized_pnl_percent": 0,
                "breakdown": {
                    "stocks": {"value": 0, "pnl": 0, "pnl_percent": 0},
                    "crypto": {"value": 0, "pnl": 0, "pnl_percent": 0},
                    "metals": {"value": 0, "pnl": 0, "pnl_percent": 0},
                },
                "last_updated": None,
                "total_fees": 0,
                "fee_transaction_count": 0,
            }

        # Calculate totals
        total_value = Decimal("0")
        total_cost_basis = Decimal("0")

        for position in open_positions:
            if position.current_value:
                total_value += position.current_value
            if position.total_cost_basis:
                total_cost_basis += position.total_cost_basis

        # Calculate unrealized P&L
        unrealized_pnl = total_value - total_cost_basis
        unrealized_pnl_percent = Decimal("0")
        if total_cost_basis > 0:
            unrealized_pnl_percent = (unrealized_pnl / total_cost_basis) * Decimal("100")

        # Calculate breakdown by asset type
        breakdown = {
            "stocks": _calculate_type_metrics([p for p in open_positions if p.asset_type == AssetType.STOCK]),
            "crypto": _calculate_type_metrics([p for p in open_positions if p.asset_type == AssetType.CRYPTO]),
            "metals": _calculate_type_metrics([p for p in open_positions if p.asset_type == AssetType.METAL]),
        }

        # Get last price update timestamp
        last_updated = None
        for position in open_positions:
            if position.last_price_update:
                if last_updated is None or position.last_price_update > last_updated:
                    last_updated = position.last_price_update

        # Calculate fee information for open positions
        fee_info = await _calculate_fee_information(session, open_positions)

        return {
            "total_value": float(total_value),
            "total_cost_basis": float(total_cost_basis),
            "unrealized_pnl": float(unrealized_pnl),
            "unrealized_pnl_percent": float(unrealized_pnl_percent),
            "breakdown": breakdown,
            "last_updated": last_updated.isoformat() if last_updated else None,
            "total_fees": fee_info["total_fees"],
            "fee_transaction_count": fee_info["fee_transaction_count"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch open positions overview: {str(e)}"
        )


def _calculate_type_metrics(positions: List) -> Dict:
    """
    Calculate aggregated metrics for a list of positions of the same asset type.

    Args:
        positions: List of Position objects of the same type

    Returns:
        Dictionary with value, pnl, and pnl_percent
    """
    if not positions:
        return {
            "value": 0,
            "pnl": 0,
            "pnl_percent": 0
        }

    total_value = Decimal("0")
    total_cost_basis = Decimal("0")

    for position in positions:
        if position.current_value:
            total_value += position.current_value
        if position.total_cost_basis:
            total_cost_basis += position.total_cost_basis

    pnl = total_value - total_cost_basis
    pnl_percent = Decimal("0")
    if total_cost_basis > 0:
        pnl_percent = (pnl / total_cost_basis) * Decimal("100")

    return {
        "value": float(total_value),
        "pnl": float(pnl),
        "pnl_percent": float(pnl_percent)
    }


async def _get_cash_balances(session: AsyncSession) -> Dict[str, Decimal]:
    """
    Calculate cash balances by currency from transactions.

    Args:
        session: Database session

    Returns:
        Dictionary mapping currency code to balance
    """
    # Get all cash transactions (CASH_IN, CASH_OUT)
    stmt = select(Transaction).where(
        Transaction.transaction_type.in_([TransactionType.CASH_IN, TransactionType.CASH_OUT])
    )
    result = await session.execute(stmt)
    cash_transactions = list(result.scalars().all())

    # Calculate balance by currency
    balances: Dict[str, Decimal] = {}

    for txn in cash_transactions:
        currency = txn.currency
        amount = txn.total_amount or Decimal("0")

        if currency not in balances:
            balances[currency] = Decimal("0")

        if txn.transaction_type == TransactionType.CASH_IN:
            balances[currency] += amount
        elif txn.transaction_type == TransactionType.CASH_OUT:
            balances[currency] -= amount

    return balances


async def _calculate_fee_information(session: AsyncSession, open_positions: List) -> Dict:
    """
    Calculate total fees and transaction count for open positions.

    Args:
        session: Database session
        open_positions: List of Position objects with quantity > 0

    Returns:
        Dictionary with total_fees and fee_transaction_count
    """
    if not open_positions:
        return {
            "total_fees": 0,
            "fee_transaction_count": 0
        }

    # Get all symbols from open positions
    symbols = [p.symbol for p in open_positions]

    # Query all transactions for these symbols
    stmt = select(Transaction).where(
        Transaction.symbol.in_(symbols)
    )
    result = await session.execute(stmt)
    transactions = list(result.scalars().all())

    # Aggregate fees
    total_fees = Decimal("0")
    fee_transaction_count = 0

    for txn in transactions:
        if txn.fee and txn.fee > 0:
            total_fees += txn.fee
            fee_transaction_count += 1

    return {
        "total_fees": float(total_fees),
        "fee_transaction_count": fee_transaction_count
    }
