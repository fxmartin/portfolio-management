# ABOUTME: FastAPI router for Settings API endpoints (Epic 9 - F9.1-003)
# ABOUTME: RESTful API for managing application settings with encryption and validation

"""
Settings API Router (Epic 9 - F9.1-003)

REST endpoints for application settings management:
- GET /api/settings/categories - List all setting categories
- GET /api/settings/category/{category} - Get settings by category
- GET /api/settings/{key} - Get single setting
- PUT /api/settings/{key} - Update setting value
- POST /api/settings/bulk - Bulk update settings
- POST /api/settings/{key}/reset - Reset setting to default
- GET /api/settings/{key}/history - Get change history
- POST /api/settings/{key}/validate - Validate value without saving
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import logging

from database import get_async_db
from cache_service import CacheService
from settings_service import SettingsService
from settings_schemas import (
    SettingResponse,
    SettingUpdateRequest,
    BulkUpdateRequest,
    SettingValidateRequest,
    SettingHistoryResponse,
    CategorySettingsResponse,
    ValidationResponse,
    ErrorResponse
)
from models import SettingCategory, ApplicationSetting
from security_utils import decrypt_value


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ==================== DEPENDENCY INJECTION ====================

async def get_settings_service(
    db: AsyncSession = Depends(get_async_db)
) -> SettingsService:
    """
    Dependency injection for SettingsService.

    Creates a SettingsService instance with database and Redis cache.
    """
    cache_service = CacheService()
    return SettingsService(db, cache_service.client)


# ==================== ENDPOINTS ====================

@router.get(
    "/categories",
    response_model=List[str],
    summary="List all setting categories",
    description="Get list of all available setting categories"
)
async def list_categories() -> List[str]:
    """
    Get all setting categories.

    Returns:
        List of category names (display, api_keys, prompts, system, advanced)
    """
    try:
        # Return all enum values
        categories = [category.value for category in SettingCategory]
        return categories

    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/category/{category}",
    response_model=CategorySettingsResponse,
    summary="Get settings by category",
    description="Get all settings in a specific category with optional decryption",
    responses={
        200: {"description": "Category settings retrieved successfully"},
        422: {"description": "Invalid category"}
    }
)
async def get_settings_by_category(
    category: SettingCategory = Path(..., description="Setting category"),
    decrypt: bool = Query(False, description="Decrypt sensitive values"),
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> CategorySettingsResponse:
    """
    Get all settings in a category.

    Args:
        category: Setting category (display, api_keys, prompts, system, advanced)
        decrypt: Whether to decrypt sensitive values (default: False, shows masked)

    Returns:
        CategorySettingsResponse with all settings in the category

    Note:
        Sensitive values are masked with "********" unless decrypt=true
    """
    try:
        # Query database for all settings in category
        result = await db.execute(
            select(ApplicationSetting).filter_by(category=category)
        )
        settings = result.scalars().all()

        # Convert to response format
        settings_responses = {}
        for setting in settings:
            # Decrypt if requested
            if setting.is_sensitive and decrypt and setting.value:
                try:
                    setting.value = decrypt_value(setting.value)
                except Exception as e:
                    logger.error(f"Failed to decrypt setting {setting.key}: {e}")

            # Parse value to correct type
            setting.value = service._parse_value(setting.value)

            # Mask sensitive values if not decrypting
            if setting.is_sensitive and not decrypt and setting.value:
                setting.value = "********"

            settings_responses[setting.key] = SettingResponse.model_validate(setting)

        return CategorySettingsResponse(
            category=category,
            settings=settings_responses
        )

    except Exception as e:
        logger.error(f"Error getting category settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{key}",
    response_model=SettingResponse,
    summary="Get single setting",
    description="Get setting by key with optional value reveal for sensitive settings",
    responses={
        200: {"description": "Setting retrieved successfully"},
        404: {"description": "Setting not found"}
    }
)
async def get_setting(
    key: str = Path(..., description="Setting key"),
    reveal: bool = Query(False, description="Reveal sensitive value"),
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> SettingResponse:
    """
    Get single setting by key.

    Args:
        key: Setting key
        reveal: Whether to reveal sensitive values (default: False, shows masked)

    Returns:
        SettingResponse with setting details

    Raises:
        404: Setting not found

    Note:
        Sensitive values are masked with "********" unless reveal=true
    """
    try:
        # Query database
        result = await db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )

        # Decrypt if requested
        if setting.is_sensitive and reveal and setting.value:
            try:
                setting.value = decrypt_value(setting.value)
            except Exception as e:
                logger.error(f"Failed to decrypt setting {key}: {e}")

        # Parse value to correct type
        setting.value = service._parse_value(setting.value)

        # Mask sensitive value unless explicitly revealed
        if setting.is_sensitive and not reveal and setting.value:
            setting.value = "********"

        return SettingResponse.model_validate(setting)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setting '{key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{key}",
    response_model=SettingResponse,
    summary="Update setting value",
    description="Update setting value with validation and audit trail",
    responses={
        200: {"description": "Setting updated successfully"},
        400: {"description": "Validation failed or read-only setting"},
        404: {"description": "Setting not found"}
    }
)
async def update_setting(
    key: str = Path(..., description="Setting key"),
    request: SettingUpdateRequest = ...,
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> SettingResponse:
    """
    Update setting value.

    Args:
        key: Setting key
        request: Update request with new value and optional change reason

    Returns:
        SettingResponse with updated setting

    Raises:
        404: Setting not found
        400: Validation failed or setting is read-only

    Note:
        - Validates value against JSON schema rules
        - Records change in history with reason
        - Invalidates cache
        - Encrypts sensitive values automatically
    """
    try:
        updated_setting = await service.update_setting(
            key,
            request.value,
            change_reason=request.change_reason
        )

        # Refresh to get latest state
        await db.refresh(updated_setting)

        # Parse value to correct type (it's stored as encrypted string in DB)
        if updated_setting.is_sensitive and updated_setting.value:
            # Decrypt temporarily to parse
            try:
                decrypted = decrypt_value(updated_setting.value)
                updated_setting.value = service._parse_value(decrypted)
            except Exception:
                pass
        else:
            updated_setting.value = service._parse_value(updated_setting.value)

        # Mask sensitive values in response
        if updated_setting.is_sensitive and updated_setting.value:
            updated_setting.value = "********"

        return SettingResponse.model_validate(updated_setting)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Error updating setting '{key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/bulk",
    response_model=List[SettingResponse],
    summary="Bulk update settings",
    description="Update multiple settings in a single transaction",
    responses={
        200: {"description": "Settings updated successfully"},
        400: {"description": "Validation failed, all changes rolled back"},
        422: {"description": "Invalid request format"}
    }
)
async def bulk_update_settings(
    request: BulkUpdateRequest = ...,
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> List[SettingResponse]:
    """
    Update multiple settings in a single transaction.

    Args:
        request: Bulk update request with dict of key: value pairs

    Returns:
        List of SettingResponse for all updated settings

    Raises:
        400: Any validation failed, all changes rolled back

    Note:
        - All updates succeed or all fail (transactional)
        - Records history for each setting
        - Invalidates cache for all updated settings
    """
    try:
        updated_settings = await service.bulk_update(
            request.updates,
            change_reason=request.change_reason
        )

        # Mask sensitive values in responses
        responses = []
        for setting in updated_settings:
            await db.refresh(setting)

            # Parse value to correct type
            if setting.is_sensitive and setting.value:
                try:
                    decrypted = decrypt_value(setting.value)
                    setting.value = service._parse_value(decrypted)
                except Exception:
                    pass
            else:
                setting.value = service._parse_value(setting.value)

            # Mask sensitive values
            if setting.is_sensitive and setting.value:
                setting.value = "********"

            responses.append(SettingResponse.model_validate(setting))

        return responses

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error bulk updating settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{key}/reset",
    response_model=SettingResponse,
    summary="Reset setting to default",
    description="Reset setting to its default value",
    responses={
        200: {"description": "Setting reset successfully"},
        400: {"description": "Setting has no default value"},
        404: {"description": "Setting not found"}
    }
)
async def reset_setting(
    key: str = Path(..., description="Setting key"),
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> SettingResponse:
    """
    Reset setting to default value.

    Args:
        key: Setting key

    Returns:
        SettingResponse with reset setting

    Raises:
        404: Setting not found
        400: Setting has no default value

    Note:
        - Records change in history
        - Invalidates cache
    """
    try:
        reset_setting_obj = await service.reset_to_default(key)

        # Refresh to get latest state
        await db.refresh(reset_setting_obj)

        # Parse value to correct type
        if reset_setting_obj.is_sensitive and reset_setting_obj.value:
            try:
                decrypted = decrypt_value(reset_setting_obj.value)
                reset_setting_obj.value = service._parse_value(decrypted)
            except Exception:
                pass
        else:
            reset_setting_obj.value = service._parse_value(reset_setting_obj.value)

        # Mask sensitive values in response
        if reset_setting_obj.is_sensitive and reset_setting_obj.value:
            reset_setting_obj.value = "********"

        return SettingResponse.model_validate(reset_setting_obj)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Error resetting setting '{key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{key}/history",
    response_model=List[SettingHistoryResponse],
    summary="Get setting change history",
    description="Get audit trail of changes for a setting",
    responses={
        200: {"description": "History retrieved successfully"},
        404: {"description": "Setting not found"}
    }
)
async def get_setting_history(
    key: str = Path(..., description="Setting key"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of history entries"),
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> List[SettingHistoryResponse]:
    """
    Get change history for a setting.

    Args:
        key: Setting key
        limit: Maximum number of history entries (1-100, default: 50)

    Returns:
        List of SettingHistoryResponse (newest first)

    Raises:
        404: Setting not found

    Note:
        - Returns empty list if no changes have been made
        - Ordered by changed_at descending (newest first)
    """
    try:
        # First check if setting exists
        result = await db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )

        history = await service.get_history(key, limit=limit)

        return [
            SettingHistoryResponse.model_validate(entry)
            for entry in history
        ]

    except HTTPException:
        raise
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting history for setting '{key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{key}/validate",
    response_model=ValidationResponse,
    summary="Validate setting value",
    description="Validate a value without saving it",
    responses={
        200: {"description": "Validation result returned"},
        404: {"description": "Setting not found"}
    }
)
async def validate_setting_value(
    key: str = Path(..., description="Setting key"),
    request: SettingValidateRequest = ...,
    service: SettingsService = Depends(get_settings_service),
    db: AsyncSession = Depends(get_async_db)
) -> ValidationResponse:
    """
    Validate a value without saving it.

    Args:
        key: Setting key
        request: Validation request with value to validate

    Returns:
        ValidationResponse with validation result

    Raises:
        404: Setting not found

    Note:
        - Checks value against JSON schema rules
        - Performs type conversion
        - Does not save value or create history entry
    """
    try:
        # Get setting
        result = await db.execute(
            select(ApplicationSetting).filter_by(key=key)
        )
        setting = result.scalar_one_or_none()

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )

        # Parse value to correct type first
        validated_value = service._parse_value(str(request.value))

        # If no validation rules, always valid
        if not setting.validation_rules:
            return ValidationResponse(
                valid=True,
                error=None,
                validated_value=validated_value
            )

        # Try to validate (use the parsed value, not the original)
        try:
            from jsonschema import validate, ValidationError
            validate(instance=validated_value, schema=setting.validation_rules)
            return ValidationResponse(
                valid=True,
                error=None,
                validated_value=validated_value
            )
        except ValidationError as e:
            return ValidationResponse(
                valid=False,
                error=str(e.message),
                validated_value=None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating setting '{key}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
