# ABOUTME: Database connection manager and session handling
# ABOUTME: Provides async database operations and connection pooling

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import AsyncGenerator

from models import Base

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://trader:profits123@postgres:5432/portfolio"
)

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Sync engine for migrations and initial setup
engine = create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1),
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

# Async engine for FastAPI operations
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL debugging
    poolclass=NullPool  # Good for containerized apps
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def init_db():
    """Initialize database tables (synchronous)"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False


async def init_db_async():
    """Initialize database tables (asynchronous)"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully (async)")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False


@contextmanager
def get_db_context():
    """Context manager for synchronous database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    """Dependency for FastAPI synchronous database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def test_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


# Helper functions for common operations
async def bulk_insert_transactions(transactions: list, session: AsyncSession):
    """Bulk insert transactions"""
    try:
        session.add_all(transactions)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        print(f"Error bulk inserting transactions: {e}")
        return False


async def get_or_create_position(symbol: str, asset_type: str, session: AsyncSession):
    """Get existing position or create new one"""
    from sqlalchemy import select
    from models import Position

    stmt = select(Position).where(
        Position.symbol == symbol,
        Position.asset_type == asset_type
    )
    result = await session.execute(stmt)
    position = result.scalar_one_or_none()

    if not position:
        position = Position(
            symbol=symbol,
            asset_type=asset_type,
            quantity=0,
            cost_lots=[]
        )
        session.add(position)

    return position