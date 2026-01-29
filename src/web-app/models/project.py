"""Project and Plan models for the Citizen Services Portal."""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step status enumeration."""
    DEFINED = "defined"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REWORK = "needs_rework"
    REJECTED = "rejected"


class UserTaskType(str, Enum):
    """User action type enumeration."""
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    IN_PERSON = "in_person"
    ONLINE_PORTAL = "online_portal"


class ActionType(str, Enum):
    """Step action type enumeration - determines if step is automated or requires user action."""
    AUTOMATED = "automated"  # Agent can execute directly via tools
    USER_ACTION = "user_action"  # User must take action (call, email, visit)


class StepType(str, Enum):
    """Step type enumeration - categorizes what kind of task the step represents."""
    PRM = "PRM"  # Permit - apply for/obtain official permits
    INS = "INS"  # Inspection - city inspections including final sign-off
    TRD = "TRD"  # Trade - hire professionals + physical work phases
    APP = "APP"  # Application - non-permit applications
    PCK = "PCK"  # Pickup - schedule pickups/drop-offs (LASAN)
    ENR = "ENR"  # Enroll - sign up for programs/plans
    DOC = "DOC"  # Document - gather documents/materials
    PAY = "PAY"  # Payment - pay fees/deposits


class ActionCardType(str, Enum):
    """Types of user action cards."""
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    FORM_SUBMISSION = "form_submission"
    IN_PERSON = "in_person"
    UPLOAD = "upload"


class StepEventType(str, Enum):
    """Types of events in a step's history."""
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    TOOL_EXECUTED = "tool_executed"
    CARD_ASSIGNED = "card_assigned"
    USER_NOTIFIED = "user_notified"
    USER_COMPLETED = "user_completed"
    AGENT_VERIFIED = "agent_verified"
    BLOCKED = "blocked"
    UNBLOCKED = "unblocked"
    NOTE_ADDED = "note_added"
    RETRY_REQUESTED = "retry_requested"


class UserTask(BaseModel):
    """Details for user-action steps (legacy - use UserActionCard instead)."""
    type: UserTaskType
    target: str  # "311", email, URL, or location
    reason: str  # Why this can't be automated
    assigned_at: Optional[datetime] = None
    phone_script: Optional[str] = None
    email_draft: Optional[str] = None
    checklist: List[str] = []
    contact_info: Optional[Dict[str, str]] = None


# ============================================================================
# Enhanced Plan Tracking Models
# ============================================================================


class ToolExecutionRecord(BaseModel):
    """Record of an automated tool execution."""
    tool_name: str  # e.g., "ladbs.submit_permit"
    request_id: Optional[str] = None  # ID returned by the tool
    reference_number: Optional[str] = None  # Business reference (permit #, application #)
    reference_url: Optional[str] = None  # Deep link to view the request/record
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class UserActionCard(BaseModel):
    """The action card shown to the user for a user-driven step."""
    step_id: str  # Required - links to plan step
    card_type: str  # phone_call, email, form_submission, in_person, upload
    title: str  # Short title for the card
    instructions: str  # Full markdown instructions

    # Prepared materials
    phone_script: Optional[str] = None
    email_draft: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    checklist: List[str] = Field(default_factory=list)

    # Contact/action info
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    action_url: Optional[str] = None

    # Timing
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_by: Optional[datetime] = None
    estimated_duration: Optional[str] = None


class CompletionRecord(BaseModel):
    """Record of step completion."""
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_by: str  # "agent" or "user:<user_id>"

    # For user-driven steps
    user_message: Optional[str] = None
    user_provided_data: Optional[Dict[str, Any]] = None

    # For automated steps
    tool_result: Optional[Dict[str, Any]] = None

    # Verification
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None


class StepEvent(BaseModel):
    """A single event in a step's history."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str  # See StepEventType
    actor: str  # "agent", "user:<id>", "system"
    summary: str  # Human-readable description
    details: Optional[Dict[str, Any]] = None
    message_id: Optional[str] = None


class PlanStep(BaseModel):
    """A single step in the project plan."""
    id: str  # Step ID in format TYPE-N (e.g., PRM-1, INS-2, TRD-1)
    title: str  # Human-readable step name
    agency: str  # LADBS, LADWP, LASAN, or any agency
    status: StepStatus
    step_type: Optional[str] = None  # PRM, INS, TRD, APP, SCH, ENR, DOC, PAY
    action_type: ActionType = ActionType.AUTOMATED  # automated, user_action, or information
    depends_on: List[str] = Field(default_factory=list)  # IDs of prerequisite steps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None  # Outcome data (permit numbers, etc.)
    estimated_duration_days: Optional[float] = None  # Average/estimated duration in days
    user_task: Optional[UserTask] = None  # Legacy - use user_action_card instead

    # ========== Enhanced Plan Tracking Fields ==========
    # For AUTOMATED steps: Record of tool execution
    execution_record: Optional[ToolExecutionRecord] = None

    # For USER_ACTION steps: The card shown to the user
    user_action_card: Optional[UserActionCard] = None

    # For ALL steps: How it was completed
    completion_record: Optional[CompletionRecord] = None

    # Audit trail: All events that happened
    history: List[StepEvent] = Field(default_factory=list)


class Plan(BaseModel):
    """The project plan with all steps."""
    id: str
    status: str = "active"
    steps: List[PlanStep] = []


class Reference(BaseModel):
    """A knowledge base reference citation."""
    source: str  # Source document filename
    agency: str  # LADBS, LADWP, or LASAN
    excerpt: str  # Brief excerpt of the content used
    title: Optional[str] = None  # Document title
    section: Optional[str] = None  # Section heading where content was found
    page_number: Optional[int] = None  # Page number (for PDFs)


class Project(BaseModel):
    """Project document with embedded plan."""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    progress: float = 0.0  # 0.0 to 1.0
    thread_id: Optional[str] = None  # Deprecated (stateless agent uses app-side message history)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    plan: Optional[Plan] = None
