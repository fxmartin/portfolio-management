# ABOUTME: FIFO cost basis calculator for accurate tax reporting and P&L
# ABOUTME: Implements First-In-First-Out methodology with lot tracking and audit trails

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class Lot:
    """Represents a purchase lot for FIFO tracking"""
    quantity: Decimal
    price: Decimal
    date: datetime
    transaction_id: int

    def __post_init__(self):
        """Ensure all numeric values are Decimal"""
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost of this lot"""
        return self.quantity * self.price

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "quantity": str(self.quantity),
            "price": str(self.price),
            "date": self.date.isoformat(),
            "transaction_id": self.transaction_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Lot':
        """Create Lot from dictionary"""
        return cls(
            quantity=Decimal(data["quantity"]),
            price=Decimal(data["price"]),
            date=datetime.fromisoformat(data["date"]),
            transaction_id=data["transaction_id"]
        )


@dataclass
class FIFOResult:
    """Result of a FIFO sale transaction"""
    ticker: str
    quantity_sold: Decimal
    sale_price: Decimal
    sale_date: datetime
    transaction_id: int
    realized_pnl: Decimal
    fee: Decimal = Decimal("0")
    lots_sold: List[dict] = field(default_factory=list)

    def __post_init__(self):
        """Ensure all numeric values are Decimal"""
        if not isinstance(self.quantity_sold, Decimal):
            self.quantity_sold = Decimal(str(self.quantity_sold))
        if not isinstance(self.sale_price, Decimal):
            self.sale_price = Decimal(str(self.sale_price))
        if not isinstance(self.realized_pnl, Decimal):
            self.realized_pnl = Decimal(str(self.realized_pnl))
        if not isinstance(self.fee, Decimal):
            self.fee = Decimal(str(self.fee))

    @property
    def net_pnl(self) -> Decimal:
        """Calculate P&L after fees"""
        return self.realized_pnl - self.fee

    @property
    def total_proceeds(self) -> Decimal:
        """Calculate total proceeds from sale"""
        return self.quantity_sold * self.sale_price

    @property
    def total_cost_basis(self) -> Decimal:
        """Calculate total cost basis of sold lots"""
        return sum(Decimal(lot["cost_basis"]) * Decimal(lot["quantity"])
                  for lot in self.lots_sold)


class FIFOCalculator:
    """
    First-In-First-Out cost basis calculator.

    Maintains lot queues for each ticker and processes sales using
    FIFO methodology for accurate tax reporting and P&L calculations.
    """

    def __init__(self):
        """Initialize FIFO calculator with empty lot queues"""
        self._lots: Dict[str, deque[Lot]] = {}

    def add_purchase(
        self,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        date: datetime,
        transaction_id: int,
        fee: Decimal = Decimal("0")
    ) -> None:
        """
        Add a purchase lot to the FIFO queue.

        Args:
            ticker: Asset symbol (e.g., AAPL, BTC, XAU)
            quantity: Number of units purchased
            price: Price per unit (before fees)
            date: Purchase date
            transaction_id: Database transaction ID for audit trail
            fee: Transaction fee to be included in cost basis
        """
        if ticker not in self._lots:
            self._lots[ticker] = deque()

        # Include fee in cost basis by calculating adjusted price per unit
        fee = Decimal(str(fee))
        total_cost = (Decimal(str(price)) * Decimal(str(quantity))) + fee
        adjusted_price = total_cost / Decimal(str(quantity)) if quantity > 0 else Decimal(str(price))

        lot = Lot(
            quantity=Decimal(str(quantity)),
            price=adjusted_price,  # Price now includes fee allocation
            date=date,
            transaction_id=transaction_id
        )

        # Insert in chronological order to maintain FIFO
        # Find correct position based on date
        lots_queue = self._lots[ticker]
        inserted = False

        # Convert to list for easier insertion
        lots_list = list(lots_queue)
        for i, existing_lot in enumerate(lots_list):
            if lot.date < existing_lot.date:
                lots_list.insert(i, lot)
                inserted = True
                break

        if not inserted:
            lots_list.append(lot)

        # Replace deque with sorted lots
        self._lots[ticker] = deque(lots_list)

    def process_sale(
        self,
        ticker: str,
        quantity: Decimal,
        sale_price: Decimal,
        date: datetime,
        transaction_id: int,
        fee: Decimal = Decimal("0")
    ) -> FIFOResult:
        """
        Process a sale transaction using FIFO methodology.

        Args:
            ticker: Asset symbol
            quantity: Number of units to sell
            sale_price: Sale price per unit
            date: Sale date
            transaction_id: Database transaction ID
            fee: Transaction fee (tracked separately from cost basis)

        Returns:
            FIFOResult with realized P&L and lot details

        Raises:
            ValueError: If ticker not found or insufficient shares
        """
        if ticker not in self._lots or not self._lots[ticker]:
            raise ValueError(f"No lots found for ticker {ticker}")

        # Convert to Decimal
        quantity = Decimal(str(quantity))
        sale_price = Decimal(str(sale_price))
        fee = Decimal(str(fee))

        # Check if we have enough shares
        total_available = sum(lot.quantity for lot in self._lots[ticker])
        if quantity > total_available:
            raise ValueError(
                f"Insufficient shares for {ticker}. "
                f"Requested: {quantity}, Available: {total_available}"
            )

        lots_queue = self._lots[ticker]
        remaining_to_sell = quantity
        realized_pnl = Decimal("0")
        lots_sold = []

        # Process sale using FIFO
        while remaining_to_sell > 0 and lots_queue:
            oldest_lot = lots_queue[0]

            if oldest_lot.quantity <= remaining_to_sell:
                # Sell entire lot
                quantity_from_lot = oldest_lot.quantity
                cost_basis = oldest_lot.price
                pnl = (sale_price - cost_basis) * quantity_from_lot

                lots_sold.append({
                    "quantity": quantity_from_lot,
                    "cost_basis": cost_basis,
                    "proceeds": sale_price,
                    "pnl": pnl,
                    "purchase_date": oldest_lot.date.isoformat(),
                    "transaction_id": oldest_lot.transaction_id
                })

                realized_pnl += pnl
                remaining_to_sell -= quantity_from_lot
                lots_queue.popleft()  # Remove depleted lot

            else:
                # Partial lot sale
                quantity_from_lot = remaining_to_sell
                cost_basis = oldest_lot.price
                pnl = (sale_price - cost_basis) * quantity_from_lot

                lots_sold.append({
                    "quantity": quantity_from_lot,
                    "cost_basis": cost_basis,
                    "proceeds": sale_price,
                    "pnl": pnl,
                    "purchase_date": oldest_lot.date.isoformat(),
                    "transaction_id": oldest_lot.transaction_id
                })

                realized_pnl += pnl
                oldest_lot.quantity -= quantity_from_lot
                remaining_to_sell = Decimal("0")

        return FIFOResult(
            ticker=ticker,
            quantity_sold=quantity,
            sale_price=sale_price,
            sale_date=date,
            transaction_id=transaction_id,
            realized_pnl=realized_pnl,
            fee=fee,
            lots_sold=lots_sold
        )

    def get_lots(self, ticker: str) -> List[Lot]:
        """
        Get all remaining lots for a ticker.

        Args:
            ticker: Asset symbol

        Returns:
            List of remaining lots in FIFO order
        """
        if ticker not in self._lots:
            return []
        return list(self._lots[ticker])

    def get_total_quantity(self, ticker: str) -> Decimal:
        """
        Calculate total quantity remaining for a ticker.

        Args:
            ticker: Asset symbol

        Returns:
            Total quantity across all lots
        """
        if ticker not in self._lots:
            return Decimal("0")
        return sum(lot.quantity for lot in self._lots[ticker])

    def get_total_cost_basis(self, ticker: str) -> Decimal:
        """
        Calculate total cost basis for all remaining lots.

        Args:
            ticker: Asset symbol

        Returns:
            Total cost basis (sum of quantity * price for each lot)
        """
        if ticker not in self._lots:
            return Decimal("0")
        return sum(lot.total_cost for lot in self._lots[ticker])

    def get_average_cost_basis(self, ticker: str) -> Decimal:
        """
        Calculate weighted average cost basis.

        Args:
            ticker: Asset symbol

        Returns:
            Weighted average cost per unit
        """
        total_quantity = self.get_total_quantity(ticker)
        if total_quantity == 0:
            return Decimal("0")

        total_cost = self.get_total_cost_basis(ticker)
        return total_cost / total_quantity

    def get_all_tickers(self) -> List[str]:
        """
        Get list of all tickers with lots.

        Returns:
            List of ticker symbols
        """
        return [ticker for ticker in self._lots.keys() if self._lots[ticker]]

    def export_lots_to_json(self, ticker: str) -> List[dict]:
        """
        Export lots as JSON for database storage.

        Args:
            ticker: Asset symbol

        Returns:
            List of lot dictionaries
        """
        if ticker not in self._lots:
            return []
        return [lot.to_dict() for lot in self._lots[ticker]]

    def import_lots_from_json(self, ticker: str, lots_data: List[dict]) -> None:
        """
        Import lots from JSON (from database).

        Args:
            ticker: Asset symbol
            lots_data: List of lot dictionaries
        """
        if ticker not in self._lots:
            self._lots[ticker] = deque()
        else:
            self._lots[ticker].clear()

        for lot_data in lots_data:
            lot = Lot.from_dict(lot_data)
            self._lots[ticker].append(lot)

    def clear_ticker(self, ticker: str) -> None:
        """
        Clear all lots for a ticker.

        Args:
            ticker: Asset symbol
        """
        if ticker in self._lots:
            del self._lots[ticker]

    def clear_all(self) -> None:
        """Clear all lots for all tickers"""
        self._lots.clear()
