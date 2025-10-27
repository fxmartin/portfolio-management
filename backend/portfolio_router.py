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
                    "asset_name": position.asset_name,
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

        # Get USD to EUR exchange rate for currency conversion
        usd_eur_rate = await yahoo_service.get_usd_to_eur_rate()

        # Fetch prices for stocks/metals
        if stock_symbols or metal_symbols:
            all_stock_symbols = stock_symbols + metal_symbols
            try:
                stock_prices = await yahoo_service.get_stock_prices(all_stock_symbols)
                for symbol, price_data in stock_prices.items():
                    try:
                        current_price = price_data.current_price
                        asset_name = price_data.asset_name
                        price_currency = price_data.price_currency
                        await portfolio_service.update_position_price(
                            symbol,
                            current_price,
                            asset_name,
                            price_currency,
                            usd_eur_rate
                        )
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
                            asset_name = price_data.asset_name
                            price_currency = price_data.price_currency
                            await portfolio_service.update_position_price(
                                symbol,
                                current_price,
                                asset_name,
                                price_currency,
                                usd_eur_rate
                            )
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

        # Calculate totals (all values already in EUR from update_position_price)
        total_value = Decimal("0")
        unrealized_pnl = Decimal("0")

        # Check if positions have been priced (have unrealized_pnl calculated)
        all_positions_priced = all(p.unrealized_pnl is not None for p in open_positions)

        for position in open_positions:
            if position.current_value:
                total_value += position.current_value
            if position.unrealized_pnl is not None:
                unrealized_pnl += position.unrealized_pnl

        # Calculate cost basis and P&L
        # If positions are priced, derive cost basis from value and P&L (avoids USD/EUR mixing)
        # If not priced, sum up cost basis directly and calculate P&L
        if all_positions_priced and (total_value > 0 or unrealized_pnl != 0):
            total_cost_basis = total_value - unrealized_pnl
        else:
            # Fallback: sum cost basis directly when positions aren't priced
            # TODO: This doesn't handle USD cost basis correctly - need exchange rate
            total_cost_basis = sum(
                p.total_cost_basis for p in open_positions if p.total_cost_basis
            )
            # Recalculate P&L from value and cost basis
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

    Uses pre-calculated unrealized_pnl from each position to avoid USD/EUR mixing issues.

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
    pnl = Decimal("0")

    # Check if positions have been priced
    all_positions_priced = all(p.unrealized_pnl is not None for p in positions)

    for position in positions:
        if position.current_value:
            total_value += position.current_value
        if position.unrealized_pnl is not None:
            pnl += position.unrealized_pnl

    # Calculate cost basis and P&L
    # If priced, derive cost basis from value and P&L (EUR-safe)
    # If not priced, sum cost basis directly and calculate P&L
    if all_positions_priced and (total_value > 0 or pnl != 0):
        total_cost_basis = total_value - pnl
    else:
        # Fallback: sum cost basis directly when positions aren't priced
        total_cost_basis = sum(
            p.total_cost_basis for p in positions if p.total_cost_basis
        )
        # Recalculate P&L from value and cost basis
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


@router.get("/history")
async def get_portfolio_history(
    period: str = "1M",
    session: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Get historical portfolio values for charting.

    Args:
        period: Time period (1D, 1W, 1M, 3M, 1Y, All)
        session: Database session

    Returns:
        Dictionary with:
        - data: Array of {date, value} points
        - period: Selected time period
        - initial_value: Starting portfolio value
        - current_value: Current portfolio value
        - change: Absolute change
        - change_percent: Percentage change
    """
    from datetime import timedelta
    import asyncio

    try:
        # Determine date range based on period
        now = datetime.now()
        period_map = {
            "1D": timedelta(days=1),
            "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
            "3M": timedelta(days=90),
            "1Y": timedelta(days=365),
            "All": None  # From first transaction
        }

        if period not in period_map:
            raise HTTPException(status_code=400, detail="Invalid period. Use: 1D, 1W, 1M, 3M, 1Y, or All")

        # Get date range
        end_date = now
        if period == "All":
            # Get first transaction date
            stmt = select(func.min(Transaction.transaction_date))
            result = await session.execute(stmt)
            start_date = result.scalar()
            if not start_date:
                # No transactions yet
                return {
                    "data": [],
                    "period": period,
                    "initial_value": 0,
                    "current_value": 0,
                    "change": 0,
                    "change_percent": 0
                }
        else:
            start_date = now - period_map[period]

        # Determine granularity (number of data points)
        days_diff = (end_date - start_date).days
        if days_diff <= 1:
            # Hourly for 1D
            data_points = 24
            interval = timedelta(hours=1)
        elif days_diff <= 7:
            # Every 6 hours for 1W
            data_points = days_diff * 4
            interval = timedelta(hours=6)
        elif days_diff <= 30:
            # Daily for 1M
            data_points = days_diff
            interval = timedelta(days=1)
        elif days_diff <= 90:
            # Every 3 days for 3M
            data_points = days_diff // 3
            interval = timedelta(days=3)
        else:
            # Weekly for 1Y and All
            data_points = days_diff // 7
            interval = timedelta(days=7)

        # Get all transactions up to end_date
        stmt = select(Transaction).where(
            Transaction.transaction_date <= end_date
        ).order_by(Transaction.transaction_date)
        result = await session.execute(stmt)
        all_transactions = list(result.scalars().all())

        if not all_transactions:
            return {
                "data": [],
                "period": period,
                "initial_value": 0,
                "current_value": 0,
                "change": 0,
                "change_percent": 0
            }

        # Get current prices for all symbols
        portfolio_service = PortfolioService(session)
        positions = await portfolio_service.get_all_positions()

        # Build price map (symbol -> current_price)
        price_map = {}
        for pos in positions:
            if pos.current_price:
                price_map[pos.symbol] = float(pos.current_price)

        # Calculate portfolio value at regular intervals
        data = []
        current_date = start_date

        for i in range(data_points + 1):
            if current_date > end_date:
                break

            # Get transactions up to this date
            txns_up_to_date = [t for t in all_transactions if t.transaction_date <= current_date]

            # Calculate positions at this date using FIFO
            from fifo_calculator import FIFOCalculator
            calculator = FIFOCalculator()

            # Track quantities by symbol
            symbol_quantities = {}

            for txn in txns_up_to_date:
                if txn.transaction_type in [TransactionType.BUY, TransactionType.STAKING,
                                            TransactionType.AIRDROP, TransactionType.MINING]:
                    if txn.symbol not in symbol_quantities:
                        symbol_quantities[txn.symbol] = Decimal("0")
                    symbol_quantities[txn.symbol] += txn.quantity or Decimal("0")

                elif txn.transaction_type == TransactionType.SELL:
                    if txn.symbol in symbol_quantities:
                        symbol_quantities[txn.symbol] -= txn.quantity or Decimal("0")
                        if symbol_quantities[txn.symbol] <= 0:
                            del symbol_quantities[txn.symbol]

            # Calculate total value using current prices
            total_value = Decimal("0")
            for symbol, quantity in symbol_quantities.items():
                if symbol in price_map and quantity > 0:
                    price = Decimal(str(price_map[symbol]))
                    total_value += quantity * price

            data.append({
                "date": current_date.isoformat(),
                "value": float(total_value)
            })

            current_date += interval

        # Calculate metrics
        initial_value = data[0]["value"] if data else 0
        current_value = data[-1]["value"] if data else 0
        change = current_value - initial_value
        change_percent = (change / initial_value * 100) if initial_value > 0 else 0

        return {
            "data": data,
            "period": period,
            "initial_value": initial_value,
            "current_value": current_value,
            "change": change,
            "change_percent": change_percent
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate portfolio history: {str(e)}")
