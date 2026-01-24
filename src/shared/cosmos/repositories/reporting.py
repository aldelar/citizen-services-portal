"""Reporting repository for step completion metrics."""

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from azure.cosmos import exceptions as cosmos_exceptions

from ..client import get_container
from ..models import StepCompletion


class ReportingRepository:
    """Repository for step completion tracking and metrics."""

    def __init__(self):
        """Initialize the reporting repository."""
        self.container_name = "step_completions"

    async def log_step_completion(
        self,
        tool_name: str,
        city: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> StepCompletion:
        """
        Log a step completion for reporting.

        Args:
            tool_name: Name of the tool/step.
            city: City where the step was completed.
            started_at: When the step was started.
            completed_at: When the step was completed.

        Returns:
            StepCompletion: The created step completion object.
        """
        container = await get_container(self.container_name)
        
        # Calculate duration in days
        duration = completed_at - started_at
        duration_days = duration.days if duration.days > 0 else 1
        
        completion = StepCompletion(
            id=str(uuid4()),
            tool_name=tool_name,
            city=city,
            started_at=started_at,
            completed_at=completed_at,
            duration_days=duration_days,
            success=True,
        )
        
        completion_dict = completion.model_dump(by_alias=True, mode="json")
        created_item = await container.create_item(body=completion_dict)
        return StepCompletion.model_validate(created_item)

    async def get_average_duration(
        self, tool_name: str, city: Optional[str] = None
    ) -> dict:
        """
        Get the average duration for a tool/step, optionally filtered by city.

        Args:
            tool_name: Name of the tool/step.
            city: Optional city filter.

        Returns:
            dict: Dictionary with average duration and count.
        """
        container = await get_container(self.container_name)
        
        if city:
            query = """
                SELECT 
                    AVG(c.durationDays) AS averageDuration,
                    COUNT(1) AS count
                FROM c 
                WHERE c.toolName = @toolName AND c.city = @city
            """
            parameters = [
                {"name": "@toolName", "value": tool_name},
                {"name": "@city", "value": city},
            ]
        else:
            query = """
                SELECT 
                    AVG(c.durationDays) AS averageDuration,
                    COUNT(1) AS count
                FROM c 
                WHERE c.toolName = @toolName
            """
            parameters = [{"name": "@toolName", "value": tool_name}]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=tool_name,
        ):
            items.append(item)
        
        if items and items[0]:
            return {
                "average_duration_days": items[0].get("averageDuration", 0),
                "count": items[0].get("count", 0),
                "tool_name": tool_name,
                "city": city,
            }
        
        return {
            "average_duration_days": 0,
            "count": 0,
            "tool_name": tool_name,
            "city": city,
        }
