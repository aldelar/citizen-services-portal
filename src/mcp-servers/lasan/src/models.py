"""Data models for LASAN MCP server."""

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
# LASAN Enums
# =============================================================================


class PickupType(str, Enum):
    """Type of special pickup."""

    BULKY_ITEM = "bulky_item"
    EWASTE = "ewaste"
    HAZARDOUS = "hazardous"


class ItemCategory(str, Enum):
    """Category of items for disposal."""

    APPLIANCES = "appliances"  # Refrigerators, washers, etc.
    FURNITURE = "furniture"  # Sofas, mattresses, etc.
    ELECTRONICS = "electronics"  # TVs, computers, etc.
    CONSTRUCTION_DEBRIS = "construction_debris"  # NOT accepted


class PickupStatus(str, Enum):
    """Status of a pickup request."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# =============================================================================
# LASAN Models
# =============================================================================


class ScheduledPickup(BaseModel):
    """A scheduled pickup."""

    pickup_id: str = Field(description="Unique pickup ID")
    pickup_type: PickupType = Field(description="Type of pickup")
    address: str = Field(description="Pickup address")
    scheduled_date: datetime = Field(description="Scheduled date")
    items: List[str] = Field(description="Items to be picked up")
    status: PickupStatus = Field(description="Current status")
    confirmation_number: Optional[str] = Field(default=None, description="Confirmation number")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class PickupScheduledResult(BaseModel):
    """Result from scheduled pickups query."""

    address: str = Field(description="Address queried")
    pickups: List[ScheduledPickup] = Field(description="Scheduled pickups")
    total_count: int = Field(description="Total count")


class EligibleItem(BaseModel):
    """An item eligible for pickup."""

    item_type: str = Field(description="Type of item")
    pickup_type: PickupType = Field(description="Pickup type for this item")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class IneligibleItem(BaseModel):
    """An item not eligible for pickup."""

    item_type: str = Field(description="Type of item")
    reason: str = Field(description="Why item is not eligible")
    alternatives: List[str] = Field(description="Alternative disposal options")


class EligibilityResult(BaseModel):
    """Result of pickup eligibility check."""

    address: str = Field(description="Address checked")
    eligible_items: List[EligibleItem] = Field(description="Items eligible for pickup")
    ineligible_items: List[IneligibleItem] = Field(description="Items not eligible")
    annual_limit: int = Field(description="Annual pickup limit")
    collections_used: int = Field(description="Collections used this year")
    collections_remaining: int = Field(description="Collections remaining")
