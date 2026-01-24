"""Data models for LADBS MCP server."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Common Models (shared across MCP servers)
# =============================================================================


class DocumentChunk(BaseModel):
    """A chunk of document content from knowledge base."""

    content: str = Field(description="Text content")
    source: str = Field(description="Source document name")
    relevance_score: float = Field(description="Relevance score 0.0 to 1.0", ge=0.0, le=1.0)


class KnowledgeResult(BaseModel):
    """Result from knowledge base query."""

    query: str = Field(description="Original query")
    results: List[DocumentChunk] = Field(description="Matching document chunks")
    total_results: int = Field(description="Total matches found")


class PreparedMaterials(BaseModel):
    """Materials prepared for user action."""

    phone_script: Optional[str] = Field(default=None, description="What to say on phone")
    email_draft: Optional[str] = Field(default=None, description="Draft email content")
    checklist: List[str] = Field(default_factory=list, description="Items to have ready")
    contact_info: Optional[Dict[str, str]] = Field(default=None, description="Phone, hours, address")
    documents_needed: List[str] = Field(default_factory=list, description="Documents to prepare")


class OnCompletePrompt(BaseModel):
    """What to ask user after they complete action."""

    prompt: str = Field(description="Question to ask")
    expected_info: List[str] = Field(description="Fields to collect")


class UserActionResponse(BaseModel):
    """Response when user must take action (cannot be automated)."""

    requires_user_action: bool = Field(default=True, description="Always true for user actions")
    action_type: str = Field(description="phone_call, email, in_person, online_portal")
    target: str = Field(description="311, email address, URL, or office location")
    reason: str = Field(description="Why this can't be automated")
    prepared_materials: PreparedMaterials = Field(description="Materials prepared for the user")
    on_complete: OnCompletePrompt = Field(description="What to ask after user completes action")


class MCPError(BaseModel):
    """Error response from MCP tool."""

    error: bool = Field(default=True, description="Always true for errors")
    code: str = Field(description="Error code: NOT_FOUND, INVALID_INPUT, SERVICE_UNAVAILABLE")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict] = Field(default=None, description="Additional error details")


# =============================================================================
# LADBS Enums
# =============================================================================


class PermitType(str, Enum):
    """Type of building permit."""

    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    BUILDING = "building"
    PLUMBING = "plumbing"


class PermitStatus(str, Enum):
    """Status of a permit application."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CORRECTIONS_REQUIRED = "corrections_required"
    APPROVED = "approved"
    ISSUED = "issued"
    EXPIRED = "expired"
    REJECTED = "rejected"


class InspectionType(str, Enum):
    """Type of building inspection."""

    ROUGH_ELECTRICAL = "rough_electrical"
    FINAL_ELECTRICAL = "final_electrical"
    ROUGH_MECHANICAL = "rough_mechanical"
    FINAL_MECHANICAL = "final_mechanical"
    FRAMING = "framing"
    FINAL = "final"


class InspectionStatus(str, Enum):
    """Status of an inspection."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# LADBS Models
# =============================================================================


class PermitFees(BaseModel):
    """Fee breakdown for permit."""

    plan_check: float = Field(description="Plan check fee")
    permit_fee: float = Field(description="Permit fee")
    other_fees: float = Field(description="Other fees")
    total: float = Field(description="Total fees")


class Permit(BaseModel):
    """Permit information."""

    permit_number: str = Field(description="Unique permit number")
    permit_type: PermitType = Field(description="Type of permit")
    status: PermitStatus = Field(description="Current status")
    address: str = Field(description="Property address")
    description: str = Field(description="Work description")
    applicant_name: str = Field(description="Name of applicant")
    submitted_at: datetime = Field(description="When submitted")
    approved_at: Optional[datetime] = Field(default=None, description="When approved")
    expires_at: Optional[datetime] = Field(default=None, description="When permit expires")
    fees: Optional[PermitFees] = Field(default=None, description="Fee breakdown")
    next_steps: Optional[str] = Field(default=None, description="Recommended next steps")


class PermitSearchResult(BaseModel):
    """Result from permit search."""

    permits: List[Permit] = Field(description="Matching permits")
    total_count: int = Field(description="Total number of matches")


class Applicant(BaseModel):
    """Applicant information for permit submission."""

    name: str = Field(description="Applicant name")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    contractor_license: Optional[str] = Field(default=None, description="Contractor license number")


class PermitSubmitResult(BaseModel):
    """Result from permit submission."""

    success: bool = Field(description="Whether submission succeeded")
    permit_number: str = Field(description="Assigned permit number")
    status: PermitStatus = Field(description="Initial status")
    submitted_at: datetime = Field(description="Submission timestamp")
    fees: PermitFees = Field(description="Fee breakdown")
    estimated_review_time: str = Field(description="Estimated review time, e.g., '4-6 weeks'")
    next_steps: str = Field(description="Next steps for applicant")


class Inspection(BaseModel):
    """Inspection information."""

    inspection_id: str = Field(description="Unique inspection ID")
    permit_number: str = Field(description="Associated permit number")
    inspection_type: InspectionType = Field(description="Type of inspection")
    status: InspectionStatus = Field(description="Current status")
    scheduled_date: Optional[datetime] = Field(default=None, description="Scheduled date")
    scheduled_time_window: Optional[str] = Field(default=None, description="Time window, e.g., '8am-12pm'")
    completed_at: Optional[datetime] = Field(default=None, description="When completed")
    result: Optional[str] = Field(default=None, description="Pass/fail result")
    inspector_notes: Optional[str] = Field(default=None, description="Inspector notes")


class InspectionListResult(BaseModel):
    """Result from inspection listing."""

    inspections: List[Inspection] = Field(description="List of inspections")
    total_count: int = Field(description="Total count")
