"""MCP tools for CSP (Citizen Services Portal) services.

This module provides:
1. Plan Lifecycle Tools - plan.get, plan.create, plan.update

Tools accept plan_json strings for simplicity - the agent generates
the plan structure per the system prompt schema.
"""

import json
from typing import Any, Dict

from .services import CSPService


class CSPTools:
    """CSP MCP tools implementation."""

    def __init__(self):
        """Initialize CSP tools with service layer."""
        self.service = CSPService()

    # =========================================================================
    # Plan Lifecycle Tools
    # =========================================================================

    async def plan_get(
        self,
        project_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get the full plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)

        Returns:
            PlanGetResponse with complete plan and all steps
        """
        result = await self.service.plan_get(
            project_id=project_id,
            user_id=user_id,
        )
        return result

    async def plan_create(
        self,
        project_id: str,
        user_id: str,
        plan_json: str,
    ) -> Dict[str, Any]:
        """
        Create a new plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            plan_json: JSON string with plan structure (title, steps)

        Returns:
            Dict with success, project_id, plan, message
        """
        # Parse JSON
        plan_data = json.loads(plan_json)
        
        result = await self.service.plan_create(
            project_id=project_id,
            user_id=user_id,
            plan_data=plan_data,
        )
        return result

    async def plan_update(
        self,
        project_id: str,
        user_id: str,
        plan_json: str,
    ) -> Dict[str, Any]:
        """
        Update the plan for a project.

        The service will:
        1. Compare with existing plan to detect status changes
        2. Log step completions for analytics when steps move to 'completed'
        3. Preserve timing data for unchanged steps

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            plan_json: JSON string with updated plan structure

        Returns:
            Dict with success, project_id, plan, message
        """
        # Parse JSON
        plan_data = json.loads(plan_json)
        
        result = await self.service.plan_update(
            project_id=project_id,
            user_id=user_id,
            plan_data=plan_data,
        )
        return result

    async def plan_updateStep(
        self,
        project_id: str,
        user_id: str,
        step_id: str,
        status: str,
        result: str = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """
        Update a single step's status in a plan.

        This is the preferred method for updating step status after executing
        a tool or when a user confirms completion. It handles timing automatically.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            step_id: The step ID to update (e.g., "PRM-1")
            status: New status: "defined", "scheduled", "in_progress", "completed", "needs_rework", "rejected"
            result: Optional JSON string with result data (e.g., permit number)
            notes: Optional notes about the step

        Returns:
            Dict with success, step (updated step), message
        """
        # Parse result JSON if provided
        result_data = None
        if result:
            try:
                result_data = json.loads(result)
            except json.JSONDecodeError:
                result_data = {"value": result}
        
        step_result = await self.service.plan_update_step(
            project_id=project_id,
            user_id=user_id,
            step_id=step_id,
            status=status,
            result=result_data,
            notes=notes,
        )
        return step_result
