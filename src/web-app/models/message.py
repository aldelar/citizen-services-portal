"""Chat message models for the Citizen Services Portal."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class MessageType(str, Enum):
    """Message type enumeration."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message document."""
    id: str
    project_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    sender_name: Optional[str] = None
