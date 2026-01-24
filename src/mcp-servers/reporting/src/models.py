"""Data models for Reporting MCP server."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Common Models (shared across MCP servers)
# =============================================================================


class MCPError(BaseModel):
    """Error response from MCP tool."""

    error: bool = Field(default=True, description="Always true for errors")
    code: str = Field(description="Error code: NOT_FOUND, INVALID_INPUT, SERVICE_UNAVAILABLE")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict] = Field(default=None, description="Additional error details")


# =============================================================================
# Reporting Models
# =============================================================================


class StepLog(BaseModel):
    """A logged step completion record."""

    id: str = Field(description="Unique ID for this log entry")
    tool_name: str = Field(description="Normalized tool name (e.g., permits.submit)")
    city: str = Field(description="City for geographic filtering")
    started_at: datetime = Field(description="When the step started")
    completed_at: datetime = Field(description="When the step completed")
    duration_days: float = Field(description="Duration in days")
    logged_at: datetime = Field(description="When this entry was logged")


class LogStepResult(BaseModel):
    """Result from logging a completed step."""

    success: bool = Field(description="Whether logging succeeded")
    log_id: str = Field(description="ID of the created log entry")
    message: str = Field(description="Confirmation message")


class AverageDurationResult(BaseModel):
    """Result from average duration query."""

    tool_name: str = Field(description="Tool name queried")
    city: Optional[str] = Field(description="City filter applied (if any)")
    average_days: float = Field(description="Average duration in days")
    sample_count: int = Field(description="Number of samples in calculation")
    period: str = Field(description="Time period for data (e.g., 'last 6 months')")
    message: Optional[str] = Field(default=None, description="Additional context")


# =============================================================================
# Normalized Tool Names
# =============================================================================


# These are the standard tool names for step tracking
NORMALIZED_TOOL_NAMES = [
    "permits.submit",        # Permit application (any type)
    "permits.getStatus",     # Permit status check
    "inspections.schedule",  # Schedule an inspection
    "tou.enroll",           # TOU rate enrollment
    "interconnection.submit", # Solar interconnection application
    "rebates.apply",        # Rebate application
    "pickup.schedule",      # Waste pickup scheduling
]
