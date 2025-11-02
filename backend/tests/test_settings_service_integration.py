# ABOUTME: Integration tests for SettingsService with real database and Redis
# ABOUTME: Tests end-to-end workflows including encryption, validation, and caching

"""
Integration Tests for SettingsService (Epic 9 - F9.1-002)

Tests full workflows with real database:
- Seed → Get → Update → Verify
- Encryption roundtrips
- History tracking
- Cache invalidation
- Transaction rollback
- Type conversion
"""

import pytest
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import redis.asyncio as redis

from models import Base, ApplicationSetting, SettingHistory, SettingCategory
from settings_service import SettingsService
from security_utils import encrypt_value, decrypt_value


# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://trader:password@localhost:5432/portfolio_test"
)


@pytest.fixture
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def redis_client():
    """Create test Redis client"""
    client = redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        encoding="utf-8",
        decode_responses=True
    )

    # Clear test keys
    await client.flushdb()

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
async def service(db_session, redis_client):
    """Create SettingsService instance with test dependencies"""
    return SettingsService(db_session, redis_client)


@pytest.fixture
async def seed_settings(db_session):
    """Seed test settings"""
    settings = [
        ApplicationSetting(
            key="base_currency",
            value="USD",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            description="Base currency for portfolio display",
            default_value="EUR"
        ),
        ApplicationSetting(
            key="refresh_interval",
            value="60",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            description="Data refresh interval in seconds",
            default_value="60",
            validation_rules={
                "type": "integer",
                "minimum": 10,
                "maximum": 300
            }
        ),
        ApplicationSetting(
            key="anthropic_api_key",
            value=encrypt_value("sk-ant-test-key-123"),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Anthropic API key for AI analysis",
            default_value=None
        ),
        ApplicationSetting(
            key="system_version",
            value="1.0.0",
            category=SettingCategory.SYSTEM,
            is_sensitive=False,
            is_editable=False,
            description="System version (read-only)",
            default_value="1.0.0"
        ),
    ]

    for setting in settings:
        db_session.add(setting)

    await db_session.commit()

    return settings


class TestFullWorkflow:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_seed_get_update_verify(self, service, db_session, seed_settings):
        """Full workflow: seed → get → update → verify"""
        # Get initial value
        initial = await service.get_setting("base_currency")
        assert initial == "USD"

        # Update value
        await service.update_setting("base_currency", "EUR", "Test update")

        # Verify update
        updated = await service.get_setting("base_currency")
        assert updated == "EUR"

        # Verify history was recorded
        history = await service.get_history("base_currency")
        assert len(history) == 1
        assert history[0].old_value == "USD"
        assert history[0].new_value == "EUR"

    @pytest.mark.asyncio
    async def test_encryption_roundtrip(self, service, db_session, seed_settings):
        """Test encryption and decryption with real database"""
        # Get encrypted value (decrypted)
        decrypted = await service.get_setting("anthropic_api_key", decrypt=True)
        assert decrypted == "sk-ant-test-key-123"

        # Update with new key
        new_key = "sk-ant-new-key-456"
        await service.update_setting("anthropic_api_key", new_key)

        # Verify encryption
        result = await db_session.execute(
            select(ApplicationSetting).filter_by(key="anthropic_api_key")
        )
        setting = result.scalar_one()
        assert setting.value != new_key  # Should be encrypted in DB

        # Verify decryption works
        retrieved = await service.get_setting("anthropic_api_key", decrypt=True)
        assert retrieved == new_key

    @pytest.mark.asyncio
    async def test_history_tracking_endtoend(self, service, db_session, seed_settings):
        """Test history tracking through multiple updates"""
        # Make multiple updates
        await service.update_setting("base_currency", "EUR", "First change")
        await service.update_setting("base_currency", "GBP", "Second change")
        await service.update_setting("base_currency", "JPY", "Third change")

        # Get history
        history = await service.get_history("base_currency")

        # Verify all changes recorded
        assert len(history) == 3
        assert history[0].old_value == "USD"
        assert history[0].new_value == "EUR"
        assert history[1].old_value == "EUR"
        assert history[1].new_value == "GBP"
        assert history[2].old_value == "GBP"
        assert history[2].new_value == "JPY"

    @pytest.mark.asyncio
    async def test_cache_invalidation_with_real_redis(self, service, redis_client, seed_settings):
        """Test cache invalidation with real Redis"""
        # First get (cache miss)
        value1 = await service.get_setting("base_currency")
        assert value1 == "USD"

        # Check cache was set
        cached = await redis_client.get("setting:base_currency")
        assert cached is not None

        # Update setting
        await service.update_setting("base_currency", "EUR")

        # Check cache was invalidated
        cached_after = await redis_client.get("setting:base_currency")
        assert cached_after is None

        # Get again (should hit DB and re-cache)
        value2 = await service.get_setting("base_currency")
        assert value2 == "EUR"

    @pytest.mark.asyncio
    async def test_bulk_update_transaction_rollback(self, service, db_session, seed_settings):
        """Test transaction rollback on bulk update failure"""
        # Attempt bulk update with one invalid update
        updates = {
            "base_currency": "EUR",  # Valid
            "system_version": "2.0.0",  # Invalid (read-only)
        }

        # Should raise error
        with pytest.raises(ValueError, match="read-only"):
            await service.bulk_update(updates)

        # Verify no changes were committed
        currency = await service.get_setting("base_currency")
        version = await service.get_setting("system_version")

        assert currency == "USD"  # Should still be original value
        assert version == "1.0.0"  # Should still be original value

    @pytest.mark.asyncio
    async def test_category_filtering(self, service, seed_settings):
        """Test retrieving settings by category"""
        # Get all DISPLAY settings
        display_settings = await service.get_settings_by_category(SettingCategory.DISPLAY)

        assert len(display_settings) == 2
        assert "base_currency" in display_settings
        assert "refresh_interval" in display_settings
        assert display_settings["base_currency"] == "USD"
        assert display_settings["refresh_interval"] == 60  # Parsed to int

        # Get all API_KEYS settings
        api_settings = await service.get_settings_by_category(SettingCategory.API_KEYS, decrypt=True)

        assert len(api_settings) == 1
        assert "anthropic_api_key" in api_settings
        assert api_settings["anthropic_api_key"] == "sk-ant-test-key-123"

    @pytest.mark.asyncio
    async def test_type_conversion_with_real_data(self, service, db_session):
        """Test type conversion with real database data"""
        # Create settings with different types
        test_settings = [
            ApplicationSetting(
                key="test_int", value="42",
                category=SettingCategory.ADVANCED, is_sensitive=False
            ),
            ApplicationSetting(
                key="test_float", value="3.14",
                category=SettingCategory.ADVANCED, is_sensitive=False
            ),
            ApplicationSetting(
                key="test_bool_true", value="true",
                category=SettingCategory.ADVANCED, is_sensitive=False
            ),
            ApplicationSetting(
                key="test_bool_false", value="false",
                category=SettingCategory.ADVANCED, is_sensitive=False
            ),
            ApplicationSetting(
                key="test_json", value='{"nested": {"value": 123}}',
                category=SettingCategory.ADVANCED, is_sensitive=False
            ),
        ]

        for setting in test_settings:
            db_session.add(setting)
        await db_session.commit()

        # Test type conversion
        assert await service.get_setting("test_int") == 42
        assert await service.get_setting("test_float") == 3.14
        assert await service.get_setting("test_bool_true") is True
        assert await service.get_setting("test_bool_false") is False

        json_value = await service.get_setting("test_json")
        assert isinstance(json_value, dict)
        assert json_value["nested"]["value"] == 123

    @pytest.mark.asyncio
    async def test_validation_failure_scenarios(self, service, seed_settings):
        """Test various validation failure scenarios"""
        # Test 1: Value below minimum
        with pytest.raises(ValueError, match="Validation failed"):
            await service.update_setting("refresh_interval", 5)  # Below minimum 10

        # Test 2: Value above maximum
        with pytest.raises(ValueError, match="Validation failed"):
            await service.update_setting("refresh_interval", 500)  # Above maximum 300

        # Test 3: Wrong type
        with pytest.raises(ValueError, match="Validation failed"):
            await service.update_setting("refresh_interval", "not_a_number")

    @pytest.mark.asyncio
    async def test_reset_to_default_workflow(self, service, seed_settings):
        """Test reset to default workflow"""
        # Change value
        await service.update_setting("base_currency", "GBP")
        assert await service.get_setting("base_currency") == "GBP"

        # Reset to default
        await service.reset_to_default("base_currency")

        # Verify reset
        value = await service.get_setting("base_currency")
        assert value == "EUR"  # Default value

        # Verify history recorded reset
        history = await service.get_history("base_currency")
        assert len(history) == 2
        assert history[1].change_reason == "Reset to default"

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, db_engine, redis_client, seed_settings):
        """Test handling of concurrent updates (race condition test)"""
        # Create two service instances (simulating concurrent requests)
        async_session1 = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async_session2 = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session1() as session1, async_session2() as session2:
            service1 = SettingsService(session1, redis_client)
            service2 = SettingsService(session2, redis_client)

            # Both services update the same setting
            await service1.update_setting("base_currency", "EUR")
            await service2.update_setting("base_currency", "GBP")

            # Final value should be from the last update
            final_value = await service1.get_setting("base_currency")
            assert final_value in ["EUR", "GBP"]  # One should win

            # History should show both updates
            history = await service1.get_history("base_currency")
            assert len(history) >= 2


class TestBulkOperations:
    """Integration tests for bulk operations"""

    @pytest.mark.asyncio
    async def test_bulk_update_success(self, service, seed_settings):
        """Test successful bulk update"""
        updates = {
            "base_currency": "EUR",
            "refresh_interval": 120,
        }

        results = await service.bulk_update(updates, "Bulk configuration")

        # Verify updates
        assert len(results) == 2
        assert await service.get_setting("base_currency") == "EUR"
        assert await service.get_setting("refresh_interval") == 120

        # Verify history for both
        history1 = await service.get_history("base_currency")
        history2 = await service.get_history("refresh_interval")

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].change_reason == "Bulk configuration"
        assert history2[0].change_reason == "Bulk configuration"

    @pytest.mark.asyncio
    async def test_get_all_settings(self, service, seed_settings):
        """Test retrieving all settings across categories"""
        all_settings = await service.get_all_settings(decrypt=False)

        # Should have 4 settings from seed
        assert len(all_settings) >= 4
        assert "base_currency" in all_settings
        assert "refresh_interval" in all_settings
        assert "anthropic_api_key" in all_settings
        assert "system_version" in all_settings

        # API key should be encrypted
        assert all_settings["anthropic_api_key"] != "sk-ant-test-key-123"

        # Get with decryption
        all_decrypted = await service.get_all_settings(decrypt=True)
        assert all_decrypted["anthropic_api_key"] == "sk-ant-test-key-123"


class TestEdgeCases:
    """Integration tests for edge cases"""

    @pytest.mark.asyncio
    async def test_update_setting_with_none_value(self, service, db_session):
        """Test updating setting with None value"""
        setting = ApplicationSetting(
            key="nullable_setting",
            value="initial",
            category=SettingCategory.ADVANCED,
            is_sensitive=False,
            is_editable=True
        )
        db_session.add(setting)
        await db_session.commit()

        # Update to None
        await service.update_setting("nullable_setting", None)

        # Verify
        result = await service.get_setting("nullable_setting")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_setting_with_empty_string(self, service, db_session):
        """Test getting setting with empty string value"""
        setting = ApplicationSetting(
            key="empty_setting",
            value="",
            category=SettingCategory.ADVANCED,
            is_sensitive=False
        )
        db_session.add(setting)
        await db_session.commit()

        result = await service.get_setting("empty_setting")
        assert result == ""

    @pytest.mark.asyncio
    async def test_history_limit(self, service, db_session, seed_settings):
        """Test history retrieval with limit parameter"""
        # Make 10 updates
        for i in range(10):
            await service.update_setting("base_currency", f"CUR{i}")

        # Get limited history
        history = await service.get_history("base_currency", limit=5)

        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, service, redis_client, seed_settings):
        """Test cache TTL behavior (manual TTL verification)"""
        # Get setting (caches it)
        value = await service.get_setting("base_currency")
        assert value == "USD"

        # Check TTL was set
        ttl = await redis_client.ttl("setting:base_currency")
        assert ttl > 0
        assert ttl <= 300  # Should be 5 minutes or less
