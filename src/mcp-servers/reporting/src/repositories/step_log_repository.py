"""Step log repository for Reporting CosmosDB operations."""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..models import StepLog

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


class StepLogRepository(BaseRepository):
    """Repository for step log CRUD operations."""

    container_name = "step_logs"
    partition_key_field = "toolName"  # Partition by tool name for efficient queries

    def _generate_log_id(self) -> str:
        """Generate a unique log ID."""
        import random
        import string
        random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"LOG-{random_suffix}"

    async def create_step_log(
        self,
        tool_name: str,
        city: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> StepLog:
        """
        Create a new step log entry.

        Args:
            tool_name: Normalized tool name (e.g., permits.submit)
            city: Geographic filter (e.g., Los Angeles)
            started_at: When the step started
            completed_at: When the step completed

        Returns:
            StepLog: The created step log.
        """
        log_id = self._generate_log_id()
        
        # Calculate duration in days
        duration = completed_at - started_at
        duration_days = duration.total_seconds() / (24 * 60 * 60)
        
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "logId": log_id,
            "toolName": tool_name,
            "city": city,
            "startedAt": started_at.isoformat(),
            "completedAt": completed_at.isoformat(),
            "durationDays": duration_days,
            "loggedAt": now.isoformat(),
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_step_log(created_item)

    async def get_logs_by_tool(
        self,
        tool_name: str,
        city: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[StepLog]:
        """
        Get step logs for a tool, optionally filtered by city and time.

        Args:
            tool_name: Tool name to filter by
            city: Optional city filter
            since: Optional date filter (only logs after this date)

        Returns:
            List[StepLog]: List of matching step logs.
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
