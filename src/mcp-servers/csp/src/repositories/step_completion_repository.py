"""Step completion repository for CSP analytics CosmosDB operations.

This repository manages the step_completions container for tracking
step timing analytics. It's partitioned by stepType for efficient aggregation queries.
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..models import StepCompletion, StepLog, StepType

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


class StepCompletionRepository(BaseRepository):
    """Repository for step completion analytics operations.
    
    This repository manages the step_completions container for tracking
    step timing analytics, partitioned by stepType for efficient aggregation.
    """

    container_name = "step_completions"
    partition_key_field = "stepType"  # Partition by step type for efficient aggregation

    def _generate_completion_id(self) -> str:
        """Generate a unique completion ID."""
        import random
        import string
        random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"COMP-{random_suffix}"

    async def log_step_completion(
        self,
        step_type: StepType,
        chain_started_at: datetime,
        completed_at: datetime,
        attempts: int = 1,
    ) -> StepCompletion:
        """
        Log a step completion for analytics.

        Args:
            step_type: The step type for aggregation
            chain_started_at: When the chain started (first step's started_at)
            completed_at: When the chain completed (final step's completed_at)
            attempts: Number of attempts in the chain

        Returns:
            StepCompletion: The created completion record
        """
        completion_id = self._generate_completion_id()
        
        # Calculate duration in days
        duration = completed_at - chain_started_at
        duration_days = duration.total_seconds() / (24 * 60 * 60)
        
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "completionId": completion_id,
            "stepType": step_type.value,
            "chainStartedAt": chain_started_at.isoformat(),
            "completedAt": completed_at.isoformat(),
            "durationDays": duration_days,
            "attempts": attempts,
            "loggedAt": now.isoformat(),
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_step_completion(created_item)

    async def create_step_log(
        self,
        tool_name: str,
        city: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> StepLog:
        """
        Create a step log entry (legacy format for backward compatibility).

        Args:
            tool_name: Normalized tool name (e.g., permits.submit)
            city: Geographic filter (e.g., Los Angeles)
            started_at: When the step started
            completed_at: When the step completed

        Returns:
            StepLog: The created step log
        """
        log_id = self._generate_completion_id().replace("COMP", "LOG")
        
        # Calculate duration in days
        duration = completed_at - started_at
        duration_days = duration.total_seconds() / (24 * 60 * 60)
        
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "logId": log_id,
            "stepType": tool_name,  # Use tool_name as step type for partitioning
            "toolName": tool_name,
            "city": city,
            "chainStartedAt": started_at.isoformat(),
            "startedAt": started_at.isoformat(),
            "completedAt": completed_at.isoformat(),
            "durationDays": duration_days,
            "attempts": 1,
            "loggedAt": now.isoformat(),
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_step_log(created_item)

    async def get_completions_by_type(
        self,
        step_type: StepType,
        since: Optional[datetime] = None,
    ) -> List[StepCompletion]:
        """
        Get step completions for a step type.

        Args:
            step_type: Step type to filter by
            since: Optional date filter (only completions after this date)

        Returns:
            List[StepCompletion]: List of matching completions
        """
        query = "SELECT * FROM c WHERE c.stepType = @stepType"
        parameters: List[Dict[str, Any]] = [{"name": "@stepType", "value": step_type.value}]
        
        if since:
            query += " AND c.completedAt > @since"
            parameters.append({"name": "@since", "value": since.isoformat()})
        
        query += " ORDER BY c.completedAt DESC"
        
        items = await self.query(query, parameters, partition_key=step_type.value)
        return [self._to_step_completion(item) for item in items]

    async def get_logs_by_tool(
        self,
        tool_name: str,
        city: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[StepLog]:
        """
        Get step logs for a tool (legacy format).

        Args:
            tool_name: Tool name to filter by
            city: Optional city filter
            since: Optional date filter (only logs after this date)

        Returns:
            List[StepLog]: List of matching step logs
        """
        query = "SELECT * FROM c WHERE c.toolName = @toolName"
        parameters: List[Dict[str, Any]] = [{"name": "@toolName", "value": tool_name}]
        
        if city:
            query += " AND c.city = @city"
            parameters.append({"name": "@city", "value": city})
        
        if since:
            query += " AND c.completedAt > @since"
            parameters.append({"name": "@since", "value": since.isoformat()})
        
        query += " ORDER BY c.completedAt DESC"
        
        items = await self.query(query, parameters, partition_key=tool_name)
        return [self._to_step_log(item) for item in items]

    async def calculate_average_duration(
        self,
        tool_name: str,
        city: Optional[str] = None,
        months: int = 6,
    ) -> Tuple[float, int]:
        """
        Calculate average duration and sample count for a tool.

        Args:
            tool_name: Tool name to calculate average for
            city: Optional city filter
            months: Number of months to look back (default: 6)

        Returns:
            Tuple[float, int]: Average duration in days and sample count.
        """
        since = datetime.now(timezone.utc) - timedelta(days=months * 30)
        logs = await self.get_logs_by_tool(tool_name, city=city, since=since)
        
        if not logs:
            return 0.0, 0
        
        total_days = sum(log.duration_days for log in logs)
        average_days = total_days / len(logs)
        
        return round(average_days, 1), len(logs)

    def _to_step_log(self, item: Dict[str, Any]) -> StepLog:
        """Convert a CosmosDB document to a StepLog model."""
        # Use the logId field as the primary identifier for the StepLog model
        # The 'id' field in Cosmos is a UUID for document identity
        return StepLog(
            id=item.get("logId", ""),
            tool_name=item.get("toolName", ""),
            city=item.get("city", ""),
            started_at=self.parse_datetime(item.get("startedAt")) or datetime.now(timezone.utc),
            completed_at=self.parse_datetime(item.get("completedAt")) or datetime.now(timezone.utc),
            duration_days=item.get("durationDays", 0.0),
            logged_at=self.parse_datetime(item.get("loggedAt")) or datetime.now(timezone.utc),
        )

    def _to_step_completion(self, item: Dict[str, Any]) -> StepCompletion:
        """Convert a CosmosDB document to a StepCompletion model."""
        step_type_str = item.get("stepType", "user.action")
        try:
            step_type = StepType(step_type_str)
        except ValueError:
            step_type = StepType.USER_ACTION
        
        return StepCompletion(
            id=item.get("completionId", item.get("logId", "")),
            step_type=step_type,
            chain_started_at=self.parse_datetime(item.get("chainStartedAt") or item.get("startedAt")) or datetime.now(timezone.utc),
            completed_at=self.parse_datetime(item.get("completedAt")) or datetime.now(timezone.utc),
            duration_days=item.get("durationDays", 0.0),
            attempts=item.get("attempts", 1),
            logged_at=self.parse_datetime(item.get("loggedAt")) or datetime.now(timezone.utc),
        )

    async def calculate_average_duration_by_type(
        self,
        step_type: StepType,
        months: int = 6,
    ) -> Tuple[float, int]:
        """
        Calculate average duration and sample count for a step type.

        Args:
            step_type: Step type to calculate average for
            months: Number of months to look back (default: 6)

        Returns:
            Tuple[float, int]: Average duration in days and sample count
        """
        since = datetime.now(timezone.utc) - timedelta(days=months * 30)
        completions = await self.get_completions_by_type(step_type, since=since)
        
        if not completions:
            return 0.0, 0
        
        total_days = sum(c.duration_days for c in completions)
        average_days = total_days / len(completions)
        
        return round(average_days, 1), len(completions)
