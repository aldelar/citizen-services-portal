"""Data models for CSP (Citizen Services Portal) MCP server.

This server manages:
1. Plan Lifecycle Management - Create, update, and modify project plans via MCP tools
2. Step Timing Analytics - Track step completion durations for reporting
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
# Enums
# =============================================================================


class StepStatus(str, Enum):
    """Step status for plan steps."""
    DEFINED = "defined"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REWORK = "needs_rework"
    REJECTED = "rejected"


class StepType(str, Enum):
    """Step type codes for plan steps and analytics aggregation."""
    PRM = "PRM"  # Permit - apply for/obtain official permits
    INS = "INS"  # Inspection - city inspections including final sign-off
    TRD = "TRD"  # Trade - hire professionals + physical work phases
    APP = "APP"  # Application - non-permit applications
    PCK = "PCK"  # Pickup - schedule pickups/drop-offs (LASAN)
    ENR = "ENR"  # Enroll - sign up for programs/plans
    DOC = "DOC"  # Document - gather documents/materials
    PAY = "PAY"  # Payment - pay fees/deposits


class Agency(str, Enum):
    """Supported agencies."""
    LADBS = "LADBS"
    LADWP = "LADWP"
    LASAN = "LASAN"


# =============================================================================
# Action Card Models
# =============================================================================


class ActionCard(BaseModel):
    """Structured prompt for user-driven steps."""
    
    title: str = Field(description="Action card title, e.g., 'Install Solar Panels'")
    description: str = Field(description="What needs to be done")
    instructions: Optional[List[str]] = Field(default=[], description="Step-by-step guidance")
    completion_prompt: str = Field(description="e.g., 'Click when installation is complete'")
    created_at: datetime = Field(description="When the action card was created")


# =============================================================================
# Plan Step Models
# =============================================================================


class PlanStepInput(BaseModel):
    """Step input from agent for plan.create and plan.update."""
    
    id: str = Field(description="Short ID (e.g., 'P1', 'I1', 'I1.2')")
    step_type: StepType = Field(description="Normalized step type for analytics")
    title: str = Field(description="Human-readable step name")
    description: Optional[str] = Field(default=None, description="Detailed description")
    agency: str = Field(description="Agency code (LADBS, LADWP, LASAN)")
    automated: bool = Field(default=True, description="True = agent-driven, False = user-driven")
    depends_on: List[str] = Field(default=[], description="IDs of prerequisite steps")
    
    # For rework scenarios
    supersedes: Optional[str] = Field(default=None, description="ID of step this replaces")
    attempt_number: int = Field(default=1, description="Attempt number (2, 3, etc. for retries)")


class PlanStep(BaseModel):
    """A single step in the project plan."""
    
    # Identity
    id: str = Field(description="Short ID (e.g., 'P1', 'I1', 'I1.2')")
    step_type: StepType = Field(description="Normalized type for analytics")
    
    # Display
    title: str = Field(description="Human-readable step name")
    description: Optional[str] = Field(default=None, description="Detailed description")
    agency: str = Field(description="Agency code (LADBS, LADWP, LASAN)")
    
    # Automation
    automated: bool = Field(default=True, description="True = agent-driven, False = user-driven")
    action_card: Optional[ActionCard] = Field(default=None, description="Generated on IN_PROGRESS for non-automated")
    
    # Dependencies
    depends_on: List[str] = Field(default=[], description="IDs of prerequisite steps")
    
    # Lineage (for rework chains)
    supersedes: Optional[str] = Field(default=None, description="ID of step this replaces")
    attempt_number: int = Field(default=1, description="1, 2, 3... for retries")
    
    # Status & Timing (managed by MCP CSP service)
    status: StepStatus = Field(default=StepStatus.DEFINED)
    started_at: Optional[datetime] = Field(default=None, description="Set on SCHEDULED or IN_PROGRESS")
    completed_at: Optional[datetime] = Field(default=None, description="Set on terminal status")
    
    # Estimated Duration (populated by MCP CSP service layer)
    estimated_duration_days: Optional[float] = Field(default=None)
    
    # Results (set on completion)
    result: Optional[Dict[str, Any]] = Field(default=None, description="Outcome data (permit #, failure reason, etc.)")
    notes: Optional[str] = Field(default=None, description="Additional notes")


# =============================================================================
# Plan Models
# =============================================================================


class Plan(BaseModel):
    """The project plan with all steps."""
    
    id: str = Field(description="Plan UUID")
    status: str = Field(default="active", description="'active', 'completed'")
    steps: List[PlanStep] = Field(default=[], description="List of plan steps")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


# =============================================================================
# Plan Tool Response Models
# =============================================================================


class PlanGetResponse(BaseModel):
    """Response from plan.get tool."""
    
    project_id: str = Field(description="Project UUID")
    plan: Optional[Plan] = Field(description="The project plan, or None if no plan exists")
    message: Optional[str] = Field(default=None, description="Additional context")


class PlanCreateResponse(BaseModel):
    """Response from plan.create tool."""
    
    success: bool = Field(description="Whether creation succeeded")
    project_id: str = Field(description="Project UUID")
    plan: Plan = Field(description="Created plan with estimates populated")
    message: str = Field(description="Confirmation message")


class PlanUpdateResponse(BaseModel):
    """Response from plan.update tool."""
    
    success: bool = Field(description="Whether update succeeded")
    project_id: str = Field(description="Project UUID")
    plan: Plan = Field(description="Updated plan with estimates populated")
    message: str = Field(description="Confirmation message")


class StepUpdateResponse(BaseModel):
    """Response from plan.updateStep tool."""
    
    success: bool = Field(description="Whether update succeeded")
    project_id: str = Field(description="Project UUID")
    step: PlanStep = Field(description="Updated step details")
    timing_logged: bool = Field(default=False, description="Whether timing was logged to step_completions")
    message: str = Field(description="Confirmation message")


# =============================================================================
# Step Completion Models (for analytics)
# =============================================================================


class StepCompletion(BaseModel):
    """Anonymized step completion record for reporting."""
    
    id: str = Field(description="Unique ID for this completion")
    step_type: StepType = Field(description="Step type for aggregation")
    chain_started_at: datetime = Field(description="When the chain started (first step's started_at)")
    completed_at: datetime = Field(description="When the chain completed (final step's completed_at)")
    duration_days: float = Field(description="End-to-end duration in days")
    attempts: int = Field(default=1, description="Number of attempts in the chain")
    logged_at: datetime = Field(description="When this entry was logged")


class StepLog(BaseModel):
    """A logged step completion record (legacy format for backward compatibility)."""

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

    step_type: str = Field(description="Step type queried")
    average_days: float = Field(description="Average duration in days")
    sample_count: int = Field(description="Number of samples in calculation")
    period: str = Field(description="Time period for data (e.g., 'last 6 months')")
    message: Optional[str] = Field(default=None, description="Additional context")


# =============================================================================
# Step Type Mapping
# =============================================================================


# Map step types to their valid status progressions
STEP_STATUS_PROGRESSIONS = {
    StepType.PRM: [StepStatus.DEFINED, StepStatus.IN_PROGRESS, StepStatus.COMPLETED, StepStatus.REJECTED],
    StepType.INS: [StepStatus.DEFINED, StepStatus.SCHEDULED, StepStatus.COMPLETED, StepStatus.NEEDS_REWORK],
    StepType.TRD: [StepStatus.DEFINED, StepStatus.IN_PROGRESS, StepStatus.COMPLETED],
    StepType.APP: [StepStatus.DEFINED, StepStatus.IN_PROGRESS, StepStatus.COMPLETED, StepStatus.REJECTED],
    StepType.PCK: [StepStatus.DEFINED, StepStatus.SCHEDULED, StepStatus.COMPLETED],
    StepType.ENR: [StepStatus.DEFINED, StepStatus.IN_PROGRESS, StepStatus.COMPLETED, StepStatus.REJECTED],
    StepType.DOC: [StepStatus.DEFINED, StepStatus.IN_PROGRESS, StepStatus.COMPLETED],
    StepType.PAY: [StepStatus.DEFINED, StepStatus.IN_PROGRESS, StepStatus.COMPLETED],
}


# Terminal statuses that complete a step
TERMINAL_STATUSES = {StepStatus.COMPLETED, StepStatus.NEEDS_REWORK, StepStatus.REJECTED}


# Statuses that start timing
TIMING_START_STATUSES = {StepStatus.SCHEDULED, StepStatus.IN_PROGRESS}
