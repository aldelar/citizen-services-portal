"""Pydantic models for CosmosDB documents."""

from datetime import datetime
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

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


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


# Configure camelCase alias for all models
class CamelCaseModel(BaseModel):
    """Base model with camelCase serialization."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split("_"))
        ),
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
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


class PlanStep(CamelCaseModel):
    """Plan step within a project."""

    id: str
    title: str
    description: str
    agency: Agency
    status: StepStatus = StepStatus.NOT_STARTED
    order: int
    estimated_duration_days: Optional[int] = None
    user_tasks: List[UserTask] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class Plan(CamelCaseModel):
    """Project plan containing steps."""

    steps: List[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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


class Message(CamelCaseModel):
    """Message document model."""

    id: str
    project_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[ToolCall]] = None
    token_usage: Optional[TokenUsage] = None


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
