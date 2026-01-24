"""Project repository for CosmosDB operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from azure.cosmos import exceptions as cosmos_exceptions
from azure.cosmos import PartitionKey

from ..client import get_container
from ..exceptions import NotFoundError
from ..models import (
    Plan,
    PlanStep,
    Project,
    ProjectContext,
    ProjectStatus,
    ProjectSummary,
    StepStatus,
)


class ProjectRepository:
    """Repository for project CRUD and plan operations."""

    def __init__(self):
        """Initialize the project repository."""
        self.container_name = "projects"

    async def create_project(self, user_id: str, context: ProjectContext) -> Project:
        """
        Create a new project for a user.

        Args:
            user_id: The user ID.
            context: Project context information.

        Returns:
            Project: The created project object.
        """
        container = await get_container(self.container_name)
        
        project = Project(
            id=str(uuid4()),
            user_id=user_id,
            title=f"Project for {context.address}",
            context=context,
            status=ProjectStatus.ACTIVE,
        )
        
        project_dict = project.model_dump(by_alias=True, mode="json")
        created_item = await container.create_item(body=project_dict)
        return Project.model_validate(created_item)

    async def get_project(
        self, project_id: str, user_id: str
    ) -> Optional[Project]:
        """
        Get a project by ID and user ID.

        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).

        Returns:
            Optional[Project]: The project object if found, None otherwise.
        """
        container = await get_container(self.container_name)
        
        try:
            item = await container.read_item(item=project_id, partition_key=user_id)
            return Project.model_validate(item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None

    async def get_user_projects(
        self, user_id: str, status: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        Get all projects for a user, optionally filtered by status.

        Args:
            user_id: The user ID.
            status: Optional status filter.

        Returns:
            List[Project]: List of project objects.
        """
        container = await get_container(self.container_name)
        
        if status:
            query = "SELECT * FROM c WHERE c.userId = @userId AND c.status = @status ORDER BY c.updatedAt DESC"
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@status", "value": status.value},
            ]
        else:
            query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.updatedAt DESC"
            parameters = [{"name": "@userId", "value": user_id}]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=user_id,
        ):
            items.append(Project.model_validate(item))
        
        return items

    async def update_project(self, project: Project) -> Project:
        """
        Update an existing project.

        Args:
            project: The project object to update.

        Returns:
            Project: The updated project object.

        Raises:
            NotFoundError: If the project is not found.
        """
        container = await get_container(self.container_name)
        
        try:
            project.updated_at = datetime.now(timezone.utc)
            project_dict = project.model_dump(by_alias=True, mode="json")
            updated_item = await container.replace_item(
                item=project.id, body=project_dict
            )
            return Project.model_validate(updated_item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise NotFoundError(f"Project with ID {project.id} not found")

    async def update_plan_step(
        self, project_id: str, user_id: str, step_id: str, updates: dict
    ) -> Project:
        """
        Update a specific plan step using patch operations.

        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).
            step_id: The step ID to update.
            updates: Dictionary of fields to update. Only fields that exist in PlanStep model are allowed.

        Returns:
            Project: The updated project object.

        Raises:
            NotFoundError: If the project or step is not found.
        """
        container = await get_container(self.container_name)
        
        try:
            # Read the current project
            item = await container.read_item(item=project_id, partition_key=user_id)
            project = Project.model_validate(item)
            
            # Find and update the step
            if not project.plan or not project.plan.steps:
                raise NotFoundError(f"No plan found for project {project_id}")
            
            step_found = False
            for step in project.plan.steps:
                if step.id == step_id:
                    # Update step fields with validation
                    step_dict = step.model_dump()
                    step_dict.update(updates)
                    # Validate the updated step
                    updated_step = PlanStep.model_validate(step_dict)
                    # Copy the validated data back to the step
                    for key, value in updated_step.model_dump().items():
                        setattr(step, key, value)
                    step_found = True
                    break
            
            if not step_found:
                raise NotFoundError(f"Step {step_id} not found in project {project_id}")
            
            # Update plan and project timestamps
            project.plan.updated_at = datetime.now(timezone.utc)
            project.updated_at = datetime.now(timezone.utc)
            
            # Replace the entire project
            project_dict = project.model_dump(by_alias=True, mode="json")
            updated_item = await container.replace_item(
                item=project_id, body=project_dict
            )
            return Project.model_validate(updated_item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise NotFoundError(f"Project with ID {project_id} not found")

    async def add_plan_step(
        self, project_id: str, user_id: str, step: PlanStep
    ) -> Project:
        """
        Add a new step to a project's plan.

        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).
            step: The plan step to add.

        Returns:
            Project: The updated project object.

        Raises:
            NotFoundError: If the project is not found.
        """
        container = await get_container(self.container_name)
        
        try:
            # Read the current project
            item = await container.read_item(item=project_id, partition_key=user_id)
            project = Project.model_validate(item)
            
            # Initialize plan if it doesn't exist
            if not project.plan:
                project.plan = Plan()
            
            # Add the new step
            project.plan.steps.append(step)
            project.plan.updated_at = datetime.now(timezone.utc)
            project.updated_at = datetime.now(timezone.utc)
            
            # Replace the entire project
            project_dict = project.model_dump(by_alias=True, mode="json")
            updated_item = await container.replace_item(
                item=project_id, body=project_dict
            )
            return Project.model_validate(updated_item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise NotFoundError(f"Project with ID {project_id} not found")

    async def update_summary(
        self, project_id: str, user_id: str
    ) -> Project:
        """
        Recalculate and update the project summary based on plan steps.

        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).

        Returns:
            Project: The updated project object.

        Raises:
            NotFoundError: If the project is not found.
        """
        container = await get_container(self.container_name)
        
        try:
            # Read the current project
            item = await container.read_item(item=project_id, partition_key=user_id)
            project = Project.model_validate(item)
            
            # Calculate summary
            if project.plan and project.plan.steps:
                total_steps = len(project.plan.steps)
                completed_steps = sum(
                    1 for step in project.plan.steps if step.status == StepStatus.COMPLETED
                )
                estimated_duration = sum(
                    step.estimated_duration_days or 0
                    for step in project.plan.steps
                )
                
                project.summary = ProjectSummary(
                    total_steps=total_steps,
                    completed_steps=completed_steps,
                    estimated_duration_days=estimated_duration if estimated_duration > 0 else None,
                )
            else:
                project.summary = ProjectSummary()
            
            project.updated_at = datetime.now(timezone.utc)
            
            # Replace the entire project
            project_dict = project.model_dump(by_alias=True, mode="json")
            updated_item = await container.replace_item(
                item=project_id, body=project_dict
            )
            return Project.model_validate(updated_item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise NotFoundError(f"Project with ID {project_id} not found")
