"""Reporting MCP Server - Track step durations for reporting and surface average times."""

import asyncio
import json
from typing import Optional

from fastmcp import FastMCP

from src.tools import ReportingTools

# Initialize FastMCP server
mcp = FastMCP("Reporting")

# Initialize tools
tools = ReportingTools()


@mcp.tool(title="Log Completed Step")
async def steps_logCompleted(
    tool_name: str,
    city: str,
    started_at: str,
    completed_at: str,
) -> str:
    """
    Log a completed step for reporting. Call this when a plan step is completed.

    Args:
        tool_name: Normalized tool name (e.g., permits.submit, tou.enroll, interconnection.submit)
        city: Geographic filter for local relevance (e.g., Los Angeles)
        started_at: ISO timestamp when the step started (e.g., 2026-01-15T10:00:00Z)
        completed_at: ISO timestamp when the step completed (e.g., 2026-02-28T14:30:00Z)

    Returns:
        Confirmation with log ID
    """
    result = await tools.steps_logCompleted(
        tool_name=tool_name,
        city=city,
        started_at=started_at,
        completed_at=completed_at,
    )
    return json.dumps(result, indent=2)


@mcp.tool(title="Get Average Step Duration")
async def steps_getAverageDuration(
    tool_name: str,
    city: Optional[str] = None,
) -> str:
    """
    Get average duration for a step type based on historical data.

    Use this to answer questions like "how long will this take?" or when building plans
    to set realistic timeline expectations.

    Args:
        tool_name: Tool name to query (e.g., permits.submit, tou.enroll, rebates.apply)
        city: Optional city filter for local relevance (e.g., Los Angeles)

    Returns:
        Average duration in days and sample count from last 6 months
    """
    result = await tools.steps_getAverageDuration(
        tool_name=tool_name,
        city=city,
    )
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=8000))
