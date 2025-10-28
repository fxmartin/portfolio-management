# ABOUTME: Pytest configuration and fixtures for test suite
# ABOUTME: Provides database setup, test client, and common fixtures

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base
from database import get_async_db
from main import app


# Test database URL - use in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    """Create a test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def test_client(test_session):
    """Create a test client with overridden database dependency"""

    async def override_get_db():
        """Override database dependency to use test session"""
        yield test_session

    # Override the dependency
    app.dependency_overrides[get_async_db] = override_get_db

    # Create test client
    with TestClient(app) as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
