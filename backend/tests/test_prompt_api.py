"""
Integration Tests for Prompt Management API (F8.1-002)

Tests all 8 REST endpoints:
- GET /api/prompts - List prompts
- GET /api/prompts/{id} - Get prompt by ID
- GET /api/prompts/name/{name} - Get prompt by name
- POST /api/prompts - Create prompt
- PUT /api/prompts/{id} - Update prompt
- DELETE /api/prompts/{id} - Delete prompt
- GET /api/prompts/{id}/versions - Get version history
- POST /api/prompts/{id}/restore/{version} - Restore version
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from models import Prompt, Base
from main import app
from database import get_async_db


# Use file-based SQLite for testing to ensure proper data persistence across requests
import tempfile
import os

# Create a temporary database file that will be deleted after tests
test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{test_db_path}"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=True  # Expire objects after commit to force refresh from DB
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create test database for each test"""
    # Create tables once
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Override the dependency to create a new session for each request
    async def override_get_async_db():
        async with TestSessionLocal() as session:
            yield session
            # Commit is handled by the service layer

    app.dependency_overrides[get_async_db] = override_get_async_db

    # Yield a session for test use (if needed)
    async with TestSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Clear dependency override
    app.dependency_overrides.clear()


# Cleanup temp database file after all tests
def pytest_sessionfinish(session, exitstatus):
    """Cleanup temp database file after all tests"""
    try:
        os.close(test_db_fd)
        os.unlink(test_db_path)
    except:
        pass


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with shared database session"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def sample_prompt(client):
    """Create a sample prompt for testing"""
    response = await client.post("/api/prompts", json={
        "name": "test_prompt",
        "category": "global",
        "prompt_text": "Test prompt with {variable}",
        "template_variables": {"variable": "string"}
    })
    assert response.status_code == 201
    return response.json()


class TestListPrompts:
    """Test GET /api/prompts"""

    @pytest.mark.asyncio
    async def test_list_empty_prompts(self, client):
        """Test listing prompts when database is empty"""
        response = await client.get("/api/prompts")

        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_prompts_with_data(self, client, sample_prompt):
        """Test listing prompts with data"""
        response = await client.get("/api/prompts")

        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["name"] == "test_prompt"

    @pytest.mark.asyncio
    async def test_list_prompts_with_category_filter(self, client, sample_prompt):
        """Test filtering prompts by category"""
        response = await client.get("/api/prompts?category=global")

        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["category"] == "global"

        # Try non-matching category
        response = await client.get("/api/prompts?category=position")
        data = response.json()
        assert len(data["prompts"]) == 0

    @pytest.mark.asyncio
    async def test_list_prompts_pagination(self, client):
        """Test pagination parameters"""
        # Create multiple prompts
        for i in range(5):
            response = await client.post("/api/prompts", json={
                "name": f"prompt_{i}",
                "category": "global",
                "prompt_text": f"Test prompt text number {i}",
                "template_variables": {}
            })
            assert response.status_code == 201, f"Failed to create prompt {i}: {response.json()}"

        # Test pagination
        response = await client.get("/api/prompts?skip=0&limit=2")
        data = response.json()
        assert len(data["prompts"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2


class TestGetPrompt:
    """Test GET /api/prompts/{id} and GET /api/prompts/name/{name}"""

    @pytest.mark.asyncio
    async def test_get_prompt_by_id(self, client, sample_prompt):
        """Test getting a prompt by ID"""
        prompt_id = sample_prompt["id"]
        response = await client.get(f"/api/prompts/{prompt_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prompt_id
        assert data["name"] == "test_prompt"

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_not_found(self, client):
        """Test getting non-existent prompt by ID"""
        response = await client.get("/api/prompts/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_prompt_by_name(self, client, sample_prompt):
        """Test getting a prompt by name"""
        response = await client.get("/api/prompts/name/test_prompt")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_prompt"

    @pytest.mark.asyncio
    async def test_get_prompt_by_name_not_found(self, client):
        """Test getting non-existent prompt by name"""
        response = await client.get("/api/prompts/name/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreatePrompt:
    """Test POST /api/prompts"""

    @pytest.mark.asyncio
    async def test_create_prompt_success(self, client):
        """Test creating a new prompt"""
        response = await client.post("/api/prompts", json={
            "name": "new_prompt",
            "category": "position",
            "prompt_text": "New prompt for {symbol}",
            "template_variables": {"symbol": "string"}
        })

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new_prompt"
        assert data["category"] == "position"
        assert data["version"] == 1
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_prompt_duplicate_name(self, client, sample_prompt):
        """Test creating prompt with duplicate name fails"""
        response = await client.post("/api/prompts", json={
            "name": "test_prompt",  # Already exists
            "category": "position",
            "prompt_text": "Duplicate prompt text",
            "template_variables": {}
        })

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_prompt_validation(self, client):
        """Test prompt validation"""
        # Missing required field
        response = await client.post("/api/prompts", json={
            "name": "invalid",
            "category": "global"
            # Missing prompt_text
        })
        assert response.status_code == 422  # Validation error


class TestUpdatePrompt:
    """Test PUT /api/prompts/{id}"""

    @pytest.mark.asyncio
    async def test_update_prompt_text(self, client, sample_prompt):
        """Test updating prompt text"""
        prompt_id = sample_prompt["id"]

        response = await client.put(f"/api/prompts/{prompt_id}", json={
            "prompt_text": "Updated prompt text",
            "change_reason": "Testing update"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_text"] == "Updated prompt text"
        assert data["version"] == 2  # Version incremented

    @pytest.mark.asyncio
    async def test_update_prompt_multiple_fields(self, client, sample_prompt):
        """Test updating multiple fields"""
        prompt_id = sample_prompt["id"]

        response = await client.put(f"/api/prompts/{prompt_id}", json={
            "name": "updated_name",
            "category": "forecast",
            "prompt_text": "Completely new",
            "template_variables": {"new_var": "integer"}
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated_name"
        assert data["category"] == "forecast"
        assert data["version"] == 2

    @pytest.mark.asyncio
    async def test_update_prompt_not_found(self, client):
        """Test updating non-existent prompt"""
        response = await client.put("/api/prompts/99999", json={
            "prompt_text": "Updated text that is long enough"
        })

        assert response.status_code == 404


class TestDeletePrompt:
    """Test DELETE /api/prompts/{id}"""

    @pytest.mark.asyncio
    async def test_delete_prompt(self, client, sample_prompt):
        """Test soft deleting a prompt"""
        prompt_id = sample_prompt["id"]

        response = await client.delete(f"/api/prompts/{prompt_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify it's deactivated
        response = await client.get(f"/api/prompts/{prompt_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        # Verify it doesn't appear in active list
        response = await client.get("/api/prompts?active_only=true")
        prompts = response.json()["prompts"]
        assert not any(p["id"] == prompt_id for p in prompts)

    @pytest.mark.asyncio
    async def test_delete_prompt_not_found(self, client):
        """Test deleting non-existent prompt"""
        response = await client.delete("/api/prompts/99999")

        assert response.status_code == 404


class TestPromptVersions:
    """Test GET /api/prompts/{id}/versions and POST /api/prompts/{id}/restore/{version}"""

    @pytest.mark.asyncio
    async def test_get_versions_empty(self, client, sample_prompt):
        """Test getting versions when no updates have been made"""
        prompt_id = sample_prompt["id"]

        response = await client.get(f"/api/prompts/{prompt_id}/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["versions"] == []

    @pytest.mark.asyncio
    async def test_get_versions_after_updates(self, client, sample_prompt):
        """Test version history after updates"""
        prompt_id = sample_prompt["id"]

        # Make several updates
        await client.put(f"/api/prompts/{prompt_id}", json={
            "prompt_text": "Updated version 2 text",
            "change_reason": "First update"
        })
        await client.put(f"/api/prompts/{prompt_id}", json={
            "prompt_text": "Updated version 3 text",
            "change_reason": "Second update"
        })

        response = await client.get(f"/api/prompts/{prompt_id}/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["versions"]) == 2
        assert data["versions"][0]["version"] == 1
        assert data["versions"][1]["version"] == 2

    @pytest.mark.asyncio
    async def test_restore_version(self, client, sample_prompt):
        """Test restoring a previous version"""
        prompt_id = sample_prompt["id"]
        original_text = sample_prompt["prompt_text"]

        # Update twice
        await client.put(f"/api/prompts/{prompt_id}", json={
            "prompt_text": "Updated version 2 text"
        })
        await client.put(f"/api/prompts/{prompt_id}", json={
            "prompt_text": "Updated version 3 text"
        })

        # Restore to version 1
        response = await client.post(
            f"/api/prompts/{prompt_id}/restore/1",
            json={"change_reason": "Restoring original"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_text"] == original_text
        assert data["version"] == 4  # New version created

    @pytest.mark.asyncio
    async def test_restore_version_not_found(self, client, sample_prompt):
        """Test restoring non-existent version"""
        prompt_id = sample_prompt["id"]

        response = await client.post(
            f"/api/prompts/{prompt_id}/restore/99",
            json={}
        )

        assert response.status_code == 404


class TestEndToEndWorkflow:
    """Test complete workflow: create, update, version, restore"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, client):
        """Test end-to-end prompt management workflow"""
        # 1. Create a prompt
        create_response = await client.post("/api/prompts", json={
            "name": "workflow_test",
            "category": "global",
            "prompt_text": "Original version",
            "template_variables": {}
        })
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # 2. Update it
        update_response = await client.put(f"/api/prompts/{prompt_id}", json={
            "prompt_text": "Updated version",
            "change_reason": "Improvement"
        })
        assert update_response.status_code == 200
        assert update_response.json()["version"] == 2

        # 3. Check version history
        versions_response = await client.get(f"/api/prompts/{prompt_id}/versions")
        assert versions_response.json()["total"] == 1

        # 4. Restore to original
        restore_response = await client.post(
            f"/api/prompts/{prompt_id}/restore/1",
            json={"change_reason": "Revert"}
        )
        assert restore_response.status_code == 200
        assert restore_response.json()["prompt_text"] == "Original version"

        # 5. Soft delete
        delete_response = await client.delete(f"/api/prompts/{prompt_id}")
        assert delete_response.status_code == 200

        # 6. Verify it's inactive but still accessible
        get_response = await client.get(f"/api/prompts/{prompt_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False
