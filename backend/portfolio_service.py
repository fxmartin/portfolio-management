# ABOUTME: Portfolio service for position aggregation and P&L calculations
# ABOUTME: Integrates FIFO calculator with database to maintain current positions

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import Transaction, Position, AssetType, TransactionType
from fifo_calculator import FIFOCalculator, Lot


class PortfolioService:
    """
    Service for managing portfolio positions and calculations.

    Integrates FIFO cost basis calculator with database operations to:
    - Calculate current positions from transaction history
    - Maintain lot-level cost basis tracking
    - Update positions when new transactions are added
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize portfolio service.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get current position for a symbol.

        Args:
            symbol: Asset symbol (e.g., AAPL, BTC, XAU)

        Returns:
            Position object or None if not found
        """
        stmt = select(Position).where(Position.symbol == symbol)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_positions(self, asset_type: Optional[AssetType] = None) -> List[Position]:
        """
        Get all current positions, optionally filtered by asset type.

        Args:
            asset_type: Optional filter by STOCK, METAL, or CRYPTO

        Returns:
            List of Position objects
        """
        if asset_type:
            stmt = select(Position).where(Position.asset_type == asset_type)
        else:
            stmt = select(Position)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_position(self, symbol: str) -> Position:
        """
        Update a single position by recalculating from all transactions.

        Args:
            symbol: Asset symbol to update

        Returns:
            Updated Position object
        """
        # Get all non-deleted transactions for this symbol, ordered by date
        stmt = (
            select(Transaction)
            .where(Transaction.symbol == symbol)
            .where(Transaction.deleted_at.is_(None))
            .order_by(Transaction.transaction_date)
        )
        result = await self.session.execute(stmt)
        transactions = list(result.scalars().all())

        if not transactions:
            # No transactions, delete position if exists
            position = await self.get_position(symbol)
            if position:
                await self.session.delete(position)
                await self.session.commit()
            return None

        # Calculate position using FIFO
        position_data = await self._calculate_position_from_transactions(symbol, transactions)

        # Get or create position
        position = await self.get_position(symbol)
        if not position:
            position = Position(symbol=symbol)
            self.session.add(position)

        # Update position fields
        position.asset_type = position_data["asset_type"]
        position.quantity = position_data["quantity"]
        position.avg_cost_basis = position_data["avg_cost_basis"]
        position.total_cost_basis = position_data["total_cost_basis"]
        position.currency = position_data["currency"]
        position.first_purchase_date = position_data["first_purchase_date"]
        position.last_transaction_date = position_data["last_transaction_date"]
        position.cost_lots = position_data["cost_lots"]

        await self.session.commit()
        await self.session.refresh(position)

        return position

    async def recalculate_all_positions(self) -> List[Position]:
        """
        Recalculate all positions from scratch.

        Useful after bulk transaction imports or database changes.

        Returns:
            List of updated Position objects
        """
        # Get all unique symbols from transactions
        stmt = select(Transaction.symbol).distinct()
        result = await self.session.execute(stmt)
        symbols = [row[0] for row in result.all()]

        # Update each position
        positions = []
        for symbol in symbols:
            position = await self.update_position(symbol)
            if position:
                positions.append(position)

        return positions

    async def _calculate_position_from_transactions(
        self,
        symbol: str,
        transactions: List[Transaction]
    ) -> Dict:
        """
        Calculate position data from transaction history using FIFO.

        Args:
            symbol: Asset symbol
            transactions: List of transactions ordered by date

        Returns:
            Dictionary with position data
        """
        if not transactions:
            return None

        calc = FIFOCalculator()
        asset_type = transactions[0].asset_type
        currency = transactions[0].currency
        first_purchase_date = None
        last_transaction_date = None

        # Process each transaction
        for txn in transactions:
            last_transaction_date = txn.transaction_date

            # BUY, STAKING, AIRDROP, and MINING all increase position quantity
            if txn.transaction_type in [TransactionType.BUY, TransactionType.STAKING,
                                        TransactionType.AIRDROP, TransactionType.MINING]:
                if first_purchase_date is None:
                    first_purchase_date = txn.transaction_date

                calc.add_purchase(
                    ticker=symbol,
                    quantity=txn.quantity,
                    price=txn.price_per_unit,  # For rewards, this is market value at receipt
                    date=txn.transaction_date,
                    transaction_id=txn.id,
                    fee=txn.fee or Decimal("0")  # Include fees in cost basis
                )

            elif txn.transaction_type == TransactionType.SELL:
                # Process sale using FIFO
                try:
                    calc.process_sale(
                        ticker=symbol,
                        quantity=txn.quantity,
                        sale_price=txn.price_per_unit,
                        date=txn.transaction_date,
                        transaction_id=txn.id,
                        fee=txn.fee or Decimal("0")
                    )
                except ValueError as e:
                    # Log error but continue - may happen with data inconsistencies
                    print(f"Warning: FIFO error for {symbol}: {e}")

        # Calculate position summary
        total_quantity = calc.get_total_quantity(symbol)
        total_cost_basis = calc.get_total_cost_basis(symbol)
        avg_cost_basis = calc.get_average_cost_basis(symbol)

        # Export lots to JSON for storage
        cost_lots = calc.export_lots_to_json(symbol)

        return {
            "asset_type": asset_type,
            "quantity": total_quantity,
            "avg_cost_basis": avg_cost_basis,
            "total_cost_basis": total_cost_basis,
            "currency": currency,
            "first_purchase_date": first_purchase_date,
            "last_transaction_date": last_transaction_date,
            "cost_lots": cost_lots,
        }

    async def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio-level summary statistics.

        Returns:
            Dictionary with portfolio totals and statistics
        """
        positions = await self.get_all_positions()

        total_positions = len([p for p in positions if p.quantity > 0])
        total_cost_basis = sum(p.total_cost_basis or Decimal("0") for p in positions)

        # Count by asset type
        stocks = [p for p in positions if p.asset_type == AssetType.STOCK and p.quantity > 0]
        metals = [p for p in positions if p.asset_type == AssetType.METAL and p.quantity > 0]
        crypto = [p for p in positions if p.asset_type == AssetType.CRYPTO and p.quantity > 0]

        return {
            "total_positions": total_positions,
            "total_cost_basis": float(total_cost_basis),
            "positions_by_type": {
                "stocks": len(stocks),
                "metals": len(metals),
                "crypto": len(crypto),
            },
            "symbols": [p.symbol for p in positions if p.quantity > 0]
        }

    async def delete_all_positions(self) -> int:
        """
        Delete all positions (for testing/reset).

        Returns:
            Number of positions deleted
        """
        positions = await self.get_all_positions()
        count = len(positions)

        for position in positions:
            await self.session.delete(position)

        await self.session.commit()
        return count

    async def update_position_price(self, symbol: str, current_price: Decimal, asset_name: str = None, price_currency: str = 'USD', usd_eur_rate: Decimal = None) -> Position:
        """
        Update position with current market price and calculate unrealized P&L.

        Prices are kept in their original currency (USD/EUR).
        Values and P&L are converted to EUR for portfolio-level calculations.

        Args:
            symbol: Asset symbol
            current_price: Current market price (in original currency)
            asset_name: Optional full asset name (e.g., "MicroStrategy", "Bitcoin")
            price_currency: Currency of the price (USD or EUR)
            usd_eur_rate: USD to EUR exchange rate (if needed for conversion)

        Returns:
            Updated Position object
        """
        position = await self.get_position(symbol)
        if not position:
            raise ValueError(f"Position not found for symbol: {symbol}")

        # Update current price (keep in original currency for display)
        position.current_price = current_price
        position.last_price_update = datetime.now()

        # Update asset name if provided
        if asset_name:
            position.asset_name = asset_name

        # Calculate current value in EUR
        # If position is in USD, convert to EUR; if already EUR, use as-is
        if position.currency == 'USD' and usd_eur_rate:
            # Convert: (quantity * price_usd) / exchange_rate = value_eur
            # usd_eur_rate from EURUSD=X means "1 EUR = X USD", so divide to get EUR
            position.current_value = (position.quantity * current_price) / usd_eur_rate
        else:
            # Already in EUR or no conversion needed
            position.current_value = position.quantity * current_price

        # Calculate unrealized P&L in EUR
        if position.quantity > 0 and position.total_cost_basis:
            # Convert total cost basis to EUR if needed
            if position.currency == 'USD' and usd_eur_rate:
                total_cost_basis_eur = position.total_cost_basis / usd_eur_rate
            else:
                total_cost_basis_eur = position.total_cost_basis

            # P&L = current_value_eur - total_cost_basis_eur
            position.unrealized_pnl = position.current_value - total_cost_basis_eur

            # Calculate percentage based on cost basis
            if total_cost_basis_eur > 0:
                pnl_pct = (position.unrealized_pnl / total_cost_basis_eur) * Decimal("100")
                position.unrealized_pnl_percent = pnl_pct.quantize(Decimal("0.01"))
        else:
            position.unrealized_pnl = Decimal("0")
            position.unrealized_pnl_percent = Decimal("0")

        await self.session.commit()
        await self.session.refresh(position)

        return position

    async def get_realized_pnl(self, symbol: str) -> Dict:
        """
        Calculate realized P&L for a ticker from all sell transactions.

        Args:
            symbol: Asset symbol

        Returns:
            Dictionary with realized P&L details
        """
        # Get all transactions for this symbol
        stmt = (
            select(Transaction)
            .where(Transaction.symbol == symbol)
            .order_by(Transaction.transaction_date)
        )
        result = await self.session.execute(stmt)
        transactions = list(result.scalars().all())

        # Use FIFO to calculate realized P&L
        calc = FIFOCalculator()
        total_realized_pnl = Decimal("0")
        total_fees = Decimal("0")
        sales = []

        for txn in transactions:
            # BUY, STAKING, AIRDROP, and MINING all increase position quantity
            if txn.transaction_type in [TransactionType.BUY, TransactionType.STAKING,
                                        TransactionType.AIRDROP, TransactionType.MINING]:
                calc.add_purchase(
                    ticker=symbol,
                    quantity=txn.quantity,
                    price=txn.price_per_unit,  # For rewards, this is market value at receipt
                    date=txn.transaction_date,
                    transaction_id=txn.id,
                    fee=txn.fee or Decimal("0")  # Include fees in cost basis
                )
            elif txn.transaction_type == TransactionType.SELL:
                try:
                    result = calc.process_sale(
                        ticker=symbol,
                        quantity=txn.quantity,
                        sale_price=txn.price_per_unit,
                        date=txn.transaction_date,
                        transaction_id=txn.id,
                        fee=txn.fee or Decimal("0")
                    )

                    total_realized_pnl += result.realized_pnl
                    total_fees += result.fee

                    sales.append({
                        "date": txn.transaction_date.isoformat(),
                        "quantity": float(txn.quantity),
                        "sale_price": float(txn.price_per_unit),
                        "realized_pnl": float(result.realized_pnl),
                        "fee": float(result.fee)
                    })
                except ValueError as e:
                    print(f"Warning: Error calculating realized P&L for {symbol}: {e}")

        return {
            "symbol": symbol,
            "total_realized_pnl": total_realized_pnl,
            "total_fees": total_fees,
            "net_realized_pnl": total_realized_pnl - total_fees,
            "sales": sales
        }

    async def get_portfolio_pnl_summary(self) -> Dict:
        """
        Get portfolio-wide P&L summary (realized and unrealized).

        Returns:
            Dictionary with total P&L statistics
        """
        positions = await self.get_all_positions()

        # Calculate totals
        total_unrealized_pnl = Decimal("0")
        total_current_value = Decimal("0")
        total_cost_basis = Decimal("0")

        for position in positions:
            if position.quantity > 0:
                if position.unrealized_pnl:
                    total_unrealized_pnl += position.unrealized_pnl
                if position.current_value:
                    total_current_value += position.current_value
                if position.total_cost_basis:
                    total_cost_basis += position.total_cost_basis

        # Get realized P&L from all symbols
        total_realized_pnl = Decimal("0")
        total_fees = Decimal("0")

        for position in positions:
            realized = await self.get_realized_pnl(position.symbol)
            total_realized_pnl += realized["total_realized_pnl"]
            total_fees += realized["total_fees"]

        # Calculate total P&L (realized + unrealized)
        total_pnl = total_realized_pnl + total_unrealized_pnl
        net_total_pnl = total_pnl - total_fees

        return {
            "total_current_value": float(total_current_value),
            "total_cost_basis": float(total_cost_basis),
            "total_unrealized_pnl": float(total_unrealized_pnl),
            "total_realized_pnl": float(total_realized_pnl),
            "total_fees": float(total_fees),
            "net_realized_pnl": float(total_realized_pnl - total_fees),
            "total_pnl": float(total_pnl),
            "net_total_pnl": float(net_total_pnl),
        }

    async def get_realized_pnl_summary(self) -> Dict:
        """
        Calculate realized P&L summary from all sell transactions (including partial sales).

        Uses FIFO methodology to calculate realized gains/losses for any symbol that has
        been sold (partially or fully).

        Returns:
            Dictionary with:
            - total_realized_pnl: Total realized gains/losses from all sales
            - total_fees: Sum of all transaction fees (buy + sell)
            - net_pnl: Realized P&L minus total fees
            - closed_positions_count: Number of symbols with sales
            - breakdown: Per-asset-type breakdown (stocks, crypto, metals) with:
                - realized_pnl: Realized gains/losses for this asset type
                - fees: Transaction fees for this asset type
                - net_pnl: Net P&L after fees for this asset type
                - closed_count: Number of symbols with sales in this asset type
        """
        from sqlalchemy import func, case
        from collections import defaultdict

        # Step 1: Get all symbols that have any SELL transactions
        # Query to get symbols with sales and their asset types
        stmt = select(
            Transaction.symbol,
            Transaction.asset_type,
            func.sum(
                case(
                    (Transaction.transaction_type.in_([
                        TransactionType.BUY,
                        TransactionType.STAKING,
                        TransactionType.AIRDROP,
                        TransactionType.MINING
                    ]), Transaction.quantity),
                    else_=Decimal("0")
                )
            ).label('total_bought'),
            func.sum(
                case(
                    (Transaction.transaction_type == TransactionType.SELL, Transaction.quantity),
                    else_=Decimal("0")
                )
            ).label('total_sold'),
        ).group_by(Transaction.symbol, Transaction.asset_type)

        result = await self.session.execute(stmt)
        position_status = result.all()

        # Get all symbols that have any sales (partial or full)
        symbols_with_sales = []
        for row in position_status:
            symbol = row.symbol
            asset_type = row.asset_type
            total_sold = row.total_sold or Decimal("0")

            # Include any symbol that has sales
            if total_sold > 0:
                symbols_with_sales.append((symbol, asset_type))

        # Step 2: Calculate realized P&L for all symbols with sales using FIFO
        total_realized_pnl = Decimal("0")
        breakdown_data = defaultdict(lambda: {
            'realized_pnl': Decimal("0"),
            'fees': Decimal("0"),
            'closed_count': 0
        })

        for symbol, asset_type in symbols_with_sales:
            # Get all transactions for this symbol
            txn_stmt = (
                select(Transaction)
                .where(Transaction.symbol == symbol)
                .order_by(Transaction.transaction_date)
            )
            txn_result = await self.session.execute(txn_stmt)
            transactions = list(txn_result.scalars().all())

            # Calculate realized P&L using FIFO
            calc = FIFOCalculator()
            realized_pnl = Decimal("0")
            fees = Decimal("0")

            for txn in transactions:
                if txn.transaction_type in [TransactionType.BUY, TransactionType.STAKING,
                                           TransactionType.AIRDROP, TransactionType.MINING]:
                    # Don't include fees in cost basis for realized P&L calculation
                    # We want to show gross P&L and fees separately
                    calc.add_purchase(
                        ticker=symbol,
                        quantity=txn.quantity,
                        price=txn.price_per_unit,
                        date=txn.transaction_date,
                        transaction_id=txn.id,
                        fee=Decimal("0")  # Track fees separately
                    )
                    fees += txn.fee or Decimal("0")

                elif txn.transaction_type == TransactionType.SELL:
                    try:
                        sale_result = calc.process_sale(
                            ticker=symbol,
                            quantity=txn.quantity,
                            sale_price=txn.price_per_unit,
                            date=txn.transaction_date,
                            transaction_id=txn.id,
                            fee=Decimal("0")  # Track fees separately
                        )
                        realized_pnl += sale_result.realized_pnl
                        fees += txn.fee or Decimal("0")
                    except ValueError as e:
                        print(f"Warning: FIFO error for {symbol}: {e}")

            # Map asset type to breakdown key
            asset_key = self._map_asset_type_to_key(asset_type)
            breakdown_data[asset_key]['realized_pnl'] += realized_pnl
            breakdown_data[asset_key]['fees'] += fees
            breakdown_data[asset_key]['closed_count'] += 1
            total_realized_pnl += realized_pnl

        # Step 3: Calculate total fees across ALL transactions (not just closed positions)
        fee_stmt = select(func.sum(Transaction.fee))
        fee_result = await self.session.execute(fee_stmt)
        total_fees = fee_result.scalar() or Decimal("0")

        # Step 4: Build breakdown response
        breakdown = {
            'stocks': {
                'realized_pnl': float(breakdown_data['stocks']['realized_pnl']),
                'fees': float(breakdown_data['stocks']['fees']),
                'net_pnl': float(breakdown_data['stocks']['realized_pnl'] - breakdown_data['stocks']['fees']),
                'closed_count': breakdown_data['stocks']['closed_count']
            },
            'crypto': {
                'realized_pnl': float(breakdown_data['crypto']['realized_pnl']),
                'fees': float(breakdown_data['crypto']['fees']),
                'net_pnl': float(breakdown_data['crypto']['realized_pnl'] - breakdown_data['crypto']['fees']),
                'closed_count': breakdown_data['crypto']['closed_count']
            },
            'metals': {
                'realized_pnl': float(breakdown_data['metals']['realized_pnl']),
                'fees': float(breakdown_data['metals']['fees']),
                'net_pnl': float(breakdown_data['metals']['realized_pnl'] - breakdown_data['metals']['fees']),
                'closed_count': breakdown_data['metals']['closed_count']
            }
        }

        return {
            'total_realized_pnl': float(total_realized_pnl),
            'total_fees': float(total_fees),
            'net_pnl': float(total_realized_pnl - total_fees),
            'closed_positions_count': len(symbols_with_sales),
            'breakdown': breakdown,
            'last_updated': datetime.now().isoformat()
        }

    def _map_asset_type_to_key(self, asset_type: AssetType) -> str:
        """
        Map AssetType enum to breakdown key.

        Args:
            asset_type: AssetType enum value

        Returns:
            String key for breakdown dictionary ('stocks', 'crypto', or 'metals')
        """
        if asset_type == AssetType.STOCK:
            return 'stocks'
        elif asset_type == AssetType.CRYPTO:
            return 'crypto'
        elif asset_type == AssetType.METAL:
            return 'metals'
        return 'stocks'  # Default fallback
