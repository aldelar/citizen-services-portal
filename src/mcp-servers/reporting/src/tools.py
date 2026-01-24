"""MCP tools for Reporting services."""

from datetime import datetime
from typing import Any, Dict, Optional

from .models import (
    AverageDurationResult,
    LogStepResult,
    NORMALIZED_TOOL_NAMES,
)
from .services import ReportingService


class ReportingTools:
    """Reporting MCP tools implementation."""

    def __init__(self):
        """Initialize Reporting tools with service layer."""
        self.service = ReportingService()

    async def steps_logCompleted(
        self,
        tool_name: str,
        city: str,
        started_at: str,
        completed_at: str,
    ) -> Dict[str, Any]:
        """
        Log a completed step for reporting.

        Args:
            tool_name: Normalized tool name (e.g., permits.submit, tou.enroll)
            city: Geographic filter (e.g., Los Angeles)
            started_at: ISO timestamp when the step started
            completed_at: ISO timestamp when the step completed

        Returns:
            LogStepResult with confirmation
        """
        # Parse timestamps
        started_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        completed_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))

        result = await self.service.log_completed_step(
            tool_name=tool_name,
            city=city,
            started_at=started_dt,
            completed_at=completed_dt,
        )
        return result.model_dump()

    async def steps_getAverageDuration(
        self,
        tool_name: str,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get average duration for a step type.

        Args:
            tool_name: Tool name to query (e.g., permits.submit)
            city: Optional city filter for local relevance

        Returns:
            AverageDurationResult with average days and sample count
        """
        result = await self.service.get_average_duration(
            tool_name=tool_name,
            city=city,
        )
        return result.model_dump()
