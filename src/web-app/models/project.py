"""Project and Plan models for the Citizen Services Portal."""

from pydantic import BaseModel
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
    id: str  # Short ID (P1, U1, I1, etc.)
    title: str  # Human-readable step name
    agency: str  # LADBS, LADWP, LASAN, or any agency
    status: StepStatus
    depends_on: List[str] = []  # IDs of prerequisite steps
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
