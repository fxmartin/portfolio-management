# ABOUTME: Tests for encryption key rotation utility
# ABOUTME: Verifies safe key rotation for sensitive settings without data loss

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select

from models import ApplicationSetting, SettingCategory
from rotate_encryption_key import (
    rotate_encryption_key,
    verify_rotation,
    KeyRotationError
)


class TestKeyRotation:
    """Test encryption key rotation functionality"""

    @pytest_asyncio.fixture
    async def sensitive_settings(self, test_session):
        """Create test sensitive settings"""
        old_key = Fernet.generate_key().decode()
        old_cipher = Fernet(old_key.encode())

        # Create sensitive settings with encrypted values
        settings = [
            ApplicationSetting(
                key="anthropic_api_key",
                value=old_cipher.encrypt(b"sk-ant-test-key-123").decode(),
                category=SettingCategory.API_KEYS,
                is_sensitive=True,
                is_editable=True,
                description="Anthropic API key"
            ),
            ApplicationSetting(
                key="alpha_vantage_api_key",
                value=old_cipher.encrypt(b"TESTAPIKEY123456").decode(),
                category=SettingCategory.API_KEYS,
                is_sensitive=True,
                is_editable=True,
                description="Alpha Vantage API key"
            ),
            ApplicationSetting(
                key="base_currency",
                value="EUR",
                category=SettingCategory.DISPLAY,
                is_sensitive=False,
                is_editable=True,
                description="Base currency"
            )
        ]

        test_session.add_all(settings)
        await test_session.commit()

        return old_key, settings

    @pytest.mark.asyncio
    async def test_rotate_key_success(self, test_session, sensitive_settings):
        """Test successful key rotation"""
        old_key, settings = sensitive_settings
        new_key = Fernet.generate_key().decode()

        # Get database URL from session
        db_url = str(test_session.get_bind().url)

        # Rotate keys
        count = await rotate_encryption_key(old_key, new_key, db_url)

        # Should rotate 2 sensitive settings (not the non-sensitive one)
        assert count == 2

        # Verify new values can be decrypted with new key
        new_cipher = Fernet(new_key.encode())
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(is_sensitive=True)
        )
        rotated_settings = result.scalars().all()

        for setting in rotated_settings:
            decrypted = new_cipher.decrypt(setting.value.encode()).decode()
            assert decrypted in ["sk-ant-test-key-123", "TESTAPIKEY123456"]

    @pytest.mark.asyncio
    async def test_rotate_key_preserves_values(self, test_session, sensitive_settings):
        """Test that rotation preserves original values"""
        old_key, settings = sensitive_settings
        new_key = Fernet.generate_key().decode()
        db_url = str(test_session.get_bind().url)

        # Get original values
        old_cipher = Fernet(old_key.encode())
        original_values = {
            "anthropic_api_key": "sk-ant-test-key-123",
            "alpha_vantage_api_key": "TESTAPIKEY123456"
        }

        # Rotate
        await rotate_encryption_key(old_key, new_key, db_url)

        # Verify decrypted values match originals
        new_cipher = Fernet(new_key.encode())
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(is_sensitive=True)
        )
        rotated_settings = result.scalars().all()

        for setting in rotated_settings:
            decrypted = new_cipher.decrypt(setting.value.encode()).decode()
            assert decrypted == original_values[setting.key]

    @pytest.mark.asyncio
    async def test_rotate_key_invalid_old_key(self, test_session, sensitive_settings):
        """Test rotation fails with invalid old key"""
        old_key, settings = sensitive_settings
        wrong_old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        db_url = str(test_session.get_bind().url)

        # Should raise KeyRotationError
        with pytest.raises(KeyRotationError) as exc_info:
            await rotate_encryption_key(wrong_old_key, new_key, db_url)

        assert "Cannot decrypt setting" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rotate_key_invalid_new_key_format(self, test_session):
        """Test rotation fails with invalid new key format"""
        old_key = Fernet.generate_key().decode()
        invalid_new_key = "not_a_valid_fernet_key"
        db_url = str(test_session.get_bind().url)

        with pytest.raises(KeyRotationError) as exc_info:
            await rotate_encryption_key(old_key, invalid_new_key, db_url)

        assert "Invalid encryption key format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rotate_key_skips_null_values(self, test_session):
        """Test rotation skips settings with null values"""
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()

        # Create setting with null value
        setting = ApplicationSetting(
            key="optional_api_key",
            value=None,
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Optional API key"
        )
        test_session.add(setting)
        await test_session.commit()

        db_url = str(test_session.get_bind().url)

        # Should not fail, should return 0
        count = await rotate_encryption_key(old_key, new_key, db_url)
        assert count == 0

    @pytest.mark.asyncio
    async def test_rotate_key_atomic_transaction(self, test_session, sensitive_settings):
        """Test that rotation is atomic - all or nothing"""
        old_key, settings = sensitive_settings
        new_key = Fernet.generate_key().decode()
        db_url = str(test_session.get_bind().url)

        # Add a setting with corrupted encryption that will fail
        corrupted_setting = ApplicationSetting(
            key="corrupted_key",
            value="not_valid_encrypted_data",
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True,
            description="Corrupted key"
        )
        test_session.add(corrupted_setting)
        await test_session.commit()

        # Rotation should fail
        with pytest.raises(KeyRotationError):
            await rotate_encryption_key(old_key, new_key, db_url)

        # Verify original settings are unchanged (transaction rolled back)
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="anthropic_api_key")
        )
        setting = result.scalar_one()

        # Should still decrypt with old key
        old_cipher = Fernet(old_key.encode())
        decrypted = old_cipher.decrypt(setting.value.encode()).decode()
        assert decrypted == "sk-ant-test-key-123"

    @pytest.mark.asyncio
    async def test_rotate_key_no_sensitive_settings(self, test_session):
        """Test rotation when no sensitive settings exist"""
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        db_url = str(test_session.get_bind().url)

        # Rotate with empty database
        count = await rotate_encryption_key(old_key, new_key, db_url)

        assert count == 0


class TestVerifyRotation:
    """Test verification of key rotation"""

    @pytest_asyncio.fixture
    async def rotated_settings(self, test_session):
        """Create settings encrypted with a known key"""
        key = Fernet.generate_key().decode()
        cipher = Fernet(key.encode())

        settings = [
            ApplicationSetting(
                key="api_key_1",
                value=cipher.encrypt(b"secret1").decode(),
                category=SettingCategory.API_KEYS,
                is_sensitive=True,
                is_editable=True
            ),
            ApplicationSetting(
                key="api_key_2",
                value=cipher.encrypt(b"secret2").decode(),
                category=SettingCategory.API_KEYS,
                is_sensitive=True,
                is_editable=True
            )
        ]

        test_session.add_all(settings)
        await test_session.commit()

        return key

    @pytest.mark.asyncio
    async def test_verify_rotation_success(self, test_session, rotated_settings):
        """Test successful verification"""
        key = rotated_settings
        db_url = str(test_session.get_bind().url)

        result = await verify_rotation(key, db_url)

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_rotation_wrong_key(self, test_session, rotated_settings):
        """Test verification fails with wrong key"""
        wrong_key = Fernet.generate_key().decode()
        db_url = str(test_session.get_bind().url)

        result = await verify_rotation(wrong_key, db_url)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_rotation_invalid_key_format(self, test_session):
        """Test verification fails with invalid key format"""
        invalid_key = "not_a_valid_key"
        db_url = str(test_session.get_bind().url)

        result = await verify_rotation(invalid_key, db_url)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_rotation_no_sensitive_settings(self, test_session):
        """Test verification passes when no sensitive settings exist"""
        key = Fernet.generate_key().decode()
        db_url = str(test_session.get_bind().url)

        result = await verify_rotation(key, db_url)

        assert result is True  # No settings to verify = success

    @pytest.mark.asyncio
    async def test_verify_rotation_mixed_encrypted_settings(self, test_session):
        """Test verification with multiple keys (partial rotation scenario)"""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        cipher1 = Fernet(key1.encode())
        cipher2 = Fernet(key2.encode())

        settings = [
            ApplicationSetting(
                key="setting1",
                value=cipher1.encrypt(b"secret1").decode(),
                category=SettingCategory.API_KEYS,
                is_sensitive=True,
                is_editable=True
            ),
            ApplicationSetting(
                key="setting2",
                value=cipher2.encrypt(b"secret2").decode(),
                category=SettingCategory.API_KEYS,
                is_sensitive=True,
                is_editable=True
            )
        ]

        test_session.add_all(settings)
        await test_session.commit()

        db_url = str(test_session.get_bind().url)

        # Verify with key1 should fail (setting2 encrypted with key2)
        result = await verify_rotation(key1, db_url)
        assert result is False

        # Verify with key2 should also fail (setting1 encrypted with key1)
        result = await verify_rotation(key2, db_url)
        assert result is False


class TestKeyRotationEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_rotate_same_key(self, test_session):
        """Test rotating to the same key (should work but is pointless)"""
        key = Fernet.generate_key().decode()
        cipher = Fernet(key.encode())

        setting = ApplicationSetting(
            key="test_key",
            value=cipher.encrypt(b"secret").decode(),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True
        )
        test_session.add(setting)
        await test_session.commit()

        db_url = str(test_session.get_bind().url)

        # Should succeed but change nothing
        count = await rotate_encryption_key(key, key, db_url)
        assert count == 1

    @pytest.mark.asyncio
    async def test_rotate_empty_string_value(self, test_session):
        """Test rotating settings with empty string values"""
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        old_cipher = Fernet(old_key.encode())

        setting = ApplicationSetting(
            key="empty_setting",
            value=old_cipher.encrypt(b"").decode(),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True
        )
        test_session.add(setting)
        await test_session.commit()

        db_url = str(test_session.get_bind().url)

        count = await rotate_encryption_key(old_key, new_key, db_url)
        assert count == 1

        # Verify empty string is preserved
        new_cipher = Fernet(new_key.encode())
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="empty_setting")
        )
        rotated = result.scalar_one()
        decrypted = new_cipher.decrypt(rotated.value.encode()).decode()
        assert decrypted == ""

    @pytest.mark.asyncio
    async def test_rotate_unicode_values(self, test_session):
        """Test rotating settings with unicode characters"""
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        old_cipher = Fernet(old_key.encode())

        unicode_value = "Hello 世界 🔐 Привет"
        setting = ApplicationSetting(
            key="unicode_setting",
            value=old_cipher.encrypt(unicode_value.encode()).decode(),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True
        )
        test_session.add(setting)
        await test_session.commit()

        db_url = str(test_session.get_bind().url)

        count = await rotate_encryption_key(old_key, new_key, db_url)
        assert count == 1

        # Verify unicode is preserved
        new_cipher = Fernet(new_key.encode())
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="unicode_setting")
        )
        rotated = result.scalar_one()
        decrypted = new_cipher.decrypt(rotated.value.encode()).decode()
        assert decrypted == unicode_value

    @pytest.mark.asyncio
    async def test_rotate_large_value(self, test_session):
        """Test rotating large encrypted values"""
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        old_cipher = Fernet(old_key.encode())

        # Create a large value (10KB)
        large_value = "A" * 10000
        setting = ApplicationSetting(
            key="large_setting",
            value=old_cipher.encrypt(large_value.encode()).decode(),
            category=SettingCategory.API_KEYS,
            is_sensitive=True,
            is_editable=True
        )
        test_session.add(setting)
        await test_session.commit()

        db_url = str(test_session.get_bind().url)

        count = await rotate_encryption_key(old_key, new_key, db_url)
        assert count == 1

        # Verify large value is preserved
        new_cipher = Fernet(new_key.encode())
        result = await test_session.execute(
            select(ApplicationSetting).filter_by(key="large_setting")
        )
        rotated = result.scalar_one()
        decrypted = new_cipher.decrypt(rotated.value.encode()).decode()
        assert decrypted == large_value
