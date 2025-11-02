# ABOUTME: Security utilities for encrypting/decrypting sensitive settings
# ABOUTME: Uses Fernet symmetric encryption for API keys and other sensitive data

import os
from cryptography.fernet import Fernet


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        str: Base64-encoded encryption key (44 characters)

    Example:
        >>> key = generate_encryption_key()
        >>> len(key)
        44
    """
    return Fernet.generate_key().decode()


def get_cipher() -> Fernet:
    """
    Get Fernet cipher instance using key from environment variable.

    Returns:
        Fernet: Cipher instance for encryption/decryption

    Raises:
        ValueError: If SETTINGS_ENCRYPTION_KEY environment variable is not set
        Exception: If the key is invalid

    Example:
        >>> cipher = get_cipher()  # Requires SETTINGS_ENCRYPTION_KEY in env
    """
    key = os.getenv("SETTINGS_ENCRYPTION_KEY")
    if not key:
        raise ValueError("SETTINGS_ENCRYPTION_KEY not set in environment")

    return Fernet(key.encode())


def encrypt_value(value: str) -> str:
    """
    Encrypt a sensitive value using Fernet symmetric encryption.

    Args:
        value: Plain text value to encrypt

    Returns:
        str: Base64-encoded encrypted value

    Example:
        >>> encrypted = encrypt_value("sk-ant-api-key-123")
        >>> encrypted != "sk-ant-api-key-123"
        True
    """
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """
    Decrypt a sensitive value using Fernet symmetric encryption.

    Args:
        encrypted: Base64-encoded encrypted value

    Returns:
        str: Decrypted plain text value

    Raises:
        cryptography.fernet.InvalidToken: If encrypted value is invalid or tampered

    Example:
        >>> encrypted = encrypt_value("secret")
        >>> decrypt_value(encrypted)
        'secret'
    """
    cipher = get_cipher()
    return cipher.decrypt(encrypted.encode()).decode()
