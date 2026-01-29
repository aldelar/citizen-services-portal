"""Pydantic models for CosmosDB documents."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Plan step status enumeration."""

    DEFINED = "defined"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REWORK = "needs_rework"
    REJECTED = "rejected"


class Agency(str, Enum):
    """Agency enumeration."""

    LADBS = "ladbs"
    LADWP = "ladwp"
    LASAN = "lasan"


class UserTaskType(str, Enum):
    """User task type enumeration."""

    FORM = "form"
    DOCUMENT = "document"
    PAYMENT = "payment"
    INSPECTION = "inspection"
    WAIT = "wait"


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


# Configure camelCase alias for all models
class CamelCaseModel(BaseModel):
    """Base model with camelCase serialization."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,  # Allow creating models from arbitrary objects
        alias_generator=lambda field_name: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split("_"))
        ),
        ser_json_timedelta='iso8601',  # Serialize timedelta as ISO 8601
    )


# User models
class UserPreferences(CamelCaseModel):
    """User preferences."""

    language: Optional[str] = "en"
    notifications_enabled: bool = True


class User(CamelCaseModel):
    """User document model."""

    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)


# Project models
class ProjectContext(CamelCaseModel):
    """Project context information."""

    address: str
    property_type: Optional[str] = None
    project_description: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class ProjectSummary(CamelCaseModel):
    """Project summary information."""

    total_steps: int = 0
    completed_steps: int = 0
    estimated_duration_days: Optional[int] = None
    estimated_cost: Optional[float] = None


class ProjectReferences(CamelCaseModel):
    """Project references to external resources."""

    permits: Dict[str, Any] = Field(default_factory=dict)
    applications: Dict[str, Any] = Field(default_factory=dict)
    documents: Dict[str, Any] = Field(default_factory=dict)


class UserTask(CamelCaseModel):
    """User task within a plan step."""

    type: UserTaskType
    description: str
    url: Optional[str] = None
    estimated_duration: Optional[str] = None


# ============================================================================
# Enhanced Plan Tracking Models (per proposal 9-proposal-enhanced-plan-tracking.md)
# ============================================================================


class ActionCardType(str, Enum):
    """Types of user action cards."""

    PHONE_CALL = "phone_call"
    EMAIL = "email"
    FORM_SUBMISSION = "form_submission"
    IN_PERSON = "in_person"
    UPLOAD = "upload"


class StepEventType(str, Enum):
    """Types of events in a step's history."""

    CREATED = "created"  # Step was added to plan
    STATUS_CHANGED = "status_changed"  # Status transition
    TOOL_EXECUTED = "tool_executed"  # Automated tool ran
    CARD_ASSIGNED = "card_assigned"  # User action card was assigned
    USER_NOTIFIED = "user_notified"  # User was reminded
    USER_COMPLETED = "user_completed"  # User marked as done
    AGENT_VERIFIED = "agent_verified"  # Agent verified completion
    BLOCKED = "blocked"  # Step was blocked
    UNBLOCKED = "unblocked"  # Block was resolved
    NOTE_ADDED = "note_added"  # Note was added
    RETRY_REQUESTED = "retry_requested"  # User/agent requested retry


class ToolExecutionRecord(CamelCaseModel):
    """Record of an automated tool execution."""

    tool_name: str  # e.g., "ladbs.submit_permit"
    request_id: Optional[str] = None  # ID returned by the tool (e.g., "REQ-2026-001234")
    reference_number: Optional[str] = None  # Business reference (permit #, application #)
    reference_url: Optional[str] = None  # Deep link to view the request/record
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_summary: Optional[Dict[str, Any]] = None  # Key inputs (sanitized)
    output_summary: Optional[Dict[str, Any]] = None  # Key outputs (sanitized)
    success: bool = True
    error_message: Optional[str] = None  # If failed


class UserActionCard(CamelCaseModel):
    """The action card shown to the user for a user-driven step."""

    step_id: str  # Required - links to plan step
    card_type: str  # phone_call, email, form_submission, in_person, upload
    title: str  # Short title for the card
    instructions: str  # Full markdown instructions

    # Prepared materials (agent-generated helpers)
    phone_script: Optional[str] = None  # Script for phone calls
    email_draft: Optional[str] = None  # Pre-drafted email content
    form_data: Optional[Dict[str, Any]] = None  # Pre-filled form fields
    checklist: List[str] = Field(default_factory=list)  # Steps to complete

    # Contact/action info
    contact_name: Optional[str] = None  # "LA Building & Safety"
    contact_phone: Optional[str] = None  # "(213) 555-1234"
    contact_email: Optional[str] = None  # "permits@lacity.org"
    action_url: Optional[str] = None  # Portal URL if online action

    # Timing
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_by: Optional[datetime] = None  # Deadline if applicable
    estimated_duration: Optional[str] = None  # "15 minutes", "1-2 business days"


class CompletionRecord(CamelCaseModel):
    """Record of step completion - works for both automated and user-driven steps."""

    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_by: str  # "agent" or "user:<user_id>"

    # For user-driven steps
    user_message: Optional[str] = None  # What the user reported ("Done! Confirmation #123")
    user_provided_data: Optional[Dict[str, Any]] = None  # Structured data from user

    # For automated steps (redundant with execution_record but explicit)
    tool_result: Optional[Dict[str, Any]] = None

    # Verification (optional)
    verified_by: Optional[str] = None  # "agent" if agent verified completion
    verification_notes: Optional[str] = None


class StepEvent(CamelCaseModel):
    """A single event in a step's history."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str  # See StepEventType
    actor: str  # "agent", "user:<id>", "system"
    summary: str  # Human-readable description
    details: Optional[Dict[str, Any]] = None  # Event-specific data
    message_id: Optional[str] = None  # Link to chat message that triggered this


class PlanStep(CamelCaseModel):
    """Plan step within a project."""

    id: str
    title: str
    description: Optional[str] = None  # Made optional for flexibility
    agency: Optional[str] = None  # Changed from Agency enum to string for flexibility
    status: StepStatus = StepStatus.DEFINED
    step_type: Optional[str] = None  # PRM, INS, TRD, APP, PCK, ENR, DOC, PAY
    action_type: Optional[str] = "automated"  # automated or user_action
    order: Optional[int] = None  # Made optional for flexibility
    estimated_duration_days: Optional[float] = None  # Can be fractional days
    user_tasks: List[UserTask] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)  # Alias for dependencies
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    result: Optional[Dict[str, Any]] = None  # Outcome data (permit numbers, application IDs, etc.)

    # ========== Enhanced Plan Tracking Fields ==========
    # For AUTOMATED steps: Record of tool execution
    execution_record: Optional[ToolExecutionRecord] = None

    # For USER_ACTION steps: The card shown to the user
    user_action_card: Optional[UserActionCard] = None

    # For ALL steps: How it was completed
    completion_record: Optional[CompletionRecord] = None

    # Audit trail: All events that happened
    history: List[StepEvent] = Field(default_factory=list)


class Plan(CamelCaseModel):
    """Project plan containing steps."""

    id: Optional[str] = None
    status: Optional[str] = "active"
    steps: List[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Project(CamelCaseModel):
    """Project document model."""

    id: str
    user_id: str
    title: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    context: ProjectContext
    plan: Optional[Plan] = None
    summary: ProjectSummary = Field(default_factory=ProjectSummary)
    references: ProjectReferences = Field(default_factory=ProjectReferences)
    thread_id: Optional[str] = None  # Agent conversation ID (conv_xxx format)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Message models
class ToolCall(CamelCaseModel):
    """Tool call information in a message."""

    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None


class TokenUsage(CamelCaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class KBReference(CamelCaseModel):
    """Knowledge base reference citation."""

    source: str  # Source document filename
    agency: str  # LADBS, LADWP, or LASAN
    excerpt: str  # Brief excerpt of the content used
    title: Optional[str] = None  # Document title
    section: Optional[str] = None  # Section heading where content was found
    page_number: Optional[int] = None  # Page number (for PDFs)


class Message(CamelCaseModel):
    """Message document model."""

    id: str
    project_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: Optional[List[ToolCall]] = None
    token_usage: Optional[TokenUsage] = None
    references: Optional[List[KBReference]] = None  # KB citations for assistant messages


# Step completion models
class StepCompletion(CamelCaseModel):
    """Step completion tracking for reporting."""

    id: str
    tool_name: str
    city: str
    started_at: datetime
    completed_at: datetime
    duration_days: int
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None
