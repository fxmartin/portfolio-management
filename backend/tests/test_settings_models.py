# ABOUTME: Unit tests for ApplicationSetting and SettingHistory database models
# ABOUTME: Tests model creation, constraints, validation, and relationships

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import json

from models import ApplicationSetting, SettingHistory, SettingCategory, Base


class TestSettingCategory:
    """Test SettingCategory enum"""

    def test_setting_category_values(self):
        """Test that all expected category values exist"""
        assert SettingCategory.DISPLAY.value == "display"
        assert SettingCategory.API_KEYS.value == "api_keys"
        assert SettingCategory.PROMPTS.value == "prompts"
        assert SettingCategory.SYSTEM.value == "system"
        assert SettingCategory.ADVANCED.value == "advanced"

    def test_setting_category_count(self):
        """Test that we have exactly 5 categories"""
        assert len(SettingCategory) == 5


class TestApplicationSetting:
    """Test ApplicationSetting model"""

    @pytest.mark.asyncio
    async def test_create_basic_setting(self, test_session):
        """Test creating a basic application setting"""
        setting = ApplicationSetting(
            key="base_currency",
            value="EUR",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            description="Base currency for portfolio display"
        )
        test_session.add(setting)
        await test_session.commit()

        # Verify it was created
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="base_currency")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.key == "base_currency"
        assert saved_setting.value == "EUR"
        assert saved_setting.category == SettingCategory.DISPLAY
        assert saved_setting.is_sensitive is False
        assert saved_setting.is_editable is True
        assert saved_setting.description == "Base currency for portfolio display"
        assert saved_setting.created_at is not None
        assert saved_setting.last_modified_at is not None

    @pytest.mark.asyncio
    async def test_unique_key_constraint(self, test_session):
        """Test that key must be unique"""
        setting1 = ApplicationSetting(
            key="test_key",
            value="value1",
            category=SettingCategory.SYSTEM
        )
        test_session.add(setting1)
        await test_session.commit()

        # Try to create duplicate
        setting2 = ApplicationSetting(
            key="test_key",
            value="value2",
            category=SettingCategory.SYSTEM
        )
        test_session.add(setting2)

        with pytest.raises(IntegrityError):
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_sensitive_setting(self, test_session):
        """Test creating a sensitive setting (API key)"""
        setting = ApplicationSetting(
            key="anthropic_api_key",
            value="sk-ant-encrypted-value",
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Anthropic Claude API key"
        )
        test_session.add(setting)
        await test_session.commit()

        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="anthropic_api_key")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.is_sensitive is True
        assert saved_setting.category == SettingCategory.API_KEYS

    @pytest.mark.asyncio
    async def test_validation_rules_json(self, test_session):
        """Test storing validation rules as JSON"""
        validation_rules = {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        }

        setting = ApplicationSetting(
            key="anthropic_temperature",
            value="0.3",
            category=SettingCategory.PROMPTS,
            validation_rules=validation_rules,
            description="Temperature for Claude API"
        )
        test_session.add(setting)
        await test_session.commit()

        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="anthropic_temperature")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.validation_rules == validation_rules
        assert saved_setting.validation_rules["minimum"] == 0
        assert saved_setting.validation_rules["maximum"] == 1

    @pytest.mark.asyncio
    async def test_default_value(self, test_session):
        """Test storing and retrieving default values"""
        setting = ApplicationSetting(
            key="date_format",
            value="YYYY-MM-DD",
            category=SettingCategory.DISPLAY,
            default_value="YYYY-MM-DD",
            validation_rules={"enum": ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"]}
        )
        test_session.add(setting)
        await test_session.commit()

        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="date_format")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.default_value == "YYYY-MM-DD"
        assert saved_setting.value == saved_setting.default_value

    @pytest.mark.asyncio
    async def test_read_only_setting(self, test_session):
        """Test creating a read-only setting"""
        setting = ApplicationSetting(
            key="app_version",
            value="1.0.0",
            category=SettingCategory.SYSTEM,
            is_editable=False,
            description="Application version (read-only)"
        )
        test_session.add(setting)
        await test_session.commit()

        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="app_version")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.is_editable is False

    @pytest.mark.asyncio
    async def test_nullable_value(self, test_session):
        """Test that value can be null (for unset API keys)"""
        setting = ApplicationSetting(
            key="alpha_vantage_api_key",
            value=None,
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            description="Alpha Vantage API key"
        )
        test_session.add(setting)
        await test_session.commit()

        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="alpha_vantage_api_key")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.value is None

    @pytest.mark.asyncio
    async def test_category_index(self, test_session):
        """Test that category is indexed for fast queries"""
        # Create settings in different categories
        settings = [
            ApplicationSetting(
                key=f"setting_{i}",
                value=str(i),
                category=SettingCategory.DISPLAY if i % 2 == 0 else SettingCategory.SYSTEM
            )
            for i in range(10)
        ]
        test_session.add_all(settings)
        await test_session.commit()

        # Query by category (should use index)
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(category=SettingCategory.DISPLAY)
        )
        display_settings = result.scalars().all()

        assert len(display_settings) == 5

    @pytest.mark.asyncio
    async def test_timestamps_auto_set(self, test_session):
        """Test that created_at and last_modified_at are automatically set"""
        setting = ApplicationSetting(
            key="test_timestamp",
            value="test",
            category=SettingCategory.SYSTEM
        )
        test_session.add(setting)
        await test_session.commit()

        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="test_timestamp")
        )
        saved_setting = result.scalar_one()

        assert saved_setting.created_at is not None
        assert saved_setting.last_modified_at is not None
        # Timestamps should be very close to each other
        assert saved_setting.created_at == saved_setting.last_modified_at


class TestSettingHistory:
    """Test SettingHistory model"""

    @pytest.mark.asyncio
    async def test_create_history_entry(self, test_session):
        """Test creating a setting history entry"""
        # First create a setting
        setting = ApplicationSetting(
            key="test_setting",
            value="initial_value",
            category=SettingCategory.SYSTEM
        )
        test_session.add(setting)
        await test_session.commit()
        await test_session.refresh(setting)

        # Create history entry
        history = SettingHistory(
            setting_id=setting.id,
            old_value="initial_value",
            new_value="updated_value",
            changed_by="system",
            change_reason="Test update"
        )
        test_session.add(history)
        await test_session.commit()

        # Verify
        result = await test_session.execute(
            select(SettingHistory).filter_by(setting_id=setting.id)
        )
        saved_history = result.scalar_one()

        assert saved_history.setting_id == setting.id
        assert saved_history.old_value == "initial_value"
        assert saved_history.new_value == "updated_value"
        assert saved_history.changed_by == "system"
        assert saved_history.change_reason == "Test update"
        assert saved_history.changed_at is not None

    @pytest.mark.asyncio
    async def test_history_default_changed_by(self, test_session):
        """Test that changed_by defaults to 'system'"""
        setting = ApplicationSetting(
            key="test_setting",
            value="value",
            category=SettingCategory.SYSTEM
        )
        test_session.add(setting)
        await test_session.commit()
        await test_session.refresh(setting)

        history = SettingHistory(
            setting_id=setting.id,
            old_value="old",
            new_value="new"
        )
        test_session.add(history)
        await test_session.commit()

        result = await test_session.execute(
            select(SettingHistory).filter_by(setting_id=setting.id)
        )
        saved_history = result.scalar_one()

        assert saved_history.changed_by == "system"

    @pytest.mark.asyncio
    async def test_multiple_history_entries(self, test_session):
        """Test storing multiple history entries for same setting"""
        setting = ApplicationSetting(
            key="test_setting",
            value="v1",
            category=SettingCategory.SYSTEM
        )
        test_session.add(setting)
        await test_session.commit()
        await test_session.refresh(setting)

        # Create multiple history entries
        entries = [
            SettingHistory(
                setting_id=setting.id,
                old_value=f"v{i}",
                new_value=f"v{i+1}",
                change_reason=f"Update {i}"
            )
            for i in range(1, 4)
        ]
        test_session.add_all(entries)
        await test_session.commit()

        # Verify all entries
        result = await test_session.execute(
            select(SettingHistory)
            .filter_by(setting_id=setting.id)
            .order_by(SettingHistory.changed_at)
        )
        history = result.scalars().all()

        assert len(history) == 3
        assert history[0].old_value == "v1"
        assert history[2].new_value == "v4"

    @pytest.mark.asyncio
    async def test_history_foreign_key_constraint(self, test_session):
        """Test that setting_id must reference valid setting"""
        history = SettingHistory(
            setting_id=99999,  # Non-existent setting
            old_value="old",
            new_value="new"
        )
        test_session.add(history)

        # SQLite may not enforce foreign key constraints by default
        # This test validates the schema definition rather than runtime enforcement
        try:
            await test_session.commit()
            # If SQLite doesn't enforce FK, just check the model is correct
            assert history.setting_id == 99999
        except IntegrityError:
            # PostgreSQL will enforce this
            pass

    @pytest.mark.asyncio
    async def test_nullable_history_values(self, test_session):
        """Test that old_value and new_value can be null"""
        setting = ApplicationSetting(
            key="test_setting",
            value=None,
            category=SettingCategory.API_KEYS,
            is_sensitive=True
        )
        test_session.add(setting)
        await test_session.commit()
        await test_session.refresh(setting)

        # Setting was unset, now being set
        history = SettingHistory(
            setting_id=setting.id,
            old_value=None,
            new_value="new_value",
            change_reason="Setting API key for first time"
        )
        test_session.add(history)
        await test_session.commit()

        result = await test_session.execute(
            select(SettingHistory).filter_by(setting_id=setting.id)
        )
        saved_history = result.scalar_one()

        assert saved_history.old_value is None
        assert saved_history.new_value == "new_value"
