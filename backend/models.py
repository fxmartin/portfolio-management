# ABOUTME: SQLAlchemy database models for portfolio management
# ABOUTME: Defines Transaction, Position, PriceHistory, PortfolioSnapshot, Prompt, PromptVersion, and AnalysisResult tables

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Index, UniqueConstraint, JSON, Enum, Text, Boolean
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
    AIRDROP = "AIRDROP"
    MINING = "MINING"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


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
    source = Column(String(20), default='CSV', index=True)  # CSV or MANUAL
    notes = Column(String(500))  # User notes for manual transactions
    deleted_at = Column(DateTime)  # Soft delete timestamp
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


class TransactionAudit(Base):
    """Transaction audit log for tracking changes to transactions"""
    __tablename__ = 'transaction_audit'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False, index=True)
    changed_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    changed_by = Column(String(100), default='system')
    old_values = Column(JSON)  # Previous values
    new_values = Column(JSON)  # New values
    change_reason = Column(String(500))
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, RESTORE

    __table_args__ = (
        Index('idx_audit_transaction_date', 'transaction_id', 'changed_at'),
    )

    def __repr__(self):
        return f"<TransactionAudit(tx_id={self.transaction_id}, action={self.action}, at={self.changed_at})>"


class Position(Base):
    """Position model for tracking current holdings"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    asset_name = Column(String(255))  # Full name (e.g., "MicroStrategy", "Bitcoin")
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


class Prompt(Base):
    """Prompt template model for AI analysis prompts"""
    __tablename__ = 'prompts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # 'global', 'position', 'forecast'
    prompt_text = Column(String, nullable=False)  # TEXT in PostgreSQL
    template_variables = Column(JSON)  # {var_name: type}
    is_active = Column(Integer, default=1)  # Using Integer for SQLite compatibility
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    versions = relationship("PromptVersion", back_populates="prompt")
    analysis_results = relationship("AnalysisResult", back_populates="prompt")

    def __repr__(self):
        return f"<Prompt({self.name}, v{self.version}, active={bool(self.is_active)})>"


class PromptVersion(Base):
    """Prompt version history model for tracking prompt changes"""
    __tablename__ = 'prompt_versions'

    id = Column(Integer, primary_key=True)
    prompt_id = Column(Integer, ForeignKey('prompts.id'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    prompt_text = Column(String, nullable=False)  # TEXT in PostgreSQL
    changed_by = Column(String(100))
    changed_at = Column(DateTime, default=func.now(), nullable=False)
    change_reason = Column(String)  # TEXT in PostgreSQL

    # Relationships
    prompt = relationship("Prompt", back_populates="versions")

    def __repr__(self):
        return f"<PromptVersion(prompt_id={self.prompt_id}, v{self.version})>"


class AnalysisResult(Base):
    """Analysis result model for storing AI-generated analysis"""
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True)
    analysis_type = Column(String(50), nullable=False, index=True)  # 'global', 'position', 'forecast'
    symbol = Column(String(20), index=True)  # NULL for global analysis
    prompt_id = Column(Integer, ForeignKey('prompts.id'))
    prompt_version = Column(Integer)
    raw_response = Column(String, nullable=False)  # TEXT in PostgreSQL
    parsed_data = Column(JSON)  # Structured analysis data
    tokens_used = Column(Integer)
    generation_time_ms = Column(Integer)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime)  # For caching/cleanup

    # Relationships
    prompt = relationship("Prompt", back_populates="analysis_results")

    __table_args__ = (
        Index('idx_analysis_type_symbol', 'analysis_type', 'symbol'),
        Index('idx_analysis_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AnalysisResult({self.analysis_type}, symbol={self.symbol}, tokens={self.tokens_used})>"


class InvestmentStrategy(Base):
    """Investment strategy model for storing user investment goals and constraints (Epic 8 - F8.8)"""
    __tablename__ = 'investment_strategy'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    strategy_text = Column(String, nullable=False)  # TEXT in PostgreSQL
    target_annual_return = Column(Numeric(5, 2))  # e.g., 12.50%
    risk_tolerance = Column(String(10))  # LOW, MEDIUM, HIGH, CUSTOM
    time_horizon_years = Column(Integer)  # e.g., 10 years
    max_positions = Column(Integer)  # e.g., 15 positions
    profit_taking_threshold = Column(Numeric(5, 2))  # e.g., 25.00%
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1, nullable=False)

    def __repr__(self):
        return f"<InvestmentStrategy(user_id={self.user_id}, v{self.version})>"


class SettingCategory(str, enum.Enum):
    """Setting category enumeration for organizing application settings (Epic 9)"""
    DISPLAY = "display"
    API_KEYS = "api_keys"
    PROMPTS = "prompts"
    SYSTEM = "system"
    ADVANCED = "advanced"


class ApplicationSetting(Base):
    """Application settings model for storing configuration (Epic 9 - F9.1-001)"""
    __tablename__ = 'application_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # JSON string for complex values
    category = Column(Enum(SettingCategory), nullable=False, index=True)
    is_sensitive = Column(Boolean, default=False)  # Encrypted if True
    is_editable = Column(Boolean, default=True)  # Some settings are read-only
    description = Column(Text, nullable=True)
    default_value = Column(Text, nullable=True)
    validation_rules = Column(JSON, nullable=True)  # JSON schema for validation
    last_modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_settings_category', 'category'),
    )

    def __repr__(self):
        return f"<ApplicationSetting(key={self.key}, category={self.category.value})>"


class SettingHistory(Base):
    """Setting change history model for audit trail (Epic 9 - F9.1-001)"""
    __tablename__ = 'setting_history'

    id = Column(Integer, primary_key=True)
    setting_id = Column(Integer, ForeignKey('application_settings.id'), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(100), default='system')  # Future: user tracking
    changed_at = Column(DateTime, default=func.now())
    change_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_setting_history_setting', 'setting_id', 'changed_at'),
    )

    def __repr__(self):
        return f"<SettingHistory(setting_id={self.setting_id}, at={self.changed_at})>"


# Create indexes for better query performance
Index('idx_transactions_import', Transaction.__table__.c.import_timestamp)
Index('idx_positions_symbol_type', Position.__table__.c.symbol, Position.__table__.c.asset_type)
Index('idx_portfolio_snapshots_date', PortfolioSnapshot.__table__.c.snapshot_date.desc())