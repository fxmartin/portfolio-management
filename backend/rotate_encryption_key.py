# ABOUTME: Encryption key rotation utility for migrating sensitive settings to a new key
# ABOUTME: Safely rotates encryption keys by decrypting with old key and re-encrypting with new key

"""
Encryption Key Rotation Utility (Epic 9 - F9.3-001)

This script safely rotates the encryption key for all sensitive settings.
It ensures zero downtime by:
1. Decrypting all sensitive values with the old key
2. Re-encrypting them with the new key
3. Atomic database transaction (all-or-nothing)

Usage:
    python rotate_encryption_key.py OLD_KEY NEW_KEY

Example:
    # Generate a new key first
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    # Rotate to the new key
    python rotate_encryption_key.py \
        "OLD_ENCRYPTION_KEY_HERE" \
        "NEW_ENCRYPTION_KEY_HERE"

Security Notes:
    - Run this script in a secure environment
    - Old and new keys should never be committed to version control
    - Backup your database before running
    - Update .env immediately after successful rotation
"""

import asyncio
import sys
import logging
from typing import List
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models import ApplicationSetting
from config import Settings

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KeyRotationError(Exception):
    """Exception raised during key rotation failures"""
    pass


async def rotate_encryption_key(
    old_key: str,
    new_key: str,
    db_url: str = None
) -> int:
    """
    Rotate encryption key for all sensitive settings.

    This function:
    1. Validates both old and new keys
    2. Retrieves all sensitive settings
    3. Decrypts with old key
    4. Re-encrypts with new key
    5. Updates database in a single transaction

    Args:
        old_key: Current encryption key (base64-encoded)
        new_key: New encryption key to rotate to (base64-encoded)
        db_url: Database URL (defaults to settings.DATABASE_URL)

    Returns:
        int: Number of settings rotated

    Raises:
        KeyRotationError: If validation fails or rotation errors occur
        InvalidToken: If old key cannot decrypt existing values

    Example:
        >>> count = await rotate_encryption_key(old_key, new_key)
        >>> print(f"Rotated {count} sensitive settings")
    """
    logger.info("Starting encryption key rotation...")

    # Validate keys
    try:
        old_cipher = Fernet(old_key.encode())
        new_cipher = Fernet(new_key.encode())
        logger.info("✓ Both keys validated successfully")
    except Exception as e:
        raise KeyRotationError(f"Invalid encryption key format: {e}")

    # Connect to database
    if not db_url:
        db_url = settings.DATABASE_URL

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    rotated_count = 0

    try:
        async with async_session() as session:
            # Get all sensitive settings
            result = await session.execute(
                select(ApplicationSetting).filter_by(is_sensitive=True)
            )
            sensitive_settings: List[ApplicationSetting] = result.scalars().all()

            if not sensitive_settings:
                logger.warning("No sensitive settings found to rotate")
                return 0

            logger.info(f"Found {len(sensitive_settings)} sensitive settings to rotate")

            # Rotate each setting
            for setting in sensitive_settings:
                if not setting.value:
                    logger.debug(f"Skipping {setting.key} - no value set")
                    continue

                try:
                    # Decrypt with old key
                    decrypted = old_cipher.decrypt(setting.value.encode()).decode()
                    logger.debug(f"✓ Decrypted {setting.key} with old key")

                    # Re-encrypt with new key
                    re_encrypted = new_cipher.encrypt(decrypted.encode()).decode()
                    logger.debug(f"✓ Re-encrypted {setting.key} with new key")

                    # Update value
                    setting.value = re_encrypted
                    rotated_count += 1

                except InvalidToken:
                    logger.error(f"✗ Failed to decrypt {setting.key} - invalid old key or corrupted value")
                    raise KeyRotationError(
                        f"Cannot decrypt setting '{setting.key}'. "
                        f"Ensure the old key is correct."
                    )
                except Exception as e:
                    logger.error(f"✗ Unexpected error rotating {setting.key}: {e}")
                    raise KeyRotationError(f"Rotation failed for {setting.key}: {e}")

            # Commit all changes atomically
            await session.commit()
            logger.info(f"✓ Successfully rotated {rotated_count} sensitive settings")

            return rotated_count

    except Exception as e:
        logger.error(f"✗ Key rotation failed: {e}")
        raise
    finally:
        await engine.dispose()


async def verify_rotation(new_key: str, db_url: str = None) -> bool:
    """
    Verify that all sensitive settings can be decrypted with the new key.

    This should be run AFTER rotation to confirm success.

    Args:
        new_key: The new encryption key
        db_url: Database URL (defaults to settings.DATABASE_URL)

    Returns:
        bool: True if all settings decrypt successfully, False otherwise

    Example:
        >>> success = await verify_rotation(new_key)
        >>> if success:
        >>>     print("Rotation verified - update .env with new key")
    """
    logger.info("Verifying key rotation...")

    try:
        new_cipher = Fernet(new_key.encode())
    except Exception as e:
        logger.error(f"✗ Invalid new key: {e}")
        return False

    # Connect to database
    if not db_url:
        db_url = settings.DATABASE_URL

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        async with async_session() as session:
            result = await session.execute(
                select(ApplicationSetting).filter_by(is_sensitive=True)
            )
            sensitive_settings = result.scalars().all()

            verified_count = 0
            for setting in sensitive_settings:
                if not setting.value:
                    continue

                try:
                    # Try to decrypt with new key
                    decrypted = new_cipher.decrypt(setting.value.encode()).decode()
                    logger.debug(f"✓ Verified {setting.key}")
                    verified_count += 1
                except InvalidToken:
                    logger.error(f"✗ Cannot decrypt {setting.key} with new key!")
                    return False

            logger.info(f"✓ Verified {verified_count} sensitive settings")
            return True

    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """CLI entry point for key rotation"""
    if len(sys.argv) != 3:
        print("Usage: python rotate_encryption_key.py OLD_KEY NEW_KEY")
        print("\nGenerate a new key with:")
        print('  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"')
        sys.exit(1)

    old_key = sys.argv[1]
    new_key = sys.argv[2]

    # Sanity check keys
    if old_key == new_key:
        logger.error("✗ Old and new keys are identical - nothing to rotate")
        sys.exit(1)

    if len(old_key) != 44 or len(new_key) != 44:
        logger.error("✗ Invalid key length - Fernet keys must be 44 characters")
        sys.exit(1)

    print("\n" + "="*60)
    print("🔐 ENCRYPTION KEY ROTATION")
    print("="*60)
    print("\n⚠️  WARNING: This will rotate the encryption key for all sensitive settings.")
    print("   Make sure you have:")
    print("   1. Backed up your database")
    print("   2. Verified the old key is correct")
    print("   3. Generated a secure new key")
    print("\n" + "="*60 + "\n")

    response = input("Continue? (yes/no): ").strip().lower()
    if response != "yes":
        print("Aborted.")
        sys.exit(0)

    try:
        # Rotate keys
        count = await rotate_encryption_key(old_key, new_key)

        print(f"\n✓ Rotated {count} sensitive settings")

        # Verify rotation
        print("\n🔍 Verifying rotation...")
        if await verify_rotation(new_key):
            print("\n" + "="*60)
            print("✅ SUCCESS! Key rotation complete and verified.")
            print("="*60)
            print("\n📝 NEXT STEPS:")
            print(f"   1. Update .env with: SETTINGS_ENCRYPTION_KEY={new_key}")
            print("   2. Restart the application")
            print("   3. Securely store/destroy the old key")
            print("\n" + "="*60 + "\n")
        else:
            print("\n" + "="*60)
            print("❌ VERIFICATION FAILED!")
            print("="*60)
            print("\nThe rotation completed but verification failed.")
            print("DO NOT update .env yet. Investigate the error above.")
            sys.exit(1)

    except KeyRotationError as e:
        print(f"\n❌ ROTATION FAILED: {e}")
        print("\nThe database was NOT modified (transaction rolled back).")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
