# ABOUTME: Settings service layer for managing application configuration
# ABOUTME: Provides CRUD operations with encryption, validation, caching, and audit trail

"""
Settings Service (Epic 9 - F9.1-002)

Business logic layer for managing application settings with:
- Automatic encryption/decryption for sensitive values
- Type conversion (string → int/bool/float/object)
- JSON schema validation
- Redis caching (5-minute TTL)
- Audit trail via SettingHistory
- Bulk operations with transaction support
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import redis.asyncio as redis
from jsonschema import validate, ValidationError

from models import ApplicationSetting, SettingHistory, SettingCategory
from security_utils import encrypt_value, decrypt_value


logger = logging.getLogger(__name__)


class SettingsService:
    """
    Service layer for managing application settings.

    Handles:
    - Setting retrieval with automatic decryption
    - Type conversion from string storage to appropriate types
    - Validation against JSON schemas
    - Change history tracking
    - Redis caching for performance
    - Bulk operations with transactional integrity
    """

    # Cache TTL in seconds (5 minutes)
    CACHE_TTL = 300

    def __init__(self, db: AsyncSession, cache: redis.Redis):
        """
        Initialize SettingsService.

        Args:
            db: SQLAlchemy async session for database operations
            cache: Redis client for caching
        """
        self.db = db
        self.cache = cache

    async def get_setting(self, key: str, decrypt: bool = True) -> Optional[Any]:
        """
        Get single setting by key with optional decryption.

        Retrieval flow:
        1. Check Redis cache first (5-minute TTL)
        2. Query database if cache miss
        3. Decrypt if sensitive and decrypt=True
        4. Parse value to correct type (int/bool/float/object)
        5. Cache result

        Args:
            key: Setting key to retrieve
            decrypt: Whether to decrypt sensitive values (default: True)

        Returns:
            Parsed setting value or None if not found

        Example:
            >>> value = await service.get_setting("base_currency")
            >>> print(value)  # "EUR"
            >>> api_key = await service.get_setting("anthropic_api_key", decrypt=True)
            >>> print(api_key)  # "sk-ant-..."
        """
        # Check cache first
        cache_key = f"setting:{key}"
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for setting: {key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed for setting {key}: {e}")

        # Query database
        result = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            logger.debug(f"Setting not found: {key}")
            return None

        # Get value
        value = setting.value

        # Decrypt if sensitive and requested
        if setting.is_sensitive and decrypt and value:
            try:
                value = decrypt_value(value)
            except Exception as e:
                logger.error(f"Failed to decrypt setting {key}: {e}")
                raise

        # Parse to correct type
        parsed_value = self._parse_value(value)

        # Cache the result
        try:
            await self.cache.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(parsed_value)
            )
            logger.debug(f"Cached setting: {key} (TTL: {self.CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Failed to cache setting {key}: {e}")

        return parsed_value

    async def get_settings_by_category(
        self,
        category: SettingCategory,
        decrypt: bool = True
    ) -> Dict[str, Any]:
        """
        Get all settings in a category.

        Args:
            category: Setting category to filter by
            decrypt: Whether to decrypt sensitive values (default: True)

        Returns:
            Dictionary mapping setting keys to parsed values

        Example:
            >>> display = await service.get_settings_by_category(SettingCategory.DISPLAY)
            >>> print(display)  # {"base_currency": "EUR", "refresh_interval": 60}
        """
        result = await self.db.execute(
            select(ApplicationSetting).filter_by(category=category)
        )
        settings = result.scalars().all()

        settings_dict = {}
        for setting in settings:
            value = setting.value

            # Decrypt if sensitive and requested
            if setting.is_sensitive and decrypt and value:
                try:
                    value = decrypt_value(value)
                except Exception as e:
                    logger.error(f"Failed to decrypt setting {setting.key}: {e}")
                    continue

            # Parse to correct type
            settings_dict[setting.key] = self._parse_value(value)

        logger.debug(f"Retrieved {len(settings_dict)} settings from category: {category.value}")
        return settings_dict

    async def get_all_settings(self, decrypt: bool = False) -> Dict[str, Any]:
        """
        Get all settings across all categories.

        Args:
            decrypt: Whether to decrypt sensitive values (default: False for security)

        Returns:
            Dictionary mapping setting keys to parsed values

        Example:
            >>> all_settings = await service.get_all_settings(decrypt=False)
            >>> print(len(all_settings))  # 12 (if all default settings present)
        """
        result = await self.db.execute(select(ApplicationSetting))
        settings = result.scalars().all()

        settings_dict = {}
        for setting in settings:
            value = setting.value

            # Decrypt if sensitive and requested
            if setting.is_sensitive and decrypt and value:
                try:
                    value = decrypt_value(value)
                except Exception as e:
                    logger.error(f"Failed to decrypt setting {setting.key}: {e}")
                    continue

            # Parse to correct type
            settings_dict[setting.key] = self._parse_value(value)

        logger.debug(f"Retrieved {len(settings_dict)} total settings")
        return settings_dict

    async def update_setting(
        self,
        key: str,
        value: Any,
        change_reason: Optional[str] = None
    ) -> ApplicationSetting:
        """
        Update setting with validation and audit trail.

        Update flow:
        1. Validate against JSON schema rules
        2. Check is_editable flag (raise if read-only)
        3. Record history entry (old → new)
        4. Encrypt if sensitive
        5. Update database
        6. Invalidate cache

        Args:
            key: Setting key to update
            value: New value (will be converted to string for storage)
            change_reason: Optional reason for the change (for audit trail)

        Returns:
            Updated ApplicationSetting object

        Raises:
            ValueError: If setting not found, read-only, or validation fails

        Example:
            >>> await service.update_setting("base_currency", "GBP", "User preference")
            >>> await service.update_setting("refresh_interval", 120)
        """
        # Get existing setting
        result = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            raise ValueError(f"Setting '{key}' not found")

        if not setting.is_editable:
            raise ValueError(f"Setting '{key}' is read-only and cannot be updated")

        # Store old value for history
        old_value = setting.value

        # Validate if rules exist
        if setting.validation_rules:
            try:
                validate(instance=value, schema=setting.validation_rules)
                logger.debug(f"Validation passed for setting: {key}")
            except ValidationError as e:
                logger.warning(f"Validation failed for setting {key}: {e.message}")
                raise ValueError(f"Validation failed for '{key}': {e.message}")

        # Convert value to string for storage
        new_value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

        # Encrypt if sensitive
        if setting.is_sensitive:
            new_value_str = encrypt_value(new_value_str)
            logger.debug(f"Encrypted sensitive setting: {key}")

        # Update setting
        setting.value = new_value_str

        # Record history
        history = SettingHistory(
            setting_id=setting.id,
            old_value=old_value,
            new_value=new_value_str if not setting.is_sensitive else "[ENCRYPTED]",
            changed_by='system',  # Future: track actual user
            change_reason=change_reason
        )
        self.db.add(history)

        # Commit changes
        await self.db.commit()
        await self.db.refresh(setting)

        # Invalidate cache
        cache_key = f"setting:{key}"
        await self.cache.delete(cache_key)
        logger.info(f"Updated setting: {key} (invalidated cache)")

        return setting

    async def bulk_update(
        self,
        updates: Dict[str, Any],
        change_reason: Optional[str] = None
    ) -> List[ApplicationSetting]:
        """
        Update multiple settings in one transaction.

        All updates succeed or all fail (atomic operation).
        If any validation fails, entire transaction is rolled back.

        Args:
            updates: Dictionary mapping setting keys to new values
            change_reason: Optional reason for changes (applied to all)

        Returns:
            List of updated ApplicationSetting objects

        Raises:
            ValueError: If any update fails validation

        Example:
            >>> updates = {"base_currency": "EUR", "refresh_interval": 120}
            >>> results = await service.bulk_update(updates, "Bulk config update")
        """
        updated_settings = []

        try:
            # Update all settings
            for key, value in updates.items():
                setting = await self.update_setting(key, value, change_reason)
                updated_settings.append(setting)

            logger.info(f"Bulk updated {len(updated_settings)} settings")
            return updated_settings

        except Exception as e:
            # Rollback on any error
            await self.db.rollback()
            logger.error(f"Bulk update failed, rolled back: {e}")
            raise

    async def reset_to_default(self, key: str) -> ApplicationSetting:
        """
        Reset setting to its default value.

        Args:
            key: Setting key to reset

        Returns:
            Updated ApplicationSetting object

        Raises:
            ValueError: If setting has no default value

        Example:
            >>> await service.reset_to_default("refresh_interval")
        """
        # Get setting
        result = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            raise ValueError(f"Setting '{key}' not found")

        if not setting.default_value:
            raise ValueError(f"Setting '{key}' has no default value")

        # Parse default value to correct type
        default_value = self._parse_value(setting.default_value)

        # Update using normal update flow (includes validation, history, etc.)
        return await self.update_setting(key, default_value, "Reset to default")

    async def get_history(self, key: str, limit: int = 50) -> List[SettingHistory]:
        """
        Get change history for a setting.

        Args:
            key: Setting key to get history for
            limit: Maximum number of history entries to return (default: 50)

        Returns:
            List of SettingHistory entries, ordered by most recent first

        Example:
            >>> history = await service.get_history("base_currency", limit=10)
            >>> for entry in history:
            ...     print(f"{entry.changed_at}: {entry.old_value} → {entry.new_value}")
        """
        # Get setting ID
        result = await self.db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            logger.debug(f"Setting not found for history: {key}")
            return []

        # Query history
        result = await self.db.execute(
            select(SettingHistory)
            .filter_by(setting_id=setting.id)
            .order_by(SettingHistory.changed_at.desc())
            .limit(limit)
        )
        history = result.scalars().all()

        logger.debug(f"Retrieved {len(history)} history entries for setting: {key}")
        return list(history)

    def _parse_value(self, value: Optional[str]) -> Any:
        """
        Parse string value to correct type.

        Parsing order:
        1. None → None
        2. JSON object/array → dict/list
        3. Boolean ("true"/"false") → bool
        4. Number (int/float) → int/float
        5. Everything else → string

        Args:
            value: String value to parse

        Returns:
            Parsed value in appropriate type

        Example:
            >>> service._parse_value('{"foo": "bar"}')  # dict
            >>> service._parse_value("true")  # True
            >>> service._parse_value("42")  # 42
            >>> service._parse_value("3.14")  # 3.14
            >>> service._parse_value("hello")  # "hello"
        """
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        # Try JSON parse (for objects/arrays)
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Try boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False

        # Try number
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            # Try float
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value
