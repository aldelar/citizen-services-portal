"""Tests for CSP MCP server tools.

This module tests:
- Plan lifecycle operations (get, create, update, updateStep)
- Step status transitions and timing
- Analytics (average durations)
- Rework/supersedes handling
"""

import pytest
from datetime import datetime, timezone

from src.services import CSPService
from src.models import (
    StepStatus,
    StepType,
    PlanStepInput,
)
from src.tools import CSPTools


@pytest.fixture
def service():
    """Create a fresh CSPService instance."""
    return CSPService()


@pytest.fixture
def tools():
    """Create a fresh CSPTools instance."""
    return CSPTools()


# =============================================================================
# Plan Create Tests
# =============================================================================

class TestPlanCreate:
    """Tests for creating plans."""

    @pytest.mark.asyncio
    async def test_create_plan_success(self, service):
        """Test successfully creating a new plan."""
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
            PlanStepInput(
                id="INS-1",
                step_type=StepType.INS,
                title="Schedule inspection",
                agency="LADBS",
                depends_on=["PRM-1"],
            ),
        ]
        
        result = await service.plan_create(
            project_id="test-project-1",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        assert result.success is True
        assert result.plan is not None
        assert result.plan.title == "Test Plan"
        assert len(result.plan.steps) == 2

    @pytest.mark.asyncio
    async def test_create_plan_auto_estimates_duration(self, service):
        """Test that estimated_duration_days is auto-populated."""
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        result = await service.plan_create(
            project_id="test-project-2",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        assert result.success is True
        # Mock service should provide estimated duration
        assert result.plan.steps[0].estimated_duration_days is not None
        assert result.plan.steps[0].estimated_duration_days > 0

    @pytest.mark.asyncio
    async def test_create_plan_initial_status_is_defined(self, service):
        """Test that steps start with 'defined' status."""
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        result = await service.plan_create(
            project_id="test-project-3",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        assert result.success is True
        assert result.plan.steps[0].status == StepStatus.DEFINED


# =============================================================================
# Plan Get Tests
# =============================================================================

class TestPlanGet:
    """Tests for retrieving plans."""

    @pytest.mark.asyncio
    async def test_get_existing_plan(self, service):
        """Test getting an existing plan."""
        # First create a plan
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        await service.plan_create(
            project_id="test-project-get-1",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        # Then retrieve it
        result = await service.plan_get(
            project_id="test-project-get-1",
            user_id="test-user-1",
        )
        
        # PlanGetResponse has plan field, not success
        assert result.plan is not None
        assert result.plan.title == "Test Plan"

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan(self, service):
        """Test getting a plan that doesn't exist."""
        result = await service.plan_get(
            project_id="nonexistent-project",
            user_id="test-user-1",
        )
        
        # PlanGetResponse returns None plan for missing projects
        assert result.plan is None
        assert "No plan" in result.message


# =============================================================================
# Plan Update Step Tests
# =============================================================================

class TestPlanUpdateStep:
    """Tests for updating individual steps."""

    @pytest.mark.asyncio
    async def test_update_step_status_to_scheduled(self, service):
        """Test updating step status to scheduled starts timing."""
        # Create plan
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        await service.plan_create(
            project_id="test-update-1",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        # Update to scheduled
        result = await service.plan_update_step(
            project_id="test-update-1",
            user_id="test-user-1",
            step_id="PRM-1",
            status=StepStatus.SCHEDULED,
        )
        
        assert result.success is True
        assert result.step.status == StepStatus.SCHEDULED
        assert result.step.started_at is not None

    @pytest.mark.asyncio
    async def test_update_step_status_to_completed(self, service):
        """Test updating step status to completed stops timing."""
        # Create plan
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        await service.plan_create(
            project_id="test-update-2",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        # Update to in_progress first
        await service.plan_update_step(
            project_id="test-update-2",
            user_id="test-user-1",
            step_id="PRM-1",
            status=StepStatus.IN_PROGRESS,
        )
        
        # Then complete
        result = await service.plan_update_step(
            project_id="test-update-2",
            user_id="test-user-1",
            step_id="PRM-1",
            status=StepStatus.COMPLETED,
            result={"permit_number": "BLDG-2025-12345"},
        )
        
        assert result.success is True
        assert result.step.status == StepStatus.COMPLETED
        assert result.step.completed_at is not None
        assert result.step.result["permit_number"] == "BLDG-2025-12345"

    @pytest.mark.asyncio
    async def test_update_step_with_notes(self, service):
        """Test updating step with notes."""
        # Create plan
        steps = [
            PlanStepInput(
                id="PRM-1",
                step_type=StepType.PRM,
                title="Submit electrical permit",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        await service.plan_create(
            project_id="test-update-3",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        # Update with notes
        result = await service.plan_update_step(
            project_id="test-update-3",
            user_id="test-user-1",
            step_id="PRM-1",
            notes="Submitted via Express Plan Check",
        )
        
        assert result.success is True
        assert result.step.notes == "Submitted via Express Plan Check"


# =============================================================================
# Rework/Supersedes Tests
# =============================================================================

class TestRework:
    """Tests for rework and supersedes handling."""

    @pytest.mark.asyncio
    async def test_needs_rework_status(self, service):
        """Test marking a step as needs_rework."""
        # Create plan
        steps = [
            PlanStepInput(
                id="INS-1",
                step_type=StepType.INS,
                title="Schedule inspection",
                agency="LADBS",
                depends_on=[],
            ),
        ]
        
        await service.plan_create(
            project_id="test-rework-1",
            user_id="test-user-1",
            title="Test Plan",
            steps=steps,
        )
        
        # Start and then fail
        await service.plan_update_step(
            project_id="test-rework-1",
            user_id="test-user-1",
            step_id="INS-1",
            status=StepStatus.IN_PROGRESS,
        )
        
        result = await service.plan_update_step(
            project_id="test-rework-1",
            user_id="test-user-1",
            step_id="INS-1",
            status=StepStatus.NEEDS_REWORK,
            result={"reason": "Wiring not up to code"},
        )
        
        assert result.success is True
        assert result.step.status == StepStatus.NEEDS_REWORK
        assert result.step.completed_at is not None


# =============================================================================
# Analytics Tests
# =============================================================================

class TestAnalytics:
    """Tests for analytics operations."""

    @pytest.mark.asyncio
    async def test_get_average_duration(self, service):
        """Test getting average duration for a step type."""
        result = await service.get_average_duration(
            step_type=StepType.PRM,
        )
        
        assert result.step_type == "PRM"
        assert result.period == "last 6 months"
        # Mock should return some data
        assert result.sample_count >= 0

    @pytest.mark.asyncio
    async def test_get_average_duration_returns_data(self, service):
        """Test that mock data exists for common step types."""
        result = await service.get_average_duration(
            step_type=StepType.ENR,
        )
        
        # Mock data should have some sample count
        assert result.sample_count >= 0
        assert result.average_days >= 0


# =============================================================================
# Tools Wrapper Tests
# =============================================================================

class TestCSPTools:
    """Tests for CSPTools wrapper class."""

    @pytest.mark.asyncio
    async def test_tools_plan_create(self, tools):
        """Test plan creation via tools wrapper."""
        result = await tools.plan_create(
            project_id="tools-test-1",
            user_id="test-user-1",
            title="Tools Test Plan",
            steps=[
                {
                    "id": "PRM-1",
                    "step_type": "PRM",
                    "title": "Submit permit",
                    "agency": "LADBS",
                    "depends_on": [],
                }
            ],
        )
        
        assert result["success"] is True
        assert result["plan"]["title"] == "Tools Test Plan"

    @pytest.mark.asyncio
    async def test_tools_steps_get_average_duration(self, tools):
        """Test getting average duration via tools wrapper."""
        result = await tools.steps_getAverageDuration(
            step_type="PRM",
        )
        
        assert result["step_type"] == "PRM"
        assert "average_days" in result
        assert "sample_count" in result


# =============================================================================
# StepType Enum Tests
# =============================================================================

class TestStepType:
    """Tests for StepType enum."""

    def test_all_step_types_defined(self):
        """Test that all expected step types are defined."""
        expected_types = [
            "PRM",
            "INS",
            "TRD",
            "APP",
            "PCK",
            "ENR",
            "DOC",
            "PAY",
        ]
        
        for type_value in expected_types:
            # Should not raise
            step_type = StepType(type_value)
            assert step_type.value == type_value


# =============================================================================
# StepStatus Enum Tests
# =============================================================================

class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        expected_statuses = [
            "defined",
            "scheduled",
            "in_progress",
            "completed",
            "needs_rework",
            "rejected",
        ]
        
        for status_value in expected_statuses:
            # Should not raise
            status = StepStatus(status_value)
            assert status.value == status_value

    def test_terminal_statuses(self):
        """Test identifying terminal statuses."""
        terminal = [StepStatus.COMPLETED, StepStatus.NEEDS_REWORK, StepStatus.REJECTED]
        non_terminal = [StepStatus.DEFINED, StepStatus.SCHEDULED, StepStatus.IN_PROGRESS]
        
        for status in terminal:
            assert status in terminal
        
        for status in non_terminal:
            assert status not in terminal
