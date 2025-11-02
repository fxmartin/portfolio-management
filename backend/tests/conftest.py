# ABOUTME: Pytest configuration and fixtures for test suite
# ABOUTME: Provides database setup, test client, and common fixtures

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ["SETTINGS_ENCRYPTION_KEY"] = "8LszS8I4wR1MMf5nj2yKDCx7USDTY0eITI9NGqgB_ns="

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

    # Create a mock Redis client
    class MockRedis:
        def __init__(self):
            self._store = {}

        async def get(self, key):
            return self._store.get(key)

        async def setex(self, key, ttl, value):
            self._store[key] = value
            return True

        async def delete(self, *keys):
            for key in keys:
                self._store.pop(key, None)
            return len(keys)

        async def close(self):
            pass

    mock_redis = MockRedis()

    # Override the dependencies
    app.dependency_overrides[get_async_db] = override_get_db

    # Override CacheService creation to use mock Redis
    from cache_service import CacheService
    original_init = CacheService.__init__

    def mock_cache_init(self):
        self.client = mock_redis

    CacheService.__init__ = mock_cache_init

    # Create test client
    with TestClient(app) as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
    CacheService.__init__ = original_init
