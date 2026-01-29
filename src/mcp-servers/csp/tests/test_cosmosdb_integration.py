"""Integration tests for CSP CosmosDB operations.

These tests require a live CosmosDB instance with COSMOS_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.models import StepType, StepStatus
from src.repositories import StepCompletionRepository, ProjectRepository


# Skip all tests in this file if CosmosDB is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("COSMOS_ENDPOINT"),
        reason="CosmosDB not configured (COSMOS_ENDPOINT not set)"
    )
]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
async def step_completion_repository():
    """Create a StepCompletionRepository instance for testing."""
    return StepCompletionRepository()


@pytest.fixture(scope="session")
async def project_repository():
    """Create a ProjectRepository instance for testing."""
    return ProjectRepository()


async def _create_test_project(project_repository: ProjectRepository, user_id: str) -> str:
    """Helper to create a project document for testing.
    
    Returns:
        str: The created project ID
    """
    project_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Create a minimal project document that the plan operations need
    project_doc = {
        "id": project_id,
        "userId": user_id,
        "title": f"Test Project {project_id[:8]}",
        "status": "active",
        "context": {
            "address": "123 Test Street",
            "projectType": "solar-installation",
        },
        "createdAt": now,
        "updatedAt": now,
    }
    
    await project_repository.create(project_doc)
    return project_id


# =============================================================================
# StepCompletionRepository Tests
# =============================================================================

class TestStepCompletionRepository:
    """Tests for step completion repository operations."""

    @pytest.mark.asyncio
    async def test_log_step_completion(self, step_completion_repository):
        """Log a step completion and verify."""
        now = datetime.now(timezone.utc)
        
        completion = await step_completion_repository.log_step_completion(
            step_type=StepType.PRM,
            chain_started_at=now - timedelta(days=45),
            completed_at=now,
            attempts=1,
        )

        assert completion.id is not None
        assert completion.step_type == StepType.PRM
        assert completion.duration_days > 0
        assert completion.attempts == 1

    @pytest.mark.asyncio
    async def test_log_step_calculates_duration(self, step_completion_repository):
        """Verify duration calculation."""
        now = datetime.now(timezone.utc)
        
        completion = await step_completion_repository.log_step_completion(
            step_type=StepType.ENR,
            chain_started_at=now - timedelta(days=30),
            completed_at=now,
            attempts=1,
        )

        # Duration should be approximately 30 days
        assert 29 < completion.duration_days < 31

    @pytest.mark.asyncio
    async def test_log_step_with_multiple_attempts(self, step_completion_repository):
        """Log a step completion with multiple rework attempts."""
        now = datetime.now(timezone.utc)
        
        completion = await step_completion_repository.log_step_completion(
            step_type=StepType.INS,
            chain_started_at=now - timedelta(days=60),
            completed_at=now,
            attempts=3,  # Failed inspection twice, passed on third attempt
        )

        assert completion.attempts == 3
        assert completion.duration_days > 59

    @pytest.mark.asyncio
    async def test_calculate_average_duration_by_type(self, step_completion_repository):
        """Verify average calculation by step type."""
        now = datetime.now(timezone.utc)
        
        # Use a unique step type to avoid interference from other tests
        test_step_type = StepType.PCK

        # Create completions with known durations (10, 20, 30 days)
        for days in [10, 20, 30]:
            await step_completion_repository.log_step_completion(
                step_type=test_step_type,
                chain_started_at=now - timedelta(days=days + 5),
                completed_at=now - timedelta(days=5),
                attempts=1,
            )

        average, count = await step_completion_repository.calculate_average_duration_by_type(
            step_type=test_step_type,
            months=6,
        )
        
        # Should have at least the 3 completions we just created
        assert count >= 3
        # Average should be around 20 days (10+20+30)/3 = 20
        assert 15 < average < 25

    @pytest.mark.asyncio
    async def test_calculate_average_no_data(self, step_completion_repository):
        """Handle case with no data for a step type."""
        # Use a unique step type that won't have test data
        average, count = await step_completion_repository.calculate_average_duration_by_type(
            step_type=StepType.DOC,
            months=1,  # Short window to avoid test data
        )
        
        # If no data, should return 0
        if count == 0:
            assert average == 0.0


# =============================================================================
# ProjectRepository Tests
# =============================================================================

class TestProjectRepository:
    """Tests for project repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_plan(self, project_repository):
        """Create and retrieve a plan."""
        user_id = f"test-user-{uuid4()}"
        project_id = await _create_test_project(project_repository, user_id)
        
        # Create plan
        plan = await project_repository.create_plan(
            project_id=project_id,
            user_id=user_id,
            title="Test Plan",
            steps=[
                {
                    "id": "P1",
                    "step_type": "permits.submit",
                    "title": "Submit permit",
                    "agency": "LADBS",
                    "status": "defined",
                    "depends_on": [],
                }
            ],
        )

        assert plan is not None
        assert plan.title == "Test Plan"
        assert len(plan.steps) == 1

        # Retrieve plan
        retrieved = await project_repository.get_plan(
            project_id=project_id,
            user_id=user_id,
        )

        assert retrieved is not None
        assert retrieved.title == "Test Plan"

    @pytest.mark.asyncio
    async def test_update_plan(self, project_repository):
        """Update an existing plan."""
        user_id = f"test-user-{uuid4()}"
        project_id = await _create_test_project(project_repository, user_id)
        
        # Create plan
        await project_repository.create_plan(
            project_id=project_id,
            user_id=user_id,
            title="Original Title",
            steps=[
                {
                    "id": "P1",
                    "step_type": "permits.submit",
                    "title": "Submit permit",
                    "agency": "LADBS",
                    "status": "defined",
                    "depends_on": [],
                }
            ],
        )

        # Update plan by adding a step
        updated = await project_repository.update_plan(
            project_id=project_id,
            user_id=user_id,
            steps=[
                {
                    "id": "P1",
                    "step_type": "permits.submit",
                    "title": "Submit permit",
                    "agency": "LADBS",
                    "status": "defined",
                    "depends_on": [],
                },
                {
                    "id": "I1",
                    "step_type": "inspection.schedule",
                    "title": "Schedule inspection",
                    "agency": "LADBS",
                    "status": "defined",
                    "depends_on": ["P1"],
                }
            ],
        )

        assert updated is not None
        assert len(updated.steps) == 2

    @pytest.mark.asyncio
    async def test_update_step(self, project_repository):
        """Update a specific step in a plan."""
        user_id = f"test-user-{uuid4()}"
        project_id = await _create_test_project(project_repository, user_id)
        
        # Create plan
        await project_repository.create_plan(
            project_id=project_id,
            user_id=user_id,
            title="Test Plan",
            steps=[
                {
                    "id": "P1",
                    "step_type": "permits.submit",
                    "title": "Submit permit",
                    "agency": "LADBS",
                    "status": "defined",
                    "depends_on": [],
                }
            ],
        )

        # Update step status
        updated_step = await project_repository.update_step(
            project_id=project_id,
            user_id=user_id,
            step_id="P1",
            status="in_progress",
        )

        assert updated_step is not None
        assert updated_step.status == StepStatus.IN_PROGRESS
        assert updated_step.started_at is not None

    @pytest.mark.asyncio
    async def test_complete_step_with_result(self, project_repository):
        """Complete a step with result data."""
        user_id = f"test-user-{uuid4()}"
        project_id = await _create_test_project(project_repository, user_id)
        
        # Create plan
        await project_repository.create_plan(
            project_id=project_id,
            user_id=user_id,
            title="Test Plan",
            steps=[
                {
                    "id": "P1",
                    "step_type": "permits.submit",
                    "title": "Submit permit",
                    "agency": "LADBS",
                    "status": "defined",
                    "depends_on": [],
                }
            ],
        )

        # Start the step
        await project_repository.update_step(
            project_id=project_id,
            user_id=user_id,
            step_id="P1",
            status="in_progress",
        )

        # Complete the step with result
        completed = await project_repository.update_step(
            project_id=project_id,
            user_id=user_id,
            step_id="P1",
            status="completed",
            result={"permit_number": "BLDG-2025-12345"},
        )

        assert completed.status == StepStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.result["permit_number"] == "BLDG-2025-12345"

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan(self, project_repository):
        """Handle case when plan doesn't exist."""
        plan = await project_repository.get_plan(
            project_id=f"nonexistent-{uuid4()}",
            user_id=f"nonexistent-{uuid4()}",
        )
        
        assert plan is None

    @pytest.mark.asyncio
    async def test_step_chain_for_rework(self, project_repository):
        """Test getting step chain for rework scenarios."""
        user_id = f"test-user-{uuid4()}"
        project_id = await _create_test_project(project_repository, user_id)
        
        # Create plan with original step and rework step
        await project_repository.create_plan(
            project_id=project_id,
            user_id=user_id,
            title="Rework Test Plan",
            steps=[
                {
                    "id": "I1",
                    "step_type": "inspection.schedule",
                    "title": "Schedule inspection",
                    "agency": "LADBS",
                    "status": "needs_rework",
                    "depends_on": [],
                },
                {
                    "id": "I1.2",
                    "step_type": "inspection.schedule",
                    "title": "Reschedule inspection (attempt 2)",
                    "agency": "LADBS",
                    "status": "defined",
                    "supersedes": "I1",
                    "attempt_number": 2,
                    "depends_on": [],
                }
            ],
        )

        # Get step chain
        chain = await project_repository.get_step_chain(
            project_id=project_id,
            user_id=user_id,
            step_id="I1.2",
        )

        assert len(chain) == 2
        assert chain[0].id == "I1"  # Original
        assert chain[1].id == "I1.2"  # Rework


# =============================================================================
# Legacy StepLog Repository Tests (backward compatibility)
# =============================================================================

class TestLegacyStepLogRepository:
    """Tests for backward-compatible step log operations."""

    @pytest.mark.asyncio
    async def test_create_step_log_legacy(self, step_completion_repository):
        """Test legacy create_step_log method."""
        now = datetime.now(timezone.utc)
        
        log = await step_completion_repository.create_step_log(
            tool_name="permits.submit",
            city="Los Angeles",
            started_at=now - timedelta(days=45),
            completed_at=now,
        )

        assert log.id is not None
        assert log.tool_name == "permits.submit"
        assert log.city == "Los Angeles"
        assert log.duration_days > 0
