"""
Tests for Epic 8 Prompt Service (F8.1-002)

Test-Driven Development for PromptService:
- list_prompts (with pagination and filtering)
- get_prompt (by ID)
- get_prompt_by_name (by name)
- create_prompt
- update_prompt (creates version)
- delete_prompt (soft delete)
- get_prompt_versions (version history)
- restore_prompt_version
"""

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from models import Prompt, PromptVersion, Base
from prompt_service import PromptService


# Use SQLite for testing (in-memory database)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session
    async with TestSessionLocal() as session:
        yield session

    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def prompt_service(db_session):
    """Create a PromptService instance"""
    return PromptService(db_session)


@pytest_asyncio.fixture
async def sample_prompts(db_session):
    """Create sample prompts for testing"""
    prompts = [
        Prompt(
            name="test_global",
            category="global",
            prompt_text="Global analysis prompt with {portfolio_value}",
            template_variables={"portfolio_value": "decimal"},
            is_active=1,
            version=1
        ),
        Prompt(
            name="test_position",
            category="position",
            prompt_text="Position analysis for {symbol}",
            template_variables={"symbol": "string"},
            is_active=1,
            version=1
        ),
        Prompt(
            name="test_forecast",
            category="forecast",
            prompt_text="Forecast for {symbol} with {market_context}",
            template_variables={"symbol": "string", "market_context": "string"},
            is_active=1,
            version=1
        ),
        Prompt(
            name="test_inactive",
            category="global",
            prompt_text="Inactive prompt",
            template_variables={},
            is_active=0,
            version=1
        )
    ]

    for prompt in prompts:
        db_session.add(prompt)
    await db_session.commit()

    return prompts


class TestListPrompts:
    """Test listing prompts with various filters"""

    @pytest.mark.asyncio
    async def test_list_all_active_prompts(self, prompt_service, sample_prompts):
        """Test listing all active prompts"""
        prompts = await prompt_service.list_prompts()

        assert len(prompts) == 3  # Only active prompts
        prompt_names = [p.name for p in prompts]
        assert "test_global" in prompt_names
        assert "test_position" in prompt_names
        assert "test_forecast" in prompt_names
        assert "test_inactive" not in prompt_names

    @pytest.mark.asyncio
    async def test_list_all_prompts_including_inactive(self, prompt_service, sample_prompts):
        """Test listing all prompts including inactive"""
        prompts = await prompt_service.list_prompts(active_only=False)

        assert len(prompts) == 4  # All prompts
        prompt_names = [p.name for p in prompts]
        assert "test_inactive" in prompt_names

    @pytest.mark.asyncio
    async def test_list_prompts_filtered_by_category(self, prompt_service, sample_prompts):
        """Test filtering prompts by category"""
        prompts = await prompt_service.list_prompts(category="position")

        assert len(prompts) == 1
        assert prompts[0].name == "test_position"
        assert prompts[0].category == "position"

    @pytest.mark.asyncio
    async def test_list_prompts_with_pagination(self, prompt_service, sample_prompts):
        """Test pagination of prompt list"""
        # Get first page
        page1 = await prompt_service.list_prompts(skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await prompt_service.list_prompts(skip=2, limit=2)
        assert len(page2) == 1

        # Verify no overlap
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_list_prompts_empty_result(self, prompt_service):
        """Test listing prompts with no matches"""
        prompts = await prompt_service.list_prompts(category="nonexistent")
        assert len(prompts) == 0


class TestGetPrompt:
    """Test retrieving individual prompts"""

    @pytest.mark.asyncio
    async def test_get_prompt_by_id(self, prompt_service, sample_prompts):
        """Test getting a prompt by ID"""
        target_prompt = sample_prompts[0]

        prompt = await prompt_service.get_prompt(target_prompt.id)

        assert prompt is not None
        assert prompt.id == target_prompt.id
        assert prompt.name == target_prompt.name
        assert prompt.category == target_prompt.category

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_not_found(self, prompt_service, sample_prompts):
        """Test getting a non-existent prompt"""
        prompt = await prompt_service.get_prompt(99999)
        assert prompt is None

    @pytest.mark.asyncio
    async def test_get_prompt_by_name(self, prompt_service, sample_prompts):
        """Test getting a prompt by name"""
        prompt = await prompt_service.get_prompt_by_name("test_global")

        assert prompt is not None
        assert prompt.name == "test_global"
        assert prompt.category == "global"

    @pytest.mark.asyncio
    async def test_get_prompt_by_name_not_found(self, prompt_service, sample_prompts):
        """Test getting a non-existent prompt by name"""
        prompt = await prompt_service.get_prompt_by_name("nonexistent")
        assert prompt is None

    @pytest.mark.asyncio
    async def test_get_inactive_prompt(self, prompt_service, sample_prompts):
        """Test that we can get inactive prompts"""
        prompt = await prompt_service.get_prompt_by_name("test_inactive")

        assert prompt is not None
        assert prompt.is_active == 0


class TestCreatePrompt:
    """Test creating new prompts"""

    @pytest.mark.asyncio
    async def test_create_prompt_success(self, prompt_service, db_session):
        """Test creating a new prompt"""
        new_prompt = await prompt_service.create_prompt(
            name="new_test_prompt",
            category="global",
            prompt_text="New test prompt with {variable}",
            template_variables={"variable": "string"}
        )

        assert new_prompt.id is not None
        assert new_prompt.name == "new_test_prompt"
        assert new_prompt.category == "global"
        assert new_prompt.version == 1
        assert new_prompt.is_active == 1

    @pytest.mark.asyncio
    async def test_create_prompt_duplicate_name(self, prompt_service, sample_prompts):
        """Test creating a prompt with duplicate name fails"""
        with pytest.raises(ValueError, match="already exists"):
            await prompt_service.create_prompt(
                name="test_global",  # Already exists
                category="position",
                prompt_text="Duplicate name",
                template_variables={}
            )

    @pytest.mark.asyncio
    async def test_create_prompt_minimal_data(self, prompt_service, db_session):
        """Test creating a prompt with minimal required fields"""
        new_prompt = await prompt_service.create_prompt(
            name="minimal",
            category="forecast",
            prompt_text="Minimal prompt text here",
            template_variables={}
        )

        assert new_prompt.id is not None
        assert new_prompt.template_variables == {}


class TestUpdatePrompt:
    """Test updating prompts (creates new version)"""

    @pytest.mark.asyncio
    async def test_update_prompt_creates_version(self, prompt_service, sample_prompts, db_session):
        """Test that updating a prompt creates a new version"""
        original_prompt = sample_prompts[0]
        original_text = original_prompt.prompt_text
        original_version = original_prompt.version

        updated = await prompt_service.update_prompt(
            prompt_id=original_prompt.id,
            prompt_text="Updated prompt text",
            change_reason="Testing update"
        )

        # Check updated prompt
        assert updated.version == original_version + 1
        assert updated.prompt_text == "Updated prompt text"

        # Verify version was saved
        versions = await prompt_service.get_prompt_versions(original_prompt.id)
        assert len(versions) >= 1
        assert versions[0].version == original_version
        assert versions[0].prompt_text == original_text

    @pytest.mark.asyncio
    async def test_update_prompt_all_fields(self, prompt_service, sample_prompts, db_session):
        """Test updating all fields of a prompt"""
        original = sample_prompts[0]

        # Refresh to get current state (in case other tests modified it)
        await db_session.refresh(original)
        original_version = original.version

        updated = await prompt_service.update_prompt(
            prompt_id=original.id,
            name="updated_name",
            category="position",
            prompt_text="Completely new text",
            template_variables={"new_var": "integer"},
            change_reason="Full update"
        )

        assert updated.name == "updated_name"
        assert updated.category == "position"
        assert updated.prompt_text == "Completely new text"
        assert updated.template_variables == {"new_var": "integer"}
        assert updated.version == original_version + 1

    @pytest.mark.asyncio
    async def test_update_prompt_not_found(self, prompt_service):
        """Test updating a non-existent prompt"""
        with pytest.raises(ValueError, match="not found"):
            await prompt_service.update_prompt(
                prompt_id=99999,
                prompt_text="Updated text"
            )

    @pytest.mark.asyncio
    async def test_update_prompt_no_changes(self, prompt_service, sample_prompts):
        """Test updating with no actual changes doesn't create version"""
        original = sample_prompts[0]
        original_version = original.version

        # Update with same values
        updated = await prompt_service.update_prompt(
            prompt_id=original.id,
            prompt_text=original.prompt_text,
            template_variables=original.template_variables
        )

        # Version should not increment if nothing changed
        assert updated.version == original_version


class TestDeletePrompt:
    """Test soft deleting prompts"""

    @pytest.mark.asyncio
    async def test_delete_prompt_soft_delete(self, prompt_service, sample_prompts):
        """Test soft deleting a prompt"""
        prompt_to_delete = sample_prompts[0]

        result = await prompt_service.delete_prompt(prompt_to_delete.id)

        assert result is True

        # Verify it's deactivated, not actually deleted
        deleted_prompt = await prompt_service.get_prompt(prompt_to_delete.id)
        assert deleted_prompt is not None
        assert deleted_prompt.is_active == 0

    @pytest.mark.asyncio
    async def test_delete_prompt_not_in_active_list(self, prompt_service, sample_prompts):
        """Test that deleted prompts don't appear in active list"""
        prompt_to_delete = sample_prompts[0]

        await prompt_service.delete_prompt(prompt_to_delete.id)

        active_prompts = await prompt_service.list_prompts(active_only=True)
        active_ids = [p.id for p in active_prompts]
        assert prompt_to_delete.id not in active_ids

    @pytest.mark.asyncio
    async def test_delete_prompt_not_found(self, prompt_service):
        """Test deleting a non-existent prompt"""
        result = await prompt_service.delete_prompt(99999)
        assert result is False


class TestPromptVersions:
    """Test version history functionality"""

    @pytest.mark.asyncio
    async def test_get_prompt_versions_empty(self, prompt_service, sample_prompts):
        """Test getting versions for prompt with no history"""
        prompt = sample_prompts[0]

        versions = await prompt_service.get_prompt_versions(prompt.id)
        assert len(versions) == 0  # No updates yet, no versions

    @pytest.mark.asyncio
    async def test_get_prompt_versions_after_updates(self, prompt_service, sample_prompts, db_session):
        """Test version history after multiple updates"""
        prompt = sample_prompts[0]

        # Make several updates
        await prompt_service.update_prompt(prompt.id, prompt_text="Version 2", change_reason="Update 1")
        await prompt_service.update_prompt(prompt.id, prompt_text="Version 3", change_reason="Update 2")
        await prompt_service.update_prompt(prompt.id, prompt_text="Version 4", change_reason="Update 3")

        versions = await prompt_service.get_prompt_versions(prompt.id)

        assert len(versions) == 3  # Three previous versions
        assert versions[0].version == 1  # Ordered by version
        assert versions[1].version == 2
        assert versions[2].version == 3

    @pytest.mark.asyncio
    async def test_restore_prompt_version(self, prompt_service, sample_prompts, db_session):
        """Test restoring a previous version"""
        prompt = sample_prompts[0]
        original_text = prompt.prompt_text

        # Update twice
        await prompt_service.update_prompt(prompt.id, prompt_text="Version 2")
        await prompt_service.update_prompt(prompt.id, prompt_text="Version 3")

        # Restore to version 1
        restored = await prompt_service.restore_prompt_version(
            prompt_id=prompt.id,
            version_number=1,
            change_reason="Restoring to original"
        )

        assert restored.prompt_text == original_text
        assert restored.version == 4  # New version number

        # Check version history shows the restore
        versions = await prompt_service.get_prompt_versions(prompt.id)
        assert len(versions) == 3  # Versions 1, 2, 3 (not 4 which is current)

    @pytest.mark.asyncio
    async def test_restore_version_not_found(self, prompt_service, sample_prompts):
        """Test restoring a non-existent version"""
        prompt = sample_prompts[0]

        with pytest.raises(ValueError, match="Version.*not found"):
            await prompt_service.restore_prompt_version(
                prompt_id=prompt.id,
                version_number=99
            )


class TestPromptValidation:
    """Test validation logic in PromptService"""

    @pytest.mark.asyncio
    async def test_validate_template_variables(self, prompt_service):
        """Test that template variables are validated"""
        # This will be implemented when we add template variable validation
        # For now, just verify we can create with various variable types
        prompt = await prompt_service.create_prompt(
            name="validation_test",
            category="global",
            prompt_text="Test {var1} and {var2}",
            template_variables={
                "var1": "string",
                "var2": "decimal",
                "var3": "integer"
            }
        )

        assert prompt.template_variables["var1"] == "string"
        assert prompt.template_variables["var2"] == "decimal"
