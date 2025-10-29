# ABOUTME: FastAPI router for Prompt Management API endpoints (Epic 8 - F8.1-002)
# ABOUTME: RESTful API for CRUD operations on AI analysis prompts

"""
Prompt Management API Router

Endpoints:
- GET /api/prompts - List prompts with filtering
- GET /api/prompts/{id} - Get prompt by ID
- GET /api/prompts/name/{name} - Get prompt by name
- POST /api/prompts - Create new prompt
- PUT /api/prompts/{id} - Update prompt
- DELETE /api/prompts/{id} - Soft delete prompt
- GET /api/prompts/{id}/versions - Get version history
- POST /api/prompts/{id}/restore/{version} - Restore version
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_db
from prompt_service import PromptService
from prompt_schemas import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptListResponse,
    PromptVersionListResponse,
    RestoreVersionRequest,
    SuccessResponse
)


router = APIRouter(prefix="/api/prompts", tags=["prompts"])


def get_prompt_service(db: AsyncSession = Depends(get_async_db)) -> PromptService:
    """Dependency to get PromptService instance"""
    return PromptService(db)


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only show active prompts"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    service: PromptService = Depends(get_prompt_service)
):
    """
    List all prompts with optional filtering and pagination

    - **category**: Filter by category ('global', 'position', 'forecast')
    - **active_only**: Only return active prompts (default: true)
    - **skip**: Pagination offset (default: 0)
    - **limit**: Page size (default: 100, max: 500)
    """
    prompts = await service.list_prompts(
        category=category,
        active_only=active_only,
        skip=skip,
        limit=limit
    )

    return PromptListResponse(
        prompts=prompts,
        total=len(prompts),
        skip=skip,
        limit=limit
    )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int = Path(..., description="Prompt ID"),
    service: PromptService = Depends(get_prompt_service)
):
    """
    Get a specific prompt by ID

    Returns the prompt with all metadata including version and active status.
    """
    prompt = await service.get_prompt(prompt_id)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found"
        )

    return prompt


@router.get("/name/{name}", response_model=PromptResponse)
async def get_prompt_by_name(
    name: str = Path(..., description="Prompt name"),
    service: PromptService = Depends(get_prompt_service)
):
    """
    Get a specific prompt by unique name

    Useful for retrieving prompts by their well-known names like
    'global_market_analysis' or 'position_analysis'.
    """
    prompt = await service.get_prompt_by_name(name)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with name '{name}' not found"
        )

    return prompt


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Create a new prompt

    - **name**: Unique identifier for the prompt
    - **category**: Must be 'global', 'position', or 'forecast'
    - **prompt_text**: The template text with {variable} placeholders
    - **template_variables**: Dict mapping variable names to types
    """
    try:
        new_prompt = await service.create_prompt(
            name=prompt_data.name,
            category=prompt_data.category,
            prompt_text=prompt_data.prompt_text,
            template_variables=prompt_data.template_variables
        )
        return new_prompt

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int = Path(..., description="Prompt ID"),
    update_data: PromptUpdate = ...,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Update a prompt (automatically creates a version record)

    When a prompt is updated, the previous state is saved to version history.
    Only fields provided in the request will be updated.

    - Creates a new version record before updating
    - Increments the version number
    - Supports partial updates (only specify fields to change)
    """
    try:
        updated_prompt = await service.update_prompt(
            prompt_id=prompt_id,
            name=update_data.name,
            category=update_data.category,
            prompt_text=update_data.prompt_text,
            template_variables=update_data.template_variables,
            change_reason=update_data.change_reason
        )
        return updated_prompt

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{prompt_id}", response_model=SuccessResponse)
async def delete_prompt(
    prompt_id: int = Path(..., description="Prompt ID"),
    service: PromptService = Depends(get_prompt_service)
):
    """
    Soft delete a prompt (sets is_active=false)

    The prompt is not actually deleted from the database, just marked as inactive.
    It will no longer appear in active prompt lists but can still be retrieved by ID.

    Version history is preserved.
    """
    success = await service.delete_prompt(prompt_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found"
        )

    return SuccessResponse(
        message=f"Prompt {prompt_id} has been deactivated",
        success=True
    )


@router.get("/{prompt_id}/versions", response_model=PromptVersionListResponse)
async def get_prompt_versions(
    prompt_id: int = Path(..., description="Prompt ID"),
    service: PromptService = Depends(get_prompt_service)
):
    """
    Get version history for a prompt

    Returns all previous versions in chronological order.
    Each version includes the prompt text, who changed it, when, and why.
    """
    # Verify prompt exists
    prompt = await service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found"
        )

    versions = await service.get_prompt_versions(prompt_id)

    return PromptVersionListResponse(
        versions=versions,
        total=len(versions)
    )


@router.post("/{prompt_id}/restore/{version_number}", response_model=PromptResponse)
async def restore_prompt_version(
    prompt_id: int = Path(..., description="Prompt ID"),
    version_number: int = Path(..., description="Version number to restore"),
    restore_data: RestoreVersionRequest = RestoreVersionRequest(),
    service: PromptService = Depends(get_prompt_service)
):
    """
    Restore a prompt to a previous version

    Creates a new version with the content from the specified historical version.
    This does not delete the interim versions - it creates a new version that
    copies the old content.

    - **prompt_id**: The prompt to restore
    - **version_number**: Which version to restore to
    - **change_reason**: Optional reason for the restoration
    """
    try:
        restored_prompt = await service.restore_prompt_version(
            prompt_id=prompt_id,
            version_number=version_number,
            change_reason=restore_data.change_reason
        )
        return restored_prompt

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
