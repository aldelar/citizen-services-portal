"""CosmosDB data access layer for Citizen Services Portal."""

from .base_repository import BaseRepository
from .client import close_client, get_container, get_cosmos_client, get_database
from .exceptions import ConflictError, NotFoundError, ValidationError
from .models import (
    ActionType,
    Agency,
    Message,
    Plan,
    PlanStep,
    Project,
    ProjectContext,
    ProjectReferences,
    ProjectStatus,
    ProjectSummary,
    StepCompletion,
    StepStatus,
    ToolCall,
    TokenUsage,
    User,
    UserPreferences,
    UserTask,
    UserTaskType,
)

__all__ = [
    # Client
    "get_cosmos_client",
    "get_database",
    "get_container",
    "close_client",
    # Base Repository
    "BaseRepository",
    # Exceptions
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    # Models - User
    "User",
    "UserPreferences",
    # Models - Project
    "Project",
    "ProjectContext",
    "ProjectSummary",
    "ProjectReferences",
    "ProjectStatus",
    # Models - Plan
    "Plan",
    "PlanStep",
    "StepStatus",
    "ActionType",
    "Agency",
    "UserTask",
    "UserTaskType",
    # Models - Message
    "Message",
    "ToolCall",
    "TokenUsage",
    # Models - Reporting
    "StepCompletion",
]
