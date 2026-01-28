"""Project and Plan models for the Citizen Services Portal."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Step status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AWAITING_USER = "awaiting_user"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    READY = "ready"


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
    SCH = "SCH"  # Schedule - book appointments/pickups
    ENR = "ENR"  # Enroll - sign up for programs/plans
    DOC = "DOC"  # Document - gather documents/materials
    PAY = "PAY"  # Payment - pay fees/deposits


class UserTask(BaseModel):
    """Details for user-action steps."""
    type: UserTaskType
    target: str  # "311", email, URL, or location
    reason: str  # Why this can't be automated
    assigned_at: Optional[datetime] = None
    phone_script: Optional[str] = None
    email_draft: Optional[str] = None
    checklist: List[str] = []
    contact_info: Optional[Dict[str, str]] = None


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
    user_task: Optional[UserTask] = None  # Present when status is awaiting_user


class Plan(BaseModel):
    """The project plan with all steps."""
    id: str
    title: str
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
