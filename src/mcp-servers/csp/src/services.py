"""Business logic for CSP (Citizen Services Portal) plan management.

This service provides:
1. Plan Lifecycle Management - Create and update project plans
2. Step Completion Tracking - Detect status changes and log completions for analytics

REQUIRES CosmosDB - no mock/in-memory fallback.
"""

import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Require CosmosDB - no mock fallback
_cosmos_endpoint = os.environ.get("COSMOS_ENDPOINT")
if not _cosmos_endpoint:
    raise RuntimeError("COSMOS_ENDPOINT environment variable is required. CSP MCP server cannot start without CosmosDB.")


def _get_project_repository():
    """Get project repository - required."""
    from .repositories import ProjectRepository
    return ProjectRepository()


def _get_step_completion_repository():
    """Get step completion repository - required."""
    from .repositories import StepCompletionRepository
    return StepCompletionRepository()


class CSPService:
    """Service layer for CSP plan operations."""

    # Terminal statuses that trigger completion logging
    TERMINAL_STATUSES = {"completed", "needs_rework", "rejected"}

    def __init__(self):
        """Initialize CSP service with CosmosDB repositories."""
        self._project_repo = _get_project_repository()
        self._step_completion_repo = _get_step_completion_repository()
        logger.info("[CSP] ✅ Service initialized with CosmosDB connection")

    # =========================================================================
    # Plan Operations
    # =========================================================================

    async def plan_get(
        self,
        project_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get the plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)

        Returns:
            Dict with project_id, plan (or None), and optional message
        """
        try:
            plan = await self._project_repo.get_plan(project_id, user_id)
            # Convert Pydantic model to dict for JSON serialization
            plan_dict = plan.model_dump(mode="json") if plan and hasattr(plan, 'model_dump') else plan
            return {
                "project_id": project_id,
                "plan": plan_dict,
                "message": None if plan else f"No plan exists for project {project_id}",
            }
        except Exception as e:
            logger.error(f"Error getting plan from CosmosDB: {e}")
            return {
                "project_id": project_id,
                "plan": None,
                "message": f"Error retrieving plan: {str(e)}",
            }

    async def plan_create(
        self,
        project_id: str,
        user_id: str,
        plan_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            plan_data: Dict with steps array

        Returns:
            Dict with success, project_id, plan, message
        """
        steps = plan_data.get("steps", [])
        
        # Normalize steps and add estimated durations (query CosmosDB for averages)
        normalized_steps = []
        for step in steps:
            normalized = await self._normalize_step_async(step)
            normalized_steps.append(normalized)
        
        if self._project_repo:
            try:
                plan = await self._project_repo.create_plan(
                    project_id=project_id,
                    user_id=user_id,
                    steps=normalized_steps,
                )
                # Convert Pydantic model to dict for JSON serialization
                plan_dict = plan.model_dump(mode="json") if hasattr(plan, 'model_dump') else plan
                return {
                    "success": True,
                    "project_id": project_id,
                    "plan": plan_dict,
                    "message": f"Created plan with {len(steps)} steps",
                }
            except Exception as e:
                logger.error(f"Error creating plan in CosmosDB: {e}")
                return {
                    "success": False,
                    "project_id": project_id,
                    "plan": None,
                    "message": f"Error creating plan: {str(e)}",
                }

    async def plan_update(
        self,
        project_id: str,
        user_id: str,
        plan_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update the plan for a project.

        Compares with existing plan to:
        1. Preserve timing data for existing steps
        2. Detect status changes to 'completed' and log for analytics

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            plan_data: Dict with steps array

        Returns:
            Dict with success, project_id, plan, message
        """
        # Get existing plan to compare
        existing_response = await self.plan_get(project_id, user_id)
        existing_plan = existing_response.get("plan")
        existing_steps = {}
        if existing_plan:
            for step in existing_plan.get("steps", []):
                existing_steps[step.get("id")] = step
        
        new_steps = plan_data.get("steps", [])
        
        # Process steps: normalize, preserve timing, detect completions
        normalized_steps = []
        completions_to_log = []
        
        for step in new_steps:
            step_id = step.get("id")
            existing = existing_steps.get(step_id)
            
            # Check if step already has duration (from existing or incoming data)
            has_duration = (
                step.get("estimatedDurationDays") or 
                step.get("estimated_duration_days") or
                (existing and existing.get("estimatedDurationDays"))
            )
            
            if has_duration:
                # Skip CosmosDB query - use simple normalization
                normalized = self._normalize_step_simple(step)
                # Preserve existing duration if not in incoming step
                if not normalized.get("estimatedDurationDays") and existing:
                    normalized["estimatedDurationDays"] = existing.get("estimatedDurationDays")
            else:
                # No duration yet - query CosmosDB for average
                normalized = await self._normalize_step_async(step)
            
            if existing:
                # Preserve timing data from existing step
                if existing.get("startedAt"):
                    normalized["startedAt"] = existing["startedAt"]
                if existing.get("completedAt"):
                    normalized["completedAt"] = existing["completedAt"]
                
                # Detect status change to 'completed'
                old_status = existing.get("status", "defined")
                new_status = step.get("status", "defined")
                
                if new_status == "completed" and old_status != "completed":
                    # Step just completed - record completion time and log
                    now = datetime.now(timezone.utc).isoformat()
                    normalized["completedAt"] = now
                    
                    # Log completion for analytics (only for automated steps)
                    action_type = normalized.get("action_type", "automated")
                    is_automated = action_type == "automated"
                    if existing.get("startedAt") and is_automated:
                        completions_to_log.append({
                            "step_type": step.get("step_type", ""),
                            "started_at": existing["startedAt"],
                            "completed_at": now,
                        })
                
                # Detect status change to in_progress - set started_at
                if new_status in ("scheduled", "in_progress") and old_status == "defined":
                    if not normalized.get("startedAt"):
                        normalized["startedAt"] = datetime.now(timezone.utc).isoformat()
            else:
                # No existing step - check if being created with non-defined status
                new_status = step.get("status", "defined")
                if new_status in ("scheduled", "in_progress") and not normalized.get("startedAt"):
                    normalized["startedAt"] = datetime.now(timezone.utc).isoformat()
            
            normalized_steps.append(normalized)
        
        try:
            plan = await self._project_repo.update_plan(
                project_id=project_id,
                user_id=user_id,
                steps=normalized_steps,
            )
            
            # Log completions for analytics
            for completion in completions_to_log:
                await self._log_step_completion(
                    step_type=completion["step_type"],
                    started_at=completion["started_at"],
                    completed_at=completion["completed_at"],
                )
            
            return {
                "success": True,
                "project_id": project_id,
                "plan": plan.model_dump(mode="json") if hasattr(plan, 'model_dump') else plan,
                "message": f"Updated plan with {len(normalized_steps)} steps",
                "completions_logged": len(completions_to_log),
            }
        except Exception as e:
            logger.error(f"Error updating plan in CosmosDB: {e}")
            return {
                "success": False,
                "project_id": project_id,
                "plan": None,
                "message": f"Error updating plan: {str(e)}",
            }

    async def plan_update_step(
        self,
        project_id: str,
        user_id: str,
        step_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a single step's status in a plan.

        Uses the repository's update_step method which handles timing automatically:
        - Sets started_at when moving to scheduled/in_progress
        - Sets completed_at when moving to completed/needs_rework/rejected

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            step_id: The step ID to update (e.g., "PRM-1")
            status: New status
            result: Optional result data (e.g., permit number, reference)
            notes: Optional notes

        Returns:
            Dict with success, step (updated step), message
        """
        try:
            # Use the repository's update_step method directly
            # This properly updates and persists the step without re-merging
            updated_step = await self._project_repo.update_step(
                project_id=project_id,
                user_id=user_id,
                step_id=step_id,
                status=status,
                result=result,
                notes=notes,
            )
            
            # Get updated plan for response
            plan_response = await self.plan_get(project_id, user_id)
            plan = plan_response.get("plan")
            
            # Log completion for analytics (only for automated steps) 
            if status in ("completed", "needs_rework", "rejected"):
                step_dict = updated_step.model_dump(mode="json") if hasattr(updated_step, 'model_dump') else updated_step
                action_type = step_dict.get("action_type", "automated")
                is_automated = action_type == "automated"
                started_at = step_dict.get("startedAt") or step_dict.get("started_at")
                completed_at = step_dict.get("completedAt") or step_dict.get("completed_at")
                step_type = step_dict.get("step_type", "")
                
                if started_at and is_automated:
                    await self._log_step_completion(
                        step_type=step_type,
                        started_at=started_at,
                        completed_at=completed_at,
                    )
            
            return {
                "success": True,
                "step": updated_step.model_dump(mode="json") if hasattr(updated_step, 'model_dump') else updated_step,
                "plan": plan,
                "message": f"Updated step {step_id} to status '{status}'",
            }
        except Exception as e:
            logger.error(f"Error updating step in CosmosDB: {e}")
            return {
                "success": False,
                "step": None,
                "message": f"Error updating step: {str(e)}",
            }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_estimated_duration(self, step_type: str) -> float:
        """Get estimated duration for a step type.
        
        1. Query CosmosDB for average duration from historical completions
        2. If no data, return a random number between 5-20 days
        """
        if self._step_completion_repo:
            try:
                # Try to get StepType enum for querying
                from .models import StepType
                try:
                    step_type_enum = StepType(step_type)
                except ValueError:
                    step_type_enum = None
                
                if step_type_enum:
                    avg_duration, count = await self._step_completion_repo.calculate_average_duration_by_type(
                        step_type_enum, months=6
                    )
                    if count > 0 and avg_duration > 0:
                        logger.debug(f"[CSP] 📊 Got avg duration for {step_type}: {avg_duration} days (n={count})")
                        return avg_duration
            except Exception as e:
                logger.warning(f"[CSP] ⚠️ Error querying duration for {step_type}: {e}")
        
        # No historical data - return random 5-20 days
        random_duration = random.uniform(5.0, 20.0)
        logger.debug(f"[CSP] 🎲 No data for {step_type}, using random: {random_duration:.1f} days")
        return round(random_duration, 1)

    async def _normalize_step_async(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a step dict with defaults and estimated duration from CosmosDB."""
        step_type = step.get("step_type", "user.action")
        
        # Determine action_type - TRD and DOC are always user_action
        is_user_driven = step_type in ("TRD", "DOC")
        action_type = "user_action" if is_user_driven else step.get("action_type", "automated")
        
        # Get estimated duration - skip for user_action steps (timing is up to user)
        estimated_duration = None
        if action_type == "automated":
            estimated_duration = step.get("estimatedDurationDays")
            if not estimated_duration:
                estimated_duration = await self._get_estimated_duration(step_type)
        
        return {
            "id": step.get("id", str(uuid4())[:8]),
            "title": step.get("title", "Untitled Step"),
            "description": step.get("description"),
            "agency": step.get("agency", ""),
            "step_type": step_type,
            "action_type": action_type,
            "automated": not is_user_driven,
            "depends_on": step.get("depends_on", []),
            "status": step.get("status", "defined"),
            "startedAt": step.get("startedAt"),
            "completedAt": step.get("completedAt"),
            "estimatedDurationDays": estimated_duration,
            "result": step.get("result"),
            "notes": step.get("notes"),
        }

    def _normalize_step_simple(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a step dict without querying CosmosDB for duration.
        
        Used when step already has estimatedDurationDays or we want to preserve existing.
        """
        step_type = step.get("step_type", "user.action")
        
        # Determine action_type - TRD and DOC are always user_action
        is_user_driven = step_type in ("TRD", "DOC")
        action_type = "user_action" if is_user_driven else step.get("action_type", "automated")
        
        # Skip duration for user_action steps
        estimated_duration = None
        if action_type == "automated":
            estimated_duration = step.get("estimatedDurationDays") or step.get("estimated_duration_days")
        
        return {
            "id": step.get("id", str(uuid4())[:8]),
            "title": step.get("title", "Untitled Step"),
            "description": step.get("description"),
            "agency": step.get("agency", ""),
            "step_type": step_type,
            "action_type": action_type,
            "automated": not is_user_driven,
            "depends_on": step.get("depends_on", []),
            "status": step.get("status", "defined"),
            "startedAt": step.get("startedAt"),
            "completedAt": step.get("completedAt"),
            "estimatedDurationDays": estimated_duration,
            "result": step.get("result"),
            "notes": step.get("notes"),
        }

    async def _log_step_completion(
        self,
        step_type: str,
        started_at: str,
        completed_at: str,
    ) -> None:
        """Log a step completion for analytics."""
        if self._step_completion_repo:
            try:
                # Parse timestamps
                started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                
                await self._step_completion_repo.create_step_log(
                    tool_name=step_type,
                    city="Los Angeles",
                    started_at=started_dt,
                    completed_at=completed_dt,
                )
                logger.info(f"[CSP] 📊 Logged completion: {step_type}")
            except Exception as e:
                logger.error(f"Error logging step completion: {e}")
