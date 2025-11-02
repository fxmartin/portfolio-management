# ABOUTME: Integration tests for settings database schema and seed data
# ABOUTME: Tests schema creation, seeding, and integration with real database

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os

from models import Base, ApplicationSetting, SettingHistory, SettingCategory
from seed_settings import seed_settings, DEFAULT_SETTINGS


@pytest_asyncio.fixture(scope="function")
async def integration_engine():
    """Create a fresh test database engine for integration tests"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def integration_session(integration_engine):
    """Create a test session for integration tests"""
    async_session = async_sessionmaker(
        integration_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


class TestSchemaCreation:
    """Test database schema creation"""

    @pytest.mark.asyncio
    async def test_application_settings_table_exists(self, integration_session):
        """Test that application_settings table is created"""
        # Try to query the table
        result = await integration_session.execute(select(ApplicationSetting))
        settings = result.scalars().all()

        # Should exist and be empty
        assert settings is not None
        assert len(settings) == 0

    @pytest.mark.asyncio
    async def test_setting_history_table_exists(self, integration_session):
        """Test that setting_history table is created"""
        result = await integration_session.execute(select(SettingHistory))
        history = result.scalars().all()

        assert history is not None
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_schema_has_correct_indexes(self, integration_engine):
        """Test that indexes are created correctly"""
        async with integration_engine.connect() as conn:
            # Check if indexes exist (SQLite specific)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='application_settings'")
            )
            indexes = [row[0] for row in result]

            # Should have index on key
            assert any('key' in idx.lower() for idx in indexes)


class TestSeedSettings:
    """Test settings seeding functionality"""

    @pytest.mark.asyncio
    async def test_seed_creates_all_default_settings(self, integration_session):
        """Test that seeding creates all 12 default settings"""
        created_count = await seed_settings(integration_session)

        assert created_count == 12

        # Verify all settings exist
        result = await integration_session.execute(select(ApplicationSetting))
        settings = result.scalars().all()

        assert len(settings) == 12

    @pytest.mark.asyncio
    async def test_seed_creates_correct_categories(self, integration_session):
        """Test that settings are created in correct categories"""
        await seed_settings(integration_session)

        # Check each category
        for category in SettingCategory:
            result = await integration_session.execute(
                select(ApplicationSetting).filter_by(category=category)
            )
            settings = result.scalars().all()

            # Each category should have at least one setting
            if category == SettingCategory.DISPLAY:
                assert len(settings) == 3
            elif category == SettingCategory.API_KEYS:
                assert len(settings) == 2
            elif category == SettingCategory.PROMPTS:
                assert len(settings) == 3
            elif category == SettingCategory.SYSTEM:
                assert len(settings) == 3
            elif category == SettingCategory.ADVANCED:
                assert len(settings) == 1

    @pytest.mark.asyncio
    async def test_seed_sets_validation_rules(self, integration_session):
        """Test that validation rules are properly stored"""
        await seed_settings(integration_session)

        # Check a setting with validation rules
        result = await integration_session.execute(
            select(ApplicationSetting).filter_by(key="base_currency")
        )
        setting = result.scalar_one()

        assert setting.validation_rules is not None
        assert "enum" in setting.validation_rules
        assert "EUR" in setting.validation_rules["enum"]

    @pytest.mark.asyncio
    async def test_seed_marks_sensitive_settings(self, integration_session):
        """Test that sensitive settings are marked correctly"""
        await seed_settings(integration_session)

        # API keys should be sensitive
        result = await integration_session.execute(
            select(ApplicationSetting).filter_by(key="anthropic_api_key")
        )
        setting = result.scalar_one()

        assert setting.is_sensitive is True

        # Display settings should not be sensitive
        result = await integration_session.execute(
            select(ApplicationSetting).filter_by(key="base_currency")
        )
        setting = result.scalar_one()

        assert setting.is_sensitive is False

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, integration_session):
        """Test that seeding twice doesn't create duplicates"""
        # Seed first time
        first_count = await seed_settings(integration_session)
        assert first_count == 12

        # Seed second time
        second_count = await seed_settings(integration_session)
        assert second_count == 0  # No new settings created

        # Verify total count
        result = await integration_session.execute(select(ApplicationSetting))
        settings = result.scalars().all()
        assert len(settings) == 12

    @pytest.mark.asyncio
    async def test_seed_default_values_match(self, integration_session):
        """Test that seeded values match default values"""
        await seed_settings(integration_session)

        for default_setting in DEFAULT_SETTINGS:
            result = await integration_session.execute(
                select(ApplicationSetting).filter_by(key=default_setting["key"])
            )
            setting = result.scalar_one()

            assert setting.value == default_setting["value"]
            assert setting.default_value == default_setting["default_value"]
            assert setting.category == default_setting["category"]


class TestSettingsIntegration:
    """Test integrated functionality of settings tables"""

    @pytest.mark.asyncio
    async def test_create_setting_and_history(self, integration_session):
        """Test creating a setting and its history entry"""
        # Create setting
        setting = ApplicationSetting(
            key="test_setting",
            value="initial",
            category=SettingCategory.SYSTEM
        )
        integration_session.add(setting)
        await integration_session.commit()
        await integration_session.refresh(setting)

        # Create history
        history = SettingHistory(
            setting_id=setting.id,
            old_value="initial",
            new_value="updated",
            change_reason="test update"
        )
        integration_session.add(history)
        await integration_session.commit()

        # Verify both exist
        result = await integration_session.execute(
            select(SettingHistory).filter_by(setting_id=setting.id)
        )
        saved_history = result.scalar_one()

        assert saved_history.setting_id == setting.id
        assert saved_history.new_value == "updated"

    @pytest.mark.asyncio
    async def test_query_settings_by_category(self, integration_session):
        """Test querying settings by category"""
        await seed_settings(integration_session)

        # Query display settings
        result = await integration_session.execute(
            select(ApplicationSetting).filter_by(category=SettingCategory.DISPLAY)
        )
        display_settings = result.scalars().all()

        assert len(display_settings) == 3
        assert all(s.category == SettingCategory.DISPLAY for s in display_settings)

    @pytest.mark.asyncio
    async def test_update_setting_preserves_metadata(self, integration_session):
        """Test that updating a setting preserves metadata"""
        await seed_settings(integration_session)

        # Get setting
        result = await integration_session.execute(
            select(ApplicationSetting).filter_by(key="base_currency")
        )
        setting = result.scalar_one()

        # Store original metadata
        original_description = setting.description
        original_validation = setting.validation_rules

        # Update value
        setting.value = "USD"
        await integration_session.commit()

        # Refresh and verify metadata preserved
        await integration_session.refresh(setting)
        assert setting.description == original_description
        assert setting.validation_rules == original_validation
        assert setting.value == "USD"

    @pytest.mark.asyncio
    async def test_nullable_api_keys(self, integration_session):
        """Test that API keys can be null (not set)"""
        await seed_settings(integration_session)

        result = await integration_session.execute(
            select(ApplicationSetting).filter_by(key="anthropic_api_key")
        )
        setting = result.scalar_one()

        assert setting.value is None
        assert setting.is_sensitive is True

    @pytest.mark.asyncio
    async def test_all_default_settings_valid(self, integration_session):
        """Test that all default settings have required fields"""
        await seed_settings(integration_session)

        result = await integration_session.execute(select(ApplicationSetting))
        settings = result.scalars().all()

        for setting in settings:
            # All must have key, category, description
            assert setting.key is not None
            assert setting.category is not None
            assert setting.description is not None

            # All must have validation rules
            assert setting.validation_rules is not None

            # is_sensitive and is_editable must be set
            assert setting.is_sensitive is not None
            assert setting.is_editable is not None
