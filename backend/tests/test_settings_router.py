# ABOUTME: Integration tests for Settings API router (Epic 9 - F9.1-003)
# ABOUTME: Tests REST endpoints for managing application settings

"""
Settings API Router Tests (Epic 9 - F9.1-003)

Tests all 8 REST endpoints with:
- Request/response validation
- Error handling (404, 400, 500)
- Sensitive value masking
- Bulk operations
- History tracking
- Validation logic
"""

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy import select
from fastapi import status

from models import ApplicationSetting, SettingHistory, SettingCategory
from settings_service import SettingsService
from security_utils import encrypt_value, decrypt_value


# ==================== FIXTURES ====================

@pytest_asyncio.fixture
async def seed_settings(test_session):
    """Seed test settings for router tests"""
    settings = [
        ApplicationSetting(
            key="base_currency",
            value="USD",
            category=SettingCategory.DISPLAY,
            is_sensitive=False,
            is_editable=True,
            description="Default currency for display",
            default_value="EUR",
            validation_rules={
                "type": "string",
                "enum": ["USD", "EUR", "GBP"]
            }
        ),
        ApplicationSetting(
            key="anthropic_api_key",
            value=encrypt_value("sk-ant-test-key-12345"),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Anthropic Claude API key",
            default_value=None,
            validation_rules={
                "type": "string",
                "pattern": "^sk-ant-"
            }
        ),
        ApplicationSetting(
            key="max_analysis_tokens",
            value="2000",
            category=SettingCategory.PROMPTS,
            is_sensitive=False,
            is_editable=True,
            description="Maximum tokens for AI analysis",
            default_value="1500",
            validation_rules={
                "type": "integer",
                "minimum": 500,
                "maximum": 5000
            }
        ),
        ApplicationSetting(
            key="system_version",
            value="1.0.0",
            category=SettingCategory.SYSTEM,
            is_sensitive=False,
            is_editable=False,  # Read-only
            description="System version",
            default_value=None,
            validation_rules=None
        ),
        ApplicationSetting(
            key="enable_caching",
            value="true",
            category=SettingCategory.ADVANCED,
            is_sensitive=False,
            is_editable=True,
            description="Enable Redis caching",
            default_value="true",
            validation_rules={
                "type": "boolean"
            }
        ),
        ApplicationSetting(
            key="no_default_setting",
            value="current_value",
            category=SettingCategory.SYSTEM,
            is_sensitive=False,
            is_editable=True,
            description="Setting without default",
            default_value=None,
            validation_rules=None
        ),
    ]

    test_session.add_all(settings)
    await test_session.commit()

    return settings


# ==================== ENDPOINT TESTS ====================

class TestCategoriesEndpoint:
    """Tests for GET /api/settings/categories"""

    @pytest.mark.asyncio
    async def test_get_categories_success(self, test_client, seed_settings):
        """Test GET /api/settings/categories returns all categories with metadata"""
        response = test_client.get("/api/settings/categories")

        assert response.status_code == status.HTTP_200_OK
        categories = response.json()
        assert isinstance(categories, list)
        assert len(categories) == 5

        # Verify response structure - should be list of objects, not strings
        category_keys = [cat["key"] for cat in categories]
        assert "display" in category_keys
        assert "api_keys" in category_keys
        assert "prompts" in category_keys
        assert "system" in category_keys
        assert "advanced" in category_keys

        # Verify each category has required fields
        for category in categories:
            assert "key" in category
            assert "name" in category
            assert "description" in category
            assert isinstance(category["key"], str)
            assert isinstance(category["name"], str)
            assert isinstance(category["description"], str) or category["description"] is None

        # Verify specific category metadata
        display_cat = next(cat for cat in categories if cat["key"] == "display")
        assert display_cat["name"] == "Display"
        assert "displayed" in display_cat["description"].lower()

    @pytest.mark.asyncio
    async def test_get_categories_empty_database(self, test_client):
        """Test GET /api/settings/categories with no settings returns all enum values as objects"""
        response = test_client.get("/api/settings/categories")

        assert response.status_code == status.HTTP_200_OK
        categories = response.json()
        assert isinstance(categories, list)
        assert len(categories) == 5  # All SettingCategory enum values

        # Verify all categories are objects with proper structure
        for category in categories:
            assert isinstance(category, dict)
            assert "key" in category
            assert "name" in category
            assert "description" in category


class TestCategorySettingsEndpoint:
    """Tests for GET /api/settings/category/{category}"""

    @pytest.mark.asyncio
    async def test_get_category_settings_display(self, test_client, seed_settings):
        """Test GET /api/settings/category/display returns DISPLAY settings"""
        response = test_client.get("/api/settings/category/display")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["category"] == "display"
        assert "settings" in data
        assert "base_currency" in data["settings"]
        assert data["settings"]["base_currency"]["value"] == "USD"
        assert data["settings"]["base_currency"]["is_sensitive"] is False

    @pytest.mark.asyncio
    async def test_get_category_settings_api_keys_masked(self, test_client, seed_settings):
        """Test GET /api/settings/category/api_keys masks sensitive values by default"""
        response = test_client.get("/api/settings/category/api_keys")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["category"] == "api_keys"
        assert "anthropic_api_key" in data["settings"]
        # Sensitive value should be masked
        assert data["settings"]["anthropic_api_key"]["value"] == "********"
        assert data["settings"]["anthropic_api_key"]["is_sensitive"] is True

    @pytest.mark.asyncio
    async def test_get_category_settings_api_keys_decrypt(self, test_client, seed_settings):
        """Test GET /api/settings/category/api_keys?decrypt=true reveals values"""
        response = test_client.get("/api/settings/category/api_keys?decrypt=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "anthropic_api_key" in data["settings"]
        # Sensitive value should be decrypted
        assert data["settings"]["anthropic_api_key"]["value"] == "sk-ant-test-key-12345"

    @pytest.mark.asyncio
    async def test_get_category_settings_invalid_category(self, test_client, seed_settings):
        """Test GET /api/settings/category/invalid returns 422"""
        response = test_client.get("/api/settings/category/invalid_category")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_category_settings_empty(self, test_client):
        """Test GET /api/settings/category/display with no settings returns empty dict"""
        response = test_client.get("/api/settings/category/display")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["category"] == "display"
        assert data["settings"] == {}


class TestGetSettingEndpoint:
    """Tests for GET /api/settings/{key}"""

    @pytest.mark.asyncio
    async def test_get_setting_success(self, test_client, seed_settings):
        """Test GET /api/settings/{key} returns setting"""
        response = test_client.get("/api/settings/base_currency")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "base_currency"
        assert data["value"] == "USD"
        assert data["category"] == "display"
        assert data["is_sensitive"] is False
        assert data["is_editable"] is True
        assert data["description"] == "Default currency for display"
        assert data["default_value"] == "EUR"
        assert "last_modified_at" in data

    @pytest.mark.asyncio
    async def test_get_setting_not_found(self, test_client, seed_settings):
        """Test GET /api/settings/{key} returns 404 for non-existent setting"""
        response = test_client.get("/api/settings/non_existent_key")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_sensitive_setting_masked(self, test_client, seed_settings):
        """Test GET /api/settings/{key} masks sensitive value by default"""
        response = test_client.get("/api/settings/anthropic_api_key")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "anthropic_api_key"
        assert data["value"] == "********"
        assert data["is_sensitive"] is True

    @pytest.mark.asyncio
    async def test_get_sensitive_setting_revealed(self, test_client, seed_settings):
        """Test GET /api/settings/{key}?reveal=true reveals sensitive value"""
        response = test_client.get("/api/settings/anthropic_api_key?reveal=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "anthropic_api_key"
        assert data["value"] == "sk-ant-test-key-12345"

    @pytest.mark.asyncio
    async def test_get_setting_response_fields(self, test_client, seed_settings):
        """Test GET /api/settings/{key} includes all required fields"""
        response = test_client.get("/api/settings/base_currency")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        required_fields = [
            "key", "value", "category", "is_sensitive",
            "is_editable", "description", "default_value", "last_modified_at"
        ]
        for field in required_fields:
            assert field in data

    @pytest.mark.asyncio
    async def test_get_setting_type_conversion(self, test_client, seed_settings):
        """Test GET /api/settings/{key} converts types correctly"""
        response = test_client.get("/api/settings/max_analysis_tokens")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should be converted to integer
        assert data["value"] == 2000
        assert isinstance(data["value"], int)


class TestUpdateSettingEndpoint:
    """Tests for PUT /api/settings/{key}"""

    @pytest.mark.asyncio
    async def test_update_setting_success(self, test_client, seed_settings):
        """Test PUT /api/settings/{key} updates setting"""
        update_data = {
            "value": "EUR",
            "change_reason": "Testing update"
        }
        response = test_client.put("/api/settings/base_currency", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "base_currency"
        assert data["value"] == "EUR"

    @pytest.mark.asyncio
    async def test_update_setting_validation_pass(self, test_client, seed_settings):
        """Test PUT /api/settings/{key} validates value successfully"""
        update_data = {
            "value": "GBP"  # Valid enum value
        }
        response = test_client.put("/api/settings/base_currency", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["value"] == "GBP"

    @pytest.mark.asyncio
    async def test_update_setting_validation_fail(self, test_client, seed_settings):
        """Test PUT /api/settings/{key} rejects invalid value"""
        update_data = {
            "value": "JPY"  # Not in enum
        }
        response = test_client.put("/api/settings/base_currency", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_read_only_setting(self, test_client, seed_settings):
        """Test PUT /api/settings/{key} rejects read-only setting"""
        update_data = {
            "value": "2.0.0"
        }
        response = test_client.put("/api/settings/system_version", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "read-only" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_setting_not_found(self, test_client, seed_settings):
        """Test PUT /api/settings/{key} returns 404 for non-existent setting"""
        update_data = {
            "value": "test"
        }
        response = test_client.put("/api/settings/non_existent", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_sensitive_setting_encrypted(self, test_client, seed_settings, test_session):
        """Test PUT /api/settings/{key} encrypts sensitive values"""
        update_data = {
            "value": "sk-ant-new-key-67890"
        }
        response = test_client.put("/api/settings/anthropic_api_key", json=update_data)

        assert response.status_code == status.HTTP_200_OK

        # Verify value is encrypted in database
        result = await test_session.execute(
            select(ApplicationSetting).where(ApplicationSetting.key == "anthropic_api_key")
        )
        setting = result.scalar_one()
        # Value in DB should be encrypted (not plaintext)
        assert setting.value != "sk-ant-new-key-67890"
        # But should decrypt correctly
        assert decrypt_value(setting.value) == "sk-ant-new-key-67890"

    @pytest.mark.asyncio
    async def test_update_setting_creates_history(self, test_client, seed_settings, test_session):
        """Test PUT /api/settings/{key} records change in history"""
        # Get initial setting
        get_response = test_client.get("/api/settings/base_currency")
        old_value = get_response.json()["value"]

        # Update setting
        update_data = {
            "value": "EUR",
            "change_reason": "Testing history"
        }
        response = test_client.put("/api/settings/base_currency", json=update_data)
        assert response.status_code == status.HTTP_200_OK

        # Check history was created
        result = await test_session.execute(
            select(SettingHistory).join(ApplicationSetting)
            .where(ApplicationSetting.key == "base_currency")
        )
        history = result.scalar_one()
        assert history.old_value == old_value
        assert history.new_value == "EUR"
        assert history.change_reason == "Testing history"

    @pytest.mark.asyncio
    async def test_update_setting_invalidates_cache(self, test_client, seed_settings):
        """Test PUT /api/settings/{key} invalidates cache"""
        # Get setting (caches it)
        get_response1 = test_client.get("/api/settings/base_currency")
        assert get_response1.status_code == status.HTTP_200_OK

        # Update setting
        update_data = {"value": "EUR"}
        update_response = test_client.put("/api/settings/base_currency", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK

        # Get setting again (should reflect new value)
        get_response2 = test_client.get("/api/settings/base_currency")
        assert get_response2.status_code == status.HTTP_200_OK
        assert get_response2.json()["value"] == "EUR"


class TestBulkUpdateEndpoint:
    """Tests for POST /api/settings/bulk"""

    @pytest.mark.asyncio
    async def test_bulk_update_success(self, test_client, seed_settings):
        """Test POST /api/settings/bulk updates multiple settings"""
        bulk_data = {
            "updates": {
                "base_currency": "EUR",
                "max_analysis_tokens": 3000
            },
            "change_reason": "Bulk update test"
        }
        response = test_client.post("/api/settings/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify both updates
        keys = [item["key"] for item in data]
        assert "base_currency" in keys
        assert "max_analysis_tokens" in keys

    @pytest.mark.asyncio
    async def test_bulk_update_partial_failure_rollback(self, test_client, seed_settings):
        """Test POST /api/settings/bulk rolls back all on any failure"""
        bulk_data = {
            "updates": {
                "base_currency": "EUR",  # Valid
                "system_version": "2.0.0"  # Read-only, should fail
            }
        }
        response = test_client.post("/api/settings/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify base_currency was NOT updated (rollback)
        get_response = test_client.get("/api/settings/base_currency")
        assert get_response.json()["value"] == "USD"  # Original value

    @pytest.mark.asyncio
    async def test_bulk_update_empty_dict(self, test_client, seed_settings):
        """Test POST /api/settings/bulk rejects empty updates"""
        bulk_data = {
            "updates": {}
        }
        response = test_client.post("/api/settings/bulk", json=bulk_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_bulk_update_creates_history_for_each(self, test_client, seed_settings, test_session):
        """Test POST /api/settings/bulk records history for each setting"""
        bulk_data = {
            "updates": {
                "base_currency": "EUR",
                "enable_caching": False
            },
            "change_reason": "Bulk test"
        }
        response = test_client.post("/api/settings/bulk", json=bulk_data)
        assert response.status_code == status.HTTP_200_OK

        # Check history for both settings
        result = await test_session.execute(
            select(SettingHistory).join(ApplicationSetting)
            .where(ApplicationSetting.key.in_(["base_currency", "enable_caching"]))
        )
        histories = result.scalars().all()
        assert len(histories) == 2


class TestResetSettingEndpoint:
    """Tests for POST /api/settings/{key}/reset"""

    @pytest.mark.asyncio
    async def test_reset_setting_success(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/reset resets to default"""
        # Update setting first
        test_client.put("/api/settings/base_currency", json={"value": "GBP"})

        # Reset to default
        response = test_client.post("/api/settings/base_currency/reset")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "base_currency"
        assert data["value"] == "EUR"  # Default value

    @pytest.mark.asyncio
    async def test_reset_setting_no_default(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/reset fails when no default"""
        response = test_client.post("/api/settings/no_default_setting/reset")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "no default" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_setting_not_found(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/reset returns 404 for non-existent"""
        response = test_client.post("/api/settings/non_existent/reset")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSettingHistoryEndpoint:
    """Tests for GET /api/settings/{key}/history"""

    @pytest.mark.asyncio
    async def test_get_history_with_changes(self, test_client, seed_settings):
        """Test GET /api/settings/{key}/history returns change history"""
        # Make some changes
        test_client.put("/api/settings/base_currency", json={
            "value": "EUR",
            "change_reason": "First change"
        })
        test_client.put("/api/settings/base_currency", json={
            "value": "GBP",
            "change_reason": "Second change"
        })

        # Get history
        response = test_client.get("/api/settings/base_currency/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        # Check most recent change
        latest = data[0]
        assert latest["new_value"] == "GBP"
        assert latest["change_reason"] == "Second change"
        assert "changed_at" in latest
        assert "changed_by" in latest

    @pytest.mark.asyncio
    async def test_get_history_no_changes(self, test_client, seed_settings):
        """Test GET /api/settings/{key}/history returns empty list for no changes"""
        response = test_client.get("/api/settings/base_currency/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_history_not_found(self, test_client, seed_settings):
        """Test GET /api/settings/{key}/history returns 404 for non-existent"""
        response = test_client.get("/api/settings/non_existent/history")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self, test_client, seed_settings):
        """Test GET /api/settings/{key}/history respects limit parameter"""
        # Make multiple changes
        for i in range(5):
            test_client.put("/api/settings/base_currency", json={
                "value": ["EUR", "GBP", "USD"][i % 3],
                "change_reason": f"Change {i}"
            })

        # Get history with limit
        response = test_client.get("/api/settings/base_currency/history?limit=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 3


class TestValidateSettingEndpoint:
    """Tests for POST /api/settings/{key}/validate"""

    @pytest.mark.asyncio
    async def test_validate_valid_value(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/validate returns valid: true"""
        validate_data = {
            "value": "EUR"  # Valid enum value
        }
        response = test_client.post("/api/settings/base_currency/validate", json=validate_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["error"] is None
        assert data["validated_value"] == "EUR"

    @pytest.mark.asyncio
    async def test_validate_invalid_value(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/validate returns valid: false"""
        validate_data = {
            "value": "JPY"  # Not in enum
        }
        response = test_client.post("/api/settings/base_currency/validate", json=validate_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is False
        assert data["error"] is not None

    @pytest.mark.asyncio
    async def test_validate_not_found(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/validate returns 404 for non-existent"""
        validate_data = {
            "value": "test"
        }
        response = test_client.post("/api/settings/non_existent/validate", json=validate_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_validate_no_rules(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/validate with no rules returns valid: true"""
        validate_data = {
            "value": "any_value"
        }
        response = test_client.post("/api/settings/no_default_setting/validate", json=validate_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_type_conversion(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/validate converts types"""
        validate_data = {
            "value": "3500"  # String that should convert to int
        }
        response = test_client.post("/api/settings/max_analysis_tokens/validate", json=validate_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["validated_value"] == 3500
        assert isinstance(data["validated_value"], int)


# ==================== API KEY TEST ENDPOINT TESTS ====================

class TestAPIKeyTestEndpoint:
    """Tests for POST /api/settings/{key}/test endpoint"""

    @pytest.mark.asyncio
    async def test_test_anthropic_key_success(self, test_client, seed_settings, mocker):
        """Test POST /api/settings/anthropic_api_key/test with valid key"""
        # Mock Anthropic client
        mock_anthropic = mocker.patch('settings_router.AsyncAnthropic')
        mock_client = mock_anthropic.return_value
        mock_client.messages.create = mocker.AsyncMock(return_value={"text": "test"})

        test_data = {
            "value": "sk-ant-valid-key-12345"
        }
        response = test_client.post("/api/settings/anthropic_api_key/test", json=test_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["error"] is None
        assert data["validated_value"] == "sk-ant-valid-key-12345"

        # Verify API was called
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_anthropic_key_invalid(self, test_client, seed_settings, mocker):
        """Test POST /api/settings/anthropic_api_key/test with invalid key"""
        # Mock Anthropic client to raise auth error
        mock_anthropic = mocker.patch('settings_router.AsyncAnthropic')
        mock_client = mock_anthropic.return_value
        mock_client.messages.create = mocker.AsyncMock(
            side_effect=Exception("authentication failed")
        )

        test_data = {
            "value": "sk-ant-invalid-key"
        }
        response = test_client.post("/api/settings/anthropic_api_key/test", json=test_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is False
        assert "authentication failed" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_test_alpha_vantage_key_success(self, test_client, seed_settings, mocker):
        """Test POST /api/settings/alpha_vantage_api_key/test with valid key"""
        # First add alpha_vantage_api_key to test data
        from models import ApplicationSetting, SettingCategory
        test_session = test_client.app.state.db_session

        new_setting = ApplicationSetting(
            key="alpha_vantage_api_key",
            value=encrypt_value("test_av_key"),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Alpha Vantage API key",
            default_value=None
        )
        test_session.add(new_setting)
        await test_session.commit()

        # Mock aiohttp response
        mock_response = mocker.MagicMock()
        mock_response.json = mocker.AsyncMock(return_value={
            "Global Quote": {"01. symbol": "AAPL", "05. price": "150.00"}
        })

        mock_session = mocker.MagicMock()
        mock_session.get = mocker.AsyncMock(return_value=mocker.AsyncMock(
            __aenter__=mocker.AsyncMock(return_value=mock_response),
            __aexit__=mocker.AsyncMock()
        ))

        mocker.patch('aiohttp.ClientSession', return_value=mocker.AsyncMock(
            __aenter__=mocker.AsyncMock(return_value=mock_session),
            __aexit__=mocker.AsyncMock()
        ))

        test_data = {
            "value": "valid_alpha_vantage_key"
        }
        response = test_client.post("/api/settings/alpha_vantage_api_key/test", json=test_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["error"] is None

    @pytest.mark.asyncio
    async def test_test_non_api_key_setting(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/test returns 404 for non-API key settings"""
        test_data = {
            "value": "test"
        }
        response = test_client.post("/api/settings/base_currency/test", json=test_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not an API key" in data["detail"]

    @pytest.mark.asyncio
    async def test_test_non_existent_setting(self, test_client, seed_settings):
        """Test POST /api/settings/{key}/test returns 404 for non-existent setting"""
        test_data = {
            "value": "test"
        }
        response = test_client.post("/api/settings/non_existent_key/test", json=test_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_test_unsupported_api_key_type(self, test_client, seed_settings, mocker):
        """Test POST /api/settings/{key}/test with unsupported API key type"""
        # Add a new API key type that's not supported
        test_session = test_client.app.state.db_session

        unsupported_setting = ApplicationSetting(
            key="some_other_api_key",
            value=encrypt_value("test_key"),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Some other API key",
            default_value=None
        )
        test_session.add(unsupported_setting)
        await test_session.commit()

        test_data = {
            "value": "test_key"
        }
        response = test_client.post("/api/settings/some_other_api_key/test", json=test_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is False
        assert "not supported" in data["error"]
