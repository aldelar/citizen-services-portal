"""Data models for LASAN MCP server."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CollectionType(str, Enum):
    """Type of waste collection."""

    TRASH = "trash"
    RECYCLING = "recycling"
    GREEN_WASTE = "green_waste"


class BinType(str, Enum):
    """Type of waste bin."""

    BLACK = "black"  # Trash
    BLUE = "blue"  # Recycling
    GREEN = "green"  # Green waste


class CollectionSchedule(BaseModel):
    """Collection schedule for an address."""

    address: str = Field(description="Service address")
    trash_day: str = Field(description="Day of week for trash collection")
    recycling_day: str = Field(description="Day of week for recycling collection")
    green_waste_day: str = Field(description="Day of week for green waste collection")
    next_pickup: date = Field(description="Date of next pickup")
    holiday_adjustments: Optional[List[dict]] = Field(default=None, description="Holiday schedule adjustments")


class BulkyPickupRequest(BaseModel):
    """Request for bulky item pickup."""

    address: str = Field(description="Pickup address")
    contact_name: str = Field(description="Contact person name")
    contact_phone: str = Field(description="Contact phone number")
    items: List[str] = Field(description="List of items to pick up")
    preferred_date: date = Field(description="Preferred pickup date")
    special_instructions: Optional[str] = Field(default=None, description="Special instructions")
    requested_at: datetime = Field(description="Request timestamp")


class BulkyPickupStatus(BaseModel):
    """Status of bulky item pickup request."""

    request_id: str = Field(description="Request ID")
    status: str = Field(description="Status: scheduled, confirmed, completed, cancelled")
    scheduled_date: Optional[date] = Field(default=None, description="Scheduled pickup date")
    items: List[str] = Field(description="Items to be picked up")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class IllegalDumpingReport(BaseModel):
    """Report of illegal dumping."""

    location_address: str = Field(description="Location of illegal dumping")
    description: str = Field(description="Description of the dumping")
    materials: List[str] = Field(description="Types of materials dumped")
    reporter_name: Optional[str] = Field(default=None, description="Reporter name (optional)")
    reporter_phone: Optional[str] = Field(default=None, description="Reporter phone (optional)")
    reported_at: datetime = Field(description="Report timestamp")


class DumpingReportStatus(BaseModel):
    """Status of illegal dumping report."""

    report_id: str = Field(description="Report ID")
    status: str = Field(description="Status: received, investigating, cleanup_scheduled, resolved")
    location: str = Field(description="Location address")
    last_updated: datetime = Field(description="Last update timestamp")
    notes: Optional[str] = Field(default=None, description="Status notes")


class BinReplacementRequest(BaseModel):
    """Request for bin replacement."""

    address: str = Field(description="Service address")
    bin_type: BinType = Field(description="Type of bin")
    reason: str = Field(description="Reason: damaged, missing, stolen, wrong_size")
    contact_name: str = Field(description="Contact person name")
    contact_phone: str = Field(description="Contact phone number")
    requested_at: datetime = Field(description="Request timestamp")


class MissedCollectionReport(BaseModel):
    """Report of missed collection."""

    address: str = Field(description="Service address")
    collection_type: CollectionType = Field(description="Type of collection that was missed")
    scheduled_date: date = Field(description="Date collection was scheduled")
    contact_name: str = Field(description="Contact person name")
    contact_phone: str = Field(description="Contact phone number")
    reported_at: datetime = Field(description="Report timestamp")
