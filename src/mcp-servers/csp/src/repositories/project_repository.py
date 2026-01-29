"""Project repository for CSP plan operations in CosmosDB."""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import Plan, PlanStep, StepStatus, StepType

logger = logging.getLogger(__name__)

# Add shared module to path if needed
shared_path = os.path.join(os.path.dirname(__file__), "../../../../shared")
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

try:
    from cosmos.base_repository import BaseRepository
    from cosmos.exceptions import NotFoundError
except ImportError:
    # Fallback for when cosmos module is installed as package
    from citizen_services_shared.cosmos.base_repository import BaseRepository
    from citizen_services_shared.cosmos.exceptions import NotFoundError


class ProjectRepository(BaseRepository):
    """Repository for project and plan CRUD operations.
    
    This repository manages the projects container which stores
    project documents including their embedded plans and steps.
    """

    container_name = "projects"
    partition_key_field = "userId"  # Projects are partitioned by user

    async def get_project(
        self,
        project_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)

        Returns:
            Optional[Dict[str, Any]]: The project document or None
        """
        return await self.get_by_id(project_id, partition_key=user_id)

    async def get_plan(
        self,
        project_id: str,
        user_id: str,
    ) -> Optional[Plan]:
        """
        Get the plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)

        Returns:
            Optional[Plan]: The plan or None if no plan exists
        """
        project = await self.get_project(project_id, user_id)
        if not project or "plan" not in project:
            return None
        
        return self._to_plan(project["plan"])

    async def create_plan(
        self,
        project_id: str,
        user_id: str,
        steps: List[Dict[str, Any]],
    ) -> Plan:
        """
        Create a new plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            steps: List of step data

        Returns:
            Plan: The created plan

        Raises:
            NotFoundError: If the project is not found
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Create plan structure
        plan_data = {
            "id": str(uuid4()),
            "status": "active",
            "steps": self._normalize_steps(steps),
            "createdAt": now,
            "updatedAt": now,
        }
        
        # Update project with new plan
        project["plan"] = plan_data
        project["updatedAt"] = now
        
        # Update summary
        project["summary"] = self._calculate_summary(plan_data["steps"])
        
        await self.update(project_id, user_id, project)
        
        return self._to_plan(plan_data)

    async def update_plan(
        self,
        project_id: str,
        user_id: str,
        steps: List[Dict[str, Any]],
    ) -> Plan:
        """
        Update the plan for a project.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            steps: Complete list of steps (replaces existing)

        Returns:
            Plan: The updated plan

        Raises:
            NotFoundError: If the project or plan is not found
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        if "plan" not in project or not project["plan"]:
            raise NotFoundError(f"No plan exists for project {project_id}")
        
        existing_plan = project["plan"]
        existing_steps = {s["id"]: s for s in existing_plan.get("steps", [])}
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Merge steps: preserve timing data for existing steps
        merged_steps = []
        for step in steps:
            step_id = step.get("id")
            if step_id in existing_steps:
                # Preserve timing and status from existing step
                existing = existing_steps[step_id]
                merged_step = self._normalize_step(step)
                
                # Preserve managed fields
                for field in ["status", "startedAt", "completedAt", "estimatedDurationDays", "actionCard"]:
                    if field in existing:
                        merged_step[field] = existing[field]
                
                merged_steps.append(merged_step)
            else:
                # New step
                merged_steps.append(self._normalize_step(step))
        
        # Update plan
        existing_plan["steps"] = merged_steps
        existing_plan["updatedAt"] = now
        
        project["plan"] = existing_plan
        project["updatedAt"] = now
        project["summary"] = self._calculate_summary(merged_steps)
        
        await self.update(project_id, user_id, project)
        
        return self._to_plan(existing_plan)

    async def update_step(
        self,
        project_id: str,
        user_id: str,
        step_id: str,
        status: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        action_card: Optional[Dict[str, Any]] = None,
    ) -> PlanStep:
        """
        Update a specific step in the project plan.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            step_id: The step ID
            status: New status (optional)
            result: Outcome data (optional)
            notes: Additional notes (optional)
            action_card: Action card for non-automated steps (optional)

        Returns:
            PlanStep: The updated step

        Raises:
            NotFoundError: If the project, plan, or step is not found
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        if "plan" not in project or not project["plan"]:
            raise NotFoundError(f"No plan exists for project {project_id}")
        
        plan = project["plan"]
        steps = plan.get("steps", [])
        
        # Find the step
        step_index = None
        step_data = None
        for i, s in enumerate(steps):
            if s.get("id") == step_id:
                step_index = i
                step_data = s
                break
        
        if step_data is None:
            raise NotFoundError(f"Step {step_id} not found in plan")
        
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        
        # Handle status transition
        timing_started = False
        timing_completed = False
        
        if status:
            old_status = step_data.get("status", "defined")
            new_status = status
            
            # Set started_at on transition to SCHEDULED or IN_PROGRESS
            if new_status in ["scheduled", "in_progress"] and not step_data.get("startedAt"):
                step_data["startedAt"] = now_iso
                timing_started = True
            
            # Set completed_at on terminal status
            if new_status in ["completed", "needs_rework", "rejected"]:
                step_data["completedAt"] = now_iso
                timing_completed = True
            
            step_data["status"] = new_status
        
        # Update result and notes
        if result is not None:
            step_data["result"] = result
        
        if notes is not None:
            step_data["notes"] = notes
        
        if action_card is not None:
            step_data["actionCard"] = action_card
        
        # Update the step in the plan
        steps[step_index] = step_data
        plan["steps"] = steps
        plan["updatedAt"] = now_iso
        
        project["plan"] = plan
        project["updatedAt"] = now_iso
        project["summary"] = self._calculate_summary(steps)
        
        await self.update(project_id, user_id, project)
        
        return self._to_plan_step(step_data)

    async def get_step(
        self,
        project_id: str,
        user_id: str,
        step_id: str,
    ) -> Optional[PlanStep]:
        """
        Get a specific step from a plan.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            step_id: The step ID

        Returns:
            Optional[PlanStep]: The step or None if not found
        """
        project = await self.get_project(project_id, user_id)
        if not project or "plan" not in project:
            return None
        
        for step in project["plan"].get("steps", []):
            if step.get("id") == step_id:
                return self._to_plan_step(step)
        
        return None

    async def get_step_chain(
        self,
        project_id: str,
        user_id: str,
        step_id: str,
    ) -> List[PlanStep]:
        """
        Get the full chain of steps for rework tracking.
        
        Follows the supersedes chain backward to find the root step.

        Args:
            project_id: The project UUID
            user_id: The user ID (partition key)
            step_id: The step ID (usually the final step in chain)

        Returns:
            List[PlanStep]: List of steps in the chain, ordered from first to last
        """
        project = await self.get_project(project_id, user_id)
        if not project or "plan" not in project:
            return []
        
        steps_by_id = {s.get("id"): s for s in project["plan"].get("steps", [])}
        
        # Start from the given step and follow supersedes backward
        current_id = step_id
        chain_ids = []
        
        while current_id:
            chain_ids.append(current_id)
            step = steps_by_id.get(current_id)
            if step:
                current_id = step.get("supersedes")
            else:
                break
        
        # Reverse to get first-to-last order
        chain_ids.reverse()
        
        return [self._to_plan_step(steps_by_id[sid]) for sid in chain_ids if sid in steps_by_id]

    def _normalize_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a step input to CosmosDB format."""
        return {
            "id": step.get("id"),
            "stepType": step.get("step_type") or step.get("stepType"),
            "title": step.get("title"),
            "description": step.get("description"),
            "agency": step.get("agency"),
            "automated": step.get("automated", True),
            "dependsOn": step.get("depends_on") or step.get("dependsOn", []),
            "supersedes": step.get("supersedes"),
            "attemptNumber": step.get("attempt_number") or step.get("attemptNumber", 1),
            "status": step.get("status", "defined"),
            "startedAt": step.get("started_at") or step.get("startedAt"),
            "completedAt": step.get("completed_at") or step.get("completedAt"),
            "estimatedDurationDays": step.get("estimated_duration_days") or step.get("estimatedDurationDays"),
            "result": step.get("result"),
            "notes": step.get("notes"),
            "actionCard": step.get("action_card") or step.get("actionCard"),
        }

    def _normalize_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a list of step inputs."""
        return [self._normalize_step(s) for s in steps]

    def _calculate_summary(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate plan summary from steps."""
        total = len(steps)
        completed = sum(1 for s in steps if s.get("status") == "completed")
        in_progress = sum(1 for s in steps if s.get("status") in ["in_progress", "scheduled"])
        not_started = sum(1 for s in steps if s.get("status") == "defined")
        
        return {
            "totalSteps": total,
            "completed": completed,
            "inProgress": in_progress,
            "notStarted": not_started,
        }

    def _to_plan(self, data: Dict[str, Any]) -> Plan:
        """Convert CosmosDB plan data to Plan model."""
        steps = [self._to_plan_step(s) for s in data.get("steps", [])]
        
        return Plan(
            id=data.get("id", ""),
            status=data.get("status", "active"),
            steps=steps,
            created_at=self.parse_datetime(data.get("createdAt")),
            updated_at=self.parse_datetime(data.get("updatedAt")),
        )

    def _to_plan_step(self, data: Dict[str, Any]) -> PlanStep:
        """Convert CosmosDB step data to PlanStep model."""
        from ..models import ActionCard
        
        action_card = None
        if data.get("actionCard"):
            ac_data = data["actionCard"]
            action_card = ActionCard(
                title=ac_data.get("title", ""),
                description=ac_data.get("description", ""),
                instructions=ac_data.get("instructions", []),
                completion_prompt=ac_data.get("completionPrompt", ""),
                created_at=self.parse_datetime(ac_data.get("createdAt")) or datetime.now(timezone.utc),
            )
        
        # Parse step_type enum
        step_type_str = data.get("stepType", "user.action")
        try:
            step_type = StepType(step_type_str)
        except ValueError:
            step_type = StepType.USER_ACTION
        
        # Parse status enum
        status_str = data.get("status", "defined")
        try:
            status = StepStatus(status_str)
        except ValueError:
            status = StepStatus.DEFINED
        
        return PlanStep(
            id=data.get("id", ""),
            step_type=step_type,
            title=data.get("title", ""),
            description=data.get("description"),
            agency=data.get("agency", ""),
            automated=data.get("automated", True),
            action_card=action_card,
            depends_on=data.get("dependsOn", []),
            supersedes=data.get("supersedes"),
            attempt_number=data.get("attemptNumber", 1),
            status=status,
            started_at=self.parse_datetime(data.get("startedAt")),
            completed_at=self.parse_datetime(data.get("completedAt")),
            estimated_duration_days=data.get("estimatedDurationDays"),
            result=data.get("result"),
            notes=data.get("notes"),
        )
