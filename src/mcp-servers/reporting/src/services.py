"""Business logic and external service integration for Reporting."""

import logging
import os
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .config import settings
from .models import (
    AverageDurationResult,
    LogStepResult,
    NORMALIZED_TOOL_NAMES,
    StepLog,
)

logger = logging.getLogger(__name__)

# Check if CosmosDB is configured
_cosmos_enabled = bool(os.environ.get("COSMOS_ENDPOINT"))


def _get_repository():
    """Get repository instance if CosmosDB is enabled."""
    if not _cosmos_enabled:
        return None
    
    try:
        from .repositories import StepLogRepository
        return StepLogRepository()
    except Exception as e:
        logger.warning(f"Failed to initialize CosmosDB repository: {e}")
        return None


class ReportingService:
    """Service layer for Reporting operations."""

    def __init__(self):
        """Initialize Reporting service."""
        self.cosmos_endpoint = settings.cosmos_endpoint
        self.database_name = settings.cosmos_database
        self.container_name = settings.cosmos_container
        self._step_log_repo = _get_repository()
        
        # Only use in-memory storage if CosmosDB is not available
        if not self._step_log_repo:
            self._step_logs: List[StepLog] = []
            self._initialize_mock_data()

    @property
    def cosmos_enabled(self) -> bool:
        """Check if CosmosDB is enabled."""
        return self._step_log_repo is not None

    def _generate_id(self, prefix: str = "LOG") -> str:
        """Generate a random ID."""
        random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}-{random_suffix}"

    def _initialize_mock_data(self):
        """Initialize with mock historical data for realistic responses."""
        # Create mock historical data for the last 6 months
        now = datetime.now()
        mock_data = [
            # Permit submissions - typically take 4-8 weeks
            {"tool_name": "permits.submit", "city": "Los Angeles", "duration_days": 42},
            {"tool_name": "permits.submit", "city": "Los Angeles", "duration_days": 56},
            {"tool_name": "permits.submit", "city": "Los Angeles", "duration_days": 35},
            {"tool_name": "permits.submit", "city": "Los Angeles", "duration_days": 49},
            {"tool_name": "permits.submit", "city": "Los Angeles", "duration_days": 45},
            {"tool_name": "permits.submit", "city": "Los Angeles", "duration_days": 52},
            # TOU enrollment - quick, typically 1-3 days
            {"tool_name": "tou.enroll", "city": "Los Angeles", "duration_days": 1},
            {"tool_name": "tou.enroll", "city": "Los Angeles", "duration_days": 2},
            {"tool_name": "tou.enroll", "city": "Los Angeles", "duration_days": 1},
            {"tool_name": "tou.enroll", "city": "Los Angeles", "duration_days": 3},
            # Interconnection - takes 2-4 weeks
            {"tool_name": "interconnection.submit", "city": "Los Angeles", "duration_days": 21},
            {"tool_name": "interconnection.submit", "city": "Los Angeles", "duration_days": 28},
            {"tool_name": "interconnection.submit", "city": "Los Angeles", "duration_days": 18},
            {"tool_name": "interconnection.submit", "city": "Los Angeles", "duration_days": 25},
            # Rebates - typically 6-10 weeks
            {"tool_name": "rebates.apply", "city": "Los Angeles", "duration_days": 49},
            {"tool_name": "rebates.apply", "city": "Los Angeles", "duration_days": 56},
            {"tool_name": "rebates.apply", "city": "Los Angeles", "duration_days": 63},
            {"tool_name": "rebates.apply", "city": "Los Angeles", "duration_days": 52},
            # Inspections - scheduled 3-7 days out
            {"tool_name": "inspections.schedule", "city": "Los Angeles", "duration_days": 5},
            {"tool_name": "inspections.schedule", "city": "Los Angeles", "duration_days": 4},
            {"tool_name": "inspections.schedule", "city": "Los Angeles", "duration_days": 7},
            {"tool_name": "inspections.schedule", "city": "Los Angeles", "duration_days": 3},
            # Pickup scheduling - typically same week
            {"tool_name": "pickup.schedule", "city": "Los Angeles", "duration_days": 3},
            {"tool_name": "pickup.schedule", "city": "Los Angeles", "duration_days": 5},
            {"tool_name": "pickup.schedule", "city": "Los Angeles", "duration_days": 4},
        ]

        for entry in mock_data:
            # Create mock log entries with varying dates
            days_ago = random.randint(7, 180)
            completed_at = now - timedelta(days=days_ago)
            started_at = completed_at - timedelta(days=entry["duration_days"])
            
            log = StepLog(
                id=self._generate_id(),
                tool_name=entry["tool_name"],
                city=entry["city"],
                started_at=started_at,
                completed_at=completed_at,
                duration_days=entry["duration_days"],
                logged_at=completed_at,
            )
            self._step_logs.append(log)

    async def log_completed_step(
        self,
        tool_name: str,
        city: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> LogStepResult:
        """
        Log a completed step for reporting.

        Args:
            tool_name: Normalized tool name (e.g., permits.submit)
            city: Geographic filter (e.g., Los Angeles)
            started_at: When the step started
            completed_at: When the step completed

        Returns:
            LogStepResult with confirmation
        """
        # Validate tool name
        if tool_name not in NORMALIZED_TOOL_NAMES:
            # Allow it but note it's non-standard
            pass

        # Use CosmosDB if available
        if self._step_log_repo:
            try:
                log = await self._step_log_repo.create_step_log(
                    tool_name=tool_name,
                    city=city,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                return LogStepResult(
                    success=True,
                    log_id=log.id,
                    message=f"Successfully logged {tool_name} completion ({log.duration_days:.1f} days)",
                )
            except Exception as e:
                logger.error(f"Error logging step to CosmosDB: {e}")
                # Fall through to mock

        # Calculate duration
        duration = completed_at - started_at
        duration_days = duration.total_seconds() / (24 * 60 * 60)

        # Create log entry
        log_id = self._generate_id()
        log = StepLog(
            id=log_id,
            tool_name=tool_name,
            city=city,
            started_at=started_at,
            completed_at=completed_at,
            duration_days=duration_days,
            logged_at=datetime.now(),
        )

        # In-memory storage for mock
        
        self._step_logs.append(log)

        return LogStepResult(
            success=True,
            log_id=log_id,
            message=f"Successfully logged {tool_name} completion ({duration_days:.1f} days)",
        )

    async def get_average_duration(
        self,
        tool_name: str,
        city: Optional[str] = None,
    ) -> AverageDurationResult:
        """
        Get average duration for a step type.

        Args:
            tool_name: Tool name to query (e.g., permits.submit)
            city: Optional city filter

        Returns:
            AverageDurationResult with average days and sample count
        """
        # Use CosmosDB if available
        if self._step_log_repo:
            try:
                average_days, sample_count = await self._step_log_repo.calculate_average_duration(
                    tool_name=tool_name,
                    city=city,
                    months=6,
                )
                
                if sample_count == 0:
                    return AverageDurationResult(
                        tool_name=tool_name,
                        city=city,
                        average_days=0,
                        sample_count=0,
                        period="last 6 months",
                        message=f"No data available for {tool_name}" + (f" in {city}" if city else ""),
                    )
                
                return AverageDurationResult(
                    tool_name=tool_name,
                    city=city,
                    average_days=average_days,
                    sample_count=sample_count,
                    period="last 6 months",
                    message=None,
                )
            except Exception as e:
                logger.error(f"Error querying CosmosDB for average duration: {e}")
                # Fall through to mock

        # Filter logs from last 6 months (mock implementation)
        six_months_ago = datetime.now() - timedelta(days=180)
        
        filtered_logs = [
            log for log in self._step_logs
            if log.tool_name == tool_name
            and log.completed_at > six_months_ago
            and (city is None or log.city == city)
        ]

        if not filtered_logs:
            return AverageDurationResult(
                tool_name=tool_name,
                city=city,
                average_days=0,
                sample_count=0,
                period="last 6 months",
                message=f"No data available for {tool_name}" + (f" in {city}" if city else ""),
            )

        # Calculate average
        total_days = sum(log.duration_days for log in filtered_logs)
        average_days = total_days / len(filtered_logs)

        return AverageDurationResult(
            tool_name=tool_name,
            city=city,
            average_days=round(average_days, 1),
            sample_count=len(filtered_logs),
            period="last 6 months",
            message=None,
        )
