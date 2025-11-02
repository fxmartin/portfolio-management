# ABOUTME: Unit tests for SettingsService business logic layer
# ABOUTME: Tests CRUD operations, encryption, validation, caching, and audit trail

"""
Unit Tests for SettingsService (Epic 9 - F9.1-002)

Tests all core functionality:
- Setting retrieval with decryption
- Category filtering
- Update with validation
- Bulk operations
- History tracking
- Type parsing
- Cache integration
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession
import json

from settings_service import SettingsService
from models import ApplicationSetting, SettingHistory, SettingCategory
from security_utils import encrypt_value


def create_mock_db_result(return_value):
    """Helper to create properly mocked database result"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=return_value)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=return_value)))
    return mock_result


class TestGetSetting:
    """Tests for get_setting method"""

    @pytest.mark.asyncio
    async def test_get_existing_setting(self):
        """Should retrieve existing setting and parse type"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.setex = AsyncMock()

        setting = ApplicationSetting(
            key="base_currency",
            value="EUR",
            category=SettingCategory.DISPLAY,
            is_sensitive=False
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_setting("base_currency")

        # Assert
        assert result == "EUR"
        mock_db.execute.assert_called_once()
        mock_cache.get.assert_called_once_with("setting:base_currency")
        mock_cache.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_nonexistent_setting(self):
        """Should return None for non-existent setting"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(None))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_setting("nonexistent_key")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_sensitive_setting_with_decrypt(self):
        """Should decrypt sensitive setting when decrypt=True"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.setex = AsyncMock()

        plain_value = "sk-ant-api-key-123"
        encrypted = encrypt_value(plain_value)

        setting = ApplicationSetting(
            key="anthropic_api_key",
            value=encrypted,
            category=SettingCategory.API_KEYS,
            is_sensitive=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_setting("anthropic_api_key", decrypt=True)

        # Assert
        assert result == plain_value

    @pytest.mark.asyncio
    async def test_get_sensitive_setting_without_decrypt(self):
        """Should return encrypted value when decrypt=False"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.setex = AsyncMock()

        plain_value = "sk-ant-api-key-123"
        encrypted = encrypt_value(plain_value)

        setting = ApplicationSetting(
            key="anthropic_api_key",
            value=encrypted,
            category=SettingCategory.API_KEYS,
            is_sensitive=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_setting("anthropic_api_key", decrypt=False)

        # Assert
        assert result == encrypted
        assert result != plain_value

    @pytest.mark.asyncio
    async def test_get_setting_cache_hit(self):
        """Should return cached value without database query"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=json.dumps("EUR"))

        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_setting("base_currency")

        # Assert
        assert result == "EUR"
        mock_db.execute.assert_not_called()  # Should not hit database

    @pytest.mark.asyncio
    async def test_get_setting_type_parsing(self):
        """Should parse values to correct types"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.setex = AsyncMock()

        test_cases = [
            ("60", 60, "integer"),
            ("true", True, "boolean_true"),
            ("false", False, "boolean_false"),
            ("0.3", 0.3, "float"),
            ('{"foo": "bar"}', {"foo": "bar"}, "json_object"),
            ("plain string", "plain string", "string"),
        ]

        service = SettingsService(mock_db, mock_cache)

        for value_str, expected, key_suffix in test_cases:
            setting = ApplicationSetting(
                key=f"test_{key_suffix}",
                value=value_str,
                category=SettingCategory.SYSTEM,
                is_sensitive=False
            )

            mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))

            # Act
            result = await service.get_setting(f"test_{key_suffix}")

            # Assert
            assert result == expected, f"Failed for {key_suffix}: expected {expected}, got {result}"


class TestGetSettingsByCategory:
    """Tests for get_settings_by_category method"""

    @pytest.mark.asyncio
    async def test_get_all_display_settings(self):
        """Should retrieve all settings in DISPLAY category"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        settings = [
            ApplicationSetting(key="base_currency", value="EUR", category=SettingCategory.DISPLAY, is_sensitive=False),
            ApplicationSetting(key="refresh_interval", value="60", category=SettingCategory.DISPLAY, is_sensitive=False),
        ]

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(settings))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_settings_by_category(SettingCategory.DISPLAY)

        # Assert
        assert len(result) == 2
        assert result["base_currency"] == "EUR"
        assert result["refresh_interval"] == 60  # Parsed to int

    @pytest.mark.asyncio
    async def test_get_api_keys_with_decrypt(self):
        """Should decrypt API keys when decrypt=True"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        plain_key = "sk-ant-123"
        encrypted = encrypt_value(plain_key)

        settings = [
            ApplicationSetting(
                key="anthropic_api_key",
                value=encrypted,
                category=SettingCategory.API_KEYS,
                is_sensitive=True
            ),
        ]

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(settings))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_settings_by_category(SettingCategory.API_KEYS, decrypt=True)

        # Assert
        assert result["anthropic_api_key"] == plain_key

    @pytest.mark.asyncio
    async def test_get_api_keys_without_decrypt(self):
        """Should keep API keys encrypted when decrypt=False"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        plain_key = "sk-ant-123"
        encrypted = encrypt_value(plain_key)

        settings = [
            ApplicationSetting(
                key="anthropic_api_key",
                value=encrypted,
                category=SettingCategory.API_KEYS,
                is_sensitive=True
            ),
        ]

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(settings))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_settings_by_category(SettingCategory.API_KEYS, decrypt=False)

        # Assert
        assert result["anthropic_api_key"] == encrypted
        assert result["anthropic_api_key"] != plain_key


class TestUpdateSetting:
    """Tests for update_setting method"""

    @pytest.mark.asyncio
    async def test_update_valid_setting(self):
        """Should update setting and record history"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="base_currency",
            value="USD",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            validation_rules=None
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.update_setting("base_currency", "EUR", "User preference change")

        # Assert
        assert setting.value == "EUR"
        mock_db.commit.assert_called_once()
        mock_db.add.assert_called()
        mock_cache.delete.assert_called_once_with("setting:base_currency")

    @pytest.mark.asyncio
    async def test_update_with_validation_pass(self):
        """Should allow update when validation passes"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="refresh_interval",
            value="60",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            validation_rules={
                "type": "integer",
                "minimum": 10,
                "maximum": 300
            }
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.update_setting("refresh_interval", 120)

        # Assert
        assert setting.value == "120"

    @pytest.mark.asyncio
    async def test_update_with_validation_fail(self):
        """Should reject update when validation fails"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="refresh_interval",
            value="60",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            validation_rules={
                "type": "integer",
                "minimum": 10,
                "maximum": 300
            }
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act & Assert
        with pytest.raises(ValueError, match="Validation failed"):
            await service.update_setting("refresh_interval", 500)  # Exceeds maximum

    @pytest.mark.asyncio
    async def test_update_readonly_setting(self):
        """Should reject updates to read-only settings"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="system_version",
            value="1.0.0",
            category=SettingCategory.SYSTEM,
            is_sensitive=False,
            is_editable=False  # Read-only
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act & Assert
        with pytest.raises(ValueError, match="read-only"):
            await service.update_setting("system_version", "2.0.0")

    @pytest.mark.asyncio
    async def test_update_nonexistent_setting(self):
        """Should raise error when updating non-existent setting"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(None))
        service = SettingsService(mock_db, mock_cache)

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await service.update_setting("nonexistent_key", "value")

    @pytest.mark.asyncio
    async def test_update_sensitive_setting(self):
        """Should encrypt sensitive setting values"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        old_encrypted = encrypt_value("old-key-123")

        setting = ApplicationSetting(
            id=1,
            key="anthropic_api_key",
            value=old_encrypted,
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        new_key = "sk-ant-new-key-456"
        result = await service.update_setting("anthropic_api_key", new_key)

        # Assert
        assert setting.value != new_key  # Should be encrypted
        assert setting.value != old_encrypted  # Should be different

    @pytest.mark.asyncio
    async def test_update_history_recorded(self):
        """Should record history entry with old and new values"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="base_currency",
            value="USD",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        await service.update_setting("base_currency", "EUR", "User changed currency")

        # Assert
        mock_db.add.assert_called()
        history_entry = mock_db.add.call_args[0][0]
        assert isinstance(history_entry, SettingHistory)
        assert history_entry.old_value == "USD"
        assert history_entry.new_value == "EUR"
        assert history_entry.change_reason == "User changed currency"

    @pytest.mark.asyncio
    async def test_update_cache_invalidated(self):
        """Should invalidate cache after update"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="base_currency",
            value="USD",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        await service.update_setting("base_currency", "EUR")

        # Assert
        mock_cache.delete.assert_called_once_with("setting:base_currency")


class TestBulkUpdate:
    """Tests for bulk_update method"""

    @pytest.mark.asyncio
    async def test_bulk_update_success(self):
        """Should update multiple settings in one transaction"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting1 = ApplicationSetting(
            id=1, key="base_currency", value="USD",
            category=SettingCategory.DISPLAY, is_sensitive=False, is_editable=True
        )
        setting2 = ApplicationSetting(
            id=2, key="refresh_interval", value="60",
            category=SettingCategory.DISPLAY, is_sensitive=False, is_editable=True
        )

        # Setup execute to return correct setting based on call
        call_count = [0]
        def get_setting_result(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 1:  # Odd calls get setting1
                return create_mock_db_result(setting1)
            else:  # Even calls get setting2
                return create_mock_db_result(setting2)

        mock_db.execute = AsyncMock(side_effect=get_setting_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        updates = {"base_currency": "EUR", "refresh_interval": 120}
        results = await service.bulk_update(updates, "Bulk configuration change")

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_bulk_update_partial_failure_rollback(self):
        """Should rollback all changes if any update fails"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting1 = ApplicationSetting(
            id=1, key="base_currency", value="USD",
            category=SettingCategory.DISPLAY, is_sensitive=False, is_editable=True
        )
        setting2 = ApplicationSetting(
            id=2, key="readonly_setting", value="locked",
            category=SettingCategory.SYSTEM, is_sensitive=False, is_editable=False
        )

        call_count = [0]
        def get_setting_result(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_mock_db_result(setting1)
            else:
                return create_mock_db_result(setting2)

        mock_db.execute = AsyncMock(side_effect=get_setting_result)
        mock_db.rollback = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act & Assert
        updates = {"base_currency": "EUR", "readonly_setting": "new_value"}
        with pytest.raises(ValueError, match="read-only"):
            await service.bulk_update(updates)

        mock_db.rollback.assert_called_once()


class TestResetToDefault:
    """Tests for reset_to_default method"""

    @pytest.mark.asyncio
    async def test_reset_to_default_success(self):
        """Should reset setting to its default value"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="refresh_interval",
            value="120",
            default_value="60",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.reset_to_default("refresh_interval")

        # Assert
        assert setting.value == "60"

    @pytest.mark.asyncio
    async def test_reset_without_default_fails(self):
        """Should raise error when setting has no default value"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="custom_setting",
            value="custom",
            default_value=None,
            category=SettingCategory.ADVANCED,
            is_sensitive=False,
            is_editable=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act & Assert
        with pytest.raises(ValueError, match="no default value"):
            await service.reset_to_default("custom_setting")


class TestGetHistory:
    """Tests for get_history method"""

    @pytest.mark.asyncio
    async def test_get_history_with_changes(self):
        """Should retrieve change history for setting"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        setting = ApplicationSetting(id=1, key="base_currency")

        history_entries = [
            SettingHistory(
                id=1, setting_id=1, old_value="USD", new_value="EUR",
                changed_by="system", changed_at=datetime(2025, 1, 1, 10, 0)
            ),
            SettingHistory(
                id=2, setting_id=1, old_value="EUR", new_value="GBP",
                changed_by="system", changed_at=datetime(2025, 1, 2, 10, 0)
            ),
        ]

        call_count = [0]
        def get_result(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_mock_db_result(setting)
            else:
                return create_mock_db_result(history_entries)

        mock_db.execute = AsyncMock(side_effect=get_result)
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_history("base_currency", limit=50)

        # Assert
        assert len(result) == 2
        assert result[0].new_value == "EUR"
        assert result[1].new_value == "GBP"

    @pytest.mark.asyncio
    async def test_get_history_without_changes(self):
        """Should return empty list for setting without changes"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        setting = ApplicationSetting(id=1, key="base_currency")

        call_count = [0]
        def get_result(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return create_mock_db_result(setting)
            else:
                return create_mock_db_result([])

        mock_db.execute = AsyncMock(side_effect=get_result)
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_history("base_currency")

        # Assert
        assert len(result) == 0


class TestGetAllSettings:
    """Tests for get_all_settings method"""

    @pytest.mark.asyncio
    async def test_get_all_settings_without_decrypt(self):
        """Should retrieve all settings without decryption"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        plain_key = "sk-ant-123"
        encrypted = encrypt_value(plain_key)

        settings = [
            ApplicationSetting(key="base_currency", value="EUR", category=SettingCategory.DISPLAY, is_sensitive=False),
            ApplicationSetting(key="anthropic_api_key", value=encrypted, category=SettingCategory.API_KEYS, is_sensitive=True),
        ]

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(settings))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_all_settings(decrypt=False)

        # Assert
        assert len(result) == 2
        assert result["base_currency"] == "EUR"
        assert result["anthropic_api_key"] == encrypted  # Should be encrypted

    @pytest.mark.asyncio
    async def test_get_all_settings_with_decrypt(self):
        """Should retrieve all settings with decryption"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()

        plain_key = "sk-ant-123"
        encrypted = encrypt_value(plain_key)

        settings = [
            ApplicationSetting(key="base_currency", value="EUR", category=SettingCategory.DISPLAY, is_sensitive=False),
            ApplicationSetting(key="anthropic_api_key", value=encrypted, category=SettingCategory.API_KEYS, is_sensitive=True),
        ]

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(settings))
        service = SettingsService(mock_db, mock_cache)

        # Act
        result = await service.get_all_settings(decrypt=True)

        # Assert
        assert len(result) == 2
        assert result["base_currency"] == "EUR"
        assert result["anthropic_api_key"] == plain_key  # Should be decrypted


class TestErrorHandling:
    """Tests for error handling scenarios"""

    @pytest.mark.asyncio
    async def test_get_setting_decryption_failure(self):
        """Should handle decryption failures gracefully"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)

        setting = ApplicationSetting(
            key="anthropic_api_key",
            value="invalid_encrypted_value",
            category=SettingCategory.API_KEYS,
            is_sensitive=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act & Assert
        with pytest.raises(Exception):  # Decryption will fail
            await service.get_setting("anthropic_api_key", decrypt=True)

    @pytest.mark.asyncio
    async def test_get_setting_cache_failure(self):
        """Should continue when cache fails"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=Exception("Redis connection failed"))

        setting = ApplicationSetting(
            key="base_currency",
            value="EUR",
            category=SettingCategory.DISPLAY,
            is_sensitive=False
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        service = SettingsService(mock_db, mock_cache)

        # Act - should still work even if cache fails
        result = await service.get_setting("base_currency")

        # Assert
        assert result == "EUR"

    @pytest.mark.asyncio
    async def test_update_setting_with_dict_value(self):
        """Should handle dict values in updates"""
        # Arrange
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        mock_cache.delete = AsyncMock()

        setting = ApplicationSetting(
            id=1,
            key="config_object",
            value='{"old": "value"}',
            category=SettingCategory.ADVANCED,
            is_sensitive=False,
            is_editable=True
        )

        mock_db.execute = AsyncMock(return_value=create_mock_db_result(setting))
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        service = SettingsService(mock_db, mock_cache)

        # Act
        new_config = {"new": "value", "nested": {"key": "data"}}
        result = await service.update_setting("config_object", new_config)

        # Assert
        assert '"new"' in setting.value  # Should be JSON stringified
        assert '"nested"' in setting.value


class TestParseValue:
    """Tests for _parse_value utility method"""

    def test_parse_json_object(self):
        """Should parse JSON object string to dict"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value('{"foo": "bar", "count": 42}')

        assert isinstance(result, dict)
        assert result["foo"] == "bar"
        assert result["count"] == 42

    def test_parse_json_array(self):
        """Should parse JSON array string to list"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value('["apple", "banana", "cherry"]')

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "apple"

    def test_parse_boolean_true(self):
        """Should parse 'true' string to True"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value("true")

        assert result is True

    def test_parse_boolean_false(self):
        """Should parse 'false' string to False"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value("false")

        assert result is False

    def test_parse_integer(self):
        """Should parse integer string to int"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value("42")

        assert isinstance(result, int)
        assert result == 42

    def test_parse_float(self):
        """Should parse float string to float"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value("3.14159")

        assert isinstance(result, float)
        assert result == 3.14159

    def test_parse_plain_string(self):
        """Should return plain string unchanged"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value("Hello World")

        assert isinstance(result, str)
        assert result == "Hello World"

    def test_parse_none(self):
        """Should handle None value"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value(None)

        assert result is None

    def test_parse_non_string_value(self):
        """Should return non-string values unchanged"""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_cache = AsyncMock()
        service = SettingsService(mock_db, mock_cache)

        result = service._parse_value(42)

        assert result == 42
