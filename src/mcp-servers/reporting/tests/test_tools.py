"""Tests for Reporting MCP server tools."""

import pytest
from datetime import datetime, timedelta

from src.services import ReportingService
from src.models import NORMALIZED_TOOL_NAMES


@pytest.fixture
def service():
    """Create a fresh ReportingService instance."""
    return ReportingService()


class TestLogCompletedStep:
    """Tests for logging completed steps."""

    @pytest.mark.asyncio
    async def test_log_step_success(self, service):
        """Test successfully logging a completed step."""
        result = await service.log_completed_step(
            tool_name="permits.submit",
            city="Los Angeles",
            started_at=datetime(2026, 1, 15, 10, 0, 0),
            completed_at=datetime(2026, 2, 28, 14, 30, 0),
        )
        
        assert result.success is True
        assert result.log_id.startswith("LOG-")
        assert "permits.submit" in result.message

    @pytest.mark.asyncio
    async def test_log_step_calculates_duration(self, service):
        """Test that duration is correctly calculated."""
        start = datetime(2026, 1, 1, 0, 0, 0)
        end = datetime(2026, 1, 8, 0, 0, 0)  # 7 days later
        
        result = await service.log_completed_step(
            tool_name="tou.enroll",
            city="Los Angeles",
            started_at=start,
            completed_at=end,
        )
        
        assert result.success is True
        assert "7.0 days" in result.message

    @pytest.mark.asyncio
    async def test_log_step_with_nonstandard_tool(self, service):
        """Test logging with a non-standard tool name."""
        result = await service.log_completed_step(
            tool_name="custom.tool",
            city="Los Angeles",
            started_at=datetime(2026, 1, 1),
            completed_at=datetime(2026, 1, 2),
        )
        
        # Should still succeed (allow non-standard tools)
        assert result.success is True


class TestGetAverageDuration:
    """Tests for querying average durations."""

    @pytest.mark.asyncio
    async def test_get_average_with_city(self, service):
        """Test getting average duration with city filter."""
        result = await service.get_average_duration(
            tool_name="permits.submit",
            city="Los Angeles",
        )
        
        assert result.tool_name == "permits.submit"
        assert result.city == "Los Angeles"
        assert result.sample_count > 0
        assert result.average_days > 0
        assert result.period == "last 6 months"

    @pytest.mark.asyncio
    async def test_get_average_without_city(self, service):
        """Test getting average duration without city filter."""
        result = await service.get_average_duration(
            tool_name="permits.submit",
        )
        
        assert result.tool_name == "permits.submit"
        assert result.city is None
        assert result.sample_count > 0

    @pytest.mark.asyncio
    async def test_get_average_unknown_tool(self, service):
        """Test getting average for unknown tool."""
        result = await service.get_average_duration(
            tool_name="unknown.tool",
            city="Los Angeles",
        )
        
        assert result.sample_count == 0
        assert result.average_days == 0
        assert "No data available" in result.message

    @pytest.mark.asyncio
    async def test_get_average_unknown_city(self, service):
        """Test getting average for unknown city."""
        result = await service.get_average_duration(
            tool_name="permits.submit",
            city="Unknown City",
        )
        
        assert result.sample_count == 0
        assert "No data available" in result.message

    @pytest.mark.asyncio
    async def test_all_standard_tools_have_data(self, service):
        """Test that all standard tools have mock data."""
        tools_with_data = [
            "permits.submit",
            "tou.enroll",
            "interconnection.submit",
            "rebates.apply",
            "inspections.schedule",
            "pickup.schedule",
        ]
        
        for tool_name in tools_with_data:
            result = await service.get_average_duration(
                tool_name=tool_name,
                city="Los Angeles",
            )
            assert result.sample_count > 0, f"No data for {tool_name}"


class TestNormalizedToolNames:
    """Tests for normalized tool names."""

    def test_all_expected_tools_defined(self):
        """Test that all expected tool names are defined."""
        expected_tools = [
            "permits.submit",
            "permits.getStatus",
            "inspections.schedule",
            "tou.enroll",
            "interconnection.submit",
            "rebates.apply",
            "pickup.schedule",
        ]
        
        for tool in expected_tools:
            assert tool in NORMALIZED_TOOL_NAMES
