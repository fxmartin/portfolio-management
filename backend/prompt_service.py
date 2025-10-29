# ABOUTME: Service layer for managing AI analysis prompts (Epic 8 - F8.1-002)
# ABOUTME: Provides CRUD operations, versioning, and prompt management functionality

"""
PromptService - Business logic for prompt management

Provides:
- List prompts with filtering and pagination
- Get prompts by ID or name
- Create new prompts
- Update prompts (automatically versions)
- Soft delete prompts
- Version history and restoration
"""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models import Prompt, PromptVersion


class PromptService:
    """Service for managing analysis prompts"""

    def __init__(self, db: AsyncSession):
        """
        Initialize PromptService

        Args:
            db: AsyncSession database session
        """
        self.db = db

    async def list_prompts(
        self,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prompt]:
        """
        List prompts with optional filtering and pagination

        Args:
            category: Filter by category ('global', 'position', 'forecast')
            active_only: Only return active prompts (default True)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of Prompt objects matching criteria
        """
        query = select(Prompt)

        # Apply filters
        if category:
            query = query.filter(Prompt.category == category)
        if active_only:
            query = query.filter(Prompt.is_active == 1)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """
        Get a specific prompt by ID

        Args:
            prompt_id: Prompt ID

        Returns:
            Prompt object or None if not found
        """
        result = await self.db.execute(
            select(Prompt).filter(Prompt.id == prompt_id)
        )
        return result.scalar_one_or_none()

    async def get_prompt_by_name(self, name: str) -> Optional[Prompt]:
        """
        Get a specific prompt by name

        Args:
            name: Unique prompt name

        Returns:
            Prompt object or None if not found
        """
        result = await self.db.execute(
            select(Prompt).filter(Prompt.name == name)
        )
        return result.scalar_one_or_none()

    async def create_prompt(
        self,
        name: str,
        category: str,
        prompt_text: str,
        template_variables: Dict[str, str]
    ) -> Prompt:
        """
        Create a new prompt

        Args:
            name: Unique prompt name
            category: Prompt category ('global', 'position', 'forecast')
            prompt_text: The prompt template text
            template_variables: Dict of variable names to types

        Returns:
            Created Prompt object

        Raises:
            ValueError: If prompt with name already exists
        """
        # Check for duplicate name
        existing = await self.get_prompt_by_name(name)
        if existing:
            raise ValueError(f"Prompt with name '{name}' already exists")

        # Create new prompt
        new_prompt = Prompt(
            name=name,
            category=category,
            prompt_text=prompt_text,
            template_variables=template_variables,
            is_active=1,
            version=1
        )

        self.db.add(new_prompt)
        await self.db.commit()
        await self.db.refresh(new_prompt)

        return new_prompt

    async def update_prompt(
        self,
        prompt_id: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
        prompt_text: Optional[str] = None,
        template_variables: Optional[Dict[str, str]] = None,
        change_reason: Optional[str] = None
    ) -> Prompt:
        """
        Update a prompt (creates a new version if content changes)

        Args:
            prompt_id: ID of prompt to update
            name: New name (optional)
            category: New category (optional)
            prompt_text: New prompt text (optional)
            template_variables: New template variables (optional)
            change_reason: Reason for the change (for version history)

        Returns:
            Updated Prompt object

        Raises:
            ValueError: If prompt not found
        """
        # Get existing prompt
        prompt = await self.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt with ID {prompt_id} not found")

        # Check if anything actually changed
        has_changes = False

        if prompt_text is not None and prompt_text != prompt.prompt_text:
            has_changes = True
        if template_variables is not None and template_variables != prompt.template_variables:
            has_changes = True
        if name is not None and name != prompt.name:
            has_changes = True
        if category is not None and category != prompt.category:
            has_changes = True

        if has_changes:
            # Create version record of current state BEFORE updating
            version_record = PromptVersion(
                prompt_id=prompt.id,
                version=prompt.version,
                prompt_text=prompt.prompt_text,
                changed_by="system",  # TODO: Get from auth context
                change_reason=change_reason
            )
            self.db.add(version_record)

            # Update prompt
            if name is not None:
                prompt.name = name
            if category is not None:
                prompt.category = category
            if prompt_text is not None:
                prompt.prompt_text = prompt_text
            if template_variables is not None:
                prompt.template_variables = template_variables

            # Increment version
            prompt.version += 1
            prompt.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(prompt)

        return prompt

    async def delete_prompt(self, prompt_id: int) -> bool:
        """
        Soft delete a prompt (sets is_active=False)

        Args:
            prompt_id: ID of prompt to delete

        Returns:
            True if deleted, False if not found
        """
        prompt = await self.get_prompt(prompt_id)
        if not prompt:
            return False

        prompt.is_active = 0
        await self.db.commit()

        return True

    async def get_prompt_versions(self, prompt_id: int) -> List[PromptVersion]:
        """
        Get version history for a prompt

        Args:
            prompt_id: ID of prompt

        Returns:
            List of PromptVersion objects, ordered by version number
        """
        result = await self.db.execute(
            select(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version)
        )
        return list(result.scalars().all())

    async def restore_prompt_version(
        self,
        prompt_id: int,
        version_number: int,
        change_reason: Optional[str] = None
    ) -> Prompt:
        """
        Restore a prompt to a previous version

        Args:
            prompt_id: ID of prompt to restore
            version_number: Version number to restore to
            change_reason: Reason for restoration

        Returns:
            Updated Prompt object

        Raises:
            ValueError: If prompt or version not found
        """
        # Get the version to restore
        result = await self.db.execute(
            select(PromptVersion).filter(
                PromptVersion.prompt_id == prompt_id,
                PromptVersion.version == version_number
            )
        )
        version_to_restore = result.scalar_one_or_none()

        if not version_to_restore:
            raise ValueError(f"Version {version_number} not found for prompt {prompt_id}")

        # Update prompt with version's content
        restored_prompt = await self.update_prompt(
            prompt_id=prompt_id,
            prompt_text=version_to_restore.prompt_text,
            change_reason=change_reason or f"Restored to version {version_number}"
        )

        return restored_prompt
