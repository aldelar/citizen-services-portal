"""Data models for LADWP MCP server."""

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
# LADWP Enums
# =============================================================================


class RatePlan(str, Enum):
    """LADWP rate plan options."""

    STANDARD = "standard"
    TOU_D_A = "TOU-D-A"
    TOU_D_B = "TOU-D-B"
    TOU_D_PRIME = "TOU-D-PRIME"  # For solar customers


class MeterType(str, Enum):
    """Type of utility meter."""

    STANDARD = "standard"
    TOU = "tou"
    NET_METER = "net_meter"


class EquipmentType(str, Enum):
    """Type of equipment eligible for rebates."""

    HEAT_PUMP_HVAC = "heat_pump_hvac"
    HEAT_PUMP_WATER_HEATER = "heat_pump_water_heater"
    SMART_THERMOSTAT = "smart_thermostat"


class RebateStatus(str, Enum):
    """Status of a rebate application."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


class InterconnectionStatus(str, Enum):
    """Status of solar interconnection application."""

    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    ENGINEERING_REVIEW = "engineering_review"
    APPROVED = "approved"
    PTO_ISSUED = "pto_issued"  # Permission to Operate
    DENIED = "denied"


# =============================================================================
# LADWP Models
# =============================================================================


class Account(BaseModel):
    """LADWP utility account information."""

    account_number: str = Field(description="Unique account number")
    account_holder: str = Field(description="Name of account holder")
    service_address: str = Field(description="Service address")
    current_rate_plan: RatePlan = Field(description="Current rate plan")
    meter_type: MeterType = Field(description="Type of meter installed")
    pending_requests: List[str] = Field(default_factory=list, description="Pending requests")
    has_solar: bool = Field(default=False, description="Whether account has solar")
    has_battery: bool = Field(default=False, description="Whether account has battery storage")


class RateSchedule(BaseModel):
    """Rate schedule details."""

    off_peak_rate: float = Field(description="Off-peak rate $/kWh")
    mid_peak_rate: Optional[float] = Field(default=None, description="Mid-peak rate $/kWh (TOU only)")
    on_peak_rate: Optional[float] = Field(default=None, description="On-peak rate $/kWh (TOU only)")
    off_peak_hours: Optional[str] = Field(default=None, description="Off-peak hours")
    on_peak_hours: Optional[str] = Field(default=None, description="On-peak hours")


class RatePlanInfo(BaseModel):
    """Rate plan details."""

    plan_code: RatePlan = Field(description="Plan code")
    plan_name: str = Field(description="Human-readable plan name")
    description: str = Field(description="Plan description")
    rates: RateSchedule = Field(description="Rate schedule")
    eligibility: str = Field(description="Who can enroll")
    best_for: str = Field(description="Who this plan suits best")


class PlansListResult(BaseModel):
    """Result from plans list query."""

    current_plan: RatePlan = Field(description="Current rate plan")
    available_plans: List[RatePlanInfo] = Field(description="Available rate plans")
    recommended_plan: Optional[RatePlan] = Field(default=None, description="Recommended plan")
    recommendation_reason: Optional[str] = Field(default=None, description="Why this plan is recommended")


class TOUEnrollmentResult(BaseModel):
    """Result of TOU enrollment."""

    success: bool = Field(description="Whether enrollment succeeded")
    confirmation_number: str = Field(description="Confirmation number")
    rate_plan: RatePlan = Field(description="Enrolled rate plan")
    effective_date: datetime = Field(description="When new rate takes effect")
    meter_swap_required: bool = Field(description="Whether meter swap is needed")
    meter_swap_date: Optional[datetime] = Field(default=None, description="Scheduled meter swap date")
    next_steps: str = Field(description="Next steps for customer")


class Interconnection(BaseModel):
    """Solar interconnection application status."""

    application_id: Optional[str] = Field(default=None, description="Application ID")
    address: str = Field(description="Service address")
    system_size_kw: float = Field(description="System size in kW")
    battery_size_kwh: Optional[float] = Field(default=None, description="Battery size in kWh")
    status: InterconnectionStatus = Field(description="Current status")
    submitted_at: Optional[datetime] = Field(default=None, description="When submitted")
    approved_at: Optional[datetime] = Field(default=None, description="When approved")
    pto_date: Optional[datetime] = Field(default=None, description="Permission to Operate date")
    next_steps: Optional[str] = Field(default=None, description="Next steps")


class RebateApplication(BaseModel):
    """Rebate application information."""

    application_id: str = Field(description="Application ID")
    account_number: str = Field(description="Account number")
    equipment_type: EquipmentType = Field(description="Type of equipment")
    status: RebateStatus = Field(description="Current status")
    submitted_at: datetime = Field(description="When submitted")
    equipment_details: str = Field(description="Equipment make, model, specs")
    estimated_rebate: float = Field(description="Estimated rebate amount")
    approved_amount: Optional[float] = Field(default=None, description="Approved rebate amount")
    paid_at: Optional[datetime] = Field(default=None, description="When rebate was paid")
    denial_reason: Optional[str] = Field(default=None, description="Reason for denial if applicable")


class RebatesFiledResult(BaseModel):
    """Result from rebates filed query."""

    applications: List[RebateApplication] = Field(description="Rebate applications")
    total_count: int = Field(description="Total count")


class RebateApplyResult(BaseModel):
    """Result from rebate application submission."""

    success: bool = Field(description="Whether submission succeeded")
    application_id: str = Field(description="Application ID")
    estimated_rebate: float = Field(description="Estimated rebate amount")
    processing_time: str = Field(description="Estimated processing time")
    next_steps: str = Field(description="Next steps")
