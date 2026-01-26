"""Integration tests for Reporting CosmosDB operations.

These tests require a live CosmosDB instance with COSMOS_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.models import StepLog
from src.repositories import StepLogRepository


# Skip all tests in this file if CosmosDB is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("COSMOS_ENDPOINT"),
        reason="CosmosDB not configured (COSMOS_ENDPOINT not set)"
    )
]


@pytest.fixture(scope="session")
async def step_log_repository():
    """Create a StepLogRepository instance for testing."""
    return StepLogRepository()


class TestStepLogRepository:
    """Tests for step log repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_step_log(self, step_log_repository):
        """Create and retrieve a step log."""
        now = datetime.now(timezone.utc)
        started_at = now - timedelta(days=45)
        completed_at = now - timedelta(days=1)

        # Create step log
        log = await step_log_repository.create_step_log(
            tool_name="permits.submit",
            city="Los Angeles",
            started_at=started_at,
            completed_at=completed_at,
        )

        assert log.id is not None
        assert log.tool_name == "permits.submit"
        assert log.city == "Los Angeles"
        assert log.duration_days > 0

        # Retrieve logs by tool
        logs = await step_log_repository.get_logs_by_tool("permits.submit")
        assert len(logs) >= 1
        assert any(l.id == log.id for l in logs)

    @pytest.mark.asyncio
    async def test_create_step_log_calculates_duration(self, step_log_repository):
        """Verify duration calculation."""
        now = datetime.now(timezone.utc)
        started_at = now - timedelta(days=30)
        completed_at = now

        log = await step_log_repository.create_step_log(
            tool_name="tou.enroll",
            city="Los Angeles",
            started_at=started_at,
            completed_at=completed_at,
        )

        # Duration should be approximately 30 days
        assert 29 < log.duration_days < 31

    @pytest.mark.asyncio
    async def test_get_logs_by_tool(self, step_log_repository):
        """Get logs filtered by tool name."""
        now = datetime.now(timezone.utc)
        unique_suffix = str(uuid4())[:8]
        tool_name = f"test.tool.{unique_suffix}"

        # Create a few logs for this tool
        for i in range(3):
            await step_log_repository.create_step_log(
                tool_name=tool_name,
                city="Los Angeles",
                started_at=now - timedelta(days=i + 10),
                completed_at=now - timedelta(days=i),
            )

        logs = await step_log_repository.get_logs_by_tool(tool_name)
        assert len(logs) >= 3
        for log in logs:
            assert log.tool_name == tool_name

    @pytest.mark.asyncio
    async def test_get_logs_by_tool_and_city(self, step_log_repository):
        """Get logs filtered by tool and city."""
        now = datetime.now(timezone.utc)
        unique_suffix = str(uuid4())[:8]
        tool_name = f"test.city.{unique_suffix}"
        city = f"TestCity-{unique_suffix}"

        # Create logs for different cities
        await step_log_repository.create_step_log(
            tool_name=tool_name,
            city=city,
            started_at=now - timedelta(days=10),
            completed_at=now,
        )
        await step_log_repository.create_step_log(
            tool_name=tool_name,
            city="Other City",
            started_at=now - timedelta(days=5),
            completed_at=now,
        )

        # Filter by city
        logs = await step_log_repository.get_logs_by_tool(tool_name, city=city)
        assert len(logs) >= 1
        for log in logs:
            assert log.city == city

    @pytest.mark.asyncio
    async def test_get_logs_with_date_range(self, step_log_repository):
        """Get logs within date range."""
        now = datetime.now(timezone.utc)
        unique_suffix = str(uuid4())[:8]
        tool_name = f"test.range.{unique_suffix}"

        # Create an old log (7 months ago)
        await step_log_repository.create_step_log(
            tool_name=tool_name,
            city="Los Angeles",
            started_at=now - timedelta(days=220),
            completed_at=now - timedelta(days=210),
        )

        # Create a recent log (1 month ago)
        await step_log_repository.create_step_log(
            tool_name=tool_name,
            city="Los Angeles",
            started_at=now - timedelta(days=35),
            completed_at=now - timedelta(days=30),
        )

        # Filter by last 6 months
        since = now - timedelta(days=180)
        logs = await step_log_repository.get_logs_by_tool(tool_name, since=since)
        
        # Should only get the recent log
        assert len(logs) >= 1
        for log in logs:
            assert log.completed_at > since

    @pytest.mark.asyncio
    async def test_calculate_average_duration(self, step_log_repository):
        """Verify average calculation."""
        now = datetime.now(timezone.utc)
        unique_suffix = str(uuid4())[:8]
        tool_name = f"test.avg.{unique_suffix}"

        # Create logs with known durations (10, 20, 30 days)
        for days in [10, 20, 30]:
            await step_log_repository.create_step_log(
                tool_name=tool_name,
                city="Los Angeles",
                started_at=now - timedelta(days=days + 5),
                completed_at=now - timedelta(days=5),
            )

        average, count = await step_log_repository.calculate_average_duration(tool_name)
        
        assert count >= 3
        # Average should be around 20 days
        assert 15 < average < 25

    @pytest.mark.asyncio
    async def test_calculate_average_with_city_filter(self, step_log_repository):
        """Verify average with city filter."""
        now = datetime.now(timezone.utc)
        unique_suffix = str(uuid4())[:8]
        tool_name = f"test.avgcity.{unique_suffix}"
        city = f"AvgCity-{unique_suffix}"

        # Create logs for the target city (10, 20 days)
        for days in [10, 20]:
            await step_log_repository.create_step_log(
                tool_name=tool_name,
                city=city,
                started_at=now - timedelta(days=days + 2),
                completed_at=now - timedelta(days=2),
            )

        # Create log for different city (100 days)
        await step_log_repository.create_step_log(
            tool_name=tool_name,
            city="Other City",
            started_at=now - timedelta(days=102),
            completed_at=now - timedelta(days=2),
        )

        average, count = await step_log_repository.calculate_average_duration(
            tool_name, city=city
        )
        
        assert count >= 2
        # Average should be around 15 days (only city logs included)
        assert 10 < average < 25

    @pytest.mark.asyncio
    async def test_calculate_average_no_data(self, step_log_repository):
        """Handle case with no data."""
        unique_suffix = str(uuid4())[:8]
        tool_name = f"nonexistent.tool.{unique_suffix}"

        average, count = await step_log_repository.calculate_average_duration(tool_name)
        
        assert average == 0.0
        assert count == 0
