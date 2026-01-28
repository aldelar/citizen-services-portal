"""User model for the Citizen Services Portal."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserPreferences(BaseModel):
    """User preferences for notifications and contact."""
    notification_email: bool = True
    preferred_contact_method: str = "email"  # "email", "phone", "sms"


class User(BaseModel):
    """User profile document."""
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    preferences: UserPreferences = UserPreferences()
