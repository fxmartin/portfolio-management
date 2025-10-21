# ABOUTME: SQLAlchemy database models for portfolio management
# ABOUTME: Defines Transaction, Position, PriceHistory, and PortfolioSnapshot tables

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Index, UniqueConstraint, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class AssetType(str, enum.Enum):
    """Asset type enumeration"""
    METAL = "METAL"
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"


class TransactionType(str, enum.Enum):
    """Transaction type enumeration"""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    STAKING = "STAKING"
    FEE = "FEE"
    TRANSFER = "TRANSFER"
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"


class Transaction(Base):
    """Transaction model for storing all imported transactions"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)  # XAU, AAPL, BTC, etc.
    quantity = Column(Numeric(18, 8))
    price_per_unit = Column(Numeric(18, 8))
    total_amount = Column(Numeric(18, 8))
    currency = Column(String(3), default='USD')
    fee = Column(Numeric(18, 8), default=0)
    cost_basis = Column(Numeric(18, 8))  # For crypto from Koinly
    tax_lot_id = Column(String(100))  # For tax tracking
    raw_data = Column(JSON)  # Original CSV row for audit
    source_file = Column(String(255), index=True)
    source_type = Column(String(10))  # REVOLUT, KOINLY
    import_timestamp = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationships
    positions = relationship("Position", back_populates="transaction")

    __table_args__ = (
        UniqueConstraint('transaction_date', 'symbol', 'quantity', 'transaction_type', 'asset_type',
                        name='uix_transaction_unique'),
        Index('idx_transactions_date_symbol', 'transaction_date', 'symbol'),
    )

    def __repr__(self):
        return f"<Transaction({self.transaction_date}, {self.symbol}, {self.transaction_type}, {self.quantity})>"


class Position(Base):
    """Position model for tracking current holdings"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)
    avg_cost_basis = Column(Numeric(18, 8))
    total_cost_basis = Column(Numeric(18, 8))
    currency = Column(String(3), default='USD')
    first_purchase_date = Column(DateTime)
    last_transaction_date = Column(DateTime)

    # FIFO queue for cost basis tracking (JSON array of lots)
    # Each lot: {"quantity": x, "cost": y, "date": z, "transaction_id": id}
    cost_lots = Column(JSON)

    # Current market data (updated separately)
    current_price = Column(Numeric(18, 8))
    current_value = Column(Numeric(18, 8))
    unrealized_pnl = Column(Numeric(18, 8))
    unrealized_pnl_percent = Column(Numeric(6, 2))
    last_price_update = Column(DateTime)

    # Foreign keys
    transaction_id = Column(Integer, ForeignKey('transactions.id'))

    # Relationships
    transaction = relationship("Transaction", back_populates="positions")
    price_history = relationship("PriceHistory", back_populates="position")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Position({self.symbol}, qty={self.quantity}, value={self.current_value})>"


class PriceHistory(Base):
    """Price history model for storing historical price data"""
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    price_date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Numeric(18, 8))
    high_price = Column(Numeric(18, 8))
    low_price = Column(Numeric(18, 8))
    close_price = Column(Numeric(18, 8))
    volume = Column(Numeric(18, 0))
    currency = Column(String(3), default='USD')
    source = Column(String(20))  # YAHOO, MANUAL, etc.

    # Foreign keys
    position_id = Column(Integer, ForeignKey('positions.id'))

    # Relationships
    position = relationship("Position", back_populates="price_history")

    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'price_date', 'source',
                        name='uix_price_history_unique'),
        Index('idx_price_history_symbol_date', 'symbol', 'price_date'),
    )

    def __repr__(self):
        return f"<PriceHistory({self.symbol}, {self.price_date}, {self.close_price})>"


class PortfolioSnapshot(Base):
    """Portfolio snapshot model for tracking portfolio value over time"""
    __tablename__ = 'portfolio_snapshots'

    id = Column(Integer, primary_key=True)
    snapshot_date = Column(DateTime, nullable=False, unique=True, index=True)
    total_value = Column(Numeric(18, 2), nullable=False)
    cash_balance = Column(Numeric(18, 2), default=0)
    invested_value = Column(Numeric(18, 2))
    total_cost_basis = Column(Numeric(18, 2))
    total_unrealized_pnl = Column(Numeric(18, 2))
    total_unrealized_pnl_percent = Column(Numeric(6, 2))
    total_realized_pnl = Column(Numeric(18, 2))

    # Position details at time of snapshot (JSON)
    # Array of: {"symbol": x, "quantity": y, "value": z, "pnl": a}
    positions_snapshot = Column(JSON)

    # Asset allocation percentages
    metals_percent = Column(Numeric(5, 2))
    stocks_percent = Column(Numeric(5, 2))
    crypto_percent = Column(Numeric(5, 2))
    cash_percent = Column(Numeric(5, 2))

    currency = Column(String(3), default='USD')
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<PortfolioSnapshot({self.snapshot_date}, value={self.total_value})>"


# Create indexes for better query performance
Index('idx_transactions_import', Transaction.__table__.c.import_timestamp)
Index('idx_positions_symbol_type', Position.__table__.c.symbol, Position.__table__.c.asset_type)
Index('idx_portfolio_snapshots_date', PortfolioSnapshot.__table__.c.snapshot_date.desc())