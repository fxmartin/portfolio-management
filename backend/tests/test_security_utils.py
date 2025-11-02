# ABOUTME: Unit tests for security_utils encryption/decryption helpers
# ABOUTME: Tests Fernet encryption, key generation, and error handling

import pytest
import os
from cryptography.fernet import Fernet, InvalidToken

from security_utils import (
    generate_encryption_key,
    encrypt_value,
    decrypt_value,
    get_cipher
)


class TestEncryptionKeyGeneration:
    """Test encryption key generation"""

    def test_generate_encryption_key_format(self):
        """Test that generated key is valid Fernet key format"""
        key = generate_encryption_key()

        # Should be a base64-encoded 32-byte key
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet keys are 44 characters when base64 encoded

        # Should be decodable as Fernet key
        cipher = Fernet(key.encode())
        assert cipher is not None

    def test_generate_encryption_key_unique(self):
        """Test that each generated key is unique"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        assert key1 != key2


class TestGetCipher:
    """Test cipher retrieval from environment"""

    def test_get_cipher_with_valid_key(self, monkeypatch):
        """Test getting cipher with valid environment key"""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", test_key)

        cipher = get_cipher()

        assert cipher is not None
        assert isinstance(cipher, Fernet)

    def test_get_cipher_missing_key(self, monkeypatch):
        """Test that missing key raises error"""
        monkeypatch.delenv("SETTINGS_ENCRYPTION_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            get_cipher()

        assert "SETTINGS_ENCRYPTION_KEY not set" in str(exc_info.value)

    def test_get_cipher_invalid_key(self, monkeypatch):
        """Test that invalid key raises error"""
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", "invalid_key")

        with pytest.raises(Exception):  # Fernet will raise on invalid key
            get_cipher()


class TestEncryptDecrypt:
    """Test encryption and decryption functions"""

    @pytest.fixture(autouse=True)
    def setup_encryption_key(self, monkeypatch):
        """Set up a test encryption key for all tests"""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", test_key)

    def test_encrypt_value_basic(self):
        """Test basic value encryption"""
        plaintext = "my_secret_api_key"

        encrypted = encrypt_value(plaintext)

        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)  # Encrypted is longer

    def test_decrypt_value_basic(self):
        """Test basic value decryption"""
        plaintext = "my_secret_api_key"

        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypt -> decrypt roundtrip preserves value"""
        test_values = [
            "simple_string",
            "sk-ant-api-key-1234567890",
            "complex!@#$%^&*()value",
            "unicode_测试_🔐",
            "multi\nline\nvalue",
            "   spaces   around   ",
            "123456789",
            ""  # Empty string
        ]

        for value in test_values:
            encrypted = encrypt_value(value)
            decrypted = decrypt_value(encrypted)
            assert decrypted == value, f"Failed for value: {value}"

    def test_encrypt_same_value_different_ciphertext(self):
        """Test that encrypting same value twice produces different ciphertext"""
        plaintext = "api_key_value"

        encrypted1 = encrypt_value(plaintext)
        encrypted2 = encrypt_value(plaintext)

        # Different ciphertext (Fernet includes timestamp/nonce)
        assert encrypted1 != encrypted2

        # But both decrypt to same value
        assert decrypt_value(encrypted1) == plaintext
        assert decrypt_value(encrypted2) == plaintext

    def test_decrypt_invalid_token(self, monkeypatch):
        """Test that decrypting invalid token raises error"""
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", Fernet.generate_key().decode())

        with pytest.raises(Exception):  # InvalidToken or similar
            decrypt_value("not_a_valid_encrypted_value")

    def test_decrypt_with_wrong_key(self, monkeypatch):
        """Test that decrypting with wrong key fails"""
        # Encrypt with first key
        key1 = Fernet.generate_key().decode()
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", key1)
        encrypted = encrypt_value("secret_value")

        # Try to decrypt with different key
        key2 = Fernet.generate_key().decode()
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", key2)

        with pytest.raises(InvalidToken):
            decrypt_value(encrypted)

    def test_encrypt_long_value(self):
        """Test encrypting long values"""
        long_value = "a" * 10000  # 10KB of data

        encrypted = encrypt_value(long_value)
        decrypted = decrypt_value(encrypted)

        assert decrypted == long_value

    def test_encrypt_unicode(self):
        """Test encrypting unicode characters"""
        unicode_value = "Hello 世界 🌍 Привет مرحبا"

        encrypted = encrypt_value(unicode_value)
        decrypted = decrypt_value(encrypted)

        assert decrypted == unicode_value

    def test_encrypt_special_characters(self):
        """Test encrypting special characters"""
        special_value = '!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\`~'

        encrypted = encrypt_value(special_value)
        decrypted = decrypt_value(encrypted)

        assert decrypted == special_value

    def test_encrypt_numeric_string(self):
        """Test encrypting numeric strings"""
        numeric_value = "1234567890"

        encrypted = encrypt_value(numeric_value)
        decrypted = decrypt_value(encrypted)

        assert decrypted == numeric_value

    def test_encrypted_value_is_base64(self):
        """Test that encrypted value is valid base64 (Fernet format)"""
        import base64

        plaintext = "test_value"
        encrypted = encrypt_value(plaintext)

        # Fernet tokens are URL-safe base64 encoded
        # They should be decodable, though may contain non-standard base64 chars
        try:
            # Use urlsafe_b64decode since Fernet uses URL-safe base64
            decoded = base64.urlsafe_b64decode(encrypted.encode() + b'==')  # Add padding if needed
            assert decoded is not None
        except Exception:
            # If that fails, at least verify it's ASCII and contains expected chars
            assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=' for c in encrypted)


class TestEncryptionSecurity:
    """Test security aspects of encryption"""

    @pytest.fixture(autouse=True)
    def setup_encryption_key(self, monkeypatch):
        """Set up a test encryption key for all tests"""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", test_key)

    def test_encrypted_value_not_contain_plaintext(self):
        """Test that encrypted value doesn't contain plaintext"""
        plaintext = "my_secret_api_key_sk-ant-123456"

        encrypted = encrypt_value(plaintext)

        # Plaintext should not appear in encrypted value
        assert plaintext not in encrypted
        assert "my_secret" not in encrypted
        assert "sk-ant" not in encrypted

    def test_encryption_determinism(self):
        """Test that encryption is not deterministic (includes nonce/timestamp)"""
        plaintext = "api_key"

        # Encrypt multiple times
        encryptions = [encrypt_value(plaintext) for _ in range(5)]

        # All should be unique
        assert len(set(encryptions)) == 5

        # But all should decrypt to same value
        for encrypted in encryptions:
            assert decrypt_value(encrypted) == plaintext

    def test_empty_string_encryption(self):
        """Test encrypting empty string"""
        plaintext = ""

        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == ""
        assert len(encrypted) > 0  # Encrypted empty string still has overhead
