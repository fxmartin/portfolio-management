# ABOUTME: Pydantic schemas for Settings API request/response models (Epic 9 - F9.1-003)
# ABOUTME: Defines validation models for settings REST endpoints

"""
Settings API Schemas

Request and response models for Settings REST API endpoints.
Provides type safety and automatic validation for:
- Setting retrieval and updates
- Bulk operations
- History tracking
- Value validation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional
from datetime import datetime
from models import SettingCategory


class SettingResponse(BaseModel):
    """
    Response model for single setting.

    Returns setting details with automatic masking
    of sensitive values unless explicitly revealed.
    """
    key: str = Field(..., description="Unique setting key")
    value: Any = Field(..., description="Setting value (masked if sensitive)")
    category: SettingCategory = Field(..., description="Setting category")
    is_sensitive: bool = Field(..., description="Whether value is encrypted")
    is_editable: bool = Field(..., description="Whether setting can be modified")
    description: Optional[str] = Field(None, description="Setting description")
    default_value: Optional[str] = Field(None, description="Default value")
    last_modified_at: datetime = Field(..., description="Last modification timestamp")

    model_config = ConfigDict(from_attributes=True)


class SettingUpdateRequest(BaseModel):
    """Request to update a setting value."""
    value: Any = Field(..., description="New value to set")
    change_reason: Optional[str] = Field(
        None,
        description="Reason for change (for audit trail)",
        max_length=500
    )


class BulkUpdateRequest(BaseModel):
    """Request to update multiple settings."""
    updates: Dict[str, Any] = Field(
        ...,
        description="Dictionary of key: value pairs to update",
        min_length=1
    )
    change_reason: Optional[str] = Field(
        None,
        description="Reason for changes (for audit trail)",
        max_length=500
    )


class SettingValidateRequest(BaseModel):
    """Request to validate a value without saving."""
    value: Any = Field(..., description="Value to validate")


class SettingHistoryResponse(BaseModel):
    """Response model for setting change history."""
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    changed_by: str = Field(..., description="Who made the change")
    changed_at: datetime = Field(..., description="When change occurred")
    change_reason: Optional[str] = Field(None, description="Reason for change")

    model_config = ConfigDict(from_attributes=True)


class CategorySettingsResponse(BaseModel):
    """Response for category-based settings."""
    category: SettingCategory = Field(..., description="Setting category")
    settings: Dict[str, SettingResponse] = Field(
        ...,
        description="Dictionary of settings in this category"
    )


class ValidationResponse(BaseModel):
    """Response for setting validation."""
    valid: bool = Field(..., description="Whether value is valid")
    error: Optional[str] = Field(None, description="Validation error message")
    validated_value: Optional[Any] = Field(
        None,
        description="Value after type conversion"
    )


class CategoryInfo(BaseModel):
    """Response model for setting category information."""
    key: str = Field(..., description="Category key identifier")
    name: str = Field(..., description="Human-readable category name")
    description: Optional[str] = Field(None, description="Category description")


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
