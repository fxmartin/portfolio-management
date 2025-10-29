# ABOUTME: Pydantic schemas for Prompt Management API (Epic 8 - F8.1-002)
# ABOUTME: Request/response models for prompt CRUD operations with validation

"""
Pydantic Schemas for Prompt Management

Provides request and response models for:
- Creating prompts
- Updating prompts
- Listing prompts
- Viewing prompt versions
"""

from typing import Dict, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    """Base prompt fields shared across create/update"""
    name: str = Field(..., min_length=1, max_length=100, description="Unique prompt name")
    category: Literal['global', 'position', 'forecast'] = Field(..., description="Prompt category")
    prompt_text: str = Field(..., min_length=10, description="The prompt template text")
    template_variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Template variable names to types (e.g., {'symbol': 'string', 'price': 'decimal'})"
    )


class PromptCreate(PromptBase):
    """Request schema for creating a new prompt"""
    pass


class PromptUpdate(BaseModel):
    """Request schema for updating a prompt (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[Literal['global', 'position', 'forecast']] = None
    prompt_text: Optional[str] = Field(None, min_length=10)
    template_variables: Optional[Dict[str, str]] = None
    change_reason: Optional[str] = Field(None, max_length=500, description="Reason for the change")


class PromptResponse(PromptBase):
    """Response schema for prompt"""
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class PromptListResponse(BaseModel):
    """Response schema for list of prompts"""
    prompts: List[PromptResponse]
    total: int
    skip: int
    limit: int


class PromptVersionResponse(BaseModel):
    """Response schema for prompt version history"""
    id: int
    prompt_id: int
    version: int
    prompt_text: str
    changed_by: Optional[str]
    changed_at: datetime
    change_reason: Optional[str]

    class Config:
        from_attributes = True


class PromptVersionListResponse(BaseModel):
    """Response schema for list of prompt versions"""
    versions: List[PromptVersionResponse]
    total: int


class RestoreVersionRequest(BaseModel):
    """Request schema for restoring a previous version"""
    change_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for restoring this version"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str


class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str
    success: bool = True
